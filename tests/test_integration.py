import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import json


class TestReceiptIntegration:
    """Integration test class for real receipt scraping"""
    
    @pytest.fixture
    def valid_api_key(self):
        """Valid API key for tests"""
        return "cbd28701-1148-4853-bcd1-0d807ee96764"
    
    @pytest.fixture
    def real_receipt_url_1(self):
        """Real receipt URL from url1.txt"""
        with open("url1.txt", "r") as f:
            return f.read().strip()
    
    @pytest.fixture
    def real_receipt_url_2(self):
        """Real receipt URL from url2.txt"""
        with open("url2.txt", "r") as f:
            return f.read().strip()
    
    @pytest.fixture
    def app_client(self):
        """FastAPI test client"""
        from src.main import app
        return TestClient(app)
    
    @pytest.fixture
    def mock_api_keys(self, valid_api_key):
        """Mock API keys file to use test key"""
        mock_keys = [valid_api_key, "test-key-2", "test-key-3"]
        
        async def mock_load_keys():
            return mock_keys
        
        return mock_load_keys
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_receipt_scraping_url1(self, app_client, valid_api_key, real_receipt_url_1, mock_api_keys):
        """Test scraping real receipt from url1.txt"""
        
        with patch("src.auth.load_api_keys", mock_api_keys):
            response = app_client.post(
                "/api/receipt",
                json={"url": real_receipt_url_1},
                headers={"x-api-key": valid_api_key}
            )
            
            # Check response status
            assert response.status_code == 200
            
            data = response.json()
            
            # Check response structure
            assert data["status"] == "success"
            assert data["url"] == real_receipt_url_1
            assert "processed_at" in data
            assert "data" in data
            
            # Check scraped data structure
            scraped_data = data["data"]
            assert "status_racuna" in scraped_data
            assert "zahtev_za_fiskalizaciju_racuna" in scraped_data
            assert "rezultat_fiskalizacije_racuna" in scraped_data
            
            # Print scraped data for inspection
            print("\n=== SCRAPED DATA FROM URL1 ===")
            print(json.dumps(scraped_data, indent=2, ensure_ascii=False))
            
            # Basic validation that we got some data
            zahtev = scraped_data["zahtev_za_fiskalizaciju_racuna"]
            assert len(zahtev) > 0, "Should have extracted some fiscalization request data"
    
    @pytest.mark.asyncio
    @pytest.mark.integration 
    async def test_real_receipt_scraping_url2(self, app_client, valid_api_key, real_receipt_url_2, mock_api_keys):
        """Test scraping real receipt from url2.txt"""
        
        with patch("src.auth.load_api_keys", mock_api_keys):
            response = app_client.post(
                "/api/receipt",
                json={"url": real_receipt_url_2},
                headers={"x-api-key": valid_api_key}
            )
            
            # Check response status
            assert response.status_code == 200
            
            data = response.json()
            
            # Check response structure
            assert data["status"] == "success"
            assert data["url"] == real_receipt_url_2
            assert "processed_at" in data
            assert "data" in data
            
            # Check scraped data structure
            scraped_data = data["data"]
            assert "status_racuna" in scraped_data
            assert "zahtev_za_fiskalizaciju_racuna" in scraped_data
            assert "rezultat_fiskalizacije_racuna" in scraped_data
            
            # Print scraped data for inspection
            print("\n=== SCRAPED DATA FROM URL2 ===")
            print(json.dumps(scraped_data, indent=2, ensure_ascii=False))
            
            # Basic validation that we got some data
            zahtev = scraped_data["zahtev_za_fiskalizaciju_racuna"]
            assert len(zahtev) > 0, "Should have extracted some fiscalization request data"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_scraper_transliteration_quality(self, app_client, valid_api_key, real_receipt_url_1, mock_api_keys):
        """Test that transliteration produces clean English keys"""
        
        with patch("src.auth.load_api_keys", mock_api_keys):
            response = app_client.post(
                "/api/receipt",
                json={"url": real_receipt_url_1},
                headers={"x-api-key": valid_api_key}
            )
            
            assert response.status_code == 200
            scraped_data = response.json()["data"]
            
            # Check that all keys are properly transliterated (lowercase, no cyrillic, underscores)
            def check_keys(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        # Key should be lowercase, contain only a-z, 0-9, and underscores
                        assert key.islower(), f"Key '{key}' at {path} should be lowercase"
                        assert all(c.isalnum() or c == '_' for c in key), f"Key '{key}' at {path} contains invalid characters"
                        assert not any(ord(c) > 127 for c in key), f"Key '{key}' at {path} contains non-ASCII characters"
                        
                        check_keys(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_keys(item, f"{path}[{i}]")
            
            check_keys(scraped_data)
            print("\n✅ All keys are properly transliterated!")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_network_error_handling(self, app_client, valid_api_key, mock_api_keys):
        """Test handling of network errors with invalid URL"""
        
        invalid_url = "https://suf.purs.gov.rs/v/?vl=INVALID_URL_PARAMETER"
        
        with patch("src.auth.load_api_keys", mock_api_keys):
            response = app_client.post(
                "/api/receipt",
                json={"url": invalid_url},
                headers={"x-api-key": valid_api_key}
            )
            
            # Should handle error gracefully
            assert response.status_code in [400, 500]  # Either validation or processing error
            
            data = response.json()
            assert "detail" in data
            print(f"\n✅ Error handled gracefully: {data['detail']}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_performance_timing(self, app_client, valid_api_key, real_receipt_url_1, mock_api_keys):
        """Test that scraping completes within reasonable time"""
        import time
        
        with patch("src.auth.load_api_keys", mock_api_keys):
            start_time = time.time()
            
            response = app_client.post(
                "/api/receipt",
                json={"url": real_receipt_url_1},
                headers={"x-api-key": valid_api_key}
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            assert response.status_code == 200
            assert processing_time < 30.0, f"Processing took too long: {processing_time:.2f}s"
            
            print(f"\n✅ Processing completed in {processing_time:.2f} seconds")