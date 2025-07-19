"""
Main FastAPI application
"""
import logging
import logging.config
import yaml
import os
from datetime import datetime
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules
try:
    # Try absolute imports first
    from src.models import ReceiptRequest, ReceiptResponse, ErrorResponse, ReceiptData
    from src.auth import validate_api_key
    from src.scraper import scrape_receipt_data
    from src.database import initialize_database, get_database
except ImportError:
    # Fallback to relative imports
    from .models import ReceiptRequest, ReceiptResponse, ErrorResponse, ReceiptData
    from .auth import validate_api_key
    from .scraper import scrape_receipt_data
    from .database import initialize_database, get_database

# Load logging configuration
def setup_logging():
    """Set up logging based on logging.yaml file"""
    # Get project root directory
    root_dir = Path(__file__).parent.parent
    
    config_path = root_dir / "logging.yaml"
    logs_dir = root_dir / "logs"
    
    # Debug: print paths
    print(f"Current file: {Path(__file__).absolute()}")
    print(f"Root dir: {root_dir.absolute()}")
    print(f"Config path: {config_path.absolute()}")
    print(f"Logs dir: {logs_dir.absolute()}")
    
    # Ensure logs directory exists
    logs_dir.mkdir(exist_ok=True)
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f.read())
        
        # Update log file paths to be absolute
        for handler_name, handler_config in config.get('handlers', {}).items():
            if 'filename' in handler_config:
                # Convert relative path to absolute
                log_file = logs_dir / Path(handler_config['filename']).name
                handler_config['filename'] = str(log_file.absolute())
                print(f"Updated {handler_name} log path: {handler_config['filename']}")
        
        logging.config.dictConfig(config)
    else:
        print(f"Config file not found: {config_path}")
        logging.basicConfig(level=logging.INFO)

# Initialize logging
setup_logging()
logger = logging.getLogger("receipt_processor.main")

# Create FastAPI application
app = FastAPI(
    title="Receipt Processor API",
    description="API for processing scanned receipts from mobile application",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Event executed on application startup"""
    # Initialize database
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/receipt_processor")
    try:
        await initialize_database(database_url)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue without database for now
    
    logger.info("Receipt Processor API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Event executed on application shutdown"""
    logger.info("Receipt Processor API shutting down")


async def get_api_key(x_api_key: Optional[str] = Header(None)):
    """Dependency for API key validation from header"""
    if not x_api_key:
        logger.warning("Request without x-api-key header")
        raise HTTPException(
            status_code=401,
            detail="x-api-key header is required"
        )
    
    # Validate API key
    await validate_api_key(x_api_key)
    return x_api_key


@app.post(
    "/api/receipt",
    response_model=ReceiptResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Unauthorized access"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def process_receipt(
    receipt_data: ReceiptRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Process scanned receipt from mobile application
    
    - **url**: URL of scanned receipt from suf.purs.gov.rs domain
    """
    processing_time = datetime.now()
    success = False
    scraped_data = None
    receipt_id = None
    
    try:
        logger.info(f"Processing receipt: {receipt_data.url[:50]}...")
        
        # Scrape receipt data from the URL
        scraped_data = await scrape_receipt_data(receipt_data.url)
        success = True
        
        # Extract fields for database
        zahtev = scraped_data.get("zahtev_za_fiskalizaciju_racuna", {})
        rezultat = scraped_data.get("rezultat_fiskalizacije_racuna", {})
        
        pib = zahtev.get("pib")
        ime_prodajnog_mesta = zahtev.get("ime_prodajnog_mesta")
        id_kupca = zahtev.get("id_kupca")
        vrsta = zahtev.get("vrsta")
        vrsta_racuna = zahtev.get("vrsta_racuna")
        
        # Parse ukupan_iznos
        ukupan_iznos_str = rezultat.get("ukupan_iznos", "").replace(".", "").replace(",", ".")
        ukupan_iznos = None
        if ukupan_iznos_str:
            try:
                ukupan_iznos = Decimal(ukupan_iznos_str)
            except:
                pass
        
        brojac_racuna = rezultat.get("brojac_racuna")
        
        # Save to database
        try:
            db = get_database()
            receipt_id = await db.insert_receipt(
                x_api_key=api_key,
                status=success,
                processed_at=processing_time,
                pib=pib,
                ime_prodajnog_mesta=ime_prodajnog_mesta,
                id_kupca=id_kupca,
                vrsta=vrsta,
                vrsta_racuna=vrsta_racuna,
                ukupan_iznos=ukupan_iznos,
                brojac_racuna=brojac_racuna,
                source={
                    "url": receipt_data.url,
                    "scraped_data": scraped_data
                }
            )
            logger.info(f"Receipt saved to database with ID: {receipt_id}")
            
            # Save items to database
            specifikacija = scraped_data.get("specifikacija_racuna")
            if specifikacija and specifikacija.get("items"):
                items_count = await db.insert_items(receipt_id, specifikacija["items"])
                logger.info(f"Saved {items_count} items to database")
            
        except Exception as db_error:
            logger.warning(f"Failed to save to database: {db_error}")
            # Continue without database
        
        # Create ReceiptData object
        receipt_data_obj = ReceiptData(**scraped_data)
        
        response = ReceiptResponse(
            status="success",
            url=receipt_data.url,
            processed_at=processing_time.isoformat(),
            message="Receipt processed and scraped successfully",
            data=receipt_data_obj
        )
        
        logger.info(f"Successfully processed and scraped receipt with API key: {api_key[:8]}...")
        return response
        
    except Exception as e:
        logger.error(f"Error processing receipt: {e}")
        
        # Save failed attempt to database
        try:
            db = get_database()
            await db.insert_receipt(
                x_api_key=api_key,
                status=False,
                processed_at=processing_time,
                pib=None,
                ime_prodajnog_mesta=None,
                id_kupca=None,
                vrsta=None,
                vrsta_racuna=None,
                ukupan_iznos=None,
                brojac_racuna=None,
                source={
                    "url": receipt_data.url,
                    "error": str(e)
                }
            )
        except Exception as db_error:
            logger.warning(f"Failed to save error to database: {db_error}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing receipt: {str(e)}"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler for HTTP errors"""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.get("/api/receipts")
async def get_receipts(
    limit: int = 100,
    api_key: str = Depends(get_api_key)
):
    """Get receipts for the authenticated API key"""
    try:
        db = get_database()
        receipts = await db.get_receipts_by_api_key(api_key, limit)
        return {
            "status": "success",
            "count": len(receipts),
            "receipts": receipts
        }
    except Exception as e:
        logger.error(f"Error getting receipts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting receipts: {str(e)}"
        )


@app.get("/api/receipts/{receipt_id}")
async def get_receipt(
    receipt_id: str,
    include_items: bool = True,
    api_key: str = Depends(get_api_key)
):
    """Get a specific receipt by ID with optional items"""
    try:
        db = get_database()
        
        if include_items:
            receipt = await db.get_receipt_with_items(receipt_id)
        else:
            receipt = await db.get_receipt(receipt_id)
        
        if not receipt:
            raise HTTPException(
                status_code=404,
                detail="Receipt not found"
            )
        
        # Check if this receipt belongs to the authenticated API key
        if receipt['x_api_key'] != api_key:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this receipt"
            )
        
        return {
            "status": "success",
            "receipt": receipt
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting receipt {receipt_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting receipt: {str(e)}"
        )


@app.get("/api/receipts/{receipt_id}/items")
async def get_receipt_items(
    receipt_id: str,
    api_key: str = Depends(get_api_key)
):
    """Get all items for a specific receipt"""
    try:
        db = get_database()
        
        # First check if receipt exists and belongs to user
        receipt = await db.get_receipt(receipt_id)
        if not receipt:
            raise HTTPException(
                status_code=404,
                detail="Receipt not found"
            )
        
        if receipt['x_api_key'] != api_key:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this receipt"
            )
        
        # Get items
        items = await db.get_receipt_items(receipt_id)
        
        return {
            "status": "success",
            "receipt_id": receipt_id,
            "count": len(items),
            "items": items
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting items for receipt {receipt_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting receipt items: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Receipt Processor API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Receipt Processor API in development mode")
    
    # Get configuration from environment variables
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=log_level,
        access_log=True
    )