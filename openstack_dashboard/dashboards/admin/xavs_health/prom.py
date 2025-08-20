import json, ssl, urllib.parse, urllib.request
from base64 import b64encode
from django.conf import settings

def _base():
    return getattr(settings, "PROMETHEUS_BASE", "").rstrip("/")

def _auth_headers():
    h = {"Accept": "application/json"}
    # Basic
    basic = getattr(settings, "PROMETHEUS_BASIC_AUTH", None)
    if isinstance(basic, (list, tuple)) and len(basic) == 2:
        raw = f"{basic[0]}:{basic[1]}".encode("utf-8")
        h["Authorization"] = "Basic " + b64encode(raw).decode("ascii")
    # Bearer (optional)
    token = getattr(settings, "PROMETHEUS_BEARER", None)
    if token and "Authorization" not in h:
        h["Authorization"] = f"Bearer {token}"
    # Extra headers (optional)
    extra = getattr(settings, "PROMETHEUS_EXTRA_HEADERS", None)
    if isinstance(extra, dict):
        h.update(extra)
    return h

def _open(url):
    verify = getattr(settings, "PROMETHEUS_VERIFY_TLS", True)
    ctx = None
    if not verify:
        ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers=_auth_headers())
    return urllib.request.urlopen(req, timeout=4, context=ctx) if ctx else urllib.request.urlopen(req, timeout=4)

def _q(query):
    base = _base()
    if not base:
        return None
    url = f"{base}/api/v1/query?{urllib.parse.urlencode({'query': query})}"
    try:
        with _open(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                return data["data"]["result"]
    except Exception:
        return None
    return None

def vector_int(query, default=0):
    res = _q(query)
    try:
        if res and len(res) > 0:
            return int(float(res[0]["value"][1]))
    except Exception:
        pass
    return default

def vector_map(query):
    res = _q(query) or []
    out = []
    for r in res:
        labels = r.get("metric", {})
        val = r.get("value", [None, "0"])[1]
        out.append((labels, val))
    return out