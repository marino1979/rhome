"""
Sistema di verifica disponibilità per prenotazioni.

Logica chiara e lineare:
1. Date valide?
2. Periodo chiuso?
3. Conflitti con prenotazioni esistenti?
4. Rispetta gap tra prenotazioni?
5. Rispetta soggiorno minimo?
6. Check-in/check-out permessi in questi giorni?
"""

from datetime import date, timedelta
from typing import Dict, List, Tuple, Set
from django.db.models import Q
from django.utils import timezone


class AvailabilityChecker:
    """
    Verifica disponibilità di un listing per un periodo specifico.

    Regole implementate (in ordine di priorità):
    1. Date valide (check_out > check_in, date future)
    2. Chiusure (ClosureRule, ExternalCalendar sync)
    3. Prenotazioni esistenti (nessuna sovrapposizione)
    4. Gap tra prenotazioni (gap_between_bookings)
    5. Soggiorno minimo (min_stay_nights, può essere sovrascritto da PriceRule)
    6. Regole check-in/out (CheckInOutRule per giorni specifici o ricorrenti)
    """

    def __init__(self, listing):
        self.listing = listing

    def check_availability(self, check_in: date, check_out: date, exclude_booking_id=None) -> Tuple[bool, str]:
        """
        Verifica se un periodo è disponibile per prenotazione.

        Args:
            check_in: Data di check-in
            check_out: Data di check-out
            exclude_booking_id: ID di booking da escludere (per modifiche)

        Returns:
            (disponibile, messaggio) - True se disponibile, False + motivo se non disponibile
        """
        # 1. Validazione date
        valid, message = self._validate_dates(check_in, check_out)
        if not valid:
            return False, message

        # 2. Verifica chiusure
        closed, message = self._check_closures(check_in, check_out)
        if closed:
            return False, message

        # 3. Verifica conflitti con prenotazioni esistenti
        conflict, message = self._check_booking_conflicts(check_in, check_out, exclude_booking_id)
        if conflict:
            return False, message

        # 4. Verifica gap tra prenotazioni
        gap_ok, message = self._check_gap_requirement(check_in, check_out, exclude_booking_id)
        if not gap_ok:
            return False, message

        # 5. Verifica soggiorno minimo
        min_stay_ok, message = self._check_min_stay(check_in, check_out)
        if not min_stay_ok:
            return False, message

        # 6. Verifica regole check-in/out
        rules_ok, message = self._check_checkinout_rules(check_in, check_out)
        if not rules_ok:
            return False, message

        return True, "Disponibile"

    def _validate_dates(self, check_in: date, check_out: date) -> Tuple[bool, str]:
        """Validazione base delle date."""
        if check_in >= check_out:
            return False, "La data di check-out deve essere successiva al check-in"

        today = timezone.now().date()
        if check_in < today:
            return False, "Non è possibile prenotare date passate"

        # Verifica anticipo prenotazione
        advance_days = (check_in - today).days
        if advance_days < self.listing.min_booking_advance:
            return False, f"Prenotazione richiede almeno {self.listing.min_booking_advance} giorni di anticipo"

        if advance_days > self.listing.max_booking_advance:
            return False, f"Prenotazione possibile solo entro {self.listing.max_booking_advance} giorni"

        return True, "Date valide"

    def _check_closures(self, check_in: date, check_out: date) -> Tuple[bool, str]:
        """Verifica se il periodo include chiusure."""
        from .models import ClosureRule

        # Verifica chiusure che si sovrappongono al periodo richiesto
        # Una chiusura blocca se c'è qualsiasi sovrapposizione con il soggiorno
        closures = ClosureRule.objects.filter(
            listing=self.listing,
            start_date__lt=check_out,  # Chiusura inizia prima del nostro check-out
            end_date__gte=check_in      # Chiusura finisce dopo (o nel) nostro check-in
        )

        if closures.exists():
            closure = closures.first()
            if closure.is_external_booking:
                return True, f"Periodo non disponibile (prenotazione esterna dal {closure.start_date} al {closure.end_date})"
            return True, f"Struttura chiusa dal {closure.start_date} al {closure.end_date}"

        return False, "Nessuna chiusura"

    def _check_booking_conflicts(self, check_in: date, check_out: date, exclude_booking_id=None) -> Tuple[bool, str]:
        """Verifica conflitti con prenotazioni esistenti."""
        from bookings.models import Booking

        # Trova prenotazioni che si sovrappongono
        # Regola: Una prenotazione occupa dal check_in (incluso) al check_out (escluso)
        # Quindi: check_out di una prenotazione = check_in di un'altra è OK (turnover stesso giorno)
        conflicting_bookings = Booking.objects.filter(
            listing=self.listing,
            status__in=['confirmed', 'pending'],
            check_in_date__lt=check_out,      # Prenotazione inizia prima del nostro check-out
            check_out_date__gt=check_in        # Prenotazione finisce dopo il nostro check-in
        )

        if exclude_booking_id:
            conflicting_bookings = conflicting_bookings.exclude(pk=exclude_booking_id)

        # Verifica sovrapposizione reale (permetti turnover stesso giorno)
        for booking in conflicting_bookings:
            # Sovrapposizione reale se NON è un semplice turnover
            if not (booking.check_out_date == check_in or booking.check_in_date == check_out):
                return True, f"Periodo già prenotato (conflitto con prenotazione dal {booking.check_in_date} al {booking.check_out_date})"

        return False, "Nessun conflitto"

    def _check_gap_requirement(self, check_in: date, check_out: date, exclude_booking_id=None) -> Tuple[bool, str]:
        """
        Verifica che il gap tra prenotazioni sia rispettato.

        Logica gap:
        - gap_days = 0: Turnover stesso giorno OK (check_out = check_in successivo)
        - gap_days = 1: Serve 1 giorno di gap (check_out + 1 = check_in successivo)
        - gap_days = 2: Servono 2 giorni di gap (check_out + 2 = check_in successivo)
        """
        gap_days = self.listing.gap_between_bookings

        if gap_days == 0:
            return True, "Nessun gap richiesto"

        from bookings.models import Booking

        # Trova prenotazioni vicine
        nearby_bookings = Booking.objects.filter(
            listing=self.listing,
            status__in=['confirmed', 'pending']
        )

        if exclude_booking_id:
            nearby_bookings = nearby_bookings.exclude(pk=exclude_booking_id)

        for booking in nearby_bookings:
            # Gap PRIMA del nostro check-in (dopo il check-out di un'altra prenotazione)
            days_after_previous = (check_in - booking.check_out_date).days
            # Se gap_days > 0, blocca se il gap è insufficiente (incluso gap = 0)
            if 0 <= days_after_previous < gap_days:
                return False, f"Richiesto gap di {gap_days} giorni tra prenotazioni (solo {days_after_previous} giorni dopo prenotazione precedente)"

            # Gap DOPO il nostro check-out (prima del check-in di un'altra prenotazione)
            days_before_next = (booking.check_in_date - check_out).days
            # Se gap_days > 0, blocca se il gap è insufficiente (incluso gap = 0)
            if 0 <= days_before_next < gap_days:
                return False, f"Richiesto gap di {gap_days} giorni tra prenotazioni (solo {days_before_next} giorni prima della prossima prenotazione)"

        return True, "Gap rispettato"

    def _check_min_stay(self, check_in: date, check_out: date) -> Tuple[bool, str]:
        """Verifica soggiorno minimo."""
        from .models import PriceRule

        nights = (check_out - check_in).days

        # Prima verifica se c'è una PriceRule con min_nights per questo periodo
        price_rules_with_min = PriceRule.objects.filter(
            listing=self.listing,
            min_nights__isnull=False,
            start_date__lte=check_in,
            end_date__gte=check_out
        ).order_by('min_nights')

        if price_rules_with_min.exists():
            min_nights = price_rules_with_min.first().min_nights
            if nights < min_nights:
                return False, f"Soggiorno minimo richiesto: {min_nights} notti per questo periodo"
        else:
            # Usa soggiorno minimo di default del listing
            min_nights = self.listing.min_stay_nights
            if nights < min_nights:
                return False, f"Soggiorno minimo richiesto: {min_nights} notti"

        return True, "Soggiorno minimo rispettato"

    def _check_checkinout_rules(self, check_in: date, check_out: date) -> Tuple[bool, str]:
        """Verifica regole di check-in/out per giorni specifici o ricorrenti."""
        from .models import CheckInOutRule

        rules = CheckInOutRule.objects.filter(listing=self.listing)

        for rule in rules:
            if rule.rule_type == 'no_checkin':
                # Verifica se il check-in cade in un giorno bloccato
                if rule.recurrence_type == 'specific_date' and rule.specific_date:
                    if check_in == rule.specific_date:
                        return False, f"Check-in non permesso il {check_in.strftime('%d/%m/%Y')}"

                elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                    # day_of_week: 0=Lunedì, 6=Domenica
                    if check_in.weekday() == rule.day_of_week:
                        days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
                        return False, f"Check-in non permesso di {days[rule.day_of_week]}"

            elif rule.rule_type == 'no_checkout':
                # Verifica se il check-out cade in un giorno bloccato
                if rule.recurrence_type == 'specific_date' and rule.specific_date:
                    if check_out == rule.specific_date:
                        return False, f"Check-out non permesso il {check_out.strftime('%d/%m/%Y')}"

                elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                    if check_out.weekday() == rule.day_of_week:
                        days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
                        return False, f"Check-out non permesso di {days[rule.day_of_week]}"

        return True, "Regole check-in/out rispettate"

    # ==================== API PER FRONTEND ====================

    def get_calendar_data(self, start_date: date, end_date: date) -> Dict:
        """
        Genera dati calendario per il frontend (stile Airbnb).

        Returns:
            {
                'blocked_dates': ['2025-01-15', '2025-01-16', ...],  # Date completamente bloccate
                'checkin_disabled': ['2025-01-20', ...],              # Solo check-in non permesso
                'checkout_disabled': ['2025-01-22', ...],             # Solo check-out non permesso
                'min_stay': 2,                                         # Soggiorno minimo default
                'gap_days': 1,                                         # Gap tra prenotazioni
                'bookings': [                                          # Prenotazioni nel periodo
                    {'check_in': '2025-01-15', 'check_out': '2025-01-20'},
                    ...
                ]
            }
        """
        blocked_dates = set()
        checkin_disabled = set()
        checkout_disabled = set()

        # 1. Date bloccate da chiusure
        blocked_dates.update(self._get_closure_dates(start_date, end_date))

        # 2. Date bloccate da prenotazioni esistenti
        blocked_dates.update(self._get_booked_dates(start_date, end_date))

        # 3. Date con check-in disabilitato (da regole)
        checkin_disabled.update(self._get_checkin_disabled_dates(start_date, end_date))

        # 4. Date con check-out disabilitato (da regole)
        checkout_disabled.update(self._get_checkout_disabled_dates(start_date, end_date))

        # 5. Date bloccate per gap tra prenotazioni
        gap_blocked = self._get_gap_blocked_dates(start_date, end_date)
        checkin_disabled.update(gap_blocked)

        # 6. Ottieni prenotazioni nel periodo per il frontend
        bookings_data = self._get_bookings_data(start_date, end_date)

        return {
            'blocked_dates': sorted(blocked_dates),
            'checkin_disabled': sorted(checkin_disabled - blocked_dates),  # Non duplicare
            'checkout_disabled': sorted(checkout_disabled - blocked_dates),
            'min_stay': self.listing.min_stay_nights,
            'gap_days': self.listing.gap_between_bookings,
            'bookings': bookings_data,
        }

    def _get_closure_dates(self, start_date: date, end_date: date) -> Set[str]:
        """Restituisce tutte le date bloccate da chiusure."""
        from .models import ClosureRule

        blocked = set()
        closures = ClosureRule.objects.filter(
            listing=self.listing,
            start_date__lte=end_date,
            end_date__gte=start_date
        )

        for closure in closures:
            current = max(closure.start_date, start_date)
            end = min(closure.end_date, end_date)

            while current <= end:
                blocked.add(current.isoformat())
                current += timedelta(days=1)

        return blocked

    def _get_booked_dates(self, start_date: date, end_date: date) -> Set[str]:
        """
        Restituisce tutte le date COMPLETAMENTE occupate da prenotazioni.

        LOGICA CORRETTA per turnover flessibile:
        - Una prenotazione occupa SOLO i giorni INTERNI (da check_in+1 a check_out-1)
        - Il check_in e check_out NON sono in blocked_dates
        - Il check_in va in checkin_disabled (gestito in _get_checkin_disabled_dates)
        - Il check_out è libero per check-out di altre prenotazioni

        Esempio: Prenotazione 14-21 gennaio
        - blocked_dates: 15,16,17,18,19,20 (giorni INTERNI)
        - checkin_disabled: 14 (+ gap days dopo 21)
        - Quindi una prenotazione 12-14 è possibile (checkout il 14)
        """
        from bookings.models import Booking

        blocked = set()
        bookings = Booking.objects.filter(
            listing=self.listing,
            status__in=['confirmed', 'pending'],
            check_in_date__lt=end_date,
            check_out_date__gt=start_date
        )

        for booking in bookings:
            # Occupazione SOLO giorni interni: da check_in+1 a check_out-1
            # ✅ +1 day: esclude il check_in (disponibile per checkout altrui)
            current = max(booking.check_in_date + timedelta(days=1), start_date)
            # ✅ -1 day: esclude il check_out (già escluso naturalmente)
            end = min(booking.check_out_date - timedelta(days=1), end_date)

            while current <= end:
                blocked.add(current.isoformat())
                current += timedelta(days=1)

        return blocked

    def _get_checkin_disabled_dates(self, start_date: date, end_date: date) -> Set[str]:
        """
        Restituisce date in cui il check-in è disabilitato.

        Include:
        1. Giorni di check-in di prenotazioni esistenti (non si può fare check-in)
        2. Regole CheckInOutRule con rule_type='no_checkin'
        """
        from .models import CheckInOutRule
        from bookings.models import Booking

        disabled = set()

        # 1. Aggiungi giorni di check-in delle prenotazioni esistenti
        bookings = Booking.objects.filter(
            listing=self.listing,
            status__in=['confirmed', 'pending'],
            check_in_date__gte=start_date,
            check_in_date__lte=end_date
        )
        for booking in bookings:
            disabled.add(booking.check_in_date.isoformat())

        # 2. Aggiungi regole no_checkin
        rules = CheckInOutRule.objects.filter(
            listing=self.listing,
            rule_type='no_checkin'
        )

        for rule in rules:
            if rule.recurrence_type == 'specific_date' and rule.specific_date:
                if start_date <= rule.specific_date <= end_date:
                    disabled.add(rule.specific_date.isoformat())

            elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                # Aggiungi tutti i giorni della settimana nel range
                current = start_date
                while current <= end_date:
                    if current.weekday() == rule.day_of_week:
                        disabled.add(current.isoformat())
                    current += timedelta(days=1)

        return disabled

    def _get_checkout_disabled_dates(self, start_date: date, end_date: date) -> Set[str]:
        """Restituisce date in cui il check-out è disabilitato."""
        from .models import CheckInOutRule

        disabled = set()
        rules = CheckInOutRule.objects.filter(
            listing=self.listing,
            rule_type='no_checkout'
        )

        for rule in rules:
            if rule.recurrence_type == 'specific_date' and rule.specific_date:
                if start_date <= rule.specific_date <= end_date:
                    disabled.add(rule.specific_date.isoformat())

            elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                current = start_date
                while current <= end_date:
                    if current.weekday() == rule.day_of_week:
                        disabled.add(current.isoformat())
                    current += timedelta(days=1)

        return disabled

    def _get_bookings_data(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Restituisce le prenotazioni nel periodo specificato.

        Returns:
            List di dict con check_in e check_out delle prenotazioni
        """
        from bookings.models import Booking

        bookings = Booking.objects.filter(
            listing=self.listing,
            status__in=['confirmed', 'pending'],
            check_in_date__lt=end_date,
            check_out_date__gt=start_date
        ).order_by('check_in_date')

        return [
            {
                'check_in': booking.check_in_date.isoformat(),
                'check_out': booking.check_out_date.isoformat()
            }
            for booking in bookings
        ]

    def _get_gap_blocked_dates(self, start_date: date, end_date: date) -> Set[str]:
        """
        Restituisce date in cui il check-in è bloccato a causa del gap tra prenotazioni.

        Logica gap CORRETTA (bidirezionale + min_stay):
        - gap_days = 0: Turnover stesso giorno OK → nessun blocco
        - gap_days = 1: Check-in bloccato SOLO il giorno del check-out → gap di 1 giorno
        - gap_days = 5: Check-in bloccato per 5 giorni DOPO check-out

        IMPORTANTE PRIMA DEL CHECK-IN:
        Il gap prima del check-in deve considerare anche il min_stay!
        - Se gap=5 e min_stay=3, devo bloccare (5+3-1)=7 giorni prima del check-in
        - Perché una prenotazione che inizia 6 giorni prima, con min_stay=3,
          terminerebbe 3 giorni prima del check-in successivo → dentro il gap!

        Formula: gap_before = gap_days + min_stay - 1

        Esempio con gap=5, min_stay=3, prenotazione 14-21:
        - Check-in 11 gen → Check-out min 14 gen → CONFLITTO (gap insufficiente)
        - Check-in 10 gen → Check-out min 13 gen → OK (finisce 1 giorno prima del gap)
        - Check-in 7 gen → Check-out min 10 gen → OK (finisce 4 giorni prima del gap)
        - Quindi blocco: dal 8 al 13 gen = 14 - (5+3-1) = 14 - 7 al 14 - 1
        """
        from bookings.models import Booking

        gap_days = self.listing.gap_between_bookings
        if gap_days == 0:
            return set()  # ✅ Nessun gap = turnover stesso giorno permesso

        blocked = set()
        bookings = Booking.objects.filter(
            listing=self.listing,
            status__in=['confirmed', 'pending']
        )

        # Ottieni min_stay effettivo
        min_stay = self.listing.min_stay_nights or 1

        for booking in bookings:
            if gap_days >= 1:
                # 1. Blocca i gap_days giorni DOPO ogni check-out
                # (per pulizia/manutenzione)
                gap_start_after = booking.check_out_date
                gap_end_after = booking.check_out_date + timedelta(days=gap_days - 1)

                current = max(gap_start_after, start_date)
                end = min(gap_end_after, end_date)

                while current <= end:
                    blocked.add(current.isoformat())
                    current += timedelta(days=1)

                # 2. Blocca PRIMA di ogni check-in considerando min_stay
                # Gap effettivo = gap_days + min_stay - 1
                # Esempio: gap=5, min_stay=3 → blocca 7 giorni prima
                # Perché: check-in a -6 giorni + min_stay 3 = check-out a -3 giorni → dentro gap!
                gap_before_days = gap_days + min_stay - 1

                gap_start_before = booking.check_in_date - timedelta(days=gap_before_days)
                gap_end_before = booking.check_in_date - timedelta(days=1)

                current = max(gap_start_before, start_date)
                end = min(gap_end_before, end_date)

                while current <= end:
                    blocked.add(current.isoformat())
                    current += timedelta(days=1)

        return blocked
