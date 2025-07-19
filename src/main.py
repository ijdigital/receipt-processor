"""
Main FastAPI application
"""
import logging
import logging.config
import yaml
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import sys
from pathlib import Path

# Add project root to path for imports
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    from src.models import ReceiptRequest, ReceiptResponse, ErrorResponse
    from src.auth import validate_api_key
else:
    from .models import ReceiptRequest, ReceiptResponse, ErrorResponse
    from .auth import validate_api_key

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
    try:
        logger.info(f"Processing receipt: {receipt_data.url[:50]}...")
        
        # Currently just return successful response
        # Here should be added logic for URL processing
        
        response = ReceiptResponse(
            status="success",
            url=receipt_data.url,
            processed_at=datetime.now().isoformat(),
            message="Receipt processed successfully"
        )
        
        logger.info(f"Successfully processed receipt with API key: {api_key[:8]}...")
        return response
        
    except Exception as e:
        logger.error(f"Error processing receipt: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error processing receipt"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler for HTTP errors"""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.get("/health")
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
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disable reload when running directly
        log_level="info",
        access_log=True
    )