/**
 * Simple Listing Detail - Entry point semplificato per il calendario
 * 
 * Versione semplificata che utilizza i moduli CSSManager, RuleManager e SimpleCalendarManager
 * per una gestione pulita e modulare del calendario di prenotazione.
 */

// Verifica che le dipendenze siano caricate
function checkDependencies() {
    const required = [
        'StateManager',
        'APIClient', 
        'ErrorHandler',
        'CSSManager',
        'RuleManager',
        'SimpleCalendarManager',
        'UIComponents',
        'Config'
    ];
    
    const missing = required.filter(dep => !window[dep]);
    
    if (missing.length > 0) {
        console.error('Dipendenze mancanti:', missing);
        return false;
    }
    
    return true;
}

// Inizializza il calendario semplificato
async function initializeSimpleCalendar() {
    try {
        // Verifica dipendenze
        if (!checkDependencies()) {
            throw new Error('Dipendenze non caricate correttamente');
        }
        
        // Ottieni dati dal DOM
        const listingData = getListingData();
        
        if (!listingData.id || !listingData.slug) {
            throw new Error('Dati listing non trovati nel DOM');
        }
        
        // Crea e inizializza il calendario semplificato
        const calendarManager = new SimpleCalendarManager(listingData.id, {
            listingSlug: listingData.slug,
            minStay: listingData.minStay,
            maxStay: listingData.maxStay,
            gapBetweenBookings: listingData.gapDays
        });
        
        await calendarManager.initialize();
        
        // Esponi globalmente per debug
        window.simpleCalendarManager = calendarManager;
        
        console.log('Calendario semplificato inizializzato con successo');
        
    } catch (error) {
        console.error('Errore durante l\'inizializzazione del calendario:', error);
        showFallbackMessage();
    }
}

// Ottiene i dati del listing dal DOM
function getListingData() {
    // Prova diversi selettori per i dati
    const selectors = [
        '#listing-data',
        '[data-listing-id]',
        '.listing-data'
    ];
    
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return {
                id: element.dataset.listingId || element.getAttribute('data-listing-id'),
                slug: element.dataset.listingSlug || element.getAttribute('data-listing-slug'),
                minStay: parseInt(element.dataset.minStay || element.getAttribute('data-min-stay') || '1', 10),
                maxStay: parseInt(element.dataset.maxStay || element.getAttribute('data-max-stay') || '30', 10),
                gapDays: parseInt(element.dataset.gapDays || element.getAttribute('data-gap-days') || '0', 10)
            };
        }
    }
    
    // Fallback: estrai dall'URL
    const path = window.location.pathname;
    const match = path.match(/\/appartamenti\/([^\/]+)/);
    if (match) {
        return {
            id: 'unknown',
            slug: match[1],
            minStay: 1,
            maxStay: 30,
            gapDays: 0
        };
    }
    
    return {};
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
        messageContainer.classList.remove('hidden');
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
    
    // Inizializza il calendario semplificato
    initializeSimpleCalendar();
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
window.SimpleListingDetailCalendar = {
    initialize: initializeSimpleCalendar,
    getListingData: getListingData
};
