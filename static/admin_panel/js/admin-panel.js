// Admin Panel JavaScript
const API_BASE_URL = '/admin-panel/api/';

// State
let currentSection = 'listings';
let listings = [];
let currentListing = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    loadListings();
    loadAmenities();
    setupForms();
});

// Navigation
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item[data-section]');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.getAttribute('data-section');
            switchSection(section);
        });
    });
}

function switchSection(section) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    document.querySelector(`[data-section="${section}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.content-section').forEach(sec => sec.classList.remove('active'));
    document.getElementById(`section-${section}`).classList.add('active');
    
    // Update title
    const titles = {
        listings: 'Gestione Annunci',
        prices: 'Gestione Prezzi',
        bookings: 'Gestione Prenotazioni',
        calendars: 'Calendari ICAL'
    };
    document.getElementById('page-title').textContent = titles[section] || 'Admin Panel';
    
    currentSection = section;
    
    // Load section data
    if (section === 'listings') {
        loadListings();
    } else if (section === 'prices') {
        loadListingsForSelect('price-listing-select');
    } else if (section === 'bookings') {
        loadBookings();
        loadListingsForSelect('booking-listing-select');
    } else if (section === 'calendars') {
        loadCalendars();
        loadListingsForSelect('calendar-listing');
    }
}

// API Functions
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        credentials: 'include'
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(API_BASE_URL + endpoint, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || result.error || 'Errore nella richiesta');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        showMessage(error.message, 'error');
        throw error;
    }
}

function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Listings
async function loadListings() {
    showLoading(true);
    try {
        const data = await apiRequest('listings/');
        listings = data.results || data;
        renderListings();
    } catch (error) {
        console.error('Error loading listings:', error);
    } finally {
        showLoading(false);
    }
}

function renderListings() {
    const container = document.getElementById('listings-list');
    if (!listings || listings.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Nessun annuncio trovato</p></div>';
        return;
    }
    
    container.innerHTML = listings.map(listing => `
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="card-title">${listing.title}</div>
                    <span class="card-status ${listing.status}">${getStatusLabel(listing.status)}</span>
                </div>
            </div>
            ${listing.main_image_url ? `<img src="${listing.main_image_url}" alt="${listing.title}" class="card-image">` : ''}
            <div class="card-info">
                <div class="card-info-item">
                    <span>Città:</span>
                    <span>${listing.city}</span>
                </div>
                <div class="card-info-item">
                    <span>Prezzo Base:</span>
                    <span>€${parseFloat(listing.base_price).toFixed(2)}</span>
                </div>
                <div class="card-info-item">
                    <span>Ospiti Max:</span>
                    <span>${listing.max_guests}</span>
                </div>
            </div>
            <div class="card-actions">
                <button class="btn btn-primary" onclick="editListing(${listing.id})">Modifica</button>
                <button class="btn btn-secondary" onclick="manageListingRooms(${listing.id})">Stanze</button>
                <button class="btn btn-secondary" onclick="manageListingPrices(${listing.id})">Prezzi</button>
            </div>
        </div>
    `).join('');
}

function getStatusLabel(status) {
    const labels = {
        draft: 'Bozza',
        active: 'Attivo',
        inactive: 'Non attivo'
    };
    return labels[status] || status;
}

// Listing Modal
function openListingModal(listingId = null) {
    const modal = document.getElementById('modal-listing');
    const form = document.getElementById('form-listing');
    
    if (listingId) {
        const listing = listings.find(l => l.id === listingId);
        if (listing) {
            fillListingForm(listing);
            document.getElementById('modal-listing-title').textContent = 'Modifica Annuncio';
        }
    } else {
        form.reset();
        document.getElementById('listing-id').value = '';
        document.getElementById('modal-listing-title').textContent = 'Nuovo Annuncio';
    }
    
    modal.classList.add('active');
}

function closeListingModal() {
    document.getElementById('modal-listing').classList.remove('active');
}

function fillListingForm(listing) {
    document.getElementById('listing-id').value = listing.id;
    document.getElementById('listing-title').value = listing.title || '';
    document.getElementById('listing-description').value = listing.description || '';
    document.getElementById('listing-city').value = listing.city || '';
    document.getElementById('listing-zone').value = listing.zone || '';
    document.getElementById('listing-address').value = listing.address || '';
    document.getElementById('listing-base-price').value = listing.base_price || '';
    document.getElementById('listing-cleaning-fee').value = listing.cleaning_fee || '0';
    document.getElementById('listing-max-guests').value = listing.max_guests || '';
    document.getElementById('listing-included-guests').value = listing.included_guests || '1';
    document.getElementById('listing-bedrooms').value = listing.bedrooms || '1';
    document.getElementById('listing-bathrooms').value = listing.bathrooms || '1';
    document.getElementById('listing-status').value = listing.status || 'draft';
    
    // Load images
    if (listing.images) {
        renderListingImages(listing.images);
    }
}

function renderListingImages(images) {
    const container = document.getElementById('listing-images-preview');
    // Sort images by order
    const sortedImages = [...images].sort((a, b) => (a.order || 0) - (b.order || 0));
    
    container.innerHTML = sortedImages.map((img, index) => `
        <div class="image-preview-item" data-image-id="${img.id}">
            <img src="${img.url}" alt="${img.alt_text || ''}">
            ${img.is_main ? '<span class="main-badge">Principale</span>' : ''}
            <button type="button" class="remove-image" onclick="deleteListingImage(${img.id})">×</button>
            <div class="image-actions">
                <button type="button" class="btn-image-action" onclick="setMainImage(${img.id})" title="Imposta come principale">⭐</button>
                ${index > 0 ? `<button type="button" class="btn-image-action" onclick="moveImageOrder(${img.id}, -1)" title="Sposta su">↑</button>` : ''}
                ${index < sortedImages.length - 1 ? `<button type="button" class="btn-image-action" onclick="moveImageOrder(${img.id}, 1)" title="Sposta giù">↓</button>` : ''}
            </div>
        </div>
    `).join('');
}

async function setMainImage(imageId) {
    const listingId = document.getElementById('listing-id').value;
    if (!listingId) return;
    
    try {
        await apiRequest(`listings/${listingId}/images/${imageId}/set-main/`, 'PATCH');
        showMessage('Immagine principale aggiornata', 'success');
        loadListings();
        // Reload current listing if editing
        if (listingId) {
            const listing = listings.find(l => l.id === parseInt(listingId));
            if (listing) {
                fillListingForm(listing);
            }
        }
    } catch (error) {
        console.error('Error setting main image:', error);
    }
}

async function moveImageOrder(imageId, direction) {
    // This would require an API endpoint to update image order
    // For now, we'll just show a message
    showMessage('Funzionalità riordino immagini in sviluppo', 'info');
}

async function deleteListingImage(imageId) {
    if (!confirm('Eliminare questa immagine?')) return;
    
    try {
        const listingId = document.getElementById('listing-id').value;
        await apiRequest(`listings/${listingId}/images/${imageId}/`, 'DELETE');
        showMessage('Immagine eliminata', 'success');
        loadListings();
    } catch (error) {
        console.error('Error deleting image:', error);
    }
}

async function uploadListingImages() {
    const input = document.getElementById('listing-image-upload');
    const files = input.files;
    const listingId = document.getElementById('listing-id').value;
    
    if (!listingId) {
        showMessage('Salva prima l\'annuncio', 'error');
        return;
    }
    
    if (files.length === 0) {
        showMessage('Seleziona almeno un\'immagine', 'error');
        return;
    }
    
    showLoading(true);
    try {
        for (let file of files) {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_BASE_URL}listings/${listingId}/upload-image/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                credentials: 'include',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Errore nel caricamento');
            }
        }
        
        showMessage('Immagini caricate con successo', 'success');
        input.value = '';
        loadListings();
    } catch (error) {
        showMessage('Errore nel caricamento delle immagini', 'error');
    } finally {
        showLoading(false);
    }
}

function editListing(id) {
    openListingModal(id);
}

async function manageListingRooms(id) {
    const modal = document.getElementById('modal-rooms-list');
    document.getElementById('room-listing-id').value = id;
    document.getElementById('modal-rooms-list-title').textContent = `Stanze - ${getListingName(id)}`;
    
    // Load room types
    await loadRoomTypes();
    
    // Load rooms
    await loadRooms(id);
    
    modal.classList.add('active');
}

function closeRoomsListModal() {
    document.getElementById('modal-rooms-list').classList.remove('active');
}

async function loadRoomTypes() {
    try {
        const data = await apiRequest('room-types/');
        const types = data.results || data;
        const select = document.getElementById('room-type');
        
        select.innerHTML = '<option value="">Seleziona tipo...</option>';
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type.id;
            option.textContent = type.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading room types:', error);
    }
}

async function loadRooms(listingId) {
    showLoading(true);
    try {
        const data = await apiRequest(`rooms/?listing_id=${listingId}`);
        const rooms = data.results || data;
        renderRooms(rooms, listingId);
    } catch (error) {
        console.error('Error loading rooms:', error);
    } finally {
        showLoading(false);
    }
}

function renderRooms(rooms, listingId) {
    const container = document.getElementById('rooms-list-content');
    
    if (!rooms || rooms.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Nessuna stanza configurata</p></div>';
        return;
    }
    
    container.innerHTML = rooms.map(room => `
        <div class="card" style="margin-bottom: 15px;">
            <div class="card-header">
                <div>
                    <div class="card-title">${room.name}</div>
                    <span style="font-size: 14px; color: #666;">${room.room_type_name}</span>
                </div>
            </div>
            ${room.images && room.images.length > 0 ? `
                <div class="images-preview" style="margin: 15px 0;">
                    ${room.images.map(img => `
                        <div class="image-preview-item">
                            <img src="${img.url}" alt="${img.alt_text || ''}">
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            <div class="card-info">
                ${room.square_meters ? `
                <div class="card-info-item">
                    <span>Metri Quadri:</span>
                    <span>${room.square_meters} m²</span>
                </div>
                ` : ''}
                ${room.description ? `
                <div class="card-info-item" style="margin-top: 10px;">
                    <span>Descrizione:</span>
                    <span>${room.description.substring(0, 100)}${room.description.length > 100 ? '...' : ''}</span>
                </div>
                ` : ''}
            </div>
            <div class="card-actions">
                <button class="btn btn-primary" onclick="editRoom(${room.id}, ${listingId})">Modifica</button>
                <button class="btn btn-danger" onclick="deleteRoom(${room.id}, ${listingId})">Elimina</button>
            </div>
        </div>
    `).join('');
}

function getListingName(id) {
    const listing = listings.find(l => l.id === parseInt(id));
    return listing ? listing.title : 'Annuncio';
}

function openRoomModal(listingId, roomId = null) {
    const modal = document.getElementById('modal-room');
    const form = document.getElementById('form-room');
    
    document.getElementById('room-listing-id').value = listingId;
    
    if (roomId) {
        loadRoomData(roomId);
        document.getElementById('modal-room-title').textContent = 'Modifica Stanza';
    } else {
        form.reset();
        document.getElementById('room-id').value = '';
        document.getElementById('modal-room-title').textContent = 'Nuova Stanza';
    }
    
    modal.classList.add('active');
}

function closeRoomModal() {
    document.getElementById('modal-room').classList.remove('active');
}

async function loadRoomData(id) {
    try {
        const room = await apiRequest(`rooms/${id}/`);
        document.getElementById('room-id').value = room.id;
        document.getElementById('room-listing-id').value = room.listing;
        document.getElementById('room-type').value = room.room_type;
        document.getElementById('room-name').value = room.name;
        document.getElementById('room-square-meters').value = room.square_meters || '';
        document.getElementById('room-order').value = room.order || 0;
        document.getElementById('room-description').value = room.description || '';
        
        if (room.images) {
            renderRoomImages(room.images);
        }
    } catch (error) {
        console.error('Error loading room:', error);
    }
}

function renderRoomImages(images) {
    const container = document.getElementById('room-images-preview');
    container.innerHTML = images.map(img => `
        <div class="image-preview-item">
            <img src="${img.url}" alt="${img.alt_text || ''}">
            <button type="button" class="remove-image" onclick="deleteRoomImage(${img.id})">×</button>
        </div>
    `).join('');
}

async function deleteRoomImage(imageId) {
    if (!confirm('Eliminare questa immagine?')) return;
    
    try {
        const roomId = document.getElementById('room-id').value;
        const listingId = document.getElementById('room-listing-id').value;
        await apiRequest(`rooms/${roomId}/images/${imageId}/`, 'DELETE');
        showMessage('Immagine eliminata', 'success');
        await loadRoomData(roomId);
    } catch (error) {
        console.error('Error deleting image:', error);
    }
}

async function uploadRoomImages() {
    const input = document.getElementById('room-image-upload');
    const files = input.files;
    const roomId = document.getElementById('room-id').value;
    
    if (!roomId) {
        showMessage('Salva prima la stanza', 'error');
        return;
    }
    
    if (files.length === 0) {
        showMessage('Seleziona almeno un\'immagine', 'error');
        return;
    }
    
    showLoading(true);
    try {
        for (let file of files) {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_BASE_URL}rooms/${roomId}/upload-image/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                credentials: 'include',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Errore nel caricamento');
            }
        }
        
        showMessage('Immagini caricate con successo', 'success');
        input.value = '';
        await loadRoomData(roomId);
    } catch (error) {
        showMessage('Errore nel caricamento delle immagini', 'error');
    } finally {
        showLoading(false);
    }
}

async function saveRoom() {
    const roomId = document.getElementById('room-id').value;
    const listingId = document.getElementById('room-listing-id').value;
    
    const data = {
        listing: parseInt(listingId),
        room_type: parseInt(document.getElementById('room-type').value),
        name: document.getElementById('room-name').value,
        order: parseInt(document.getElementById('room-order').value) || 0,
        description: document.getElementById('room-description').value
    };
    
    const squareMeters = document.getElementById('room-square-meters').value;
    if (squareMeters) {
        data.square_meters = parseFloat(squareMeters);
    }
    
    showLoading(true);
    try {
        if (roomId) {
            await apiRequest(`rooms/${roomId}/`, 'PUT', data);
            showMessage('Stanza aggiornata con successo', 'success');
        } else {
            await apiRequest('rooms/', 'POST', data);
            showMessage('Stanza creata con successo', 'success');
        }
        closeRoomModal();
        await loadRooms(listingId);
    } catch (error) {
        console.error('Error saving room:', error);
    } finally {
        showLoading(false);
    }
}

function editRoom(id, listingId) {
    openRoomModal(listingId, id);
}

async function deleteRoom(id, listingId) {
    if (!confirm('Eliminare questa stanza?')) return;
    
    try {
        await apiRequest(`rooms/${id}/`, 'DELETE');
        showMessage('Stanza eliminata', 'success');
        await loadRooms(listingId);
    } catch (error) {
        console.error('Error deleting room:', error);
    }
}

function manageListingPrices(id) {
    switchSection('prices');
    document.getElementById('price-listing-select').value = id;
    loadPriceRules(id);
}

// Forms
function setupForms() {
    // Listing form
    document.getElementById('form-listing').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveListing();
    });
    
    // Calendar form
    document.getElementById('form-calendar').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveCalendar();
    });
    
    // Price listing select
    document.getElementById('price-listing-select').addEventListener('change', (e) => {
        if (e.target.value) {
            const listingId = e.target.value;
            loadPriceRules(listingId);
            
            // Initialize calendar widget
            initCalendarWidget(listingId);
        } else {
            document.getElementById('prices-content').innerHTML = '<div class="empty-state"><p>Seleziona un annuncio per gestire i prezzi</p></div>';
            document.getElementById('calendar-container').style.display = 'none';
            if (calendarWidget) {
                calendarWidget = null;
            }
        }
    });
    
    // Booking filters
    document.getElementById('booking-listing-select').addEventListener('change', loadBookings);
    document.getElementById('booking-status-select').addEventListener('change', loadBookings);
    
    // Price rule form
    document.getElementById('form-price-rule').addEventListener('submit', async (e) => {
        e.preventDefault();
        await savePriceRule();
    });
    
    // Closure form
    document.getElementById('form-closure').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveClosure();
    });
    
    // New closure button
    document.getElementById('btn-new-closure').addEventListener('click', () => {
        const listingId = document.getElementById('price-listing-select').value;
        if (listingId) {
            openClosureModal(listingId);
        }
    });
    
    // Room form
    document.getElementById('form-room').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveRoom();
    });
    
    // New room button
    document.getElementById('btn-new-room').addEventListener('click', () => {
        const listingId = document.getElementById('room-listing-id').value;
        if (listingId) {
            openRoomModal(listingId);
        }
    });
}

async function saveListing() {
    const form = document.getElementById('form-listing');
    const formData = new FormData(form);
    const listingId = document.getElementById('listing-id').value;
    
    const data = {
        title: document.getElementById('listing-title').value,
        description: document.getElementById('listing-description').value,
        city: document.getElementById('listing-city').value,
        zone: document.getElementById('listing-zone').value,
        address: document.getElementById('listing-address').value,
        base_price: document.getElementById('listing-base-price').value,
        cleaning_fee: document.getElementById('listing-cleaning-fee').value,
        max_guests: parseInt(document.getElementById('listing-max-guests').value),
        included_guests: parseInt(document.getElementById('listing-included-guests').value),
        bedrooms: parseInt(document.getElementById('listing-bedrooms').value),
        bathrooms: parseFloat(document.getElementById('listing-bathrooms').value),
        status: document.getElementById('listing-status').value
    };
    
    showLoading(true);
    try {
        if (listingId) {
            await apiRequest(`listings/${listingId}/`, 'PUT', data);
            showMessage('Annuncio aggiornato con successo', 'success');
        } else {
            await apiRequest('listings/', 'POST', data);
            showMessage('Annuncio creato con successo', 'success');
        }
        closeListingModal();
        loadListings();
    } catch (error) {
        console.error('Error saving listing:', error);
    } finally {
        showLoading(false);
    }
}

// Price Rules
async function loadPriceRules(listingId) {
    showLoading(true);
    try {
        const data = await apiRequest(`price-rules/?listing_id=${listingId}`);
        const rules = data.results || data;
        renderPriceRules(rules, listingId);
        
        // Load closures for the same listing
        await loadClosures(listingId);
    } catch (error) {
        console.error('Error loading price rules:', error);
    } finally {
        showLoading(false);
    }
}

// Closures
async function loadClosures(listingId) {
    try {
        const data = await apiRequest(`closure-rules/?listing_id=${listingId}`);
        const closures = data.results || data;
        renderClosures(closures, listingId);
        
        // Show closures section
        document.getElementById('closures-content').style.display = 'block';
        document.getElementById('btn-new-closure').style.display = 'inline-block';
    } catch (error) {
        console.error('Error loading closures:', error);
    }
}

function renderClosures(closures, listingId) {
    const container = document.getElementById('closures-list');
    
    if (!closures || closures.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Nessuna chiusura configurata</p></div>';
        return;
    }
    
    container.innerHTML = closures.map(closure => `
        <div class="price-rule-item">
            <div class="price-rule-info">
                <div class="price-rule-dates">${formatDate(closure.start_date)} - ${formatDate(closure.end_date)}</div>
                ${closure.reason ? `<div style="font-size: 14px; color: #666; margin-top: 5px;">${closure.reason}</div>` : ''}
                ${closure.is_external_booking ? `<div style="font-size: 12px; color: #e74c3c; margin-top: 3px;">Prenotazione esterna</div>` : ''}
            </div>
            <div>
                <button class="btn btn-secondary" onclick="editClosure(${closure.id}, ${listingId})">Modifica</button>
                <button class="btn btn-danger" onclick="deleteClosure(${closure.id}, ${listingId})">Elimina</button>
            </div>
        </div>
    `).join('');
}

function openClosureModal(listingId, closureId = null) {
    const modal = document.getElementById('modal-closure');
    const form = document.getElementById('form-closure');
    
    document.getElementById('closure-listing-id').value = listingId;
    
    if (closureId) {
        loadClosureData(closureId);
        document.getElementById('modal-closure-title').textContent = 'Modifica Chiusura';
    } else {
        form.reset();
        document.getElementById('closure-id').value = '';
        document.getElementById('modal-closure-title').textContent = 'Nuova Chiusura';
    }
    
    modal.classList.add('active');
}

function closeClosureModal() {
    document.getElementById('modal-closure').classList.remove('active');
}

async function loadClosureData(id) {
    try {
        const closure = await apiRequest(`closure-rules/${id}/`);
        document.getElementById('closure-id').value = closure.id;
        document.getElementById('closure-listing-id').value = closure.listing;
        document.getElementById('closure-start-date').value = closure.start_date;
        document.getElementById('closure-end-date').value = closure.end_date;
        document.getElementById('closure-reason').value = closure.reason || '';
        document.getElementById('closure-is-external').checked = closure.is_external_booking || false;
    } catch (error) {
        console.error('Error loading closure:', error);
    }
}

async function saveClosure() {
    const closureId = document.getElementById('closure-id').value;
    const listingId = document.getElementById('closure-listing-id').value;
    
    const data = {
        listing: parseInt(listingId),
        start_date: document.getElementById('closure-start-date').value,
        end_date: document.getElementById('closure-end-date').value,
        reason: document.getElementById('closure-reason').value,
        is_external_booking: document.getElementById('closure-is-external').checked
    };
    
    showLoading(true);
    try {
        if (closureId) {
            await apiRequest(`closure-rules/${closureId}/`, 'PUT', data);
            showMessage('Chiusura aggiornata con successo', 'success');
        } else {
            await apiRequest('closure-rules/', 'POST', data);
            showMessage('Chiusura creata con successo', 'success');
        }
        closeClosureModal();
        await loadClosures(listingId);
        await refreshCalendarAfterPriceChange(listingId);
    } catch (error) {
        console.error('Error saving closure:', error);
    } finally {
        showLoading(false);
    }
}

function editClosure(id, listingId) {
    openClosureModal(listingId, id);
}

async function deleteClosure(id, listingId) {
    if (!confirm('Eliminare questa chiusura?')) return;
    
    try {
        await apiRequest(`closure-rules/${id}/`, 'DELETE');
        showMessage('Chiusura eliminata', 'success');
        await loadClosures(listingId);
    } catch (error) {
        console.error('Error deleting closure:', error);
    }
}

function renderPriceRules(rules, listingId) {
    const container = document.getElementById('prices-content');
    
    if (!rules || rules.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>Nessuna regola di prezzo. Il prezzo base è €${getListingBasePrice(listingId)}</p>
                <button class="btn btn-primary" onclick="openPriceRuleModal(${listingId})">Aggiungi Regola Prezzo</button>
            </div>
        `;
    } else {
        container.innerHTML = `
            <div style="margin-bottom: 20px;">
                <button class="btn btn-primary" onclick="openPriceRuleModal(${listingId})">+ Aggiungi Regola Prezzo</button>
            </div>
            ${rules.map(rule => `
                <div class="price-rule-item">
                    <div class="price-rule-info">
                        <div class="price-rule-dates">${formatDate(rule.start_date)} - ${formatDate(rule.end_date)}</div>
                        <div class="price-rule-price">€${parseFloat(rule.price).toFixed(2)}/notte</div>
                        ${rule.min_nights ? `<div style="font-size: 12px; color: #666;">Min. ${rule.min_nights} notti</div>` : ''}
                    </div>
                    <div>
                        <button class="btn btn-secondary" onclick="editPriceRule(${rule.id}, ${listingId})">Modifica</button>
                        <button class="btn btn-danger" onclick="deletePriceRule(${rule.id}, ${listingId})">Elimina</button>
                    </div>
                </div>
            `).join('')}
        `;
    }
}

function getListingBasePrice(listingId) {
    const listing = listings.find(l => l.id === parseInt(listingId));
    return listing ? parseFloat(listing.base_price).toFixed(2) : '0.00';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT');
}

function openPriceRuleModal(listingId, ruleId = null) {
    const modal = document.getElementById('modal-price-rule');
    const form = document.getElementById('form-price-rule');
    
    document.getElementById('price-rule-listing-id').value = listingId;
    
    if (ruleId) {
        loadPriceRuleData(ruleId);
        document.getElementById('modal-price-rule-title').textContent = 'Modifica Regola Prezzo';
    } else {
        form.reset();
        document.getElementById('price-rule-id').value = '';
        document.getElementById('modal-price-rule-title').textContent = 'Nuova Regola Prezzo';
    }
    
    modal.classList.add('active');
}

function closePriceRuleModal() {
    document.getElementById('modal-price-rule').classList.remove('active');
}

async function loadPriceRuleData(id) {
    try {
        const rule = await apiRequest(`price-rules/${id}/`);
        document.getElementById('price-rule-id').value = rule.id;
        document.getElementById('price-rule-listing-id').value = rule.listing;
        document.getElementById('price-rule-start-date').value = rule.start_date;
        document.getElementById('price-rule-end-date').value = rule.end_date;
        document.getElementById('price-rule-price').value = rule.price;
        document.getElementById('price-rule-min-nights').value = rule.min_nights || '';
    } catch (error) {
        console.error('Error loading price rule:', error);
    }
}

async function savePriceRule() {
    const ruleId = document.getElementById('price-rule-id').value;
    const listingId = document.getElementById('price-rule-listing-id').value;
    
    const data = {
        listing: parseInt(listingId),
        start_date: document.getElementById('price-rule-start-date').value,
        end_date: document.getElementById('price-rule-end-date').value,
        price: parseFloat(document.getElementById('price-rule-price').value),
    };
    
    const minNights = document.getElementById('price-rule-min-nights').value;
    if (minNights) {
        data.min_nights = parseInt(minNights);
    }
    
    showLoading(true);
    try {
        if (ruleId) {
            await apiRequest(`price-rules/${ruleId}/`, 'PUT', data);
            showMessage('Regola prezzo aggiornata con successo', 'success');
        } else {
            await apiRequest('price-rules/', 'POST', data);
            showMessage('Regola prezzo creata con successo', 'success');
        }
        closePriceRuleModal();
        
        // Reload price rules list
        await loadPriceRules(listingId);
        
        // Force calendar refresh with a small delay to ensure data is updated
        setTimeout(async () => {
            await refreshCalendarAfterPriceChange(listingId);
        }, 300);
    } catch (error) {
        console.error('Error saving price rule:', error);
    } finally {
        showLoading(false);
    }
}

function editPriceRule(ruleId, listingId) {
    openPriceRuleModal(listingId, ruleId);
}

async function deletePriceRule(ruleId, listingId) {
    if (!confirm('Eliminare questa regola di prezzo?')) return;
    
    showLoading(true);
    try {
        await apiRequest(`price-rules/${ruleId}/`, 'DELETE');
        showMessage('Regola eliminata', 'success');
        await loadPriceRules(listingId);
        // Force calendar refresh
        setTimeout(async () => {
            await refreshCalendarAfterPriceChange(listingId);
        }, 300);
    } catch (error) {
        console.error('Error deleting price rule:', error);
        showMessage('Errore nell\'eliminazione della regola', 'error');
    } finally {
        showLoading(false);
    }
}

// Bookings
async function loadBookings() {
    showLoading(true);
    try {
        const listingId = document.getElementById('booking-listing-select').value;
        const status = document.getElementById('booking-status-select').value;
        
        let url = 'bookings/';
        const params = [];
        if (listingId) params.push(`listing_id=${listingId}`);
        if (status) params.push(`status=${status}`);
        if (params.length > 0) url += '?' + params.join('&');
        
        const data = await apiRequest(url);
        const bookings = data.results || data;
        renderBookings(bookings);
    } catch (error) {
        console.error('Error loading bookings:', error);
    } finally {
        showLoading(false);
    }
}

function renderBookings(bookings) {
    const tbody = document.getElementById('bookings-tbody');
    
    if (!bookings || bookings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px;">Nessuna prenotazione trovata</td></tr>';
        return;
    }
    
    tbody.innerHTML = bookings.map(booking => `
        <tr>
            <td>${booking.listing_title}</td>
            <td>${booking.guest_name || booking.guest_email}</td>
            <td>${formatDate(booking.check_in_date)}</td>
            <td>${formatDate(booking.check_out_date)}</td>
            <td>${booking.num_guests}</td>
            <td>€${parseFloat(booking.total_amount).toFixed(2)}</td>
            <td><span class="card-status ${booking.status}">${getBookingStatusLabel(booking.status)}</span></td>
            <td>
                <button class="btn btn-secondary" onclick="viewBooking(${booking.id})">Dettagli</button>
            </td>
        </tr>
    `).join('');
}

function getBookingStatusLabel(status) {
    const labels = {
        pending: 'In Attesa',
        confirmed: 'Confermata',
        cancelled: 'Cancellata',
        completed: 'Completata',
        no_show: 'No Show'
    };
    return labels[status] || status;
}

async function viewBooking(id) {
    showLoading(true);
    try {
        const booking = await apiRequest(`bookings/${id}/`);
        renderBookingDetail(booking);
        document.getElementById('modal-booking').classList.add('active');
    } catch (error) {
        console.error('Error loading booking:', error);
        showMessage('Errore nel caricamento della prenotazione', 'error');
    } finally {
        showLoading(false);
    }
}

function closeBookingModal() {
    document.getElementById('modal-booking').classList.remove('active');
}

function renderBookingDetail(booking) {
    const container = document.getElementById('booking-detail-content');
    
    container.innerHTML = `
        <div class="booking-detail">
            <div class="form-row">
                <div class="form-group">
                    <label>Annuncio</label>
                    <div class="form-control-static">${booking.listing_title}</div>
                </div>
                <div class="form-group">
                    <label>Ospite</label>
                    <div class="form-control-static">${booking.guest_name || booking.guest_email}</div>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Check-in</label>
                    <div class="form-control-static">${formatDate(booking.check_in_date)}</div>
                </div>
                <div class="form-group">
                    <label>Check-out</label>
                    <div class="form-control-static">${formatDate(booking.check_out_date)}</div>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Notti</label>
                    <div class="form-control-static">${booking.total_nights}</div>
                </div>
                <div class="form-group">
                    <label>Ospiti</label>
                    <div class="form-control-static">${booking.num_guests} (${booking.num_adults} adulti, ${booking.num_children} bambini)</div>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Stato</label>
                    <select id="booking-status-update" class="form-control">
                        <option value="pending" ${booking.status === 'pending' ? 'selected' : ''}>In Attesa</option>
                        <option value="confirmed" ${booking.status === 'confirmed' ? 'selected' : ''}>Confermata</option>
                        <option value="cancelled" ${booking.status === 'cancelled' ? 'selected' : ''}>Cancellata</option>
                        <option value="completed" ${booking.status === 'completed' ? 'selected' : ''}>Completata</option>
                        <option value="no_show" ${booking.status === 'no_show' ? 'selected' : ''}>No Show</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Stato Pagamento</label>
                    <select id="booking-payment-status-update" class="form-control">
                        <option value="pending" ${booking.payment_status === 'pending' ? 'selected' : ''}>In Attesa</option>
                        <option value="partial" ${booking.payment_status === 'partial' ? 'selected' : ''}>Parziale</option>
                        <option value="paid" ${booking.payment_status === 'paid' ? 'selected' : ''}>Pagato</option>
                        <option value="refunded" ${booking.payment_status === 'refunded' ? 'selected' : ''}>Rimborsato</option>
                    </select>
                </div>
            </div>
            
            <div class="form-group">
                <label>Prezzo per Notte</label>
                <div class="form-control-static">€${parseFloat(booking.base_price_per_night).toFixed(2)}</div>
            </div>
            
            <div class="price-breakdown">
                <h4>Dettaglio Prezzi</h4>
                <div class="price-row">
                    <span>Subtotale (${booking.total_nights} notti):</span>
                    <span>€${parseFloat(booking.subtotal).toFixed(2)}</span>
                </div>
                <div class="price-row">
                    <span>Pulizie:</span>
                    <span>€${parseFloat(booking.cleaning_fee).toFixed(2)}</span>
                </div>
                ${parseFloat(booking.extra_guest_fee) > 0 ? `
                <div class="price-row">
                    <span>Ospiti extra:</span>
                    <span>€${parseFloat(booking.extra_guest_fee).toFixed(2)}</span>
                </div>
                ` : ''}
                <div class="price-row total">
                    <span><strong>Totale:</strong></span>
                    <span><strong>€${parseFloat(booking.total_amount).toFixed(2)}</strong></span>
                </div>
            </div>
            
            ${booking.special_requests ? `
            <div class="form-group">
                <label>Richieste Speciali</label>
                <div class="form-control-static">${booking.special_requests}</div>
            </div>
            ` : ''}
            
            ${booking.guest_phone ? `
            <div class="form-group">
                <label>Telefono Ospite</label>
                <div class="form-control-static">${booking.guest_phone}</div>
            </div>
            ` : ''}
            
            ${booking.check_in_code ? `
            <div class="form-group">
                <label>Codice Check-in</label>
                <div class="form-control-static"><code>${booking.check_in_code}</code></div>
            </div>
            ` : ''}
            
            ${booking.host_notes ? `
            <div class="form-group">
                <label>Note Host</label>
                <textarea id="booking-host-notes" class="form-control" rows="3">${booking.host_notes}</textarea>
            </div>
            ` : `
            <div class="form-group">
                <label>Note Host</label>
                <textarea id="booking-host-notes" class="form-control" rows="3"></textarea>
            </div>
            `}
            
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeBookingModal()">Chiudi</button>
                <button type="button" class="btn btn-primary" onclick="updateBooking(${booking.id})">Salva Modifiche</button>
            </div>
        </div>
    `;
}

async function updateBooking(id) {
    // Load current booking data first
    let currentBooking;
    try {
        currentBooking = await apiRequest(`bookings/${id}/`);
    } catch (error) {
        console.error('Error loading booking:', error);
        showMessage('Errore nel caricamento della prenotazione', 'error');
        return;
    }
    
    // Use PATCH for partial update instead of PUT
    const data = {
        status: document.getElementById('booking-status-update').value,
        payment_status: document.getElementById('booking-payment-status-update').value,
        host_notes: document.getElementById('booking-host-notes').value,
        // Include required fields to avoid validation errors
        listing: currentBooking.listing,
        guest: currentBooking.guest,
        check_in_date: currentBooking.check_in_date,
        check_out_date: currentBooking.check_out_date,
        num_guests: currentBooking.num_guests,
        num_adults: currentBooking.num_adults || 1,
        num_children: currentBooking.num_children || 0
    };
    
    showLoading(true);
    try {
        await apiRequest(`bookings/${id}/`, 'PATCH', data);
        showMessage('Prenotazione aggiornata con successo', 'success');
        closeBookingModal();
        loadBookings();
    } catch (error) {
        console.error('Error updating booking:', error);
    } finally {
        showLoading(false);
    }
}

// Calendars
async function loadCalendars() {
    showLoading(true);
    try {
        const data = await apiRequest('external-calendars/');
        const calendars = data.results || data;
        renderCalendars(calendars);
    } catch (error) {
        console.error('Error loading calendars:', error);
    } finally {
        showLoading(false);
    }
}

function renderCalendars(calendars) {
    const container = document.getElementById('calendars-list');
    
    if (!calendars || calendars.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Nessun calendario ICAL configurato</p></div>';
        return;
    }
    
    container.innerHTML = calendars.map(calendar => `
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="card-title">${calendar.name}</div>
                    <span class="card-status ${calendar.is_active ? 'active' : 'inactive'}">
                        ${calendar.is_active ? 'Attivo' : 'Non attivo'}
                    </span>
                </div>
            </div>
            <div class="card-info">
                <div class="card-info-item">
                    <span>Provider:</span>
                    <span>${getProviderLabel(calendar.provider)}</span>
                </div>
                <div class="card-info-item">
                    <span>Ultima Sincronizzazione:</span>
                    <span>${calendar.last_sync_display || 'Mai'}</span>
                </div>
                <div class="card-info-item">
                    <span>Stato:</span>
                    <span>${getSyncStatusLabel(calendar.last_sync_status)}</span>
                </div>
            </div>
            <div class="card-actions">
                <button class="btn btn-primary" onclick="syncCalendar(${calendar.id})">Sincronizza</button>
                <button class="btn btn-secondary" onclick="editCalendar(${calendar.id})">Modifica</button>
                <button class="btn btn-danger" onclick="deleteCalendar(${calendar.id})">Elimina</button>
            </div>
        </div>
    `).join('');
}

function getProviderLabel(provider) {
    const labels = {
        airbnb: 'Airbnb',
        booking: 'Booking.com',
        expedia: 'Expedia',
        other: 'Altro'
    };
    return labels[provider] || provider;
}

function getSyncStatusLabel(status) {
    const labels = {
        success: 'Successo',
        error: 'Errore',
        pending: 'In attesa'
    };
    return labels[status] || status;
}

function openCalendarModal(calendarId = null) {
    const modal = document.getElementById('modal-calendar');
    const form = document.getElementById('form-calendar');
    
    if (calendarId) {
        // Load calendar data
        loadCalendarData(calendarId);
        document.getElementById('modal-calendar-title').textContent = 'Modifica Calendario';
    } else {
        form.reset();
        document.getElementById('calendar-id').value = '';
        document.getElementById('modal-calendar-title').textContent = 'Nuovo Calendario ICAL';
    }
    
    modal.classList.add('active');
}

function closeCalendarModal() {
    document.getElementById('modal-calendar').classList.remove('active');
}

async function loadCalendarData(id) {
    try {
        const calendar = await apiRequest(`external-calendars/${id}/`);
        document.getElementById('calendar-id').value = calendar.id;
        document.getElementById('calendar-listing').value = calendar.listing;
        document.getElementById('calendar-name').value = calendar.name;
        document.getElementById('calendar-provider').value = calendar.provider;
        document.getElementById('calendar-ical-url').value = calendar.ical_url;
        document.getElementById('calendar-sync-interval').value = calendar.sync_interval_minutes;
        document.getElementById('calendar-is-active').checked = calendar.is_active;
    } catch (error) {
        console.error('Error loading calendar:', error);
    }
}

async function saveCalendar() {
    const calendarId = document.getElementById('calendar-id').value;
    const data = {
        listing: parseInt(document.getElementById('calendar-listing').value),
        name: document.getElementById('calendar-name').value,
        provider: document.getElementById('calendar-provider').value,
        ical_url: document.getElementById('calendar-ical-url').value,
        sync_interval_minutes: parseInt(document.getElementById('calendar-sync-interval').value),
        is_active: document.getElementById('calendar-is-active').checked
    };
    
    showLoading(true);
    try {
        if (calendarId) {
            await apiRequest(`external-calendars/${calendarId}/`, 'PUT', data);
            showMessage('Calendario aggiornato con successo', 'success');
        } else {
            await apiRequest('external-calendars/', 'POST', data);
            showMessage('Calendario creato con successo', 'success');
        }
        closeCalendarModal();
        loadCalendars();
    } catch (error) {
        console.error('Error saving calendar:', error);
    } finally {
        showLoading(false);
    }
}

async function syncCalendar(id) {
    showLoading(true);
    try {
        const result = await apiRequest(`external-calendars/${id}/sync/`, 'POST');
        showMessage(result.message || 'Sincronizzazione completata', 'success');
        loadCalendars();
    } catch (error) {
        console.error('Error syncing calendar:', error);
    } finally {
        showLoading(false);
    }
}

function editCalendar(id) {
    openCalendarModal(id);
}

async function deleteCalendar(id) {
    if (!confirm('Eliminare questo calendario?')) return;
    
    try {
        await apiRequest(`external-calendars/${id}/`, 'DELETE');
        showMessage('Calendario eliminato', 'success');
        loadCalendars();
    } catch (error) {
        console.error('Error deleting calendar:', error);
    }
}

// Utility Functions
async function loadListingsForSelect(selectId) {
    try {
        const data = await apiRequest('listings/');
        const listingsData = data.results || data;
        const select = document.getElementById(selectId);
        
        // Clear existing options except first
        while (select.options.length > 1) {
            select.remove(1);
        }
        
        listingsData.forEach(listing => {
            const option = document.createElement('option');
            option.value = listing.id;
            option.textContent = listing.title;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading listings for select:', error);
    }
}

async function loadAmenities() {
    // Load amenities for future use
    try {
        await apiRequest('amenities/');
    } catch (error) {
        console.error('Error loading amenities:', error);
    }
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
}

function showMessage(message, type = 'info') {
    const container = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `
        <span>${message}</span>
        <button class="message-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(messageDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Calendar Widget initialization
function initCalendarWidget(listingId) {
    const container = document.getElementById('calendar-container');
    container.style.display = 'block';
    
    // Destroy existing widget if any
    if (calendarWidget) {
        calendarWidget = null;
    }
    
    // Create new widget
    calendarWidget = new CalendarWidget('calendar-container', listingId);
}

// Refresh calendar after price rule changes
async function refreshCalendarAfterPriceChange(listingId) {
    if (calendarWidget && calendarWidget.listingId == listingId) {
        // Clear current data to force reload
        calendarWidget.calendarData = {};
        calendarWidget.priceRules = [];
        
        // Force reload of calendar data
        await calendarWidget.loadCalendarData();
        await calendarWidget.loadBookings();
        calendarWidget.render();
    }
}
