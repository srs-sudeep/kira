"""Dashboard service unit tests (pure math + status mapping)."""

from app.services.dashboard_service import _map_channel_status, _pct_change


def test_pct_change():
    assert _pct_change(10.0, 5.0) == 100.0
    assert _pct_change(5.0, 10.0) == -50.0
    assert _pct_change(0.0, 0.0) == 0.0


def test_map_channel_status():
    assert _map_channel_status("connected") == "synced"
    assert _map_channel_status("error") == "failed"
