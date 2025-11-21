from services.api.app.decision.models import DecisionTaskRecord, PlannedDecisionTask
from services.api.routes import decision_serializers


def test_serialize_task_maps_state():
    record = DecisionTaskRecord.from_mapping(
        {
            "id": "t1",
            "source": "decision_engine",
            "entity": {"type": "sku_vendor", "asin": "A1"},
            "decision": "request_price",
            "priority": 80,
            "state": "pending",
            "why": [],
            "alternatives": [],
        }
    )
    serialized = decision_serializers.serialize_task(record)
    assert serialized.state == "open"
    assert serialized.entity["asin"] == "A1"


def test_serialize_planned_uses_surrogate_state():
    planned = PlannedDecisionTask(
        asin="A2",
        vendor_id=2,
        decision="continue",
        priority=10,
        summary="ok",
        default_action=None,
        why=[],
        alternatives=[],
    )
    planned.entity = {"type": "sku_vendor", "asin": "A2", "vendor_id": 2}
    serialized = decision_serializers.serialize_planned(planned, 1)
    assert serialized.id.startswith("planned-1-")
    assert serialized.state == "pending" or serialized.state == "open"


def test_derive_summary_maps_counts():
    raw = {"pending": 2, "dismissed": 1, "expired": 1, "snoozed": 3}
    summary = decision_serializers.derive_summary(raw)
    assert summary.pending == 2
    assert summary.blocked == 1
    assert summary.in_progress == 3
