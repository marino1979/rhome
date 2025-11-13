/**
 * ErrorHandler - Gestione centralizzata degli errori
 * 
 * Fornisce un sistema di gestione errori con categorizzazione,
 * logging e notifiche user-friendly.
 */

class ErrorHandler {
    constructor() {
        this.errorTypes = {
            NETWORK: 'network',
            SERVER: 'server',
            VALIDATION: 'validation',
            CALENDAR: 'calendar',
            PRICING: 'pricing',
            BOOKING: 'booking'
        };
        
        this.errorCallbacks = {};
        this.setupGlobalErrorHandling();
    }

    /**
     * Gestisce un errore
     * @param {Error|string} error - Errore da gestire
     * @param {Object} context - Contesto dell'errore
     */
    handle(error, context = {}) {
        const errorInfo = this.categorizeError(error, context);
        
        // Log dell'errore
        this.logError(errorInfo);
        
        // Notifica i callback specifici
        this.notifyCallbacks(errorInfo);
        
        // Gestione globale se nessun callback specifico
        if (!this.errorCallbacks[errorInfo.type]) {
            this.handleGlobalError(errorInfo);
        }
    }

    /**
     * Registra un callback per un tipo di errore
     * @param {string} errorType - Tipo di errore
     * @param {Function} callback - Callback da chiamare
     */
    onError(errorType, callback) {
        if (!this.errorCallbacks[errorType]) {
            this.errorCallbacks[errorType] = [];
        }
        this.errorCallbacks[errorType].push(callback);
    }

    /**
     * Rimuove un callback per un tipo di errore
     * @param {string} errorType - Tipo di errore
     * @param {Function} callback - Callback da rimuovere
     */
    offError(errorType, callback) {
        if (this.errorCallbacks[errorType]) {
            this.errorCallbacks[errorType] = this.errorCallbacks[errorType].filter(cb => cb !== callback);
        }
    }

    /**
     * Categorizza un errore
     * @private
     */
    categorizeError(error, context) {
        const errorMessage = typeof error === 'string' ? error : error.message;
        const errorStack = error.stack || '';
        
        let type = this.errorTypes.SERVER;
        let userMessage = 'Si è verificato un errore imprevisto.';
        
        // Categorizzazione basata sul messaggio
        if (errorMessage.includes('fetch') || errorMessage.includes('network') || errorMessage.includes('connessione')) {
            type = this.errorTypes.NETWORK;
            userMessage = 'Errore di connessione. Verifica la tua connessione internet.';
        } else if (errorMessage.includes('disponibilità') || errorMessage.includes('calendario')) {
            type = this.errorTypes.CALENDAR;
            userMessage = 'Errore nel calendario. Ricarica la pagina.';
        } else if (errorMessage.includes('prezzo') || errorMessage.includes('pricing')) {
            type = this.errorTypes.PRICING;
            userMessage = 'Errore nel calcolo del prezzo. Riprova.';
        } else if (errorMessage.includes('prenotazione') || errorMessage.includes('booking')) {
            type = this.errorTypes.BOOKING;
            userMessage = 'Errore nella prenotazione. Riprova.';
        } else if (errorMessage.includes('validazione') || errorMessage.includes('validation')) {
            type = this.errorTypes.VALIDATION;
            userMessage = errorMessage; // Usa il messaggio originale per errori di validazione
        }
        
        return {
            originalError: error,
            message: errorMessage,
            stack: errorStack,
            type: type,
            userMessage: userMessage,
            context: context,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Logga un errore
     * @private
     */
    logError(errorInfo) {
        console.group(`🚨 Errore ${errorInfo.type.toUpperCase()}`);
        console.error('Messaggio:', errorInfo.message);
        console.error('Contesto:', errorInfo.context);
        console.error('Timestamp:', errorInfo.timestamp);
        if (errorInfo.stack) {
            console.error('Stack:', errorInfo.stack);
        }
        console.groupEnd();
    }

    /**
     * Notifica i callback registrati
     * @private
     */
    notifyCallbacks(errorInfo) {
        const callbacks = this.errorCallbacks[errorInfo.type];
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(errorInfo.originalError, errorInfo.context);
                } catch (callbackError) {
                    console.error('Errore nel callback di gestione errori:', callbackError);
                }
            });
        }
    }

    /**
     * Gestione globale degli errori
     * @private
     */
    handleGlobalError(errorInfo) {
        // Mostra notifica globale
        this.showGlobalNotification(errorInfo.userMessage, 'error');
    }

    /**
     * Mostra una notifica globale
     * @private
     */
    showGlobalNotification(message, type = 'error') {
        // Crea elemento notifica
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-sm ${
            type === 'error' ? 'bg-red-500 text-white' : 
            type === 'warning' ? 'bg-yellow-500 text-black' : 
            'bg-blue-500 text-white'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="mr-2">${type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}</span>
                <span>${message}</span>
                <button class="ml-2 text-lg leading-none" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Rimuovi automaticamente dopo 5 secondi
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Configura la gestione globale degli errori
     * @private
     */
    setupGlobalErrorHandling() {
        // Gestione errori JavaScript non catturati
        window.addEventListener('error', (event) => {
            this.handle(event.error, {
                context: 'global-error',
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });

        // Gestione Promise rifiutate non gestite
        window.addEventListener('unhandledrejection', (event) => {
            this.handle(event.reason, {
                context: 'unhandled-promise-rejection'
            });
        });
    }

    /**
     * Crea un errore personalizzato
     * @param {string} message - Messaggio dell'errore
     * @param {string} type - Tipo dell'errore
     * @param {Object} context - Contesto aggiuntivo
     * @returns {Error} Errore personalizzato
     */
    createError(message, type = this.errorTypes.SERVER, context = {}) {
        const error = new Error(message);
        error.type = type;
        error.context = context;
        return error;
    }

    /**
     * Verifica se un errore è di un tipo specifico
     * @param {Error} error - Errore da verificare
     * @param {string} type - Tipo da verificare
     * @returns {boolean} True se l'errore è del tipo specificato
     */
    isErrorType(error, type) {
        return error.type === type || 
               (error.message && error.message.toLowerCase().includes(type.toLowerCase()));
    }
}

// Esporta per uso in altri moduli
window.ErrorHandler = ErrorHandler;