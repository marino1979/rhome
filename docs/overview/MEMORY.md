Obiettivo del progetto
=====================

Applicazione gestionale per Rhome Book che integra annunci immobiliari, recensioni sincronizzate da Airbnb, prenotazioni singole e combinate, oltre a strumenti di amministrazione per staff e proprietari. L’obiettivo è centralizzare sincronizzazione dati, disponibilità e flusso di prenotazione (frontend e backend).

Stack tecnologico
=================

- Python 3.14, Django 5.1
- PostgreSQL/SQLite (attuale DB locale sqlite3)
- Django REST Framework
- Frontend server-side templates (Tailwind/Vanilla JS) + admin Django
- pyairbnb per sync recensioni/medie Airbnb

Struttura delle cartelle
========================

- `Rhome_book/`: configurazione progetto Django (settings, urls, wsgi/asgi).
- `listings/`: logica annunci, recensioni, integrazioni Airbnb, servizi di sync, admin personalizzato.
- `bookings/`: modelli e viste prenotazioni singole/combinate, pagamenti, messaggistica.
- `calendar_rules/`: regole disponibilità, manager, servizi calendario e gestione blocchi/gap.
- `templates/`: template globali (frontend, admin override, account).
- `users/`: viste account (dashboard, profilo), form registrazione.
- `amenities/`, `prices/`, ecc.: moduli di supporto per cataloghi e regole.

Moduli principali e cosa fanno
==============================

- `listings.models`: `Listing`, `Review`, campi Airbnb, statistiche medie, gruppi per combinazioni.
- `listings.services.review_sync`: sincronizza recensioni Airbnb, aggiorna dati esistenti, importa medie categoria da `pyairbnb.get_details`.
- `bookings.models`: `Booking`, `MultiBooking`, pagamenti, messaggi; calcoli prezzi e blocchi disponibilità.
- `bookings.views`: API per disponibilità singola/ combinata, creazione prenotazioni combinate (`create_combined_booking`), elenco/ dettaglio prenotazioni.
- `calendar_rules.managers.CalendarManager`: orchestratore disponibilità/prezzi con `CalendarService`.
- `calendar_rules.services.calendar_service`: logica avanzata per blocked ranges, gap rules, turnover, integrazione chiusure.

API esposte
===========

- `/prenotazioni/api/check-availability/` (`check_availability`) – POST, verifica disponibilità singola.
- `/prenotazioni/api/quick-availability/` (`quick_availability_check`) – POST, versione rapida.
- `/prenotazioni/api/combined-availability/` (`combined_availability`) – POST, ricerca combinazioni gruppi.
- `/prenotazioni/api/combined-booking/` (`create_combined_booking`) – POST, crea `MultiBooking` con `Booking` per ogni listing.
- `/prenotazioni/api/create-booking/` (`create_booking`) – POST, prenotazione singola.
- `/calendar/<listing_id>/` ecc. – API calendario (occupato/chiuso/prezzi).

Decisioni architetturali importanti
===================================

- Le combinazioni multi-appartamento si basano su `ListingGroup` e vengono orchestrate da `MultiBooking` + `Booking` collegati, mantenendo atomicità tramite transazioni.
- Il calcolo disponibilità/prezzi passa da `CalendarManager` → `CalendarService`, che consolida dati in un’unica pipeline (bookings/gap/turnover).
- Le recensioni Airbnb vengono sincronizzate aggiornando record esistenti, salvando medie categoria separate direttamente sul modello `Listing` per esposizione frontend.
- Logging dettagliato per `listings.services.review_sync` e `calendar_rules` per facilitare debug in ambiente Windows (niente emoji).



