"""Deployment evidence must reject count and aggregate mismatches."""
from copy import deepcopy
import pytest
from scripts.check_deployment import verify_data_statistics


@pytest.fixture
def records_and_summary():
    rows = [{'id': 'a', 'date': '2026-01-01', 'value': 1},
            {'id': 'b', 'date': '2026-01-03', 'value': 2.5}]
    summary = {'count': 2, 'period': {'start': '2026-01-01', 'end': '2026-01-03'},
               'metrics': {'total': 3.5, 'average': 1.75, 'max': 2.5, 'min': 1}}
    return rows, summary


def test_matching_statistics(records_and_summary):
    rows, summary = records_and_summary
    assert verify_data_statistics(rows, summary)['period_and_statistics_match']


@pytest.mark.parametrize('field', ['total', 'average', 'max', 'min'])
def test_wrong_statistics_are_rejected(records_and_summary, field):
    rows, summary = deepcopy(records_and_summary)
    summary['metrics'][field] += 1
    with pytest.raises(AssertionError):
        verify_data_statistics(rows, summary)


def test_duplicate_rows_are_not_count_evidence(records_and_summary):
    rows, summary = records_and_summary
    with pytest.raises(AssertionError):
        verify_data_statistics([rows[0], rows[0]], summary)


def test_wrong_count_is_rejected(records_and_summary):
    rows, summary = records_and_summary
    summary['count'] = 120
    with pytest.raises(AssertionError):
        verify_data_statistics(rows, summary)


def test_wrong_period_is_rejected(records_and_summary):
    rows, summary = records_and_summary
    summary['period']['end'] = '2026-12-31'
    with pytest.raises(AssertionError):
        verify_data_statistics(rows, summary)
