/**
 * Combined Search - Sistema di ricerca combinata appartamenti
 * Usa BookingCalendar in modalità combinata per mostrare disponibilità aggregata
 * Version: 2.4 - Fixed booking combination parameter + gap rules
 */

console.log('Combined Search v2.4 loaded - booking combination fix + gap rules');

document.addEventListener('DOMContentLoaded', function() {
    let combinedCalendar = null;
    const calendarTrigger = document.getElementById('combined-calendar-trigger');
    const calendarWrapper = document.getElementById('combined-calendar-wrapper');
    const calendarDisplay = document.getElementById('combined-calendar-display');
    const searchForm = document.getElementById('combinedSearchForm');
    const searchButton = document.getElementById('searchButton');
    const searchResults = document.getElementById('searchResults');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const combinationsList = document.getElementById('combinationsList');

    // Toggle calendario
    calendarTrigger.addEventListener('click', function(e) {
        e.stopPropagation();
        if (calendarWrapper.classList.contains('hidden')) {
            calendarWrapper.classList.remove('hidden');
            if (!combinedCalendar) {
                initCombinedCalendar();
            }
        } else {
            calendarWrapper.classList.add('hidden');
        }
    });

    // Chiudi calendario con ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !calendarWrapper.classList.contains('hidden')) {
            calendarWrapper.classList.add('hidden');
        }
    });

    // Inizializza calendario combinato
    function initCombinedCalendar() {
        combinedCalendar = new BookingCalendar({
            listingId: null, // Non serve per modalità combinata
            isCombined: true, // Abilita modalità combinata
            container: '#combined-booking-calendar',
            monthsToShow: 2,
            onDateSelect: function(selection) {
                if (selection && selection.checkIn && selection.checkOut) {
                    const checkIn = new Date(selection.checkIn);
                    const checkOut = new Date(selection.checkOut);

                    // Nascondi eventuali errori precedenti
                    document.getElementById('combined-availability-error').classList.add('hidden');

                    // Aggiorna display
                    calendarDisplay.textContent = `${formatDateDisplay(checkIn)} - ${formatDateDisplay(checkOut)}`;
                    calendarDisplay.classList.remove('text-gray-500');
                    calendarDisplay.classList.add('text-gray-900');

                    // Aggiorna hidden inputs
                    document.getElementById('check_in').value = selection.checkIn;
                    document.getElementById('check_out').value = selection.checkOut;

                    // Abilita pulsante cerca
                    searchButton.disabled = false;
                    searchButton.classList.remove('opacity-50', 'cursor-not-allowed');

                    // Chiudi calendario
                    calendarWrapper.classList.add('hidden');
                }
            },
            onError: function(errorMessage) {
                // Mostra errore sempre visibile
                const errorDiv = document.getElementById('combined-availability-error');
                const errorMessageEl = document.getElementById('combined-availability-error-message');
                errorMessageEl.textContent = errorMessage;
                errorDiv.classList.remove('hidden');

                // Disabilita pulsante cerca
                searchButton.disabled = true;
                searchButton.classList.add('opacity-50', 'cursor-not-allowed');
            }
        });
    }

    // Submit form - cerca combinazioni
    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const checkIn = document.getElementById('check_in').value;
        const checkOut = document.getElementById('check_out').value;
        const totalGuests = parseInt(document.getElementById('total_guests').value);

        if (!checkIn || !checkOut) {
            alert('Seleziona le date di check-in e check-out');
            return;
        }

        // Mostra loading
        loadingSpinner.classList.remove('hidden');
        searchResults.classList.add('hidden');
        searchButton.disabled = true;

        try {
            const response = await fetch('/prenotazioni/api/combined-availability/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    check_in: checkIn,
                    check_out: checkOut,
                    total_guests: totalGuests
                })
            });

            const data = await response.json();

            if (data.success && data.combinations && data.combinations.length > 0) {
                displayCombinations(data.combinations, checkIn, checkOut, totalGuests);
            } else {
                displayNoCombinations();
            }
        } catch (error) {
            console.error('Error searching combinations:', error);
            alert('Errore durante la ricerca. Riprova più tardi.');
        } finally {
            loadingSpinner.classList.add('hidden');
            searchButton.disabled = false;
        }
    });

    // Visualizza combinazioni
    function displayCombinations(combinations, checkIn, checkOut, totalGuests) {
        combinationsList.innerHTML = '';

        combinations.forEach((combo, index) => {
            const comboCard = createCombinationCard(combo, index + 1, checkIn, checkOut, totalGuests);
            combinationsList.appendChild(comboCard);
        });

        searchResults.classList.remove('hidden');
    }

    // Crea card combinazione
    function createCombinationCard(combo, optionNumber, checkIn, checkOut, totalGuests) {
        const card = document.createElement('div');
        card.className = 'bg-gray-50 rounded-lg border border-gray-200 p-4 mb-4 hover:border-blue-400 transition-colors';

        const nights = calculateNights(checkIn, checkOut);

        // Header opzione
        const header = document.createElement('div');
        header.className = 'flex justify-between items-start mb-3';
        header.innerHTML = `
            <div>
                <h5 class="font-semibold text-lg text-gray-900">Opzione ${optionNumber}</h5>
                <p class="text-sm text-gray-600">${combo.group_name || 'Combinazione appartamenti'}</p>
            </div>
            <div class="text-right">
                <div class="text-2xl font-bold text-gray-900">€${combo.total_price.toFixed(0)}</div>
                <div class="text-sm text-gray-600">${nights} ${nights === 1 ? 'notte' : 'notti'}</div>
            </div>
        `;
        card.appendChild(header);

        // Appartamenti nella combinazione
        const listingsDiv = document.createElement('div');
        listingsDiv.className = 'grid grid-cols-1 md:grid-cols-2 gap-3 mb-4';

        // L'API restituisce 'combination' con struttura nidificata
        const combination = combo.combination || combo.listings || [];
        combination.forEach(item => {
            // Ogni item ha { listing: {...}, guests: N, price: X, nights: N }
            const listing = item.listing || item;
            const listingCard = document.createElement('div');
            listingCard.className = 'bg-white rounded p-3 border border-gray-200';
            listingCard.innerHTML = `
                <div class="font-medium text-gray-900 mb-1">${listing.title}</div>
                <div class="text-sm text-gray-600 space-y-1">
                    <div><i class="fas fa-door-open mr-1"></i>${listing.bedrooms} ${listing.bedrooms === 1 ? 'camera' : 'camere'}</div>
                    <div><i class="fas fa-user-friends mr-1"></i>Fino a ${listing.max_guests} ospiti</div>
                    <div><i class="fas fa-users mr-1"></i>Ospiti assegnati: ${item.guests || 0}</div>
                    <div class="font-medium text-gray-900">€${listing.base_price} / notte</div>
                    <div class="text-sm text-blue-600">Prezzo totale: €${item.price ? item.price.toFixed(2) : '0.00'}</div>
                </div>
            `;
            listingsDiv.appendChild(listingCard);
        });
        card.appendChild(listingsDiv);

        // Breakdown prezzo
        const priceBreakdown = document.createElement('div');
        priceBreakdown.className = 'border-t border-gray-200 pt-3 space-y-2 text-sm mb-4';

        // Calcola subtotal (totale - pulizie)
        const totalPrice = combo.total_price || 0;
        const cleaningFee = combo.total_cleaning_fee || 0;
        const subtotal = totalPrice - cleaningFee;

        priceBreakdown.innerHTML = `
            <div class="flex justify-between">
                <span class="text-gray-600">Soggiorno (${nights} ${nights === 1 ? 'notte' : 'notti'})</span>
                <span class="text-gray-900">€${subtotal.toFixed(2)}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-600">Pulizie</span>
                <span class="text-gray-900">€${cleaningFee.toFixed(2)}</span>
            </div>
            <div class="flex justify-between font-semibold text-base border-t border-gray-200 pt-2">
                <span class="text-gray-900">Totale</span>
                <span class="text-gray-900">€${totalPrice.toFixed(2)}</span>
            </div>
        `;
        card.appendChild(priceBreakdown);

        // Bottone prenota
        const bookButton = document.createElement('button');
        bookButton.type = 'button';
        bookButton.className = 'w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center';
        bookButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Prenota questa combinazione
        `;
        bookButton.addEventListener('click', () => bookCombination(combo, checkIn, checkOut, totalGuests));
        card.appendChild(bookButton);

        return card;
    }

    // Visualizza "nessuna combinazione"
    function displayNoCombinations() {
        combinationsList.innerHTML = `
            <div class="text-center py-8">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 class="text-lg font-semibold text-gray-900 mb-2">Nessuna combinazione disponibile</h3>
                <p class="text-gray-600">Prova con date diverse o un numero di ospiti inferiore.</p>
            </div>
        `;
        searchResults.classList.remove('hidden');
    }

    // Prenota combinazione
    async function bookCombination(combo, checkIn, checkOut, totalGuests) {
        // Verifica autenticazione
        const isAuthenticated = document.body.dataset.userAuthenticated === 'true';

        if (!isAuthenticated) {
            alert('Devi essere autenticato per prenotare. Reindirizzamento al login...');
            window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
            return;
        }

        if (!confirm('Confermi la prenotazione di questa combinazione di appartamenti?')) {
            return;
        }

        try {
            const response = await fetch('/prenotazioni/api/combined-booking/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    group_id: combo.group_id,
                    check_in: checkIn,
                    check_out: checkOut,
                    total_guests: totalGuests,
                    combination: combo.combination
                })
            });

            const data = await response.json();

            if (data.success) {
                alert('Prenotazione combinata creata con successo!');
                window.location.href = '/accounts/dashboard/';
            } else {
                alert(data.error || 'Errore durante la prenotazione');
            }
        } catch (error) {
            console.error('Error booking combination:', error);
            alert('Errore di connessione. Riprova più tardi.');
        }
    }

    // Helper: formatta date per display
    function formatDateDisplay(date) {
        const options = { day: 'numeric', month: 'short', year: 'numeric' };
        return date.toLocaleDateString('it-IT', options);
    }

    // Helper: calcola notti
    function calculateNights(checkIn, checkOut) {
        const date1 = new Date(checkIn);
        const date2 = new Date(checkOut);
        const diffTime = date2 - date1;
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }

    // Helper: ottieni CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
