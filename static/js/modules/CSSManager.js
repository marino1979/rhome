/**
 * CSSManager - Gestione degli stili del calendario
 * 
 * Gestisce l'applicazione dinamica degli stili CSS per il calendario
 * basandosi sullo stato delle date e delle regole.
 */

class CSSManager {
    constructor() {
        this.styles = {
            // Stili per giorni bloccati
            blocked: 'flatpickr-disabled',
            // Stili per giorni di check-in bloccati
            noCheckin: 'no-checkin-rule',
            // Stili per giorni di check-out bloccati
            noCheckout: 'no-checkout-rule',
            // Stili per giorni di turnover
            turnover: 'turnover-day',
            // Stili per giorni disponibili per check-out
            availableForCheckout: 'available-for-checkout',
            // Stili per giorni selezionati
            selected: 'selected',
            // Stili per giorni in range
            inRange: 'inRange'
        };
        
        this.setupCustomStyles();
    }

    /**
     * Applica stili a un elemento giorno
     * @param {HTMLElement} dayElement - Elemento del giorno
     * @param {Object} dayState - Stato del giorno
     */
    applyDayStyles(dayElement, dayState) {
        if (!dayElement || !dayState) return;

        // Rimuovi tutti gli stili dinamici
        this.removeDynamicStyles(dayElement);

        // Applica stili basati sullo stato
        if (dayState.isBlocked) {
            dayElement.classList.add(this.styles.blocked);
            dayElement.title = 'Non disponibile';
        }

        if (dayState.isCheckinBlocked) {
            dayElement.classList.add(this.styles.noCheckin);
            dayElement.title = 'Check-in non permesso';
        }

        if (dayState.isCheckoutBlocked) {
            dayElement.classList.add(this.styles.noCheckout);
            dayElement.title = 'Check-out non permesso';
        }

        if (dayState.isTurnover) {
            dayElement.classList.add(this.styles.turnover);
            dayElement.title = 'Giorno di turnover (disponibile per check-in)';
        }

        if (dayState.isAvailableForCheckout) {
            dayElement.classList.add(this.styles.availableForCheckout);
            dayElement.title = 'Disponibile per check-out';
        }

        // Applica stili per selezione
        if (dayState.isSelected) {
            dayElement.classList.add(this.styles.selected);
        }

        if (dayState.isInRange) {
            dayElement.classList.add(this.styles.inRange);
        }
    }

    /**
     * Aggiorna gli stili del calendario
     * @param {Object} calendar - Istanza Flatpickr
     * @param {Object} rules - Regole del calendario
     * @param {Array} selectedDates - Date selezionate
     */
    updateCalendarStyles(calendar, rules, selectedDates) {
        if (!calendar || !calendar.calendarContainer) return;

        const dayElements = calendar.calendarContainer.querySelectorAll('.flatpickr-day');
        
        dayElements.forEach(dayElement => {
            const date = dayElement.dateObj;
            if (!date) return;

            const dayState = this.calculateDayState(date, rules, selectedDates);
            this.applyDayStyles(dayElement, dayState);
        });
    }

    /**
     * Calcola lo stato di un giorno
     * @private
     */
    calculateDayState(date, rules, selectedDates) {
        const isoDate = this.formatDateISO(date);
        const pythonWeekday = this.toPythonWeekday(date.getDay());
        
        const state = {
            date: date,
            isoDate: isoDate,
            pythonWeekday: pythonWeekday,
            isBlocked: false,
            isCheckinBlocked: false,
            isCheckoutBlocked: false,
            isTurnover: false,
            isAvailableForCheckout: false,
            isSelected: false,
            isInRange: false
        };

        // Verifica se è bloccato
        if (rules.blockedRanges) {
            state.isBlocked = this.isDateInBlockedRanges(date, rules.blockedRanges);
        }

        // Verifica se check-in è bloccato
        if (rules.checkinBlock) {
            state.isCheckinBlocked = this.isCheckinBlocked(date, rules.checkinBlock);
        }

        // Verifica se check-out è bloccato
        if (rules.checkoutBlock) {
            state.isCheckoutBlocked = this.isCheckoutBlocked(date, rules.checkoutBlock);
        }

        // Verifica se è giorno di turnover
        if (rules.turnoverDays) {
            state.isTurnover = rules.turnoverDays.includes(isoDate);
        }

        // Verifica selezione
        if (selectedDates && selectedDates.length > 0) {
            state.isSelected = selectedDates.some(selectedDate => 
                this.formatDateISO(selectedDate) === isoDate
            );
            
            if (selectedDates.length === 2) {
                state.isInRange = this.isDateInRange(date, selectedDates[0], selectedDates[1]);
            }
        }

        // Verifica disponibilità per check-out
        if (selectedDates && selectedDates.length === 1) {
            state.isAvailableForCheckout = this.isAvailableForCheckout(date, selectedDates[0], rules);
        }

        return state;
    }

    /**
     * Verifica se una data è in range bloccati
     * @private
     */
    isDateInBlockedRanges(date, blockedRanges) {
        return blockedRanges.some(range => {
            const start = new Date(range.from);
            const end = new Date(range.to);
            return date >= start && date <= end;
        });
    }

    /**
     * Verifica se check-in è bloccato
     * @private
     */
    isCheckinBlocked(date, checkinBlock) {
        const isoDate = this.formatDateISO(date);
        const pythonWeekday = this.toPythonWeekday(date.getDay());
        
        return checkinBlock.dates.includes(isoDate) || 
               checkinBlock.weekdays.includes(pythonWeekday);
    }

    /**
     * Verifica se check-out è bloccato
     * @private
     */
    isCheckoutBlocked(date, checkoutBlock) {
        const isoDate = this.formatDateISO(date);
        const pythonWeekday = this.toPythonWeekday(date.getDay());
        
        return checkoutBlock.dates.includes(isoDate) || 
               checkoutBlock.weekdays.includes(pythonWeekday);
    }

    /**
     * Verifica se una data è in un range
     * @private
     */
    isDateInRange(date, startDate, endDate) {
        return date > startDate && date < endDate;
    }

    /**
     * Verifica se una data è disponibile per check-out
     * @private
     */
    isAvailableForCheckout(date, checkInDate, rules) {
        if (date <= checkInDate) return false;
        
        // Non deve essere bloccata per check-out
        if (rules.checkoutBlock && this.isCheckoutBlocked(date, rules.checkoutBlock)) {
            return false;
        }
        
        // Non deve essere in range bloccati
        if (rules.blockedRanges && this.isDateInBlockedRanges(date, rules.blockedRanges)) {
            return false;
        }
        
        return true;
    }

    /**
     * Rimuove tutti gli stili dinamici
     * @private
     */
    removeDynamicStyles(dayElement) {
        Object.values(this.styles).forEach(styleClass => {
            dayElement.classList.remove(styleClass);
        });
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
     * Configura stili CSS personalizzati
     * @private
     */
    setupCustomStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Stili per giorni bloccati */
            .flatpickr-day.no-checkin-rule {
                background-color: #ffebee !important;
                color: #c62828 !important;
                cursor: not-allowed !important;
                position: relative;
            }
            
            .flatpickr-day.no-checkin-rule:after {
                content: '🚫';
                position: absolute;
                top: 2px;
                right: 2px;
                font-size: 10px;
            }
            
            /* Stili per giorni di turnover */
            .flatpickr-day.turnover-day {
                background-color: #e8f5e8 !important;
                color: #2e7d32 !important;
                position: relative;
            }
            
            .flatpickr-day.turnover-day:after {
                content: '✓';
                position: absolute;
                top: 2px;
                right: 2px;
                font-size: 10px;
                font-weight: bold;
            }
            
            /* Stili per giorni disponibili per check-out */
            .flatpickr-day.available-for-checkout {
                background-color: #e3f2fd !important;
                color: #1565c0 !important;
            }
            
            /* Stili per giorni selezionati */
            .flatpickr-day.selected {
                background-color: #1976d2 !important;
                color: white !important;
            }
            
            /* Stili per giorni in range */
            .flatpickr-day.inRange {
                background-color: #bbdefb !important;
                color: #0d47a1 !important;
            }
            
            /* Hover effects */
            .flatpickr-day:not(.flatpickr-disabled):hover {
                background-color: #f5f5f5 !important;
            }
            
            .flatpickr-day.turnover-day:hover {
                background-color: #c8e6c9 !important;
            }
            
            .flatpickr-day.available-for-checkout:hover {
                background-color: #bbdefb !important;
            }
        `;
        
        document.head.appendChild(style);
    }
}

// Esporta per uso in altri moduli
window.CSSManager = CSSManager;