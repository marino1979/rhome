# 📅 Sistema di Calendario Migliorato - Rhome Book

## 🎯 Panoramica

Il sistema di calendario per le prenotazioni è stato completamente rinnovato per fornire una migliore esperienza utente e prestazioni ottimizzate. Questo documento descrive le migliorie implementate e come utilizzare il nuovo sistema.

## ✨ Nuove Funzionalità

### 🔧 Backend Migliorato

#### **CalendarManager Avanzato**
- **CalendarService** integrato per gestione sofisticata delle disponibilità
- **Logica separata** per diversi tipi di blocchi (prenotazioni, chiusure, regole)
- **Calcolo prezzi dinamico** con supporto per regole personalizzate
- **Validazione completa** delle prenotazioni con messaggi dettagliati

#### **API Endpoints Ottimizzati**
- `GET /prenotazioni/api/calendar/slug/<slug>/` - Dati calendario tramite slug
- `POST /prenotazioni/api/check-availability/` - Verifica disponibilità completa
- `POST /prenotazioni/api/quick-availability/` - Verifica rapida ottimizzata
- `POST /prenotazioni/api/combined-availability/` - Ricerca combinata per gruppi

### 🎨 Frontend Modernizzato

#### **Architettura Modulare**
- **APIClient** - Gestione centralizzata delle chiamate API
- **StateManager** - Gestione stato reattivo dell'applicazione
- **ErrorHandler** - Gestione errori centralizzata con notifiche
- **CSSManager** - Applicazione dinamica degli stili
- **RuleManager** - Logica delle regole di disponibilità
- **UIComponents** - Componenti UI riutilizzabili

#### **SimpleCalendarManager**
- **Integrazione Flatpickr** migliorata
- **Gestione errori** robusta
- **Calcolo prezzi** in tempo reale
- **Validazione** lato client
- **Feedback visivo** immediato

### 🎨 UI/UX Migliorata

#### **Calendario Visivo**
- **Stili personalizzati** per diversi stati delle date
- **Indicatori visivi** per giorni bloccati, turnover, disponibili
- **Animazioni fluide** e transizioni
- **Design responsive** per mobile e desktop
- **Tooltip informativi** per ogni giorno

#### **Template Migliorato**
- **Design moderno** con Tailwind CSS
- **Galleria immagini** integrata
- **Breakdown prezzi** dettagliato
- **Messaggi di stato** chiari
- **Loading indicators** eleganti

## 🚀 Come Utilizzare

### 1. **Template Base**
```html
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/calendar-styles.css' %}">
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/simple-listing-detail.js' %}"></script>
{% endblock %}
```

### 2. **Dati Listing**
```html
<div id="listing-data" 
     data-listing-id="{{ listing.id }}" 
     data-listing-slug="{{ listing.slug }}"
     data-min-stay="{{ listing.min_stay|default:1 }}"
     data-max-stay="{{ listing.max_stay|default:30 }}"
     data-gap-days="{{ listing.gap_between_bookings|default:0 }}"
     style="display: none;">
</div>
```

### 3. **Elementi Calendario**
```html
<!-- Input calendario -->
<input type="text" id="calendar" class="calendar-input" readonly>

<!-- Input nascosti -->
<input type="hidden" id="check-in" name="check_in">
<input type="hidden" id="check-out" name="check_out">

<!-- Select ospiti -->
<select id="guests" name="guests">
    <option value="1">1 ospite</option>
    <option value="2">2 ospiti</option>
    <!-- ... -->
</select>

<!-- Messaggi di stato -->
<div id="availability-message" class="hidden">
    <div id="availability-text"></div>
</div>

<!-- Breakdown prezzo -->
<div id="price-breakdown" class="hidden">
    <!-- Contenuto dinamico -->
</div>
```

## 🔧 Configurazione

### **Configurazione Base**
```javascript
// config.js
const Config = {
    API: {
        BASE_URL: window.location.origin,
        ENDPOINTS: {
            CHECK_AVAILABILITY: '/prenotazioni/api/check-availability/',
            GET_CALENDAR: '/prenotazioni/api/calendar/slug/',
            // ...
        }
    },
    CALENDAR: {
        MIN_DATE: 'today',
        MAX_DATE_OFFSET: 365,
        DATE_FORMAT: 'Y-m-d',
        LOCALE: 'it'
    }
};
```

### **Inizializzazione**
```javascript
// Il calendario si inizializza automaticamente
document.addEventListener('DOMContentLoaded', function() {
    // SimpleCalendarManager viene creato automaticamente
    // se trova gli elementi necessari nel DOM
});
```

## 📊 Struttura Dati API

### **Risposta Calendario**
```json
{
    "success": true,
    "listing_id": 1,
    "listing_slug": "appartamento-test",
    "base_price": 100.0,
    "max_guests": 4,
    "calendar_data": {
        "blocked_ranges": [
            {"from": "2024-01-15", "to": "2024-01-17"}
        ],
        "checkin_dates": ["2024-01-15"],
        "checkout_dates": ["2024-01-17"],
        "gap_days": ["2024-01-18"],
        "checkin_blocked_rules": {
            "dates": [],
            "weekdays": [6]
        },
        "checkout_blocked_rules": {
            "dates": [],
            "weekdays": []
        },
        "metadata": {
            "min_stay": 1,
            "max_stay": 30,
            "gap_between_bookings": 1
        }
    }
}
```

### **Risposta Verifica Disponibilità**
```json
{
    "available": true,
    "pricing": {
        "base_price_per_night": 100.0,
        "total_nights": 3,
        "subtotal": 300.0,
        "cleaning_fee": 50.0,
        "extra_guest_fee": 0.0,
        "total_amount": 350.0,
        "daily_prices": [
            {"date": "2024-01-15", "price": 100.0},
            {"date": "2024-01-16", "price": 100.0},
            {"date": "2024-01-17", "price": 100.0}
        ]
    }
}
```

## 🎨 Personalizzazione Stili

### **Classi CSS Disponibili**
```css
/* Giorni bloccati */
.flatpickr-day.flatpickr-disabled { }

/* Giorni con regole */
.flatpickr-day.no-checkin-rule { }
.flatpickr-day.no-checkout-rule { }

/* Giorni speciali */
.flatpickr-day.turnover-day { }
.flatpickr-day.available-for-checkout { }

/* Stati selezione */
.flatpickr-day.selected { }
.flatpickr-day.inRange { }
```

### **Personalizzazione Colori**
```css
:root {
    --calendar-primary: #3b82f6;
    --calendar-success: #10b981;
    --calendar-warning: #f59e0b;
    --calendar-error: #ef4444;
    --calendar-info: #06b6d4;
}
```

## 🧪 Testing

### **Eseguire i Test**
```bash
# Test completo del sistema
python test_calendar_system.py

# Test specifici
python manage.py test bookings.tests
python manage.py test calendar_rules.tests
```

### **Test Scenari**
- ✅ Prenotazione normale
- ✅ Troppi ospiti
- ✅ Date nel passato
- ✅ Conflitti prenotazioni
- ✅ Regole di chiusura
- ✅ Regole check-in/out
- ✅ Regole prezzi
- ✅ Gap tra prenotazioni

## 🔍 Debug e Troubleshooting

### **Logging**
```python
# Abilita debug calendario
LOGGING = {
    'loggers': {
        'calendar_debug': {
            'handlers': ['calendar_console', 'file'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}
```

### **Debug Frontend**
```javascript
// Abilita debug in console
Config.DEBUG.ENABLED = true;
Config.DEBUG.LOG_LEVEL = 'debug';

// Accedi al manager globale
console.log(window.simpleCalendarManager);
```

### **Problemi Comuni**

#### **Calendario non si carica**
- Verifica che Flatpickr sia incluso
- Controlla errori JavaScript in console
- Verifica che gli elementi DOM esistano

#### **API non risponde**
- Controlla URL endpoint
- Verifica token CSRF
- Controlla log server Django

#### **Stili non applicati**
- Verifica che calendar-styles.css sia incluso
- Controlla conflitti CSS
- Verifica specificità selettori

## 📈 Performance

### **Ottimizzazioni Implementate**
- **Query ottimizzate** per database
- **Caching** dei dati calendario
- **Lazy loading** delle immagini
- **Debouncing** per input utente
- **Compressione** file statici

### **Metriche Target**
- **Tempo caricamento**: < 2 secondi
- **Risposta API**: < 500ms
- **Interazione calendario**: < 100ms
- **Bundle JavaScript**: < 500KB

## 🔄 Migrazione da Sistema Precedente

### **Passi Migrazione**
1. **Backup** dati esistenti
2. **Aggiorna** template HTML
3. **Includi** nuovi file JavaScript/CSS
4. **Testa** funzionalità
5. **Deploy** in produzione

### **Compatibilità**
- ✅ **Backward compatible** con API esistenti
- ✅ **Dati esistenti** preservati
- ✅ **Configurazioni** mantenute
- ✅ **Prenotazioni** esistenti funzionanti

## 📚 Riferimenti

### **Documentazione**
- [Django Calendar Rules](calendar_rules/README.md)
- [Flatpickr Documentation](https://flatpickr.js.org/)
- [Tailwind CSS](https://tailwindcss.com/)

### **File Principali**
- `calendar_rules/managers.py` - CalendarManager
- `calendar_rules/services/calendar_service.py` - CalendarService
- `static/js/modules/SimpleCalendarManager.js` - Frontend Manager
- `static/css/calendar-styles.css` - Stili personalizzati
- `templates/listings/listing_detail_improved.html` - Template migliorato

---

## 🎉 Conclusione

Il nuovo sistema di calendario offre:
- **Esperienza utente** migliorata
- **Prestazioni** ottimizzate
- **Manutenibilità** aumentata
- **Scalabilità** garantita
- **Compatibilità** mantenuta

Per supporto o domande, contatta il team di sviluppo.
