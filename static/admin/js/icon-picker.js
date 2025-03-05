// static/admin/js/icon-picker.js

// Funzione di utilità per il logging
function debug(message, data = null) {
    console.log(`[IconPicker] ${message}`, data || '');
}

document.addEventListener('DOMContentLoaded', function() {
    debug('Initializing IconPicker');
    
    // Trova tutti i container del icon picker
    const containers = document.querySelectorAll('.icon-picker-container');
    debug(`Found ${containers.length} icon picker containers`);
    
    containers.forEach((container, index) => {
        debug(`Setting up container ${index + 1}`);
        
        // Trova gli elementi all'interno di questo container specifico
        const input = container.querySelector('input[type="hidden"]');
        const tabs = container.querySelectorAll('.icon-picker-tab');
        const categories = container.querySelectorAll('.icon-picker-category');
        const icons = container.querySelectorAll('.icon-item');
        
        debug(`Container ${index + 1} elements:`, {
            input: input ? 'found' : 'missing',
            tabs: tabs.length,
            categories: categories.length,
            icons: icons.length
        });
        
        // Gestione dei tab
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                debug('Tab clicked:', tab.dataset.category);
                
                // Rimuovi active da tutti i tab e categorie
                tabs.forEach(t => t.classList.remove('active'));
                categories.forEach(c => c.classList.remove('active'));
                
                // Attiva il tab cliccato e la categoria corrispondente
                tab.classList.add('active');
                const categoryId = tab.dataset.category;
                const activeCategory = container.querySelector(`.icon-picker-category[data-category="${categoryId}"]`);
                if (activeCategory) {
                    activeCategory.classList.add('active');
                    debug('Activated category:', categoryId);
                } else {
                    debug('Category not found:', categoryId);
                }
            });
        });
        
        // Gestione della selezione icone
        icons.forEach(iconElement => {
            iconElement.addEventListener('click', () => {
                const iconId = iconElement.dataset.iconId;
                debug('Icon clicked:', {
                    id: iconId,
                    name: iconElement.dataset.iconName
                });
                
                // Rimuovi selected da tutte le icone
                icons.forEach(i => i.classList.remove('selected'));
                
                // Seleziona l'icona cliccata
                iconElement.classList.add('selected');
                
                // Aggiorna il valore dell'input nascosto
                if (input) {
                    input.value = iconId;
                    debug('Input value updated:', iconId);
                    
                    // Trigger change event
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    debug('Change event dispatched');
                } else {
                    debug('ERROR: Input element not found');
                }
            });
            
            // Aggiungi tooltip se c'è un nome
            if (iconElement.dataset.iconName) {
                iconElement.title = iconElement.dataset.iconName;
            }
        });
        
        // Verifica iniziale
        if (input && input.value) {
            const selectedIcon = container.querySelector(`[data-icon-id="${input.value}"]`);
            if (selectedIcon) {
                selectedIcon.classList.add('selected');
                debug('Initially selected icon:', input.value);
            }
        }
    });
    
    debug('IconPicker initialization complete');
});