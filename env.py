import os


def load_dotenv(path=".env"):
    """Minimal .env loader — no pip package needed. Only sets a variable
    if it isn't already set in the real environment, so real env vars
    (e.g. set by a host like Render/Railway) always take priority."""
    if not os.path.exists(path):
        return
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value
