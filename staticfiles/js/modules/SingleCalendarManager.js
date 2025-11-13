/**
 * SingleCalendarManager - Gestione calendario per singolo appartamento
 * 
 * Gestisce la logica del calendario per la prenotazione di un singolo appartamento,
 * inclusa la validazione delle date, il calcolo dei prezzi e l'interazione con Flatpickr.
 */

class SingleCalendarManager {
    constructor(listingId, options = {}) {
        this.listingId = listingId;
        this.listingSlug = options.listingSlug;
        this.options = {
            minStay: 1,
            maxStay: 30,
            gapBetweenBookings: 0,
            ...options
        };
        
        // Inizializza moduli
        this.stateManager = new StateManager();
        this.apiClient = new APIClient();
        this.errorHandler = new ErrorHandler();
        this.dateUtils = DateUtils;
        
        // Stato del calendario
        this.calendar = null;
        this.isInitialized = false;
        
        // Elementi DOM
        this.elements = {
            calendarInput: null,
            checkInInput: null,
            checkOutInput: null,
            guestsSelect: null,
            priceBreakdown: null,
            availabilityMessage: null
        };
        
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
            this.errorHandler.setLoading(true);
            
            // Trova elementi DOM
            this.findDOMElements();
            
            // Carica dati di disponibilità
            await this.loadAvailabilityData();
            
            // Inizializza Flatpickr
            this.initializeFlatpickr();
            
            // Configura eventi
            this.setupEventListeners();
            
            this.isInitialized = true;
            console.log('SingleCalendarManager inizializzato con successo');
            
        } catch (error) {
            this.errorHandler.handle(error, {
                context: 'calendar-initialization',
                listingId: this.listingId
            });
            throw error;
        } finally {
            this.errorHandler.setLoading(false);
        }
    }
    
    /**
     * Trova gli elementi DOM necessari
     * @private
     */
    findDOMElements() {
        this.elements.calendarInput = document.getElementById('calendar');
        this.elements.checkInInput = document.getElementById('check-in');
        this.elements.checkOutInput = document.getElementById('check-out');
        this.elements.guestsSelect = document.getElementById('guests');
        this.elements.priceBreakdown = document.getElementById('price-breakdown');
        this.elements.availabilityMessage = document.getElementById('availability-message');
        
        if (!this.elements.calendarInput) {
            throw new Error('Elemento calendario non trovato');
        }
        
        // Log degli elementi trovati per debug
        console.log('Elementi DOM trovati:', {
            calendarInput: !!this.elements.calendarInput,
            checkInInput: !!this.elements.checkInInput,
            checkOutInput: !!this.elements.checkOutInput,
            guestsSelect: !!this.elements.guestsSelect,
            priceBreakdown: !!this.elements.priceBreakdown,
            availabilityMessage: !!this.elements.availabilityMessage
        });
    }
    
    /**
     * Carica i dati di disponibilità dal backend
     * @private
     */
    async loadAvailabilityData() {
        if (!this.listingSlug) {
            throw new Error('Listing slug non fornito');
        }
        
        const data = await this.apiClient.getUnavailableDates(this.listingSlug);
        this.hydrateBookingRules(data);
    }
    
    /**
     * Popola le regole di prenotazione dall'API
     * @private
     */
    hydrateBookingRules(data) {
        // Aggiorna stato con i dati ricevuti
        this.stateManager.updateState('singleCalendar.blockedRanges', data.blocked_ranges || []);
        this.stateManager.updateState('singleCalendar.checkinBlockedDates', new Set(data.checkin_block?.dates || []));
        this.stateManager.updateState('singleCalendar.checkoutBlockedDates', new Set(data.checkout_block?.dates || []));
        this.stateManager.updateState('singleCalendar.checkinBlockedWeekdays', new Set(data.checkin_block?.weekdays || []));
        this.stateManager.updateState('singleCalendar.checkoutBlockedWeekdays', new Set(data.checkout_block?.weekdays || []));
        this.stateManager.updateState('singleCalendar.turnoverDays', new Set(data.turnover_days || []));
        this.stateManager.updateState('singleCalendar.realCheckinDates', new Set(data.real_checkin_dates || []));
        
        // Aggiorna metadata
        if (data.metadata) {
            this.stateManager.updateState('singleCalendar.metadata', {
                minStay: data.metadata.min_stay || this.options.minStay,
                maxStay: data.metadata.max_stay || this.options.maxStay,
                gapBetweenBookings: data.metadata.gap_between_bookings || this.options.gapBetweenBookings
            });
        }
    }
    
    /**
     * Inizializza Flatpickr
     * @private
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
            maxDate: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000), // 1 anno
            disable: this.buildDisabledDates(),
            onDayCreate: this.onDayCreate.bind(this),
            onChange: this.onDateChange.bind(this),
            onReady: this.onCalendarReady.bind(this)
        };
        
        this.calendar = flatpickr(this.elements.calendarInput, config);
    }
    
    /**
     * Costruisce l'array delle date disabilitate
     * @private
     */
    buildDisabledDates() {
        const disabled = [];
        const blockedRanges = this.stateManager.getState('singleCalendar.blockedRanges');
        
        blockedRanges.forEach(range => {
            const start = this.dateUtils.parseDate(range.from);
            const end = this.dateUtils.parseDate(range.to);
            
            if (start && end) {
                const dates = this.dateUtils.getDateRange(start, end);
                dates.forEach(date => {
                    disabled.push(this.dateUtils.formatDate(date, 'YYYY-MM-DD'));
                });
            }
        });
        
        return disabled;
    }
    
    /**
     * Gestisce la creazione di un giorno nel calendario
     * @private
     */
    onDayCreate(dObj, dStr, fp, dayElem) {
        const date = dayElem.dateObj;
        if (!date) return;
        
        const isoDate = this.dateUtils.formatDate(date, 'YYYY-MM-DD');
        const pythonWeekday = this.dateUtils.toPythonWeekday(date.getDay());
        
        // Verifica se il giorno è bloccato per check-in
        const checkinBlockedDates = this.stateManager.getState('singleCalendar.checkinBlockedDates');
        const checkinBlockedWeekdays = this.stateManager.getState('singleCalendar.checkinBlockedWeekdays');
        const isCheckinBlocked = checkinBlockedDates.has(isoDate) || checkinBlockedWeekdays.has(pythonWeekday);
        
        // Verifica se il giorno è bloccato per check-out
        const checkoutBlockedDates = this.stateManager.getState('singleCalendar.checkoutBlockedDates');
        const checkoutBlockedWeekdays = this.stateManager.getState('singleCalendar.checkoutBlockedWeekdays');
        const isCheckoutBlocked = checkoutBlockedDates.has(isoDate) || checkoutBlockedWeekdays.has(pythonWeekday);
        
        // Applica stili
        if (isCheckinBlocked && !isCheckoutBlocked) {
            dayElem.classList.add('no-checkin-rule');
            dayElem.title = 'Check-in non permesso (disponibile per check-out)';
        } else if (isCheckoutBlocked && !isCheckinBlocked) {
            dayElem.title = 'Check-out non permesso';
        }
        
        // Giorni di turnover
        const turnoverDays = this.stateManager.getState('singleCalendar.turnoverDays');
        if (turnoverDays.has(isoDate)) {
            dayElem.classList.add('turnover-day');
            dayElem.title = 'Giorno di check-out (disponibile per nuovo check-in)';
        }
    }
    
    /**
     * Gestisce il cambio di date
     * @private
     */
    onDateChange(selectedDates, dateStr, instance) {
        this.stateManager.updateState('singleCalendar.selectedDates', selectedDates);
        
        if (selectedDates.length === 2) {
            this.calculatePrice(selectedDates[0], selectedDates[1]);
        } else {
            this.hidePriceBreakdown();
        }
    }
    
    /**
     * Gestisce il ready del calendario
     * @private
     */
    onCalendarReady(selectedDates, dateStr, instance) {
        console.log('Calendario Flatpickr pronto');
        this.updateCalendarDayStyles();
    }
    
    /**
     * Aggiorna gli stili dei giorni del calendario
     * @private
     */
    updateCalendarDayStyles() {
        if (!this.calendar || !this.calendar.calendarContainer) return;
        
        const dayElements = this.calendar.calendarContainer.querySelectorAll('.flatpickr-day');
        const selectedDates = this.stateManager.getState('singleCalendar.selectedDates');
        
        dayElements.forEach(dayElem => {
            const date = dayElem.dateObj;
            if (!date) return;
            
            const isoDate = this.dateUtils.formatDate(date, 'YYYY-MM-DD');
            const pythonWeekday = this.dateUtils.toPythonWeekday(date.getDay());
            
            // Reset classi dinamiche
            dayElem.classList.remove('available-for-checkout', 'no-checkout-rule');
            
            // Applica stili basati sullo stato di selezione
            if (selectedDates.length === 0) {
                this.applyInitialDayStyles(dayElem, date, isoDate, pythonWeekday);
            } else if (selectedDates.length === 1) {
                this.applyCheckinSelectedStyles(dayElem, date, isoDate, pythonWeekday, selectedDates[0]);
            }
        });
    }
    
    /**
     * Applica stili quando nessuna data è selezionata
     * @private
     */
    applyInitialDayStyles(dayElem, date, isoDate, pythonWeekday) {
        const checkinBlockedDates = this.stateManager.getState('singleCalendar.checkinBlockedDates');
        const checkinBlockedWeekdays = this.stateManager.getState('singleCalendar.checkinBlockedWeekdays');
        const checkoutBlockedDates = this.stateManager.getState('singleCalendar.checkoutBlockedDates');
        const checkoutBlockedWeekdays = this.stateManager.getState('singleCalendar.checkoutBlockedWeekdays');
        
        const isCheckinBlocked = checkinBlockedDates.has(isoDate) || checkinBlockedWeekdays.has(pythonWeekday);
        const isCheckoutBlocked = checkoutBlockedDates.has(isoDate) || checkoutBlockedWeekdays.has(pythonWeekday);
        
        if (isCheckinBlocked && !isCheckoutBlocked) {
            dayElem.classList.add('no-checkin-rule');
            dayElem.title = 'Check-in non permesso (disponibile per check-out)';
        } else if (isCheckoutBlocked && !isCheckinBlocked) {
            dayElem.title = 'Check-out non permesso';
        }
    }
    
    /**
     * Applica stili quando il check-in è selezionato
     * @private
     */
    applyCheckinSelectedStyles(dayElem, date, isoDate, pythonWeekday, checkInDate) {
        if (date <= checkInDate) {
            dayElem.classList.add('flatpickr-disabled');
            dayElem.title = 'Check-out deve essere dopo il check-in';
            return;
        }
        
        const checkinBlockedDates = this.stateManager.getState('singleCalendar.checkinBlockedDates');
        const checkinBlockedWeekdays = this.stateManager.getState('singleCalendar.checkinBlockedWeekdays');
        const checkoutBlockedDates = this.stateManager.getState('singleCalendar.checkoutBlockedDates');
        const checkoutBlockedWeekdays = this.stateManager.getState('singleCalendar.checkoutBlockedWeekdays');
        
        const isCheckinBlocked = checkinBlockedDates.has(isoDate) || checkinBlockedWeekdays.has(pythonWeekday);
        const isCheckoutBlocked = checkoutBlockedDates.has(isoDate) || checkoutBlockedWeekdays.has(pythonWeekday);
        
        if (isCheckoutBlocked) {
            dayElem.classList.add('flatpickr-disabled');
            dayElem.title = 'Check-out non permesso';
        } else if (isCheckinBlocked) {
            dayElem.classList.add('available-for-checkout');
            dayElem.title = 'Disponibile per check-out';
        }
    }
    
    /**
     * Calcola il prezzo per un periodo
     * @private
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
     * @private
     */
    getGuestsCount() {
        if (!this.elements.guestsSelect) return 1;
        
        const value = parseInt(this.elements.guestsSelect.value, 10);
        return Number.isFinite(value) && value > 0 ? value : 1;
    }
    
    /**
     * Mostra il breakdown del prezzo
     * @private
     */
    showPriceBreakdown(pricingData) {
        if (!this.elements.priceBreakdown) return;
        
        // TODO: Implementare la visualizzazione del breakdown
        console.log('Mostra breakdown prezzo:', pricingData);
    }
    
    /**
     * Nasconde il breakdown del prezzo
     * @private
     */
    hidePriceBreakdown() {
        if (!this.elements.priceBreakdown) return;
        
        // TODO: Implementare la nascondita del breakdown
        console.log('Nasconde breakdown prezzo');
    }
    
    /**
     * Configura la gestione degli errori
     * @private
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
     * @private
     */
    setupStateSubscriptions() {
        this.stateManager.subscribe('singleCalendar.selectedDates', (dates) => {
            this.updateCalendarDayStyles();
        });
        
        this.stateManager.subscribe('singleCalendar.loading', (loading) => {
            this.setLoadingState(loading);
        });
    }
    
    /**
     * Mostra un messaggio di disponibilità
     * @private
     */
    showAvailabilityMessage(message, type) {
        if (!this.elements.availabilityMessage) return;
        
        const textElement = this.elements.availabilityMessage.querySelector('#availability-text');
        if (textElement) {
            textElement.textContent = message;
        }
        
        this.elements.availabilityMessage.className = 'mt-2 p-2 rounded-lg';
        
        if (type === 'success') {
            this.elements.availabilityMessage.classList.add('bg-green-100', 'text-green-800');
        } else if (type === 'error') {
            this.elements.availabilityMessage.classList.add('bg-red-100', 'text-red-800');
        } else if (type === 'warning') {
            this.elements.availabilityMessage.classList.add('bg-yellow-100', 'text-yellow-800');
        }
    }
    
    /**
     * Imposta lo stato di caricamento
     * @private
     */
    setLoadingState(loading) {
        // TODO: Implementare UI di caricamento
        console.log('Loading state:', loading);
    }
    
    /**
     * Configura i listener degli eventi
     * @private
     */
    setupEventListeners() {
        // Listener per cambio numero ospiti
        if (this.elements.guestsSelect) {
            console.log('Aggiungendo listener per cambio ospiti');
            this.elements.guestsSelect.addEventListener('change', () => {
                const selectedDates = this.stateManager.getState('singleCalendar.selectedDates');
                if (selectedDates.length === 2) {
                    this.calculatePrice(selectedDates[0], selectedDates[1]);
                }
            });
        } else {
            console.warn('Elemento guestsSelect non trovato, listener non aggiunto');
        }
        
        // Listener per input nascosti
        if (this.elements.checkInInput) {
            console.log('Aggiungendo listener per check-in input');
            this.elements.checkInInput.addEventListener('change', () => {
                this.updateCalendarFromHiddenInputs();
            });
        }
        
        if (this.elements.checkOutInput) {
            console.log('Aggiungendo listener per check-out input');
            this.elements.checkOutInput.addEventListener('change', () => {
                this.updateCalendarFromHiddenInputs();
            });
        }
    }
    
    /**
     * Aggiorna il calendario dai valori degli input nascosti
     * @private
     */
    updateCalendarFromHiddenInputs() {
        if (!this.elements.checkInInput || !this.elements.checkOutInput) return;
        
        const checkIn = this.elements.checkInInput.value;
        const checkOut = this.elements.checkOutInput.value;
        
        if (checkIn && checkOut && this.calendar) {
            try {
                this.calendar.setDate([checkIn, checkOut]);
            } catch (error) {
                console.warn('Errore nell\'aggiornamento del calendario:', error);
            }
        }
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
        console.log('SingleCalendarManager distrutto');
    }
}

// Esporta per uso in altri moduli
window.SingleCalendarManager = SingleCalendarManager;
