/**
 * DateUtils - Utility per la gestione delle date
 * 
 * Fornisce funzioni di utilità per la manipolazione e formattazione
 * delle date nel calendario.
 */

const DateUtils = {
    /**
     * Formatta una data in formato ISO (YYYY-MM-DD)
     * @param {Date} date - Data da formattare
     * @returns {string} Data formattata
     */
    formatDateISO(date) {
        if (!date) return '';
        return date.toISOString().split('T')[0];
    },

    /**
     * Formatta una data in formato italiano (DD/MM/YYYY)
     * @param {Date} date - Data da formattare
     * @returns {string} Data formattata
     */
    formatDateItalian(date) {
        if (!date) return '';
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
    },

    /**
     * Formatta una data in formato personalizzato
     * @param {Date} date - Data da formattare
     * @param {string} format - Formato desiderato (YYYY-MM-DD, DD/MM/YYYY, etc.)
     * @returns {string} Data formattata
     */
    formatDate(date, format = 'YYYY-MM-DD') {
        if (!date) return '';
        
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day);
    },

    /**
     * Converte una stringa in oggetto Date
     * @param {string} dateString - Stringa della data
     * @returns {Date|null} Oggetto Date o null se non valido
     */
    parseDate(dateString) {
        if (!dateString) return null;
        
        const date = new Date(dateString);
        return isNaN(date.getTime()) ? null : date;
    },

    /**
     * Converte weekday JavaScript in Python weekday
     * @param {number} jsWeekday - Weekday JavaScript (0=domenica, 1=lunedì, etc.)
     * @returns {number} Weekday Python (0=lunedì, 1=martedì, etc.)
     */
    toPythonWeekday(jsWeekday) {
        return (jsWeekday + 6) % 7;
    },

    /**
     * Converte weekday Python in JavaScript weekday
     * @param {number} pythonWeekday - Weekday Python (0=lunedì, 1=martedì, etc.)
     * @returns {number} Weekday JavaScript (0=domenica, 1=lunedì, etc.)
     */
    toJSWeekday(pythonWeekday) {
        return (pythonWeekday + 1) % 7;
    },

    /**
     * Ottiene il nome del giorno della settimana
     * @param {Date} date - Data
     * @param {string} locale - Locale (default: 'it')
     * @returns {string} Nome del giorno
     */
    getDayName(date, locale = 'it') {
        if (!date) return '';
        return date.toLocaleDateString(locale, { weekday: 'long' });
    },

    /**
     * Ottiene il nome abbreviato del giorno della settimana
     * @param {Date} date - Data
     * @param {string} locale - Locale (default: 'it')
     * @returns {string} Nome abbreviato del giorno
     */
    getDayNameShort(date, locale = 'it') {
        if (!date) return '';
        return date.toLocaleDateString(locale, { weekday: 'short' });
    },

    /**
     * Calcola il numero di giorni tra due date
     * @param {Date} startDate - Data di inizio
     * @param {Date} endDate - Data di fine
     * @returns {number} Numero di giorni
     */
    daysBetween(startDate, endDate) {
        if (!startDate || !endDate) return 0;
        
        const timeDiff = endDate.getTime() - startDate.getTime();
        return Math.ceil(timeDiff / (1000 * 3600 * 24));
    },

    /**
     * Calcola il numero di notti tra due date
     * @param {Date} startDate - Data di inizio
     * @param {Date} endDate - Data di fine
     * @returns {number} Numero di notti
     */
    nightsBetween(startDate, endDate) {
        return Math.max(0, this.daysBetween(startDate, endDate));
    },

    /**
     * Genera un array di date tra due date
     * @param {Date} startDate - Data di inizio
     * @param {Date} endDate - Data di fine
     * @param {boolean} inclusive - Include le date di inizio e fine
     * @returns {Array<Date>} Array di date
     */
    getDateRange(startDate, endDate, inclusive = true) {
        if (!startDate || !endDate) return [];
        
        const dates = [];
        const current = new Date(startDate);
        const end = new Date(endDate);
        
        if (!inclusive) {
            current.setDate(current.getDate() + 1);
            end.setDate(end.getDate() - 1);
        }
        
        while (current <= end) {
            dates.push(new Date(current));
            current.setDate(current.getDate() + 1);
        }
        
        return dates;
    },

    /**
     * Verifica se una data è oggi
     * @param {Date} date - Data da verificare
     * @returns {boolean} True se è oggi
     */
    isToday(date) {
        if (!date) return false;
        
        const today = new Date();
        return date.toDateString() === today.toDateString();
    },

    /**
     * Verifica se una data è nel passato
     * @param {Date} date - Data da verificare
     * @returns {boolean} True se è nel passato
     */
    isPast(date) {
        if (!date) return false;
        
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        date.setHours(0, 0, 0, 0);
        
        return date < today;
    },

    /**
     * Verifica se una data è nel futuro
     * @param {Date} date - Data da verificare
     * @returns {boolean} True se è nel futuro
     */
    isFuture(date) {
        if (!date) return false;
        
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        date.setHours(0, 0, 0, 0);
        
        return date > today;
    },

    /**
     * Verifica se una data è in un range
     * @param {Date} date - Data da verificare
     * @param {Date} startDate - Data di inizio del range
     * @param {Date} endDate - Data di fine del range
     * @param {boolean} inclusive - Include le date di inizio e fine
     * @returns {boolean} True se è nel range
     */
    isInRange(date, startDate, endDate, inclusive = true) {
        if (!date || !startDate || !endDate) return false;
        
        if (inclusive) {
            return date >= startDate && date <= endDate;
        } else {
            return date > startDate && date < endDate;
        }
    },

    /**
     * Aggiunge giorni a una data
     * @param {Date} date - Data base
     * @param {number} days - Numero di giorni da aggiungere
     * @returns {Date} Nuova data
     */
    addDays(date, days) {
        if (!date) return null;
        
        const newDate = new Date(date);
        newDate.setDate(newDate.getDate() + days);
        return newDate;
    },

    /**
     * Sottrae giorni da una data
     * @param {Date} date - Data base
     * @param {number} days - Numero di giorni da sottrarre
     * @returns {Date} Nuova data
     */
    subtractDays(date, days) {
        return this.addDays(date, -days);
    },

    /**
     * Ottiene la data di inizio del mese
     * @param {Date} date - Data di riferimento
     * @returns {Date} Primo giorno del mese
     */
    getMonthStart(date) {
        if (!date) return null;
        
        return new Date(date.getFullYear(), date.getMonth(), 1);
    },

    /**
     * Ottiene la data di fine del mese
     * @param {Date} date - Data di riferimento
     * @returns {Date} Ultimo giorno del mese
     */
    getMonthEnd(date) {
        if (!date) return null;
        
        return new Date(date.getFullYear(), date.getMonth() + 1, 0);
    },

    /**
     * Verifica se due date sono lo stesso giorno
     * @param {Date} date1 - Prima data
     * @param {Date} date2 - Seconda data
     * @returns {boolean} True se sono lo stesso giorno
     */
    isSameDay(date1, date2) {
        if (!date1 || !date2) return false;
        
        return date1.toDateString() === date2.toDateString();
    },

    /**
     * Ottiene il numero del giorno della settimana (1=lunedì, 7=domenica)
     * @param {Date} date - Data
     * @returns {number} Numero del giorno
     */
    getWeekdayNumber(date) {
        if (!date) return 0;
        
        const weekday = date.getDay();
        return weekday === 0 ? 7 : weekday;
    },

    /**
     * Formatta una durata in giorni e notti
     * @param {number} days - Numero di giorni
     * @returns {string} Durata formattata
     */
    formatDuration(days) {
        if (days <= 0) return '0 notti';
        if (days === 1) return '1 notte';
        return `${days} notti`;
    },

    /**
     * Ottiene la data di oggi senza ore
     * @returns {Date} Data di oggi alle 00:00:00
     */
    getToday() {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return today;
    },

    /**
     * Ottiene la data di domani senza ore
     * @returns {Date} Data di domani alle 00:00:00
     */
    getTomorrow() {
        return this.addDays(this.getToday(), 1);
    }
};

// Esporta per uso globale
window.DateUtils = DateUtils;