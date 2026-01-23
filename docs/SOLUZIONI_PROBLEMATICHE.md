# Soluzioni e Problematiche - Pannello Admin Esterno

## Data: 19 Gennaio 2026

### Problema: Creazione Pannello Admin Esterno a Django

**Requisiti:**
1. Creazione e modifica dell'annuncio, con descrizione stanze, foto, etc.
2. Aggiornamento prezzi
3. Gestione prenotazioni
4. Gestione calendari sincronizzati ICAL

### Soluzione Implementata

#### 1. Architettura

È stato creato un pannello admin esterno completamente separato dall'admin Django standard, utilizzando:

- **Backend**: Django REST Framework (già presente nel progetto)
- **Frontend**: Single Page Application (SPA) con HTML/CSS/JavaScript vanilla
- **Autenticazione**: Session-based authentication (richiede login Django)

#### 2. Struttura Creata

```
admin_panel/
├── serializers.py      # Serializers per tutti i modelli
├── views.py            # ViewSet per API REST
├── urls.py             # Routing API
└── templates/
    └── admin_panel/
        └── index.html  # Frontend SPA

static/admin_panel/
├── css/
│   └── admin-panel.css # Stili del pannello
└── js/
    └── admin-panel.js  # Logica JavaScript
```

#### 3. API REST Implementate

**Endpoint Base**: `/admin-panel/api/`

- **Listings** (`/listings/`): CRUD completo per annunci
  - GET: Lista tutti gli annunci
  - POST: Crea nuovo annuncio
  - PUT: Aggiorna annuncio
  - DELETE: Elimina annuncio
  - POST `/listings/{id}/upload-image/`: Carica immagini
  - DELETE `/listings/{id}/images/{image_id}/`: Elimina immagine
  - PATCH `/listings/{id}/images/{image_id}/set-main/`: Imposta immagine principale

- **Rooms** (`/rooms/`): CRUD per stanze
  - Supporta upload immagini per stanza
  - Filtrabile per listing

- **Price Rules** (`/price-rules/`): Gestione regole di prezzo
  - Filtrabile per listing
  - Supporta prezzo personalizzato per periodo

- **Closure Rules** (`/closure-rules/`): Gestione chiusure
  - Filtrabile per listing

- **External Calendars** (`/external-calendars/`): Gestione calendari ICAL
  - POST `/external-calendars/{id}/sync/`: Sincronizzazione manuale
  - Supporta provider: Airbnb, Booking.com, Expedia, Altro

- **Bookings** (`/bookings/`): Gestione prenotazioni
  - Filtrabile per listing e stato
  - Visualizzazione completa informazioni prenotazione

- **Amenities** (`/amenities/`): Lista servizi (solo lettura)

#### 4. Frontend SPA

Il frontend è organizzato in sezioni:

1. **Annunci**: 
   - Lista annunci con card
   - Creazione/modifica annuncio
   - Upload immagini
   - Gestione stanze (in sviluppo)

2. **Prezzi**:
   - Selezione annuncio
   - Visualizzazione regole prezzo esistenti
   - Aggiunta/modifica/eliminazione regole

3. **Prenotazioni**:
   - Tabella prenotazioni
   - Filtri per annuncio e stato
   - Dettagli prenotazione (in sviluppo)

4. **Calendari ICAL**:
   - Lista calendari sincronizzati
   - Creazione/modifica calendario
   - Sincronizzazione manuale
   - Visualizzazione stato sincronizzazione

#### 5. Funzionalità Chiave

- **Upload Immagini**: Supporto multiplo, preview, eliminazione
- **Gestione Prezzi**: Regole per periodo con prezzo personalizzato
- **Sincronizzazione ICAL**: Integrazione con servizio esistente `CalendarSyncService`
- **Filtri Avanzati**: Per prenotazioni e regole
- **UI Responsive**: Adattabile a mobile e desktop

### Problematiche Affrontate

#### 1. Autenticazione e Permessi

**Problema**: Le API devono essere accessibili solo agli admin autenticati.

**Soluzione**: 
- Utilizzato `IsAuthenticated` e `IsAdminUser` come permission classes
- Session authentication per mantenere compatibilità con Django
- Decorator `@staff_member_required` per la view HTML

#### 2. Upload Immagini

**Problema**: Gestione upload file tramite API REST.

**Soluzione**:
- Endpoint dedicato `/upload-image/` che accetta `FormData`
- Supporto per immagini multiple
- Gestione flag `is_main` per immagine principale
- Preview immagini nel frontend

#### 3. Serializzazione Modelli Complessi

**Problema**: Modelli con relazioni multiple (Listing -> Images, Rooms, Amenities).

**Soluzione**:
- Serializers annidati per immagini e stanze
- Campo `SerializerMethodField` per URL immagini assolute
- Supporto `write_only` per `amenities_ids` per facilitare creazione

#### 4. Gestione CSRF Token

**Problema**: Richieste AJAX richiedono CSRF token.

**Soluzione**:
- Funzione JavaScript `getCsrfToken()` che legge il cookie
- Token incluso in tutte le richieste POST/PUT/DELETE
- Compatibile con session authentication Django

#### 5. Sincronizzazione ICAL

**Problema**: Integrazione con servizio esistente per sincronizzazione.

**Soluzione**:
- Endpoint `/sync/` che chiama `CalendarSyncService`
- Gestione errori e messaggi di stato
- Aggiornamento automatico stato sincronizzazione

### Configurazione Aggiunta

#### settings.py

```python
INSTALLED_APPS = [
    # ...
    'admin_panel',
    # ...
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

#### urls.py

```python
urlpatterns = [
    # ...
    path('admin-panel/', include('admin_panel.urls')),
]
```

### Accesso al Pannello

**URL**: `/admin-panel/`

**Requisiti**:
- Utente deve essere autenticato
- Utente deve essere staff (IsAdminUser)

### Funzionalità Completate (Aggiornamento)

1. ✅ **Gestione Stanze**: Form completo per creazione/modifica stanze con upload immagini
2. ✅ **Dettagli Prenotazione**: Vista dettagliata con modifica stato e note host
3. ✅ **Regole Prezzo**: Form modale completo per creazione/modifica
4. ✅ **Gestione Chiusure**: Interfaccia completa per creazione/modifica chiusure

### Note Tecniche

- Il pannello è completamente separato dall'admin Django
- Utilizza API REST standard per comunicazione
- Frontend vanilla JavaScript (no framework esterni)
- Compatibile con sistema di autenticazione esistente
- Integrato con servizi calendario esistenti

### Funzionalità Aggiunte (Ultimo Aggiornamento)

#### 1. Gestione Completa Stanze
- Modale per creazione/modifica stanze
- Upload immagini per stanza
- Visualizzazione lista stanze con immagini
- Eliminazione stanze e immagini

#### 2. Vista Dettagli Prenotazione
- Modale con tutte le informazioni prenotazione
- Modifica stato prenotazione (pending, confirmed, cancelled, etc.)
- Modifica stato pagamento
- Gestione note host
- Visualizzazione breakdown prezzi completo
- Informazioni ospite e contatti

#### 3. Gestione Chiusure
- Sezione dedicata nella gestione prezzi
- Creazione/modifica/eliminazione chiusure
- Supporto per prenotazioni esterne
- Visualizzazione motivo chiusura

#### 4. Miglioramenti Immagini
- Badge "Principale" per immagine principale
- Pulsante per impostare immagine principale
- Preview migliorato con azioni hover
- Ordinamento immagini

### Calendario Stile Airbnb (Nuovo)

#### Funzionalità Implementate

1. **Calendario Mensile Interattivo**
   - Visualizzazione mensile con navigazione tra mesi
   - Prezzo visualizzato per ogni giorno
   - Indicatore visivo per giorni con prenotazioni
   - Badge con iniziale ospite per giorni occupati

2. **Selezione Multipla Giorni**
   - Click singolo per selezionare/deselezionare giorni
   - Supporto selezione range con Shift+Click
   - Visualizzazione range selezionato con stili distinti
   - Barra azioni quando ci sono giorni selezionati

3. **Modifica Prezzo per Periodo**
   - Modale prezzo pre-compilato con date selezionate
   - Calcolo automatico prezzo medio per periodo
   - Creazione/modifica regole prezzo direttamente dal calendario

4. **Gestione Chiusure dal Calendario**
   - Creazione chiusure per periodo selezionato
   - Visualizzazione giorni bloccati nel calendario
   - Distinzione visiva tra giorni occupati e chiusi

5. **Integrazione Completa**
   - Calendario integrato nella sezione prezzi
   - Aggiornamento automatico dopo modifiche
   - Caricamento dati prenotazioni e regole prezzo
   - Sincronizzazione con sistema esistente

#### Caratteristiche UI

- Design moderno stile Airbnb
- Colori distintivi per stati diversi (occupato, chiuso, disponibile)
- Tooltip con informazioni dettagliate
- Responsive per mobile
- Animazioni fluide

### Prossimi Passi Suggeriti

1. ✅ ~~Completare funzionalità in sviluppo~~ (Completato)
2. ✅ ~~Calendario stile Airbnb~~ (Completato)
3. Aggiungere validazione lato client più robusta
4. Implementare paginazione nel frontend
5. Aggiungere ricerca e filtri avanzati
6. Implementare notifiche real-time per sincronizzazioni
7. Aggiungere export dati (CSV, Excel)
8. Implementare riordino immagini con drag & drop
9. Aggiungere statistiche e dashboard
10. Aggiungere vista annuale del calendario
