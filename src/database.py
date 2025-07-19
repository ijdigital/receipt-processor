"""
Database module for PostgreSQL operations
"""
import logging
import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("receipt_processor.database")


class DatabaseConnection:
    """Database connection and operations manager"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            # Test connection
            conn = await psycopg.AsyncConnection.connect(self.connection_string)
            async with conn:
                await conn.execute("SELECT 1")
                logger.info("Database connection successful")
            
            await self.create_tables()
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def create_tables(self):
        """Create receipts and items tables if they don't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS receipts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            x_api_key UUID NOT NULL,
            status BOOLEAN NOT NULL DEFAULT FALSE,
            processed_at TIMESTAMP WITH TIME ZONE,
            pib VARCHAR(20),
            ime_prodajnog_mesta TEXT,
            id_kupca TEXT,
            vrsta VARCHAR(100),
            vrsta_racuna VARCHAR(100),
            ukupan_iznos DECIMAL(15,2),
            brojac_racuna VARCHAR(100),
            source JSONB NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            receipt_id UUID NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            gtin VARCHAR(100),
            name TEXT NOT NULL,
            quantity DECIMAL(10,3) NOT NULL,
            total DECIMAL(15,2) NOT NULL,
            unit_price DECIMAL(15,2) NOT NULL,
            label VARCHAR(10),
            label_rate DECIMAL(5,2),
            tax_base_amount DECIMAL(15,2),
            vat_amount DECIMAL(15,2)
        );
        
        CREATE INDEX IF NOT EXISTS idx_receipts_created_at ON receipts(created_at);
        CREATE INDEX IF NOT EXISTS idx_receipts_x_api_key ON receipts(x_api_key);
        CREATE INDEX IF NOT EXISTS idx_receipts_pib ON receipts(pib);
        CREATE INDEX IF NOT EXISTS idx_items_receipt_id ON items(receipt_id);
        CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
        CREATE INDEX IF NOT EXISTS idx_items_label ON items(label);
        """
        
        try:
            conn = await psycopg.AsyncConnection.connect(self.connection_string)
            async with conn:
                await conn.execute(create_table_sql)
                await conn.commit()
                logger.info("Receipts table created/verified successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    async def insert_receipt(
        self,
        x_api_key: str,
        status: bool,
        processed_at: datetime,
        pib: Optional[str],
        ime_prodajnog_mesta: Optional[str], 
        id_kupca: Optional[str],
        vrsta: Optional[str],
        vrsta_racuna: Optional[str],
        ukupan_iznos: Optional[Decimal],
        brojac_racuna: Optional[str],
        source: Dict[str, Any]
    ) -> str:
        """Insert a new receipt record and return the ID"""
        
        insert_sql = """
        INSERT INTO receipts (
            x_api_key, status, processed_at, pib, ime_prodajnog_mesta,
            id_kupca, vrsta, vrsta_racuna, ukupan_iznos, brojac_racuna, source
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id;
        """
        
        try:
            conn = await psycopg.AsyncConnection.connect(self.connection_string)
            async with conn:
                cursor = await conn.execute(
                    insert_sql,
                    (
                        x_api_key, status, processed_at, pib, ime_prodajnog_mesta,
                        id_kupca, vrsta, vrsta_racuna, ukupan_iznos, brojac_racuna,
                        json.dumps(source, ensure_ascii=False)
                    )
                )
                result = await cursor.fetchone()
                await conn.commit()
                
                receipt_id = str(result[0])
                logger.info(f"Receipt inserted with ID: {receipt_id}")
                return receipt_id
                
        except Exception as e:
            logger.error(f"Error inserting receipt: {e}")
            raise
    
    async def insert_items(self, receipt_id: str, items: list[Dict[str, Any]]) -> int:
        """Insert receipt items and return count of inserted items"""
        if not items:
            return 0
        
        insert_sql = """
        INSERT INTO items (
            receipt_id, gtin, name, quantity, total, unit_price,
            label, label_rate, tax_base_amount, vat_amount
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
        """
        
        try:
            conn = await psycopg.AsyncConnection.connect(self.connection_string)
            async with conn:
                for item in items:
                    await conn.execute(
                        insert_sql,
                        (
                            receipt_id,
                            item.get("gtin", ""),
                            item.get("name", ""),
                            item.get("quantity", 0),
                            item.get("total", 0),
                            item.get("unit_price", 0),
                            item.get("label", ""),
                            item.get("label_rate", 0),
                            item.get("tax_base_amount", 0),
                            item.get("vat_amount", 0)
                        )
                    )
                await conn.commit()
                
                logger.info(f"Inserted {len(items)} items for receipt {receipt_id}")
                return len(items)
                
        except Exception as e:
            logger.error(f"Error inserting items for receipt {receipt_id}: {e}")
            raise
    
    async def get_receipt(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """Get a receipt by ID"""
        
        select_sql = """
        SELECT id, created_at, x_api_key, status, processed_at,
               pib, ime_prodajnog_mesta, id_kupca, vrsta, vrsta_racuna,
               ukupan_iznos, brojac_racuna, source
        FROM receipts 
        WHERE id = %s;
        """
        
        try:
            conn = await psycopg.AsyncConnection.connect(self.connection_string, row_factory=dict_row)
            async with conn:
                cursor = await conn.execute(select_sql, (receipt_id,))
                result = await cursor.fetchone()
                
                if result:
                    # Convert UUID and datetime objects to strings for JSON serialization
                    result['id'] = str(result['id'])
                    result['x_api_key'] = str(result['x_api_key'])
                    if result['created_at']:
                        result['created_at'] = result['created_at'].isoformat()
                    if result['processed_at']:
                        result['processed_at'] = result['processed_at'].isoformat()
                    
                return result
                
        except Exception as e:
            logger.error(f"Error getting receipt {receipt_id}: {e}")
            raise
    
    async def get_receipts_by_api_key(self, x_api_key: str, limit: int = 100) -> list[Dict[str, Any]]:
        """Get receipts by API key"""
        
        select_sql = """
        SELECT id, created_at, x_api_key, status, processed_at,
               pib, ime_prodajnog_mesta, id_kupca, vrsta, vrsta_racuna,
               ukupan_iznos, brojac_racuna
        FROM receipts 
        WHERE x_api_key = %s
        ORDER BY created_at DESC
        LIMIT %s;
        """
        
        try:
            conn = await psycopg.AsyncConnection.connect(self.connection_string, row_factory=dict_row)
            async with conn:
                cursor = await conn.execute(select_sql, (x_api_key, limit))
                results = await cursor.fetchall()
                
                # Convert UUID and datetime objects to strings
                for result in results:
                    result['id'] = str(result['id'])
                    result['x_api_key'] = str(result['x_api_key'])
                    if result['created_at']:
                        result['created_at'] = result['created_at'].isoformat()
                    if result['processed_at']:
                        result['processed_at'] = result['processed_at'].isoformat()
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting receipts for API key {x_api_key}: {e}")
            raise
    
    async def get_receipt_items(self, receipt_id: str) -> list[Dict[str, Any]]:
        """Get all items for a specific receipt"""
        
        select_sql = """
        SELECT id, receipt_id, created_at, gtin, name, quantity, total,
               unit_price, label, label_rate, tax_base_amount, vat_amount
        FROM items 
        WHERE receipt_id = %s
        ORDER BY created_at;
        """
        
        try:
            conn = await psycopg.AsyncConnection.connect(self.connection_string, row_factory=dict_row)
            async with conn:
                cursor = await conn.execute(select_sql, (receipt_id,))
                results = await cursor.fetchall()
                
                # Convert UUID and datetime objects to strings
                for result in results:
                    result['id'] = str(result['id'])
                    result['receipt_id'] = str(result['receipt_id'])
                    if result['created_at']:
                        result['created_at'] = result['created_at'].isoformat()
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting items for receipt {receipt_id}: {e}")
            raise
    
    async def get_receipt_with_items(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """Get receipt with all its items"""
        receipt = await self.get_receipt(receipt_id)
        if not receipt:
            return None
        
        items = await self.get_receipt_items(receipt_id)
        receipt['items'] = items
        
        return receipt


# Global database instance
db: Optional[DatabaseConnection] = None


async def initialize_database(connection_string: str):
    """Initialize the global database connection"""
    global db
    db = DatabaseConnection(connection_string)
    await db.initialize()


def get_database() -> DatabaseConnection:
    """Get the global database instance"""
    if db is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return db