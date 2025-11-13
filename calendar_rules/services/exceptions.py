# calendar_rules/services/exceptions.py
"""
Eccezioni custom per i servizi calendario.
"""


class CalendarServiceError(Exception):
    """Base exception per errori del calendario."""
    pass


class InvalidDateRangeError(CalendarServiceError):
    """Errore quando il range di date non è valido."""
    pass


class GapCalculationError(CalendarServiceError):
    """Errore durante il calcolo dei gap days."""
    pass


class RangeConsolidationError(CalendarServiceError):
    """Errore durante il consolidamento dei range."""
    pass


class QueryOptimizationError(CalendarServiceError):
    """Errore durante l'ottimizzazione delle query."""
    pass

