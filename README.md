# Receipt Processor API

A FastAPI-based web service for processing and extracting structured data from Serbian tax authority receipts (suf.purs.gov.rs). This API scrapes receipt data, converts Cyrillic text to Latin script, normalizes field names, and stores results in a PostgreSQL database.

> **Note**: This project was created as a demonstration of using Claude Code for AI-assisted software development. While the Serbian tax authority API supports JSON responses via `Accept: application/json` header, this implementation intentionally uses HTML parsing to showcase AI capabilities in complex data extraction and software development workflows.

## Features

- **Receipt Data Extraction**: Scrapes and parses receipt data from Serbian tax authority URLs
- **Cyrillic to Latin Conversion**: Automatic transliteration of Serbian text
- **Structured Data Output**: Returns normalized JSON with consistent field naming
- **Database Integration**: PostgreSQL storage with normalized receipt and items tables
- **API Key Authentication**: UUID-based authentication system
- **Caching System**: SHA256-based URL caching for improved performance
- **Docker Support**: Complete containerized deployment setup
- **Comprehensive Testing**: Unit, integration, and API tests with TDD approach

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Docker Deployment](#docker-deployment)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Testing](#testing)
- [Architecture](#architecture)
- [Contributing](#contributing)

## Requirements

### System Requirements
- **Python 3.13.5** or higher
- **PostgreSQL 15+** database server
- **Docker and Docker Compose** (for containerized deployment)

### Python Dependencies
All Python dependencies are listed in `requirements.txt`:
```
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
httpx>=0.25.0
beautifulsoup4>=4.12.2
psycopg[binary]>=3.1.12
pydantic>=2.4.2
python-dotenv>=1.0.0
unidecode>=1.3.7
pyyaml>=6.0.1
pytest>=7.4.3
pytest-asyncio>=0.21.1
```

### Database Requirements
- PostgreSQL 15 or higher
- Database user with CREATE, INSERT, SELECT, UPDATE permissions
- Network connectivity to the database server

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd receipt-processor
```

### 2. Create Virtual Environment
```bash
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
# Create PostgreSQL database
createdb receipt_processor

# Or using psql
psql -c "CREATE DATABASE receipt_processor;"
```

### 5. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

Required environment variables in `.env`:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/receipt_processor
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=true
LOG_LEVEL=info
```

### 6. Initialize Database Tables
```bash
python database_config.py
```

### 7. Setup API Keys
Create a `keys.txt` file with valid UUID API keys (one per line):
```bash
echo "cbd28701-1148-4853-bcd1-0d807ee96764" > keys.txt
echo "$(uuidgen)" >> keys.txt  # Add more keys as needed
```

## Running the Application

### Development Mode
```bash
# Using Python directly
python src/main.py

# Or using uvicorn
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### Production Mode
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API Base**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`

## Docker Deployment

### Quick Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at `http://localhost` (port 80).

### Manual Docker Build
```bash
# Build the application image
docker build -t receipt-processor .

# Run with external PostgreSQL
docker run -d \
  -p 80:80 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/receipt_processor \
  receipt-processor
```

For detailed Docker instructions, see [README-docker.md](README-docker.md).

## API Documentation

### Authentication
All protected endpoints require an `X-API-Key` header:
```bash
curl -H "X-API-Key: your-uuid-key" http://localhost:8000/api/receipts
```

### Endpoints

#### Process Receipt
```http
POST /api/receipt
```
Processes a receipt URL and returns structured data.

**Request Body:**
```json
{
  "url": "https://suf.purs.gov.rs/v/?vl=..."
}
```

**Response:**
```json
{
  "status": "success",
  "url": "https://suf.purs.gov.rs/v/?vl=...",
  "processed_at": "2024-01-01T12:00:00",
  "message": "Receipt processed and scraped successfully",
  "data": {
    "status_racuna": {...},
    "zahtev_za_fiskalizaciju_racuna": {...},
    "rezultat_fiskalizacije_racuna": {...},
    "specifikacija_racuna": {
      "success": true,
      "items": [...]
    }
  }
}
```

#### Get Receipts
```http
GET /api/receipts?limit=100
```
Returns a list of receipts for the authenticated API key.

#### Get Receipt Details
```http
GET /api/receipts/{receipt_id}?include_items=true
```
Returns detailed information about a specific receipt.

#### Get Receipt Items
```http
GET /api/receipts/{receipt_id}/items
```
Returns all line items for a specific receipt.

#### Health Check
```http
GET /api/health
```
Returns API health status.

### Example Usage
```bash
# Process a receipt
curl -X POST http://localhost:8000/api/receipt \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cbd28701-1148-4853-bcd1-0d807ee96764" \
  -d '{"url": "https://suf.purs.gov.rs/v/?vl=..."}'

# Get receipts list
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/api/receipts?limit=10"

# Get receipt details
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/api/receipts/receipt-uuid"
```

### Alternative JSON API Approach
> **Note**: The Serbian tax authority also supports direct JSON responses. For production use, you could bypass HTML parsing by adding the `Accept: application/json` header:
> ```bash
> curl "https://suf.purs.gov.rs/v/?vl=..." \
>   -H "Accept: application/json"
> ```
> This project intentionally uses HTML parsing to demonstrate AI-assisted development capabilities and complex data extraction techniques.

## Configuration

### Environment Variables
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `API_HOST` | Host to bind the server | `127.0.0.1` | No |
| `API_PORT` | Port to bind the server | `8000` | No |
| `DEBUG` | Enable debug mode | `false` | No |
| `LOG_LEVEL` | Logging level | `info` | No |

### Database Schema
The application creates two main tables:
- **receipts**: Stores receipt metadata and processing results
- **items**: Stores individual line items from receipts (normalized)

### Caching
- Receipt HTML content is cached using SHA256 URL hashes
- Cache files are stored in `cache/` directory
- Supports `.html`, `.json`, and `.txt` file extensions based on content type

## Testing

### Run All Tests
```bash
# Using pytest from virtual environment
.venv/bin/pytest tests/ -v

# Run specific test categories
.venv/bin/pytest tests/test_api.py -v          # API tests
.venv/bin/pytest tests/test_database.py -v    # Database tests
.venv/bin/pytest tests/test_integration.py -v # Integration tests
```

### Test Coverage
```bash
.venv/bin/pytest tests/ --cov=src --cov-report=html
```

### Test Categories
- **Unit Tests**: Database operations, auth middleware, data models
- **API Tests**: Endpoint functionality, error handling, validation
- **Integration Tests**: Real receipt processing, network handling

## Architecture

### Core Components
- **FastAPI Application** (`src/main.py`): REST API endpoints and request handling
- **Receipt Scraper** (`src/scraper.py`): HTML parsing and data extraction
- **Database Layer** (`src/database.py`): PostgreSQL integration and ORM
- **Authentication** (`src/auth.py`): API key validation middleware
- **Data Models** (`src/models.py`): Pydantic schemas for request/response

### Data Flow
1. **API Request**: Client sends receipt URL with API key
2. **Authentication**: Validate API key against `keys.txt`
3. **Caching Check**: Look for cached HTML content
4. **Scraping**: Fetch and parse receipt HTML if not cached
5. **Data Extraction**: Extract 3 main sections + line items from journal
6. **Translation**: Convert Cyrillic to Latin script
7. **Database Storage**: Save receipt and items to PostgreSQL
8. **Response**: Return structured JSON data

### Security Features
- UUID-based API key authentication
- Domain validation (only suf.purs.gov.rs URLs accepted)
- Request/response logging for audit trails
- Database isolation per API key
- No sensitive data stored in code repository

## Contributing

### Development Setup
1. Follow the installation instructions above
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Write tests for new functionality (TDD approach)
4. Ensure all tests pass: `.venv/bin/pytest tests/ -v`
5. Update documentation as needed
6. Submit a pull request

### Code Standards
- Follow TDD (Test-Driven Development) approach
- Use English for all code, comments, and documentation
- Maintain Serbian language only for user communication
- Add type hints to all functions
- Include docstrings for public methods
- Follow existing code formatting and style

### Testing Requirements
- All new features must include unit tests
- Integration tests for API endpoints
- Maintain test coverage above 80%
- Use async/await patterns consistently

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, feature requests, or questions:
1. Check existing issues in the repository
2. Create a new issue with detailed description
3. Include logs and error messages when reporting bugs
4. Provide example receipt URLs for reproduction (if applicable)