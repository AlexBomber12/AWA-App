from typing import Mapping, Optional, Any
from urllib.parse import quote, urlencode

DEFAULT_PORT = {"postgresql": 5432, "postgres": 5432, "mysql": 3306, "mariadb": 3306, "redis": 6379, "amqp": 5672}

def _bracket_ipv6(host: str) -> str:
    if ":" in host and not (host.startswith("[") and host.endswith("]")):
        return f"[{host}]"
    return host

def build_dsn(
    scheme: str,
    host: str = "localhost",
    port: Optional[int | str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None,
    params: Optional[Mapping[str, Any]] = None,
) -> str:
    auth = ""
    if user:
        u = quote(str(user))
        if password is not None:
            auth = f"{u}:{quote(str(password))}@"
        else:
            auth = f"{u}@"
    h = _bracket_ipv6(host)
    eff = int(port) if port not in (None, "", 0) else DEFAULT_PORT.get(scheme)
    p = f":{eff}" if eff else ""
    db = f"/{database}" if database else ""
    q = ""
    if params:
        q = "?" + urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
    return f"{scheme}://{auth}{h}{p}{db}{q}"

__all__ = ["build_dsn"]
