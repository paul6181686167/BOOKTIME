"""
Tests backend du système de chapitres - Version simplifiée
=========================================================

Tests directs et autonomes du module chapters sans pytest complexe
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Configuration path
sys.path.insert(0, '/app/backend')

# Test d'import simple
def test_imports():
    """Test des imports du module chapters"""
    try:
        from app.chapters.service import ChapterService
        from app.chapters.models import SeriesChapters, Chapter, Volume
        from app.chapters.integrations.anilist import AniListService
        
        print("✅ Import ChapterService: OK")
        print("✅ Import models (SeriesChapters, Chapter, Volume): OK")
        print("✅ Import AniListService: OK")
        return True
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        return False

def test_models():
    """Test création modèles Pydantic"""
    try:
        from app.chapters.models import SeriesChapters, Chapter, Volume, ChapterStatus
        
        # Test Chapter
        chapter = Chapter(
            chapter_number=1101,
            title="Heavy Rotation",
            status=ChapterStatus.RELEASED,
            release_date=datetime(2024, 1, 15)
        )
        
        assert chapter.chapter_number == 1101
        assert chapter.title == "Heavy Rotation"
        assert chapter.status == ChapterStatus.RELEASED
        print("✅ Modèle Chapter: OK")
        
        # Test Volume  
        volume = Volume(
            volume_number=108,
            chapters_range="1095-1105",
            chapters_included=[1095, 1096, 1097, 1098, 1099, 1100],
            page_count=192
        )
        
        assert volume.volume_number == 108
        assert volume.chapters_range == "1095-1105"
        assert len(volume.chapters_included) == 6
        print("✅ Modèle Volume: OK")
        
        # Test SeriesChapters
        series = SeriesChapters(
            id="test-uuid",
            series_name="One Piece",
            manga_id_anilist=30013,
            total_chapters_released=1101
        )
        
        assert series.series_name == "One Piece"
        assert series.manga_id_anilist == 30013
        assert series.enable_predictions is True
        print("✅ Modèle SeriesChapters: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur modèles: {e}")
        traceback.print_exc()
        return False

def test_service_basic():
    """Test initialisation service"""
    try:
        from app.chapters.service import ChapterService
        
        service = ChapterService()
        
        assert service.collection_name == "series_chapters"
        assert service.cache_duration.total_seconds() == 10800  # 3 heures
        assert hasattr(service, 'anilist')
        assert hasattr(service, 'mangaupdates')
        assert hasattr(service, 'predictor')
        
        print("✅ Service ChapterService initialization: OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur service: {e}")
        traceback.print_exc()
        return False

def test_anilist_service():
    """Test service AniList"""
    try:
        from app.chapters.integrations.anilist import AniListService
        
        anilist = AniListService()
        
        assert anilist.BASE_URL == "https://graphql.anilist.co"
        assert anilist.rate_limit_delay == 1.0
        assert anilist.cache == {}
        
        # Test méthodes utilitaires
        title_obj = {
            "english": "One Piece",
            "romaji": "One Piece", 
            "native": "ワンピース"
        }
        
        best_title = anilist._extract_best_title(title_obj)
        assert best_title == "One Piece"
        
        all_titles = anilist._extract_all_titles(title_obj)
        assert len(all_titles) == 2  # "One Piece" et "ワンピース"
        assert "One Piece" in all_titles
        assert "ワンピース" in all_titles
        
        # Test formatage date
        date_obj = {"year": 1997, "month": 7, "day": 22}
        formatted_date = anilist._format_date(date_obj)
        assert formatted_date == "1997-07-22"
        
        # Test calcul confiance
        media = {
            "title": {"english": "One Piece"},
            "popularity": 50000
        }
        confidence = anilist._calculate_search_confidence("One Piece", media)
        assert confidence == 1.0
        
        print("✅ Service AniList: OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur AniList service: {e}")
        traceback.print_exc()
        return False

async def test_service_async():
    """Test méthodes async du service"""
    try:
        from app.chapters.service import ChapterService
        from app.chapters.models import SeriesChapters
        
        service = ChapterService()
        
        # Test avec mock de _get_cached_series
        sample_series = SeriesChapters(
            id="test-uuid",
            series_name="One Piece Test", 
            current_chapters=[],
            total_chapters_released=1100
        )
        
        # Mock de la méthode pour éviter la DB
        with patch.object(service, '_get_cached_series', return_value=sample_series):
            with patch.object(service, '_is_cache_expired', return_value=False):
                result = await service.get_series_chapters("One Piece Test")
                
                assert result is not None
                assert result.series_name == "One Piece Test"
                assert result.total_chapters_released == 1100
                
        print("✅ Service async methods: OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur service async: {e}")
        traceback.print_exc()
        return False

def test_api_health_check():
    """Test health check API"""
    try:
        import requests
        
        response = requests.get("http://localhost:8001/api/chapters/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["module"] == "chapters"
        assert "features" in data
        assert "series_chapters" in data["features"]
        
        print("✅ API Health Check: OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur API health: {e}")
        return False

def run_all_tests():
    """Exécute tous les tests"""
    print("🧪 TESTS BACKEND - SYSTÈME CHAPITRES INDIVIDUELS")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Modèles Pydantic", test_models),
        ("Service Basic", test_service_basic),
        ("AniList Service", test_anilist_service),
        ("API Health Check", test_api_health_check)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 Test: {test_name}")
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: SUCCÈS")
            else:
                print(f"❌ {test_name}: ÉCHEC")
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
        print()
    
    # Test async séparé
    print("🔍 Test: Service Async Methods")
    try:
        result = asyncio.run(test_service_async())
        if result:
            passed += 1
            print("✅ Service Async Methods: SUCCÈS")
        else:
            print("❌ Service Async Methods: ÉCHEC")
    except Exception as e:
        print(f"❌ Service Async Methods: EXCEPTION - {e}")
    
    total += 1  # Pour le test async
    print()
    
    print("📊 RÉSULTATS FINAUX")
    print("=" * 30)
    print(f"✅ Tests réussis: {passed}/{total}")
    print(f"❌ Tests échoués: {total - passed}/{total}")
    print(f"📈 Taux de succès: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        return True
    else:
        print(f"\n⚠️  {total - passed} TEST(S) ONT ÉCHOUÉ")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)