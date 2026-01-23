// Calendar Widget - Airbnb Style
class CalendarWidget {
    constructor(containerId, listingId) {
        this.container = document.getElementById(containerId);
        this.listingId = listingId;
        this.currentDate = new Date();
        this.selectedDates = [];
        this.calendarData = {};
        this.bookings = [];
        this.listing = null;
        this.priceRules = [];
        
        this.init();
    }
    
    init() {
        this.render();
        this.loadCalendarData();
        this.loadBookings();
    }
    
    async loadCalendarData() {
        const startDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
        const endDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 2, 0);
        
        try {
            // Load prices from price rules - force fresh data
            const priceRulesResponse = await fetch(`/admin-panel/api/price-rules/?listing_id=${this.listingId}&_t=${Date.now()}`, {
                credentials: 'include'
            });
            
            if (!priceRulesResponse.ok) {
                throw new Error(`HTTP error! status: ${priceRulesResponse.status}`);
            }
            
            const priceRules = await priceRulesResponse.json();
            const rules = priceRules.results || priceRules;
            
            // Debug: log rules to see what we're getting
            console.log('Loaded price rules:', rules);
            
            // Load base price from listing
            const listingResponse = await fetch(`/admin-panel/api/listings/${this.listingId}/?_t=${Date.now()}`, {
                credentials: 'include'
            });
            
            if (!listingResponse.ok) {
                throw new Error(`HTTP error! status: ${listingResponse.status}`);
            }
            
            const listing = await listingResponse.json();
            
            // Store for later use
            this.listing = listing;
            this.priceRules = rules;
            
            // Build calendar data
            this.buildCalendarData(startDate, endDate, listing, rules);
            this.render();
        } catch (error) {
            console.error('Error loading calendar data:', error);
            showMessage('Errore nel caricamento dei dati del calendario', 'error');
        }
    }
    
    async loadBookings() {
        try {
            const response = await fetch(`/admin-panel/api/bookings/?listing_id=${this.listingId}`);
            const data = await response.json();
            this.bookings = data.results || data;
            this.render();
        } catch (error) {
            console.error('Error loading bookings:', error);
        }
    }
    
    buildCalendarData(startDate, endDate, listing, rules) {
        this.calendarData = {};
        const current = new Date(startDate);
        current.setHours(0, 0, 0, 0);
        
        const end = new Date(endDate);
        end.setHours(23, 59, 59, 999);
        
        while (current <= end) {
            const dateKey = this.formatDateKey(current);
            const price = this.getPriceForDate(current, listing, rules);
            const booking = this.getBookingForDate(current);
            
            this.calendarData[dateKey] = {
                date: new Date(current),
                price: price,
                booking: booking,
                isBlocked: booking !== null
            };
            
            current.setDate(current.getDate() + 1);
        }
    }
    
    getPriceForDate(date, listing, rules) {
        // Normalize date to start of day (remove time component)
        const normalizedDate = new Date(date);
        normalizedDate.setHours(0, 0, 0, 0);
        
        // Convert date to YYYY-MM-DD string for comparison
        const dateStr = this.formatDateKey(normalizedDate);
        
        // Ensure rules is an array
        if (!Array.isArray(rules)) {
            rules = [];
        }
        
        // Sort rules by start_date descending to get the most recent/relevant rule first
        const sortedRules = [...rules].sort((a, b) => {
            // Handle both string and date formats
            let dateA = a.start_date;
            let dateB = b.start_date;
            
            if (typeof dateA === 'string') {
                dateA = dateA.split('T')[0];
            } else if (dateA) {
                dateA = new Date(dateA).toISOString().split('T')[0];
            }
            
            if (typeof dateB === 'string') {
                dateB = dateB.split('T')[0];
            } else if (dateB) {
                dateB = new Date(dateB).toISOString().split('T')[0];
            }
            
            return dateB.localeCompare(dateA); // Descending order (newest first)
        });
        
        // Check if there's a price rule for this date
        for (const rule of sortedRules) {
            if (!rule.start_date || !rule.end_date) continue;
            
            // Parse dates as strings to avoid timezone issues
            let ruleStartStr = rule.start_date;
            let ruleEndStr = rule.end_date;
            
            // Handle different date formats
            if (typeof ruleStartStr === 'string') {
                if (ruleStartStr.includes('T')) {
                    ruleStartStr = ruleStartStr.split('T')[0];
                }
            } else {
                ruleStartStr = new Date(ruleStartStr).toISOString().split('T')[0];
            }
            
            if (typeof ruleEndStr === 'string') {
                if (ruleEndStr.includes('T')) {
                    ruleEndStr = ruleEndStr.split('T')[0];
                }
            } else {
                ruleEndStr = new Date(ruleEndStr).toISOString().split('T')[0];
            }
            
            // Compare as strings (YYYY-MM-DD format)
            if (dateStr >= ruleStartStr && dateStr <= ruleEndStr) {
                const price = parseFloat(rule.price);
                // Debug for specific date
                if (dateStr === '2026-02-24') {
                    console.log('Price rule matched for 2026-02-24:', {
                        rule: rule,
                        ruleStart: ruleStartStr,
                        ruleEnd: ruleEndStr,
                        dateStr: dateStr,
                        price: price
                    });
                }
                return price;
            }
        }
        
        // Return base price
        const basePrice = parseFloat(listing.base_price);
        if (dateStr === '2026-02-24') {
            console.log('No price rule matched for 2026-02-24, using base price:', basePrice);
        }
        return basePrice;
    }
    
    getBookingForDate(date) {
        const dateStr = date.toISOString().split('T')[0];
        
        for (const booking of this.bookings) {
            const checkIn = new Date(booking.check_in_date);
            const checkOut = new Date(booking.check_out_date);
            
            if (date >= checkIn && date < checkOut && booking.status !== 'cancelled') {
                return booking;
            }
        }
        
        return null;
    }
    
    formatDateKey(date) {
        return date.toISOString().split('T')[0];
    }
    
    formatDateDisplay(date) {
        return date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' });
    }
    
    render() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay()); // Start from Sunday
        
        let html = `
            <div class="calendar-widget">
                <div class="calendar-header">
                    <button class="calendar-nav-btn" onclick="calendarWidget.prevMonth()">‹</button>
                    <h3>${this.currentDate.toLocaleDateString('it-IT', { month: 'long', year: 'numeric' })}</h3>
                    <button class="calendar-nav-btn" onclick="calendarWidget.nextMonth()">›</button>
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
            const dayData = this.calendarData[dateKey] || {
                date: new Date(current),
                price: null,
                booking: null,
                isBlocked: false
            };
            
            const isCurrentMonth = current.getMonth() === month;
            const isSelected = this.selectedDates.includes(dateKey);
            const isToday = this.formatDateKey(new Date()) === dateKey;
            const isPast = current < new Date(new Date().setHours(0, 0, 0, 0));
            
            // Check if date is in selected range
            let rangeClass = '';
            if (this.selectedDates.length > 1) {
                const firstSelected = new Date(this.selectedDates[0]);
                const lastSelected = new Date(this.selectedDates[this.selectedDates.length - 1]);
                
                if (isSelected && current.getTime() === firstSelected.getTime()) {
                    rangeClass = 'range-start';
                } else if (isSelected && current.getTime() === lastSelected.getTime()) {
                    rangeClass = 'range-end';
                } else if (isSelected && current > firstSelected && current < lastSelected) {
                    rangeClass = 'range-middle';
                }
            }
            
            html += `
                <div class="calendar-day ${!isCurrentMonth ? 'other-month' : ''} ${isSelected ? 'selected ' + rangeClass : ''} ${isToday ? 'today' : ''} ${isPast ? 'past' : ''} ${dayData.isBlocked ? 'blocked' : ''}"
                     data-date="${dateKey}"
                     onclick="calendarWidget.toggleDate('${dateKey}', event)"
                     title="${dayData.booking ? `Ospite: ${dayData.booking.guest_name || dayData.booking.guest_email}` : `Prezzo: €${dayData.price?.toFixed(2) || 'N/A'}`}">
                    <div class="day-number">${current.getDate()}</div>
                    ${dayData.price !== null ? `<div class="day-price">€${dayData.price.toFixed(0)}</div>` : ''}
                    ${dayData.booking ? `
                        <div class="day-booking" title="${dayData.booking.guest_name || dayData.booking.guest_email}">
                            ${dayData.booking.guest_name ? dayData.booking.guest_name.substring(0, 1).toUpperCase() : 'G'}
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
                            <button class="btn btn-secondary" onclick="calendarWidget.clearSelection()">Annulla</button>
                            <button class="btn btn-primary" onclick="calendarWidget.openPriceModal()">Modifica Prezzo</button>
                            <button class="btn btn-danger" onclick="calendarWidget.openClosureModal()">Chiudi Periodo</button>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    toggleDate(dateKey, event = null) {
        const date = new Date(dateKey);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        // Don't allow selection of past dates
        if (date < today) {
            return;
        }
        
        const index = this.selectedDates.indexOf(dateKey);
        if (index > -1) {
            this.selectedDates.splice(index, 1);
        } else {
            // If shift is pressed, select range
            if (event && event.shiftKey && this.selectedDates.length > 0) {
                const lastSelected = new Date(this.selectedDates[this.selectedDates.length - 1]);
                const current = new Date(dateKey);
                
                // Select all dates between last selected and current
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
            return this.formatDateDisplay(new Date(this.selectedDates[0]));
        }
        
        const start = new Date(this.selectedDates[0]);
        const end = new Date(this.selectedDates[this.selectedDates.length - 1]);
        
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
        
        // Open price rule modal with pre-filled dates
        document.getElementById('price-rule-listing-id').value = this.listingId;
        document.getElementById('price-rule-start-date').value = startDate;
        document.getElementById('price-rule-end-date').value = endDate;
        document.getElementById('price-rule-id').value = '';
        
        // Calculate average price for selected dates
        let totalPrice = 0;
        let count = 0;
        this.selectedDates.forEach(dateKey => {
            const dayData = this.calendarData[dateKey];
            if (dayData && dayData.price !== null) {
                totalPrice += dayData.price;
                count++;
            }
        });
        
        if (count > 0) {
            const avgPrice = totalPrice / count;
            document.getElementById('price-rule-price').value = avgPrice.toFixed(2);
        }
        
        document.getElementById('modal-price-rule').classList.add('active');
        this.selectedDates = [];
        this.render();
    }
    
    openClosureModal() {
        if (this.selectedDates.length === 0) return;
        
        const startDate = this.selectedDates[0];
        const endDate = this.selectedDates[this.selectedDates.length - 1];
        
        // Open closure modal with pre-filled dates
        document.getElementById('closure-listing-id').value = this.listingId;
        document.getElementById('closure-start-date').value = startDate;
        document.getElementById('closure-end-date').value = endDate;
        document.getElementById('closure-id').value = '';
        
        document.getElementById('modal-closure').classList.add('active');
        this.selectedDates = [];
        this.render();
    }
}

// Global instance
let calendarWidget = null;
