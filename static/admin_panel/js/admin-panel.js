// Admin Panel JavaScript
const API_BASE_URL = '/admin-panel/api/';

// State
let currentSection = 'listings';
let listings = [];
let currentListing = null;
let loadListingsForSelectSeq = 0;
let globalCalendarWidget = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    loadListings();
    loadAmenities();
    setupForms();
});

// ---- Pricing import (JSON) ----
let pricingImportParsed = null;

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
        prices: 'Prezzi e disponibilità',
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
        // Initialize global calendar if no listing is selected
        const priceSelect = document.getElementById('price-listing-select');
        if (!priceSelect.value) {
            initGlobalCalendar();
        }
    } else if (section === 'bookings') {
        loadBookings();
        loadListingsForSelect('booking-listing-select');
    } else if (section === 'calendars') {
        loadCalendars();
        loadListingsForSelect('calendar-listing');
    }
}

function setupPricingImportUi() {
    const card = document.getElementById('prices-import-card');
    const fileInput = document.getElementById('pricing-import-file');
    const analyzeBtn = document.getElementById('pricing-import-analyze-btn');
    const applyBtn = document.getElementById('pricing-import-apply-btn');
    const preview = document.getElementById('pricing-import-preview');
    const mappingBox = document.getElementById('pricing-import-mapping');

    if (!card || !fileInput || !analyzeBtn || !applyBtn || !preview || !mappingBox) return;

    analyzeBtn.addEventListener('click', async () => {
        const file = fileInput.files && fileInput.files[0];
        if (!file) {
            showMessage('Seleziona un file JSON', 'error');
            return;
        }
        try {
            const text = await file.text();
            const json = JSON.parse(text);
            if (!Array.isArray(json)) throw new Error('JSON root deve essere una lista');
            const rooms = json
                .filter(x => x && typeof x === 'object')
                .map(x => ({
                    room_id: String(x.room_id ?? '').trim(),
                    room_name: String(x.room_name ?? '').trim(),
                    prices_count: Array.isArray(x.prices) ? x.prices.length : 0
                }))
                .filter(x => x.room_id && x.prices_count > 0);

            if (rooms.length === 0) throw new Error('Nessuna room valida nel file');

            pricingImportParsed = { raw: json, rooms };

            // Show preview
            preview.style.display = 'block';
            preview.innerHTML = `
                <div style="background:#f8f9fa; padding:12px; border-radius:8px;">
                    <strong>Rooms trovate:</strong>
                    <ul style="margin:8px 0 0 18px;">
                        ${rooms.map(r => `<li><code>${r.room_id}</code> — ${r.room_name || '(senza nome)'} (${r.prices_count} giorni)</li>`).join('')}
                    </ul>
                </div>
            `;

            // Mapping UI
            mappingBox.style.display = 'block';
            const currentListingId = document.getElementById('price-listing-select')?.value || '';

            if (rooms.length === 1) {
                mappingBox.innerHTML = `
                    <div style="background:#fff3cd; padding:12px; border-radius:8px; border:1px solid #ffeeba;">
                        <strong>Verifica:</strong> questa unica room (<code>${rooms[0].room_id}</code>) si riferisce all'annuncio selezionato?
                        <div style="margin-top:10px;">
                            <label style="display:block; font-weight:600; margin-bottom:6px;">Importa su annuncio</label>
                            <select class="form-control" id="pricing-import-mapping-single"></select>
                        </div>
                    </div>
                `;
                fillListingSelect(document.getElementById('pricing-import-mapping-single'), currentListingId);
            } else {
                mappingBox.innerHTML = `
                    <div style="background:#f8f9fa; padding:12px; border-radius:8px;">
                        <strong>Corrispondenza room → annuncio</strong>
                        <div style="margin-top:10px; display:flex; flex-direction:column; gap:10px;" id="pricing-import-mapping-rows"></div>
                    </div>
                `;
                const rows = document.getElementById('pricing-import-mapping-rows');
                rooms.forEach(r => {
                    const row = document.createElement('div');
                    row.style.display = 'grid';
                    row.style.gridTemplateColumns = '1fr 1fr';
                    row.style.gap = '12px';
                    row.innerHTML = `
                        <div>
                            <div style="font-weight:600;"><code>${r.room_id}</code> — ${r.room_name || '(senza nome)'}</div>
                            <div style="font-size:12px; color:#666;">${r.prices_count} giorni</div>
                        </div>
                        <div>
                            <select class="form-control pricing-import-mapping-select" data-room-id="${r.room_id}"></select>
                        </div>
                    `;
                    rows.appendChild(row);
                });
                rows.querySelectorAll('.pricing-import-mapping-select').forEach(sel => fillListingSelect(sel, currentListingId));
            }

            applyBtn.disabled = false;
        } catch (e) {
            pricingImportParsed = null;
            applyBtn.disabled = true;
            preview.style.display = 'none';
            mappingBox.style.display = 'none';
            showMessage(`Errore parsing file: ${e.message}`, 'error');
        }
    });

    applyBtn.addEventListener('click', async () => {
        if (!pricingImportParsed) {
            showMessage('Prima analizza un file valido', 'error');
            return;
        }
        const file = fileInput.files && fileInput.files[0];
        if (!file) {
            showMessage('Seleziona un file JSON', 'error');
            return;
        }

        // Build mapping
        const mapping = {};
        if (pricingImportParsed.rooms.length === 1) {
            const sel = document.getElementById('pricing-import-mapping-single');
            const listingId = sel?.value;
            if (!listingId) {
                showMessage('Seleziona un annuncio per l’import', 'error');
                return;
            }
            mapping[pricingImportParsed.rooms[0].room_id] = parseInt(listingId);
        } else {
            const selects = document.querySelectorAll('.pricing-import-mapping-select');
            for (const s of selects) {
                const roomId = s.getAttribute('data-room-id');
                const listingId = s.value;
                if (!listingId) {
                    showMessage(`Seleziona un annuncio per room_id ${roomId}`, 'error');
                    return;
                }
                mapping[roomId] = parseInt(listingId);
            }
        }

        const replace = document.getElementById('pricing-import-replace')?.checked ? 'true' : 'false';
        const importClosures = document.getElementById('pricing-import-closures')?.checked ? 'true' : 'false';
        const priceModificationPercent = document.getElementById('pricing-import-percent')?.value || '0';

        const form = new FormData();
        form.append('file', file);
        form.append('mapping', JSON.stringify(mapping));
        form.append('replace', replace);
        form.append('import_closures', importClosures);
        form.append('price_modification_percent', priceModificationPercent);

        showLoading(true);
        try {
            const res = await apiRequestFormData('price-rules/import-room-pricing/', form);
            showMessage(`Import completato. Regole create: ${res?.totals?.price_rules_created ?? 0}`, 'success');

            // Refresh current listing view
            const currentListingId = document.getElementById('price-listing-select')?.value;
            if (currentListingId) {
                await loadPriceRules(currentListingId);
                await refreshCalendarAfterPriceChange(currentListingId);
            }
        } catch (e) {
            console.error(e);
        } finally {
            showLoading(false);
        }
    });
}

function fillListingSelect(selectEl, preselectId = '') {
    if (!selectEl) return;
    // Placeholder
    selectEl.innerHTML = '';
    const ph = document.createElement('option');
    ph.value = '';
    ph.textContent = 'Seleziona annuncio...';
    selectEl.appendChild(ph);

    const seen = new Set();
    for (const l of (listings || [])) {
        const id = String(l.id);
        if (seen.has(id)) continue;
        seen.add(id);
        const opt = document.createElement('option');
        opt.value = l.id;
        opt.textContent = l.title;
        selectEl.appendChild(opt);
    }
    if (preselectId) {
        selectEl.value = String(preselectId);
    }
}

async function apiRequestFormData(endpoint, formData) {
    const response = await fetch(API_BASE_URL + endpoint, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        credentials: 'include',
        body: formData
    });

    if (response.status === 204) return null;
    const contentType = response.headers.get('content-type') || '';
    const bodyText = await response.text();
    const json = contentType.includes('application/json') && bodyText ? JSON.parse(bodyText) : null;

    if (!response.ok) {
        const msg = (json && (json.detail || json.error)) || bodyText.slice(0, 200) || `Errore (HTTP ${response.status})`;
        showMessage(msg, 'error');
        throw new Error(msg);
    }

    return json;
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
        
        // 204 No Content (tipico per DELETE): non c'è body da parsare
        if (response.status === 204) {
            return null;
        }

        const contentType = response.headers.get('content-type') || '';
        let result = null;
        let text = null;

        // Se non è JSON (es. redirect/login HTML), non fare response.json()
        if (contentType.includes('application/json')) {
            // Alcune risposte 200/201 possono comunque avere body vuoto
            const bodyText = await response.text();
            result = bodyText ? JSON.parse(bodyText) : null;
        } else {
            text = await response.text();
        }

        // Caso tipico: sessione scaduta / redirect a login (HTML)
        if (contentType.includes('text/html')) {
            throw new Error('Sessione scaduta o accesso negato. Effettua il login e ricarica la pagina.');
        }
        
        if (!response.ok) {
            const msg =
                (result && (result.detail || result.error)) ||
                (text ? text.slice(0, 200) : null) ||
                `Errore nella richiesta (HTTP ${response.status})`;
            throw new Error(msg);
        }
        
        return result ?? { raw: text };
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
            ${listing.airbnb_listing_url ? `
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                    <div style="display: flex; gap: 8px; align-items: center; justify-content: space-between;">
                        <div style="flex: 1;">
                            <small style="color: #666; display: block; margin-bottom: 4px;">URL Airbnb:</small>
                            <a href="${listing.airbnb_listing_url}" target="_blank" style="font-size: 12px; color: #0066cc; word-break: break-all;">${listing.airbnb_listing_url}</a>
                        </div>
                        <button class="btn btn-secondary" onclick="syncAirbnbReviews(${listing.id}, event)" style="white-space: nowrap; padding: 6px 12px; font-size: 12px;" title="Sincronizza recensioni da Airbnb">
                            🔄 Sync Recensioni
                        </button>
                    </div>
                    ${listing.airbnb_reviews_last_synced ? `
                        <small style="color: #666; display: block; margin-top: 8px;">
                            Ultima sync: ${new Date(listing.airbnb_reviews_last_synced).toLocaleString('it-IT')}
                        </small>
                    ` : ''}
                </div>
            ` : `
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                    <small style="color: #999;">Nessun URL Airbnb configurato</small>
                </div>
            `}
        </div>
    `).join('');
}

async function syncAirbnbReviews(listingId, event) {
    if (event) {
        event.stopPropagation();
    }
    
    const listing = listings.find(l => l.id === listingId);
    if (!listing) {
        showMessage('Annuncio non trovato', 'error');
        return;
    }
    
    if (!listing.airbnb_listing_url) {
        showMessage('URL Airbnb non configurato per questo annuncio', 'error');
        return;
    }
    
    if (!confirm(`Vuoi sincronizzare le recensioni da Airbnb per "${listing.title}"?\n\nURL: ${listing.airbnb_listing_url}`)) {
        return;
    }
    
    showLoading(true);
    try {
        const response = await apiRequest(`listings/${listingId}/sync-airbnb-reviews/`, 'POST', {
            airbnb_url: listing.airbnb_listing_url
        });
        
        if (response.success) {
            showMessage(
                `Sincronizzazione completata! Trovate: ${response.stats.total_found}, Create: ${response.stats.created}, Aggiornate: ${response.stats.updated}`,
                'success'
            );
            // Reload listings to update last_synced timestamp
            await loadListings();
        } else {
            showMessage(response.error || 'Errore durante la sincronizzazione', 'error');
        }
    } catch (error) {
        console.error('Error syncing reviews:', error);
        showMessage(error.message || 'Errore durante la sincronizzazione', 'error');
    } finally {
        showLoading(false);
    }
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
    document.getElementById('listing-airbnb-url').value = listing.airbnb_listing_url || '';
    
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
    
    // Check if modal-rooms-list is open
    const roomsListModal = document.getElementById('modal-rooms-list');
    const isRoomsListOpen = roomsListModal && roomsListModal.classList.contains('active');
    
    document.getElementById('room-listing-id').value = listingId;
    
    if (roomId) {
        loadRoomData(roomId);
        document.getElementById('modal-room-title').textContent = 'Modifica Stanza';
    } else {
        form.reset();
        document.getElementById('room-id').value = '';
        document.getElementById('modal-room-title').textContent = 'Nuova Stanza';
    }
    
    // Increase z-index if opened from rooms list modal
    if (isRoomsListOpen) {
        modal.style.zIndex = '2000';
    } else {
        modal.style.zIndex = '';
    }
    
    modal.classList.add('active');
}

function closeRoomModal() {
    const modal = document.getElementById('modal-room');
    modal.classList.remove('active');
    // Reset z-index when closing
    modal.style.zIndex = '';
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
        // Hide tabs container when no listing is selected
        document.getElementById('rules-tabs-container').style.display = 'none';
        
        if (e.target.value) {
            const listingId = e.target.value;
            loadPriceRules(listingId);
            
            // Initialize calendar widget for single listing
            initCalendarWidget(listingId);

            // Hide global calendar
            document.getElementById('global-calendar-container').style.display = 'none';
            if (globalCalendarWidget) {
                globalCalendarWidget = null;
            }

            // Show import UI when a listing is selected
            const importCard = document.getElementById('prices-import-card');
            if (importCard) importCard.style.display = 'block';
        } else {
            // Show global view
            document.getElementById('prices-content').innerHTML = '<div class="empty-state"><p>Vista globale attiva. Seleziona un annuncio specifico per gestire i dettagli.</p></div>';
            document.getElementById('calendar-container').style.display = 'none';
            document.getElementById('rules-tabs-container').style.display = 'none';
            const importCard = document.getElementById('prices-import-card');
            if (importCard) importCard.style.display = 'none';
            
            // Hide global calendar if it was shown
            document.getElementById('global-calendar-container').style.display = 'none';
            if (calendarWidget) {
                calendarWidget = null;
            }
            
            // Initialize global calendar
            initGlobalCalendar();
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
    
    // CheckInOut Rule form
    document.getElementById('form-checkinout-rule').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveCheckInOutRule();
    });
    
    document.getElementById('btn-new-checkinout').addEventListener('click', () => {
        const listingId = document.getElementById('price-listing-select').value;
        if (listingId) {
            openCheckInOutRuleModal(listingId);
        }
    });
    
    // Show/hide fields based on recurrence type
    document.getElementById('checkinout-recurrence-type').addEventListener('change', (e) => {
        const recurrenceType = e.target.value;
        const specificDateGroup = document.getElementById('checkinout-specific-date-group');
        const dayOfWeekGroup = document.getElementById('checkinout-day-of-week-group');
        
        if (recurrenceType === 'specific_date') {
            specificDateGroup.style.display = 'block';
            dayOfWeekGroup.style.display = 'none';
            document.getElementById('checkinout-specific-date').required = true;
            document.getElementById('checkinout-day-of-week').required = false;
        } else if (recurrenceType === 'weekly') {
            specificDateGroup.style.display = 'none';
            dayOfWeekGroup.style.display = 'block';
            document.getElementById('checkinout-specific-date').required = false;
            document.getElementById('checkinout-day-of-week').required = true;
        } else {
            specificDateGroup.style.display = 'none';
            dayOfWeekGroup.style.display = 'none';
            document.getElementById('checkinout-specific-date').required = false;
            document.getElementById('checkinout-day-of-week').required = false;
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

    // Pricing import UI
    setupPricingImportUi();
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
        status: document.getElementById('listing-status').value,
        airbnb_listing_url: document.getElementById('listing-airbnb-url').value || null
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
        
        // Load checkinout rules for the same listing
        await loadCheckInOutRules(listingId);
        
        // Show tabs container
        document.getElementById('rules-tabs-container').style.display = 'block';
        
        // Switch to price rules tab by default
        switchRulesTab('price-rules');
    } catch (error) {
        console.error('Error loading price rules:', error);
    } finally {
        showLoading(false);
    }
}

// Switch between rules tabs
function switchRulesTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.rules-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.rules-tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab content
    const selectedContent = document.getElementById(`tab-content-${tabName}`);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }
    
    // Add active class to selected button
    const selectedButton = document.querySelector(`.rules-tab-button[data-tab="${tabName}"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
}

// Closures
async function loadClosures(listingId) {
    try {
        const data = await apiRequest(`closure-rules/?listing_id=${listingId}`);
        const closures = data.results || data;
        renderClosures(closures, listingId);
        
        // Show button (tab container is already shown by loadPriceRules)
        const btnNewClosure = document.getElementById('btn-new-closure');
        if (btnNewClosure) {
            btnNewClosure.style.display = 'inline-block';
        }
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

// CheckInOut Rules
async function loadCheckInOutRules(listingId) {
    try {
        const data = await apiRequest(`checkinout-rules/?listing_id=${listingId}`);
        const rules = data.results || data;
        renderCheckInOutRules(rules, listingId);
        
        // Show button (tab container is already shown by loadPriceRules)
        const btnNewCheckinout = document.getElementById('btn-new-checkinout');
        if (btnNewCheckinout) {
            btnNewCheckinout.style.display = 'inline-block';
        }
    } catch (error) {
        console.error('Error loading checkinout rules:', error);
    }
}

function renderCheckInOutRules(rules, listingId) {
    const container = document.getElementById('checkinout-list');
    
    if (!rules || rules.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Nessuna regola check-in/check-out configurata</p></div>';
        return;
    }
    
    const ruleTypeLabels = {
        'no_checkin': 'No Check-in',
        'no_checkout': 'No Check-out'
    };
    
    const recurrenceTypeLabels = {
        'specific_date': 'Data Specifica',
        'weekly': 'Settimanale'
    };
    
    container.innerHTML = rules.map(rule => {
        const restrictionDisplay = rule.restriction_display || 'N/A';
        return `
        <div class="price-rule-item">
            <div class="price-rule-info">
                <div class="price-rule-dates">
                    <strong>${ruleTypeLabels[rule.rule_type] || rule.rule_type}</strong> - ${recurrenceTypeLabels[rule.recurrence_type] || rule.recurrence_type}
                </div>
                <div style="font-size: 14px; color: #666; margin-top: 5px;">${restrictionDisplay}</div>
            </div>
            <div>
                <button class="btn btn-secondary" onclick="editCheckInOutRule(${rule.id}, ${listingId})">Modifica</button>
                <button class="btn btn-danger" onclick="deleteCheckInOutRule(${rule.id}, ${listingId})">Elimina</button>
            </div>
        </div>
        `;
    }).join('');
}

function openCheckInOutRuleModal(listingId, ruleId = null) {
    const modal = document.getElementById('modal-checkinout-rule');
    const form = document.getElementById('form-checkinout-rule');
    
    document.getElementById('checkinout-rule-listing-id').value = listingId;
    
    if (ruleId) {
        loadCheckInOutRuleData(ruleId);
        document.getElementById('modal-checkinout-rule-title').textContent = 'Modifica Regola Check-in/Check-out';
    } else {
        form.reset();
        document.getElementById('checkinout-rule-id').value = '';
        document.getElementById('checkinout-specific-date-group').style.display = 'none';
        document.getElementById('checkinout-day-of-week-group').style.display = 'none';
        document.getElementById('modal-checkinout-rule-title').textContent = 'Nuova Regola Check-in/Check-out';
    }
    
    modal.classList.add('active');
}

function closeCheckInOutRuleModal() {
    const modal = document.getElementById('modal-checkinout-rule');
    modal.classList.remove('active');
    
    // Reset form and hide conditional fields
    const form = document.getElementById('form-checkinout-rule');
    form.reset();
    document.getElementById('checkinout-specific-date-group').style.display = 'none';
    document.getElementById('checkinout-day-of-week-group').style.display = 'none';
    document.getElementById('checkinout-specific-date').required = false;
    document.getElementById('checkinout-day-of-week').required = false;
}

async function loadCheckInOutRuleData(id) {
    try {
        const rule = await apiRequest(`checkinout-rules/${id}/`);
        document.getElementById('checkinout-rule-id').value = rule.id;
        document.getElementById('checkinout-rule-listing-id').value = rule.listing;
        document.getElementById('checkinout-rule-type').value = rule.rule_type || '';
        document.getElementById('checkinout-recurrence-type').value = rule.recurrence_type || '';
        
        // Show/hide appropriate fields based on recurrence_type
        if (rule.recurrence_type === 'specific_date') {
            document.getElementById('checkinout-specific-date-group').style.display = 'block';
            document.getElementById('checkinout-day-of-week-group').style.display = 'none';
            document.getElementById('checkinout-specific-date').value = rule.specific_date || '';
        } else if (rule.recurrence_type === 'weekly') {
            document.getElementById('checkinout-specific-date-group').style.display = 'none';
            document.getElementById('checkinout-day-of-week-group').style.display = 'block';
            document.getElementById('checkinout-day-of-week').value = rule.day_of_week !== null && rule.day_of_week !== undefined ? rule.day_of_week.toString() : '';
        }
    } catch (error) {
        console.error('Error loading checkinout rule:', error);
    }
}

async function saveCheckInOutRule() {
    const ruleId = document.getElementById('checkinout-rule-id').value;
    const listingId = document.getElementById('checkinout-rule-listing-id').value;
    const recurrenceType = document.getElementById('checkinout-recurrence-type').value;
    
    const data = {
        listing: parseInt(listingId),
        rule_type: document.getElementById('checkinout-rule-type').value,
        recurrence_type: recurrenceType
    };
    
    // Add appropriate field based on recurrence_type
    if (recurrenceType === 'specific_date') {
        const specificDate = document.getElementById('checkinout-specific-date').value;
        if (!specificDate) {
            showMessage('Inserisci una data specifica', 'error');
            return;
        }
        data.specific_date = specificDate;
        data.day_of_week = null;
    } else if (recurrenceType === 'weekly') {
        const dayOfWeek = document.getElementById('checkinout-day-of-week').value;
        if (dayOfWeek === '') {
            showMessage('Seleziona un giorno della settimana', 'error');
            return;
        }
        data.day_of_week = parseInt(dayOfWeek);
        data.specific_date = null;
    }
    
    showLoading(true);
    try {
        if (ruleId) {
            await apiRequest(`checkinout-rules/${ruleId}/`, 'PUT', data);
            showMessage('Regola aggiornata con successo', 'success');
        } else {
            await apiRequest('checkinout-rules/', 'POST', data);
            showMessage('Regola creata con successo', 'success');
        }
        closeCheckInOutRuleModal();
        await loadCheckInOutRules(listingId);
        await refreshCalendarAfterPriceChange(listingId);
    } catch (error) {
        console.error('Error saving checkinout rule:', error);
        showMessage('Errore nel salvataggio della regola', 'error');
    } finally {
        showLoading(false);
    }
}

function editCheckInOutRule(id, listingId) {
    openCheckInOutRuleModal(listingId, id);
}

async function deleteCheckInOutRule(id, listingId) {
    if (!confirm('Eliminare questa regola?')) return;
    
    try {
        await apiRequest(`checkinout-rules/${id}/`, 'DELETE');
        showMessage('Regola eliminata', 'success');
        await loadCheckInOutRules(listingId);
    } catch (error) {
        console.error('Error deleting checkinout rule:', error);
    }
}

function renderPriceRules(rules, listingId) {
    const container = document.getElementById('price-rules-list-container');
    if (!container) return;
    
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

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getDaysUntil(dateString) {
    if (!dateString) return null;
    const targetDate = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    targetDate.setHours(0, 0, 0, 0);
    const diffTime = targetDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
}

function getDaysUntilLabel(dateString) {
    const days = getDaysUntil(dateString);
    if (days === null) return '-';
    if (days < 0) return `Scaduto (${Math.abs(days)} giorni fa)`;
    if (days === 0) return 'Oggi';
    if (days === 1) return 'Domani';
    return `${days} giorni`;
}

function getPaymentStatusLabel(status) {
    const labels = {
        pending: 'In Attesa',
        partial: 'Parziale',
        paid: 'Pagato',
        refunded: 'Rimborsato'
    };
    return labels[status] || status;
}

function openPriceRuleModal(listingId, ruleId = null) {
    const modal = document.getElementById('modal-price-rule');
    const form = document.getElementById('form-price-rule');
    const listingsGroup = document.getElementById('price-rule-listings-group');
    const listingsCheckboxes = document.getElementById('price-rule-listings-checkboxes');
    
    // When editing an existing rule, always hide multi-select
    if (ruleId) {
        listingsGroup.style.display = 'none';
        loadPriceRuleData(ruleId);
        document.getElementById('modal-price-rule-title').textContent = 'Modifica Regola Prezzo';
    } else {
        // If listingId is null or empty, show multi-select (global view)
        if (!listingId || listingId === '') {
            listingsGroup.style.display = 'block';
            listingsCheckboxes.innerHTML = '';
            
            // Populate checkboxes with all listings
            listings.forEach(listing => {
                const label = document.createElement('label');
                label.style.display = 'flex';
                label.style.gap = '8px';
                label.style.alignItems = 'center';
                label.style.fontWeight = 'normal';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = listing.id;
                checkbox.checked = true; // Default: all selected
                checkbox.setAttribute('data-listing-id', listing.id);
                
                const span = document.createElement('span');
                span.textContent = listing.title;
                
                label.appendChild(checkbox);
                label.appendChild(span);
                listingsCheckboxes.appendChild(label);
            });
            
            document.getElementById('price-rule-listing-id').value = '';
        } else {
            listingsGroup.style.display = 'none';
            document.getElementById('price-rule-listing-id').value = listingId;
        }
        
        form.reset();
        document.getElementById('price-rule-id').value = '';
        document.getElementById('modal-price-rule-title').textContent = 'Nuova Regola Prezzo';
    }
    
    modal.classList.add('active');
}

function closePriceRuleModal() {
    const modal = document.getElementById('modal-price-rule');
    modal.classList.remove('active');
    
    // Reset form
    const form = document.getElementById('form-price-rule');
    form.reset();
    document.getElementById('price-rule-id').value = '';
    document.getElementById('price-rule-listing-id').value = '';
    document.getElementById('price-rule-listings-group').style.display = 'none';
    document.getElementById('price-rule-listings-checkboxes').innerHTML = '';
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
    const listingsGroup = document.getElementById('price-rule-listings-group');
    
    // Determine which listings to apply the rule to
    let targetListingIds = [];
    if (listingsGroup.style.display === 'block') {
        // Multi-select mode: get checked listings
        const checkboxes = listingsGroup.querySelectorAll('input[type="checkbox"]:checked');
        if (checkboxes.length === 0) {
            showMessage('Seleziona almeno un appartamento', 'error');
            return;
        }
        targetListingIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    } else {
        // Single listing mode
        if (!listingId) {
            showMessage('Seleziona un appartamento', 'error');
            return;
        }
        targetListingIds = [parseInt(listingId)];
    }
    
    const baseData = {
        start_date: document.getElementById('price-rule-start-date').value,
        end_date: document.getElementById('price-rule-end-date').value,
        price: parseFloat(document.getElementById('price-rule-price').value),
    };
    
    const minNights = document.getElementById('price-rule-min-nights').value;
    if (minNights) {
        baseData.min_nights = parseInt(minNights);
    }
    
    showLoading(true);
    try {
        if (ruleId) {
            // Editing: only update the single rule
            const data = { ...baseData, listing: targetListingIds[0] };
            await apiRequest(`price-rules/${ruleId}/`, 'PUT', data);
            showMessage('Regola prezzo aggiornata con successo', 'success');
            
            // Refresh calendar for the listing
            if (targetListingIds[0]) {
                await loadPriceRules(targetListingIds[0]);
                setTimeout(async () => {
                    await refreshCalendarAfterPriceChange(targetListingIds[0]);
                }, 300);
            }
        } else {
            // Creating: create rules for all selected listings
            const promises = targetListingIds.map(listingId => {
                const data = { ...baseData, listing: listingId };
                return apiRequest('price-rules/', 'POST', data);
            });
            
            await Promise.all(promises);
            showMessage(`Regola prezzo creata per ${targetListingIds.length} appartamento/i`, 'success');
            
            // Refresh global calendar if active
            if (globalCalendarWidget) {
                setTimeout(async () => {
                    await globalCalendarWidget.loadCalendarData();
                }, 300);
            }
            
            // Refresh single listing view if active
            const currentListingId = document.getElementById('price-listing-select')?.value;
            if (currentListingId && calendarWidget) {
                await loadPriceRules(currentListingId);
                setTimeout(async () => {
                    await refreshCalendarAfterPriceChange(currentListingId);
                }, 300);
            }
        }
        closePriceRuleModal();
    } catch (error) {
        console.error('Error saving price rule:', error);
        showMessage('Errore nel salvataggio della regola', 'error');
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
        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 40px;">Nessuna prenotazione trovata</td></tr>';
        return;
    }
    
    tbody.innerHTML = bookings.map(booking => {
        const daysUntilCheckin = getDaysUntil(booking.check_in_date);
        const isUrgent = daysUntilCheckin !== null && daysUntilCheckin >= 0 && daysUntilCheckin <= 3;
        const rowClass = isUrgent ? 'booking-row-urgent' : '';
        
        return `
        <tr class="${rowClass}" data-booking-id="${booking.id}">
            <td>
                <div class="booking-listing-cell">
                    <strong>${booking.listing_title || '-'}</strong>
                </div>
            </td>
            <td>
                <div class="booking-guest-cell">
                    ${booking.guest_name || booking.guest_email || '-'}
                </div>
            </td>
            <td>
                <div class="booking-date-cell">
                    ${formatDate(booking.check_in_date)}
                    ${isUrgent ? `<span class="booking-urgent-badge">${getDaysUntilLabel(booking.check_in_date)}</span>` : ''}
                </div>
            </td>
            <td>${formatDate(booking.check_out_date)}</td>
            <td>${booking.num_guests}</td>
            <td><strong>€${parseFloat(booking.total_amount).toFixed(2)}</strong></td>
            <td>
                <span class="booking-badge booking-badge-status booking-badge-${booking.status}">
                    ${getBookingStatusLabel(booking.status)}
                </span>
            </td>
            <td>
                <span class="booking-badge booking-badge-payment booking-badge-${booking.payment_status}">
                    ${getPaymentStatusLabel(booking.payment_status)}
                </span>
            </td>
            <td>
                <span class="booking-date-small">${formatDateTime(booking.created_at)}</span>
            </td>
            <td>
                <div class="booking-actions-cell">
                    <button class="btn btn-secondary btn-sm" onclick="viewBooking(${booking.id})" title="Dettagli">
                        👁️
                    </button>
                    ${booking.status === 'pending' ? `
                    <button class="btn btn-success btn-sm" onclick="quickConfirmBooking(${booking.id})" title="Conferma">
                        ✓
                    </button>
                    ` : ''}
                    ${booking.status !== 'cancelled' && booking.status !== 'completed' ? `
                    <button class="btn btn-danger btn-sm" onclick="quickCancelBooking(${booking.id})" title="Cancella">
                        ✕
                    </button>
                    ` : ''}
                </div>
            </td>
        </tr>
        `;
    }).join('');
}

async function quickConfirmBooking(id) {
    if (!confirm('Confermare questa prenotazione?')) return;
    
    showLoading(true);
    try {
        const booking = await apiRequest(`bookings/${id}/`);
        const data = {
            ...booking,
            status: 'confirmed'
        };
        await apiRequest(`bookings/${id}/`, 'PATCH', data);
        showMessage('Prenotazione confermata', 'success');
        loadBookings();
    } catch (error) {
        console.error('Error confirming booking:', error);
        showMessage('Errore nella conferma', 'error');
    } finally {
        showLoading(false);
    }
}

async function quickCancelBooking(id) {
    if (!confirm('Cancellare questa prenotazione?')) return;
    
    showLoading(true);
    try {
        const booking = await apiRequest(`bookings/${id}/`);
        const data = {
            ...booking,
            status: 'cancelled'
        };
        await apiRequest(`bookings/${id}/`, 'PATCH', data);
        showMessage('Prenotazione cancellata', 'success');
        loadBookings();
    } catch (error) {
        console.error('Error cancelling booking:', error);
        showMessage('Errore nella cancellazione', 'error');
    } finally {
        showLoading(false);
    }
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
    const daysUntilCheckin = getDaysUntil(booking.check_in_date);
    const isUrgent = daysUntilCheckin !== null && daysUntilCheckin >= 0 && daysUntilCheckin <= 3;
    
    container.innerHTML = `
        <div class="booking-detail">
            <!-- Header con ID e Badge -->
            <div class="booking-detail-header">
                <div class="booking-detail-title">
                    <h3>Prenotazione #${booking.id}</h3>
                    <div class="booking-badges">
                        <span class="booking-badge booking-badge-status booking-badge-${booking.status}">
                            ${getBookingStatusLabel(booking.status)}
                        </span>
                        <span class="booking-badge booking-badge-payment booking-badge-${booking.payment_status}">
                            ${getPaymentStatusLabel(booking.payment_status)}
                        </span>
                        ${isUrgent ? `<span class="booking-badge booking-badge-urgent">Check-in tra ${getDaysUntilLabel(booking.check_in_date)}</span>` : ''}
                    </div>
                </div>
                <div class="booking-detail-meta">
                    <span class="booking-meta-item">
                        <span class="booking-meta-label">Creata:</span>
                        <span>${formatDateTime(booking.created_at)}</span>
                    </span>
                    ${booking.updated_at && booking.updated_at !== booking.created_at ? `
                    <span class="booking-meta-item">
                        <span class="booking-meta-label">Aggiornata:</span>
                        <span>${formatDateTime(booking.updated_at)}</span>
                    </span>
                    ` : ''}
                </div>
            </div>

            <!-- Tabs Navigation -->
            <div class="booking-tabs">
                <button class="booking-tab active" data-tab="info" onclick="switchBookingTab('info')">
                    <span class="tab-icon">📋</span>
                    <span>Informazioni</span>
                </button>
                <button class="booking-tab" data-tab="pricing" onclick="switchBookingTab('pricing')">
                    <span class="tab-icon">💰</span>
                    <span>Prezzi</span>
                </button>
                <button class="booking-tab" data-tab="contacts" onclick="switchBookingTab('contacts')">
                    <span class="tab-icon">📞</span>
                    <span>Contatti</span>
                </button>
                <button class="booking-tab" data-tab="access" onclick="switchBookingTab('access')">
                    <span class="tab-icon">🔑</span>
                    <span>Accesso</span>
                </button>
                <button class="booking-tab" data-tab="payments" onclick="switchBookingTab('payments')">
                    <span class="tab-icon">💳</span>
                    <span>Pagamenti</span>
                </button>
                <button class="booking-tab" data-tab="messages" onclick="switchBookingTab('messages')">
                    <span class="tab-icon">💬</span>
                    <span>Messaggi</span>
                </button>
                <button class="booking-tab" data-tab="notes" onclick="switchBookingTab('notes')">
                    <span class="tab-icon">📝</span>
                    <span>Note</span>
                </button>
            </div>

            <!-- Tab Content: Informazioni -->
            <div class="booking-tab-content active" id="booking-tab-info">
                <div class="booking-card">
                    <h4 class="booking-card-title">Informazioni Base</h4>
                    <div class="booking-card-grid">
                        <div class="booking-info-item">
                            <label>Annuncio</label>
                            <div class="booking-info-value">
                                ${booking.listing_title}
                                ${booking.listing ? `<a href="/admin/listings/listing/${booking.listing}/change/" target="_blank" class="booking-link">Vedi annuncio →</a>` : ''}
                            </div>
                        </div>
                        <div class="booking-info-item">
                            <label>Ospite</label>
                            <div class="booking-info-value">
                                ${booking.guest_name || booking.guest_email}
                                ${booking.guest ? `<a href="/admin/auth/user/${booking.guest}/change/" target="_blank" class="booking-link">Vedi profilo →</a>` : ''}
                            </div>
                        </div>
                        <div class="booking-info-item">
                            <label>Check-in</label>
                            <div class="booking-info-value">
                                ${formatDate(booking.check_in_date)}
                                <span class="booking-days-badge">${getDaysUntilLabel(booking.check_in_date)}</span>
                            </div>
                        </div>
                        <div class="booking-info-item">
                            <label>Check-out</label>
                            <div class="booking-info-value">${formatDate(booking.check_out_date)}</div>
                        </div>
                        <div class="booking-info-item">
                            <label>Notti</label>
                            <div class="booking-info-value">${booking.total_nights}</div>
                        </div>
                        <div class="booking-info-item">
                            <label>Ospiti</label>
                            <div class="booking-info-value">
                                ${booking.num_guests} totali
                                ${booking.num_adults || booking.num_children ? `(${booking.num_adults || 0} adulti, ${booking.num_children || 0} bambini)` : ''}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="booking-card">
                    <h4 class="booking-card-title">Stati</h4>
                    <div class="booking-card-grid">
                        <div class="booking-info-item">
                            <label>Stato Prenotazione</label>
                            <select id="booking-status-update" class="form-control">
                                <option value="pending" ${booking.status === 'pending' ? 'selected' : ''}>In Attesa</option>
                                <option value="confirmed" ${booking.status === 'confirmed' ? 'selected' : ''}>Confermata</option>
                                <option value="cancelled" ${booking.status === 'cancelled' ? 'selected' : ''}>Cancellata</option>
                                <option value="completed" ${booking.status === 'completed' ? 'selected' : ''}>Completata</option>
                                <option value="no_show" ${booking.status === 'no_show' ? 'selected' : ''}>No Show</option>
                            </select>
                        </div>
                        <div class="booking-info-item">
                            <label>Stato Pagamento</label>
                            <select id="booking-payment-status-update" class="form-control">
                                <option value="pending" ${booking.payment_status === 'pending' ? 'selected' : ''}>In Attesa</option>
                                <option value="partial" ${booking.payment_status === 'partial' ? 'selected' : ''}>Parziale</option>
                                <option value="paid" ${booking.payment_status === 'paid' ? 'selected' : ''}>Pagato</option>
                                <option value="refunded" ${booking.payment_status === 'refunded' ? 'selected' : ''}>Rimborsato</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab Content: Prezzi -->
            <div class="booking-tab-content" id="booking-tab-pricing">
                <div class="booking-card">
                    <h4 class="booking-card-title">Dettaglio Prezzi</h4>
                    <div class="price-breakdown">
                        <div class="price-breakdown-item">
                            <div class="price-breakdown-label">
                                <span>Prezzo per notte</span>
                                <span class="price-breakdown-nights">× ${booking.total_nights} notti</span>
                            </div>
                            <div class="price-breakdown-value">€${parseFloat(booking.base_price_per_night).toFixed(2)}</div>
                        </div>
                        <div class="price-breakdown-item">
                            <div class="price-breakdown-label">Subtotale</div>
                            <div class="price-breakdown-value">€${parseFloat(booking.subtotal).toFixed(2)}</div>
                        </div>
                        <div class="price-breakdown-item">
                            <div class="price-breakdown-label">Pulizie</div>
                            <div class="price-breakdown-value">€${parseFloat(booking.cleaning_fee).toFixed(2)}</div>
                        </div>
                        ${parseFloat(booking.extra_guest_fee) > 0 ? `
                        <div class="price-breakdown-item">
                            <div class="price-breakdown-label">Ospiti extra</div>
                            <div class="price-breakdown-value">€${parseFloat(booking.extra_guest_fee).toFixed(2)}</div>
                        </div>
                        ` : ''}
                        <div class="price-breakdown-item price-breakdown-total">
                            <div class="price-breakdown-label">Totale</div>
                            <div class="price-breakdown-value">€${parseFloat(booking.total_amount).toFixed(2)}</div>
                        </div>
                    </div>
                </div>
                
                <div class="booking-card" style="margin-top: 16px;">
                    <h4 class="booking-card-title">Prezzo Finale (Offerta)</h4>
                    <div class="booking-card-grid">
                        <div class="booking-info-item">
                            <label for="booking-total-amount">Prezzo finale modificabile</label>
                            <div class="booking-price-offer-container">
                                <input type="number" 
                                       id="booking-total-amount" 
                                       class="form-control" 
                                       step="0.01"
                                       min="0"
                                       placeholder="0.00"
                                       value="${parseFloat(booking.total_amount).toFixed(2)}">
                                <span class="booking-price-currency">€</span>
                            </div>
                            <small class="form-text">Puoi modificare il prezzo finale per creare un'offerta personalizzata</small>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab Content: Contatti -->
            <div class="booking-tab-content" id="booking-tab-contacts">
                <div class="booking-card">
                    <h4 class="booking-card-title">Informazioni Contatto</h4>
                    <div class="booking-card-grid">
                        <div class="booking-info-item">
                            <label>Email</label>
                            <div class="booking-info-value">
                                ${booking.guest_email || booking.guest_email || '-'}
                                ${booking.guest_email ? `<a href="mailto:${booking.guest_email}" class="booking-link">Invia email →</a>` : ''}
                            </div>
                        </div>
                        ${booking.guest_phone ? `
                        <div class="booking-info-item">
                            <label>Telefono</label>
                            <div class="booking-info-value">
                                ${booking.guest_phone}
                                <a href="tel:${booking.guest_phone}" class="booking-link">Chiama →</a>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
                ${booking.special_requests ? `
                <div class="booking-card">
                    <h4 class="booking-card-title">Richieste Speciali</h4>
                    <div class="booking-special-requests">${booking.special_requests}</div>
                </div>
                ` : ''}
            </div>

            <!-- Tab Content: Accesso -->
            <div class="booking-tab-content" id="booking-tab-access">
                <div class="booking-card">
                    <h4 class="booking-card-title">Codice Check-in</h4>
                    <form id="booking-checkin-form" onsubmit="saveBookingCheckInCode(event, ${booking.id})">
                        <div class="booking-card-grid">
                            <div class="booking-info-item">
                                <label for="booking-checkin-code">Codice Check-in</label>
                                <div class="booking-checkin-code-container">
                                    <input type="text" 
                                           id="booking-checkin-code" 
                                           class="form-control" 
                                           maxlength="10"
                                           placeholder="Inserisci o genera il codice check-in"
                                           value="${booking.check_in_code || ''}">
                                    ${booking.check_in_code ? `
                                    <button type="button" class="btn btn-secondary btn-sm" onclick="copyToClipboard('${booking.check_in_code}')">Copia</button>
                                    ` : ''}
                                    <button type="button" class="btn btn-secondary btn-sm" onclick="generateCheckInCode(${booking.id})">Genera</button>
                                </div>
                                <small class="form-text">Codice di accesso per l'ospite</small>
                            </div>
                        </div>
                        <div class="booking-form-actions" style="margin-top: 16px;">
                            <button type="submit" class="btn btn-primary">Salva Codice Check-in</button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Tab Content: Pagamenti -->
            <div class="booking-tab-content" id="booking-tab-payments">
                <div class="booking-card">
                    <h4 class="booking-card-title">Storico Pagamenti</h4>
                    ${booking.payments && booking.payments.length > 0 ? `
                    <div class="booking-payments-list">
                        ${booking.payments.map(payment => `
                        <div class="booking-payment-item">
                            <div class="booking-payment-info">
                                <div class="booking-payment-type">${payment.payment_type_display || payment.payment_type || 'Pagamento'}</div>
                                <div class="booking-payment-date">${formatDateTime(payment.payment_date)}</div>
                                ${payment.transaction_id ? `<div class="booking-payment-transaction">ID: ${payment.transaction_id}</div>` : ''}
                                ${payment.notes ? `<div class="booking-payment-notes" style="font-size: 12px; color: #6c757d; margin-top: 4px;">${payment.notes}</div>` : ''}
                            </div>
                            <div class="booking-payment-amount">€${parseFloat(payment.amount).toFixed(2)}</div>
                        </div>
                        `).join('')}
                    </div>
                    ` : `
                    <div class="booking-empty-state">Nessun pagamento registrato</div>
                    `}
                </div>
            </div>

            <!-- Tab Content: Messaggi -->
            <div class="booking-tab-content" id="booking-tab-messages">
                <div class="booking-card">
                    <h4 class="booking-card-title">Conversazione</h4>
                    ${booking.messages && booking.messages.length > 0 ? `
                    <div class="booking-messages-list" id="booking-messages-list">
                        ${booking.messages.map(msg => {
                            // Determina se il messaggio è dell'ospite confrontando gli ID
                            const isGuest = booking.guest && (msg.sender === booking.guest || msg.sender === booking.guest.id || (typeof msg.sender === 'object' && msg.sender.id === booking.guest));
                            return `
                        <div class="booking-message-item ${isGuest ? 'booking-message-guest' : 'booking-message-host'}" data-message-id="${msg.id}">
                            <div class="booking-message-header">
                                <span class="booking-message-sender">${msg.sender_name || 'Utente'}</span>
                                <span class="booking-message-date">${formatDateTime(msg.created_at)}</span>
                                ${msg.is_read ? '<span class="booking-message-read" style="font-size: 11px; color: #28a745;">✓ Letto</span>' : ''}
                            </div>
                            <div class="booking-message-content">${msg.message || ''}</div>
                        </div>
                        `;
                        }).join('')}
                    </div>
                    ` : `
                    <div class="booking-empty-state" id="booking-messages-empty">Nessun messaggio</div>
                    `}
                </div>
                
                <div class="booking-card">
                    <h4 class="booking-card-title">Invia Messaggio</h4>
                    <form id="booking-message-form" onsubmit="sendBookingMessage(event, ${booking.id})">
                        <div class="form-group">
                            <label for="booking-message-text">Messaggio</label>
                            <textarea id="booking-message-text" 
                                      class="form-control" 
                                      rows="4" 
                                      placeholder="Scrivi un messaggio all'ospite..."
                                      required></textarea>
                            <small class="form-text">Il messaggio verrà inviato all'ospite della prenotazione</small>
                        </div>
                        <div class="booking-form-actions">
                            <button type="submit" class="btn btn-primary">Invia Messaggio</button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Tab Content: Note -->
            <div class="booking-tab-content" id="booking-tab-notes">
                <div class="booking-card">
                    <h4 class="booking-card-title">Note Host</h4>
                    <textarea id="booking-host-notes" class="form-control" rows="5" placeholder="Aggiungi note interne per questa prenotazione...">${booking.host_notes || ''}</textarea>
                </div>
                ${booking.change_requested ? `
                <div class="booking-card booking-card-warning">
                    <h4 class="booking-card-title">Richiesta di Modifica</h4>
                    <div class="booking-change-request">
                        <div class="booking-change-request-date">
                            Richiesta il ${formatDateTime(booking.change_request_created_at)}
                        </div>
                        ${booking.change_request_note ? `
                        <div class="booking-change-request-note">
                            <strong>Note:</strong> ${booking.change_request_note}
                        </div>
                        ` : ''}
                    </div>
                </div>
                ` : ''}
            </div>

            <!-- Actions Footer -->
            <div class="booking-detail-actions">
                <button type="button" class="btn btn-secondary" onclick="closeBookingModal()">Chiudi</button>
                <button type="button" class="btn btn-primary" onclick="updateBooking(${booking.id})">Salva Modifiche</button>
            </div>
        </div>
    `;
}

function switchBookingTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.booking-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.booking-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`booking-tab-${tabName}`).classList.add('active');
    document.querySelector(`.booking-tab[data-tab="${tabName}"]`).classList.add('active');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showMessage('Copiato negli appunti!', 'success');
    }).catch(() => {
        showMessage('Errore nella copia', 'error');
    });
}

async function saveBookingCheckInCode(event, bookingId) {
    event.preventDefault();
    
    const checkInCode = document.getElementById('booking-checkin-code').value.trim();
    
    if (!checkInCode) {
        showMessage('Inserisci un codice check-in', 'error');
        return;
    }
    
    showLoading(true);
    try {
        // Carica i dati attuali della prenotazione
        const currentBooking = await apiRequest(`bookings/${bookingId}/`);
        
        // Prepara i dati per l'aggiornamento
        const data = {
            ...currentBooking,
            check_in_code: checkInCode
        };
        
        await apiRequest(`bookings/${bookingId}/`, 'PATCH', data);
        showMessage('Codice check-in salvato con successo', 'success');
        
        // Ricarica i dettagli della prenotazione per aggiornare la vista
        const updatedBooking = await apiRequest(`bookings/${bookingId}/`);
        renderBookingDetail(updatedBooking);
        
        // Torna alla tab Accesso per vedere le modifiche
        switchBookingTab('access');
    } catch (error) {
        console.error('Error saving check-in code:', error);
        showMessage('Errore nel salvataggio del codice check-in', 'error');
    } finally {
        showLoading(false);
    }
}

async function generateCheckInCode(bookingId) {
    // Genera un codice a 6 cifre casuale
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    
    // Inserisci il codice nel campo input
    const checkInCodeInput = document.getElementById('booking-checkin-code');
    if (checkInCodeInput) {
        checkInCodeInput.value = code;
        showMessage('Codice generato. Ricorda di salvare!', 'success');
    }
}

async function sendBookingMessage(event, bookingId) {
    event.preventDefault();
    
    const messageText = document.getElementById('booking-message-text').value.trim();
    
    if (!messageText) {
        showMessage('Inserisci un messaggio', 'error');
        return;
    }
    
    showLoading(true);
    try {
        // Carica i dati della prenotazione per ottenere il guest
        const booking = await apiRequest(`bookings/${bookingId}/`);
        
        // Crea il messaggio
        const messageData = {
            booking: bookingId,
            message: messageText,
            recipient: booking.guest
        };
        
        const newMessage = await apiRequest('messages/', 'POST', messageData);
        showMessage('Messaggio inviato con successo', 'success');
        
        // Pulisci il form
        document.getElementById('booking-message-text').value = '';
        
        // Ricarica i dettagli della prenotazione per mostrare il nuovo messaggio
        const updatedBooking = await apiRequest(`bookings/${bookingId}/`);
        renderBookingDetail(updatedBooking);
        
        // Scrolla alla fine della lista messaggi
        const messagesList = document.getElementById('booking-messages-list');
        if (messagesList) {
            messagesList.scrollTop = messagesList.scrollHeight;
        }
    } catch (error) {
        console.error('Error sending message:', error);
        showMessage('Errore nell\'invio del messaggio', 'error');
    } finally {
        showLoading(false);
    }
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
    const totalAmountInput = document.getElementById('booking-total-amount');
    const totalAmount = totalAmountInput ? parseFloat(totalAmountInput.value) : null;
    
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
    
    // Include total_amount if it was modified
    if (totalAmount !== null && !isNaN(totalAmount) && totalAmount !== parseFloat(currentBooking.total_amount)) {
        data.total_amount = totalAmount.toFixed(2);
    }
    
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
        const requestSeq = ++loadListingsForSelectSeq;
        const data = await apiRequest('listings/');
        const listingsData = data.results || data;
        const select = document.getElementById(selectId);
        if (!select) return;

        // If another call started after this one, ignore this result (prevents duplicate appends on races)
        select.dataset.loadSeq = String(requestSeq);
        if (select.dataset.loadSeq !== String(requestSeq)) {
            return;
        }
        
        // Build options in memory, then replace to avoid duplicates.
        const frag = document.createDocumentFragment();

        const needsPlaceholder =
            selectId === 'calendar-listing' ||
            selectId === 'price-listing-select' ||
            selectId === 'booking-listing-select';

        if (needsPlaceholder) {
            const ph = document.createElement('option');
            ph.value = '';
            ph.textContent = selectId === 'calendar-listing' ? 'Seleziona annuncio...' :
                (selectId === 'price-listing-select' ? 'Vista globale (tutti gli appartamenti)' : 'Tutti gli annunci');
            frag.appendChild(ph);
        }

        const seen = new Set();
        for (const listing of listingsData) {
            const id = String(listing.id);
            if (seen.has(id)) continue;
            seen.add(id);
            const option = document.createElement('option');
            option.value = listing.id;
            option.textContent = listing.title;
            frag.appendChild(option);
        }

        // Replace children atomically
        select.replaceChildren(frag);
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
    
    // Also refresh global calendar if active
    if (globalCalendarWidget) {
        await globalCalendarWidget.loadCalendarData();
    }
}

// Global Calendar Widget - shows all listings together
class GlobalCalendarWidget {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentDate = new Date();
        this.selectedDates = [];
        this.calendarData = {}; // { dateKey: { listings: [{listingId, listing, price, booking}], ... } }
        this.listings = [];
        this.allBookings = [];
        this.allPriceRules = [];
        this.allClosureRules = []; // Per prenotazioni ICAL
        this.listingColors = {};
        
        this.init();
    }
    
    init() {
        this.render();
        this.loadCalendarData();
    }
    
    async loadCalendarData() {
        try {
            // Load all listings
            const listingsResponse = await fetch('/admin-panel/api/listings/', {
                credentials: 'include'
            });
            if (!listingsResponse.ok) {
                throw new Error(`HTTP error! status: ${listingsResponse.status}`);
            }
            const listingsData = await listingsResponse.json();
            this.listings = Array.isArray(listingsData.results) ? listingsData.results : 
                          (Array.isArray(listingsData) ? listingsData : []);
            
            if (this.listings.length === 0) {
                console.warn('No listings found for global calendar');
                this.render();
                return;
            }
            
            // Load saved colors from localStorage or assign defaults
            const savedColors = this.loadSavedColors();
            const defaultColors = ['#FF5A5F', '#00A699', '#FC642D', '#484848', '#767676'];
            this.listings.forEach((listing, idx) => {
                if (listing && listing.id) {
                    // Use saved color if available, otherwise use default
                    this.listingColors[listing.id] = savedColors[listing.id] || defaultColors[idx % defaultColors.length];
                }
            });
            
            // Load all price rules
            const priceRulesResponse = await fetch('/admin-panel/api/price-rules/', {
                credentials: 'include'
            });
            if (priceRulesResponse.ok) {
                const priceRulesData = await priceRulesResponse.json();
                this.allPriceRules = Array.isArray(priceRulesData.results) ? priceRulesData.results : 
                                   (Array.isArray(priceRulesData) ? priceRulesData : []);
            } else {
                console.warn('Failed to load price rules');
                this.allPriceRules = [];
            }
            
            // Load all bookings
            const bookingsResponse = await fetch('/admin-panel/api/bookings/', {
                credentials: 'include'
            });
            if (bookingsResponse.ok) {
                const bookingsData = await bookingsResponse.json();
                this.allBookings = Array.isArray(bookingsData.results) ? bookingsData.results : 
                                 (Array.isArray(bookingsData) ? bookingsData : []);
            } else {
                console.warn('Failed to load bookings');
                this.allBookings = [];
            }
            
            // Load all closure rules (for ICAL bookings)
            const closureResponse = await fetch('/admin-panel/api/closure-rules/', {
                credentials: 'include'
            });
            if (closureResponse.ok) {
                const closureData = await closureResponse.json();
                const closures = Array.isArray(closureData.results) ? closureData.results : 
                               (Array.isArray(closureData) ? closureData : []);
                // Filtra solo quelle esterne (ICAL)
                this.allClosureRules = closures.filter(c => c.is_external_booking === true);
            } else {
                console.warn('Failed to load closure rules');
                this.allClosureRules = [];
            }
            
            // Build calendar data
            const startDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
            const endDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 2, 0);
            this.buildCalendarData(startDate, endDate);
            
            // Render legend
            this.renderLegend();
            
            this.render();
        } catch (error) {
            console.error('Error loading global calendar data:', error);
            showMessage('Errore nel caricamento dei dati del calendario globale: ' + error.message, 'error');
            // Render empty calendar to prevent further errors
            this.listings = [];
            this.allPriceRules = [];
            this.allBookings = [];
            this.calendarData = {};
            this.render();
        }
    }
    
    buildCalendarData(startDate, endDate) {
        this.calendarData = {};
        const current = new Date(startDate);
        current.setHours(0, 0, 0, 0);
        
        const end = new Date(endDate);
        end.setHours(23, 59, 59, 999);
        
        while (current <= end) {
            const dateKey = this.formatDateKey(current);
            const dayListings = [];
            
            this.listings.forEach(listing => {
                const price = this.getPriceForDate(current, listing);
                const booking = this.getBookingForDate(current, listing.id);
                const externalBooking = this.getExternalBookingForDate(current, listing.id);
                
                dayListings.push({
                    listingId: listing.id,
                    listing: listing,
                    price: price,
                    booking: booking,
                    externalBooking: externalBooking,
                    isBlocked: booking !== null || externalBooking !== null
                });
            });
            
            this.calendarData[dateKey] = {
                date: new Date(current),
                listings: dayListings
            };
            
            current.setDate(current.getDate() + 1);
        }
    }
    
    getPriceForDate(date, listing) {
        if (!listing || !listing.id) return null;
        
        const dateStr = this.formatDateKey(date);
        const listingRules = this.allPriceRules.filter(r => r.listing === listing.id);
        
        // Sort rules by start_date descending
        const sortedRules = [...listingRules].sort((a, b) => {
            const dateA = typeof a.start_date === 'string' ? a.start_date.split('T')[0] : this.formatDateKey(new Date(a.start_date));
            const dateB = typeof b.start_date === 'string' ? b.start_date.split('T')[0] : this.formatDateKey(new Date(b.start_date));
            return dateB.localeCompare(dateA);
        });
        
        // Check if there's a price rule for this date
        for (const rule of sortedRules) {
            if (!rule.start_date || !rule.end_date || !rule.price) continue;
            
            let ruleStartStr = typeof rule.start_date === 'string' 
                ? (rule.start_date.includes('T') ? rule.start_date.split('T')[0] : rule.start_date)
                : this.formatDateKey(new Date(rule.start_date));
            let ruleEndStr = typeof rule.end_date === 'string'
                ? (rule.end_date.includes('T') ? rule.end_date.split('T')[0] : rule.end_date)
                : this.formatDateKey(new Date(rule.end_date));
            
            if (dateStr >= ruleStartStr && dateStr <= ruleEndStr) {
                const price = parseFloat(rule.price);
                return isNaN(price) ? null : price;
            }
        }
        
        // Return base price if available
        if (listing.base_price !== null && listing.base_price !== undefined) {
            const basePrice = parseFloat(listing.base_price);
            return isNaN(basePrice) ? null : basePrice;
        }
        
        return null;
    }
    
    getBookingForDate(date, listingId) {
        const dateStr = this.formatDateKey(date);
        
        for (const booking of this.allBookings) {
            if (booking.listing !== listingId || booking.status === 'cancelled') continue;
            
            const checkInStr = this.normalizeDateString(booking.check_in_date);
            const checkOutStr = this.normalizeDateString(booking.check_out_date);
            
            if (dateStr >= checkInStr && dateStr < checkOutStr) {
                return booking;
            }
        }
        
        return null;
    }
    
    getExternalBookingForDate(date, listingId) {
        const dateStr = this.formatDateKey(date);
        
        for (const closure of this.allClosureRules) {
            if (closure.listing !== listingId || !closure.start_date || !closure.end_date) continue;
            
            const startStr = this.normalizeDateString(closure.start_date);
            const endStr = this.normalizeDateString(closure.end_date);
            
            // Check if date is within closure range (end_date is exclusive in ICAL)
            if (dateStr >= startStr && dateStr < endStr) {
                return closure;
            }
        }
        
        return null;
    }
    
    extractProviderFromReason(reason) {
        if (!reason) return 'OTA';
        // Reason format: "[NomeCalendario] Sincronizzato da Provider"
        const match = reason.match(/Sincronizzato da\s+(\w+)/i);
        if (match) {
            const provider = match[1].toLowerCase();
            const providerNames = {
                'airbnb': 'Airbnb',
                'booking': 'Booking.com',
                'expedia': 'Expedia',
                'other': 'Altro'
            };
            return providerNames[provider] || match[1];
        }
        return 'OTA';
    }
    
    normalizeDateString(value) {
        if (!value) return '';
        if (typeof value === 'string') {
            return value.includes('T') ? value.split('T')[0] : value;
        }
        return this.formatDateKey(new Date(value));
    }
    
    formatDateKey(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }
    
    parseDateKey(dateKey) {
        if (!dateKey) return null;
        const d = (typeof dateKey === 'string' && dateKey.includes('T')) ? dateKey.split('T')[0] : dateKey;
        const [y, m, day] = String(d).split('-').map(n => parseInt(n, 10));
        if (!y || !m || !day) return null;
        const dt = new Date(y, m - 1, day);
        dt.setHours(0, 0, 0, 0);
        return dt;
    }
    
    formatDateDisplay(date) {
        return date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' });
    }
    
    loadSavedColors() {
        try {
            const saved = localStorage.getItem('globalCalendarColors');
            return saved ? JSON.parse(saved) : {};
        } catch (error) {
            console.error('Error loading saved colors:', error);
            return {};
        }
    }
    
    saveColors() {
        try {
            localStorage.setItem('globalCalendarColors', JSON.stringify(this.listingColors));
        } catch (error) {
            console.error('Error saving colors:', error);
        }
    }
    
    changeListingColor(listingId, newColor) {
        this.listingColors[listingId] = newColor;
        this.saveColors();
        this.renderLegend();
        this.render(); // Re-render calendar with new colors
    }
    
    renderLegend() {
        const legendContainer = document.getElementById('global-calendar-legend');
        if (!legendContainer) return;
        
        legendContainer.innerHTML = this.listings.map(listing => {
            const color = this.listingColors[listing.id] || '#999';
            return `
                <div style="display: flex; align-items: center; gap: 8px; padding: 8px; border-radius: 4px; transition: background 0.2s;" 
                     onmouseover="this.style.background='#f0f0f0'" 
                     onmouseout="this.style.background='transparent'">
                    <div style="position: relative;">
                        <div style="width: 24px; height: 24px; background: ${color}; border-radius: 4px; cursor: pointer; border: 2px solid #ddd;" 
                             onclick="globalCalendarWidget.openColorPicker(${listing.id}, '${color}')"
                             title="Clicca per cambiare colore"></div>
                    </div>
                    <span style="font-weight: 500;">${listing.title}</span>
                </div>
            `;
        }).join('');
    }
    
    openColorPicker(listingId, currentColor) {
        // Create a simple color picker modal
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;
        
        const listing = this.listings.find(l => l.id === listingId);
        const listingName = listing ? listing.title : 'Appartamento';
        
        const colorPicker = document.createElement('div');
        colorPicker.style.cssText = `
            background: white;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            max-width: 400px;
            width: 90%;
        `;
        
        // Predefined color palette
        const colorPalette = [
            '#FF5A5F', '#00A699', '#FC642D', '#484848', '#767676',
            '#FF385C', '#008489', '#FFB400', '#00D1C1', '#007A87',
            '#E31C5F', '#1DB954', '#FF6B6B', '#4ECDC4', '#45B7D1',
            '#96CEB4', '#FFEAA7', '#DDA15E', '#BC6C25', '#606C38',
            '#283618', '#F77F00', '#FCBF49', '#EAE2B7', '#D62828'
        ];
        
        let html = `
            <h3 style="margin: 0 0 16px 0; font-size: 18px;">Seleziona colore per ${listingName}</h3>
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 16px;">
        `;
        
        colorPalette.forEach(color => {
            const isSelected = color === currentColor;
            html += `
                <div style="
                    width: 40px;
                    height: 40px;
                    background: ${color};
                    border-radius: 4px;
                    cursor: pointer;
                    border: ${isSelected ? '3px solid #333' : '2px solid #ddd'};
                    transition: transform 0.2s;
                " 
                onclick="globalCalendarWidget.selectColor(${listingId}, '${color}')"
                onmouseover="this.style.transform='scale(1.1)'"
                onmouseout="this.style.transform='scale(1)'"
                title="${color}"></div>
            `;
        });
        
        html += `
            </div>
            <div style="margin-bottom: 16px;">
                <label style="display: block; margin-bottom: 8px; font-weight: 500;">Colore personalizzato:</label>
                <input type="color" 
                       id="custom-color-picker-${listingId}" 
                       value="${currentColor}" 
                       style="width: 100%; height: 40px; border-radius: 4px; border: 2px solid #ddd; cursor: pointer;"
                       onchange="globalCalendarWidget.selectColor(${listingId}, this.value)">
            </div>
            <div style="display: flex; gap: 8px; justify-content: flex-end;">
                <button onclick="this.closest('[style*=\"position: fixed\"]').remove()" 
                        style="padding: 8px 16px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer;">
                    Annulla
                </button>
            </div>
        `;
        
        colorPicker.innerHTML = html;
        modal.appendChild(colorPicker);
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        document.body.appendChild(modal);
    }
    
    selectColor(listingId, color) {
        this.changeListingColor(listingId, color);
        // Close color picker modal
        const modal = document.querySelector('[style*="position: fixed"][style*="z-index: 10000"]');
        if (modal) {
            modal.remove();
        }
    }
    
    render() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());
        
        let html = `
            <div class="calendar-widget">
                <div class="calendar-header">
                    <button class="calendar-nav-btn" onclick="globalCalendarWidget.prevMonth()">‹</button>
                    <h3>${this.currentDate.toLocaleDateString('it-IT', { month: 'long', year: 'numeric' })}</h3>
                    <button class="calendar-nav-btn" onclick="globalCalendarWidget.nextMonth()">›</button>
                </div>
                
                <div class="calendar-weekdays">
                    <div class="calendar-weekday">Dom</div>
                    <div class="calendar-weekday">Lun</div>
                    <div class="calendar-weekday">Mar</div>
                    <div class="calendar-weekday">Mer</div>
                    <div class="calendar-weekday">Gio</div>
                    <div class="calendar-weekday">Ven</div>
                    <div class="calendar-weekday">Sab</div>
                </div>
                
                <div class="calendar-grid">
        `;
        
        const current = new Date(startDate);
        const endRender = new Date(lastDay);
        endRender.setDate(endRender.getDate() + (6 - lastDay.getDay()));
        
        while (current <= endRender) {
            const dateKey = this.formatDateKey(current);
            const dayData = this.calendarData[dateKey] || { date: new Date(current), listings: [] };
            
            const isCurrentMonth = current.getMonth() === month;
            const isSelected = this.selectedDates.includes(dateKey);
            const isToday = this.formatDateKey(new Date()) === dateKey;
            const isPast = current < new Date(new Date().setHours(0, 0, 0, 0));
            
            // Ensure listings is an array
            const dayListings = Array.isArray(dayData.listings) ? dayData.listings : [];
            
            // Count bookings and blocked listings
            const blockedCount = dayListings.filter(l => l && l.isBlocked).length;
            const hasBookings = blockedCount > 0;
            const hasExternalBookings = dayListings.some(l => l && l.externalBooking);
            
            // Get price range
            const prices = dayListings.map(l => l && l.price !== null && l.price !== undefined ? l.price : null)
                .filter(p => p !== null && !isNaN(p));
            const minPrice = prices.length > 0 ? Math.min(...prices) : null;
            const maxPrice = prices.length > 0 ? Math.max(...prices) : null;
            const priceDisplay = minPrice !== null && maxPrice !== null
                ? (minPrice === maxPrice 
                    ? `€${minPrice.toFixed(0)}` 
                    : `€${minPrice.toFixed(0)}-${maxPrice.toFixed(0)}`)
                : '';
            
            // Build tooltip
            const tooltipParts = [];
            dayListings.forEach(l => {
                if (!l || !l.listing) return;
                if (l.externalBooking) {
                    const provider = this.extractProviderFromReason(l.externalBooking.reason);
                    tooltipParts.push(`${l.listing.title}: Prenotazione ${provider} (ICAL)`);
                } else if (l.booking) {
                    tooltipParts.push(`${l.listing.title}: Prenotato`);
                } else if (l.price !== null && l.price !== undefined && !isNaN(l.price)) {
                    tooltipParts.push(`${l.listing.title}: €${l.price.toFixed(2)}`);
                } else {
                    tooltipParts.push(`${l.listing.title}: Prezzo non disponibile`);
                }
            });
            const tooltip = tooltipParts.length > 0 ? tooltipParts.join('\n') : 'Nessun dato disponibile';
            
            html += `
                <div class="calendar-day ${!isCurrentMonth ? 'other-month' : ''} ${isSelected ? 'selected' : ''} ${isToday ? 'today' : ''} ${isPast ? 'past' : ''} ${hasBookings ? 'blocked' : ''} ${hasExternalBookings ? 'external-booking' : ''}"
                     data-date="${dateKey}"
                     onclick="globalCalendarWidget.toggleDate('${dateKey}', event)"
                     title="${tooltip}">
                    <div class="day-number">${current.getDate()}</div>
                    ${minPrice !== null ? `<div class="day-price">${priceDisplay}</div>` : ''}
                    ${hasExternalBookings ? `
                        <div class="day-external-booking" style="position: absolute; top: 4px; right: 4px;">
                            <span class="external-booking-icon">📅</span>
                        </div>
                    ` : ''}
                    ${hasBookings ? `
                        <div class="day-booking" style="display: flex; gap: 2px; flex-wrap: wrap;">
                            ${dayListings.filter(l => l && l.isBlocked).map(l => {
                                const title = l.externalBooking 
                                    ? `${l.listing ? l.listing.title : 'Sconosciuto'}: ${this.extractProviderFromReason(l.externalBooking.reason)} (ICAL)`
                                    : `${l.listing ? l.listing.title : 'Sconosciuto'}: ${l.booking && (l.booking.guest_name || l.booking.guest_email) || 'Prenotato'}`;
                                return `<div style="width: 8px; height: 8px; background: ${this.listingColors[l.listingId] || '#999'}; border-radius: 50%;" 
                                     title="${title}"></div>`;
                            }).join('')}
                        </div>
                    ` : ''}
                    ${!hasBookings && dayListings.length > 0 ? `
                        <div style="display: flex; gap: 2px; margin-top: 2px; flex-wrap: wrap;">
                            ${dayListings.slice(0, 3).filter(l => l && l.listing).map(l => `
                                <div style="width: 6px; height: 6px; background: ${this.listingColors[l.listingId] || '#999'}; border-radius: 50%;" 
                                     title="${l.listing.title}"></div>
                            `).join('')}
                            ${dayListings.length > 3 ? `<div style="font-size: 8px;">+${dayListings.length - 3}</div>` : ''}
                        </div>
                    ` : ''}
                </div>
            `;
            
            current.setDate(current.getDate() + 1);
        }
        
        html += `
                </div>
                
                ${this.selectedDates.length > 0 ? `
                    <div class="calendar-selection-bar">
                        <div class="selection-info">
                            <span>${this.selectedDates.length} giorno/i selezionato/i</span>
                            <span class="selection-dates">${this.getSelectedDatesRange()}</span>
                        </div>
                        <div class="selection-actions">
                            <button class="btn btn-secondary" onclick="globalCalendarWidget.clearSelection()">Annulla</button>
                            <button class="btn btn-primary" onclick="globalCalendarWidget.openPriceModal()">Crea Regola Prezzo</button>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    toggleDate(dateKey, event = null) {
        const date = this.parseDateKey(dateKey);
        if (!date) return;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (date < today) return;
        
        const index = this.selectedDates.indexOf(dateKey);
        if (index > -1) {
            this.selectedDates.splice(index, 1);
        } else {
            if (event && event.shiftKey && this.selectedDates.length > 0) {
                const lastSelected = this.parseDateKey(this.selectedDates[this.selectedDates.length - 1]);
                const current = this.parseDateKey(dateKey);
                if (!lastSelected || !current) return;
                
                const start = lastSelected < current ? lastSelected : current;
                const end = lastSelected < current ? current : lastSelected;
                
                const rangeDates = [];
                const temp = new Date(start);
                while (temp <= end) {
                    const key = this.formatDateKey(temp);
                    if (!this.selectedDates.includes(key)) {
                        rangeDates.push(key);
                    }
                    temp.setDate(temp.getDate() + 1);
                }
                
                this.selectedDates = [...this.selectedDates, ...rangeDates];
            } else {
                this.selectedDates.push(dateKey);
            }
            this.selectedDates.sort();
        }
        this.render();
    }
    
    clearSelection() {
        this.selectedDates = [];
        this.render();
    }
    
    getSelectedDatesRange() {
        if (this.selectedDates.length === 0) return '';
        if (this.selectedDates.length === 1) {
            return this.formatDateDisplay(this.parseDateKey(this.selectedDates[0]));
        }
        
        const start = this.parseDateKey(this.selectedDates[0]);
        const end = this.parseDateKey(this.selectedDates[this.selectedDates.length - 1]);
        
        return `${this.formatDateDisplay(start)} - ${this.formatDateDisplay(end)}`;
    }
    
    prevMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        this.selectedDates = [];
        this.loadCalendarData();
    }
    
    nextMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        this.selectedDates = [];
        this.loadCalendarData();
    }
    
    openPriceModal() {
        if (this.selectedDates.length === 0) return;
        
        const startDate = this.selectedDates[0];
        const endDate = this.selectedDates[this.selectedDates.length - 1];
        
        // Open price rule modal in global mode (no listingId)
        document.getElementById('price-rule-listing-id').value = '';
        document.getElementById('price-rule-start-date').value = startDate;
        document.getElementById('price-rule-end-date').value = endDate;
        document.getElementById('price-rule-id').value = '';
        
        // Calculate average price
        let totalPrice = 0;
        let count = 0;
        this.selectedDates.forEach(dateKey => {
            const dayData = this.calendarData[dateKey];
            if (dayData && Array.isArray(dayData.listings)) {
                dayData.listings.forEach(l => {
                    if (l && l.price !== null && l.price !== undefined && !isNaN(l.price)) {
                        totalPrice += l.price;
                        count++;
                    }
                });
            }
        });
        
        if (count > 0) {
            const avgPrice = totalPrice / count;
            document.getElementById('price-rule-price').value = avgPrice.toFixed(2);
        }
        
        // Show multi-select
        openPriceRuleModal(null);
        this.selectedDates = [];
        this.render();
    }
}

// Initialize global calendar
function initGlobalCalendar() {
    const container = document.getElementById('global-calendar-container');
    const widgetContainer = document.getElementById('global-calendar-widget');
    
    if (!container || !widgetContainer) {
        console.error('Global calendar containers not found');
        return;
    }
    
    container.style.display = 'block';
    
    // Destroy existing widget if any
    if (globalCalendarWidget) {
        globalCalendarWidget = null;
    }
    
    try {
        // Create new widget
        globalCalendarWidget = new GlobalCalendarWidget('global-calendar-widget');
    } catch (error) {
        console.error('Error initializing global calendar widget:', error);
        showMessage('Errore nell\'inizializzazione del calendario globale: ' + error.message, 'error');
    }
}
