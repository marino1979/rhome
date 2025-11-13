"""
Servizio per sincronizzare calendari esterni tramite iCal.
Scarica i file iCal, li parsa e crea ClosureRule per bloccare le date occupate.
"""

import logging
import requests
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional
from django.utils import timezone
from django.db import transaction

try:
    from icalendar import Calendar
    ICALENDAR_AVAILABLE = True
except ImportError:
    ICALENDAR_AVAILABLE = False
    Calendar = None

from ..models import ExternalCalendar, ClosureRule
from .exceptions import CalendarServiceError

logger = logging.getLogger('calendar_debug')


class ICalSyncService:
    """
    Servizio per sincronizzare un calendario esterno tramite iCal.
    """
    
    def __init__(self, external_calendar: ExternalCalendar):
        """
        Inizializza il servizio per un calendario esterno.
        
        Args:
            external_calendar: Istanza di ExternalCalendar da sincronizzare
        """
        self.external_calendar = external_calendar
        self.listing = external_calendar.listing
    
    def sync(self) -> Tuple[bool, Optional[str]]:
        """
        Sincronizza il calendario esterno.
        
        Returns:
            Tuple (success, error_message)
        """
        if not ICALENDAR_AVAILABLE:
            return False, "Libreria icalendar non installata. Esegui: pip install icalendar"
        
        if not self.external_calendar.is_active:
            logger.info(f"[ICAL] Calendario {self.external_calendar.name} non attivo, skip sincronizzazione")
            return False, "Calendario non attivo"
        
        try:
            # Scarica il file iCal
            ical_data = self._download_ical()
            
            # Parsa il file iCal
            blocked_ranges = self._parse_ical(ical_data)
            
            # Aggiorna le ClosureRule
            self._update_closure_rules(blocked_ranges)
            
            # Aggiorna lo stato della sincronizzazione
            self.external_calendar.last_sync = timezone.now()
            self.external_calendar.last_sync_status = 'success'
            self.external_calendar.last_sync_error = ''
            self.external_calendar.save()
            
            logger.info(f"[ICAL] Sincronizzazione completata per {self.external_calendar.name}: {len(blocked_ranges)} periodi bloccati")
            return True, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[ICAL] Errore sincronizzazione {self.external_calendar.name}: {error_msg}")
            
            # Salva l'errore
            self.external_calendar.last_sync = timezone.now()
            self.external_calendar.last_sync_status = 'error'
            self.external_calendar.last_sync_error = error_msg
            self.external_calendar.save()
            
            return False, error_msg
    
    def _download_ical(self) -> bytes:
        """
        Scarica il file iCal dall'URL configurato.
        
        Returns:
            Contenuto del file iCal in bytes
            
        Raises:
            CalendarServiceError: Se il download fallisce
        """
        try:
            logger.info(f"[ICAL] Download iCal da {self.external_calendar.ical_url}")
            
            # Timeout di 30 secondi
            response = requests.get(
                self.external_calendar.ical_url,
                timeout=30,
                headers={
                    'User-Agent': 'RhomeBook-iCal-Sync/1.0'
                }
            )
            response.raise_for_status()
            
            logger.info(f"[ICAL] Download completato: {len(response.content)} bytes")
            return response.content
            
        except requests.exceptions.RequestException as e:
            raise CalendarServiceError(f"Errore download iCal: {str(e)}")
    
    def _parse_ical(self, ical_data: bytes) -> List[Tuple[date, date]]:
        """
        Parsa il file iCal e estrae i periodi bloccati.
        
        Args:
            ical_data: Contenuto del file iCal in bytes
            
        Returns:
            Lista di tuple (start_date, end_date) per i periodi bloccati
            
        Raises:
            CalendarServiceError: Se il parsing fallisce
        """
        try:
            # Parsa il calendario iCal
            calendar = Calendar.from_ical(ical_data)
            
            blocked_ranges: List[Tuple[date, date]] = []
            
            # Itera su tutti gli eventi nel calendario
            for component in calendar.walk('VEVENT'):
                # Estrai date inizio e fine
                dtstart = component.get('dtstart')
                dtend = component.get('dtend')
                
                if not dtstart or not dtend:
                    continue
                
                # Converti in date Python
                start_date = self._to_date(dtstart.dt)
                end_date = self._to_date(dtend.dt)
                
                # Salta eventi nel passato (oltre 1 anno fa)
                if end_date < date.today() - timedelta(days=365):
                    continue
                
                # Salta eventi troppo nel futuro (oltre 2 anni)
                if start_date > date.today() + timedelta(days=730):
                    continue
                
                # Estrai status e summary per determinare se è una prenotazione
                status = str(component.get('status', '')).upper()
                summary = str(component.get('summary', '')).upper()
                
                # Considera come prenotazione se:
                # - Status è CONFIRMED o mancante
                # - Summary contiene parole chiave come "RESERVED", "BOOKED", "OCCUPIED", ecc.
                # - O se non c'è status/summary, assumiamo che sia una prenotazione
                is_booking = (
                    status in ['CONFIRMED', ''] or
                    any(keyword in summary for keyword in ['RESERVED', 'BOOKED', 'OCCUPIED', 'BLOCKED', 'RENTAL'])
                )
                
                if is_booking:
                    # Aggiungi 1 giorno alla fine per includere il giorno di check-out
                    # (iCal tipicamente include solo fino al check-out escluso)
                    blocked_ranges.append((start_date, end_date))
                    logger.debug(f"[ICAL] Prenotazione trovata: {start_date} -> {end_date}")
            
            logger.info(f"[ICAL] Parsing completato: {len(blocked_ranges)} periodi bloccati trovati")
            return blocked_ranges
            
        except Exception as e:
            raise CalendarServiceError(f"Errore parsing iCal: {str(e)}")
    
    def _to_date(self, dt) -> date:
        """
        Converte un datetime/date in date Python.
        
        Args:
            dt: datetime o date da convertire
            
        Returns:
            date Python
        """
        if isinstance(dt, date):
            return dt
        elif isinstance(dt, datetime):
            return dt.date()
        else:
            # Prova a convertire stringa
            return datetime.fromisoformat(str(dt)).date()
    
    @transaction.atomic
    def _update_closure_rules(self, blocked_ranges: List[Tuple[date, date]]):
        """
        Aggiorna le ClosureRule con i periodi bloccati dal calendario esterno.
        
        Rimuove le ClosureRule esistenti create da questo calendario e ne crea di nuove.
        
        Args:
            blocked_ranges: Lista di tuple (start_date, end_date) per i periodi bloccati
        """
        # Rimuovi le ClosureRule esistenti create da questo calendario
        # Usiamo il campo is_external_booking=True e il nome del calendario nella reason
        # per identificare le regole create da questo calendario
        existing_rules = ClosureRule.objects.filter(
            listing=self.listing,
            is_external_booking=True,
            reason__startswith=f"[{self.external_calendar.name}]"
        )
        count_deleted = existing_rules.count()
        existing_rules.delete()
        logger.info(f"[ICAL] Rimosse {count_deleted} ClosureRule esistenti")
        
        # Crea nuove ClosureRule per ogni periodo bloccato
        created_count = 0
        for start_date, end_date in blocked_ranges:
            # Verifica che il range sia valido
            if start_date >= end_date:
                logger.warning(f"[ICAL] Range non valido saltato: {start_date} -> {end_date}")
                continue
            
            # Crea la ClosureRule
            ClosureRule.objects.create(
                listing=self.listing,
                start_date=start_date,
                end_date=end_date,
                is_external_booking=True,
                reason=f"[{self.external_calendar.name}] Sincronizzato da {self.external_calendar.provider}"
            )
            created_count += 1
        
        logger.info(f"[ICAL] Create {created_count} nuove ClosureRule")
    
    @staticmethod
    def sync_all_active():
        """
        Sincronizza tutti i calendari esterni attivi che necessitano di sincronizzazione.
        
        Returns:
            Dict con statistiche della sincronizzazione
        """
        active_calendars = ExternalCalendar.objects.filter(is_active=True)
        
        stats = {
            'total': active_calendars.count(),
            'synced': 0,
            'skipped': 0,
            'errors': 0,
        }
        
        for calendar in active_calendars:
            if not calendar.needs_sync():
                stats['skipped'] += 1
                logger.info(f"[ICAL] Calendario {calendar.name} non necessita sincronizzazione")
                continue
            
            service = ICalSyncService(calendar)
            success, error = service.sync()
            
            if success:
                stats['synced'] += 1
            else:
                stats['errors'] += 1
                logger.error(f"[ICAL] Errore sincronizzazione {calendar.name}: {error}")
        
        logger.info(f"[ICAL] Sincronizzazione completata: {stats}")
        return stats

