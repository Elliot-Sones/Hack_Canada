import uuid

from app.models.entitlement import EntitlementResult
from app.services.job_service import _serialize_job_status


def test_serialize_job_status_falls_back_to_entitlement_compliance():
    row = EntitlementResult(
        id=uuid.uuid4(),
        scenario_run_id=uuid.uuid4(),
        overall_compliance="compliant",
        result_json={"variances": 0},
    )

    status = _serialize_job_status("entitlement_result", row)

    assert status.job_type == "entitlement_result"
    assert status.status == "compliant"
    assert status.result == {"variances": 0}
    assert status.started_at is None
    assert status.completed_at is None
