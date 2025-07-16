import pytest

pytestmark = pytest.mark.integration


def test_roi_views(migrated_session):
    migrated_session.execute("SELECT 1 FROM v_roi_full LIMIT 1")
    migrated_session.execute("SELECT 1 FROM roi_view LIMIT 1")
