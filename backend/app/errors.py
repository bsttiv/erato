"""Approved machine-readable API error catalog (decision 07, section 6)."""
STATUS = {
    "validation_error": 422, "email_taken": 409, "username_taken": 409,
    "invalid_credentials": 401, "not_authenticated": 401, "forbidden": 403,
    "not_found": 404, "version_conflict": 409, "already_member": 409,
    "owner_must_transfer": 409, "quota_exceeded": 422, "rate_limited": 429,
    "session_upstream_error": 502, "storage_unavailable": 503,
}


class APIError(Exception):
    def __init__(self, code, *, headers=None):
        self.code = code
        self.status = STATUS[code]
        self.headers = headers
        super().__init__(code)
