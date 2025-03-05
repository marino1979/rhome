// static/admin/js/icon-picker.js
document.addEventListener('DOMContentLoaded', function() {
    const ICON_LIBRARIES = {
        fontawesome: {
            name: 'Font Awesome',
            prefix: 'fa-',
            icons: [
                'wifi', 'tv', 'bed', 'shower', 'bath', 'key', 'door-open',
                'kitchen-set', 'temperature-high', 'fan', 'soap', 'shirt',
                'box', 'sink', 'fire', 'utensils', 'mug-hot', 'wind'
                // Aggiungi altre icone Font Awesome
            ]
        },
        bootstrap: {
            name: 'Bootstrap Icons',
            prefix: 'bi-',
            icons: [
                'wifi', 'tv', 'house', 'door-open', 'key', 'thermometer-high',
                'fan', 'cup-hot', 'box', 'gear', 'tools'
                // Aggiungi altre icone Bootstrap
            ]
        },
        material: {
            name: 'Material Icons',
            prefix: 'material-',
            icons: [
                'wifi', 'tv', 'bed', 'shower', 'bathroom', 'key', 'door_front',
                'kitchen', 'thermostat', 'fan', 'local_laundry_service'
                // Aggiungi altre icone Material
            ]
        }
    };

    function createIconPicker(input) {
        const container = document.createElement('div');
        container.className = 'icon-picker-container';

        // Tabs per le librerie
        const tabs = document.createElement('div');
        tabs.className = 'icon-library-tabs';
        
        Object.entries(ICON_LIBRARIES).forEach(([key, lib], index) => {
            const tab = document.createElement('div');
            tab.className = `icon-library-tab ${index === 0 ? 'active' : ''}`;
            tab.textContent = lib.name;
            tab.dataset.library = key;
            tabs.appendChild(tab);
        });
        
        container.appendChild(tabs);

        // Campo di ricerca
        const search = document.createElement('input');
        search.type = 'text';
        search.placeholder = 'Cerca icona...';
        search.className = 'icon-search';
        container.appendChild(search);

        // Contenitore per le griglie di icone
        Object.entries(ICON_LIBRARIES).forEach(([key, lib], index) => {
            const library = document.createElement('div');
            library.className = `icon-library ${index === 0 ? 'active' : ''}`;
            library.dataset.library = key;

            const grid = document.createElement('div');
            grid.className = 'icon-grid';

            lib.icons.forEach(iconName => {
                const iconDiv = document.createElement('div');
                iconDiv.className = 'icon-item';
                iconDiv.dataset.name = lib.prefix + iconName;

                if (key === 'material') {
                    iconDiv.innerHTML = `<span class="material-symbols-outlined">${iconName}</span>`;
                } else {
                    const prefix = key === 'fontawesome' ? 'fas' : 'bi';
                    iconDiv.innerHTML = `<i class="${prefix} ${lib.prefix}${iconName}"></i>`;
                }

                iconDiv.addEventListener('click', () => {
                    input.value = lib.prefix + iconName;
                    document.querySelectorAll('.icon-item').forEach(i => i.classList.remove('selected'));
                    iconDiv.classList.add('selected');
                    
                    // Aggiorna preview
                    const previewContainer = document.querySelector('.field-icon_preview');
                    if (previewContainer) {
                        previewContainer.querySelector('.readonly').click();
                    }
                });

                grid.appendChild(iconDiv);
            });

            library.appendChild(grid);
            container.appendChild(library);
        });

        // Gestione tab click
        tabs.addEventListener('click', (e) => {
            if (e.target.classList.contains('icon-library-tab')) {
                const library = e.target.dataset.library;
                document.querySelectorAll('.icon-library-tab').forEach(tab => 
                    tab.classList.toggle('active', tab.dataset.library === library));
                document.querySelectorAll('.icon-library').forEach(lib => 
                    lib.classList.toggle('active', lib.dataset.library === library));
            }
        });

        // Gestione ricerca
        search.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            document.querySelectorAll('.icon-item').forEach(item => {
                const iconName = item.dataset.name.toLowerCase();
                item.style.display = iconName.includes(searchTerm) ? '' : 'none';
            });
        });

        input.parentNode.insertBefore(container, input.nextSibling);
    }

    // Inizializza tutti i picker
    document.querySelectorAll('.icon-picker').forEach(createIconPicker);
});