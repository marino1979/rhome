/**
 * StateManager - Gestione stato globale dell'applicazione
 * 
 * Fornisce un sistema di gestione stato reattivo per il calendario
 * con sottoscrizioni e notifiche di cambiamento.
 */

class StateManager {
    constructor() {
        this.state = {};
        this.subscribers = {};
        this.loading = false;
    }

    /**
     * Aggiorna lo stato
     * @param {string} key - Chiave dello stato (supporta notazione dot)
     * @param {any} value - Nuovo valore
     */
    updateState(key, value) {
        const oldValue = this.getState(key);
        
        if (oldValue === value) {
            return; // Nessun cambiamento
        }

        this.setNestedValue(this.state, key, value);
        this.notifySubscribers(key, value, oldValue);
    }

    /**
     * Ottiene lo stato
     * @param {string} key - Chiave dello stato (supporta notazione dot)
     * @returns {any} Valore dello stato
     */
    getState(key) {
        return this.getNestedValue(this.state, key);
    }

    /**
     * Sottoscrive ai cambiamenti di stato
     * @param {string} key - Chiave dello stato
     * @param {Function} callback - Callback da chiamare
     */
    subscribe(key, callback) {
        if (!this.subscribers[key]) {
            this.subscribers[key] = [];
        }
        this.subscribers[key].push(callback);
    }

    /**
     * Disiscrive da un cambiamento di stato
     * @param {string} key - Chiave dello stato
     * @param {Function} callback - Callback da rimuovere
     */
    unsubscribe(key, callback) {
        if (this.subscribers[key]) {
            this.subscribers[key] = this.subscribers[key].filter(cb => cb !== callback);
        }
    }

    /**
     * Imposta lo stato di caricamento
     * @param {boolean} loading - Stato di caricamento
     */
    setLoading(loading) {
        this.loading = loading;
        this.notifySubscribers('loading', loading);
    }

    /**
     * Ottiene lo stato di caricamento
     * @returns {boolean} Stato di caricamento
     */
    isLoading() {
        return this.loading;
    }

    /**
     * Resetta tutto lo stato
     */
    reset() {
        this.state = {};
        this.subscribers = {};
        this.loading = false;
    }

    /**
     * Ottiene tutto lo stato
     * @returns {Object} Stato completo
     */
    getFullState() {
        return { ...this.state };
    }

    /**
     * Imposta un valore annidato nell'oggetto
     * @private
     */
    setNestedValue(obj, path, value) {
        const keys = path.split('.');
        let current = obj;

        for (let i = 0; i < keys.length - 1; i++) {
            const key = keys[i];
            if (!(key in current) || typeof current[key] !== 'object') {
                current[key] = {};
            }
            current = current[key];
        }

        current[keys[keys.length - 1]] = value;
    }

    /**
     * Ottiene un valore annidato dall'oggetto
     * @private
     */
    getNestedValue(obj, path) {
        const keys = path.split('.');
        let current = obj;

        for (const key of keys) {
            if (current === null || current === undefined || !(key in current)) {
                return undefined;
            }
            current = current[key];
        }

        return current;
    }

    /**
     * Notifica i sottoscrittori
     * @private
     */
    notifySubscribers(key, newValue, oldValue) {
        if (this.subscribers[key]) {
            this.subscribers[key].forEach(callback => {
                try {
                    callback(newValue, oldValue);
                } catch (error) {
                    console.error(`Errore nel callback per ${key}:`, error);
                }
            });
        }
    }
}

// Esporta per uso in altri moduli
window.StateManager = StateManager;
