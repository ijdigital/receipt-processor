# Docker Setup za Receipt Processor

Ovaj fajl sadrži instrukcije za pokretanje Receipt Processor aplikacije pomoću Docker-a i docker-compose.

## Preduslovi

- Docker i Docker Compose instalirani na sistemu
- Port 80 i 5432 dostupni na host sistemu

## Struktura Docker okruženja

### Servisi:
1. **postgres** - PostgreSQL 15 baza podataka
   - Port: 5432
   - Podaci čuvani u `./postgres-data/` folderu na host sistemu
   - Health check za dostupnost baze

2. **app** - Receipt Processor aplikacija
   - Port: 80
   - Zavisi od postgres servisa
   - Automatsko povezivanje sa bazom
   - Volume mapping za cache i logove

## Pokretanje aplikacije

### 1. Pripremiti okruženje
```bash
# Kreirati potrebne direktorijume
mkdir -p postgres-data cache logs

# Proveriti da API ključevi postoje
ls keys.txt
```

### 2. Pokrenuti servise
```bash
# Pokretanje u background (detached mode)
docker-compose up -d

# Ili pokretanje sa logovima
docker-compose up
```

### 3. Proveriti status
```bash
# Status servisa
docker-compose ps

# Logovi aplikacije
docker-compose logs app

# Logovi baze
docker-compose logs postgres
```

## Korisni Docker komande

### Upravljanje servisima
```bash
# Zaustavi servise
docker-compose down

# Zaustavi i ukloni volumes (PAŽNJA: briše podatke!)
docker-compose down -v

# Restart servisa
docker-compose restart

# Rebuild aplikacije
docker-compose build app
docker-compose up -d app
```

### Debugging
```bash
# Povezivanje na aplikaciju container
docker-compose exec app bash

# Povezivanje na bazu
docker-compose exec postgres psql -U receipt_user -d receipt_processor

# Pregled logova u realnom vremenu
docker-compose logs -f app
```

### Database operacije
```bash
# Backup baze
docker-compose exec postgres pg_dump -U receipt_user receipt_processor > backup.sql

# Restore baze
docker-compose exec -T postgres psql -U receipt_user receipt_processor < backup.sql
```

## Environment varijable

Glavne environment varijable su definisane u `docker-compose.yml`:

- `DATABASE_URL` - PostgreSQL connection string
- `API_HOST` - Host adresa (0.0.0.0 za Docker)
- `API_PORT` - Port broj (80)
- `DEBUG` - Debug mode (false za production)

## Volume mapping

### PostgreSQL podaci
- Host: `./postgres-data/`
- Container: `/var/lib/postgresql/data`

### Aplikacija
- Cache: `./cache/` → `/app/cache`
- Logovi: `./logs/` → `/app/logs`

## Health checks

Oba servisa imaju health check-ove:
- **postgres**: `pg_isready` komanda
- **app**: HTTP GET na `/health` endpoint

## Testiranje

```bash
# Test API dostupnosti
curl http://localhost/api/health

# Test sa API ključem
curl -X POST http://localhost/api/receipt \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"url": "https://suf.purs.gov.rs/v/?vl=..."}'

# Test drugih endpoints
curl -H "X-API-Key: your-api-key" http://localhost/api/receipts
curl -H "X-API-Key: your-api-key" http://localhost/api/receipts/{receipt-id}
```

## Troubleshooting

### Port već u upotrebi
```bash
# Promeniti port u docker-compose.yml
ports:
  - "8080:80"  # koristi port 8080 umesto 80
```

### Problemi sa bazom
```bash
# Obriši postgres-data folder i restart
sudo rm -rf postgres-data
docker-compose down
docker-compose up -d
```

### Rebuild aplikacije
```bash
# Nakon izmena koda
docker-compose build app
docker-compose up -d app
```