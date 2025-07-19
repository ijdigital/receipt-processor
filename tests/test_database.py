"""
Unit tests for database functionality
"""
import pytest
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from src.database import DatabaseConnection


class TestDatabaseConnection:
    """Test class for database connection and operations"""

    @pytest.fixture
    def mock_connection_string(self):
        """Mock database connection string"""
        return "postgresql://test:test@localhost:5432/test_receipt_processor"

    @pytest.fixture
    def db_connection(self, mock_connection_string):
        """Database connection instance"""
        return DatabaseConnection(mock_connection_string)

    @pytest.fixture
    def sample_receipt_data(self):
        """Sample receipt data for testing"""
        return {
            "x_api_key": str(uuid.uuid4()),
            "status": True,
            "processed_at": datetime.now(),
            "pib": "123456789",
            "ime_prodajnog_mesta": "Test Market",
            "id_kupca": "test_customer",
            "vrsta": "Promet",
            "vrsta_racuna": "Prodaja",
            "ukupan_iznos": Decimal("150.00"),
            "brojac_racuna": "12345",
            "source": {"url": "https://test.com", "data": "test"}
        }

    @pytest.fixture
    def sample_items_data(self):
        """Sample items data for testing"""
        return [
            {
                "gtin": "1234567890123",
                "name": "Test Item 1",
                "quantity": 2.0,
                "total": 100.0,
                "unit_price": 50.0,
                "label": "Е",
                "label_rate": 10.0,
                "tax_base_amount": 90.91,
                "vat_amount": 9.09
            },
            {
                "gtin": "",
                "name": "Test Item 2",
                "quantity": 1.0,
                "total": 50.0,
                "unit_price": 50.0,
                "label": "Ђ",
                "label_rate": 20.0,
                "tax_base_amount": 41.67,
                "vat_amount": 8.33
            }
        ]

    @pytest.mark.asyncio
    async def test_create_tables_success(self, db_connection):
        """Test successful table creation"""
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            await db_connection.create_tables()
            
            mock_connect.assert_called_once()
            mock_conn.execute.assert_called_once()
            mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_receipt_success(self, db_connection, sample_receipt_data):
        """Test successful receipt insertion"""
        expected_id = str(uuid.uuid4())
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_cursor = AsyncMock()
            mock_cursor.fetchone.return_value = (expected_id,)
            mock_conn.execute.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            receipt_id = await db_connection.insert_receipt(**sample_receipt_data)
            
            assert receipt_id == expected_id
            mock_connect.assert_called_once()
            mock_conn.execute.assert_called_once()
            mock_cursor.fetchone.assert_called_once()
            mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_items_success(self, db_connection, sample_items_data):
        """Test successful items insertion"""
        receipt_id = str(uuid.uuid4())
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            items_count = await db_connection.insert_items(receipt_id, sample_items_data)
            
            assert items_count == len(sample_items_data)
            mock_connect.assert_called_once()
            assert mock_conn.execute.call_count == len(sample_items_data)
            mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_items_empty_list(self, db_connection):
        """Test inserting empty items list"""
        receipt_id = str(uuid.uuid4())
        
        items_count = await db_connection.insert_items(receipt_id, [])
        
        assert items_count == 0

    @pytest.mark.asyncio
    async def test_get_receipt_success(self, db_connection):
        """Test successful receipt retrieval"""
        receipt_id = str(uuid.uuid4())
        expected_receipt = {
            'id': receipt_id,
            'x_api_key': str(uuid.uuid4()),
            'created_at': datetime.now(),
            'processed_at': datetime.now(),
            'pib': '123456789',
            'status': True
        }
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_cursor = AsyncMock()
            mock_cursor.fetchone.return_value = expected_receipt
            mock_conn.execute.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            result = await db_connection.get_receipt(receipt_id)
            
            assert result is not None
            assert result['id'] == str(expected_receipt['id'])  # Should be converted to string
            mock_connect.assert_called_once()
            mock_conn.execute.assert_called_once()
            mock_cursor.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_receipt_not_found(self, db_connection):
        """Test receipt not found scenario"""
        receipt_id = str(uuid.uuid4())
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_cursor = AsyncMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.execute.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            result = await db_connection.get_receipt(receipt_id)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_receipt_items_success(self, db_connection):
        """Test successful receipt items retrieval"""
        receipt_id = str(uuid.uuid4())
        expected_items = [
            {
                'id': str(uuid.uuid4()),
                'receipt_id': receipt_id,
                'created_at': datetime.now(),
                'name': 'Test Item 1',
                'quantity': 2.0,
                'total': 100.0
            },
            {
                'id': str(uuid.uuid4()),
                'receipt_id': receipt_id,
                'created_at': datetime.now(),
                'name': 'Test Item 2',
                'quantity': 1.0,
                'total': 50.0
            }
        ]
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_cursor = AsyncMock()
            mock_cursor.fetchall.return_value = expected_items
            mock_conn.execute.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            result = await db_connection.get_receipt_items(receipt_id)
            
            assert len(result) == len(expected_items)
            for item in result:
                assert 'id' in item
                assert 'receipt_id' in item
            mock_connect.assert_called_once()
            mock_conn.execute.assert_called_once()
            mock_cursor.fetchall.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_receipt_with_items_success(self, db_connection):
        """Test successful receipt with items retrieval"""
        receipt_id = str(uuid.uuid4())
        
        # Mock the individual methods
        with patch.object(db_connection, 'get_receipt') as mock_get_receipt, \
             patch.object(db_connection, 'get_receipt_items') as mock_get_items:
            
            mock_receipt = {'id': receipt_id, 'pib': '123456789'}
            mock_items = [{'id': str(uuid.uuid4()), 'name': 'Test Item'}]
            
            mock_get_receipt.return_value = mock_receipt
            mock_get_items.return_value = mock_items
            
            result = await db_connection.get_receipt_with_items(receipt_id)
            
            assert result is not None
            assert result['id'] == receipt_id
            assert 'items' in result
            assert len(result['items']) == len(mock_items)
            
            mock_get_receipt.assert_called_once_with(receipt_id)
            mock_get_items.assert_called_once_with(receipt_id)

    @pytest.mark.asyncio
    async def test_get_receipt_with_items_not_found(self, db_connection):
        """Test receipt with items when receipt not found"""
        receipt_id = str(uuid.uuid4())
        
        with patch.object(db_connection, 'get_receipt') as mock_get_receipt:
            mock_get_receipt.return_value = None
            
            result = await db_connection.get_receipt_with_items(receipt_id)
            
            assert result is None
            mock_get_receipt.assert_called_once_with(receipt_id)

    @pytest.mark.asyncio
    async def test_get_receipts_by_api_key_success(self, db_connection):
        """Test successful receipts retrieval by API key"""
        api_key = str(uuid.uuid4())
        processed_at = datetime.now()
        expected_receipts = [
            {
                'id': str(uuid.uuid4()),
                'x_api_key': api_key,
                'created_at': datetime.now(),
                'processed_at': processed_at.isoformat(),  # Already converted to string like real DB
                'pib': '123456789'
            }
        ]
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_cursor = AsyncMock()
            mock_cursor.fetchall.return_value = expected_receipts
            mock_conn.execute.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            result = await db_connection.get_receipts_by_api_key(api_key, limit=10)
            
            assert len(result) == len(expected_receipts)
            assert result[0]['x_api_key'] == str(expected_receipts[0]['x_api_key'])
            assert result[0]['processed_at'] == expected_receipts[0]['processed_at']
            mock_connect.assert_called_once()
            mock_conn.execute.assert_called_once()
            mock_cursor.fetchall.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_error_handling(self, db_connection):
        """Test database error handling"""
        receipt_id = str(uuid.uuid4())
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_connect.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception) as exc_info:
                await db_connection.get_receipt(receipt_id)
            
            assert "Database connection failed" in str(exc_info.value)