from datetime import date, timedelta
from types import SimpleNamespace
import pytest

from calendar_rules.services.calendar_service import CalendarService


class RuleStub(SimpleNamespace):
    """
    Semplice stub compatibile con gli attributi usati:
    - rule_type: 'no_checkin' | 'no_checkout'
    - recurrence_type: 'specific_date' | 'weekly'
    - specific_date: date | None
    - day_of_week: int | None (0=Lun .. 6=Dom)
    """
    pass


def make_service(listing_id=1, gap=0):
    listing = SimpleNamespace(id=listing_id, gap_between_bookings=gap, price_rules=None, closure_rules=None, checkinout_rules=None)
    return CalendarService(listing)


def fake_metadata(start, end):
    return {
        'start': start.isoformat(),
        'end': end.isoformat(),
        'window_days': (end - start).days,
        'max_stay': 30,
        'gap_between_bookings': 0,
    }


def run_with_calendar_data(svc, start, end, calendar_data):
    # Bypassa le query reali
    svc._get_optimized_calendar_data = lambda s, e: calendar_data
    svc._generate_metadata = lambda s, e: (fake_metadata(s, e) | {'min_stay': calendar_data.get('min_nights', 1)})
    return svc.get_unavailable_dates(start, end)


@pytest.mark.django_db
def test_gap0_turnover_allowed_when_no_rules():
    svc = make_service(gap=0)
    start, end = date(2025, 1, 1), date(2025, 1, 31)
    calendar_data = {
        'bookings': [{'check_in_date': date(2025, 1, 10), 'check_out_date': date(2025, 1, 15)}],
        'closures': [],
        'checkinout_rules': [],
        'price_rules': [{'min_nights': 1}],
        'gap_days': 0,
        'min_nights': 1,
        'start_date': start,
        'end_date': end,
        'gap_start_date': start,
    }
    res = run_with_calendar_data(svc, start, end, calendar_data)

    # Interni prenotazione 11..14
    assert res['blocked_ranges'] == [{'from': '2025-01-11', 'to': '2025-01-14'}]
    # Turnover al 15 (gap=0, nessuna regola no_checkin)
    assert res['turnover_days'] == ['2025-01-15']
    # Nessun blocco check-in "spurio" sul 10
    assert '2025-01-10' not in res['checkin_block']['dates']


@pytest.mark.django_db
def test_gap1_min3_blocks_and_no_turnover():
    svc = make_service(gap=1)
    start, end = date(2025, 1, 1), date(2025, 1, 31)
    calendar_data = {
        'bookings': [{'check_in_date': date(2025, 1, 10), 'check_out_date': date(2025, 1, 15)}],
        'closures': [],
        'checkinout_rules': [],
        'price_rules': [{'min_nights': 3}],
        'gap_days': 1,
        'min_nights': 3,
        'start_date': start,
        'end_date': end,
        'gap_start_date': start - timedelta(days=1),
    }
    res = run_with_calendar_data(svc, start, end, calendar_data)

    # Interno prenotazione 11..14
    assert res['blocked_ranges'] == [{'from': '2025-01-11', 'to': '2025-01-14'}]
    # Check-in bloccati: 8-9 (min_nights) e 15 (post-gap)
    expected = {'2025-01-08', '2025-01-09', '2025-01-15'}
    assert set(res['checkin_block']['dates']) == expected
    # Nessun turnover (gap=1)
    assert res['turnover_days'] == []


@pytest.mark.django_db
def test_turnover_blocked_by_weekly_no_checkin():
    svc = make_service(gap=0)
    start, end = date(2025, 1, 1), date(2025, 1, 31)
    # 2025-01-12 è Domenica (weekday=6)
    bookings = [{'check_in_date': date(2025, 1, 10), 'check_out_date': date(2025, 1, 12)}]
    rules = [RuleStub(rule_type='no_checkin', recurrence_type='weekly', specific_date=None, day_of_week=6)]
    calendar_data = {
        'bookings': bookings,
        'closures': [],
        'checkinout_rules': rules,
        'price_rules': [{'min_nights': 1}],
        'gap_days': 0,
        'min_nights': 1,
        'start_date': start,
        'end_date': end,
        'gap_start_date': start,
    }
    res = run_with_calendar_data(svc, start, end, calendar_data)

    # Interni: check-in 10, check-out 12 => interni 11..11
    assert res['blocked_ranges'] == [{'from': '2025-01-11', 'to': '2025-01-11'}]
    # Turnover sul 12 bloccato dalla regola no_checkin domenicale
    assert res['turnover_days'] == []
    # La regola weekly compare tra i weekdays bloccati
    assert res['checkin_block']['weekdays'] == [6]


@pytest.mark.django_db
def test_back_to_back_bookings_gap0_turnover_ok():
    svc = make_service(gap=0)
    start, end = date(2025, 1, 1), date(2025, 1, 31)
    calendar_data = {
        'bookings': [
            {'check_in_date': date(2025, 1, 10), 'check_out_date': date(2025, 1, 15)},
            {'check_in_date': date(2025, 1, 15), 'check_out_date': date(2025, 1, 20)},
        ],
        'closures': [],
        'checkinout_rules': [],
        'price_rules': [{'min_nights': 1}],
        'gap_days': 0,
        'min_nights': 1,
        'start_date': start,
        'end_date': end,
        'gap_start_date': start,
    }
    res = run_with_calendar_data(svc, start, end, calendar_data)
    # giorno di turnover valido
    assert '2025-01-15' in res['turnover_days']
    # niente blocco artificiale sul 15
    assert '2025-01-15' not in res['checkin_block']['dates']


@pytest.mark.django_db
def test_booking_checkout_day_before_window_gap_blocks_edge():
    svc = make_service(gap=2)
    start, end = date(2025, 1, 10), date(2025, 1, 20)
    calendar_data = {
        'bookings': [{'check_in_date': date(2025, 1, 1), 'check_out_date': date(2025, 1, 9)}],
        'closures': [],
        'checkinout_rules': [],
        'price_rules': [{'min_nights': 1}],
        'gap_days': 2,
        'min_nights': 1,
        'start_date': start,
        'end_date': end,
        'gap_start_date': start - timedelta(days=2),
    }
    res = run_with_calendar_data(svc, start, end, calendar_data)
    # Dopo checkout 9, con gap 2, blocca 9 e 10; nel range [10..20] vedo il 10 bloccato
    assert '2025-01-10' in res['checkin_block']['dates']


@pytest.mark.django_db
def test_weekly_no_checkin_overlaps_min_nights():
    svc = make_service(gap=0)
    start, end = date(2025, 2, 1), date(2025, 2, 28)
    # Prossimo check-in 2025-02-10 (Lunedì) con min_nights=4 ⇒ blocca 6..9
    rules = [RuleStub(rule_type='no_checkin', recurrence_type='weekly', specific_date=None, day_of_week=6)]  # Domenica
    calendar_data = {
        'bookings': [{'check_in_date': date(2025, 2, 10), 'check_out_date': date(2025, 2, 12)}],
        'closures': [],
        'checkinout_rules': rules,
        'price_rules': [{'min_nights': 4}],
        'gap_days': 0,
        'min_nights': 4,
        'start_date': start,
        'end_date': end,
        'gap_start_date': start,
    }
    res = run_with_calendar_data(svc, start, end, calendar_data)
    blocked = set(res['checkin_block']['dates'])
    assert {'2025-02-07', '2025-02-08', '2025-02-09'}.issubset(blocked)
    assert 6 in res['checkin_block']['weekdays']  # Domenica vietata in generale


@pytest.mark.django_db
def test_consolidation_with_closure_overlap():
    svc = make_service(gap=0)
    start, end = date(2025, 3, 1), date(2025, 3, 31)
    calendar_data = {
        'bookings': [{'check_in_date': date(2025, 3, 10), 'check_out_date': date(2025, 3, 16)}],  # interni 11..15
        'closures': [{'start_date': date(2025, 3, 14), 'end_date': date(2025, 3, 18)}],
        'checkinout_rules': [],
        'price_rules': [{'min_nights': 1}],
        'gap_days': 0,
        'min_nights': 1,
        'start_date': start,
        'end_date': end,
        'gap_start_date': start,
    }
    res = run_with_calendar_data(svc, start, end, calendar_data)
    # interni (11..15) ∪ chiusura (14..18) ⇒ consolidato (11..18)
    assert res['blocked_ranges'] == [{'from': '2025-03-11', 'to': '2025-03-18'}]
