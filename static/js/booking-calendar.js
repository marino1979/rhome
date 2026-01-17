/**
 * Booking Calendar - Stile Airbnb
 *
 * Calendario interattivo per selezione date prenotazione con:
 * - Selezione range check-in/check-out
 * - Visualizzazione prezzi per notte
 * - Indicatori visivi per disponibilità
 * - Calcolo prezzo totale in tempo reale
 */

class BookingCalendar {
    constructor(options) {
        this.listingId = options.listingId;
        this.isCombined = options.isCombined || false; // Modalità combinata (tutti i gruppi)
        this.containerEl = document.querySelector(options.container);
        this.onDateSelect = options.onDateSelect || (() => {});
        this.onPriceUpdate = options.onPriceUpdate || (() => {});
        this.onError = options.onError || null; // Callback per errori persistenti
        this.monthsToShow = options.monthsToShow || 2; // Numero di mesi da mostrare (default 2)

        // Stato
        this.currentMonth = new Date();
        this.selectedCheckIn = null;
        this.selectedCheckOut = null;
        this.isSelectingCheckOut = false;
        this.hoverDate = null;

        // Dati dal backend
        this.blockedDates = new Set();
        this.checkinDisabled = new Set();
        this.checkoutDisabled = new Set();
        this.blockedReasons = {}; // Mappa date -> motivo blocco
        this.prices = {};
        this.minStay = 1;
        this.gapDays = 0;
        this.listingInfo = null;
        this.bookings = []; // Array delle prenotazioni per trovare la prossima
        this.groups = []; // Gruppi di appartamenti (solo per modalità combinata)

        // Cache
        this.loadedMonths = new Set();

        this.init();
    }

    async init() {
        if (!this.containerEl) {
            console.error('Container element not found');
            return;
        }

        // Mostra loading
        this.showLoading();

        // Carica info listing
        await this.loadListingInfo();

        // Carica dati calendario per i prossimi 3 mesi
        await this.loadCalendarData(this.currentMonth, 3);

        // Render iniziale
        this.render();

        // Setup event listeners (event delegation)
        this.setupEventListeners();
    }

    async loadListingInfo() {
        // In modalità combinata, non carichiamo info su un singolo listing
        if (this.isCombined) {
            this.listingInfo = {
                title: 'Ricerca Combinata',
                description: 'Disponibilità aggregata di tutti gli appartamenti'
            };
            return;
        }

        try {
            const response = await fetch(`/calendar/api/listings/${this.listingId}/info/`);
            if (!response.ok) throw new Error('Failed to load listing info');
            this.listingInfo = await response.json();
        } catch (error) {
            console.error('Error loading listing info:', error);
        }
    }

    async loadCalendarData(startMonth, monthsAhead = 2) {
        const startDate = new Date(startMonth.getFullYear(), startMonth.getMonth(), 1);
        const endDate = new Date(startMonth.getFullYear(), startMonth.getMonth() + monthsAhead, 0);

        const startStr = this.formatDate(startDate);
        const endStr = this.formatDate(endDate);

        try {
            let response, data;

            if (this.isCombined) {
                // Modalità combinata: usa API aggregata
                response = await fetch(
                    `/calendar/api/calendar/combined/?start=${startStr}&end=${endStr}`
                );
            } else {
                // Modalità singola: usa API per listing specifico
                response = await fetch(
                    `/calendar/api/listings/${this.listingId}/calendar/?start=${startStr}&end=${endStr}`
                );
            }

            if (!response.ok) throw new Error('Failed to load calendar data');

            data = await response.json();

            // Aggiorna stato
            data.blocked_dates.forEach(date => this.blockedDates.add(date));
            data.checkin_disabled.forEach(date => this.checkinDisabled.add(date));
            data.checkout_disabled.forEach(date => this.checkoutDisabled.add(date));
            Object.assign(this.prices, data.prices);
            this.minStay = data.min_stay;
            this.gapDays = data.gap_days;

            // Se modalità combinata, salva anche i gruppi
            if (this.isCombined && data.groups) {
                this.groups = data.groups;
            }

            // Salva informazioni per motivi di blocco
            if (data.bookings) {
                data.bookings.forEach(booking => {
                    this.bookings.push({
                        check_in: booking.check_in,
                        check_out: booking.check_out
                    });
                });
            }

            // Costruisci mappa motivi di blocco
            if (data.blocked_dates) {
                data.blocked_dates.forEach(date => {
                    this.blockedReasons[date] = this.blockedReasons[date] || 'Non disponibile';
                });
            }

            if (data.checkin_disabled) {
                data.checkin_disabled.forEach(date => {
                    this.blockedReasons[date] = 'Check-in non disponibile in questa data';
                });
            }

            if (data.checkout_disabled) {
                data.checkout_disabled.forEach(date => {
                    this.blockedReasons[date] = 'Check-out non disponibile in questa data';
                });
            }

            // Marca mesi come caricati
            for (let i = 0; i < monthsAhead; i++) {
                const monthKey = this.getMonthKey(new Date(startDate.getFullYear(), startDate.getMonth() + i, 1));
                this.loadedMonths.add(monthKey);
            }

        } catch (error) {
            console.error('Error loading calendar data:', error);
            this.showError('Errore caricamento calendario');
        }
    }

    render() {
        this.containerEl.innerHTML = '';

        // Header con navigazione mesi
        const header = this.createHeader();
        this.containerEl.appendChild(header);

        // Calendario con numero variabile di mesi
        const calendarsContainer = document.createElement('div');
        calendarsContainer.className = 'calendars-container';

        // Crea i mesi richiesti
        for (let i = 0; i < this.monthsToShow; i++) {
            const monthDate = new Date(this.currentMonth);
            monthDate.setMonth(this.currentMonth.getMonth() + i);
            const calendar = this.createMonthCalendar(monthDate);
            calendarsContainer.appendChild(calendar);
        }

        this.containerEl.appendChild(calendarsContainer);

        // Footer con info selezione
        const footer = this.createFooter();
        this.containerEl.appendChild(footer);
    }

    createHeader() {
        const header = document.createElement('div');
        header.className = 'calendar-header';

        const prevBtn = document.createElement('button');
        prevBtn.className = 'calendar-nav-btn calendar-nav-prev';
        prevBtn.innerHTML = '←';
        prevBtn.onclick = () => this.previousMonth();

        const nextBtn = document.createElement('button');
        nextBtn.className = 'calendar-nav-btn calendar-nav-next';
        nextBtn.innerHTML = '→';
        nextBtn.onclick = () => this.nextMonth();

        const title = document.createElement('div');
        title.className = 'calendar-title';
        title.textContent = 'Seleziona le date';

        header.appendChild(prevBtn);
        header.appendChild(title);
        header.appendChild(nextBtn);

        return header;
    }

    createMonthCalendar(month) {
        const calendar = document.createElement('div');
        calendar.className = 'month-calendar';

        // Header mese
        const monthHeader = document.createElement('div');
        monthHeader.className = 'month-header';
        monthHeader.textContent = this.formatMonthYear(month);
        calendar.appendChild(monthHeader);

        // Giorni settimana
        const weekdays = document.createElement('div');
        weekdays.className = 'weekdays';
        ['Dom', 'Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab'].forEach(day => {
            const dayEl = document.createElement('div');
            dayEl.className = 'weekday';
            dayEl.textContent = day;
            weekdays.appendChild(dayEl);
        });
        calendar.appendChild(weekdays);

        // Griglia giorni
        const daysGrid = document.createElement('div');
        daysGrid.className = 'days-grid';

        const firstDay = new Date(month.getFullYear(), month.getMonth(), 1);
        const lastDay = new Date(month.getFullYear(), month.getMonth() + 1, 0);
        const startPadding = firstDay.getDay(); // 0 = domenica

        // Padding iniziale
        for (let i = 0; i < startPadding; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'day-cell empty';
            daysGrid.appendChild(emptyDay);
        }

        // Giorni del mese
        for (let day = 1; day <= lastDay.getDate(); day++) {
            const date = new Date(month.getFullYear(), month.getMonth(), day);
            const dayCell = this.createDayCell(date);
            daysGrid.appendChild(dayCell);
        }

        calendar.appendChild(daysGrid);
        return calendar;
    }

    createDayCell(date) {
        const cell = document.createElement('div');
        cell.className = 'day-cell';

        const dateStr = this.formatDate(date);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Classe base
        cell.dataset.date = dateStr;

        // Stati
        const isPast = date < today;
        const isBlocked = this.blockedDates.has(dateStr);
        const isCheckinDisabled = this.checkinDisabled.has(dateStr);
        const isCheckoutDisabled = this.checkoutDisabled.has(dateStr);
        const isAfterNextBooking = this.isDateAfterNextBooking(dateStr);
        const isSelected = this.isDateSelected(dateStr);
        const isInRange = this.isDateInRange(dateStr);
        const isHovered = this.hoverDate && this.isDateInHoverRange(dateStr);

        // Variabile per tracciare se il giorno è cliccabile
        // In modalità combinata, ignora blocchi da disponibilità
        let isClickable = !isPast;
        if (!this.isCombined) {
            // Solo in modalità singolo listing applica blocchi da prenotazioni
            isClickable = isClickable && !isBlocked;
        }
        let tooltipMessage = '';

        // Gestione stati e tooltip
        if (isPast) {
            cell.classList.add('past');
            tooltipMessage = 'Data passata';
            isClickable = false;
        } else if (isBlocked && !this.isCombined) {
            // Solo in modalità singolo listing mostra blocchi
            cell.classList.add('blocked');
            tooltipMessage = this.blockedReasons[dateStr] || 'Non disponibile';
            isClickable = false;
        }

        // Logica specifica per check-in vs check-out
        if (!this.selectedCheckIn || !this.isSelectingCheckOut) {
            // Modalità selezione check-in
            if (isCheckinDisabled && isClickable && !this.isCombined) {
                // Solo in modalità singolo listing
                cell.classList.add('checkin-disabled');
                tooltipMessage = 'Check-in non disponibile in questa data';
                isClickable = false;
            }
        } else if (this.isSelectingCheckOut) {
            // Modalità selezione check-out
            if (isAfterNextBooking && isClickable && !this.isCombined) {
                // Solo in modalità singolo listing
                cell.classList.add('after-next-booking');
                tooltipMessage = 'Non disponibile: prenotazione esistente';
                isClickable = false;
            } else if (isCheckoutDisabled && isClickable && !this.isCombined) {
                // Solo in modalità singolo listing
                cell.classList.add('checkout-disabled');
                tooltipMessage = 'Check-out non disponibile in questa data';
                isClickable = false;
            } else if (new Date(dateStr) <= new Date(this.selectedCheckIn)) {
                // Non può fare check-out prima o nello stesso giorno del check-in
                tooltipMessage = 'Check-out deve essere dopo il check-in';
                isClickable = false;
            }
        }

        // Applica classi di selezione
        if (isSelected) cell.classList.add('selected');
        if (isInRange) cell.classList.add('in-range');
        if (isHovered) cell.classList.add('hover-range');

        // Check-in/out specifici
        if (dateStr === this.selectedCheckIn) cell.classList.add('check-in');
        if (dateStr === this.selectedCheckOut) cell.classList.add('check-out');

        // Aggiungi tooltip se presente
        if (tooltipMessage) {
            cell.setAttribute('title', tooltipMessage);
        }

        // Numero giorno
        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = date.getDate();
        cell.appendChild(dayNumber);

        // Prezzo - solo in modalità singolo listing
        if (!isPast && !isBlocked && this.prices[dateStr] && !this.isCombined) {
            const price = document.createElement('div');
            price.className = 'day-price';
            price.textContent = `€${Math.round(this.prices[dateStr])}`;
            cell.appendChild(price);
        }

        // Eventi click
        if (isClickable) {
            cell.onclick = () => this.selectDate(dateStr);
        }

        return cell;
    }

    createFooter() {
        const footer = document.createElement('div');
        footer.className = 'calendar-footer';

        if (this.selectedCheckIn && this.selectedCheckOut) {
            const nights = this.calculateNights();

            footer.innerHTML = `
                <div class="selection-info">
                    <div class="selected-dates">
                        <span class="check-in-date">${this.formatDateDisplay(this.selectedCheckIn)}</span>
                        <span class="arrow">→</span>
                        <span class="check-out-date">${this.formatDateDisplay(this.selectedCheckOut)}</span>
                    </div>
                    <div class="nights-info">${nights} ${nights === 1 ? 'notte' : 'notti'}</div>
                    <div class="hint-reset">Clicca su una data per selezionare un nuovo periodo</div>
                </div>
            `;

            // Carica prezzo
            this.updatePrice();
        } else if (this.selectedCheckIn) {
            const nextBooking = this.findNextBookingAfter(this.selectedCheckIn);
            const maxDateMsg = nextBooking
                ? `<div class="calendar-message info">
                     <strong>Nota:</strong> La prossima prenotazione inizia il ${this.formatDateDisplay(nextBooking)}
                   </div>`
                : '';

            footer.innerHTML = `
                <div class="selection-info">
                    <div class="hint">Seleziona la data di check-out</div>
                    <div class="min-stay-hint">Soggiorno minimo: ${this.minStay} ${this.minStay === 1 ? 'notte' : 'notti'}</div>
                    ${maxDateMsg}
                </div>
            `;
        } else {
            footer.innerHTML = `
                <div class="selection-info">
                    <div class="hint">Seleziona le date del soggiorno</div>
                    <div class="calendar-message info">
                        <strong>Legenda:</strong><br>
                        🔴 Rosso = Check-in non disponibile<br>
                        🟠 Arancione = Check-out non disponibile<br>
                        ⚪ Grigio = Data già prenotata
                    </div>
                </div>
            `;
        }

        return footer;
    }

    selectDate(dateStr) {
        // Se c'è già un range completo selezionato, reset e ricomincia
        if (this.selectedCheckIn && this.selectedCheckOut) {
            this.clearDates();
            this.selectedCheckIn = dateStr;
            this.isSelectingCheckOut = true;
            this.render();
            return;
        }

        if (!this.selectedCheckIn) {
            // Seleziona check-in
            this.selectedCheckIn = dateStr;
            this.isSelectingCheckOut = true;
        } else if (this.isSelectingCheckOut) {
            // Seleziona check-out
            const checkInDate = new Date(this.selectedCheckIn);
            const checkOutDate = new Date(dateStr);

            // Verifica che check-out sia dopo check-in
            if (checkOutDate <= checkInDate) {
                // Reset e ricomincia
                this.selectedCheckIn = dateStr;
                this.selectedCheckOut = null;
                this.isSelectingCheckOut = true;
            } else {
                // Verifica soggiorno minimo
                const nights = this.calculateNightsBetween(this.selectedCheckIn, dateStr);
                if (nights < this.minStay) {
                    this.showMessage(
                        `Soggiorno minimo richiesto: ${this.minStay} ${this.minStay === 1 ? 'notte' : 'notti'}`,
                        'warning'
                    );
                    return;
                }

                this.selectedCheckOut = dateStr;
                this.isSelectingCheckOut = false;

                // Prima verifica la disponibilità, poi chiama il callback solo se OK
                this.checkAvailability().then(isAvailable => {
                    if (isAvailable) {
                        // Callback solo se disponibile
                        this.onDateSelect({
                            checkIn: this.selectedCheckIn,
                            checkOut: this.selectedCheckOut,
                            nights: nights
                        });
                    }
                });
            }
        }

        this.render();
    }

    showMessage(text, type = 'info') {
        /**
         * Mostra un messaggio informativo nel footer del calendario
         * type: 'info', 'warning', 'error'
         */
        const footer = this.containerEl.querySelector('.calendar-footer');
        if (!footer) return;

        // Rimuovi messaggi precedenti
        const existingMsg = footer.querySelector('.calendar-message.temporary');
        if (existingMsg) existingMsg.remove();

        // Crea nuovo messaggio
        const message = document.createElement('div');
        message.className = `calendar-message temporary ${type}`;
        message.innerHTML = `<strong>${type === 'error' ? 'Errore:' : type === 'warning' ? 'Attenzione:' : 'Nota:'}</strong> ${text}`;

        footer.appendChild(message);

        // Rimuovi dopo 5 secondi
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    }

    handleHover(dateStr) {
        if (!this.isSelectingCheckOut || !this.selectedCheckIn) return;
        if (this.hoverDate === dateStr) return; // No change needed

        this.hoverDate = dateStr;
        this.clearHoverRangeClasses();
        this.applyHoverRangeClasses();
    }

    handleHoverOut() {
        if (!this.hoverDate) return;

        this.hoverDate = null;
        this.clearHoverRangeClasses();
    }

    isDateSelected(dateStr) {
        return dateStr === this.selectedCheckIn || dateStr === this.selectedCheckOut;
    }

    isDateInRange(dateStr) {
        if (!this.selectedCheckIn || !this.selectedCheckOut) return false;
        const date = new Date(dateStr);
        const checkIn = new Date(this.selectedCheckIn);
        const checkOut = new Date(this.selectedCheckOut);
        return date > checkIn && date < checkOut;
    }

    isDateInHoverRange(dateStr) {
        if (!this.isSelectingCheckOut || !this.selectedCheckIn || !this.hoverDate) return false;

        const date = new Date(dateStr);
        const checkIn = new Date(this.selectedCheckIn);
        const hover = new Date(this.hoverDate);

        // Support both forward and backward selection
        const start = hover < checkIn ? hover : checkIn;
        const end = hover < checkIn ? checkIn : hover;

        // Include both boundaries
        return date >= start && date <= end;
    }

    findNextBookingAfter(checkInStr) {
        /**
         * Trova la prossima prenotazione dopo la data di check-in specificata
         * Returns: data di check-in della prossima prenotazione o null
         */
        if (!checkInStr || this.bookings.length === 0) return null;

        const checkInDate = new Date(checkInStr);
        let nextBooking = null;

        for (const booking of this.bookings) {
            const bookingCheckIn = new Date(booking.check_in);

            // Trova la prenotazione più vicina che inizia dopo il check-in
            if (bookingCheckIn > checkInDate) {
                if (!nextBooking || bookingCheckIn < new Date(nextBooking.check_in)) {
                    nextBooking = booking;
                }
            }
        }

        return nextBooking ? nextBooking.check_in : null;
    }

    isDateAfterNextBooking(dateStr) {
        /**
         * Verifica se una data è dopo la prossima prenotazione
         * (quindi non selezionabile come check-out)
         */
        if (!this.selectedCheckIn) return false;

        const nextBookingDate = this.findNextBookingAfter(this.selectedCheckIn);
        if (!nextBookingDate) return false;

        const date = new Date(dateStr);
        const nextBooking = new Date(nextBookingDate);

        return date >= nextBooking;
    }

    clearHoverRangeClasses() {
        // Remove all hover-range classes and reset border-radius
        const hoverCells = this.containerEl.querySelectorAll('.hover-range');
        hoverCells.forEach(cell => {
            cell.classList.remove('hover-range');
            cell.style.borderRadius = '';
        });
    }

    applyHoverRangeClasses() {
        if (!this.hoverDate || !this.selectedCheckIn) return;

        const checkIn = new Date(this.selectedCheckIn);
        const hover = new Date(this.hoverDate);

        // Support both forward and backward selection
        const start = hover < checkIn ? hover : checkIn;
        const end = hover < checkIn ? checkIn : hover;

        const allCells = this.containerEl.querySelectorAll('.day-cell[data-date]');
        const rangeCells = [];

        allCells.forEach(cell => {
            const dateStr = cell.dataset.date;
            const cellDate = new Date(dateStr);

            if (cellDate >= start && cellDate <= end) {
                cell.classList.add('hover-range');
                rangeCells.push(cell);
            }
        });

        // Apply border-radius to first and last
        if (rangeCells.length > 0) {
            rangeCells[0].style.borderRadius = '8px 0 0 8px';
            rangeCells[rangeCells.length - 1].style.borderRadius = '0 8px 8px 0';

            // If only one cell, make it fully rounded
            if (rangeCells.length === 1) {
                rangeCells[0].style.borderRadius = '8px';
            }
        }
    }

    setupEventListeners() {
        const calendarsContainer = this.containerEl.querySelector('.calendars-container');
        if (!calendarsContainer) return;

        // Event delegation for hover
        calendarsContainer.addEventListener('mouseover', (e) => {
            const cell = e.target.closest('.day-cell[data-date]');
            if (cell && !cell.classList.contains('blocked') && !cell.classList.contains('past')) {
                this.handleHover(cell.dataset.date);
            }
        });

        // Clear hover when leaving calendar area
        calendarsContainer.addEventListener('mouseleave', () => {
            this.handleHoverOut();
        });
    }

    calculateNights() {
        if (!this.selectedCheckIn || !this.selectedCheckOut) return 0;
        return this.calculateNightsBetween(this.selectedCheckIn, this.selectedCheckOut);
    }

    calculateNightsBetween(date1Str, date2Str) {
        const date1 = new Date(date1Str);
        const date2 = new Date(date2Str);
        const diffTime = date2 - date1;
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }

    async checkAvailability() {
        // In modalità combinata, non verifichiamo disponibilità qui
        // (verrà verificata dall'API combined-availability quando si cercano le combinazioni)
        if (this.isCombined) {
            return true; // Assume disponibile, sarà verificato dopo
        }

        try {
            const response = await fetch(`/calendar/api/listings/${this.listingId}/check-availability/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    check_in: this.selectedCheckIn,
                    check_out: this.selectedCheckOut
                })
            });

            const data = await response.json();

            if (!data.available) {
                // Mostra errore nel calendario
                this.showMessage(`Non disponibile: ${data.message}`, 'error');

                // Se esiste un callback onError, chiamalo per mostrare l'errore nella sidebar
                if (this.onError) {
                    this.onError(data.message);
                }

                // Pulisce le date dopo 3 secondi per dare tempo di leggere l'errore
                setTimeout(() => {
                    this.clearDates();
                }, 3000);

                return false; // Non disponibile
            }

            return true; // Disponibile
        } catch (error) {
            console.error('Error checking availability:', error);
            this.showMessage('Errore durante la verifica della disponibilità', 'error');

            if (this.onError) {
                this.onError('Errore durante la verifica della disponibilità');
            }

            return false; // Errore = non disponibile
        }
    }

    async updatePrice() {
        // In modalità combinata, non calcoliamo prezzi (verrà fatto dopo la ricerca)
        if (this.isCombined) return;

        if (!this.selectedCheckIn || !this.selectedCheckOut) return;

        // Leggi il numero di ospiti dal DOM se presente, altrimenti usa default 2
        let numGuests = 2;
        const guestsInput = document.getElementById('numGuests');
        if (guestsInput) {
            numGuests = parseInt(guestsInput.value) || 2;
        }

        try {
            const response = await fetch(`/calendar/api/listings/${this.listingId}/calculate-price/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    check_in: this.selectedCheckIn,
                    check_out: this.selectedCheckOut,
                    num_guests: numGuests
                })
            });

            const pricing = await response.json();
            this.onPriceUpdate(pricing);
        } catch (error) {
            console.error('Error calculating price:', error);
        }
    }

    clearDates() {
        this.selectedCheckIn = null;
        this.selectedCheckOut = null;
        this.isSelectingCheckOut = false;
        this.hoverDate = null;
        this.render();
        this.onDateSelect(null);
        this.onPriceUpdate(null);
    }

    async previousMonth() {
        this.currentMonth = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() - 1, 1);

        // Carica dati se necessario
        const monthKey = this.getMonthKey(this.currentMonth);
        if (!this.loadedMonths.has(monthKey)) {
            await this.loadCalendarData(this.currentMonth, 2);
        }

        this.render();
    }

    async nextMonth() {
        this.currentMonth = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() + 1, 1);

        // Carica dati se necessario
        const nextMonth = this.getNextMonth(this.currentMonth);
        const nextMonthKey = this.getMonthKey(nextMonth);
        if (!this.loadedMonths.has(nextMonthKey)) {
            await this.loadCalendarData(this.currentMonth, 2);
        }

        this.render();
    }

    getNextMonth(date) {
        return new Date(date.getFullYear(), date.getMonth() + 1, 1);
    }

    getMonthKey(date) {
        return `${date.getFullYear()}-${date.getMonth()}`;
    }

    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    formatMonthYear(date) {
        const months = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                       'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'];
        return `${months[date.getMonth()]} ${date.getFullYear()}`;
    }

    formatDateDisplay(dateStr) {
        const date = new Date(dateStr);
        const day = date.getDate();
        const month = date.toLocaleDateString('it-IT', { month: 'short' });
        return `${day} ${month}`;
    }

    showLoading() {
        this.containerEl.innerHTML = '<div class="calendar-loading">Caricamento calendario...</div>';
    }

    showError(message) {
        this.containerEl.innerHTML = `<div class="calendar-error">${message}</div>`;
    }
}

// Export per uso globale
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BookingCalendar;
}
