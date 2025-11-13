# 📅 Calendar Services - Sistema di Gestione Calendario

Questo modulo contiene i servizi specializzati per la gestione del calendario e della disponibilità degli alloggi. Il sistema è progettato con un'architettura modulare che separa le responsabilità in servizi specializzati.

## 🏗️ Architettura del Sistema

```
CalendarService (Orchestratore Principale)
├── GapCalculator (Gestione Gap Days)
├── RangeConsolidator (Gestione Range)
├── QueryOptimizer (Ottimizzazione DB)
└── Exceptions (Gestione Errori)
```

## 🔧 Componenti Principali

### 1. **CalendarService** - Orchestratore Principale

**File**: `calendar_service.py`

Il servizio principale che orchestra tutti gli altri componenti per fornire una API pulita e testabile.

#### **Responsabilità:**
- ✅ Orchestrazione dei servizi specializzati
- ✅ Validazione input e gestione errori
- ✅ Formattazione output per API
- ✅ Debug e logging dettagliato

#### **Metodo Principale:**
```python
def get_unavailable_dates(self, start_date: date, end_date: date) -> Dict[str, Any]:
    """
    Metodo principale per ottenere tutte le informazioni di disponibilità.
    
    Returns:
        Dict con:
        - blocked_ranges: Range completamente bloccati
        - checkin_block: Giorni bloccati per check-in
        - checkout_block: Giorni bloccati per check-out  
        - turnover_days: Giorni di turnover (check-out disponibili per check-in)
        - real_checkin_dates: Date di check-in reali
        - metadata: Informazioni aggiuntive
    """
```

#### **Metodi Interni:**
- `_get_optimized_calendar_data()`: Ottiene dati con query ottimizzate
- `_calculate_blocked_ranges()`: Calcola range completamente bloccati
- `_calculate_checkin_blocks()`: Calcola blocchi check-in
- `_calculate_checkout_blocks()`: Calcola blocchi check-out
- `_calculate_turnover_days()`: Calcola giorni di turnover
- `_extract_real_checkin_dates()`: Estrae date check-in reali
- `_consolidate_ranges()`: Consolida range sovrapposti
- `_format_response()`: Formatta la risposta finale

### 2. **GapCalculator** - Gestione Gap Days

**File**: `gap_calculator.py`

Servizio specializzato per calcolare i gap days tra prenotazioni.

#### **Responsabilità:**
- ✅ Calcolo gap days dopo check-out
- ✅ Calcolo gap days prima di check-in
- ✅ Gestione regole gap complesse
- ✅ Validazione gap days

#### **Concetti Chiave:**
- **Gap Days**: Giorni di pausa richiesti tra prenotazioni
- **Pre-gap**: Giorni bloccati prima del prossimo check-in
- **Post-gap**: Giorni bloccati dopo un check-out

#### **Metodi Principali:**
```python
def calculate_pre_gap_days(self, check_in_date: date, gap_days: int) -> List[date]:
    """Calcola i giorni di gap prima di un check-in."""

def calculate_post_gap_days(self, check_out_date: date, gap_days: int) -> List[date]:
    """Calcola i giorni di gap dopo un check-out."""

def calculate_min_nights_block(self, check_in_date: date, min_nights: int) -> List[date]:
    """Calcola i giorni bloccati per soggiorno minimo."""
```

### 3. **RangeConsolidator** - Gestione Range

**File**: `range_consolidator.py`

Servizio per consolidare e gestire i range di date bloccate.

#### **Responsabilità:**
- ✅ Consolidamento range sovrapposti
- ✅ Merge range adiacenti
- ✅ Gestione range vuoti o invalidi
- ✅ Ottimizzazione performance per range numerosi

#### **Algoritmo di Consolidamento:**
1. **Ordinamento**: Range ordinati per data di inizio
2. **Iterazione**: Analisi sequenziale dei range
3. **Unione**: Range sovrapposti o adiacenti vengono uniti
4. **Ottimizzazione**: Riduzione del numero totale di range

#### **Metodi Principali:**
```python
def consolidate_ranges(self, ranges: List[Tuple[date, date]]) -> List[Tuple[date, date]]:
    """Consolida i range sovrapposti e adiacenti."""

def merge_overlapping_ranges(self, ranges: List[Tuple[date, date]]) -> List[Tuple[date, date]]:
    """Unisce solo i range sovrapposti."""

def are_ranges_overlapping(self, range1: Tuple[date, date], range2: Tuple[date, date]) -> bool:
    """Verifica se due range si sovrappongono."""
```

### 4. **QueryOptimizer** - Ottimizzazione Database

**File**: `query_optimizer.py`

Servizio per ottimizzare le query del database.

#### **Responsabilità:**
- ✅ Ottimizzazione query per calendario
- ✅ Prefetch delle relazioni
- ✅ Caching dei risultati
- ✅ Riduzione query N+1

#### **Ottimizzazioni Implementate:**
- **Prefetch**: Caricamento anticipato delle relazioni
- **Select Related**: Join ottimizzati
- **Batch Loading**: Caricamento in batch
- **Query Filtering**: Filtri ottimizzati per date

#### **Metodi Principali:**
```python
def get_optimized_calendar_data(self, listing, start_date: date, end_date: date) -> Dict[str, Any]:
    """Ottiene tutti i dati del calendario con query ottimizzate."""

def optimize_bookings_query(self, listing, start_date: date, end_date: date) -> QuerySet:
    """Ottimizza la query per le prenotazioni."""

def optimize_rules_query(self, listing, start_date: date, end_date: date) -> QuerySet:
    """Ottimizza la query per le regole."""
```

### 5. **Exceptions** - Gestione Errori

**File**: `exceptions.py`

Sistema di eccezioni custom per gestire errori specifici del calendario.

#### **Gerarchia delle Eccezioni:**
```python
CalendarServiceError (Base)
├── InvalidDateRangeError
├── GapCalculationError
├── RangeConsolidationError
└── QueryOptimizationError
```

## 🔄 Flusso di Esecuzione

### 1. **Inizializzazione**
```python
# Creazione del servizio per un listing specifico
service = CalendarService(listing)
```

### 2. **Richiesta Disponibilità**
```python
# Ottenimento date non disponibili
result = service.get_unavailable_dates(start_date, end_date)
```

### 3. **Processo Interno**
```
1. Validazione input
   ↓
2. Ottimizzazione query (QueryOptimizer)
   ↓
3. Calcolo componenti separati:
   - Range bloccati (interiori + chiusure)
   - Blocchi check-in (gap + min_nights + regole)
   - Blocchi check-out (regole)
   - Turnover days (gap=0 + no regole)
   ↓
4. Consolidamento range (RangeConsolidator)
   ↓
5. Formattazione risposta
```

## 📊 Logica di Calcolo

### **Range Bloccati (Completamente Non Selezionabili)**
- **Giorni interni prenotazioni**: `(check_in+1) .. (check_out-1)`
- **Chiusure**: Range definiti dalle regole di chiusura

### **Blocchi Check-in (Non Iniziare Soggiorno)**
- **Pre-gap**: `[check_in-gap_days, check_in-1]`
- **Min nights**: `[check_in-(min_nights-1), check_in-1]`
- **Post-gap**: `[check_out, check_out+gap_days-1]`
- **Regole no_checkin**: Date specifiche + giorni settimanali

### **Turnover Days (Check-out Utilizzabili per Check-in)**
- **Condizioni**: `gap_days == 0` AND `no regole no_checkin`
- **Calcolo**: Giorni di check-out che rispettano le condizioni

## 🧪 Testing

### **Suite di Test**
Il sistema include una suite completa di test in `test_calendar_service.py` che copre:

- ✅ Gap days (0, 1, 2+)
- ✅ Min nights (1, 3, 4+)
- ✅ Turnover days
- ✅ Regole no_checkin (date + settimanali)
- ✅ Consolidamento range
- ✅ Prenotazioni consecutive
- ✅ Edge cases

### **Esecuzione Test**
```bash
python -m pytest tests/test_calendar_service.py -v --ds=Rhome_book.settings
```

## 🚀 Utilizzo Pratico

### **Esempio Base**
```python
from calendar_rules.services import CalendarService
from listings.models import Listing
from datetime import date

# Inizializzazione
listing = Listing.objects.get(id=1)
service = CalendarService(listing)

# Richiesta disponibilità
start_date = date(2025, 1, 1)
end_date = date(2025, 1, 31)
result = service.get_unavailable_dates(start_date, end_date)

# Risultato
print(f"Range bloccati: {result['blocked_ranges']}")
print(f"Check-in bloccati: {result['checkin_block']['dates']}")
print(f"Turnover days: {result['turnover_days']}")
```

### **Esempio con Debug**
```python
# Il servizio include logging dettagliato automatico
# I log sono disponibili in:
# - Console (con colori)
# - File: calendar_debug.log
# - Browser: /api/debug-page/{listing_id}/
```

## 📈 Performance e Ottimizzazioni

### **Query Optimization**
- Prefetch delle relazioni per evitare query N+1
- Filtri ottimizzati per range di date
- Caricamento lazy delle regole

### **Memory Management**
- Consolidamento range per ridurre memoria
- Lazy loading dei dati non critici
- Caching intelligente dei risultati

### **Scalabilità**
- Architettura modulare per estensibilità
- Servizi specializzati per responsabilità specifiche
- API pulita per integrazione

## 🔧 Configurazione

### **Settings Django**
```python
# Rhome_book/settings.py
LOGGING = {
    'loggers': {
        'calendar_debug': {
            'level': 'INFO',
            'handlers': ['calendar_console', 'file'],
            'propagate': False,
        },
    },
    'handlers': {
        'calendar_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'calendar_debug',
        },
    },
    'formatters': {
        'calendar_debug': {
            'format': '\033[1;32m[CALENDAR DEBUG]\033[0m %(message)s',
        },
    },
}
```

### **Variabili di Ambiente**
- `DEBUG`: Abilita logging dettagliato
- `LOG_LEVEL`: Livello di logging (INFO, DEBUG, WARNING)

## 🐛 Debug e Troubleshooting

### **Debug Console**
```python
# I log sono colorati e visibili in console
python manage.py test_calendar_debug --days 30
```

### **Debug Browser**
```
# Interfaccia web per debug
http://127.0.0.1:8000/api/debug-page/{listing_id}/
```

### **Debug API**
```python
# Endpoint API per debug programmatico
GET /api/debug/{listing_id}/?days=30&start_date=2025-01-01
```

## 📝 Note di Sviluppo

### **Estensibilità**
Il sistema è progettato per essere facilmente estensibile:
- Nuovi servizi specializzati possono essere aggiunti
- La logica di business è separata dall'orchestrazione
- Le eccezioni sono gerarchiche per gestione granulare

### **Manutenibilità**
- Codice ben documentato e commentato
- Test completi per tutti i casi d'uso
- Logging dettagliato per debugging
- Architettura modulare e pulita

### **Best Practices**
- Separazione delle responsabilità
- Gestione errori robusta
- Performance ottimizzate
- API consistente e prevedibile

---

## 📞 Supporto

Per domande o problemi relativi al sistema di servizi del calendario, consultare:
- Log di debug in console o file
- Test suite per esempi di utilizzo
- Documentazione inline nel codice
- Interfaccia web di debug per analisi visiva
