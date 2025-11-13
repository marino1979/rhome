/**
 * APIClient - Cliente per le chiamate API del calendario
 * 
 * Gestisce tutte le comunicazioni con il backend per:
 * - Verifica disponibilità
 * - Calcolo prezzi
 * - Gestione prenotazioni
 */

class APIClient {
    constructor() {
        this.baseURL = window.location.origin;
        this.endpoints = {
            checkAvailability: '/prenotazioni/api/check-availability/',
            getCalendar: '/prenotazioni/api/calendar/',
            createBooking: '/prenotazioni/create/',
            combinedAvailability: '/prenotazioni/api/combined-availability/',
            createCombinedBooking: '/prenotazioni/api/combined-booking/'
        };
    }
    
    /**
     * Ottiene le date non disponibili per un listing
     * @param {string|number} listingIdentifier - ID o slug del listing
     * @returns {Promise<Object>} Dati di disponibilità
     */
    async getUnavailableDates(listingIdentifier) {
        try {
            // Determina se è un ID numerico o uno slug
            const isNumeric = /^\d+$/.test(listingIdentifier);
            const endpoint = isNumeric 
                ? `${this.endpoints.getCalendar}${listingIdentifier}/`
                : `/prenotazioni/api/calendar/slug/${listingIdentifier}/`;

            const response = await fetch(endpoint, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Se è un endpoint per slug, estrai i dati del calendario
            if (data.success && data.calendar_data) {
                return data.calendar_data;
            }
            
            return data;

        } catch (error) {
            console.error('Errore nel recupero date non disponibili:', error);
            throw new Error(`Impossibile caricare le date di disponibilità: ${error.message}`);
        }
    }

    /**
     * Verifica disponibilità per un periodo specifico
     * @param {Object} requestData - Dati della richiesta
     * @returns {Promise<Object>} Risultato della verifica
     */
    async checkAvailability(requestData) {
        try {
            const response = await fetch(this.endpoints.checkAvailability, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('Errore nella verifica disponibilità:', error);
            throw new Error(`Impossibile verificare la disponibilità: ${error.message}`);
        }
    }

    /**
     * Calcola il prezzo per un periodo
     * @param {Object} requestData - Dati della richiesta
     * @returns {Promise<Object>} Dati di pricing
     */
    async calculatePrice(requestData) {
        try {
            const response = await fetch(this.endpoints.checkAvailability, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (!data.available) {
                throw new Error(data.error || 'Periodo non disponibile');
            }

            return data.pricing;
            
        } catch (error) {
            console.error('Errore nel calcolo prezzo:', error);
            throw new Error(`Impossibile calcolare il prezzo: ${error.message}`);
        }
    }

    /**
     * Formatta i dati per una richiesta di prezzo
     * @param {string|number} listingId - ID del listing
     * @param {Date} checkIn - Data check-in
     * @param {Date} checkOut - Data check-out
     * @param {number} guests - Numero ospiti
     * @returns {Object} Dati formattati
     */
    formatPriceRequest(listingId, checkIn, checkOut, guests) {
        return {
            listing_id: parseInt(listingId),
            check_in: this.formatDate(checkIn),
            check_out: this.formatDate(checkOut),
            num_guests: parseInt(guests)
        };
    }

    /**
     * Crea una prenotazione
     * @param {Object} bookingData - Dati della prenotazione
     * @returns {Promise<Object>} Risultato della creazione
     */
    async createBooking(bookingData) {
        try {
            const response = await fetch(this.endpoints.createBooking, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(bookingData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('Errore nella creazione prenotazione:', error);
            throw new Error(`Impossibile creare la prenotazione: ${error.message}`);
        }
    }

    /**
     * Cerca disponibilità combinata per più appartamenti
     * @param {Object} searchData - Dati di ricerca
     * @returns {Promise<Object>} Risultati della ricerca
     */
    async searchCombinedAvailability(searchData) {
        try {
            const response = await fetch(this.endpoints.combinedAvailability, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(searchData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('Errore nella ricerca combinata:', error);
            throw new Error(`Impossibile cercare disponibilità combinata: ${error.message}`);
        }
    }

    /**
     * Ottiene il token CSRF
     * @returns {string} Token CSRF
     */
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    /**
     * Formatta una data in formato YYYY-MM-DD
     * @param {Date} date - Data da formattare
     * @returns {string} Data formattata
     */
    formatDate(date) {
        if (!date) return '';
        
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        
        return `${year}-${month}-${day}`;
    }
    
    /**
     * Gestisce gli errori di rete
     * @param {Error} error - Errore da gestire
     * @returns {string} Messaggio di errore user-friendly
     */
    handleNetworkError(error) {
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            return 'Errore di connessione. Verifica la tua connessione internet.';
        }
        
        if (error.message.includes('404')) {
            return 'Servizio non trovato. Riprova più tardi.';
        }
        
        if (error.message.includes('500')) {
            return 'Errore del server. Riprova più tardi.';
        }
        
        return error.message || 'Errore sconosciuto';
    }
}

// Esporta per uso in altri moduli
window.APIClient = APIClient;