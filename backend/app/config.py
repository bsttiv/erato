"""Environment configuration, validated before the application starts."""
import os

REQUIRED = ("MONGODB_URI", "MONGODB_DB", "MAESTRO_URL", "MAESTRO_API_KEY")
OPTIONAL = ("INVITATION_TTL", "CLOUDINARY_URL")


def load_config():
    config = {}
    for name in REQUIRED:
        value = os.environ.get(name)
        if not value:
            raise ValueError(f"Missing required variable: {name}")
        config[name] = value
    # Optional so the application starts without credentials; demos answer 503 until it is set.
    config["CLOUDINARY_URL"] = os.environ.get("CLOUDINARY_URL", "")
    ttl = os.environ.get("INVITATION_TTL", "7d")
    if not ttl.endswith("d") or not ttl[:-1].isdigit() or int(ttl[:-1]) < 1:
        raise ValueError("Invalid INVITATION_TTL: expected a positive duration such as 7d")
    config["INVITATION_TTL"] = int(ttl[:-1]) * 86400
    return config
