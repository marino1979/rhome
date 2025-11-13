# calendar_rules/services/range_consolidator.py
"""
Servizio specializzato per il consolidamento e la gestione dei range di date.

Responsabilità:
- Consolidamento range sovrapposti
- Merge range adiacenti
- Gestione range vuoti o invalidi
- Ottimizzazione performance per range numerosi
"""

from datetime import date, timedelta
from typing import List, Tuple, Dict, Any
from .exceptions import RangeConsolidationError


class RangeConsolidator:
    """
    Servizio per consolidare e gestire i range di date.
    
    Un range è rappresentato come una tuple (start_date, end_date).
    """
    
    def __init__(self):
        """Inizializza il consolidatore."""
        pass
    
    def consolidate_ranges(self, ranges: List[Tuple[date, date]]) -> List[Tuple[date, date]]:
        """
        Consolida i range sovrapposti e adiacenti.
        
        Args:
            ranges: Lista di range da consolidare
            
        Returns:
            Lista di range consolidati
            
        Raises:
            RangeConsolidationError: Se i range non sono validi
        """
        if not ranges:
            return []
        
        # Valida i range di input
        self._validate_ranges(ranges)
        
        # Ordina i range per data di inizio
        sorted_ranges = sorted(ranges, key=lambda item: item[0])
        
        # Consolida i range
        consolidated = []
        current_start, current_end = sorted_ranges[0]
        
        for next_start, next_end in sorted_ranges[1:]:
            # Se il range successivo è sovrapposto o adiacente
            if next_start <= current_end + timedelta(days=1):
                # Merge i range
                current_end = max(current_end, next_end)
            else:
                # Range separato, salva il corrente e inizia il nuovo
                consolidated.append((current_start, current_end))
                current_start, current_end = next_start, next_end
        
        # Aggiungi l'ultimo range
        consolidated.append((current_start, current_end))
        
        return consolidated
    
    def consolidate_ranges_with_metadata(self, ranges: List[Tuple[date, date]]) -> List[Dict[str, Any]]:
        """
        Consolida i range e aggiunge metadata utili.
        
        Args:
            ranges: Lista di range da consolidare
            
        Returns:
            Lista di dict con range consolidati e metadata
        """
        consolidated_ranges = self.consolidate_ranges(ranges)
        
        result = []
        for start, end in consolidated_ranges:
            days_count = (end - start).days + 1
            
            result.append({
                'from': start.isoformat(),
                'to': end.isoformat(),
                'start_date': start,
                'end_date': end,
                'days_count': days_count,
                'duration_days': days_count
            })
        
        return result
    
    def merge_adjacent_ranges(self, ranges: List[Tuple[date, date]], 
                            max_gap_days: int = 1) -> List[Tuple[date, date]]:
        """
        Merge range che sono adiacenti o hanno un gap piccolo.
        
        Args:
            ranges: Lista di range da merge
            max_gap_days: Massimo numero di giorni di gap per considerare i range adiacenti
            
        Returns:
            Lista di range merge
        """
        if not ranges:
            return []
        
        self._validate_ranges(ranges)
        
        sorted_ranges = sorted(ranges, key=lambda item: item[0])
        merged = []
        current_start, current_end = sorted_ranges[0]
        
        for next_start, next_end in sorted_ranges[1:]:
            gap_days = (next_start - current_end).days - 1
            
            if gap_days <= max_gap_days:
                # Merge i range
                current_end = max(current_end, next_end)
            else:
                # Gap troppo grande, salva il corrente e inizia il nuovo
                merged.append((current_start, current_end))
                current_start, current_end = next_start, next_end
        
        # Aggiungi l'ultimo range
        merged.append((current_start, current_end))
        
        return merged
    
    def split_large_ranges(self, ranges: List[Tuple[date, date]], 
                         max_days: int = 30) -> List[Tuple[date, date]]:
        """
        Suddivide range troppo grandi in range più piccoli.
        
        Args:
            ranges: Lista di range da suddividere
            max_days: Massimo numero di giorni per range
            
        Returns:
            Lista di range suddivisi
        """
        if not ranges:
            return []
        
        self._validate_ranges(ranges)
        
        split_ranges = []
        
        for start, end in ranges:
            days_count = (end - start).days + 1
            
            if days_count <= max_days:
                # Range già abbastanza piccolo
                split_ranges.append((start, end))
            else:
                # Suddividi il range
                current_start = start
                while current_start <= end:
                    current_end = min(current_start + timedelta(days=max_days - 1), end)
                    split_ranges.append((current_start, current_end))
                    current_start = current_end + timedelta(days=1)
        
        return split_ranges
    
    def find_gaps_in_ranges(self, ranges: List[Tuple[date, date]], 
                          start_date: date, end_date: date) -> List[Tuple[date, date]]:
        """
        Trova i gap (periodi liberi) tra i range bloccati.
        
        Args:
            ranges: Lista di range bloccati
            start_date: Data di inizio del periodo di ricerca
            end_date: Data di fine del periodo di ricerca
            
        Returns:
            Lista di range che rappresentano i gap
        """
        if not ranges:
            return [(start_date, end_date)]
        
        self._validate_ranges(ranges)
        
        # Consolida i range bloccati
        blocked_ranges = self.consolidate_ranges(ranges)
        
        # Trova i gap
        gaps = []
        current_date = start_date
        
        for blocked_start, blocked_end in blocked_ranges:
            # Se c'è un gap prima del range bloccato
            if current_date < blocked_start:
                gap_end = min(blocked_start - timedelta(days=1), end_date)
                if current_date <= gap_end:
                    gaps.append((current_date, gap_end))
            
            # Avanza alla fine del range bloccato
            current_date = max(current_date, blocked_end + timedelta(days=1))
        
        # Se c'è un gap dopo l'ultimo range bloccato
        if current_date <= end_date:
            gaps.append((current_date, end_date))
        
        return gaps
    
    def get_range_statistics(self, ranges: List[Tuple[date, date]]) -> Dict[str, Any]:
        """
        Ottiene statistiche sui range.
        
        Args:
            ranges: Lista di range da analizzare
            
        Returns:
            Dict con statistiche
        """
        if not ranges:
            return {
                'total_ranges': 0,
                'total_days': 0,
                'average_range_length': 0,
                'longest_range': 0,
                'shortest_range': 0
            }
        
        self._validate_ranges(ranges)
        
        total_ranges = len(ranges)
        range_lengths = []
        total_days = 0
        
        for start, end in ranges:
            length = (end - start).days + 1
            range_lengths.append(length)
            total_days += length
        
        return {
            'total_ranges': total_ranges,
            'total_days': total_days,
            'average_range_length': total_days / total_ranges if total_ranges > 0 else 0,
            'longest_range': max(range_lengths) if range_lengths else 0,
            'shortest_range': min(range_lengths) if range_lengths else 0,
            'range_lengths': range_lengths
        }
    
    def _validate_ranges(self, ranges: List[Tuple[date, date]]) -> None:
        """
        Valida che i range siano corretti.
        
        Args:
            ranges: Lista di range da validare
            
        Raises:
            RangeConsolidationError: Se i range non sono validi
        """
        for i, (start, end) in enumerate(ranges):
            if not isinstance(start, date) or not isinstance(end, date):
                raise RangeConsolidationError(f"Range {i}: start e end devono essere istanze di date")
            
            if start > end:
                raise RangeConsolidationError(f"Range {i}: start ({start}) deve essere <= end ({end})")
    
    def optimize_ranges_for_api(self, ranges: List[Tuple[date, date]]) -> List[Dict[str, str]]:
        """
        Ottimizza i range per l'output API.
        
        Args:
            ranges: Lista di range da ottimizzare
            
        Returns:
            Lista di dict ottimizzati per API
        """
        consolidated = self.consolidate_ranges(ranges)
        
        return [
            {
                'from': start.isoformat(),
                'to': end.isoformat()
            }
            for start, end in consolidated
        ]

