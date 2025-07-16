import pytest

pytestmark = pytest.mark.integration


def test_roi_view_upgrades_ok(migrated_session):
    migrated_session.execute("SELECT 1 FROM v_roi_full LIMIT 1")
