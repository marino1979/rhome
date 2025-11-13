/**
 * Config - Configurazione globale dell'applicazione
 * 
 * Contiene tutte le configurazioni e costanti utilizzate
 * nell'applicazione del calendario.
 */

const Config = {
    // Configurazioni API
    API: {
        BASE_URL: window.location.origin,
        ENDPOINTS: {
            CHECK_AVAILABILITY: '/prenotazioni/api/check-availability/',
            GET_CALENDAR: '/prenotazioni/api/calendar/',
            CREATE_BOOKING: '/prenotazioni/create/',
            COMBINED_AVAILABILITY: '/prenotazioni/api/combined-availability/',
            CREATE_COMBINED_BOOKING: '/prenotazioni/api/combined-booking/'
        },
        TIMEOUT: 10000, // 10 secondi
        RETRY_ATTEMPTS: 3
    },

    // Configurazioni calendario
    CALENDAR: {
        MIN_DATE: 'today',
        MAX_DATE_OFFSET: 365, // giorni nel futuro
        DATE_FORMAT: 'Y-m-d',
        LOCALE: 'it',
        MODE: 'range',
        DISABLE_MOBILE: false,
        ALLOW_INPUT: false,
        CLICK_OPENS: true,
        CLOSE_ON_SELECT: false
    },

    // Configurazioni UI
    UI: {
        LOADING_DELAY: 300, // ms prima di mostrare loading
        NOTIFICATION_DURATION: 5000, // ms
        ANIMATION_DURATION: 200, // ms
        DEBOUNCE_DELAY: 300 // ms per debounce
    },

    // Configurazioni validazione
    VALIDATION: {
        MIN_STAY_DEFAULT: 1,
        MAX_STAY_DEFAULT: 30,
        MAX_GUESTS_DEFAULT: 10,
        MIN_GUESTS_DEFAULT: 1
    },

    // Configurazioni errori
    ERRORS: {
        NETWORK_TIMEOUT: 'Timeout della connessione',
        SERVER_ERROR: 'Errore del server',
        VALIDATION_ERROR: 'Errore di validazione',
        CALENDAR_ERROR: 'Errore del calendario',
        BOOKING_ERROR: 'Errore nella prenotazione'
    },

    // Configurazioni debug
    DEBUG: {
        ENABLED: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
        LOG_LEVEL: 'info', // 'debug', 'info', 'warn', 'error'
        LOG_API_CALLS: true,
        LOG_STATE_CHANGES: true
    },

    // Configurazioni CSS
    CSS: {
        CLASSES: {
            LOADING: 'calendar-loading',
            ERROR: 'calendar-error',
            SUCCESS: 'calendar-success',
            WARNING: 'calendar-warning',
            DISABLED: 'flatpickr-disabled',
            SELECTED: 'selected',
            IN_RANGE: 'inRange',
            NO_CHECKIN: 'no-checkin-rule',
            NO_CHECKOUT: 'no-checkout-rule',
            TURNOVER: 'turnover-day',
            AVAILABLE_CHECKOUT: 'available-for-checkout'
        },
        SELECTORS: {
            CALENDAR_INPUT: '#calendar',
            CHECK_IN_INPUT: '#check-in',
            CHECK_OUT_INPUT: '#check-out',
            GUESTS_SELECT: '#guests',
            PRICE_BREAKDOWN: '#price-breakdown',
            AVAILABILITY_MESSAGE: '#availability-message',
            BOOKING_FORM: '#booking-form',
            LOADING_INDICATOR: '#calendar-loading'
        }
    },

    // Configurazioni messaggi
    MESSAGES: {
        LOADING: 'Caricamento calendario...',
        ERROR_NETWORK: 'Errore di connessione. Verifica la tua connessione internet.',
        ERROR_SERVER: 'Errore del server. Riprova più tardi.',
        ERROR_CALENDAR: 'Errore nel calendario. Ricarica la pagina.',
        ERROR_BOOKING: 'Errore nella prenotazione. Riprova.',
        SUCCESS_BOOKING: 'Prenotazione creata con successo!',
        WARNING_DATES: 'Seleziona le date di check-in e check-out',
        WARNING_GUESTS: 'Seleziona il numero di ospiti',
        INFO_AVAILABLE: 'Date disponibili',
        INFO_UNAVAILABLE: 'Date non disponibili'
    },

    // Configurazioni Flatpickr
    FLATPICKR: {
        DEFAULT_CONFIG: {
            mode: 'range',
            dateFormat: 'Y-m-d',
            locale: 'it',
            minDate: 'today',
            allowInput: false,
            clickOpens: true,
            closeOnSelect: false,
            disableMobile: false,
            static: false,
            monthSelectorType: 'static',
            prevArrow: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>',
            nextArrow: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>'
        }
    },

    // Configurazioni prenotazione esterna
    EXTERNAL_BOOKING: {
        ENABLED: true,
        BASE_URL: 'https://maggimilano-new.kross.travel/book/step1',
        PARAMS: {
            from: 'from',
            to: 'to',
            guests: 'guests',
            adults: 'adults',
            children: 'children',
            rooms: 'rooms'
        }
    }
};

// Funzioni di utilità per la configurazione
Config.API.getEndpoint = function(endpointName) {
    return this.BASE_URL + this.ENDPOINTS[endpointName];
};

Config.CALENDAR.getMaxDate = function() {
    const maxDate = new Date();
    maxDate.setDate(maxDate.getDate() + this.MAX_DATE_OFFSET);
    return maxDate;
};

Config.DEBUG.log = function(level, message, data = null) {
    if (!this.ENABLED) return;
    
    const levels = ['debug', 'info', 'warn', 'error'];
    const currentLevel = levels.indexOf(this.LOG_LEVEL);
    const messageLevel = levels.indexOf(level);
    
    if (messageLevel >= currentLevel) {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
        
        switch (level) {
            case 'debug':
                console.debug(logMessage, data);
                break;
            case 'info':
                console.info(logMessage, data);
                break;
            case 'warn':
                console.warn(logMessage, data);
                break;
            case 'error':
                console.error(logMessage, data);
                break;
        }
    }
};

// Esporta per uso globale
window.Config = Config;