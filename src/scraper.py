"""
Receipt scraper module for extracting data from Serbian tax authority receipts
"""
import logging
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import httpx
from unidecode import unidecode

logger = logging.getLogger("receipt_processor.scraper")

# Cyrillic to Latin mapping for Serbian
CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'ђ': 'dj', 'е': 'e', 'ж': 'z',
    'з': 'z', 'и': 'i', 'ј': 'j', 'к': 'k', 'л': 'l', 'љ': 'lj', 'м': 'm', 'н': 'n',
    'њ': 'nj', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'ћ': 'c', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'c', 'џ': 'dz', 'ш': 's',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Ђ': 'Dj', 'Е': 'E', 'Ж': 'Z',
    'З': 'Z', 'И': 'I', 'Ј': 'J', 'К': 'K', 'Л': 'L', 'Љ': 'Lj', 'М': 'M', 'Н': 'N',
    'Њ': 'Nj', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'Ћ': 'C', 'У': 'U',
    'Ф': 'F', 'Х': 'H', 'Ц': 'C', 'Ч': 'C', 'Џ': 'Dz', 'Ш': 'S'
}


def transliterate_serbian(text: str) -> str:
    """Convert Serbian Cyrillic text to Latin script"""
    if not text:
        return ""
    
    # First pass: Serbian specific characters
    result = ""
    for char in text:
        result += CYRILLIC_TO_LATIN.get(char, char)
    
    # Second pass: fallback to unidecode for any remaining non-ASCII
    result = unidecode(result)
    
    return result


def normalize_key(text: str) -> str:
    """Normalize text to be used as JSON key (lowercase, no spaces, no punctuation)"""
    if not text:
        return ""
    
    # Convert to Latin
    latin_text = transliterate_serbian(text)
    
    # Convert to lowercase
    latin_text = latin_text.lower()
    
    # Replace spaces and punctuation with underscore
    latin_text = re.sub(r'[^a-z0-9]+', '_', latin_text)
    
    # Remove leading/trailing underscores
    latin_text = latin_text.strip('_')
    
    return latin_text


async def fetch_receipt_html(url: str) -> str:
    """Fetch HTML content from receipt URL"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            logger.info(f"Successfully fetched receipt HTML from: {url[:50]}...")
            return response.text
            
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching receipt: {url}")
        raise Exception("Timeout fetching receipt data")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching receipt: {e.response.status_code}")
        raise Exception(f"HTTP error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching receipt: {e}")
        raise Exception("Failed to fetch receipt data")


def extract_status_racuna(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract receipt status section (Статус рачуна)"""
    status_data = {}
    
    try:
        # Look for status section
        status_sections = soup.find_all(['div', 'section', 'table'], 
                                       string=re.compile(r'Статус.*рачуна', re.IGNORECASE))
        
        if not status_sections:
            # Alternative: look for verification text
            verification_text = soup.find(string=re.compile(r'провер.*', re.IGNORECASE))
            if verification_text:
                status_data[normalize_key("Статус")] = transliterate_serbian(verification_text.strip())
        
        # Look for common status indicators
        for element in soup.find_all(string=re.compile(r'(провер|важећ|валид)', re.IGNORECASE)):
            if element.strip():
                status_data[normalize_key("Статус рачуна")] = transliterate_serbian(element.strip())
                break
        
        logger.debug(f"Extracted status section: {status_data}")
        return status_data
        
    except Exception as e:
        logger.error(f"Error extracting status section: {e}")
        return {"status": "unknown"}


def extract_zahtev_fiskalizacija(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract fiscalization request section (Захтев за фискализацију рачуна)"""
    zahtev_data = {}
    
    try:
        # Common fields to look for
        field_patterns = {
            'ПИБ': r'ПИБ[\s:]*(\d+)',
            'Име продајног места': r'Име.*места[\s:]*([^\n]+)',
            'Адреса': r'Адреса[\s:]*([^\n]+)',
            'Град': r'Град[\s:]*([^\n]+)',
            'Општина': r'Општина[\s:]*([^\n]+)',
            'Купац': r'Купац[\s:]*([^\n]+)',
            'Идентификатор захтева': r'Идентификатор.*захтева[\s:]*([^\n]+)',
            'Врста промета': r'Врста.*промета[\s:]*([^\n]+)',
        }
        
        html_text = soup.get_text()
        
        for field_name, pattern in field_patterns.items():
            match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
            if match:
                key = normalize_key(field_name)
                value = transliterate_serbian(match.group(1).strip())
                zahtev_data[key] = value
        
        # Also look in table structures
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    
                    if any(keyword in label for keyword in ['ПИБ', 'Име', 'Адреса', 'Град']):
                        key = normalize_key(label)
                        zahtev_data[key] = transliterate_serbian(value)
        
        logger.debug(f"Extracted zahtev section: {zahtev_data}")
        return zahtev_data
        
    except Exception as e:
        logger.error(f"Error extracting zahtev section: {e}")
        return {}


def extract_rezultat_fiskalizacije(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract fiscalization result section (Резултат фискализације рачуна)"""
    rezultat_data = {}
    
    try:
        # Common fields to look for
        field_patterns = {
            'Укупан износ': r'Укупан.*износ[\s:]*([0-9,.]+)',
            'Бројач промета': r'Бројач.*промета[\s:]*(\d+)',
            'Укупан бројач': r'Укупан.*бројач[\s:]*(\d+)',
            'Проширење бројача': r'Проширење.*бројача[\s:]*([^\n]+)',
            'Захтев-Потписан-Бројач': r'Захтев.*Потписан.*Бројач[\s:]*([^\n]+)',
            'Време сервера': r'Време.*сервера[\s:]*([^\n]+)',
        }
        
        html_text = soup.get_text()
        
        for field_name, pattern in field_patterns.items():
            match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
            if match:
                key = normalize_key(field_name)
                value = transliterate_serbian(match.group(1).strip())
                rezultat_data[key] = value
        
        # Also look in table structures
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    
                    if any(keyword in label for keyword in ['Укупан', 'Бројач', 'Време']):
                        key = normalize_key(label)
                        rezultat_data[key] = transliterate_serbian(value)
        
        logger.debug(f"Extracted rezultat section: {rezultat_data}")
        return rezultat_data
        
    except Exception as e:
        logger.error(f"Error extracting rezultat section: {e}")
        return {}


async def scrape_receipt_data(url: str) -> Dict[str, Any]:
    """Main function to scrape all receipt data"""
    try:
        logger.info(f"Starting receipt scraping for: {url[:50]}...")
        
        # Fetch HTML
        html_content = await fetch_receipt_html(url)
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract all sections
        status_racuna = extract_status_racuna(soup)
        zahtev_za_fiskalizaciju_racuna = extract_zahtev_fiskalizacija(soup)
        rezultat_fiskalizacije_racuna = extract_rezultat_fiskalizacije(soup)
        
        result = {
            "status_racuna": status_racuna,
            "zahtev_za_fiskalizaciju_racuna": zahtev_za_fiskalizaciju_racuna,
            "rezultat_fiskalizacije_racuna": rezultat_fiskalizacije_racuna
        }
        
        logger.info("Receipt scraping completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error scraping receipt data: {e}")
        raise Exception(f"Failed to scrape receipt: {str(e)}")