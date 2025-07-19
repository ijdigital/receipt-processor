"""
Auth module for API key validation
"""
import logging
from typing import List
from fastapi import HTTPException
import os

logger = logging.getLogger("receipt_processor.auth")


async def load_api_keys() -> List[str]:
    """Load API keys from keys.txt file"""
    try:
        keys_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "keys.txt")
        
        with open(keys_file_path, "r", encoding="utf-8") as file:
            keys = [line.strip() for line in file.readlines() if line.strip()]
        
        logger.info(f"Loaded {len(keys)} API keys")
        return keys
    
    except FileNotFoundError:
        logger.error("keys.txt file not found")
        raise HTTPException(
            status_code=500,
            detail="Configuration error: keys.txt file not found"
        )
    except Exception as e:
        logger.error(f"Error loading API keys: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error loading API keys"
        )


async def validate_api_key(api_key: str) -> bool:
    """Validate API key"""
    if not api_key:
        logger.warning("Access attempt without API key")
        raise HTTPException(
            status_code=401,
            detail="API key is required"
        )
    
    valid_keys = await load_api_keys()
    
    if api_key not in valid_keys:
        logger.warning(f"Invalid API key: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    logger.info(f"Successful authentication with API key: {api_key[:8]}...")
    return True