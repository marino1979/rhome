# Guida al Debug del Calendario

## Panoramica

È stato implementato un sistema di debug avanzato per il servizio calendario che fornisce informazioni dettagliate su tutte le date non disponibili e le ragioni per cui vengono bloccate.

## Come Funziona

### 1. Configurazione Logging

Il sistema di logging è configurato in `Rhome_book/settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'calendar_debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'calendar_debug': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 2. Messaggi di Debug

Il sistema fornisce messaggi dettagliati per ogni fase del calcolo:

#### Dati del Calendario
- **Prenotazioni trovate**: Mostra tutte le prenotazioni nel periodo
- **Chiusure trovate**: Mostra le chiusure programmate
- **Regole check-in/out**: Mostra le regole di blocco
- **Regole prezzi**: Mostra le regole di prezzo con soggiorno minimo
- **Gap days**: Mostra i giorni di gap configurati

#### Calcolo Range Bloccati
- **Range interni**: Giorni interni alle prenotazioni
- **Gap days**: Giorni bloccati dai gap tra prenotazioni
- **Chiusure**: Range bloccati dalle chiusure

#### Calcolo Check-in Bloccati
- **Date specifiche**: Date bloccate per check-in
- **Gap prima check-in**: Giorni bloccati prima del check-in
- **Gap dopo check-out**: Giorni bloccati dopo il check-out
- **Regole**: Date bloccate dalle regole

#### Calcolo Check-out Bloccati
- **Date specifiche**: Date bloccate per check-out
- **Giorni settimana**: Giorni della settimana bloccati

#### Turnover Days
- **Date di turnover**: Date di check-out disponibili per nuovi check-in

#### Consolidamento Range
- **Range originali**: Range bloccati prima del consolidamento
- **Range consolidati**: Range finali dopo l'unione di quelli sovrapposti

## Esempio di Output

```
INFO [CALENDAR DEBUG] Inizio calcolo disponibilità per Listing 3
INFO [CALENDAR DEBUG] Periodo richiesto: 2025-10-06 -> 2025-11-05
INFO [CALENDAR DEBUG] Gap tra prenotazioni: 3 giorni

INFO [DATA] [CALENDAR DEBUG] === DATI CALENDARIO OTTENUTI ===
INFO [RULES] [CALENDAR DEBUG] Prenotazioni trovate: 1
INFO    [ITEM] Prenotazione 1: Check-in 2025-10-25 -> Check-out 2025-10-28
INFO [BLOCKED] [CALENDAR DEBUG] Chiusure trovate: 0
INFO [RULES] [CALENDAR DEBUG] Regole check-in/out: 2
INFO    [DATE] Regola 1: NO CHECK-IN il 2025-12-25
INFO    [DATE] Regola 2: NO CHECK-OUT ogni Gio

INFO [BLOCKED] [CALENDAR DEBUG] === CALCOLO RANGE BLOCCATI ===
INFO [BLOCKED] [CALENDAR DEBUG] Analizzando 1 prenotazioni per range bloccati
INFO [BLOCKED] [CALENDAR DEBUG] Prenotazione 1: 2025-10-25 -> 2025-10-28
INFO    [BLOCKED] Range interno bloccato: 2025-10-25 -> 2025-10-27
INFO    [GAP] Gap days bloccati: 2025-10-29 -> 2025-10-31 (gap: 3 giorni)

INFO [BLOCKED] [CALENDAR DEBUG] === CALCOLO CHECK-IN BLOCCATI ===
INFO [BLOCKED] [CALENDAR DEBUG] Analizzando 1 prenotazioni per check-in bloccati
INFO    [BLOCKED] Check-in bloccato da prenotazione 1: 2025-10-25
INFO [GAP] [CALENDAR DEBUG] Calcolando gap days (3 giorni) per check-in
INFO    [GAP] Gap prima check-in 1: 2025-10-22 -> 2025-10-24 (3 giorni)
INFO    [GAP] Gap dopo check-out 1: 2025-10-29 -> 2025-10-31 (3 giorni)

INFO [RESULT] [CALENDAR DEBUG] === RISULTATO FINALE ===
INFO [RESULT] [CALENDAR DEBUG] Listing ID: 3
INFO [RESULT] [CALENDAR DEBUG] Range bloccati finali: 2
INFO [RESULT] [CALENDAR DEBUG] Check-in bloccati: 7
INFO [RESULT] [CALENDAR DEBUG] Check-out bloccati: 0
INFO [RESULT] [CALENDAR DEBUG] Gap tra prenotazioni: 3
```

## Interpretazione dei Risultati

### Date Bloccate per Check-in
Nel esempio sopra, le 7 date bloccate per check-in sono:
- **2025-10-22, 2025-10-23, 2025-10-24**: Gap days prima del check-in
- **2025-10-25**: Data di check-in della prenotazione esistente
- **2025-10-29, 2025-10-30, 2025-10-31**: Gap days dopo il check-out

### Range Bloccati
- **2025-10-25 -> 2025-10-27**: Giorni interni alla prenotazione
- **2025-10-29 -> 2025-10-31**: Gap days dopo il check-out

### Check-out Bloccati
- **Giovedì**: Bloccato da regola (giorno della settimana)

## Utilizzo per Debug Lato Client

Con questi messaggi di debug, puoi:

1. **Identificare date bloccate erroneamente**: Confronta le date bloccate dal server con quelle mostrate dal calendario lato client
2. **Verificare gap days**: Controlla che i gap days siano applicati correttamente
3. **Analizzare regole**: Verifica che le regole di check-in/out siano applicate correttamente
4. **Debug consolidamento**: Controlla che i range sovrapposti siano uniti correttamente

## File di Log

I messaggi di debug vengono salvati anche nel file `calendar_debug.log` nella root del progetto per un'analisi successiva.

## Attivazione/Disattivazione

Per disattivare il debug, modifica il livello di logging in `settings.py`:

```python
'loggers': {
    'calendar_debug': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',  # Cambia da INFO a WARNING per disattivare
        'propagate': True,
    },
},
```

## Note Tecniche

- Il debug è attivo solo per il logger `calendar_debug`
- I messaggi vengono mostrati sia in console che salvati in file
- Il sistema è ottimizzato per non impattare le performance in produzione
- Tutte le emoji sono state rimosse per compatibilità con Windows
