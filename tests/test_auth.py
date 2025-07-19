import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
import os


class TestAuthMiddleware:
    """Test klasa za auth middleware funkcionalnost"""
    
    @pytest.fixture
    def valid_api_keys(self):
        """Mock validnih API ključeva"""
        return [
            "cbd28701-1148-4853-bcd1-0d807ee96764",
            "32db2b75-9b9c-4136-8b8c-466571c1bb8c",
            "0b31f1d8-dfaf-4872-91b4-6607be1e9f62"
        ]
    
    @pytest.fixture
    def mock_keys_file(self, valid_api_keys):
        """Mock keys.txt fajla"""
        keys_content = "\n".join(valid_api_keys)
        return mock_open(read_data=keys_content)
    
    @pytest.mark.asyncio
    async def test_valid_api_key_should_pass(self, valid_api_keys, mock_keys_file):
        """Test da validni API ključ prolazi autentifikaciju"""
        from src.auth import validate_api_key
        
        with patch("builtins.open", mock_keys_file):
            result = await validate_api_key(valid_api_keys[0])
            assert result is True
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_should_fail(self, mock_keys_file):
        """Test da nevalidni API ključ ne prolazi autentifikaciju"""
        from src.auth import validate_api_key
        
        with patch("builtins.open", mock_keys_file):
            with pytest.raises(HTTPException) as exc_info:
                await validate_api_key("invalid-key-123")
            
            assert exc_info.value.status_code == 401
            assert "Nevaljan API ključ" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_missing_api_key_should_fail(self, mock_keys_file):
        """Test da nedostatak API ključa vraća grešku"""
        from src.auth import validate_api_key
        
        with patch("builtins.open", mock_keys_file):
            with pytest.raises(HTTPException) as exc_info:
                await validate_api_key("")
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_none_api_key_should_fail(self, mock_keys_file):
        """Test da None umesto API ključa vraća grešku"""
        from src.auth import validate_api_key
        
        with patch("builtins.open", mock_keys_file):
            with pytest.raises(HTTPException) as exc_info:
                await validate_api_key(None)
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_keys_file_not_found_should_fail(self):
        """Test da nepostojanje keys.txt fajla vraća grešku"""
        from src.auth import validate_api_key
        
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(HTTPException) as exc_info:
                await validate_api_key("some-key")
            
            assert exc_info.value.status_code == 500
            assert "keys.txt" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_load_api_keys_success(self, valid_api_keys, mock_keys_file):
        """Test uspešnog učitavanja API ključeva iz fajla"""
        from src.auth import load_api_keys
        
        with patch("builtins.open", mock_keys_file):
            keys = await load_api_keys()
            assert keys == valid_api_keys
    
    @pytest.mark.asyncio
    async def test_api_key_whitespace_handling(self, mock_keys_file):
        """Test da se whitespace pravilno obrađuje u API ključevima"""
        keys_with_whitespace = mock_open(read_data="  key1  \n\n  key2  \n  ")
        from src.auth import load_api_keys
        
        with patch("builtins.open", keys_with_whitespace):
            keys = await load_api_keys()
            assert keys == ["key1", "key2"]