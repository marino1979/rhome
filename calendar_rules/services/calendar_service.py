# calendar_rules/services/calendar_service.py
"""
Servizio principale per la gestione del calendario e disponibilit.

Questo servizio orchestra tutti i componenti specializzati per fornire
una API pulita e testabile per la gestione della disponibilit calendario.
"""

import logging
from datetime import date, timedelta
from typing import Dict, List, Set, Tuple, Any
from django.db.models import QuerySet

from ..models import ClosureRule, CheckInOutRule, PriceRule
from bookings.models import Booking
from .exceptions import CalendarServiceError, InvalidDateRangeError

# Configura logger per debug calendario
logger = logging.getLogger('calendar_debug')


class CalendarService:
    """
    Servizio principale per la gestione del calendario.
    
    Responsabilit:
    - Orchestrazione dei servizi specializzati
    - Validazione input
    - Formattazione output per API
    """
    
    def __init__(self, listing):
        """
        Inizializza il servizio per un listing specifico.
        
        Args:
            listing: Istanza del modello Listing
        """
        self.listing = listing
    
    def get_unavailable_dates(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Metodo principale per ottenere tutte le informazioni di disponibilit.
        
        Args:
            start_date: Data di inizio del periodo
            end_date: Data di fine del periodo
            
        Returns:
            Dict con tutte le informazioni di disponibilit
            
        Raises:
            InvalidDateRangeError: Se il range di date non  valido
            CalendarServiceError: Per altri errori del calendario
        """
        # Validazione input
        self._validate_date_range(start_date, end_date)
        
        # DEBUG: Inizio calcolo disponibilit
        logger.info(f"[CALENDAR DEBUG] Inizio calcolo disponibilit per Listing {self.listing.id}")
        logger.info(f"[CALENDAR DEBUG] Periodo richiesto: {start_date} -> {end_date}")
        logger.info(f"[CALENDAR DEBUG] Gap tra prenotazioni: {self.listing.gap_between_bookings or 0} giorni")
        
        try:
            # Ottieni dati ottimizzati
            calendar_data = self._get_optimized_calendar_data(start_date, end_date)
            
            # DEBUG: Dati ottenuti
            self._debug_calendar_data(calendar_data)
            
            # Calcola componenti separati con la nuova logica
            blocked_ranges = self._calculate_blocked_ranges_only_bookings(calendar_data, start_date, end_date)
            checkin_dates = self._extract_checkin_dates(calendar_data, start_date, end_date)
            checkout_dates = self._extract_checkout_dates(calendar_data, start_date, end_date)
            gap_days = self._calculate_gap_days(calendar_data, start_date, end_date)
            checkin_blocked_rules = self._calculate_checkin_blocked_by_rules(calendar_data, start_date, end_date)
            checkout_blocked_rules = self._calculate_checkout_blocked_by_rules(calendar_data, start_date, end_date)
            checkin_blocked_gap = self._calculate_checkin_blocked_by_gap(calendar_data, start_date, end_date)
            
            # DEBUG: Risultati calcoli
            self._debug_new_calculation_results(
                blocked_ranges, checkin_dates, checkout_dates, gap_days,
                checkin_blocked_rules, checkout_blocked_rules, checkin_blocked_gap
            )
            
            # Consolida i range bloccati
            consolidated_ranges = self._consolidate_ranges(blocked_ranges)
            
            # DEBUG: Range consolidati
            self._debug_consolidated_ranges(consolidated_ranges)
            
            # Genera metadata
            metadata = self._generate_metadata(start_date, end_date)
            
            # Formatta response con la nuova struttura
            result = self._format_new_response(
                consolidated_ranges=consolidated_ranges,
                checkin_dates=checkin_dates,
                checkout_dates=checkout_dates,
                gap_days=gap_days,
                checkin_blocked_rules=checkin_blocked_rules,
                checkout_blocked_rules=checkout_blocked_rules,
                checkin_blocked_gap=checkin_blocked_gap,
                metadata=metadata
            )
            
            # DEBUG: Risultato finale
            self._debug_final_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] [CALENDAR DEBUG] Errore durante il calcolo: {str(e)}")
            if isinstance(e, CalendarServiceError):
                raise
            raise CalendarServiceError(f"Errore durante il calcolo disponibilit: {str(e)}")
    
    def _validate_date_range(self, start_date: date, end_date: date) -> None:
        """Valida che il range di date sia corretto."""
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            raise InvalidDateRangeError("Le date devono essere istanze di datetime.date")
        
        if start_date >= end_date:
            raise InvalidDateRangeError("La data di inizio deve essere precedente alla data di fine")
        
        # Verifica che le date non siano troppo nel passato
        today = date.today()
        if start_date < today - timedelta(days=365):
            raise InvalidDateRangeError("Non  possibile calcolare disponibilit per date troppo nel passato")
        
        # Verifica che le date non siano troppo nel futuro
        if end_date > today + timedelta(days=365):
            raise InvalidDateRangeError("Non  possibile calcolare disponibilit per date troppo nel futuro")
    
    def _get_optimized_calendar_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Ottiene tutti i dati necessari con query ottimizzate.
        """
        gap_lookback_days = self.listing.gap_between_bookings or 0
        gap_start_date = start_date - timedelta(days=gap_lookback_days)

        # Booking window leggermente estesa a sinistra per gestire gap prima dell'intervallo
        bookings = Booking.objects.filter(
            listing=self.listing,
            status__in=['pending', 'confirmed'],
            check_out_date__gte=gap_start_date,
            check_in_date__lte=end_date
        ).values('check_in_date', 'check_out_date')

        closures = self.listing.closure_rules.filter(
            end_date__gte=start_date,
            start_date__lte=end_date
        ).values('start_date', 'end_date', 'is_external_booking')

        checkinout_rules = self.listing.checkinout_rules.all()

        # Price rules + calcolo min_nights effettivo (il più piccolo nel periodo)
        price_rules_qs = self.listing.price_rules.filter(
            end_date__gte=start_date,
            start_date__lte=end_date
        )
        price_rules = list(price_rules_qs.values('min_nights'))
        min_nights_values = [pr['min_nights'] for pr in price_rules if pr.get('min_nights') is not None]
        effective_min_nights = min(min_nights_values) if min_nights_values else 1

        return {
            'bookings': list(bookings),
            'closures': list(closures),
            'checkinout_rules': checkinout_rules,
            'price_rules': list(price_rules),
            'gap_days': self.listing.gap_between_bookings or 0,
            'min_nights': effective_min_nights,
            'start_date': start_date,
            'end_date': end_date,
            'gap_start_date': gap_start_date,
        }
    
    def _calculate_blocked_ranges(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> List[Tuple[date, date]]:
        """
        Calcola i range *totalmente* non selezionabili:
        - Giorni interni alle prenotazioni (escludendo check-in e check-out)
        - Chiusure
        (Niente logica di gap/min_notti qui: quella è competenza dei blocchi di check-in/out)
        """
        logger.info("[BLOCKED] [CALENDAR DEBUG] === CALCOLO RANGE BLOCCATI (PULITI) ===")

        blocked_ranges: List[Tuple[date, date]] = []
        bookings = calendar_data['bookings']
        closures = calendar_data['closures']

        # 1) Interno prenotazioni: (check_in+1) .. (check_out-1)
        sorted_bookings = sorted(
            (b for b in bookings if b['check_in_date'] and b['check_out_date']),
            key=lambda x: x['check_in_date']
        )
        for i, booking in enumerate(sorted_bookings, 1):
            ci, co = booking['check_in_date'], booking['check_out_date']
            interior_start = max(ci + timedelta(days=1), start_date)
            interior_end   = min(co - timedelta(days=1), end_date)
            if interior_start <= interior_end:
                blocked_ranges.append((interior_start, interior_end))
                logger.info(f"   [INTERIOR] {interior_start} -> {interior_end}")

        # 2) Chiusure
        for i, closure in enumerate(closures, 1):
            r0 = max(closure['start_date'], start_date)
            r1 = min(closure['end_date'], end_date)
            if r0 <= r1:
                blocked_ranges.append((r0, r1))
                logger.info(f"   [CLOSURE] {r0} -> {r1}")

        logger.info(f"[BLOCKED] [CALENDAR DEBUG] Totale range bloccati: {len(blocked_ranges)}")
        return blocked_ranges
    
    def _calculate_checkin_blocks(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Giorni in cui NON è consentito iniziare un soggiorno:
        - Gap prima del prossimo check-in: [bi-gap, bi-1]
        - Gap dopo un check-out: [bo, bo+gap-1]  (se gap>0)
        - Min notti prima del prossimo check-in: [bi-(min_nights-1), bi-1]
        - Regole 'no_checkin' (date specifiche / settimanali)
        """
        logger.info("[BLOCKED] [CALENDAR DEBUG] === CALCOLO CHECK-IN BLOCCATI ===")
        bookings = calendar_data['bookings']
        gap_days = calendar_data['gap_days']
        min_nights = calendar_data.get('min_nights', 1)

        checkin_block_dates: Set[str] = set()
        checkin_block_weekdays: Set[int] = set()

        # GAP & MIN NOTTI intorno alle prenotazioni
        if gap_days > 0 or min_nights > 1:
            for b in bookings:
                ci, co = b['check_in_date'], b['check_out_date']

                # (a) Pre-gap: giorni immediatamente prima del prossimo check-in
                if gap_days > 0 and ci:
                    pre_start = max(ci - timedelta(days=gap_days), start_date)
                    pre_end   = min(ci - timedelta(days=1), end_date)
                    d = pre_start
                    while d <= pre_end:
                        checkin_block_dates.add(d.isoformat())
                        d += timedelta(days=1)

                # (b) Soggiorno minimo: ultimi (min_nights-1) giorni prima del prossimo check-in
                if min_nights > 1 and ci:
                    min_start = max(ci - timedelta(days=min_nights - 1), start_date)
                    min_end   = min(ci - timedelta(days=1), end_date)
                    d = min_start
                    while d <= min_end:
                        checkin_block_dates.add(d.isoformat())
                        d += timedelta(days=1)

                # (c) Post-gap dopo il check-out: i primi 'gap' giorni NON si può iniziare
                if gap_days > 0 and co:
                    post_start = max(co, start_date)
                    post_end   = min(co + timedelta(days=gap_days - 1), end_date)
                    d = post_start
                    while d <= post_end:
                        checkin_block_dates.add(d.isoformat())
                        d += timedelta(days=1)

        # Regole 'no_checkin'
        for rule in calendar_data['checkinout_rules']:
            if rule.rule_type == 'no_checkin':
                if rule.recurrence_type == 'specific_date' and rule.specific_date:
                    if start_date <= rule.specific_date <= end_date:
                        checkin_block_dates.add(rule.specific_date.isoformat())
                elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                    checkin_block_weekdays.add(rule.day_of_week)

        result = {
            'dates': sorted(checkin_block_dates),
            'weekdays': sorted(checkin_block_weekdays),
        }
        logger.info(f"[BLOCKED] [CALENDAR DEBUG] Check-in bloccati: {len(result['dates'])} date, {len(result['weekdays'])} weekday")
        return result
    
    def _calculate_checkout_blocks(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> Dict[str, Any]:
        """Calcola i giorni bloccati per check-out."""
        logger.info("[BLOCKED] [CALENDAR DEBUG] === CALCOLO CHECK-OUT BLOCCATI ===")
        
        checkout_block_dates = set()
        checkout_block_weekdays = set()
        
        # Regole check-out
        logger.info(f"[RULES] [CALENDAR DEBUG] Analizzando regole check-out")
        for i, rule in enumerate(calendar_data['checkinout_rules'], 1):
            if rule.rule_type == 'no_checkout':
                if rule.recurrence_type == 'specific_date' and rule.specific_date:
                    if start_date <= rule.specific_date <= end_date:
                        checkout_block_dates.add(rule.specific_date.isoformat())
                        logger.info(f"   [BLOCKED] Regola {i}: Check-out bloccato il {rule.specific_date}")
                    else:
                        logger.info(f"   [OK] Regola {i}: Check-out bloccato il {rule.specific_date} (fuori periodo)")
                elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                    checkout_block_weekdays.add(rule.day_of_week)
                    days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
                    logger.info(f"   [BLOCKED] Regola {i}: Check-out bloccato ogni {days[rule.day_of_week]}")
        
        result = {
            'dates': sorted(checkout_block_dates),
            'weekdays': sorted(checkout_block_weekdays),
        }
        
        logger.info(f"[BLOCKED] [CALENDAR DEBUG] Totale check-out bloccati: {len(result['dates'])} date, {len(result['weekdays'])} giorni settimana")
        logger.info("[BLOCKED] [CALENDAR DEBUG] === FINE CALCOLO CHECK-OUT BLOCCATI ===")
        
        return result
    
    def _calculate_turnover_days(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> Set[str]:
        """
        Giorni di turnover = giorni di check-out utilizzabili per iniziare un nuovo soggiorno.
        Consentiti SOLO se gap_days == 0 e non vige un divieto di 'no_checkin' su quel giorno.
        """
        logger.info("[TURNOVER] [CALENDAR DEBUG] === CALCOLO TURNOVER DAYS ===")
        turnover_days: Set[str] = set()
        gap_days = calendar_data['gap_days']

        # Raccogli divieti no_checkin
        no_dates: Set[date] = set()
        no_weekdays: Set[int] = set()
        for rule in calendar_data['checkinout_rules']:
            if rule.rule_type == 'no_checkin':
                if rule.recurrence_type == 'specific_date' and rule.specific_date:
                    if start_date <= rule.specific_date <= end_date:
                        no_dates.add(rule.specific_date)
                elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                    no_weekdays.add(rule.day_of_week)

        for b in calendar_data['bookings']:
            co = b['check_out_date']
            if not co or not (start_date <= co <= end_date):
                continue
            if gap_days == 0:
                wd = co.weekday()
                if (co not in no_dates) and (wd not in no_weekdays):
                    turnover_days.add(co.isoformat())

        logger.info(f"[TURNOVER] [CALENDAR DEBUG] Totale turnover days: {len(turnover_days)}")
        return turnover_days
    
    def _extract_real_checkin_dates(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> Set[str]:
        """Estrae i giorni di check-in reali (esclusi i gap days)."""
        logger.info("[OK] [CALENDAR DEBUG] === ESTRAZIONE CHECK-IN REALI ===")
        
        real_checkin_dates = set()
        
        for i, booking in enumerate(calendar_data['bookings'], 1):
            check_in = booking['check_in_date']
            if check_in and start_date <= check_in <= end_date:
                real_checkin_dates.add(check_in.isoformat())
                logger.info(f"   [OK] Check-in reale {i}: {check_in}")
            elif check_in:
                logger.info(f"   [OK] Check-in prenotazione {i} ({check_in}) fuori dal periodo richiesto")
 
        closures = calendar_data.get('closures', [])
        for closure in closures:
            c_start = closure.get('start_date')
            if c_start and start_date <= c_start <= end_date:
                real_checkin_dates.add(c_start.isoformat())
                logger.info(f"   [OK] Check-in chiusura: {c_start}")

        logger.info(f"[OK] [CALENDAR DEBUG] Totale check-in reali: {len(real_checkin_dates)}")
        logger.info("[OK] [CALENDAR DEBUG] === FINE ESTRAZIONE CHECK-IN REALI ===")
 
        return real_checkin_dates
    
    # ==================== NUOVI METODI PER LOGICA SEPARATA ====================
    
    def _calculate_blocked_ranges_only_bookings(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> List[Tuple[date, date]]:
        """
        Calcola i giorni totalmente occupati da prenotazioni esistenti.
        Include tutte le date della prenotazione (dal check-in incluso al check-out escluso).
        Questo blocca tutte le date che non possono essere selezionate per nuove prenotazioni.
        """
        logger.info("[BLOCKED] [CALENDAR DEBUG] === CALCOLO RANGE BLOCCATI (INCLUDE CHECK-IN/OUT) ===")
        
        blocked_ranges: List[Tuple[date, date]] = []
        bookings = calendar_data['bookings']
        closures = calendar_data['closures']
        min_stay = calendar_data.get('min_nights', 1)
        
        # Range bloccati dalle prenotazioni (dal check-in incluso al check-out escluso)
        # Una prenotazione dal 9 al 23 gennaio occupa la struttura dal 9 al 22 incluso
        # (il 23 è il giorno di check-out, quindi la struttura è libera)
        for i, booking in enumerate(bookings, 1):
            ci, co = booking['check_in_date'], booking['check_out_date']
            if ci and co:
                # Inizio: giorno di check-in (incluso)
                blocked_start = max(ci, start_date)
                # Fine: giorno PRIMA del check-out (il check-out non è occupato)
                blocked_end = min(co - timedelta(days=1), end_date)
                if blocked_start <= blocked_end:
                    blocked_ranges.append((blocked_start, blocked_end))
                    logger.info(f"   [BOOKING] Prenotazione {i}: {blocked_start} -> {blocked_end} (check-in={ci}, check-out={co})")
                else:
                    logger.info(f"   [BOOKING] Prenotazione {i}: nessun giorno bloccato (check-in={ci}, check-out={co})")
        
        # Chiusure
        for i, closure in enumerate(closures, 1):
            r0 = max(closure['start_date'], start_date)
            r1 = min(closure['end_date'], end_date)
            if r0 <= r1:
                blocked_ranges.append((r0, r1))
                logger.info(f"   [CLOSURE] Chiusura {i}: {r0} -> {r1}")
        
        logger.info(f"[BLOCKED] [CALENDAR DEBUG] Totale range bloccati: {len(blocked_ranges)}")
        return blocked_ranges
    
    def _extract_checkin_dates(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> List[str]:
        """
        Estrae le date di check-in (arrivo) delle prenotazioni esistenti.
        """
        logger.info("[CHECKIN] [CALENDAR DEBUG] === ESTRAZIONE DATE CHECK-IN ===")
        
        checkin_dates: Set[str] = set()
        bookings = calendar_data['bookings']
        
        for i, booking in enumerate(bookings, 1):
            check_in = booking['check_in_date']
            if check_in and start_date <= check_in <= end_date:
                checkin_dates.add(check_in.isoformat())
                logger.info(f"   [CHECKIN] Check-in {i}: {check_in}")
        
        logger.info(f"[CHECKIN] [CALENDAR DEBUG] Totale check-in: {len(checkin_dates)}")
        return sorted(checkin_dates)
    
    def _extract_checkout_dates(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> List[str]:
        """
        Estrae le date di check-out (partenza) delle prenotazioni esistenti.
        """
        logger.info("[CHECKOUT] [CALENDAR DEBUG] === ESTRAZIONE DATE CHECK-OUT ===")
        
        checkout_dates: Set[str] = set()
        bookings = calendar_data['bookings']
        
        for i, booking in enumerate(bookings, 1):
            check_out = booking['check_out_date']
            if check_out and start_date <= check_out <= end_date:
                checkout_dates.add(check_out.isoformat())
                logger.info(f"   [CHECKOUT] Check-out {i}: {check_out}")
        
        logger.info(f"[CHECKOUT] [CALENDAR DEBUG] Totale check-out: {len(checkout_dates)}")
        return sorted(checkout_dates)
    
    def _calculate_gap_days(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> List[str]:
        """
        Calcola i giorni di gap tra prenotazioni e chiusure (interne o esterne).
        I gap days sono giorni in cui non è consentito un nuovo check-in o check-out
        per garantire il tempo di preparazione dell'alloggio.
        """
        logger.info("[GAP] [CALENDAR DEBUG] === CALCOLO GAP DAYS ===")

        gap_days_set: Set[str] = set()
        bookings = calendar_data['bookings']
        closures = calendar_data.get('closures', [])
        gap_days = calendar_data['gap_days']
        min_stay = calendar_data.get('min_nights', 1)

        if gap_days == 0 and min_stay <= 1:
            logger.info("[GAP] [CALENDAR DEBUG] Nessun gap configurato")
            return []

        logger.info(f"[GAP] [CALENDAR DEBUG] Gap configurato: {gap_days} giorni")

        periods: List[Tuple[date, date]] = []

        for booking in bookings:
            ci, co = booking['check_in_date'], booking['check_out_date']
            if ci and co:
                periods.append((ci, co))

        for closure in closures:
            c_start = closure.get('start_date')
            c_end = closure.get('end_date')
            if c_start and c_end:
                periods.append((c_start, c_end))

        for idx, (period_start, period_end) in enumerate(periods, 1):
            if gap_days > 0:
                # Blocca i giorni prima dell'inizio nel rispetto del gap
                pre_start = period_start - timedelta(days=max(gap_days - 1, 0))
                pre_end = period_start - timedelta(days=1)
                if pre_start < start_date:
                    pre_start = start_date
                if pre_end > end_date:
                    pre_end = end_date
                d = pre_start
                while d <= pre_end:
                    gap_days_set.add(d.isoformat())
                    d += timedelta(days=1)
                if pre_start <= pre_end:
                    logger.info(f"   [GAP] Pre-gap periodo {idx}: {pre_start} -> {pre_end}")

                # Blocca il giorno di check-out e i successivi gap_days-1 giorni
                post_start = period_end
                post_end = period_end + timedelta(days=gap_days - 1)
                if post_start < start_date:
                    post_start = start_date
                if post_end > end_date:
                    post_end = end_date
                d = post_start
                while d <= post_end:
                    gap_days_set.add(d.isoformat())
                    d += timedelta(days=1)
                if post_start <= post_end:
                    logger.info(f"   [GAP] Post-gap periodo {idx}: {post_start} -> {post_end}")

            # Enforce minimum stay by blocking ranges that would be shorter than min_stay
            if min_stay > 1:
                short_range_end = min(period_start - timedelta(days=1), end_date)
                short_range_start = max(start_date, short_range_end - timedelta(days=min_stay - 2))
                if short_range_start <= short_range_end:
                    logger.info(f"   [GAP] Blocked short stay before periodo {idx}: {short_range_start} -> {short_range_end}")
                    d = short_range_start
                    while d <= short_range_end:
                        gap_days_set.add(d.isoformat())
                        d += timedelta(days=1)

        logger.info(f"[GAP] [CALENDAR DEBUG] Totale gap days: {len(gap_days_set)}")
        return sorted(gap_days_set)
    
    def _calculate_checkin_blocked_by_rules(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Calcola i giorni bloccati per check-in a causa delle regole (no_checkin).
        """
        logger.info("[RULES] [CALENDAR DEBUG] === CALCOLO CHECK-IN BLOCCATI DA REGOLE ===")
        
        checkin_blocked_dates: Set[str] = set()
        checkin_blocked_weekdays: Set[int] = set()
        
        for rule in calendar_data['checkinout_rules']:
            if rule.rule_type == 'no_checkin':
                if rule.recurrence_type == 'specific_date' and rule.specific_date:
                    if start_date <= rule.specific_date <= end_date:
                        checkin_blocked_dates.add(rule.specific_date.isoformat())
                        logger.info(f"   [RULE] Data specifica bloccata: {rule.specific_date}")
                elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                    checkin_blocked_weekdays.add(rule.day_of_week)
                    days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
                    logger.info(f"   [RULE] Giorno settimana bloccato: {days[rule.day_of_week]}")
        
        logger.info(f"[RULES] [CALENDAR DEBUG] Check-in bloccati: {len(checkin_blocked_dates)} date, {len(checkin_blocked_weekdays)} weekdays")
        
        return {
            'dates': sorted(checkin_blocked_dates),
            'weekdays': sorted(checkin_blocked_weekdays)
        }
    
    def _calculate_checkout_blocked_by_rules(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Calcola i giorni bloccati per check-out a causa delle regole (no_checkout).
        """
        logger.info("[RULES] [CALENDAR DEBUG] === CALCOLO CHECK-OUT BLOCCATI DA REGOLE ===")
        
        checkout_blocked_dates: Set[str] = set()
        checkout_blocked_weekdays: Set[int] = set()
        
        for rule in calendar_data['checkinout_rules']:
            if rule.rule_type == 'no_checkout':
                if rule.recurrence_type == 'specific_date' and rule.specific_date:
                    if start_date <= rule.specific_date <= end_date:
                        checkout_blocked_dates.add(rule.specific_date.isoformat())
                        logger.info(f"   [RULE] Data specifica bloccata: {rule.specific_date}")
                elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                    checkout_blocked_weekdays.add(rule.day_of_week)
                    days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
                    logger.info(f"   [RULE] Giorno settimana bloccato: {days[rule.day_of_week]}")
        
        logger.info(f"[RULES] [CALENDAR DEBUG] Check-out bloccati: {len(checkout_blocked_dates)} date, {len(checkout_blocked_weekdays)} weekdays")
        
        return {
            'dates': sorted(checkout_blocked_dates),
            'weekdays': sorted(checkout_blocked_weekdays)
        }
    
    def _calculate_checkin_blocked_by_gap(self, calendar_data: Dict[str, Any], start_date: date, end_date: date) -> List[str]:
        """
        Calcola i giorni AGGIUNTIVI bloccati per check-in a causa della combinazione gap + min_nights.
        
        NON include i giorni che sono già gap days (quelli sono già nella sezione gap_days).
        
        Logica:
        - Se min_nights = 1: NON aggiunge nulla (i gap days sono sufficienti)
        - Se min_nights > 1: Blocca i giorni PRIMA dei gap days necessari per rispettare il min_nights
        
        Esempio con gap=3 giorni, min_nights=2, check-in successivo il 25:
        - Gap days: 22, 23, 24 (già nella sezione gap_days)
        - Ultimo check-out possibile: 21 (prima dei gap)
        - Ultimo check-in possibile: 20 (per avere 2 notti fino al 21)
        - Check-in bloccato da gap: 21 (giorno aggiuntivo bloccato)
        """
        logger.info("[GAP_CHECKIN] [CALENDAR DEBUG] === CALCOLO CHECK-IN BLOCCATI DA GAP + MIN_NIGHTS ===")
        
        checkin_blocked_gap: Set[str] = set()
        bookings = calendar_data['bookings']
        gap_days = calendar_data['gap_days']
        min_nights = calendar_data.get('min_nights', 1)
        
        if gap_days == 0:
            logger.info("[GAP_CHECKIN] [CALENDAR DEBUG] Nessun gap configurato")
            return []
        
        if min_nights <= 1:
            logger.info(f"[GAP_CHECKIN] [CALENDAR DEBUG] Min nights = {min_nights}, nessun blocco aggiuntivo necessario")
            return []
        
        logger.info(f"[GAP_CHECKIN] [CALENDAR DEBUG] Gap: {gap_days} giorni, Min nights: {min_nights}")
        
        periods: List[Tuple[date, date]] = []
        for booking in bookings:
            ci = booking['check_in_date']
            co = booking['check_out_date']
            if ci and co:
                periods.append((ci, co))
        closures = calendar_data.get('closures', [])
        for closure in closures:
            c_start = closure.get('start_date')
            c_end = closure.get('end_date')
            if c_start and c_end:
                periods.append((c_start, c_end))

        for idx, (ci, co) in enumerate(periods, 1):
            first_gap_day = ci - timedelta(days=gap_days)
            last_checkout_day = first_gap_day - timedelta(days=1)
            last_valid_checkin = last_checkout_day - timedelta(days=min_nights)
            
            block_start = max(last_valid_checkin + timedelta(days=1), start_date)
            block_end = min(first_gap_day - timedelta(days=1), end_date)
            
            if block_start <= block_end:
                d = block_start
                while d <= block_end:
                    checkin_blocked_gap.add(d.isoformat())
                    d += timedelta(days=1)
                logger.info(f"   [GAP_CHECKIN] Periodo {idx}: bloccati {block_start} -> {block_end}")
                logger.info(f"      (gap inizia: {first_gap_day}, ultimo check-out: {last_checkout_day}, ultimo check-in valido: {last_valid_checkin})")
            else:
                logger.info(f"   [GAP_CHECKIN] Periodo {idx}: nessun blocco aggiuntivo necessario")
        
        logger.info(f"[GAP_CHECKIN] [CALENDAR DEBUG] Totale check-in bloccati da gap+min_nights: {len(checkin_blocked_gap)}")
        return sorted(checkin_blocked_gap)
    
    # ==================== FINE NUOVI METODI ====================
    
    def _consolidate_ranges(self, blocked_ranges: List[Tuple[date, date]]) -> List[Dict[str, str]]:
        """
        Consolida i range bloccati sovrapposti.
        
        TODO: Implementare RangeConsolidator per logica pi robusta
        """
        logger.info("[CONSOLIDATE] [CALENDAR DEBUG] === CONSOLIDAMENTO RANGE ===")
        
        if not blocked_ranges:
            logger.info("[CONSOLIDATE] [CALENDAR DEBUG] Nessun range da consolidare")
            return []
        
        logger.info(f"[CONSOLIDATE] [CALENDAR DEBUG] Consolidando {len(blocked_ranges)} range bloccati")
        
        # Per ora, usa la logica esistente semplificata
        sorted_ranges = sorted(blocked_ranges, key=lambda item: item[0])
        logger.info("[CONSOLIDATE] [CALENDAR DEBUG] Range ordinati per data di inizio")
        
        merged = [list(sorted_ranges[0])]
        logger.info(f"[CONSOLIDATE] [CALENDAR DEBUG] Range iniziale: {sorted_ranges[0][0]} -> {sorted_ranges[0][1]}")
        
        for i, (current_start, current_end) in enumerate(sorted_ranges[1:], 2):
            last_start, last_end = merged[-1]
            logger.info(f"[CONSOLIDATE] [CALENDAR DEBUG] Analizzando range {i}: {current_start} -> {current_end}")
            logger.info(f"[CONSOLIDATE] [CALENDAR DEBUG] Ultimo range consolidato: {last_start} -> {last_end}")
            
            if current_start <= last_end + timedelta(days=1):
                # Range sovrapposti o adiacenti - unisci
                old_end = merged[-1][1]
                merged[-1][1] = max(last_end, current_end)
                logger.info(f"   [CONSOLIDATE] Range {i} unito al precedente: {last_start} -> {merged[-1][1]} (era {old_end})")
            else:
                # Range separati - aggiungi nuovo
                merged.append([current_start, current_end])
                logger.info(f"   [CONSOLIDATE] Range {i} aggiunto come nuovo: {current_start} -> {current_end}")
        
        result = [
            {'from': start.isoformat(), 'to': end.isoformat()}
            for start, end in merged
        ]
        
        logger.info(f"[CONSOLIDATE] [CALENDAR DEBUG] Consolidamento completato: {len(blocked_ranges)} -> {len(result)} range")
        logger.info("[CONSOLIDATE] [CALENDAR DEBUG] === FINE CONSOLIDAMENTO RANGE ===")
        
        return result
    
    def _generate_metadata(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Genera i metadati per la response."""
        booking_window_days = (end_date - start_date).days
        
        # Calcola soggiorno minimo dalle price rules
        min_stay = 1  # Default
        price_rules_with_min = self.listing.price_rules.filter(
            min_nights__isnull=False,
            end_date__gte=start_date,
            start_date__lte=end_date
        ).order_by('min_nights').values_list('min_nights', flat=True).first()
        
        if price_rules_with_min:
            min_stay = int(price_rules_with_min)
        
        return {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'window_days': booking_window_days,
            'min_stay': min_stay,
            'max_stay': 30,
            'gap_between_bookings': self.listing.gap_between_bookings or 0,
        }
    
    def _format_response(self, **kwargs) -> Dict[str, Any]:
        """Formatta la response finale (vecchia struttura - mantenuta per compatibilità)."""
        return {
            'blocked_ranges': kwargs['consolidated_ranges'],
            'turnover_days': sorted(kwargs['turnover_days']),
            'checkin_block': kwargs['checkin_block_data'],
            'checkout_block': kwargs['checkout_block_data'],
            'real_checkin_dates': sorted(kwargs['real_checkin_dates']),
            'metadata': kwargs['metadata'],
            'listing_id': self.listing.id,
        }
    
    def _format_new_response(self, **kwargs) -> Dict[str, Any]:
        """
        Formatta la response finale con la nuova struttura separata.
        
        Struttura:
        1. blocked_ranges: Giorni totalmente occupati da prenotazioni
        2. checkin_dates: Date di arrivo (check-in)
        3. checkout_dates: Date di partenza (check-out)
        4. gap_days: Giorni di gap tra prenotazioni
        5. checkin_blocked_rules: Giorni bloccati per check-in da regole
        6. checkout_blocked_rules: Giorni bloccati per check-out da regole
        7. checkin_blocked_gap: Giorni bloccati per check-in da gap + min_nights
        """
        return {
            'blocked_ranges': kwargs['consolidated_ranges'],
            'checkin_dates': kwargs['checkin_dates'],
            'checkout_dates': kwargs['checkout_dates'],
            'gap_days': kwargs['gap_days'],
            'checkin_blocked_rules': kwargs['checkin_blocked_rules'],
            'checkout_blocked_rules': kwargs['checkout_blocked_rules'],
            'checkin_blocked_gap': kwargs['checkin_blocked_gap'],
            'metadata': kwargs['metadata'],
            'listing_id': self.listing.id,
        }
    
    # ==================== METODI DI DEBUG ====================
    
    def _debug_calendar_data(self, calendar_data: Dict[str, Any]) -> None:
        """Debug dettagliato dei dati del calendario ottenuti."""
        logger.info("[DATA] [CALENDAR DEBUG] === DATI CALENDARIO OTTENUTI ===")
        
        # Debug prenotazioni
        bookings = calendar_data['bookings']
        logger.info(f"[RULES] [CALENDAR DEBUG] Prenotazioni trovate: {len(bookings)}")
        for i, booking in enumerate(bookings, 1):
            logger.info(f"   [ITEM] Prenotazione {i}: Check-in {booking['check_in_date']} -> Check-out {booking['check_out_date']}")
        
        # Debug chiusure
        closures = calendar_data['closures']
        logger.info(f"[BLOCKED] [CALENDAR DEBUG] Chiusure trovate: {len(closures)}")
        for i, closure in enumerate(closures, 1):
            logger.info(f"   [BLOCKED] Chiusura {i}: {closure['start_date']} -> {closure['end_date']}")
        
        # Debug regole check-in/out
        checkinout_rules = calendar_data['checkinout_rules']
        logger.info(f"[RULES] [CALENDAR DEBUG] Regole check-in/out: {len(checkinout_rules)}")
        for i, rule in enumerate(checkinout_rules, 1):
            rule_type = "NO CHECK-IN" if rule.rule_type == 'no_checkin' else "NO CHECK-OUT"
            if rule.recurrence_type == 'specific_date':
                logger.info(f"   [DATE] Regola {i}: {rule_type} il {rule.specific_date}")
            elif rule.recurrence_type == 'weekly':
                days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
                logger.info(f"   [DATE] Regola {i}: {rule_type} ogni {days[rule.day_of_week] if rule.day_of_week is not None else 'N/A'}")
        
        # Debug price rules
        price_rules = calendar_data['price_rules']
        logger.info(f"[PRICE] [CALENDAR DEBUG] Regole prezzi: {len(price_rules)}")
        for i, rule in enumerate(price_rules, 1):
            logger.info(f"   [PRICE] Regola {i}: Min notti {rule.get('min_nights', 'N/A')}")
        
        logger.info(f"[GAP] [CALENDAR DEBUG] Gap days: {calendar_data['gap_days']}")
        logger.info("[DATA] [CALENDAR DEBUG] === FINE DATI CALENDARIO ===")
    
    def _debug_calculation_results(self, blocked_ranges, checkin_block_data, checkout_block_data, turnover_days, real_checkin_dates):
        """Debug dettagliato dei risultati dei calcoli."""
        logger.info("[CALC] [CALENDAR DEBUG] === RISULTATI CALCOLI ===")
        
        # Debug range bloccati
        logger.info(f"[BLOCKED] [CALENDAR DEBUG] Range bloccati trovati: {len(blocked_ranges)}")
        for i, (start, end) in enumerate(blocked_ranges, 1):
            logger.info(f"   [BLOCKED] Range {i}: {start} -> {end}")
        
        # Debug check-in bloccati
        checkin_dates = checkin_block_data['dates']
        checkin_weekdays = checkin_block_data['weekdays']
        logger.info(f"[BLOCKED] [CALENDAR DEBUG] Date check-in bloccate: {len(checkin_dates)}")
        for date_str in checkin_dates:
            logger.info(f"   [BLOCKED] Check-in bloccato: {date_str}")
        if checkin_weekdays:
            days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
            weekdays_str = [days[wd] for wd in checkin_weekdays]
            logger.info(f"   [BLOCKED] Giorni settimana check-in bloccati: {', '.join(weekdays_str)}")
        
        # Debug check-out bloccati
        checkout_dates = checkout_block_data['dates']
        checkout_weekdays = checkout_block_data['weekdays']
        logger.info(f"[BLOCKED] [CALENDAR DEBUG] Date check-out bloccate: {len(checkout_dates)}")
        for date_str in checkout_dates:
            logger.info(f"   [BLOCKED] Check-out bloccato: {date_str}")
        if checkout_weekdays:
            days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
            weekdays_str = [days[wd] for wd in checkout_weekdays]
            logger.info(f"   [BLOCKED] Giorni settimana check-out bloccati: {', '.join(weekdays_str)}")
        
        # Debug turnover days
        logger.info(f"[TURNOVER] [CALENDAR DEBUG] Giorni di turnover: {len(turnover_days)}")
        for date_str in sorted(turnover_days):
            logger.info(f"   [TURNOVER] Turnover: {date_str}")
        
        # Debug real check-in dates
        logger.info(f"[OK] [CALENDAR DEBUG] Date check-in reali: {len(real_checkin_dates)}")
        for date_str in sorted(real_checkin_dates):
            logger.info(f"   [OK] Check-in reale: {date_str}")
        
        logger.info("[CALC] [CALENDAR DEBUG] === FINE RISULTATI CALCOLI ===")
    
    def _debug_new_calculation_results(self, blocked_ranges, checkin_dates, checkout_dates, gap_days, 
                                       checkin_blocked_rules, checkout_blocked_rules, checkin_blocked_gap):
        """Debug dettagliato dei risultati dei calcoli con la nuova struttura."""
        logger.info("[NEW_CALC] [CALENDAR DEBUG] === RISULTATI NUOVI CALCOLI ===")
        
        # Debug range bloccati
        logger.info(f"[BLOCKED] [CALENDAR DEBUG] Range bloccati (solo prenotazioni): {len(blocked_ranges)}")
        for i, (start, end) in enumerate(blocked_ranges, 1):
            logger.info(f"   [BLOCKED] Range {i}: {start} -> {end}")
        
        # Debug check-in dates
        logger.info(f"[CHECKIN] [CALENDAR DEBUG] Date check-in: {len(checkin_dates)}")
        for date_str in checkin_dates:
            logger.info(f"   [CHECKIN] {date_str}")
        
        # Debug check-out dates
        logger.info(f"[CHECKOUT] [CALENDAR DEBUG] Date check-out: {len(checkout_dates)}")
        for date_str in checkout_dates:
            logger.info(f"   [CHECKOUT] {date_str}")
        
        # Debug gap days
        logger.info(f"[GAP] [CALENDAR DEBUG] Gap days: {len(gap_days)}")
        if len(gap_days) <= 20:  # Mostra solo se non troppi
            for date_str in gap_days:
                logger.info(f"   [GAP] {date_str}")
        
        # Debug check-in bloccati da regole
        logger.info(f"[RULES] [CALENDAR DEBUG] Check-in bloccati da regole: {len(checkin_blocked_rules['dates'])} date, {len(checkin_blocked_rules['weekdays'])} weekdays")
        for date_str in checkin_blocked_rules['dates']:
            logger.info(f"   [RULE] Check-in bloccato: {date_str}")
        if checkin_blocked_rules['weekdays']:
            days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
            weekdays_str = [days[wd] for wd in checkin_blocked_rules['weekdays']]
            logger.info(f"   [RULE] Weekdays check-in bloccati: {', '.join(weekdays_str)}")
        
        # Debug check-out bloccati da regole
        logger.info(f"[RULES] [CALENDAR DEBUG] Check-out bloccati da regole: {len(checkout_blocked_rules['dates'])} date, {len(checkout_blocked_rules['weekdays'])} weekdays")
        for date_str in checkout_blocked_rules['dates']:
            logger.info(f"   [RULE] Check-out bloccato: {date_str}")
        if checkout_blocked_rules['weekdays']:
            days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
            weekdays_str = [days[wd] for wd in checkout_blocked_rules['weekdays']]
            logger.info(f"   [RULE] Weekdays check-out bloccati: {', '.join(weekdays_str)}")
        
        # Debug check-in bloccati da gap
        logger.info(f"[GAP_CHECKIN] [CALENDAR DEBUG] Check-in bloccati da gap: {len(checkin_blocked_gap)}")
        if len(checkin_blocked_gap) <= 20:  # Mostra solo se non troppi
            for date_str in checkin_blocked_gap:
                logger.info(f"   [GAP_CHECKIN] {date_str}")
        
        logger.info("[NEW_CALC] [CALENDAR DEBUG] === FINE RISULTATI NUOVI CALCOLI ===")
    
    def _debug_consolidated_ranges(self, consolidated_ranges):
        """Debug dei range consolidati."""
        logger.info("[CONSOLIDATE] [CALENDAR DEBUG] === RANGE CONSOLIDATI ===")
        logger.info(f"[CONSOLIDATE] [CALENDAR DEBUG] Range consolidati finali: {len(consolidated_ranges)}")
        for i, range_dict in enumerate(consolidated_ranges, 1):
            logger.info(f"   [CONSOLIDATE] Range {i}: {range_dict['from']} -> {range_dict['to']}")
        logger.info("[CONSOLIDATE] [CALENDAR DEBUG] === FINE RANGE CONSOLIDATI ===")
    
    def _debug_final_result(self, result):
        """Debug del risultato finale (supporta sia vecchia che nuova struttura)."""
        logger.info("[RESULT] [CALENDAR DEBUG] === RISULTATO FINALE ===")
        logger.info(f"[RESULT] [CALENDAR DEBUG] Listing ID: {result['listing_id']}")
        logger.info(f"[RESULT] [CALENDAR DEBUG] Range bloccati finali: {len(result['blocked_ranges'])}")
        
        # Nuova struttura
        if 'checkin_dates' in result:
            logger.info(f"[RESULT] [CALENDAR DEBUG] Check-in dates: {len(result['checkin_dates'])}")
            logger.info(f"[RESULT] [CALENDAR DEBUG] Check-out dates: {len(result['checkout_dates'])}")
            logger.info(f"[RESULT] [CALENDAR DEBUG] Gap days: {len(result['gap_days'])}")
            logger.info(f"[RESULT] [CALENDAR DEBUG] Check-in bloccati da regole: {len(result['checkin_blocked_rules']['dates'])}")
            logger.info(f"[RESULT] [CALENDAR DEBUG] Check-out bloccati da regole: {len(result['checkout_blocked_rules']['dates'])}")
            logger.info(f"[RESULT] [CALENDAR DEBUG] Check-in bloccati da gap: {len(result['checkin_blocked_gap'])}")
        # Vecchia struttura
        else:
            logger.info(f"[RESULT] [CALENDAR DEBUG] Giorni turnover: {len(result.get('turnover_days', []))}")
            logger.info(f"[RESULT] [CALENDAR DEBUG] Check-in bloccati: {len(result.get('checkin_block', {}).get('dates', []))}")
            logger.info(f"[RESULT] [CALENDAR DEBUG] Check-out bloccati: {len(result.get('checkout_block', {}).get('dates', []))}")
            logger.info(f"[RESULT] [CALENDAR DEBUG] Check-in reali: {len(result.get('real_checkin_dates', []))}")
        
        logger.info(f"[RESULT] [CALENDAR DEBUG] Gap tra prenotazioni: {result['metadata']['gap_between_bookings']}")
        logger.info(f"[RESULT] [CALENDAR DEBUG] Soggiorno minimo: {result['metadata']['min_stay']}")
        logger.info("[RESULT] [CALENDAR DEBUG] === FINE RISULTATO FINALE ===")
