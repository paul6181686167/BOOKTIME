"""
PHASE 3.2 - Routes Export/Import de Données
Endpoints pour export/import avec formats multiples
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.responses import Response
from typing import Optional, List
from datetime import datetime
import json

from ..security.jwt import get_current_user
from .service import ExportImportService, ExportOptions, ImportResult

router = APIRouter(prefix="/api/export-import", tags=["export-import"])

# Instance du service
export_import_service = ExportImportService()

@router.get("/export")
async def export_user_data(
    format_type: str = Query("json", description="Format d'export (json, csv, excel, full_backup)"),
    include_metadata: bool = Query(True, description="Inclure les métadonnées"),
    include_stats: bool = Query(True, description="Inclure les statistiques"),
    include_reading_progress: bool = Query(True, description="Inclure la progression"),
    include_reviews: bool = Query(True, description="Inclure les avis"),
    include_covers: bool = Query(False, description="Inclure les couvertures (base64)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Exporte les données utilisateur dans le format spécifié
    
    Args:
        format_type: Type de format (json, csv, excel, full_backup)
        include_metadata: Inclure métadonnées utilisateur
        include_stats: Inclure statistiques de lecture
        include_reading_progress: Inclure progression détaillée
        include_reviews: Inclure avis et notes
        include_covers: Inclure couvertures en base64
        current_user: Utilisateur connecté
        
    Returns:
        Fichier d'export dans le format demandé
    """
    try:
        user_id = current_user.get("id")
        
        # Valider le format
        if format_type not in export_import_service.supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Format non supporté. Formats supportés: {export_import_service.supported_formats}"
            )
        
        # Créer les options d'export
        options = ExportOptions(
            include_metadata=include_metadata,
            include_stats=include_stats,
            include_reading_progress=include_reading_progress,
            include_reviews=include_reviews,
            include_covers=include_covers,
            format_type=format_type
        )
        
        # Effectuer l'export
        export_result = await export_import_service.export_user_data(user_id, options)
        
        # Retourner le fichier
        return Response(
            content=export_result['content'],
            media_type=export_result['content_type'],
            headers={
                "Content-Disposition": f"attachment; filename={export_result['filename']}"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'export: {str(e)}"
        )

@router.post("/import")
async def import_user_data(
    file: UploadFile = File(..., description="Fichier à importer"),
    skip_duplicates: bool = Form(True, description="Ignorer les doublons"),
    update_existing: bool = Form(False, description="Mettre à jour les livres existants"),
    dry_run: bool = Form(False, description="Simulation sans import réel"),
    current_user: dict = Depends(get_current_user)
):
    """
    Importe des données dans la bibliothèque utilisateur
    
    Args:
        file: Fichier à importer (JSON, CSV, Excel)
        skip_duplicates: Ignorer les livres en doublon
        update_existing: Mettre à jour les livres existants
        dry_run: Mode simulation pour prévisualiser l'import
        current_user: Utilisateur connecté
        
    Returns:
        Résultat de l'import avec détails
    """
    try:
        user_id = current_user.get("user_id")
        
        # Lire le contenu du fichier
        file_content = await file.read()
        
        # Options d'import
        import_options = {
            'skip_duplicates': skip_duplicates,
            'update_existing': update_existing,
            'dry_run': dry_run
        }
        
        # Effectuer l'import
        import_result = await export_import_service.import_user_data(
            user_id=user_id,
            file_content=file_content,
            filename=file.filename,
            options=import_options
        )
        
        # Formater la réponse
        response_data = {
            "success": import_result.success,
            "summary": {
                "total_processed": import_result.total_processed,
                "imported_count": import_result.imported_count,
                "skipped_count": import_result.skipped_count,
                "error_count": import_result.error_count
            },
            "details": {
                "duplicates_found": len(import_result.duplicates),
                "errors": import_result.errors[:10],  # Limiter les erreurs affichées
                "imported_books": [
                    {
                        "title": book.get("title"),
                        "author": book.get("author"),
                        "category": book.get("category")
                    }
                    for book in import_result.imported_books[:20]  # Limiter l'affichage
                ]
            },
            "options_used": import_options,
            "import_date": datetime.utcnow().isoformat()
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'import: {str(e)}"
        )

@router.post("/import/preview")
async def preview_import(
    file: UploadFile = File(..., description="Fichier à prévisualiser"),
    current_user: dict = Depends(get_current_user)
):
    """
    Prévisualise un import sans l'effectuer réellement
    
    Args:
        file: Fichier à prévisualiser
        current_user: Utilisateur connecté
        
    Returns:
        Aperçu des données qui seraient importées
    """
    try:
        user_id = current_user.get("user_id")
        
        # Lire le contenu du fichier
        file_content = await file.read()
        
        # Options en mode preview
        import_options = {
            'skip_duplicates': True,
            'update_existing': False,
            'dry_run': True  # Mode simulation
        }
        
        # Effectuer la preview
        preview_result = await export_import_service.import_user_data(
            user_id=user_id,
            file_content=file_content,
            filename=file.filename,
            options=import_options
        )
        
        # Formater la réponse pour preview
        response_data = {
            "success": True,
            "preview": {
                "total_books_found": preview_result.total_processed,
                "would_import": preview_result.imported_count,
                "would_skip": preview_result.skipped_count,
                "duplicates_detected": len(preview_result.duplicates),
                "errors_detected": preview_result.error_count
            },
            "sample_books": [
                {
                    "title": book.get("title"),
                    "author": book.get("author"),
                    "category": book.get("category"),
                    "status": book.get("status")
                }
                for book in preview_result.imported_books[:10]  # 10 premiers livres
            ],
            "duplicates_sample": [
                {
                    "title": dup["import_book"]["title"],
                    "author": dup["import_book"]["author"],
                    "match_reason": dup["match_reason"]
                }
                for dup in preview_result.duplicates[:5]  # 5 premiers doublons
            ],
            "errors_sample": preview_result.errors[:5],  # 5 premières erreurs
            "file_info": {
                "filename": file.filename,
                "size_bytes": len(file_content),
                "detected_format": export_import_service._detect_file_format(file.filename, file_content)
            }
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la preview: {str(e)}"
        )

@router.get("/export/formats")
async def get_supported_formats(
    current_user: dict = Depends(get_current_user)
):
    """
    Récupère la liste des formats supportés pour l'export
    
    Returns:
        Liste des formats avec descriptions
    """
    formats_info = {
        "json": {
            "name": "JSON",
            "description": "Format JSON complet avec toutes les données",
            "extension": ".json",
            "supports_metadata": True,
            "best_for": "Sauvegarde complète et réimport"
        },
        "csv": {
            "name": "CSV",
            "description": "Format CSV pour tableurs (Excel, LibreOffice)",
            "extension": ".csv",
            "supports_metadata": False,
            "best_for": "Analyse dans Excel ou autre tableur"
        },
        "excel": {
            "name": "Excel",
            "description": "Fichier Excel avec feuilles multiples",
            "extension": ".xlsx",
            "supports_metadata": True,
            "best_for": "Analyse avancée et rapports"
        },
        "full_backup": {
            "name": "Sauvegarde Complète",
            "description": "Archive ZIP avec tous les formats",
            "extension": ".zip",
            "supports_metadata": True,
            "best_for": "Sauvegarde complète avec documentation"
        }
    }
    
    return {
        "supported_formats": list(export_import_service.supported_formats),
        "formats_details": formats_info,
        "recommendations": {
            "backup": "full_backup",
            "analysis": "excel",
            "simple_export": "csv",
            "reimport": "json"
        }
    }

@router.get("/import/formats")
async def get_supported_import_formats(
    current_user: dict = Depends(get_current_user)
):
    """
    Récupère la liste des formats supportés pour l'import
    
    Returns:
        Liste des formats d'import avec descriptions
    """
    import_formats = {
        "json": {
            "name": "JSON BOOKTIME",
            "description": "Fichier JSON exporté depuis BOOKTIME",
            "extensions": [".json"],
            "compatibility": "Parfaite",
            "supports_all_fields": True
        },
        "csv": {
            "name": "CSV Générique",
            "description": "Fichier CSV avec colonnes titre, auteur, etc.",
            "extensions": [".csv"],
            "compatibility": "Bonne",
            "supports_all_fields": False,
            "required_columns": ["title", "author"]
        },
        "goodreads": {
            "name": "Export Goodreads",
            "description": "Fichier CSV exporté depuis Goodreads",
            "extensions": [".csv"],
            "compatibility": "Bonne",
            "supports_all_fields": False,
            "special_handling": True
        },
        "excel": {
            "name": "Excel",
            "description": "Fichier Excel (.xlsx)",
            "extensions": [".xlsx", ".xls"],
            "compatibility": "Bonne",
            "supports_all_fields": True
        }
    }
    
    return {
        "supported_formats": import_formats,
        "tips": [
            "Pour un import optimal, utilisez un export JSON de BOOKTIME",
            "Les fichiers CSV doivent contenir au minimum les colonnes 'title' et 'author'",
            "L'import Goodreads est automatiquement détecté",
            "Utilisez la preview pour vérifier avant l'import définitif"
        ],
        "max_file_size_mb": export_import_service.max_file_size // 1024 // 1024
    }

@router.get("/user/export-history")
async def get_export_history(
    limit: int = Query(10, ge=1, le=50, description="Nombre d'exports à retourner"),
    current_user: dict = Depends(get_current_user)
):
    """
    Récupère l'historique des exports de l'utilisateur
    
    Args:
        limit: Nombre d'exports à retourner
        current_user: Utilisateur connecté
        
    Returns:
        Historique des exports
    """
    try:
        user_id = current_user.get("user_id")
        
        # Récupérer l'historique depuis la base (si implémenté)
        # Pour l'instant, retourner une structure vide
        
        return {
            "success": True,
            "exports": [],  # À implémenter avec une collection export_history
            "message": "Historique des exports (fonctionnalité à venir)"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )

@router.post("/templates/generate")
async def generate_import_template(
    format_type: str = Query("csv", description="Format du template (csv, excel)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Génère un template d'import vide
    
    Args:
        format_type: Format du template à générer
        current_user: Utilisateur connecté
        
    Returns:
        Template d'import vide
    """
    try:
        if format_type == "csv":
            # Créer un CSV template
            import io
            import csv
            
            output = io.StringIO()
            fieldnames = [
                'title', 'author', 'category', 'status', 'rating', 'review',
                'current_page', 'total_pages', 'original_language', 'reading_language'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            # Ajouter quelques exemples
            examples = [
                {
                    'title': 'Exemple Livre 1',
                    'author': 'Auteur Exemple',
                    'category': 'roman',
                    'status': 'to_read',
                    'rating': '',
                    'review': '',
                    'current_page': '0',
                    'total_pages': '300',
                    'original_language': 'français',
                    'reading_language': 'français'
                },
                {
                    'title': 'Exemple Livre 2',
                    'author': 'Autre Auteur',
                    'category': 'bd',
                    'status': 'completed',
                    'rating': '4',
                    'review': 'Très bon livre !',
                    'current_page': '150',
                    'total_pages': '150',
                    'original_language': 'français',
                    'reading_language': 'français'
                }
            ]
            
            for example in examples:
                writer.writerow(example)
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content.encode('utf-8'),
                media_type='text/csv',
                headers={
                    "Content-Disposition": "attachment; filename=booktime_import_template.csv"
                }
            )
            
        else:
            raise HTTPException(
                status_code=400,
                detail="Format de template non supporté. Utilisez 'csv'."
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du template: {str(e)}"
        )