"""
Tests pour le système de chapitres individuels
=============================================

Tests complets du module chapters :
- Service ChapterService
- Endpoints API (8 routes)  
- Intégrations externes AniList/MangaUpdates
- Modèles Pydantic
- Cache et prédictions
"""

import pytest
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from pydantic import ValidationError

# Imports du module chapters
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chapters.service import ChapterService
from app.chapters.models import (
    SeriesChapters, Chapter, Volume,
    ChapterPrediction, ChapterStatus, VolumeStatus
)
from app.chapters.integrations.anilist import AniListService
from app.main import app
from app.dependencies import get_current_user as deps_get_current_user

# Client de test
client = TestClient(app)


@pytest.fixture
def chapters_auth_override():
    """JWT simulé pour les tests d'endpoints chapitres (override FastAPI)."""

    def fake_user():
        return SimpleNamespace(id="test-user", email="pytest@example.com")

    app.dependency_overrides[deps_get_current_user] = fake_user
    yield
    app.dependency_overrides.pop(deps_get_current_user, None)


class TestChapterService:
    """Tests unitaires du ChapterService"""
    
    @pytest.fixture
    def service(self):
        """Fixture du service chapters"""
        return ChapterService()
    
    @pytest.fixture
    def sample_series_data(self):
        """Données d'exemple pour les tests"""
        return SeriesChapters(
            id="test-uuid",
            series_name="One Piece Test",
            manga_id_anilist=30013,
            total_chapters_released=1100,
            current_chapters=[
                Chapter(
                    id="ch-1099-test",
                    chapter_number=1099,
                    title="Pacifista",
                    status=ChapterStatus.RELEASED,
                    release_date=datetime(2024, 1, 15)
                ),
                Chapter(
                    id="ch-1100-test",
                    chapter_number=1100,
                    title="Thank You, Bonney",
                    status=ChapterStatus.RELEASED,
                    release_date=datetime(2024, 1, 22)
                )
            ]
        )
    
    def test_service_initialization(self, service):
        """Test initialisation du service"""
        assert service.collection_name == "series_chapters"
        assert service.cache_duration.total_seconds() == 10800  # 3 heures
        assert hasattr(service, 'anilist')
        assert hasattr(service, 'mangaupdates')
        assert hasattr(service, 'predictor')
    
    @pytest.mark.asyncio
    async def test_get_series_chapters_cached(self, service, sample_series_data):
        """Test récupération depuis cache"""
        # Mock du cache
        with patch.object(service, '_get_cached_series', return_value=sample_series_data):
            with patch.object(service, '_is_cache_expired', return_value=False):
                
                result = await service.get_series_chapters("One Piece Test")
                
                assert result is not None
                assert result.series_name == "One Piece Test"
                assert len(result.current_chapters) == 2
                assert result.current_chapters[0].chapter_number == 1099
    
    @pytest.mark.asyncio
    async def test_get_series_chapters_external_apis(self, service):
        """Test récupération depuis APIs externes"""
        # Mock des APIs externes
        with patch.object(service, '_get_cached_series', return_value=None):
            with patch.object(service, '_fetch_from_external_apis') as mock_fetch:
                mock_series = SeriesChapters(
                    id="test-id",
                    series_name="Test Series",
                    current_chapters=[]
                )
                mock_fetch.return_value = mock_series
                
                with patch.object(service, '_enrich_with_predictions', return_value=mock_series):
                    with patch.object(service, '_save_to_cache', return_value=True):
                        
                        result = await service.get_series_chapters("Test Series", force_refresh=True)
                        
                        assert result is not None
                        assert result.series_name == "Test Series"
                        mock_fetch.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_search_series_in_apis(self, service):
        """Test recherche dans APIs externes"""
        # Mock des résultats AniList et MangaUpdates
        anilist_results = [
            {"id": 30013, "title": "One Piece", "popularity": 50000}
        ]
        mu_results = [
            {"id": 319, "title": "One Piece", "rating": 9.5}
        ]
        
        with patch.object(service.anilist, 'search_manga', return_value=anilist_results):
            with patch.object(service.mangaupdates, 'search_series', return_value=mu_results):
                
                result = await service.search_series_in_apis("One Piece")
                
                assert "anilist_matches" in result
                assert "mangaupdates_matches" in result
                assert "confidence_scores" in result
                assert len(result["anilist_matches"]) == 1
                assert result["anilist_matches"][0]["id"] == 30013
    
    @pytest.mark.asyncio
    async def test_get_upcoming_releases(self, service):
        """Test récupération planning sorties"""
        # Mock de la base de données
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [
            {
                "series_name": "One Piece",
                "next_chapter": {
                    "estimated_number": 1101,
                    "estimated_date": datetime.now() + timedelta(days=2),
                    "confidence": 0.95
                }
            }
        ]
        
        with patch.object(service, '_ensure_db'):
            with patch.object(service, 'db', {"series_chapters": Mock()}):
                service.db["series_chapters"].find.return_value = mock_cursor
                
                result = await service.get_upcoming_releases()
                
                assert "this_week" in result
                assert "next_week" in result  
                assert "this_month" in result
                assert isinstance(result["this_week"], list)


class TestChapterEndpointsPublic:
    """Endpoints sans JWT."""

    def test_health_check_endpoint(self):
        """Test endpoint health check"""
        response = client.get("/api/chapters/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["module"] == "chapters"
        assert "features" in data
        assert "series_chapters" in data["features"]

    def test_get_series_chapters_unauthenticated(self):
        """Test endpoint série sans authentification"""
        response = client.get("/api/chapters/series/One Piece")

        assert response.status_code == 401


@pytest.mark.usefixtures("chapters_auth_override")
class TestChapterEndpoints:
    """Tests des endpoints API chapters (JWT via dependency override)."""

    def test_get_series_chapters_authenticated(self):
        """Test endpoint série avec authentification"""
        with patch(
            "app.chapters.routes.service.get_series_chapters", new_callable=AsyncMock
        ) as mock_service:
            mock_series = SeriesChapters(
                id="test-id",
                series_name="One Piece",
                current_chapters=[],
                total_chapters_released=1101,
            )
            mock_service.return_value = mock_series

            response = client.get("/api/chapters/series/One Piece")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["series_name"] == "One Piece"

    def test_refresh_series_chapters(self):
        """Test endpoint refresh série"""
        with patch(
            "app.chapters.routes.service.refresh_series_chapters", new_callable=AsyncMock
        ) as mock_refresh:
            mock_refresh.return_value = True

            response = client.post("/api/chapters/series/One Piece/refresh")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "updated_at" in data

    def test_get_upcoming_releases(self):
        """Test endpoint planning sorties"""
        with patch(
            "app.chapters.routes.service.get_upcoming_releases", new_callable=AsyncMock
        ) as mock_upcoming:
            mock_upcoming.return_value = {
                "this_week": [
                    {
                        "series_name": "One Piece",
                        "chapter_number": 1101,
                        "estimated_date": "2024-01-29",
                        "confidence": 0.95,
                    }
                ],
                "next_week": [],
                "this_month": [],
            }

            response = client.get("/api/chapters/releases/upcoming")

            assert response.status_code == 200
            data = response.json()
            assert "this_week" in data
            assert len(data["this_week"]) == 1
            assert data["this_week"][0]["series_name"] == "One Piece"

    def test_get_user_chapter_stats(self):
        """Test endpoint statistiques utilisateur"""
        response = client.get("/api/chapters/user/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stats" in data
        assert "predictions_accuracy" in data["stats"]

    def test_search_series_in_apis(self):
        """Test endpoint recherche série"""
        with patch(
            "app.chapters.routes.service.search_series_in_apis", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = {
                "anilist_matches": [{"id": 30013, "title": "One Piece"}],
                "mangaupdates_matches": [{"id": 319, "title": "One Piece"}],
                "confidence_scores": {"anilist": 0.98, "mangaupdates": 0.95},
            }

            response = client.get("/api/chapters/search/One Piece")

            assert response.status_code == 200
            data = response.json()
            assert "anilist_matches" in data
            assert "confidence_scores" in data

    def test_map_series_ids(self):
        """Test endpoint mapping IDs"""
        with patch(
            "app.chapters.routes.service.map_series_ids", new_callable=AsyncMock
        ) as mock_map:
            mock_map.return_value = True

            payload = {
                "anilist_id": 30013,
                "mangaupdates_id": 319,
            }

            response = client.post(
                "/api/chapters/series/One Piece/map-ids", json=payload
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["mapped_ids"]["anilist_id"] == 30013

    def test_get_integrations_status(self):
        """Test endpoint statut intégrations"""
        with patch(
            "app.chapters.routes.service.get_integration_status", new_callable=AsyncMock
        ) as mock_status:
            mock_status.return_value = {
                "anilist": {"status": "ok", "response_time": 150},
                "mangaupdates": {"status": "ok", "response_time": 890},
            }

            response = client.get("/api/chapters/integrations/status")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "integrations" in data
            assert data["integrations"]["anilist"]["status"] == "ok"

    def test_update_predictions_config(self):
        """Test endpoint configuration prédictions"""
        payload = {
            "enable_predictions": True,
            "confidence_threshold": 0.85,
        }

        response = client.put("/api/chapters/predictions/config", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["config"]["enable_predictions"] is True
        assert data["config"]["confidence_threshold"] == 0.85


class TestAniListService:
    """Tests de l'intégration AniList"""
    
    @pytest.fixture
    def anilist_service(self):
        """Fixture service AniList"""
        return AniListService()
    
    def test_anilist_service_initialization(self, anilist_service):
        """Test initialisation service AniList"""
        assert anilist_service.BASE_URL == "https://graphql.anilist.co"
        assert anilist_service.rate_limit_delay == 1.0
        assert anilist_service.cache == {}
        assert anilist_service.cache_duration.total_seconds() == 21600  # 6 heures
    
    def test_extract_best_title(self, anilist_service):
        """Test extraction meilleur titre"""
        title_obj = {
            "english": "One Piece",
            "romaji": "One Piece", 
            "native": "ワンピース"
        }
        
        result = anilist_service._extract_best_title(title_obj)
        assert result == "One Piece"
        
        # Test avec seulement titre natif
        title_obj_native = {"native": "ワンピース"}
        result_native = anilist_service._extract_best_title(title_obj_native)
        assert result_native == "ワンピース"
        
        # Test avec objet vide
        result_empty = anilist_service._extract_best_title({})
        assert result_empty == ""
    
    def test_extract_all_titles(self, anilist_service):
        """Test extraction tous les titres"""
        title_obj = {
            "english": "One Piece",
            "romaji": "One Piece",
            "native": "ワンピース"
        }
        
        result = anilist_service._extract_all_titles(title_obj)
        assert len(result) == 2  # "One Piece" et "ワンピース" (dédupliqué)
        assert "One Piece" in result
        assert "ワンピース" in result
    
    def test_format_date(self, anilist_service):
        """Test formatage dates AniList"""
        date_obj = {"year": 1997, "month": 7, "day": 22}
        result = anilist_service._format_date(date_obj)
        assert result == "1997-07-22"
        
        # Test avec date partielle
        date_partial = {"year": 1997}
        result_partial = anilist_service._format_date(date_partial)
        assert result_partial == "1997-01-01"
        
        # Test avec objet vide
        result_empty = anilist_service._format_date(None)
        assert result_empty is None
    
    def test_calculate_search_confidence(self, anilist_service):
        """Test calcul confiance recherche"""
        media = {
            "title": {
                "english": "One Piece",
                "romaji": "One Piece"
            },
            "popularity": 50000
        }
        
        # Correspondance exacte
        confidence_exact = anilist_service._calculate_search_confidence("One Piece", media)
        assert confidence_exact == 1.0
        
        # Correspondance partielle
        confidence_partial = anilist_service._calculate_search_confidence("One", media)
        assert confidence_partial == 0.9
        
        # Aucune correspondance mais populaire
        media_no_match = {
            "title": {"english": "Different Series"},
            "popularity": 20000
        }
        confidence_popular = anilist_service._calculate_search_confidence("One Piece", media_no_match)
        assert confidence_popular == 0.6
    
    @pytest.mark.asyncio
    async def test_health_check_mock(self, anilist_service):
        """Test health check avec mock"""
        # Mock de la requête
        with patch.object(anilist_service, '_make_request') as mock_request:
            mock_request.return_value = {
                "Media": {
                    "id": 30013,
                    "title": {"romaji": "One Piece"}
                }
            }
            
            result = await anilist_service.health_check()
            assert result is True
            
            # Test avec erreur
            mock_request.return_value = {}
            result_error = await anilist_service.health_check()
            assert result_error is False


class TestChapterModels:
    """Tests des modèles Pydantic"""
    
    def test_chapter_model_creation(self):
        """Test création modèle Chapter"""
        chapter = Chapter(
            id="ch-1101-test",
            chapter_number=1101,
            title="Heavy Rotation",
            release_date=datetime(2024, 1, 15),
            status=ChapterStatus.RELEASED,
            page_count=17
        )
        
        assert chapter.chapter_number == 1101
        assert chapter.title == "Heavy Rotation"
        assert chapter.status == ChapterStatus.RELEASED
        assert chapter.page_count == 17
        assert chapter.volume_number is None
    
    def test_volume_model_creation(self):
        """Test création modèle Volume"""
        volume = Volume(
            volume_number=108,
            chapters_range="1095-1105",
            chapters_included=[1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105],
            status=VolumeStatus.UPCOMING,
            page_count=192
        )
        
        assert volume.volume_number == 108
        assert volume.chapters_range == "1095-1105"
        assert len(volume.chapters_included) == 11
        assert volume.status == VolumeStatus.UPCOMING
        assert volume.page_count == 192
    
    def test_series_chapters_model_creation(self):
        """Test création modèle SeriesChapters"""
        series = SeriesChapters(
            id="test-uuid",
            series_name="One Piece",
            manga_id_anilist=30013,
            manga_id_mangaupdates=319,
            total_chapters_released=1101,
            total_volumes_released=107
        )
        
        assert series.id == "test-uuid"
        assert series.series_name == "One Piece"
        assert series.manga_id_anilist == 30013
        assert series.manga_id_mangaupdates == 319
        assert series.total_chapters_released == 1101
        assert series.total_volumes_released == 107
        assert series.enable_predictions is True  # Valeur par défaut
        assert series.auto_volume_grouping is True
    
    def test_chapter_prediction_model(self):
        """Test création modèle ChapterPrediction"""
        prediction = ChapterPrediction(
            estimated_number=1102,
            estimated_date=datetime(2024, 1, 29),
            confidence=0.95,
            method="weekly_pattern"
        )
        
        assert prediction.estimated_number == 1102
        assert prediction.confidence == 0.95
        assert prediction.method == "weekly_pattern"
        
        # Test validation confidence (doit être entre 0 et 1)
        with pytest.raises(ValidationError):
            ChapterPrediction(
                estimated_number=1103,
                confidence=1.5,  # Invalide
                method="test"
            )


if __name__ == "__main__":
    # Exécution des tests
    print("🧪 Tests du système chapitres individuels")
    print("=" * 50)
    
    # Configuration pytest
    pytest.main([
        __file__,
        "-v",  # Verbose
        "--tb=short",  # Traceback court
        "--color=yes"  # Couleurs
    ])