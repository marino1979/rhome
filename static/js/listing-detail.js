/**
 * Listing Detail - Entry point per il calendario singolo appartamento
 * 
 * Inizializza e gestisce il calendario per la prenotazione di un singolo appartamento.
 * Questo file sostituisce la logica JavaScript inline nel template.
 */

// Verifica che le dipendenze siano caricate
function checkDependencies() {
    const required = [
        'StateManager',
        'APIClient', 
        'ErrorHandler',
        'DateUtils',
        'SingleCalendarManager',
        'Config'
    ];
    
    const missing = required.filter(dep => !window[dep]);
    
    if (missing.length > 0) {
        console.error('Dipendenze mancanti:', missing);
        return false;
    }
    
    return true;
}

// Inizializza il calendario
async function initializeCalendar() {
    try {
        // Verifica dipendenze
        if (!checkDependencies()) {
            throw new Error('Dipendenze non caricate correttamente');
        }
        
        // Ottieni dati dal DOM
        const listingId = getListingId();
        const listingSlug = getListingSlug();
        
        if (!listingId || !listingSlug) {
            throw new Error('Dati listing non trovati nel DOM');
        }
        
        // Configura opzioni
        const options = {
            listingSlug: listingSlug,
            minStay: getMinStay(),
            maxStay: getMaxStay(),
            gapBetweenBookings: getGapBetweenBookings()
        };
        
        // Crea e inizializza il calendario
        const calendarManager = new SingleCalendarManager(listingId, options);
        await calendarManager.initialize();
        
        // Esponi globalmente per debug
        window.calendarManager = calendarManager;
        
        console.log('Calendario inizializzato con successo');
        
    } catch (error) {
        console.error('Errore durante l\'inizializzazione del calendario:', error);
        showFallbackMessage();
    }
}

// Ottiene l'ID del listing dal DOM
function getListingId() {
    // Prova diversi selettori
    const selectors = [
        '[data-listing-id]',
        '#listing-id',
        '.listing-id'
    ];
    
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.dataset.listingId || element.value || element.textContent;
        }
    }
    
    // Fallback: cerca nel template Django
    const templateData = document.querySelector('script[type="application/json"][data-listing]');
    if (templateData) {
        try {
            const data = JSON.parse(templateData.textContent);
            return data.listing_id;
        } catch (e) {
            console.warn('Errore nel parsing dei dati del template:', e);
        }
    }
    
    return null;
}

// Ottiene lo slug del listing dal DOM
function getListingSlug() {
    // Prova diversi selettori
    const selectors = [
        '[data-listing-slug]',
        '#listing-slug',
        '.listing-slug'
    ];
    
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.dataset.listingSlug || element.value || element.textContent;
        }
    }
    
    // Fallback: estrai dall'URL
    const path = window.location.pathname;
    const match = path.match(/\/appartamenti\/([^\/]+)/);
    if (match) {
        return match[1];
    }
    
    return null;
}

// Ottiene il soggiorno minimo
function getMinStay() {
    const element = document.querySelector('[data-min-stay]');
    if (element) {
        return parseInt(element.dataset.minStay, 10) || Config.calendar.defaultMinStay;
    }
    return Config.calendar.defaultMinStay;
}

// Ottiene il soggiorno massimo
function getMaxStay() {
    const element = document.querySelector('[data-max-stay]');
    if (element) {
        return parseInt(element.dataset.maxStay, 10) || Config.calendar.defaultMaxStay;
    }
    return Config.calendar.defaultMaxStay;
}

// Ottiene i gap days
function getGapBetweenBookings() {
    const element = document.querySelector('[data-gap-days]');
    if (element) {
        return parseInt(element.dataset.gapDays, 10) || Config.calendar.defaultGapDays;
    }
    return Config.calendar.defaultGapDays;
}

// Mostra messaggio di fallback
function showFallbackMessage() {
    const messageContainer = document.getElementById('availability-message');
    if (messageContainer) {
        messageContainer.innerHTML = `
            <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
                <strong>Attenzione:</strong> Il calendario non è disponibile. 
                <a href="javascript:location.reload()" class="underline">Ricarica la pagina</a> o 
                <a href="/contatti" class="underline">contattaci</a> per assistenza.
            </div>
        `;
    }
}

// Inizializza quando il DOM è pronto
document.addEventListener('DOMContentLoaded', function() {
    // Verifica che Flatpickr sia caricato
    if (!window.flatpickr) {
        console.error('Flatpickr non è caricato. Assicurati che sia incluso nel template.');
        showFallbackMessage();
        return;
    }
    
    // Inizializza il calendario
    initializeCalendar();
});

// Gestione errori globali
window.addEventListener('error', function(event) {
    console.error('Errore JavaScript globale:', event.error);
    
    // Se l'errore è relativo al calendario, mostra fallback
    if (event.error && event.error.message && 
        event.error.message.includes('calendar')) {
        showFallbackMessage();
    }
});

// Gestione errori non gestiti nelle Promise
window.addEventListener('unhandledrejection', function(event) {
    console.error('Promise rifiutata non gestita:', event.reason);
    
    // Se l'errore è relativo al calendario, mostra fallback
    if (event.reason && event.reason.message && 
        event.reason.message.includes('calendar')) {
        showFallbackMessage();
    }
});

// Esporta funzioni per uso esterno
window.ListingDetailCalendar = {
    initialize: initializeCalendar,
    getListingId: getListingId,
    getListingSlug: getListingSlug
};


