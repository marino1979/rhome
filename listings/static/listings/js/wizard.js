// Gestione delle stanze e dei letti
document.addEventListener('DOMContentLoaded', function() {
    const roomsContainer = document.getElementById('rooms-container');
    const addRoomButton = document.getElementById('add-room');
    const roomTemplate = document.getElementById('room-template');
    const bedTemplate = document.getElementById('bed-template');
    let roomTypes = [];
    let bedTypes = [];

    // Carica i tipi di stanze e letti
    async function loadTypes() {
        try {
            const [roomTypesResponse, bedTypesResponse] = await Promise.all([
                fetch('/appartamenti/room-types/'),
                fetch('/appartamenti/bed-types/')
            ]);
            
            roomTypes = await roomTypesResponse.json();
            bedTypes = await bedTypesResponse.json();
        } catch (error) {
            console.error('Errore nel caricamento dei tipi:', error);
        }
    }

    // Aggiungi una nuova stanza
    function addRoom() {
        const roomElement = roomTemplate.content.cloneNode(true);
        const roomSelect = roomElement.querySelector('select[name="room_type"]');
        
        // Popola il select dei tipi di stanza
        roomTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type.id;
            option.textContent = type.name;
            roomSelect.appendChild(option);
        });

        // Aggiungi event listener per il pulsante "Aggiungi Letto"
        const addBedButton = roomElement.querySelector('.add-bed');
        addBedButton.addEventListener('click', () => addBed(roomElement.querySelector('.beds-container')));

        // Aggiungi event listener per il pulsante "Rimuovi Stanza"
        const removeRoomButton = roomElement.querySelector('.remove-room');
        removeRoomButton.addEventListener('click', () => roomElement.querySelector('.room-item').remove());

        roomsContainer.appendChild(roomElement);
    }

    // Aggiungi un nuovo letto
    function addBed(bedsContainer) {
        const bedElement = bedTemplate.content.cloneNode(true);
        const bedSelect = bedElement.querySelector('select[name="bed_type"]');
        
        // Popola il select dei tipi di letto
        bedTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type.id;
            option.textContent = `${type.name} (${type.capacity} posti)`;
            bedSelect.appendChild(option);
        });

        // Aggiungi event listener per il pulsante "Rimuovi Letto"
        const removeBedButton = bedElement.querySelector('.remove-bed');
        removeBedButton.addEventListener('click', () => bedElement.querySelector('.bed-item').remove());

        bedsContainer.appendChild(bedElement);
    }

    // Gestione delle foto
    const photosInput = document.getElementById('photos');
    const photosPreview = document.getElementById('photos-preview');

    photosInput.addEventListener('change', function(e) {
        photosPreview.innerHTML = '';
        Array.from(e.target.files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.createElement('div');
                    preview.className = 'photo-preview';
                    preview.innerHTML = `
                        <img src="${e.target.result}" alt="Preview">
                        <button type="button" class="remove-photo">&times;</button>
                    `;
                    
                    preview.querySelector('.remove-photo').addEventListener('click', () => {
                        preview.remove();
                    });
                    
                    photosPreview.appendChild(preview);
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Carica i tipi all'inizializzazione
    loadTypes();

    // Aggiungi event listener per il pulsante "Aggiungi Stanza"
    addRoomButton.addEventListener('click', addRoom);
});

// Gestione dei servizi (amenities)
document.addEventListener('DOMContentLoaded', function() {
    const amenitiesContainer = document.getElementById('amenities-container');

    async function loadAmenities() {
        try {
            const response = await fetch('/appartamenti/amenity-categories/');
            const categories = await response.json();
            
            categories.forEach(category => {
                const categorySection = document.createElement('div');
                categorySection.className = 'amenity-category';
                categorySection.innerHTML = `
                    <h3>${category.name}</h3>
                    <div class="amenities-grid">
                        ${category.amenities.map(amenity => `
                            <label class="amenity-checkbox">
                                <input type="checkbox" name="amenities[]" value="${amenity.id}">
                                <span class="amenity-icon">${amenity.icon}</span>
                                <span class="amenity-name">${amenity.name}</span>
                            </label>
                        `).join('')}
                    </div>
                `;
                amenitiesContainer.appendChild(categorySection);
            });
        } catch (error) {
            console.error('Errore nel caricamento dei servizi:', error);
        }
    }

    loadAmenities();
}); 