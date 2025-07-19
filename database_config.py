"""
Database configuration and setup script
"""
import asyncio
import os
from dotenv import load_dotenv
from src.database import initialize_database

# Load environment variables from .env file
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/receipt_processor"
)

async def setup_database():
    """Setup database tables and connections"""
    print(f"Connecting to database: {DATABASE_URL}")
    
    try:
        await initialize_database(DATABASE_URL)
        print("✅ Database setup completed successfully")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_database())