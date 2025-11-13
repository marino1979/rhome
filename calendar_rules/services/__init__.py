# calendar_rules/services/__init__.py
"""
Servizi per la gestione del calendario e disponibilità.

Questo modulo contiene i servizi specializzati per:
- CalendarService: Orchestrazione principale
- GapCalculator: Calcolo gap days
- RangeConsolidator: Gestione range bloccati
- QueryOptimizer: Ottimizzazione query database
"""

from .calendar_service import CalendarService
from .gap_calculator import GapCalculator
from .range_consolidator import RangeConsolidator
from .query_optimizer import QueryOptimizer
from .ical_sync import ICalSyncService
from .exceptions import (
    CalendarServiceError, 
    InvalidDateRangeError, 
    GapCalculationError,
    RangeConsolidationError,
    QueryOptimizationError
)

__all__ = [
    'CalendarService',
    'GapCalculator',
    'RangeConsolidator', 
    'QueryOptimizer',
    'ICalSyncService',
    'CalendarServiceError', 
    'InvalidDateRangeError',
    'GapCalculationError',
    'RangeConsolidationError',
    'QueryOptimizationError',
]
