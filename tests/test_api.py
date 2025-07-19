import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
import json


class TestReceiptAPI:
    """Test class for /api/receipt endpoint"""
    
    @pytest.fixture
    def valid_api_key(self):
        """Valid API key for tests"""
        return "cbd28701-1148-4853-bcd1-0d807ee96764"
    
    @pytest.fixture
    def valid_receipt_url(self):
        """Valid URL for receipt"""
        return "https://suf.purs.gov.rs/v/?vl=A0dMN1hUNjNOR0w3WFQ2M066LwAAbiwAAAwkTwgAAAAAAAABmBxSTwgAAAwxMDoxMDkyNjI5NzJ9ge8%2BdWX2LERh8fQ2E4ng9q0yXzCzGi%2Bz0Dl3F%2BmXjsatfZHjPSa8q2agv2MD%2BL2JkxoUHtqC6xx0L5VdsEt6ZbzlOc%2B0Nyap9tUnnyEogRlJoHw88lAIOlBvtHxUciTZ4CU7mvhcAc4HbaDIx%2BDZpfYGJO3qshNnT5%2BkK6Scw01Li%2BPuqR4m6QRmpPY4%2Bi7kwQ9pH8%2B2xTCi%2BPdXQ9u1riLDW3DToNvIKEfUsA1iASQHEFf%2BVK%2F4yGYx2efhTSqsUwLxmFnwyaRRp7h8W%2F2GdlblLSEkv%2FvYUpBPfXWUBgF%2FjYLHxgbX9q1JZzMokfFvPWPHuLnJj0oNdgaC15sNUjpbQy5Qpxzl1gX7tmoi8dotGNBdDjOyORZjsS0da%2BLpWC6NMgknlY5OR6UNums9oPj6wdVwGLDBbufwinSdcJXSHFuHE%2F01pTJR%2F6uKuYxg3J4c78k%2BZOC%2B59%2BB%2FXEDicIWDFYhuuR%2FpivPeYaGvyooTuteQTzw9zuXGuUxMqM4EkMmSsPUPvB%2BITKGSnRhHId0REWITTRMun1sJBw%2FVbfaVUzAcTkmnnJ12HSQskcJh3CEHz5stextmQ7jT%2Bi8hfXCnWGBnyDMC3ZEtTUuCuBk8pDW7fpnP6YD87hO4aHeEEACw%2BMj9WSXfyNkuDSofRIQKRaRMASiniVUiAo%2FW%2BI5SylFpvvWQ3hD4Ld1lzk%3D"
    
    @pytest.fixture
    def app_client(self):
        """FastAPI test client"""
        from src.main import app
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth_middleware(self, valid_api_key):
        """Mock auth middleware that always passes"""
        async def mock_validate(api_key):
            if api_key == valid_api_key:
                return True
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return mock_validate
    
    @pytest.mark.asyncio
    async def test_valid_request_should_return_success(self, app_client, valid_api_key, valid_receipt_url, mock_auth_middleware):
        """Test that valid request returns successful response"""
        with patch("src.auth.validate_api_key", mock_auth_middleware):
            response = app_client.post(
                "/api/receipt",
                json={"url": valid_receipt_url},
                headers={"x-api-key": valid_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["url"] == valid_receipt_url
            assert "processed_at" in data
    
    @pytest.mark.asyncio
    async def test_missing_api_key_should_return_401(self, app_client, valid_receipt_url):
        """Test that missing API key returns 401"""
        response = app_client.post(
            "/api/receipt",
            json={"url": valid_receipt_url}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "x-api-key" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_should_return_401(self, app_client, valid_receipt_url, mock_auth_middleware):
        """Test that invalid API key returns 401"""
        with patch("src.auth.validate_api_key", mock_auth_middleware):
            response = app_client.post(
                "/api/receipt",
                json={"url": valid_receipt_url},
                headers={"x-api-key": "invalid-key"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid API key" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_missing_url_should_return_400(self, app_client, valid_api_key, mock_auth_middleware):
        """Test that missing URL returns 400"""
        with patch("src.auth.validate_api_key", mock_auth_middleware):
            response = app_client.post(
                "/api/receipt",
                json={},
                headers={"x-api-key": valid_api_key}
            )
            
            assert response.status_code == 422  # FastAPI validation error
    
    @pytest.mark.asyncio
    async def test_empty_url_should_return_400(self, app_client, valid_api_key, mock_auth_middleware):
        """Test that empty URL returns 400"""
        with patch("src.auth.validate_api_key", mock_auth_middleware):
            response = app_client.post(
                "/api/receipt",
                json={"url": ""},
                headers={"x-api-key": valid_api_key}
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "url" in str(data["detail"]).lower()
    
    @pytest.mark.asyncio
    async def test_invalid_url_format_should_return_400(self, app_client, valid_api_key, mock_auth_middleware):
        """Test that invalid URL format returns 400"""
        with patch("src.auth.validate_api_key", mock_auth_middleware):
            response = app_client.post(
                "/api/receipt",
                json={"url": "not-a-valid-url"},
                headers={"x-api-key": valid_api_key}
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "url" in str(data["detail"]).lower()
    
    @pytest.mark.asyncio
    async def test_non_purs_domain_should_return_400(self, app_client, valid_api_key, mock_auth_middleware):
        """Test that URL not from suf.purs.gov.rs domain returns 400"""
        with patch("src.auth.validate_api_key", mock_auth_middleware):
            response = app_client.post(
                "/api/receipt",
                json={"url": "https://example.com/some/path"},
                headers={"x-api-key": valid_api_key}
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "suf.purs.gov.rs" in str(data["detail"])
    
    @pytest.mark.asyncio
    async def test_malformed_json_should_return_400(self, app_client, valid_api_key):
        """Test that malformed JSON returns 400"""
        response = app_client.post(
            "/api/receipt",
            data="invalid json",
            headers={
                "x-api-key": valid_api_key,
                "content-type": "application/json"
            }
        )
        
        assert response.status_code == 422  # FastAPI validation error
    
    @pytest.mark.asyncio
    async def test_request_logging(self, app_client, valid_api_key, valid_receipt_url, mock_auth_middleware):
        """Test that requests are properly logged"""
        with patch("src.auth.validate_api_key", mock_auth_middleware):
            with patch("logging.Logger.info") as mock_logger:
                response = app_client.post(
                    "/api/receipt",
                    json={"url": valid_receipt_url},
                    headers={"x-api-key": valid_api_key}
                )
                
                assert response.status_code == 200
                # Check that logging was called
                mock_logger.assert_called()
    
    @pytest.mark.asyncio
    async def test_response_format(self, app_client, valid_api_key, valid_receipt_url, mock_auth_middleware):
        """Test API response format"""
        with patch("src.auth.validate_api_key", mock_auth_middleware):
            response = app_client.post(
                "/api/receipt",
                json={"url": valid_receipt_url},
                headers={"x-api-key": valid_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required fields
            required_fields = ["status", "url", "processed_at"]
            for field in required_fields:
                assert field in data
            
            # Check types
            assert isinstance(data["status"], str)
            assert isinstance(data["url"], str)
            assert isinstance(data["processed_at"], str)