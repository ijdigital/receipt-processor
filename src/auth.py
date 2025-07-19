"""
Auth modul za validaciju API ključeva
"""
import logging
from typing import List
from fastapi import HTTPException
import os

logger = logging.getLogger("receipt_processor.auth")


async def load_api_keys() -> List[str]:
    """Učitava API ključeve iz keys.txt fajla"""
    try:
        keys_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "keys.txt")
        
        with open(keys_file_path, "r", encoding="utf-8") as file:
            keys = [line.strip() for line in file.readlines() if line.strip()]
        
        logger.info(f"Učitano {len(keys)} API ključeva")
        return keys
    
    except FileNotFoundError:
        logger.error("keys.txt fajl nije pronađen")
        raise HTTPException(
            status_code=500,
            detail="Greška u konfiguraciji: keys.txt fajl nije pronađen"
        )
    except Exception as e:
        logger.error(f"Greška pri učitavanju API ključeva: {e}")
        raise HTTPException(
            status_code=500,
            detail="Greška pri učitavanju API ključeva"
        )


async def validate_api_key(api_key: str) -> bool:
    """Validira API ključ"""
    if not api_key:
        logger.warning("Pokušaj pristupa bez API ključa")
        raise HTTPException(
            status_code=401,
            detail="API ključ je obavezan"
        )
    
    valid_keys = await load_api_keys()
    
    if api_key not in valid_keys:
        logger.warning(f"Nevaljan API ključ: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Nevaljan API ključ"
        )
    
    logger.info(f"Uspešna autentifikacija sa API ključem: {api_key[:8]}...")
    return True