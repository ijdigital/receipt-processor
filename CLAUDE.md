# CLAUDE.md

Ovaj fajl pruža uputstva za Claude Code (claude.ai/code) prilikom rada sa kodom u ovom repozitorijumu.

## Jezička pravila

**KOMUNIKACIJA** - Claude treba uvek da odgovara na srpskom jeziku, a svi MD fajlovi sa pravilima treba da budu na srpskom.

**KOD I DOKUMENTACIJA** - Svi elementi koda koriste engleski jezik:
- Git commit poruke su na engleskom
- Komentari u programima i testovima su na engleskom  
- Imena funkcija, klasa, varijabli su na engleskom
- Samo konverzacija između Claude-a i korisnika je na srpskom

## Pregled repozitorijuma

Ovaj repozitorijum sadrži kompletnu Receipt Processor API aplikaciju za obradu računa iz srpskog poreskog sistema (suf.purs.gov.rs).

### Ključne funkcionalnosti:
- **Receipt Processing** - Automatska obrada URL-ova računa sa poreske uprave
- **Data Extraction** - Parsiranje HTML-a i izvlačenje strukturiranih podataka
- **Journal Parsing** - Analiza "Журнал" sekcije za specifikaciju računa 
- **Database Storage** - PostgreSQL baza za čuvanje svih obrađenih računa
- **API Authentication** - UUID-based API ključevi
- **Caching** - SHA256-based URL kesiranje za performanse

### Struktura projekta:
```
src/
├── main.py          # FastAPI aplikacija i endpoints
├── models.py        # Pydantic modeli za request/response
├── auth.py          # API key autentifikacija
├── scraper.py       # HTML parsing i data extraction
└── database.py      # PostgreSQL integration

tests/
├── assets/          # Test URL-ovi za poreske račune
├── test_api.py      # API endpoint testovi
├── test_auth.py     # Autentifikacija testovi
└── test_integration.py  # Integracijski testovi

database_config.py   # Database setup script
.env.example        # Template za environment varijable
requirements.txt    # Python dependencies
```

## Arhitektura

### API Endpoints:
- `POST /api/receipt` - Obradi receipt URL i vrati strukturirane podatke
- `GET /api/receipts` - Lista svih računa za API key
- `GET /api/receipts/{id}` - Detalji specifičnog računa
- `GET /api/receipts/{id}/items` - Lista svih stavki za račun
- `GET /api/health` - Health check
- `GET /` - API info

### Data Flow:
1. **Input** - URL sa suf.purs.gov.rs domena
2. **Caching** - Proveri cache za postojeće HTML
3. **Scraping** - Preuzmi i parsiraj HTML sadržaj
4. **Extraction** - Izvuci podatke iz 3 sekcije + Журнал
5. **Database** - Sačuvaj rezultat u PostgreSQL
6. **Response** - Vrati strukturirane podatke

### Security:
- UUID-based API ključevi u `keys.txt`
- Rate limiting po API ključu
- Validacija domena (samo suf.purs.gov.rs)
- Database isolation po API ključu

## Tehnologije

Projekat koristi sledeće tehnologije:
- **Python 3.13.5** - glavni programski jezik
- **FastAPI** - async web framework
- **PostgreSQL** - glavna baza podataka
- **psycopg3** - async PostgreSQL driver (binary variant)
- **BeautifulSoup4** - HTML parsing
- **httpx** - async HTTP klijent
- **pydantic** - data validation i serialization
- **python-dotenv** - environment varijable
- **pytest** - testing framework sa async podrškom

## Podešavanje razvoja

### Kreiranje virtualnog okruženja
```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

### Instaliranje zavisnosti
```bash
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Copy environment template and configure
cp .env.example .env

# Edit .env file with your database credentials
# DATABASE_URL=postgresql://username:password@localhost:5432/receipt_processor
```

### Database Setup
```bash
# Install PostgreSQL and create database
createdb receipt_processor

# Setup database tables (reads from .env)
python database_config.py
```

### Pokretanje servera
```bash
# Setup database (first time only)
python database_config.py

# Pokreni API
python src/main.py

# Ili koristi uvicorn direktno
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

## Važna pravila za razvoj

### TDD Pristup
- **UVEK** koristi Test-Driven Development
- Piši testove pre implementacije funkcionalnosti
- **VAŽNO**: Koristi pytest iz venv-a: `.venv/bin/pytest tests/ -v`
- Aktiviraj venv ili pozovi direktno `.venv/bin/python`, `.venv/bin/pip`, itd.

### Commit standardi
- Commit poruke na engleskom
- Koristi descriptive commit messages
- Automatski dodaj Claude Code signature na kraj commit-a
- Format: `git commit -m "Description\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"`

### Kesiranje strategije
- **URL kesiranje** - SHA256 hash za cache fajlove u `cache/{hash}.{ext}`
- **Ekstenzije** - .html, .json, .txt na osnovu content-type
- **Cache hit/miss** logovanje za debugging
- **Automatsko kreiranje** cache foldera

### Database best practices
- **UUID primary keys** za sve tabele
- **JSONB source field** za čuvanje kompletnih podataka
- **Index** na frequently queried fields (created_at, x_api_key, pib)
- **Security** - korisnici vide samo svoje podatke
- **Graceful degradation** - nastavi rad i bez baze

### Error handling
- **Logging** na svim nivoima (DEBUG, INFO, WARNING, ERROR)
- **Structured logging** sa YAML konfiguracijom
- **Exception handling** sa specifičnim porukama
- **HTTP status codes** prema REST standardima

### Security pravila
- **Samo suf.purs.gov.rs domen** za receipt URL-ove
- **API key validacija** za sve zaštićene endpoints
- **No secrets** u kodu - sve u .env fajlovima
- **Database isolation** po API ključu

### Code organization
- **Modularni pristup** - svaki modul ima jasnu odgovornost
- **Async/await** gde god je moguće
- **Type hints** na svim funkcijama i metodama
- **Docstrings** za sve javne funkcije
- **Constants** na vrhu modula