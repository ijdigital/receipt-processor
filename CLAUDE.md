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

Ovaj repozitorijum sadrži minimalan receipt-processor projekat sa samo dva fajla:
- `url1.txt` - Sadrži URL sa kodiranim parametrima za srpski poreski organ (suf.purs.gov.rs)
- `url2.txt` - Sadrži drugi URL sa kodiranim parametrima za isti poreski organ

## Arhitektura

Repozitorijum je izgleda u početnom stanju bez implementacije koda. URL-ovi u tekstualnim fajlovima sugerišu da se možda radi o validaciji računa ili obradi poreskih dokumenata iz Srbije, jer pokazuju na Poresku upravu Republike Srbije.

## Tehnologije

Projekat koristi sledeće tehnologije:
- **Python 3.13.5** - glavni programski jezik
- **venv** - virtualno okruženje (lokacija: `.venv/`)
- **httpx** - async HTTP klijent za komunikaciju sa API-jima
- **FastAPI** - web framework za kreiranje API-ja

## Podešavanje razvoja

### Kreiranje virtualnog okruženja
```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

### Instaliranje zavisnosti
```bash
pip install httpx fastapi uvicorn
```

### Pokretanje servera
```bash
uvicorn main:app --reload
```

## Važne napomene

- Ovaj repozitorijum još uvek nije inicijalizovan kao git repozitorijum
- Trenutno ne postoje fajlovi sa kodom ili konfiguracijski fajlovi  
- Parametri URL-a u tekstualnim fajlovima su kodirani i verovatno sadrže osetljive podatke o porezima/računima