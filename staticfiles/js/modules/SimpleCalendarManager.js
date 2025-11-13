/**
 * SimpleCalendarManager - Versione semplificata del gestore calendario
 * 
 * Utilizza i moduli CSSManager e RuleManager per una gestione pulita
 * e modulare del calendario di prenotazione.
 */

class SimpleCalendarManager {
    constructor(listingId, options = {}) {
        this.listingId = listingId;
        this.listingSlug = options.listingSlug;
        this.options = options;
        
        // Inizializza moduli
        this.stateManager = new StateManager();
        this.apiClient = new APIClient();
        this.errorHandler = new ErrorHandler();
        this.cssManager = new CSSManager();
        this.ruleManager = new RuleManager();
        
        // Stato del calendario
        this.calendar = null;
        this.isInitialized = false;
        
        // Elementi DOM
        this.elements = {};
        
        // Configura gestione errori
        this.setupErrorHandling();
        
        // Configura sottoscrizioni stato
        this.setupStateSubscriptions();
    }
    
    /**
     * Inizializza il calendario
     */
    async initialize() {
        try {
            this.setLoading(true);
            
            // Trova elementi DOM
            this.findDOMElements();
            
            // Carica dati di disponibilità
            await this.loadAvailabilityData();
            
            // Inizializza Flatpickr
            this.initializeFlatpickr();
            
            // Configura eventi
            this.setupEventListeners();
            
            this.isInitialized = true;
            console.log('SimpleCalendarManager inizializzato con successo');
            
        } catch (error) {
            this.errorHandler.handle(error, {
                context: 'calendar-initialization',
                listingId: this.listingId
            });
            throw error;
        } finally {
            this.setLoading(false);
        }
    }
    
    /**
     * Trova gli elementi DOM necessari
     */
    findDOMElements() {
        this.elements = {
            calendarInput: document.getElementById('calendar'),
            checkInInput: document.getElementById('check-in'),
            checkOutInput: document.getElementById('check-out'),
            guestsSelect: document.getElementById('guests'),
            priceBreakdown: document.getElementById('price-breakdown'),
            availabilityMessage: document.getElementById('availability-message'),
            bookingForm: document.getElementById('booking-form')
        };
        
        if (!this.elements.calendarInput) {
            throw new Error('Elemento calendario non trovato');
        }
        
        console.log('Elementi DOM trovati:', Object.keys(this.elements).filter(key => this.elements[key]));
    }
    
    /**
     * Carica i dati di disponibilità dal backend
     */
    async loadAvailabilityData() {
        if (!this.listingSlug) {
            throw new Error('Listing slug non fornito');
        }
        
        try {
            const data = await this.apiClient.getUnavailableDates(this.listingSlug);
            this.ruleManager.loadRules(data);
            
            // Aggiorna stato
            this.stateManager.updateState('singleCalendar.rules', this.ruleManager.getRules());
            
            console.log('Dati di disponibilità caricati:', data);
        } catch (error) {
            console.error('Errore nel caricamento dati disponibilità:', error);
            throw error;
        }
    }
    
    /**
     * Inizializza Flatpickr
     */
    initializeFlatpickr() {
        if (!window.flatpickr) {
            throw new Error('Flatpickr non è caricato');
        }
        
        const config = {
            mode: 'range',
            dateFormat: 'Y-m-d',
            locale: 'it',
            minDate: 'today',
            maxDate: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000),
            disable: this.buildDisabledDates(),
            onDayCreate: this.onDayCreate.bind(this),
            onChange: this.onDateChange.bind(this),
            onReady: this.onCalendarReady.bind(this)
        };
        
        this.calendar = flatpickr(this.elements.calendarInput, config);
    }
    
    /**
     * Costruisce l'array delle date disabilitate
     */
    buildDisabledDates() {
        const disabled = [];
        const rules = this.ruleManager.getRules();
        
        rules.blockedRanges.forEach(range => {
            const start = new Date(range.from);
            const end = new Date(range.to);
            const dates = this.getDateRange(start, end);
            dates.forEach(date => {
                disabled.push(this.formatDateISO(date));
            });
        });
        
        return disabled;
    }
    
    /**
     * Gestisce la creazione di un giorno nel calendario
     */
    onDayCreate(dObj, dStr, fp, dayElem) {
        const date = dayElem.dateObj;
        if (!date) return;
        
        const selectedDates = this.stateManager.getState('singleCalendar.selectedDates') || [];
        const dayState = this.ruleManager.getDayState(date, selectedDates);
        
        this.cssManager.applyDayStyles(dayElem, dayState);
    }
    
    /**
     * Gestisce il cambio di date
     */
    onDateChange(selectedDates, dateStr, instance) {
        this.stateManager.updateState('singleCalendar.selectedDates', selectedDates);
        
        // Aggiorna input nascosti
        if (selectedDates.length >= 1) {
            this.elements.checkInInput.value = this.formatDateISO(selectedDates[0]);
        }
        if (selectedDates.length >= 2) {
            this.elements.checkOutInput.value = this.formatDateISO(selectedDates[1]);
            this.calculatePrice(selectedDates[0], selectedDates[1]);
        }
        
        // Aggiorna stili
        this.updateCalendarStyles();
    }
    
    /**
     * Gestisce il ready del calendario
     */
    onCalendarReady(selectedDates, dateStr, instance) {
        console.log('Calendario Flatpickr pronto');
        this.updateCalendarStyles();
    }
    
    /**
     * Aggiorna gli stili del calendario
     */
    updateCalendarStyles() {
        const selectedDates = this.stateManager.getState('singleCalendar.selectedDates') || [];
        const rules = this.ruleManager.getRules();
        
        this.cssManager.updateCalendarStyles(this.calendar, rules, selectedDates);
    }
    
    /**
     * Calcola il prezzo per un periodo
     */
    async calculatePrice(checkIn, checkOut) {
        try {
            const guests = this.getGuestsCount();
            const requestData = this.apiClient.formatPriceRequest(
                this.listingId,
                checkIn,
                checkOut,
                guests
            );
            
            const pricingData = await this.apiClient.calculatePrice(requestData);
            this.stateManager.updateState('singleCalendar.pricing', pricingData);
            this.showPriceBreakdown(pricingData);
            
        } catch (error) {
            this.errorHandler.handle(error, {
                context: 'price-calculation',
                checkIn: checkIn,
                checkOut: checkOut
            });
            this.hidePriceBreakdown();
        }
    }
    
    /**
     * Ottiene il numero di ospiti
     */
    getGuestsCount() {
        if (!this.elements.guestsSelect) return 1;
        
        const value = parseInt(this.elements.guestsSelect.value, 10);
        return Number.isFinite(value) && value > 0 ? value : 1;
    }
    
    /**
     * Mostra il breakdown del prezzo
     */
    showPriceBreakdown(pricingData) {
        if (!this.elements.priceBreakdown) return;
        
        const basePrice = document.getElementById('base-price');
        const totalPrice = document.getElementById('total-price');
        
        if (basePrice) basePrice.textContent = `€${pricingData.base_price || 0}`;
        if (totalPrice) totalPrice.textContent = `€${pricingData.total_price || 0}`;
        
        this.elements.priceBreakdown.classList.remove('hidden');
    }
    
    /**
     * Nasconde il breakdown del prezzo
     */
    hidePriceBreakdown() {
        if (!this.elements.priceBreakdown) return;
        
        this.elements.priceBreakdown.classList.add('hidden');
    }
    
    /**
     * Mostra un messaggio di disponibilità
     */
    showAvailabilityMessage(message, type = 'info') {
        if (!this.elements.availabilityMessage) return;
        
        const textElement = this.elements.availabilityMessage.querySelector('#availability-text');
        if (textElement) {
            textElement.textContent = message;
        }
        
        this.elements.availabilityMessage.className = 'mt-2 p-2 rounded-lg';
        
        const typeClasses = {
            success: 'bg-green-100 text-green-800',
            error: 'bg-red-100 text-red-800',
            warning: 'bg-yellow-100 text-yellow-800',
            info: 'bg-blue-100 text-blue-800'
        };
        
        this.elements.availabilityMessage.classList.add(...typeClasses[type].split(' '));
        this.elements.availabilityMessage.classList.remove('hidden');
    }
    
    /**
     * Nasconde il messaggio di disponibilità
     */
    hideAvailabilityMessage() {
        if (!this.elements.availabilityMessage) return;
        
        this.elements.availabilityMessage.classList.add('hidden');
    }
    
    /**
     * Imposta lo stato di caricamento
     */
    setLoading(loading) {
        this.stateManager.setLoading(loading);
        
        // Mostra/nascondi loading indicator
        const loadingElement = document.getElementById('calendar-loading');
        if (loadingElement) {
            loadingElement.style.display = loading ? 'flex' : 'none';
        }
    }
    
    /**
     * Configura la gestione degli errori
     */
    setupErrorHandling() {
        this.errorHandler.onError('network', (error, context) => {
            this.showAvailabilityMessage('Errore di connessione. Riprova più tardi.', 'error');
        });
        
        this.errorHandler.onError('server', (error, context) => {
            this.showAvailabilityMessage('Errore del server. Riprova più tardi.', 'error');
        });
        
        this.errorHandler.onError('calendar', (error, context) => {
            this.showAvailabilityMessage('Errore nel calendario. Ricarica la pagina.', 'error');
        });
    }
    
    /**
     * Configura le sottoscrizioni allo stato
     */
    setupStateSubscriptions() {
        this.stateManager.subscribe('singleCalendar.selectedDates', (dates) => {
            this.updateCalendarStyles();
        });
        
        this.stateManager.subscribe('singleCalendar.loading', (loading) => {
            this.setLoading(loading);
        });
    }
    
    /**
     * Configura i listener degli eventi
     */
    setupEventListeners() {
        // Listener per cambio numero ospiti
        if (this.elements.guestsSelect) {
            this.elements.guestsSelect.addEventListener('change', () => {
                const selectedDates = this.stateManager.getState('singleCalendar.selectedDates') || [];
                if (selectedDates.length === 2) {
                    this.calculatePrice(selectedDates[0], selectedDates[1]);
                }
            });
        }
        
        // Listener per form prenotazione
        if (this.elements.bookingForm) {
            this.elements.bookingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleBookingSubmit();
            });
        }
    }
    
    /**
     * Gestisce l'invio del form di prenotazione
     */
    handleBookingSubmit() {
        const checkIn = this.elements.checkInInput.value;
        const checkOut = this.elements.checkOutInput.value;
        const guests = this.getGuestsCount();
        
        if (!checkIn || !checkOut) {
            this.showAvailabilityMessage('Seleziona le date di check-in e check-out', 'warning');
            return;
        }
        
        // Validazione range
        const validation = this.ruleManager.validateDateRange(
            new Date(checkIn),
            new Date(checkOut)
        );
        
        if (!validation.valid) {
            this.showAvailabilityMessage(validation.message, 'error');
            return;
        }
        
        // Redirect al sistema di prenotazione esterno
        const url = new URL('https://maggimilano-new.kross.travel/book/step1');
        url.searchParams.set('from', checkIn);
        url.searchParams.set('to', checkOut);
        url.searchParams.set('guests', guests);
        url.searchParams.set('adults', guests);
        url.searchParams.set('children', '0');
        url.searchParams.set('rooms', '1');
        
        window.location.href = url.toString();
    }
    
    /**
     * Utility: Genera un array di date tra due date
     */
    getDateRange(start, end) {
        const dates = [];
        const current = new Date(start);
        
        while (current <= end) {
            dates.push(new Date(current));
            current.setDate(current.getDate() + 1);
        }
        
        return dates;
    }
    
    /**
     * Utility: Formatta una data in formato ISO
     */
    formatDateISO(date) {
        return date.toISOString().split('T')[0];
    }
    
    /**
     * Distrugge il calendario
     */
    destroy() {
        if (this.calendar) {
            this.calendar.destroy();
            this.calendar = null;
        }
        
        this.isInitialized = false;
        console.log('SimpleCalendarManager distrutto');
    }
}

// Esporta per uso in altri moduli
window.SimpleCalendarManager = SimpleCalendarManager;
