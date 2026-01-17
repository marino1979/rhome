# Copilot Instructions for Rhome Book

## Project Overview

**Rhome Book** is a Django 5.1 property management platform integrating Airbnb listings, reviews, single/multi-property bookings, availability calendars, and admin tools. The app manages complex availability logic, dynamic pricing, and combined multi-property reservations.

**Stack**: Python 3.14, Django 5.1, SQLite/PostgreSQL, Django REST Framework, Tailwind CSS, pyairbnb

---

## Architecture & Component Boundaries

### Core Django Apps (in `Rhome_book/`)

1. **`listings`** - Property catalog & Airbnb sync
   - `Listing` model: title, base_price, amenities, airbnb_listing_url, gap_between_bookings
   - `Review` model: Airbnb reviews with ratings, sync tracking (airbnb_review_id)
   - `ListingGroup` model: groups listings for multi-property bookings
   - **Service**: `listings.services.review_sync.AirbnbReviewSync` syncs reviews via `pyairbnb.get_reviews()`, updates existing records, stores category averages on Listing

2. **`bookings`** - Reservation orchestration
   - `Booking` model: single property reservation (check_in_date, check_out_date, guest, status, payment_status)
   - `MultiBooking` model: groups multiple Bookings for combined reservations
   - `BookingPayment` model: payment tracking
   - `Message` model: guest-host messaging
   - **Key Views**: `check_availability()`, `create_combined_booking()`, `create_booking()` (POST JSON APIs)

3. **`calendar_rules`** - Availability & pricing engine
   - **Managers**: `CalendarManager` (listingwise orchestrator, routes to CalendarService)
   - **Services** (`calendar_rules/services/`):
     - `CalendarService`: Main orchestrator for availability queries (get_unavailable_dates, get_prices)
     - `GapCalculator`: Gap day logic (days between bookings, defined per Listing)
     - `RangeConsolidator`: Merges overlapping blocked ranges
     - `QueryOptimizer`: Optimizes DB queries (select_related, only() to prevent N+1)
   - **Models**: `ClosureRule` (blackout periods), `CheckInOutRule` (min stay, turnover), `PriceRule` (dynamic pricing)

4. **`users`** - Account & profile management
   - Django built-in User model extended via forms
   - OAuth via django-allauth (Facebook, Google)

5. **Supporting apps**: `amenities`, `rooms`, `beds`, `images`, `icons`, `translations`, `calendar_rules/management/`

---

## Data Flow Patterns

### Availability Check Pipeline
```
POST /prenotazioni/api/check-availability/
  → bookings.views.check_availability()
    → CalendarManager(listing).get_unavailable_dates(start, end)
      → CalendarService.get_unavailable_dates()
        → GapCalculator + RangeConsolidator
        → Returns: blocked_ranges, gap_days, checkin_blocked, checkout_blocked
  → JSON response: {available: bool, unavailable_dates: [...]}
```

### Multi-Property Booking
```
POST /prenotazioni/api/combined-availability/
  → bookings.views.combined_availability()
    → Loop over each Listing in ListingGroup
      → Check availability with CalendarService
    → Return compatible date ranges
      
POST /prenotazioni/api/combined-booking/
  → bookings.views.create_combined_booking()
    → @transaction.atomic: Create MultiBooking + Booking per listing
    → Update blocking in calendar_rules
    → Response: MultiBooking ID
```

### Review Synchronization
```
Django Admin: Sync Airbnb Reviews
  → AirbnbReviewSync(listing, airbnb_url).sync_reviews()
    → pyairbnb.get_reviews(url, language, proxy_url)
    → Update/create Review records, save category averages to Listing.airbnb_rating_category_*
    → Returns: {synced, created, updated, skipped, errors}
```

---

## Critical Workflows & Commands

### Development Server
```bash
python manage.py runserver
# Runs on http://localhost:8000
# Settings loaded from .env (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
```

### Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata amenities  # If fixtures exist
```

### Testing
```bash
pytest bookings/tests.py -v  # Run tests
pytest --cov=bookings --cov=calendar_rules  # With coverage
# pytest.ini: DJANGO_SETTINGS_MODULE=Rhome_book.settings
```

### Debugging Calendar Issues
- Logs to `calendar_debug` logger (see `calendar_rules/services/calendar_service.py`)
- Enable: Add `'calendar_debug': {'level': 'DEBUG'}` to LOGGING in settings
- Common issues: gap_between_bookings not applied, overlap detection fails, turnover not blocking next checkin

### Review Sync Troubleshooting
- pyairbnb requires valid Airbnb listing URL in `Listing.airbnb_listing_url`
- Language: 'it' for Italian reviews
- Proxy URL optional for geo-restrictions
- Check `listings/services/review_sync.py` for error handling

---

## Key Conventions & Patterns

### Service Layer Architecture
- **Services live in `<app>/services/`** with custom exceptions in `exceptions.py`
- **CalendarService pattern**: Single entry point, internal methods prefixed `_` for private orchestration
  ```python
  # calendar_rules/services/calendar_service.py
  class CalendarService:
      def get_unavailable_dates(self, start_date, end_date) -> Dict:
          self._validate_date_range(start_date, end_date)
          calendar_data = self._get_optimized_calendar_data(start_date, end_date)
          blocked_ranges = self._calculate_blocked_ranges_only_bookings(...)
          return {...}
  ```
- **GapCalculator pattern**: Stateless utility, single responsibility
  ```python
  calculator = GapCalculator(gap_days=2)
  gaps = calculator.calculate_gap_days_after_checkout(checkout_date, start, end)
  ```

### Error Handling
- Custom exceptions: `CalendarServiceError`, `InvalidDateRangeError`, `GapCalculationError`, `AirbnbReviewSyncError`
- Raise early with descriptive messages, don't swallow exceptions
- Return structured error responses in JSON views: `{'error': 'message', 'code': 'ERROR_CODE'}`

### Transactions for Multi-Step Operations
```python
@transaction.atomic
def create_combined_booking(request):
    multi_booking = MultiBooking.objects.create(...)
    for listing in group.listings.all():
        Booking.objects.create(multi_booking=multi_booking, listing=listing, ...)
    # Atomically succeed or rollback
```

### Query Optimization
- Use `select_related()` for FK relationships: `Booking.objects.select_related('listing', 'guest')`
- Use `only()` to fetch specific fields: `Booking.objects.only('id', 'check_in_date', 'check_out_date')`
- Calendar queries group by Listing to prevent N+1: See `QueryOptimizer` in services

### API Endpoints
- **Location**: `<app>/urls.py` with `app_name` for URL reversal
- **Pattern**: POST for state-changing (create_booking, combined_booking), GET for reads
- **Response format**: JSON with `{data: {...}, error: null}` or `{error: 'message'}`
- **Date format**: ISO string '%Y-%m-%d'

### Internationalization (i18n)
- `django-modeltranslation` for model fields (see settings INSTALLED_APPS)
- Template strings: `{% trans "text" %}` or `_("text")` in Python
- Language middleware in place: locale from URL or browser

### Logging
- Use `logger = logging.getLogger(__name__)` per module
- Special logger `calendar_debug` for calendar troubleshooting
- Log INFO for major operations, DEBUG for data flow, WARNING for recoverable issues

---

## Important Files & Patterns to Reference

| File | Purpose | Key Patterns |
|------|---------|--------------|
| `Rhome_book/settings.py` | Django config, .env loading | INSTALLED_APPS order critical (modeltranslation before admin) |
| `MEMORY.md` | Project architecture doc | Read first for high-level design rationale |
| `calendar_rules/services/calendar_service.py` | Main availability engine | Orchestrator pattern, extensive logging for debugging |
| `listings/services/review_sync.py` | Airbnb sync logic | Transaction safety, rate limit handling in pyairbnb |
| `bookings/views.py` | Booking APIs | Multi-booking atomicity, JSON request parsing |
| `calendar_rules/managers.py` | Listing-specific calendar wrapper | Routes to CalendarService, caches results |

---

## Common Pitfalls & Solutions

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| "Booking not blocked after checkout" | Gap days not applied | Check `Listing.gap_between_bookings` is set; verify `GapCalculator` receives correct gap_days |
| "Availability check returns wrong dates" | Query not ordered, duplicates in ranges | Use `QueryOptimizer` to fetch once per date; call `RangeConsolidator` to merge overlaps |
| "Airbnb reviews not syncing" | Invalid listing URL or proxy issues | Verify `Listing.airbnb_listing_url`, check pyairbnb version matches |
| "Multi-property booking rolls back" | Transaction failure mid-booking | Ensure all Listing IDs exist, prices are valid, all bookings pass validation before @transaction.atomic block |
| "N+1 queries in availability check" | Services fetching bookings per date | Use `QueryOptimizer.optimize_query()` to batch fetch; see calendar_service debug logs |

---

## When to Ask for Clarification

- **Ambiguous multi-property logic**: Confirm which ListingGroups can combine and date overlap rules
- **Custom pricing rules**: Clarify precedence (PriceRule.priority vs base_price)
- **Timezone handling**: Check if stored dates are UTC or local (currently naive, no TZ-awareness)
- **Frontend integration**: Confirm date format/locale expected by frontend templates
