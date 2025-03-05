// static/admin/js/icon-picker.js
document.addEventListener('DOMContentLoaded', function() {
    const ICON_LIBRARIES = {
        fontawesome: {
            name: 'Font Awesome',
            prefix: 'fa-',
            cssClass: 'fas',
            icons: [
                // Stanze e Spazi
                'house', 'bed', 'couch', 'door-open', 'stairs', 'elevator',
                'warehouse', 'square-parking', 'garage', 'door-closed', 'chair',
                'table', 'desktop', 'window', 'building', 'shop', 'store',
                
                // Elettrodomestici e Tech
                'tv', 'laptop', 'computer', 'mobile', 'tablet', 'print',
                'plug', 'lightbulb', 'battery-full', 'power-off', 'wifi',
                'router', 'microwave', 'blender', 'toaster',
                
                // Bagno e Pulizia
                'bath', 'shower', 'sink', 'toilet', 'toilet-paper',
                'pump-soap', 'spray-can', 'broom', 'bucket', 'trash',
                'recycle', 'soap', 'hands-wash',
                
                // Cucina e Food
                'kitchen-set', 'utensils', 'plate-wheat', 'mug-hot',
                'wine-glass', 'martini-glass', 'beer-mug', 'bottle-water',
                'egg', 'burger', 'pizza-slice', 'apple-whole', 'cookie',
                'ice-cream', 'carrot', 'bread-slice', 'cheese',
                
                // Comfort e Clima
                'temperature-high', 'temperature-low', 'temperature-half',
                'fan', 'wind', 'snowflake', 'sun', 'cloud', 'fire',
                'umbrella', 'moon', 'stars',
                
                // Sicurezza
                'key', 'lock', 'unlock', 'shield', 'shield-check',
                'camera', 'video', 'bell', 'phone', 'phone-volume',
                'fingerprint', 'eye', 'user-shield',
                
                // Intrattenimento
                'gamepad', 'headphones', 'music', 'book', 'books',
                'radio', 'film', 'dice', 'puzzle-piece', 'palette',
                'guitar', 'drum', 'piano',
                
                // Sport e Attività
                'person-swimming', 'person-running', 'person-biking',
                'dumbbell', 'table-tennis', 'football', 'basketball',
                'volleyball', 'baseball', 'golf-ball',
                
                // Esterni
                'tree', 'umbrella-beach', 'mountain-sun', 'leaf',
                'flower', 'campground', 'fire-flame', 'water', 'cloud-sun',
                'rainbow', 'seedling',
                
                // Servizi
                'suitcase', 'clock', 'calendar', 'map', 'map-location-dot',
                'compass', 'info', 'question', 'phone', 'envelope',
                'message', 'comments',
    
                // Animali e Bambini
                'baby', 'baby-carriage', 'child', 'children',
                'paw', 'dog', 'cat', 'fish', 'bone', 'feather',
                
                // Divieti e Avvisi
                'smoking', 'smoking-ban', 'ban', 'circle-exclamation',
                'triangle-exclamation', 'circle-info', 'bell-slash',
                'volume-xmark', 'wheelchair', 'circle-radiation',
                
                // Trasporti
                'car', 'bicycle', 'motorcycle', 'bus', 'train', 'taxi',
                'truck', 'plane', 'ship', 'helicopter'
            ]
        },
        bootstrap: {
            name: 'Bootstrap Icons',
            prefix: 'bi-',
            cssClass: 'bi',
            icons: [
                // Casa e Ambienti
                'house', 'door', 'window', 'building', 'shop', 'box',
                'boxes', 'basket', 'cart', 'bag', 'archive',
                
                // Elettrodomestici e Tech
                'tv', 'laptop', 'pc-display', 'phone', 'printer',
                'wifi', 'modem', 'router', 'plug', 'outlet', 'battery',
                'lamp', 'lightbulb',
                
                // Bagno e Pulizia
                'water', 'droplet', 'moisture', 'wash', 'trash',
                'bucket', 'brush', 'spray', 'cup-hot-fill',
                
                // Comfort e Servizi
                'thermometer', 'thermometer-high', 'thermometer-low',
                'snow', 'sun', 'cloud', 'wind', 'fan', 'stars',
                'moon', 'umbrella',
                
                // Sicurezza
                'shield', 'shield-check', 'shield-lock', 'lock', 'unlock',
                'key', 'door-closed', 'door-open', 'camera', 'camera-video',
                
                // Utility
                'gear', 'tools', 'wrench', 'screwdriver', 'hammer',
                'calendar', 'clock', 'alarm', 'bell', 'envelope'
            ]
        },
        material: {
            name: 'Material Icons',
            prefix: 'material-',
            cssClass: 'material-symbols-outlined',
            icons: [
                // Casa e Stanze
                'home', 'apartment', 'house', 'bedroom_parent', 'bedroom_baby',
                'living', 'chair', 'table_restaurant', 'kitchen', 'bathroom',
                'garage', 'elevator',
                
                // Elettrodomestici
                'tv', 'computer', 'smartphone', 'print', 'router', 'wifi',
                'local_laundry_service', 'countertops', 'microwave',
                'outlet', 'air_purifier',
                
                // Comfort e Clima
                'ac_unit', 'thermostat', 'nest_farsight_weather', 'sunny',
                'cloud', 'thunderstorm', 'fan', 'mode_fan', 'air',
                
                // Servizi e Sicurezza
                'key', 'lock', 'security', 'shield', 'door_front',
                'garage_door', 'cctv', 'doorbell', 'phone', 'mail',
                
                // Sport e Attività
                'pool', 'sports_tennis', 'sports_basketball',
                'sports_football', 'hiking', 'surfing', 'golf_course',
                
                // Utility e Info
                'info', 'help', 'warning', 'error', 'calendar_month',
                'schedule', 'alarm', 'notifications', 'settings', 'build'
            ]
        },
        remix: {
            name: 'Remix Icon',
            prefix: 'ri-',
            cssClass: 'ri',
            icons: [
                // Casa e Ambienti
                'home-line', 'door-open-line', 'window-line', 'building-line',
                'store-line', 'box-line', 'archive-line', 'chest-line',
                
                // Tech e Comfort
                'tv-line', 'computer-line', 'smartphone-line', 'wifi-line',
                'router-line', 'plug-line', 'battery-line', 'flashlight-line',
                
                // Servizi e Sicurezza
                'lock-line', 'unlock-line', 'key-line', 'shield-line',
                'door-lock-line', 'camera-line', 'video-line', 'bell-line',
                
                // Utility e Info
                'information-line', 'question-line', 'alert-line',
                'calendar-line', 'time-line', 'map-pin-line', 'settings-line'
            ]
        },
        boxicons: {
            name: 'Boxicons',
            prefix: 'bx-',
            cssClass: 'bx',
            icons: [
                // Casa e Ambienti
                'home', 'building-house', 'door', 'window', 'cabinet',
                'box', 'archive', 'store', 'shopping-bag',
                
                // Tech e Comfort
                'tv', 'laptop', 'mobile', 'printer', 'wifi', 'router',
                'plug', 'bulb', 'battery', 'broadcast',
                
                // Servizi e Sicurezza
                'lock', 'lock-open', 'key', 'shield', 'camera', 'video',
                'bell', 'phone', 'envelope', 'message',
                
                // Utility e Info
                'info-circle', 'help-circle', 'error-circle',
                'calendar', 'time', 'map', 'cog', 'wrench'
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

        // Contenitore per ogni libreria
        Object.entries(ICON_LIBRARIES).forEach(([key, lib], index) => {
            const library = document.createElement('div');
            library.className = `icon-library ${index === 0 ? 'active' : ''}`;
            library.dataset.library = key;

            const grid = document.createElement('div');
            grid.className = 'icon-grid';

            lib.icons.forEach(iconName => {
                const iconDiv = document.createElement('div');
                iconDiv.className = 'icon-item';
                const fullIconName = lib.prefix + iconName;
                iconDiv.dataset.name = fullIconName;

                if (key === 'material') {
                    iconDiv.innerHTML = `<span class="${lib.cssClass}">${iconName}</span>`;
                } else {
                    iconDiv.innerHTML = `<i class="${lib.cssClass} ${fullIconName}"></i>`;
                }

                iconDiv.title = iconName; // Tooltip con il nome dell'icona

                iconDiv.addEventListener('click', () => {
                    input.value = fullIconName;
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
            const activeLibrary = document.querySelector('.icon-library.active');
            if (activeLibrary) {
                activeLibrary.querySelectorAll('.icon-item').forEach(item => {
                    const iconName = item.dataset.name.toLowerCase();
                    item.style.display = iconName.includes(searchTerm) ? '' : 'none';
                });
            }
        });

        input.parentNode.insertBefore(container, input.nextSibling);

        // Se c'è già un valore, seleziona l'icona corrispondente
        if (input.value) {
            const selectedIcon = document.querySelector(`[data-name="${input.value}"]`);
            if (selectedIcon) {
                selectedIcon.classList.add('selected');
                // Attiva la tab corretta
                const libraryKey = Object.keys(ICON_LIBRARIES).find(key => 
                    input.value.startsWith(ICON_LIBRARIES[key].prefix)
                );
                if (libraryKey) {
                    const tab = document.querySelector(`[data-library="${libraryKey}"]`);
                    if (tab) tab.click();
                }
            }
        }
    }

    // Inizializza tutti i picker
    document.querySelectorAll('.icon-picker').forEach(createIconPicker);
});