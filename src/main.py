"""
Glavna FastAPI aplikacija
"""
import logging
import logging.config
import yaml
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import os

from .models import ReceiptRequest, ReceiptResponse, ErrorResponse
from .auth import validate_api_key

# Učitaj logging konfiguraciju
def setup_logging():
    """Podešava logging na osnovu logging.yaml fajla"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logging.yaml")
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)

# Inicijalizuj logging
setup_logging()
logger = logging.getLogger("receipt_processor.main")

# Kreiraj FastAPI aplikaciju
app = FastAPI(
    title="Receipt Processor API",
    description="API za obradu skeniranih računa iz mobilne aplikacije",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Event koji se izvršava pri pokretanju aplikacije"""
    logger.info("Receipt Processor API je pokrenuta")


@app.on_event("shutdown")
async def shutdown_event():
    """Event koji se izvršava pri gašenju aplikacije"""
    logger.info("Receipt Processor API se gasi")


async def get_api_key(x_api_key: Optional[str] = Header(None)):
    """Dependency za validaciju API ključa iz header-a"""
    if not x_api_key:
        logger.warning("Zahtev bez x-api-key header-a")
        raise HTTPException(
            status_code=401,
            detail="x-api-key header je obavezan"
        )
    
    # Validacija API ključa
    await validate_api_key(x_api_key)
    return x_api_key


@app.post(
    "/api/receipt",
    response_model=ReceiptResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Nevaljan zahtev"},
        401: {"model": ErrorResponse, "description": "Neautorizovan pristup"},
        500: {"model": ErrorResponse, "description": "Greška servera"}
    }
)
async def process_receipt(
    receipt_data: ReceiptRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Obrađuje skenirani račun iz mobilne aplikacije
    
    - **url**: URL skeniranog računa sa suf.purs.gov.rs domena
    """
    try:
        logger.info(f"Obrađujem račun: {receipt_data.url[:50]}...")
        
        # Trenutno samo vraćamo uspešan odgovor
        # Ovde bi trebalo dodati logiku za obradu URL-a
        
        response = ReceiptResponse(
            status="success",
            url=receipt_data.url,
            processed_at=datetime.now().isoformat(),
            message="Račun je uspešno obrađen"
        )
        
        logger.info(f"Uspešno obrađen račun sa API ključem: {api_key[:8]}...")
        return response
        
    except Exception as e:
        logger.error(f"Greška pri obradi računa: {e}")
        raise HTTPException(
            status_code=500,
            detail="Greška pri obradi računa"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler za HTTP greške"""
    logger.warning(f"HTTP greška {exc.status_code}: {exc.detail}")
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