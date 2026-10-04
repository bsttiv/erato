import pytest
from app.core.errors import ForbiddenError, GoneError, PlanGateError


def test_plan_gate_error_properties_and_serialization():
    err = PlanGateError(code="plan_gate_sharing")
    assert isinstance(err, ForbiddenError)
    assert err.status_code == 403
    assert err.code == "plan_gate_sharing"

    payload = err.to_dict()
    assert payload["error"] == "plan_gate_sharing"
    assert "message" in payload
    assert "detail" in payload


def test_gone_error_properties_and_serialization():
    err = GoneError(code="invitation_expired")
    assert err.status_code == 410
    assert err.code == "invitation_expired"

    payload = err.to_dict()
    assert payload["error"] == "invitation_expired"
    assert "message" in payload
