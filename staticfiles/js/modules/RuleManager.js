/**
 * RuleManager - Gestione delle regole del calendario
 * 
 * Gestisce la logica delle regole di disponibilità e validazione
 * per il calendario di prenotazione.
 */

class RuleManager {
    constructor() {
        this.rules = {
            blockedRanges: [],
            checkinBlock: { dates: [], weekdays: [] },
            checkoutBlock: { dates: [], weekdays: [] },
            turnoverDays: [],
            realCheckinDates: [],
            metadata: {
                minStay: 1,
                maxStay: 30,
                gapBetweenBookings: 0
            }
        };
    }
    
    /**
     * Carica le regole dall'API
     * @param {Object} data - Dati ricevuti dall'API
     */
    loadRules(data) {
        this.rules = {
            blockedRanges: data.blocked_ranges || [],
            checkinBlock: data.checkin_block || { dates: [], weekdays: [] },
            checkoutBlock: data.checkout_block || { dates: [], weekdays: [] },
            turnoverDays: data.turnover_days || [],
            realCheckinDates: data.real_checkin_dates || [],
            metadata: data.metadata || {
                minStay: 1,
                maxStay: 30,
                gapBetweenBookings: 0
            }
        };
        
        console.log('Regole caricate:', this.rules);
    }

    /**
     * Ottiene le regole correnti
     * @returns {Object} Regole correnti
     */
    getRules() {
        return this.rules;
    }

    /**
     * Ottiene lo stato di un giorno specifico
     * @param {Date} date - Data da verificare
     * @param {Array} selectedDates - Date attualmente selezionate
     * @returns {Object} Stato del giorno
     */
    getDayState(date, selectedDates = []) {
        const isoDate = this.formatDateISO(date);
        const pythonWeekday = this.toPythonWeekday(date.getDay());
        
            return {
            date: date,
            isoDate: isoDate,
            pythonWeekday: pythonWeekday,
            isBlocked: this.isDateBlocked(date),
            isCheckinBlocked: this.isCheckinBlocked(date),
            isCheckoutBlocked: this.isCheckoutBlocked(date),
            isTurnover: this.isTurnoverDay(date),
            isSelected: this.isDateSelected(date, selectedDates),
            isInRange: this.isDateInRange(date, selectedDates)
        };
    }
    
    /**
     * Valida un range di date
     * @param {Date} startDate - Data di inizio
     * @param {Date} endDate - Data di fine
     * @returns {Object} Risultato della validazione
     */
    validateDateRange(startDate, endDate) {
        const validation = {
            valid: true,
            message: '',
            errors: []
        };

        // Verifica che le date siano valide
        if (!startDate || !endDate) {
            validation.valid = false;
            validation.errors.push('Date non valide');
            validation.message = 'Seleziona date valide';
            return validation;
        }

        // Verifica che la data di fine sia dopo quella di inizio
        if (endDate <= startDate) {
            validation.valid = false;
            validation.errors.push('Data check-out deve essere dopo check-in');
            validation.message = 'La data di check-out deve essere successiva al check-in';
            return validation;
        }
        
        // Verifica soggiorno minimo
        const nights = this.calculateNights(startDate, endDate);
        if (nights < this.rules.metadata.minStay) {
            validation.valid = false;
            validation.errors.push(`Soggiorno minimo: ${this.rules.metadata.minStay} notti`);
            validation.message = `Soggiorno minimo richiesto: ${this.rules.metadata.minStay} notti`;
            return validation;
        }
        
        // Verifica soggiorno massimo
        if (nights > this.rules.metadata.maxStay) {
            validation.valid = false;
            validation.errors.push(`Soggiorno massimo: ${this.rules.metadata.maxStay} notti`);
            validation.message = `Soggiorno massimo consentito: ${this.rules.metadata.maxStay} notti`;
            return validation;
        }

        // Verifica disponibilità per ogni giorno del range
        const availabilityCheck = this.checkRangeAvailability(startDate, endDate);
        if (!availabilityCheck.available) {
            validation.valid = false;
            validation.errors.push(availabilityCheck.message);
            validation.message = availabilityCheck.message;
            return validation;
        }

        return validation;
    }

    /**
     * Verifica se una data è bloccata
     * @private
     */
    isDateBlocked(date) {
        return this.rules.blockedRanges.some(range => {
            const start = new Date(range.from);
            const end = new Date(range.to);
            return date >= start && date <= end;
        });
    }

    /**
     * Verifica se check-in è bloccato per una data
     * @private
     */
    isCheckinBlocked(date) {
        const isoDate = this.formatDateISO(date);
        const pythonWeekday = this.toPythonWeekday(date.getDay());
        
        return this.rules.checkinBlock.dates.includes(isoDate) || 
               this.rules.checkinBlock.weekdays.includes(pythonWeekday);
    }

    /**
     * Verifica se check-out è bloccato per una data
     * @private
     */
    isCheckoutBlocked(date) {
        const isoDate = this.formatDateISO(date);
        const pythonWeekday = this.toPythonWeekday(date.getDay());
        
        return this.rules.checkoutBlock.dates.includes(isoDate) || 
               this.rules.checkoutBlock.weekdays.includes(pythonWeekday);
    }

    /**
     * Verifica se una data è giorno di turnover
     * @private
     */
    isTurnoverDay(date) {
        const isoDate = this.formatDateISO(date);
        return this.rules.turnoverDays.includes(isoDate);
    }

    /**
     * Verifica se una data è selezionata
     * @private
     */
    isDateSelected(date, selectedDates) {
        return selectedDates.some(selectedDate => 
            this.formatDateISO(selectedDate) === this.formatDateISO(date)
        );
    }

    /**
     * Verifica se una data è nel range selezionato
     * @private
     */
    isDateInRange(date, selectedDates) {
        if (selectedDates.length !== 2) return false;
        
        const start = selectedDates[0];
        const end = selectedDates[1];
        
        return date > start && date < end;
    }

    /**
     * Verifica disponibilità per un range di date
     * @private
     */
    checkRangeAvailability(startDate, endDate) {
        const currentDate = new Date(startDate);
        
        while (currentDate < endDate) {
            // Verifica se il giorno è bloccato
            if (this.isDateBlocked(currentDate)) {
                return {
                    available: false,
                    message: `Data ${this.formatDateISO(currentDate)} non disponibile`
                };
            }
            
            // Verifica se check-in è bloccato per il primo giorno
            if (currentDate.getTime() === startDate.getTime() && this.isCheckinBlocked(currentDate)) {
                return {
                    available: false,
                    message: `Check-in non permesso il ${this.formatDateISO(currentDate)}`
                };
            }
            
            // Verifica se check-out è bloccato per l'ultimo giorno
            const nextDay = new Date(currentDate);
            nextDay.setDate(nextDay.getDate() + 1);
            if (nextDay.getTime() === endDate.getTime() && this.isCheckoutBlocked(currentDate)) {
        return {
                    available: false,
                    message: `Check-out non permesso il ${this.formatDateISO(currentDate)}`
                };
            }
            
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        return { available: true, message: 'Disponibile' };
    }
    
    /**
     * Calcola il numero di notti tra due date
     * @private
     */
    calculateNights(startDate, endDate) {
        const timeDiff = endDate.getTime() - startDate.getTime();
        return Math.ceil(timeDiff / (1000 * 3600 * 24));
    }
    
    /**
     * Formatta una data in formato ISO
     * @private
     */
    formatDateISO(date) {
        return date.toISOString().split('T')[0];
    }
    
    /**
     * Converte weekday JavaScript in Python weekday
     * @private
     */
    toPythonWeekday(jsWeekday) {
        // JS: 0=domenica, 1=lunedì, ..., 6=sabato
        // Python: 0=lunedì, 1=martedì, ..., 6=domenica
        return (jsWeekday + 6) % 7;
    }
    
    /**
     * Ottiene le date disponibili per check-in in un range
     * @param {Date} startDate - Data di inizio del range
     * @param {Date} endDate - Data di fine del range
     * @returns {Array} Array di date disponibili per check-in
     */
    getAvailableCheckinDates(startDate, endDate) {
        const availableDates = [];
        const currentDate = new Date(startDate);
        
        while (currentDate <= endDate) {
            if (!this.isDateBlocked(currentDate) && !this.isCheckinBlocked(currentDate)) {
                availableDates.push(new Date(currentDate));
            }
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        return availableDates;
    }

    /**
     * Ottiene le date disponibili per check-out in un range
     * @param {Date} startDate - Data di inizio del range
     * @param {Date} endDate - Data di fine del range
     * @returns {Array} Array di date disponibili per check-out
     */
    getAvailableCheckoutDates(startDate, endDate) {
        const availableDates = [];
        const currentDate = new Date(startDate);
        
        while (currentDate <= endDate) {
            if (!this.isDateBlocked(currentDate) && !this.isCheckoutBlocked(currentDate)) {
                availableDates.push(new Date(currentDate));
            }
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        return availableDates;
    }
}

// Esporta per uso in altri moduli
window.RuleManager = RuleManager;