/**
 * UIComponents - Componenti UI riutilizzabili
 * 
 * Fornisce componenti UI standardizzati per il calendario
 * e le prenotazioni.
 */

class UIComponents {
    /**
     * Crea un indicatore di caricamento
     * @param {string} message - Messaggio da mostrare
     * @param {string} size - Dimensione ('small', 'medium', 'large')
     * @returns {HTMLElement} Elemento di caricamento
     */
    static createLoadingIndicator(message = 'Caricamento...', size = 'medium') {
        const sizes = {
            small: 'h-4 w-4',
            medium: 'h-8 w-8',
            large: 'h-12 w-12'
        };
        
        const container = document.createElement('div');
        container.className = 'flex items-center justify-center p-4';
        container.innerHTML = `
            <div class="flex flex-col items-center">
                <div class="animate-spin rounded-full border-b-2 border-blue-500 ${sizes[size]} mb-2"></div>
                <div class="text-sm text-gray-600">${message}</div>
            </div>
        `;
        
        return container;
    }
    
    /**
     * Crea una notifica
     * @param {string} message - Messaggio da mostrare
     * @param {string} type - Tipo di notifica ('success', 'error', 'warning', 'info')
     * @param {number} duration - Durata in millisecondi (0 = permanente)
     * @returns {HTMLElement} Elemento notifica
     */
    static createNotification(message, type = 'info', duration = 5000) {
        const typeClasses = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-black',
            info: 'bg-blue-500 text-white'
        };
        
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-sm ${typeClasses[type]} transform transition-all duration-300 ease-in-out`;
        notification.style.transform = 'translateX(100%)';
        
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="mr-2 text-lg">${icons[type]}</span>
                <span class="flex-1">${message}</span>
                <button class="ml-2 text-lg leading-none hover:opacity-75" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animazione di entrata
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Rimozione automatica
        if (duration > 0) {
            setTimeout(() => {
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }, duration);
        }
        
        return notification;
    }

    /**
     * Crea un messaggio di disponibilità
     * @param {string} message - Messaggio da mostrare
     * @param {string} type - Tipo di messaggio
     * @returns {HTMLElement} Elemento messaggio
     */
    static createAvailabilityMessage(message, type = 'info') {
        const typeClasses = {
            success: 'bg-green-100 text-green-800 border-green-200',
            error: 'bg-red-100 text-red-800 border-red-200',
            warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
            info: 'bg-blue-100 text-blue-800 border-blue-200'
        };
        
        const messageElement = document.createElement('div');
        messageElement.className = `mt-2 p-3 rounded-lg border ${typeClasses[type]}`;
        messageElement.innerHTML = `
            <div class="flex items-center">
                <span class="text-sm">${message}</span>
            </div>
        `;
        
        return messageElement;
    }

    /**
     * Crea un breakdown del prezzo
     * @param {Object} pricing - Dati di pricing
     * @returns {HTMLElement} Elemento breakdown prezzo
     */
    static createPriceBreakdown(pricing) {
        const breakdown = document.createElement('div');
        breakdown.className = 'border-t pt-4 mt-4';
        breakdown.innerHTML = `
                <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                    <span>Prezzo base (${pricing.total_nights} notti)</span>
                    <span>€${pricing.subtotal.toFixed(2)}</span>
                </div>
                ${pricing.cleaning_fee > 0 ? `
                    <div class="flex justify-between">
                        <span>Pulizie</span>
                        <span>€${pricing.cleaning_fee.toFixed(2)}</span>
                    </div>
                ` : ''}
                ${pricing.extra_guest_fee > 0 ? `
                    <div class="flex justify-between">
                        <span>Ospiti extra</span>
                        <span>€${pricing.extra_guest_fee.toFixed(2)}</span>
                    </div>
                ` : ''}
                    <div class="flex justify-between font-semibold border-t pt-2 text-base">
                        <span>Totale</span>
                    <span>€${pricing.total_amount.toFixed(2)}</span>
                    </div>
            </div>
        `;
        
        return breakdown;
    }
    
    /**
     * Crea un pulsante
     * @param {string} text - Testo del pulsante
     * @param {string} type - Tipo di pulsante ('primary', 'secondary', 'danger')
     * @param {Function} onClick - Callback per il click
     * @param {boolean} disabled - Se il pulsante è disabilitato
     * @returns {HTMLElement} Elemento pulsante
     */
    static createButton(text, type = 'primary', onClick = null, disabled = false) {
        const typeClasses = {
            primary: 'bg-blue-600 hover:bg-blue-700 text-white',
            secondary: 'bg-gray-600 hover:bg-gray-700 text-white',
            danger: 'bg-red-600 hover:bg-red-700 text-white',
            success: 'bg-green-600 hover:bg-green-700 text-white'
        };
        
        const button = document.createElement('button');
        button.className = `px-4 py-2 rounded-md font-medium transition-colors duration-200 ${typeClasses[type]} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`;
        button.textContent = text;
        button.disabled = disabled;
        
        if (onClick && !disabled) {
            button.addEventListener('click', onClick);
        }
        
        return button;
    }
    
    /**
     * Crea un input di testo
     * @param {string} placeholder - Placeholder del campo
     * @param {string} value - Valore iniziale
     * @param {Function} onChange - Callback per il cambio
     * @returns {HTMLElement} Elemento input
     */
    static createTextInput(placeholder = '', value = '', onChange = null) {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent';
        input.placeholder = placeholder;
        input.value = value;
        
        if (onChange) {
            input.addEventListener('input', onChange);
        }
        
        return input;
    }

    /**
     * Crea un select
     * @param {Array} options - Opzioni del select
     * @param {string} selectedValue - Valore selezionato
     * @param {Function} onChange - Callback per il cambio
     * @returns {HTMLElement} Elemento select
     */
    static createSelect(options, selectedValue = '', onChange = null) {
        const select = document.createElement('select');
        select.className = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent';
        
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.value;
            optionElement.textContent = option.text;
            optionElement.selected = option.value === selectedValue;
            select.appendChild(optionElement);
        });
        
        if (onChange) {
            select.addEventListener('change', onChange);
        }
        
        return select;
    }
    
    /**
     * Crea un modal
     * @param {string} title - Titolo del modal
     * @param {HTMLElement|string} content - Contenuto del modal
     * @param {Array} buttons - Array di pulsanti
     * @returns {HTMLElement} Elemento modal
     */
    static createModal(title, content, buttons = []) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'bg-white rounded-lg shadow-xl max-w-md w-full mx-4';
        
        modalContent.innerHTML = `
            <div class="p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">${title}</h3>
                <div class="mb-6">
                    ${typeof content === 'string' ? content : content.outerHTML}
                </div>
                <div class="flex justify-end space-x-3">
                    ${buttons.map(button => button.outerHTML).join('')}
                </div>
            </div>
        `;
        
        modal.appendChild(modalContent);
        
        // Chiudi modal cliccando fuori
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // Chiudi modal con ESC
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', handleKeyDown);
            }
        };
        document.addEventListener('keydown', handleKeyDown);
        
        return modal;
    }
    
    /**
     * Crea un tooltip
     * @param {HTMLElement} target - Elemento target
     * @param {string} text - Testo del tooltip
     * @param {string} position - Posizione ('top', 'bottom', 'left', 'right')
     * @returns {HTMLElement} Elemento tooltip
     */
    static createTooltip(target, text, position = 'top') {
        const tooltip = document.createElement('div');
        tooltip.className = `absolute z-50 px-2 py-1 text-xs text-white bg-gray-900 rounded shadow-lg opacity-0 transition-opacity duration-200 pointer-events-none`;
        tooltip.textContent = text;
        
        // Posiziona il tooltip
        const updatePosition = () => {
            const targetRect = target.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            
            switch (position) {
                case 'top':
                    tooltip.style.left = `${targetRect.left + targetRect.width / 2 - tooltipRect.width / 2}px`;
                    tooltip.style.top = `${targetRect.top - tooltipRect.height - 8}px`;
                    break;
                case 'bottom':
                    tooltip.style.left = `${targetRect.left + targetRect.width / 2 - tooltipRect.width / 2}px`;
                    tooltip.style.top = `${targetRect.bottom + 8}px`;
                    break;
                case 'left':
                    tooltip.style.left = `${targetRect.left - tooltipRect.width - 8}px`;
                    tooltip.style.top = `${targetRect.top + targetRect.height / 2 - tooltipRect.height / 2}px`;
                    break;
                case 'right':
                    tooltip.style.left = `${targetRect.right + 8}px`;
                    tooltip.style.top = `${targetRect.top + targetRect.height / 2 - tooltipRect.height / 2}px`;
                    break;
            }
        };
        
        // Mostra tooltip
        target.addEventListener('mouseenter', () => {
            document.body.appendChild(tooltip);
            updatePosition();
            tooltip.style.opacity = '1';
        });
        
        // Nascondi tooltip
        target.addEventListener('mouseleave', () => {
            tooltip.style.opacity = '0';
            setTimeout(() => {
                if (tooltip.parentElement) {
                    tooltip.remove();
                }
            }, 200);
        });
        
        return tooltip;
    }
    
    /**
     * Mostra un modal di conferma
     * @param {string} message - Messaggio di conferma
     * @param {Function} onConfirm - Callback per conferma
     * @param {Function} onCancel - Callback per annullamento
     * @returns {HTMLElement} Elemento modal
     */
    static showConfirmModal(message, onConfirm = null, onCancel = null) {
        const confirmButton = this.createButton('Conferma', 'primary', () => {
            modal.remove();
            if (onConfirm) onConfirm();
        });
        
        const cancelButton = this.createButton('Annulla', 'secondary', () => {
            modal.remove();
            if (onCancel) onCancel();
        });
        
        const modal = this.createModal('Conferma', message, [cancelButton, confirmButton]);
        document.body.appendChild(modal);
        
        return modal;
    }

    /**
     * Mostra un modal di errore
     * @param {string} message - Messaggio di errore
     * @param {Function} onClose - Callback per chiusura
     * @returns {HTMLElement} Elemento modal
     */
    static showErrorModal(message, onClose = null) {
        const closeButton = this.createButton('Chiudi', 'primary', () => {
            modal.remove();
            if (onClose) onClose();
        });
        
        const modal = this.createModal('Errore', message, [closeButton]);
        document.body.appendChild(modal);
        
        return modal;
    }
}

// Esporta per uso globale
window.UIComponents = UIComponents;