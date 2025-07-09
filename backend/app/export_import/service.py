"""
PHASE 3.2 - Service Export/Import de Données
Gestion complète export/import bibliothèque avec formats multiples
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import csv
import io
import zipfile
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
import pandas as pd
import uuid

from ..database.connection import client
from ..models.user import User

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExportOptions:
    """Options d'export configurables"""
    include_metadata: bool = True
    include_stats: bool = True
    include_reading_progress: bool = True
    include_reviews: bool = True
    include_covers: bool = False  # Base64 des couvertures
    format_type: str = 'json'  # json, csv, excel, full_backup

@dataclass
class ImportResult:
    """Résultat d'une opération d'import"""
    success: bool
    total_processed: int
    imported_count: int
    skipped_count: int
    error_count: int
    errors: List[str]
    duplicates: List[Dict]
    imported_books: List[Dict]

class ExportImportService:
    """Service principal pour export/import de données"""
    
    def __init__(self):
        self.db = client.booktime
        self.supported_formats = ['json', 'csv', 'excel', 'full_backup']
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
    async def export_user_data(self, user_id: str, options: ExportOptions) -> Dict:
        """
        Exporte les données utilisateur selon les options spécifiées
        
        Args:
            user_id: ID de l'utilisateur
            options: Options d'export
            
        Returns:
            Dict avec données exportées et métadonnées
        """
        try:
            logger.info(f"Début export pour utilisateur {user_id}, format: {options.format_type}")
            
            # 1. Récupérer les données utilisateur
            user_data = await self._gather_user_data(user_id, options)
            
            # 2. Formater selon le type d'export
            if options.format_type == 'json':
                export_result = await self._export_json(user_data, options)
            elif options.format_type == 'csv':
                export_result = await self._export_csv(user_data, options)
            elif options.format_type == 'excel':
                export_result = await self._export_excel(user_data, options)
            elif options.format_type == 'full_backup':
                export_result = await self._export_full_backup(user_data, options)
            else:
                raise ValueError(f"Format non supporté: {options.format_type}")
            
            # 3. Ajouter métadonnées d'export
            export_result.update({
                'export_metadata': {
                    'user_id': user_id,
                    'export_date': datetime.utcnow().isoformat(),
                    'format': options.format_type,
                    'options': options.__dict__,
                    'total_books': len(user_data.get('books', [])),
                    'version': '1.0'
                }
            })
            
            logger.info(f"Export terminé avec succès: {len(user_data.get('books', []))} livres")
            return export_result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {str(e)}")
            raise Exception(f"Erreur lors de l'export: {str(e)}")
    
    async def import_user_data(self, user_id: str, file_content: bytes, 
                             filename: str, options: Dict = None) -> ImportResult:
        """
        Importe des données dans la bibliothèque utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            file_content: Contenu du fichier
            filename: Nom du fichier
            options: Options d'import
            
        Returns:
            ImportResult avec détails de l'opération
        """
        try:
            logger.info(f"Début import pour utilisateur {user_id}, fichier: {filename}")
            
            # Vérifications préliminaires
            if len(file_content) > self.max_file_size:
                raise ValueError(f"Fichier trop volumineux (max {self.max_file_size // 1024 // 1024}MB)")
            
            # Détecter le format du fichier
            file_format = self._detect_file_format(filename, file_content)
            
            # Parser selon le format
            if file_format == 'json':
                books_data = await self._parse_json_import(file_content)
            elif file_format == 'csv':
                books_data = await self._parse_csv_import(file_content)
            elif file_format == 'excel':
                books_data = await self._parse_excel_import(file_content)
            elif file_format == 'goodreads':
                books_data = await self._parse_goodreads_csv(file_content)
            else:
                raise ValueError(f"Format de fichier non supporté: {file_format}")
            
            # Valider et nettoyer les données
            validated_books = await self._validate_import_data(books_data)
            
            # Détecter les doublons
            duplicates = await self._detect_duplicates(user_id, validated_books)
            
            # Importer les livres (en excluant les doublons si demandé)
            import_result = await self._import_books(user_id, validated_books, duplicates, options)
            
            logger.info(f"Import terminé: {import_result.imported_count} livres importés")
            return import_result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import: {str(e)}")
            return ImportResult(
                success=False,
                total_processed=0,
                imported_count=0,
                skipped_count=0,
                error_count=1,
                errors=[str(e)],
                duplicates=[],
                imported_books=[]
            )
    
    async def _gather_user_data(self, user_id: str, options: ExportOptions) -> Dict:
        """Rassemble toutes les données utilisateur à exporter"""
        data = {'user_id': user_id}
        
        # Livres (toujours inclus)
        books = list(self.db.books.find({"user_id": user_id}))
        # Convertir ObjectId en string pour JSON
        for book in books:
            book['_id'] = str(book['_id'])
        data['books'] = books
        
        # Métadonnées optionnelles
        if options.include_metadata:
            # Informations utilisateur
            user_info = self.db.users.find_one({"id": user_id})
            if user_info:
                user_info['_id'] = str(user_info['_id'])
                data['user_info'] = user_info
        
        if options.include_stats:
            # Statistiques
            stats = await self._calculate_export_stats(user_id)
            data['statistics'] = stats
        
        if options.include_reading_progress:
            # Progression de lecture détaillée
            progress = await self._get_reading_progress(user_id)
            data['reading_progress'] = progress
        
        if options.include_reviews:
            # Avis et notes détaillés
            reviews = await self._get_detailed_reviews(user_id)
            data['reviews'] = reviews
        
        return data
    
    async def _export_json(self, user_data: Dict, options: ExportOptions) -> Dict:
        """Exporte en format JSON"""
        return {
            'content': json.dumps(user_data, indent=2, ensure_ascii=False, default=str),
            'content_type': 'application/json',
            'filename': f"booktime_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    
    async def _export_csv(self, user_data: Dict, options: ExportOptions) -> Dict:
        """Exporte en format CSV"""
        books = user_data.get('books', [])
        
        # Définir les colonnes CSV
        fieldnames = [
            'title', 'author', 'category', 'status', 'rating', 'review',
            'current_page', 'total_pages', 'date_added', 'date_started', 
            'date_completed', 'original_language', 'reading_language',
            'cover_url', 'ol_key', 'saga_name', 'volume_number', 'auto_added'
        ]
        
        # Créer le CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for book in books:
            # Nettoyer les données pour CSV
            row = {}
            for field in fieldnames:
                value = book.get(field, '')
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif value is None:
                    value = ''
                row[field] = str(value)
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return {
            'content': csv_content.encode('utf-8'),
            'content_type': 'text/csv',
            'filename': f"booktime_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    
    async def _export_excel(self, user_data: Dict, options: ExportOptions) -> Dict:
        """Exporte en format Excel avec multiple feuilles"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Feuille Livres
            books_df = pd.DataFrame(user_data.get('books', []))
            if not books_df.empty:
                # Nettoyer les données
                books_df = books_df.drop(columns=['_id'], errors='ignore')
                books_df.to_excel(writer, sheet_name='Livres', index=False)
            
            # Feuille Statistiques
            if options.include_stats and 'statistics' in user_data:
                stats_df = pd.DataFrame([user_data['statistics']])
                stats_df.to_excel(writer, sheet_name='Statistiques', index=False)
            
            # Feuille Progression
            if options.include_reading_progress and 'reading_progress' in user_data:
                progress_df = pd.DataFrame(user_data['reading_progress'])
                if not progress_df.empty:
                    progress_df.to_excel(writer, sheet_name='Progression', index=False)
        
        excel_content = output.getvalue()
        output.close()
        
        return {
            'content': excel_content,
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'filename': f"booktime_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    
    async def _export_full_backup(self, user_data: Dict, options: ExportOptions) -> Dict:
        """Crée une sauvegarde complète en ZIP"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # JSON principal
            json_data = json.dumps(user_data, indent=2, ensure_ascii=False, default=str)
            zip_file.writestr('booktime_data.json', json_data)
            
            # CSV des livres
            csv_export = await self._export_csv(user_data, options)
            zip_file.writestr('books.csv', csv_export['content'])
            
            # Métadonnées d'export
            metadata = {
                'backup_date': datetime.utcnow().isoformat(),
                'user_id': user_data['user_id'],
                'total_books': len(user_data.get('books', [])),
                'booktime_version': '1.0',
                'export_options': options.__dict__
            }
            zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))
            
            # README
            readme_content = self._generate_backup_readme(user_data)
            zip_file.writestr('README.txt', readme_content)
        
        zip_content = zip_buffer.getvalue()
        zip_buffer.close()
        
        return {
            'content': zip_content,
            'content_type': 'application/zip',
            'filename': f"booktime_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        }
    
    def _detect_file_format(self, filename: str, content: bytes) -> str:
        """Détecte le format d'un fichier"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.json'):
            return 'json'
        elif filename_lower.endswith('.csv'):
            # Détecter si c'est un export Goodreads
            try:
                content_str = content.decode('utf-8')
                if 'goodreads' in content_str.lower() or 'Book Id' in content_str:
                    return 'goodreads'
                return 'csv'
            except:
                return 'csv'
        elif filename_lower.endswith(('.xlsx', '.xls')):
            return 'excel'
        elif filename_lower.endswith('.zip'):
            return 'backup'
        else:
            # Essayer de détecter par le contenu
            try:
                json.loads(content.decode('utf-8'))
                return 'json'
            except:
                return 'csv'  # Par défaut
    
    async def _parse_json_import(self, content: bytes) -> List[Dict]:
        """Parse un fichier JSON d'import"""
        try:
            data = json.loads(content.decode('utf-8'))
            
            # Si c'est un export BOOKTIME
            if isinstance(data, dict) and 'books' in data:
                return data['books']
            # Si c'est une liste de livres
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("Format JSON non reconnu")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Fichier JSON invalide: {str(e)}")
    
    async def _parse_csv_import(self, content: bytes) -> List[Dict]:
        """Parse un fichier CSV générique"""
        try:
            content_str = content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(content_str))
            
            books = []
            for row in reader:
                # Mapping des colonnes communes
                book = self._map_csv_row_to_book(row)
                if book:
                    books.append(book)
            
            return books
            
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du CSV: {str(e)}")
    
    async def _parse_goodreads_csv(self, content: bytes) -> List[Dict]:
        """Parse un export Goodreads CSV"""
        try:
            content_str = content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(content_str))
            
            books = []
            for row in reader:
                book = {
                    'title': row.get('Title', ''),
                    'author': row.get('Author', ''),
                    'rating': self._parse_rating(row.get('My Rating', '0')),
                    'review': row.get('My Review', ''),
                    'date_added': self._parse_date(row.get('Date Added', '')),
                    'date_started': self._parse_date(row.get('Date Read', '')),
                    'date_completed': self._parse_date(row.get('Date Read', '')),
                    'status': self._map_goodreads_status(row.get('Exclusive Shelf', '')),
                    'total_pages': self._parse_int(row.get('Number of Pages', '0')),
                    'cover_url': row.get('Book Id', ''),  # On pourrait récupérer l'image
                    'category': self._detect_category_from_title(row.get('Title', '')),
                    'source': 'goodreads_import'
                }
                
                if book['title'] and book['author']:
                    books.append(book)
            
            return books
            
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du fichier Goodreads: {str(e)}")
    
    async def _validate_import_data(self, books_data: List[Dict]) -> List[Dict]:
        """Valide et nettoie les données d'import"""
        validated_books = []
        
        for book in books_data:
            try:
                # Champs obligatoires
                if not book.get('title') or not book.get('author'):
                    continue
                
                # Nettoyer et valider les données
                validated_book = {
                    'title': str(book.get('title', '')).strip(),
                    'author': str(book.get('author', '')).strip(),
                    'category': self._validate_category(book.get('category', 'roman')),
                    'status': self._validate_status(book.get('status', 'to_read')),
                    'rating': max(0, min(5, self._parse_rating(book.get('rating', 0)))),
                    'review': str(book.get('review', '')).strip(),
                    'current_page': max(0, self._parse_int(book.get('current_page', 0))),
                    'total_pages': max(0, self._parse_int(book.get('total_pages', 0))),
                    'date_added': self._parse_date(book.get('date_added', None)),
                    'date_started': self._parse_date(book.get('date_started', None)),
                    'date_completed': self._parse_date(book.get('date_completed', None)),
                    'original_language': str(book.get('original_language', 'français')),
                    'reading_language': str(book.get('reading_language', 'français')),
                    'cover_url': str(book.get('cover_url', '')),
                    'ol_key': str(book.get('ol_key', '')),
                    'saga_name': str(book.get('saga_name', '')),
                    'volume_number': self._parse_int(book.get('volume_number', 0)),
                    'source': str(book.get('source', 'import')),
                    'imported_at': datetime.utcnow()
                }
                
                validated_books.append(validated_book)
                
            except Exception as e:
                logger.warning(f"Livre ignoré lors de la validation: {str(e)}")
                continue
        
        return validated_books
    
    async def _detect_duplicates(self, user_id: str, books: List[Dict]) -> List[Dict]:
        """Détecte les livres en doublon"""
        duplicates = []
        
        # Récupérer les livres existants
        existing_books = list(self.db.books.find({"user_id": user_id}))
        
        for book in books:
            # Vérifier les doublons par titre + auteur
            for existing in existing_books:
                if (self._normalize_text(book['title']) == self._normalize_text(existing.get('title', '')) and
                    self._normalize_text(book['author']) == self._normalize_text(existing.get('author', ''))):
                    duplicates.append({
                        'import_book': book,
                        'existing_book': existing,
                        'match_reason': 'title_author'
                    })
                    break
        
        return duplicates
    
    async def _import_books(self, user_id: str, books: List[Dict], 
                          duplicates: List[Dict], options: Dict = None) -> ImportResult:
        """Importe les livres validés"""
        options = options or {}
        skip_duplicates = options.get('skip_duplicates', True)
        
        imported_books = []
        skipped_books = []
        errors = []
        
        # Livres à ignorer (doublons)
        duplicate_titles = {dup['import_book']['title'] for dup in duplicates}
        
        for book in books:
            try:
                # Ignorer les doublons si demandé
                if skip_duplicates and book['title'] in duplicate_titles:
                    skipped_books.append(book)
                    continue
                
                # Ajouter l'ID utilisateur
                book['user_id'] = user_id
                book['_id'] = str(uuid.uuid4())
                
                # Insérer en base
                result = self.db.books.insert_one(book)
                if result.inserted_id:
                    imported_books.append(book)
                else:
                    errors.append(f"Échec insertion: {book['title']}")
                    
            except Exception as e:
                errors.append(f"Erreur {book['title']}: {str(e)}")
        
        return ImportResult(
            success=len(errors) == 0,
            total_processed=len(books),
            imported_count=len(imported_books),
            skipped_count=len(skipped_books),
            error_count=len(errors),
            errors=errors,
            duplicates=duplicates,
            imported_books=imported_books
        )
    
    # Méthodes utilitaires
    def _normalize_text(self, text: str) -> str:
        """Normalise un texte pour comparaison"""
        return text.lower().strip().replace(' ', '')
    
    def _parse_rating(self, rating) -> float:
        """Parse une note en float"""
        try:
            return float(rating)
        except:
            return 0.0
    
    def _parse_int(self, value) -> int:
        """Parse un entier"""
        try:
            return int(float(value))
        except:
            return 0
    
    def _parse_date(self, date_str) -> Optional[datetime]:
        """Parse une date depuis différents formats"""
        if not date_str:
            return None
        
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except:
                continue
        
        return None
    
    def _validate_category(self, category: str) -> str:
        """Valide une catégorie"""
        valid_categories = ['roman', 'bd', 'manga']
        category = category.lower().strip()
        return category if category in valid_categories else 'roman'
    
    def _validate_status(self, status: str) -> str:
        """Valide un statut"""
        valid_statuses = ['to_read', 'reading', 'completed']
        status = status.lower().strip().replace(' ', '_')
        return status if status in valid_statuses else 'to_read'
    
    def _map_goodreads_status(self, shelf: str) -> str:
        """Mappe un statut Goodreads vers BOOKTIME"""
        mapping = {
            'to-read': 'to_read',
            'currently-reading': 'reading',
            'read': 'completed'
        }
        return mapping.get(shelf.lower(), 'to_read')
    
    def _detect_category_from_title(self, title: str) -> str:
        """Détecte la catégorie depuis le titre"""
        title_lower = title.lower()
        
        manga_keywords = ['manga', 'tome', 'one piece', 'naruto', 'dragon ball']
        bd_keywords = ['astérix', 'tintin', 'lucky luke', 'bd', 'bande dessinée']
        
        for keyword in manga_keywords:
            if keyword in title_lower:
                return 'manga'
        
        for keyword in bd_keywords:
            if keyword in title_lower:
                return 'bd'
        
        return 'roman'
    
    def _map_csv_row_to_book(self, row: Dict) -> Optional[Dict]:
        """Mappe une ligne CSV vers un livre"""
        # Mapping flexible des colonnes
        title = row.get('title') or row.get('Title') or row.get('TITLE')
        author = row.get('author') or row.get('Author') or row.get('AUTHOR')
        
        if not title or not author:
            return None
        
        return {
            'title': title,
            'author': author,
            'category': row.get('category', 'roman'),
            'status': row.get('status', 'to_read'),
            'rating': self._parse_rating(row.get('rating', 0)),
            'review': row.get('review', ''),
            'current_page': self._parse_int(row.get('current_page', 0)),
            'total_pages': self._parse_int(row.get('total_pages', 0)),
            'cover_url': row.get('cover_url', ''),
            'source': 'csv_import'
        }
    
    async def _calculate_export_stats(self, user_id: str) -> Dict:
        """Calcule les statistiques d'export"""
        books = list(self.db.books.find({"user_id": user_id}))
        
        total_books = len(books)
        if total_books == 0:
            return {}
        
        stats = {
            'total_books': total_books,
            'by_category': {},
            'by_status': {},
            'by_rating': {},
            'reading_stats': {
                'total_pages_read': 0,
                'average_rating': 0,
                'completion_rate': 0
            }
        }
        
        # Analyser les livres
        ratings = []
        completed_books = 0
        total_pages = 0
        
        for book in books:
            # Par catégorie
            category = book.get('category', 'unknown')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Par statut
            status = book.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Par note
            rating = book.get('rating', 0)
            if rating > 0:
                ratings.append(rating)
                stats['by_rating'][str(rating)] = stats['by_rating'].get(str(rating), 0) + 1
            
            # Stats de lecture
            if status == 'completed':
                completed_books += 1
                pages = book.get('total_pages', 0)
                if pages > 0:
                    total_pages += pages
        
        # Calculer les moyennes
        stats['reading_stats']['completion_rate'] = completed_books / total_books
        stats['reading_stats']['average_rating'] = sum(ratings) / len(ratings) if ratings else 0
        stats['reading_stats']['total_pages_read'] = total_pages
        
        return stats
    
    async def _get_reading_progress(self, user_id: str) -> List[Dict]:
        """Récupère la progression de lecture détaillée"""
        books = list(self.db.books.find({"user_id": user_id}))
        
        progress = []
        for book in books:
            if book.get('status') in ['reading', 'completed']:
                current = book.get('current_page', 0)
                total = book.get('total_pages', 0)
                
                if total > 0:
                    progress.append({
                        'title': book.get('title'),
                        'author': book.get('author'),
                        'current_page': current,
                        'total_pages': total,
                        'progress_percent': (current / total) * 100,
                        'status': book.get('status'),
                        'date_started': book.get('date_started'),
                        'date_completed': book.get('date_completed')
                    })
        
        return progress
    
    async def _get_detailed_reviews(self, user_id: str) -> List[Dict]:
        """Récupère les avis détaillés"""
        books = list(self.db.books.find({
            "user_id": user_id,
            "$or": [
                {"rating": {"$gt": 0}},
                {"review": {"$ne": ""}}
            ]
        }))
        
        reviews = []
        for book in books:
            if book.get('rating', 0) > 0 or book.get('review', ''):
                reviews.append({
                    'title': book.get('title'),
                    'author': book.get('author'),
                    'rating': book.get('rating', 0),
                    'review': book.get('review', ''),
                    'date_completed': book.get('date_completed'),
                    'category': book.get('category')
                })
        
        return reviews
    
    def _generate_backup_readme(self, user_data: Dict) -> str:
        """Génère un README pour la sauvegarde"""
        total_books = len(user_data.get('books', []))
        backup_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""
BOOKTIME - Sauvegarde Complète
==============================

Date de sauvegarde: {backup_date}
Utilisateur: {user_data['user_id']}
Total livres: {total_books}

Contenu du fichier:
------------------
- booktime_data.json: Données complètes en format JSON
- books.csv: Liste des livres en format CSV
- metadata.json: Métadonnées de la sauvegarde
- README.txt: Ce fichier

Format des données:
------------------
Les données sont compatibles avec BOOKTIME et peuvent être
réimportées via l'interface d'import.

Pour restaurer:
--------------
1. Connectez-vous à BOOKTIME
2. Allez dans Paramètres > Import/Export
3. Sélectionnez "Importer des données"
4. Choisissez le fichier booktime_data.json ou books.csv

Support:
--------
Pour toute question, consultez la documentation BOOKTIME
ou contactez le support.

BOOKTIME - Votre bibliothèque personnelle
        """.strip()