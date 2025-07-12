import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://0b242f2a-081a-491a-bb79-9c027627f29c.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class SeriesLibraryAPITest(unittest.TestCase):
    """Test suite for the Series Library API endpoints"""

    def setUp(self):
        """Setup for each test"""
        # Register a test user for authentication
        self.user_data = {
            "first_name": "Test",
            "last_name": "SeriesLibrary"
        }
        
        # Register and login
        response = requests.post(f"{API_URL}/auth/register", json=self.user_data)
        if response.status_code == 400:  # User already exists
            response = requests.post(f"{API_URL}/auth/login", json=self.user_data)
        
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test series data
        self.test_series_data = {
            "series_name": "Harry Potter",
            "authors": ["J.K. Rowling"],
            "category": "roman",
            "total_volumes": 7,
            "volumes": [
                {"volume_number": 1, "volume_title": "Harry Potter à l'École des Sorciers", "is_read": False},
                {"volume_number": 2, "volume_title": "Harry Potter et la Chambre des Secrets", "is_read": False},
                {"volume_number": 3, "volume_title": "Harry Potter et le Prisonnier d'Azkaban", "is_read": False},
                {"volume_number": 4, "volume_title": "Harry Potter et la Coupe de Feu", "is_read": False},
                {"volume_number": 5, "volume_title": "Harry Potter et l'Ordre du Phénix", "is_read": False},
                {"volume_number": 6, "volume_title": "Harry Potter et le Prince de Sang-Mêlé", "is_read": False},
                {"volume_number": 7, "volume_title": "Harry Potter et les Reliques de la Mort", "is_read": False}
            ],
            "series_status": "to_read",
            "description_fr": "La célèbre saga du jeune sorcier Harry Potter qui découvre qu'il est un sorcier et intègre l'école de sorcellerie Poudlard.",
            "cover_image_url": "https://example.com/harry-potter.jpg",
            "first_published": "1997",
            "last_published": "2007",
            "publisher": "Gallimard"
        }
        
        # Series IDs to be used/cleaned up during testing
        self.series_ids_to_delete = []

    def tearDown(self):
        """Clean up after each test"""
        # Delete any series created during testing
        for series_id in self.series_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/series/library/{series_id}", headers=self.headers)
            except:
                pass

    def test_add_series_to_library(self):
        """Test adding a series to the library"""
        # Generate a unique series name to avoid conflicts
        unique_series_name = f"Test Series {uuid.uuid4().hex[:8]}"
        test_data = self.test_series_data.copy()
        test_data["series_name"] = unique_series_name
        
        # Add the series to the library
        response = requests.post(f"{API_URL}/series/library", json=test_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("series_id", data)
        self.assertIn("message", data)
        self.assertIn("series", data)
        
        # Add the series ID to the cleanup list
        self.series_ids_to_delete.append(data["series_id"])
        
        # Check that the series was created with the correct data
        series = data["series"]
        self.assertEqual(series["series_name"], unique_series_name)
        self.assertEqual(series["authors"], test_data["authors"])
        self.assertEqual(series["category"], test_data["category"])
        self.assertEqual(series["total_volumes"], test_data["total_volumes"])
        self.assertEqual(len(series["volumes"]), len(test_data["volumes"]))
        self.assertEqual(series["series_status"], test_data["series_status"])
        self.assertEqual(series["description_fr"], test_data["description_fr"])
        self.assertEqual(series["cover_image_url"], test_data["cover_image_url"])
        self.assertEqual(series["first_published"], test_data["first_published"])
        self.assertEqual(series["last_published"], test_data["last_published"])
        self.assertEqual(series["publisher"], test_data["publisher"])
        
        print(f"✅ Add series to library endpoint working, created series '{unique_series_name}'")
        
        # Test adding a series with missing required fields
        invalid_data = {
            "series_name": "",
            "authors": [],
            "category": "roman"
        }
        
        response = requests.post(f"{API_URL}/series/library", json=invalid_data, headers=self.headers)
        self.assertNotEqual(response.status_code, 200)  # Could be 400 or 422 depending on validation
        
        print("✅ Add series with missing data fails as expected")
        
        # Test adding a duplicate series
        response = requests.post(f"{API_URL}/series/library", json=test_data, headers=self.headers)
        self.assertEqual(response.status_code, 409)
        
        print("✅ Add duplicate series fails as expected")

    def test_get_user_series_library(self):
        """Test retrieving all series from the library"""
        # First add a series to the library
        unique_series_name = f"Test Series {uuid.uuid4().hex[:8]}"
        test_data = self.test_series_data.copy()
        test_data["series_name"] = unique_series_name
        
        response = requests.post(f"{API_URL}/series/library", json=test_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.series_ids_to_delete.append(data["series_id"])
        
        # Get all series from the library
        response = requests.get(f"{API_URL}/series/library", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertIn("series", data)
        self.assertIn("total_count", data)
        
        # Check that our test series is in the list
        found = False
        for series in data["series"]:
            if series["series_name"] == unique_series_name:
                found = True
                self.assertEqual(series["category"], test_data["category"])
                self.assertEqual(series["authors"], test_data["authors"])
                self.assertEqual(series["series_status"], test_data["series_status"])
                self.assertEqual(len(series["volumes"]), len(test_data["volumes"]))
                break
        
        self.assertTrue(found, f"Test series '{unique_series_name}' should be in the library")
        
        print(f"✅ Get user series library endpoint working, found {data['total_count']} series")
        
        # Test filtering by category
        response = requests.get(f"{API_URL}/series/library?category=roman", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all series are of category "roman"
        for series in data["series"]:
            self.assertEqual(series["category"], "roman")
        
        print(f"✅ Filter by category 'roman' working, found {len(data['series'])} series")
        
        # Test filtering by status
        response = requests.get(f"{API_URL}/series/library?status=to_read", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all series have status "to_read"
        for series in data["series"]:
            self.assertEqual(series["series_status"], "to_read")
        
        print(f"✅ Filter by status 'to_read' working, found {len(data['series'])} series")

    def test_toggle_volume_read_status(self):
        """Test toggling the read status of a volume"""
        # First add a series to the library
        unique_series_name = f"Test Series {uuid.uuid4().hex[:8]}"
        test_data = self.test_series_data.copy()
        test_data["series_name"] = unique_series_name
        
        response = requests.post(f"{API_URL}/series/library", json=test_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        series_id = data["series_id"]
        self.series_ids_to_delete.append(series_id)
        
        # Toggle the read status of volume 1 to true
        response = requests.put(f"{API_URL}/series/library/{series_id}/volume/1?is_read=true", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("completion_percentage", data)
        self.assertIn("series_status", data)
        self.assertIn("message", data)
        
        # Check that the completion percentage is correct (1/7 = ~14%)
        self.assertAlmostEqual(data["completion_percentage"], 14, delta=1)
        
        # Check that the series status is now "reading"
        self.assertEqual(data["series_status"], "reading")
        
        print("✅ Toggle volume read status endpoint working (mark as read)")
        
        # Get the series to verify the volume status
        response = requests.get(f"{API_URL}/series/library", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find our test series
        found = False
        for series in data["series"]:
            if series["series_name"] == unique_series_name:
                found = True
                # Check that volume 1 is marked as read
                volume_1 = next((v for v in series["volumes"] if v["volume_number"] == 1), None)
                self.assertIsNotNone(volume_1)
                self.assertTrue(volume_1["is_read"])
                # Check that other volumes are not read
                for v in series["volumes"]:
                    if v["volume_number"] != 1:
                        self.assertFalse(v["is_read"])
                break
        
        self.assertTrue(found, f"Test series '{unique_series_name}' should be in the library")
        
        # Toggle the read status of volume 1 back to false
        response = requests.put(f"{API_URL}/series/library/{series_id}/volume/1?is_read=false", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the completion percentage is now 0%
        self.assertEqual(data["completion_percentage"], 0)
        
        # Check that the series status is back to "to_read"
        self.assertEqual(data["series_status"], "to_read")
        
        print("✅ Toggle volume read status endpoint working (mark as unread)")
        
        # Mark all volumes as read
        for i in range(1, 8):
            response = requests.put(f"{API_URL}/series/library/{series_id}/volume/{i}?is_read=true", headers=self.headers)
            self.assertEqual(response.status_code, 200)
        
        # Get the series to verify all volumes are read
        response = requests.get(f"{API_URL}/series/library", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find our test series
        found = False
        for series in data["series"]:
            if series["series_name"] == unique_series_name:
                found = True
                # Check that all volumes are marked as read
                for v in series["volumes"]:
                    self.assertTrue(v["is_read"])
                # Check that the completion percentage is 100%
                self.assertEqual(series["completion_percentage"], 100)
                # Check that the series status is "completed"
                self.assertEqual(series["series_status"], "completed")
                break
        
        self.assertTrue(found, f"Test series '{unique_series_name}' should be in the library")
        
        print("✅ Series status automatically updated to 'completed' when all volumes are read")
        
        # Test with invalid series ID
        fake_id = str(uuid.uuid4())
        response = requests.put(f"{API_URL}/series/library/{fake_id}/volume/1?is_read=true", headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        print("✅ Toggle volume with invalid series ID fails as expected")
        
        # Test with invalid volume number
        response = requests.put(f"{API_URL}/series/library/{series_id}/volume/999?is_read=true", headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        print("✅ Toggle volume with invalid volume number fails as expected")

    def test_update_series_library(self):
        """Test updating a series in the library"""
        # First add a series to the library
        unique_series_name = f"Test Series {uuid.uuid4().hex[:8]}"
        test_data = self.test_series_data.copy()
        test_data["series_name"] = unique_series_name
        
        response = requests.post(f"{API_URL}/series/library", json=test_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        series_id = data["series_id"]
        self.series_ids_to_delete.append(series_id)
        
        # Update the series
        update_data = {
            "series_status": "reading",
            "description_fr": "Description mise à jour pour les tests"
        }
        
        response = requests.put(f"{API_URL}/series/library/{series_id}", json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("message", data)
        self.assertIn("series", data)
        
        # Check that the series was updated correctly
        series = data["series"]
        self.assertEqual(series["series_status"], update_data["series_status"])
        self.assertEqual(series["description_fr"], update_data["description_fr"])
        
        print("✅ Update series library endpoint working")
        
        # Test with invalid series ID
        fake_id = str(uuid.uuid4())
        response = requests.put(f"{API_URL}/series/library/{fake_id}", json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        print("✅ Update series with invalid ID fails as expected")

    def test_delete_series_from_library(self):
        """Test deleting a series from the library"""
        # First add a series to the library
        unique_series_name = f"Test Series {uuid.uuid4().hex[:8]}"
        test_data = self.test_series_data.copy()
        test_data["series_name"] = unique_series_name
        
        response = requests.post(f"{API_URL}/series/library", json=test_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        series_id = data["series_id"]
        
        # Delete the series
        response = requests.delete(f"{API_URL}/series/library/{series_id}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("message", data)
        
        # Verify the series was deleted
        response = requests.get(f"{API_URL}/series/library", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that our test series is not in the list
        for series in data["series"]:
            self.assertNotEqual(series["series_name"], unique_series_name)
        
        print("✅ Delete series from library endpoint working")
        
        # Test with invalid series ID
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{API_URL}/series/library/{fake_id}", headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        print("✅ Delete series with invalid ID fails as expected")

    def test_integration_full_workflow(self):
        """Test the full workflow: add series, mark volumes as read, check progress, delete series"""
        # Generate unique series names for different categories
        roman_series_name = f"Roman Series {uuid.uuid4().hex[:8]}"
        bd_series_name = f"BD Series {uuid.uuid4().hex[:8]}"
        manga_series_name = f"Manga Series {uuid.uuid4().hex[:8]}"
        
        # Create test data for each category
        roman_data = self.test_series_data.copy()
        roman_data["series_name"] = roman_series_name
        roman_data["category"] = "roman"
        
        bd_data = self.test_series_data.copy()
        bd_data["series_name"] = bd_series_name
        bd_data["category"] = "bd"
        bd_data["volumes"] = bd_data["volumes"][:5]  # Fewer volumes for BD
        bd_data["total_volumes"] = 5
        
        manga_data = self.test_series_data.copy()
        manga_data["series_name"] = manga_series_name
        manga_data["category"] = "manga"
        manga_data["volumes"] = [
            {"volume_number": i, "volume_title": f"{manga_series_name} Tome {i}", "is_read": False}
            for i in range(1, 11)  # 10 volumes for manga
        ]
        manga_data["total_volumes"] = 10
        
        # Add all series to the library
        series_ids = {}
        
        # Add roman series
        response = requests.post(f"{API_URL}/series/library", json=roman_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        series_ids["roman"] = data["series_id"]
        self.series_ids_to_delete.append(data["series_id"])
        
        # Add BD series
        response = requests.post(f"{API_URL}/series/library", json=bd_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        series_ids["bd"] = data["series_id"]
        self.series_ids_to_delete.append(data["series_id"])
        
        # Add manga series
        response = requests.post(f"{API_URL}/series/library", json=manga_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        series_ids["manga"] = data["series_id"]
        self.series_ids_to_delete.append(data["series_id"])
        
        print("✅ Added series of all categories to the library")
        
        # Mark some volumes as read for each series
        # Roman: 3/7 volumes read
        for i in range(1, 4):
            response = requests.put(f"{API_URL}/series/library/{series_ids['roman']}/volume/{i}?is_read=true", headers=self.headers)
            self.assertEqual(response.status_code, 200)
        
        # BD: 2/5 volumes read
        for i in range(1, 3):
            response = requests.put(f"{API_URL}/series/library/{series_ids['bd']}/volume/{i}?is_read=true", headers=self.headers)
            self.assertEqual(response.status_code, 200)
        
        # Manga: 5/10 volumes read
        for i in range(1, 6):
            response = requests.put(f"{API_URL}/series/library/{series_ids['manga']}/volume/{i}?is_read=true", headers=self.headers)
            self.assertEqual(response.status_code, 200)
        
        print("✅ Marked volumes as read for all series")
        
        # Get all series and check progress
        response = requests.get(f"{API_URL}/series/library", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find our test series and check their progress
        for series in data["series"]:
            if series["series_name"] == roman_series_name:
                # Roman: 3/7 volumes read (~43%)
                self.assertAlmostEqual(series["completion_percentage"], 43, delta=1)
                self.assertEqual(series["series_status"], "reading")
            elif series["series_name"] == bd_series_name:
                # BD: 2/5 volumes read (40%)
                self.assertEqual(series["completion_percentage"], 40)
                self.assertEqual(series["series_status"], "reading")
            elif series["series_name"] == manga_series_name:
                # Manga: 5/10 volumes read (50%)
                self.assertEqual(series["completion_percentage"], 50)
                self.assertEqual(series["series_status"], "reading")
        
        print("✅ Progress correctly calculated for all series")
        
        # Mark all volumes as read for the manga series
        for i in range(6, 11):
            response = requests.put(f"{API_URL}/series/library/{series_ids['manga']}/volume/{i}?is_read=true", headers=self.headers)
            self.assertEqual(response.status_code, 200)
        
        # Get the manga series and check it's marked as completed
        response = requests.get(f"{API_URL}/series/library?category=manga", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        for series in data["series"]:
            if series["series_name"] == manga_series_name:
                self.assertEqual(series["completion_percentage"], 100)
                self.assertEqual(series["series_status"], "completed")
        
        print("✅ Series automatically marked as completed when all volumes are read")
        
        # Delete all series
        for series_id in series_ids.values():
            response = requests.delete(f"{API_URL}/series/library/{series_id}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            # Remove from cleanup list since we've already deleted it
            if series_id in self.series_ids_to_delete:
                self.series_ids_to_delete.remove(series_id)
        
        # Verify all series were deleted
        response = requests.get(f"{API_URL}/series/library", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        for series in data["series"]:
            self.assertNotIn(series["series_name"], [roman_series_name, bd_series_name, manga_series_name])
        
        print("✅ Successfully deleted all test series")
        print("✅ Full integration workflow completed successfully")

if __name__ == "__main__":
    unittest.main(verbosity=2)