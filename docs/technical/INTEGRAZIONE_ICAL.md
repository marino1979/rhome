# 📅 Integrazione iCal per Sincronizzazione Calendari Esterni

## Panoramica

Il sistema ora supporta la sincronizzazione automatica di calendari esterni (Airbnb, Booking.com, Expedia, ecc.) tramite iCal. Questo permette di bloccare automaticamente le date occupate su altre piattaforme, evitando doppie prenotazioni.

---

## 🎯 Funzionalità

- ✅ **Download automatico** di file iCal da URL esterni
- ✅ **Parsing intelligente** degli eventi per identificare prenotazioni
- ✅ **Creazione automatica** di `ClosureRule` per bloccare le date occupate
- ✅ **Sincronizzazione periodica** tramite management command
- ✅ **Interfaccia admin** per gestire i calendari esterni
- ✅ **Gestione errori** e logging dettagliato

---

## 📦 Installazione

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

Il file `requirements.txt` include già `icalendar>=5.0.0`.

### 2. Esegui le migrazioni

```bash
python manage.py migrate calendar_rules
```

Questo creerà la tabella `ExternalCalendar` nel database.

---

## ⚙️ Configurazione

### 1. Aggiungi un calendario esterno nell'admin

1. Vai all'admin Django: `/admin/`
2. Sezione **"Calendar Rules"** → **"Calendari Esterni"**
3. Clicca **"Aggiungi Calendario Esterno"**
4. Compila i campi:
   - **Appartamento**: Seleziona il listing
   - **Nome calendario**: Es. "Airbnb Roma Centro"
   - **Provider**: Seleziona il provider (Airbnb, Booking.com, ecc.)
   - **URL iCal**: Incolla l'URL del calendario iCal
   - **Attivo**: ✅ (attiva per abilitare la sincronizzazione)
   - **Intervallo sincronizzazione**: Minuti tra una sincronizzazione e l'altra (default: 60)

### 2. Ottenere l'URL iCal

#### Airbnb
1. Vai su **Airbnb** → **Impostazioni** → **Calendari**
2. Clicca su **"Sincronizza calendari"** o **"Export calendar"**
3. Copia l'URL del calendario iCal (es: `https://calendar.airbnb.com/ical/.../calendar.ics`)

#### Booking.com
1. Vai su **Booking.com** → **Extranet** → **Calendario**
2. Cerca **"Esporta calendario"** o **"iCal"**
3. Copia l'URL del calendario iCal

#### Expedia
1. Vai su **Expedia Partner Central** → **Calendar**
2. Cerca l'opzione per esportare il calendario
3. Copia l'URL del calendario iCal

---

## 🔄 Sincronizzazione

### Sincronizzazione Manuale

#### Tramite Admin
1. Vai all'admin → **"Calendari Esterni"**
2. Seleziona uno o più calendari
3. Azione dropdown: **"Sincronizza calendari selezionati"**
4. Clicca **"Vai"**

#### Tramite Management Command

Sincronizza tutti i calendari attivi:
```bash
python manage.py sync_external_calendars
```

Sincronizza un calendario specifico:
```bash
python manage.py sync_external_calendars --calendar-id 1
```

Forza la sincronizzazione anche se non necessaria:
```bash
python manage.py sync_external_calendars --force
```

### Sincronizzazione Automatica (Cron Job)

Per sincronizzare automaticamente i calendari, configura un cron job:

**Linux/Mac:**
```bash
# Aggiungi al crontab (crontab -e)
# Sincronizza ogni ora
0 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py sync_external_calendars
```

**Windows (Task Scheduler):**
1. Apri **Task Scheduler**
2. Crea nuova attività
3. Trigger: **Ogni ora**
4. Azione: Esegui programma
   - Programma: `C:\path\to\venv\Scripts\python.exe`
   - Argomenti: `manage.py sync_external_calendars`
   - Directory: `C:\path\to\project`

---

## 🔍 Come Funziona

### 1. Download iCal
Il sistema scarica il file iCal dall'URL configurato con un timeout di 30 secondi.

### 2. Parsing Eventi
Il sistema analizza tutti gli eventi nel calendario iCal e identifica le prenotazioni basandosi su:
- **Status**: Eventi con status `CONFIRMED` o mancante
- **Summary**: Eventi con parole chiave come "RESERVED", "BOOKED", "OCCUPIED", "BLOCKED", "RENTAL"

### 3. Creazione ClosureRule
Per ogni prenotazione trovata, viene creata una `ClosureRule` con:
- `start_date`: Data inizio prenotazione
- `end_date`: Data fine prenotazione
- `is_external_booking`: `True` (indica che è una prenotazione esterna)
- `reason`: Nome del calendario e provider (es: "[Airbnb Roma Centro] Sincronizzato da airbnb")

### 4. Rimozione Vecchie Regole
Prima di creare nuove regole, vengono rimosse le `ClosureRule` esistenti create da questo calendario (identificate dal nome nella `reason`).

---

## 📊 Integrazione con CalendarService

Le date bloccate dai calendari esterni vengono automaticamente integrate nel sistema di disponibilità esistente tramite `ClosureRule`. Il `CalendarService` le include già nei calcoli di disponibilità:

```python
# Nel CalendarService, le closure_rules vengono già incluse
closures = self.listing.closure_rules.filter(
    end_date__gte=start_date,
    start_date__lte=end_date
)
```

Non è necessario modificare il codice esistente! 🎉

---

## 🛠️ Struttura del Codice

### Modelli
- **`ExternalCalendar`** (`calendar_rules/models.py`): Modello per salvare i calendari esterni configurati

### Servizi
- **`ICalSyncService`** (`calendar_rules/services/ical_sync.py`): Servizio per sincronizzare un calendario esterno

### Management Commands
- **`sync_external_calendars`** (`calendar_rules/management/commands/sync_external_calendars.py`): Command per sincronizzare i calendari

### Admin
- **`ExternalCalendarAdmin`** (`calendar_rules/admin.py`): Interfaccia admin per gestire i calendari esterni

---

## 🐛 Troubleshooting

### Errore: "Errore download iCal"
- Verifica che l'URL iCal sia corretto e accessibile
- Controlla che il server possa raggiungere l'URL (non ci siano firewall)
- Verifica che l'URL non richieda autenticazione

### Errore: "Errore parsing iCal"
- Verifica che il file iCal sia valido
- Controlla i log per dettagli sull'errore

### Nessuna prenotazione trovata
- Verifica che gli eventi nel calendario iCal abbiano:
  - Status `CONFIRMED` o mancante
  - Summary con parole chiave come "RESERVED", "BOOKED", ecc.
- Controlla che le date degli eventi siano nel futuro (non oltre 2 anni)

### Date non bloccate
- Verifica che la sincronizzazione sia stata eseguita con successo
- Controlla che le `ClosureRule` siano state create (admin → Regole di Chiusura)
- Verifica che le date siano nel range di validità

---

## 📝 Esempio di Utilizzo

```python
from calendar_rules.models import ExternalCalendar
from calendar_rules.services.ical_sync import ICalSyncService

# Sincronizza un calendario specifico
calendar = ExternalCalendar.objects.get(pk=1)
service = ICalSyncService(calendar)
success, error = service.sync()

if success:
    print("Sincronizzazione completata!")
else:
    print(f"Errore: {error}")

# Sincronizza tutti i calendari attivi
stats = ICalSyncService.sync_all_active()
print(f"Sincronizzati: {stats['synced']}, Errori: {stats['errors']}")
```

---

## ✅ Checklist Setup

- [ ] Installato `icalendar` (via `requirements.txt`)
- [ ] Eseguite le migrazioni (`python manage.py migrate`)
- [ ] Configurato almeno un calendario esterno nell'admin
- [ ] Testato sincronizzazione manuale
- [ ] Configurato cron job per sincronizzazione automatica (opzionale)
- [ ] Verificato che le date vengano bloccate correttamente

---

## 🎉 Risultato

Dopo la configurazione, le date occupate su Airbnb, Booking.com, ecc. verranno automaticamente bloccate nel tuo sistema, evitando doppie prenotazioni!

Le date bloccate appariranno come **"Regole di Chiusura"** nell'admin, con `is_external_booking=True` e la `reason` che indica il calendario di origine.

