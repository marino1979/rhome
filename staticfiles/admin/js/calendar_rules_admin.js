// JavaScript per interfaccia admin tipo Airbnb
document.addEventListener('DOMContentLoaded', function() {
    
    // Inizializza tooltip
    initTooltips();
    
    // Inizializza preview prezzi
    initPricePreview();
    
    // Inizializza template buttons
    initTemplateButtons();
    
    // Inizializza calendario interattivo
    initInteractiveCalendar();
    
    // Inizializza validazione form
    initFormValidation();
});

function initTooltips() {
    const tooltips = document.querySelectorAll('.tooltip');
    
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function() {
            const tooltipText = this.dataset.tooltip;
            if (tooltipText) {
                showTooltip(this, tooltipText);
            }
        });
        
        tooltip.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    // Rimuovi tooltip esistente
    hideTooltip();
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip-popup';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #2c3e50;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        z-index: 1000;
        max-width: 250px;
        word-wrap: break-word;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    `;
    
    document.body.appendChild(tooltip);
    
    // Posiziona il tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
    
    // Assicurati che sia visibile
    const tooltipRect = tooltip.getBoundingClientRect();
    if (tooltipRect.left < 0) {
        tooltip.style.left = '10px';
    }
    if (tooltipRect.right > window.innerWidth) {
        tooltip.style.left = (window.innerWidth - tooltipRect.width - 10) + 'px';
    }
}

function hideTooltip() {
    const existingTooltip = document.querySelector('.tooltip-popup');
    if (existingTooltip) {
        existingTooltip.remove();
    }
}

function initPricePreview() {
    const basePriceInput = document.querySelector('#id_base_price');
    const multiplierInput = document.querySelector('#id_price_multiplier');
    
    if (basePriceInput && multiplierInput) {
        function updatePreview() {
            const basePrice = parseFloat(basePriceInput.value) || 0;
            const multiplier = parseFloat(multiplierInput.value) || 1.0;
            const finalPrice = basePrice * multiplier;
            const change = ((multiplier - 1) * 100);
            
            // Aggiorna elementi preview se esistono
            const previewBase = document.getElementById('preview-base');
            const previewMultiplier = document.getElementById('preview-multiplier');
            const previewFinal = document.getElementById('preview-final');
            const previewChange = document.getElementById('preview-change');
            
            if (previewBase) previewBase.textContent = '€' + basePrice.toFixed(2);
            if (previewMultiplier) previewMultiplier.textContent = multiplier.toFixed(2) + 'x';
            if (previewFinal) previewFinal.textContent = '€' + finalPrice.toFixed(2);
            if (previewChange) {
                previewChange.textContent = (change >= 0 ? '+' : '') + change.toFixed(0) + '%';
                previewChange.style.color = change > 0 ? '#f44336' : change < 0 ? '#4caf50' : 'white';
            }
        }
        
        basePriceInput.addEventListener('input', updatePreview);
        multiplierInput.addEventListener('input', updatePreview);
        updatePreview(); // Inizializza
    }
}

function initTemplateButtons() {
    const templateButtons = document.querySelectorAll('.template-btn');
    
    templateButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Rimuovi selezione precedente
            templateButtons.forEach(btn => {
                btn.style.borderColor = '#e1e5e9';
                btn.style.background = 'white';
            });
            
            // Evidenzia pulsante selezionato
            this.style.borderColor = '#FF9800';
            this.style.background = '#fff3e0';
            
            // Applica valori
            const multiplier = this.dataset.multiplier;
            const minNights = this.dataset.minNights;
            const name = this.dataset.name;
            
            if (multiplier) {
                const multiplierInput = document.querySelector('#id_price_multiplier');
                if (multiplierInput) {
                    multiplierInput.value = multiplier;
                    multiplierInput.dispatchEvent(new Event('input'));
                }
            }
            
            if (minNights) {
                const minNightsInput = document.querySelector('#id_min_nights');
                if (minNightsInput) {
                    minNightsInput.value = minNights;
                }
            }
            
            if (name) {
                const nameInput = document.querySelector('#id_name');
                if (nameInput) {
                    nameInput.value = name;
                }
            }
        });
    });
}

function initInteractiveCalendar() {
    const calendarContainer = document.querySelector('.calendar-widget');
    if (!calendarContainer) return;
    
    const calendarGrid = calendarContainer.querySelector('.calendar-grid');
    if (!calendarGrid) return;
    
    // Crea calendario se non esiste
    if (!calendarGrid.children.length) {
        createCalendar(calendarGrid);
    }
    
    // Aggiungi event listeners ai giorni
    const days = calendarGrid.querySelectorAll('.calendar-day');
    days.forEach(day => {
        day.addEventListener('click', function() {
            toggleDaySelection(this);
        });
    });
}

function createCalendar(container) {
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    // Header del calendario
    const monthNames = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                       'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'];
    
    // Crea giorni della settimana
    const dayNames = ['Dom', 'Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab'];
    dayNames.forEach(dayName => {
        const dayHeader = document.createElement('div');
        dayHeader.textContent = dayName;
        dayHeader.style.cssText = 'text-align: center; font-weight: 600; padding: 10px; background: #f8f9fa;';
        container.appendChild(dayHeader);
    });
    
    // Crea giorni del mese
    const firstDay = new Date(currentYear, currentMonth, 1);
    const lastDay = new Date(currentYear, currentMonth + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();
    
    // Giorni vuoti all'inizio
    for (let i = 0; i < startingDay; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day';
        emptyDay.style.visibility = 'hidden';
        container.appendChild(emptyDay);
    }
    
    // Giorni del mese
    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.textContent = day;
        dayElement.dataset.day = day;
        
        // Aggiungi classi per weekend
        const dayOfWeek = (startingDay + day - 1) % 7;
        if (dayOfWeek === 0 || dayOfWeek === 6) { // Domenica o Sabato
            dayElement.classList.add('weekend');
        }
        
        container.appendChild(dayElement);
    }
}

function toggleDaySelection(dayElement) {
    if (dayElement.classList.contains('blocked')) return;
    
    dayElement.classList.toggle('selected');
    
    // Aggiorna campi nascosti con giorni selezionati
    updateSelectedDays();
}

function updateSelectedDays() {
    const selectedDays = document.querySelectorAll('.calendar-day.selected');
    const selectedDates = Array.from(selectedDays).map(day => day.dataset.day);
    
    // Aggiorna campo nascosto se esiste
    const hiddenField = document.querySelector('#selected_days');
    if (hiddenField) {
        hiddenField.value = selectedDates.join(',');
    }
}

function initFormValidation() {
    const form = document.querySelector('form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        const errors = validateForm();
        if (errors.length > 0) {
            e.preventDefault();
            showValidationErrors(errors);
        }
    });
}

function validateForm() {
    const errors = [];
    
    // Valida date
    const startDate = document.querySelector('#id_start_date');
    const endDate = document.querySelector('#id_end_date');
    
    if (startDate && endDate) {
        const start = new Date(startDate.value);
        const end = new Date(endDate.value);
        
        if (start >= end) {
            errors.push('La data di fine deve essere successiva alla data di inizio');
        }
    }
    
    // Valida prezzi
    const basePrice = document.querySelector('#id_base_price');
    if (basePrice && parseFloat(basePrice.value) <= 0) {
        errors.push('Il prezzo base deve essere maggiore di zero');
    }
    
    // Valida moltiplicatore
    const multiplier = document.querySelector('#id_price_multiplier');
    if (multiplier && parseFloat(multiplier.value) <= 0) {
        errors.push('Il moltiplicatore deve essere maggiore di zero');
    }
    
    return errors;
}

function showValidationErrors(errors) {
    // Rimuovi errori precedenti
    const existingErrors = document.querySelectorAll('.validation-error');
    existingErrors.forEach(error => error.remove());
    
    // Crea container errori
    const errorContainer = document.createElement('div');
    errorContainer.className = 'validation-error';
    errorContainer.style.cssText = `
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
        border-radius: 6px;
        padding: 15px;
        margin-bottom: 20px;
    `;
    
    const errorTitle = document.createElement('h4');
    errorTitle.textContent = '⚠️ Errori di Validazione';
    errorTitle.style.margin = '0 0 10px 0';
    
    const errorList = document.createElement('ul');
    errorList.style.margin = '0';
    errorList.style.paddingLeft = '20px';
    
    errors.forEach(error => {
        const li = document.createElement('li');
        li.textContent = error;
        errorList.appendChild(li);
    });
    
    errorContainer.appendChild(errorTitle);
    errorContainer.appendChild(errorList);
    
    // Inserisci all'inizio del form
    const form = document.querySelector('form');
    form.insertBefore(errorContainer, form.firstChild);
    
    // Scrolla verso l'errore
    errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Funzioni utility
function formatPrice(price) {
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR'
    }).format(price);
}

function calculatePercentageChange(oldPrice, newPrice) {
    return ((newPrice - oldPrice) / oldPrice) * 100;
}

// Animazioni
function animateElement(element, animation) {
    element.style.animation = animation;
    element.addEventListener('animationend', function() {
        element.style.animation = '';
    });
}

// Esporta funzioni per uso globale
window.CalendarRulesAdmin = {
    formatPrice,
    calculatePercentageChange,
    animateElement
};
