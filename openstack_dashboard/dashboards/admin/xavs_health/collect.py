# XAVS_Health direct probes (no Prometheus, no Horizon token)

from __future__ import annotations
import os, socket, json
from typing import Any, Dict, List, Optional, Tuple

# Import *lazily* from Django; don't force configuration at import time
try:
    from django.conf import settings as dj_settings  # LazySettings proxy
except Exception:  # pragma: no cover
    dj_settings = None  # type: ignore

try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # type: ignore


# --------------------------- helpers ---------------------------

def _get_setting(name: str, default: Any = None) -> Any:
    """
    Safe accessor:
      - If Django settings are configured, read from them (with env/default fallback)
      - If not configured (e.g., ad-hoc python one-liners), use env/default only
    """
    # env always wins over default (and is used when Django isn't configured)
    env_val = os.environ.get(name, None)

    try:
        if dj_settings is not None and getattr(dj_settings, "configured", False):
            return getattr(dj_settings, name, env_val if env_val is not None else default)
    except Exception:
        pass  # fall back to env/default

    return env_val if env_val is not None else default


def _read_kolla_passwords() -> Dict[str, Any]:
    for p in ("/etc/kolla/passwords.yml", "/etc/kolla/passwords.yaml"):
        try:
            if os.path.exists(p):
                if yaml:
                    data = yaml.safe_load(open(p, "r")) or {}
                    return data if isinstance(data, dict) else {}
                out: Dict[str, Any] = {}
                with open(p, "r") as fh:
                    for line in fh:
                        if ":" in line and not line.strip().startswith("#"):
                            k, v = line.split(":", 1)
                            out[k.strip()] = v.strip().strip("'").strip('"')
                return out
        except Exception:
            pass
    return {}

def _tcp_reachable(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def _http_get_json(url: str, auth: Optional[Tuple[str, str]] = None, timeout: float = 3.0) -> Tuple[bool, Any]:
    if requests:
        try:
            r = requests.get(url, auth=auth, timeout=timeout)
            if r.status_code == 200:
                return True, r.json()
            return False, f"HTTP {r.status_code}"
        except Exception as e:
            return False, str(e)
    # urllib fallback
    try:
        from urllib.request import Request, build_opener, HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm
        req = Request(url)
        if auth:
            mgr = HTTPPasswordMgrWithDefaultRealm()
            mgr.add_password(None, url, auth[0], auth[1])
            opener = build_opener(HTTPBasicAuthHandler(mgr))
        else:
            opener = build_opener()
        with opener.open(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            if status == 200:
                import json as _json
                return True, _json.loads(resp.read().decode("utf-8", "ignore"))
            return False, f"HTTP {status}"
    except Exception as e:
        return False, str(e)


# --------------------------- targets ---------------------------

OS_HOST = _get_setting("XAVS_OS_HOST", "10.0.1.79")

DEFAULT_SERVICE_TARGETS: Dict[str, Tuple[str, int, str]] = {
    "keystone_api":   (OS_HOST, 5000, "Keystone API"),
    "glance_api":     (OS_HOST, 9292, "Glance API"),
    "cinder_api":     (OS_HOST, 8776, "Cinder API"),
    "nova_api":       (OS_HOST, 8774, "Nova API"),
    "placement_api":  (OS_HOST, 8778, "Placement API"),
    "neutron_api":    (OS_HOST, 9696, "Neutron API"),
    "heat_api":       (OS_HOST, 8004, "Heat API"),
    "heat_api_cfn":   (OS_HOST, 8000, "Heat API CFN"),
    "horizon":        (OS_HOST,   80, "Horizon"),
}

def _service_targets() -> Dict[str, Tuple[str, int, str]]:
    user_map = _get_setting("XAVS_SERVICE_TARGETS")
    if isinstance(user_map, dict):
        out: Dict[str, Tuple[str, int, str]] = {}
        for k, v in user_map.items():
            try:
                host, port, label = v
                out[k] = (str(host), int(port), str(label))
            except Exception:
                continue
        merged = dict(DEFAULT_SERVICE_TARGETS)
        merged.update(out)
        return merged
    return DEFAULT_SERVICE_TARGETS


# ------------------ OpenStack services (TCP) -------------------

def get_openstack_services() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for _name, (host, port, label) in _service_targets().items():
        ok = _tcp_reachable(host, port, 2.0)
        rows.append({
            "type": "api",
            "service": label,
            "host": f"{host}:{port}",
            "status": "up" if ok else "down",
        })
    return rows


# --------------------------- RabbitMQ --------------------------

def get_rabbitmq_status() -> Dict[str, Any]:
    """
    Returns a rich status payload, e.g.:
    {
      "cluster_up": True,
      "vhost_aliveness_ok": True/False/None,
      "object_totals": {"connections": 3, "channels": 6, "queues": 12, "consumers": 9},
      "queue_totals": {"messages": 42, "ready": 40, "unacked": 2},
      "message_stats": {"publish": 12345, "ack": 12340, "deliver_get": 12000},
      "mgmt_version": "3.12.1",
      "nodes": [
        {"name":"rabbit@ctrl1","type":"disc","up":True,
         "mem_used": 123456789, "mem_limit": 4294967296, "mem_alarm": False,
         "fd_used": 123, "fd_total": 4096,
         "sockets_used": 22, "sockets_total": 4096,
         "proc_used": 450, "proc_total": 32768,
         "disk_free": 9876543210, "disk_free_limit": 50000000, "disk_free_alarm": False,
         "partitions": 0, "uptime": 86400}
      ],
      "warnings": []
    }
    """
    status: Dict[str, Any] = {
        "cluster_up": False,
        "nodes": [],
        "object_totals": {},
        "queue_totals": {},
        "message_stats": {},
        "mgmt_version": None,
        "vhost_aliveness_ok": None,
        "warnings": [],
    }

    amqp_host = _get_setting("RABBITMQ_HOST", OS_HOST)
    amqp_port = int(_get_setting("RABBITMQ_PORT", 5672))
    if _tcp_reachable(amqp_host, amqp_port, 2.0):
        status["cluster_up"] = True
        status["nodes"].append({"node": f"{amqp_host}:{amqp_port}", "up": True})  # keep old lightweight row for compatibility

    pwd = _read_kolla_passwords()
    base = (_get_setting("RABBITMQ_MGMT_URL", f"http://{OS_HOST}:15672") or "").rstrip("/")
    user = _get_setting("RABBITMQ_USER", "openstack")
    password = _get_setting("RABBITMQ_PASSWORD", pwd.get("rabbitmq_password"))

    # Try to parse host:port from mgmt URL for TCP reachability
    try:
        hp = base.split("://", 1)[-1].split("/", 1)[0]
        mgmt_host = hp.split(":")[0]
        mgmt_port = int(hp.split(":")[1]) if ":" in hp else 80
    except Exception:
        mgmt_host, mgmt_port = OS_HOST, 15672

    if not (password and _tcp_reachable(mgmt_host, mgmt_port, 2.0)):
        return status

    def _get(path: str):
        return _http_get_json(f"{base}{path}", auth=(user, password))

    # /api/overview (totals, message_stats, mgmt version)
    ok, overview = _get("/api/overview")
    if ok and isinstance(overview, dict):
        status["object_totals"] = overview.get("object_totals") or {}
        status["queue_totals"] = overview.get("queue_totals") or {}
        # message_stats may be absent on idle brokers
        ms = overview.get("message_stats") or {}
        # Keep a few high-signal counters if present
        for k in ("publish", "ack", "deliver_get", "confirm", "deliver_no_ack"):
            if k in ms:
                status["message_stats"][k] = ms.get(k)
        status["mgmt_version"] = overview.get("management_version") or overview.get("rabbitmq_version")

    # /api/nodes (per-node health & resource usage)
    ok, nodes = _get("/api/nodes")
    if ok and isinstance(nodes, list):
        status["nodes"] = []
        for n in nodes:
            row = {
                "name": n.get("name"),
                "type": n.get("type"),  # 'disc' or 'ram'
                "up": bool(n.get("running", True)),
                "mem_used": n.get("mem_used"),
                "mem_limit": n.get("mem_limit"),
                "mem_alarm": bool(n.get("mem_alarm", False)),
                "fd_used": n.get("fd_used"),
                "fd_total": n.get("fd_total"),
                "sockets_used": n.get("sockets_used"),
                "sockets_total": n.get("sockets_total"),
                "proc_used": n.get("proc_used"),
                "proc_total": n.get("proc_total"),
                "disk_free": n.get("disk_free"),
                "disk_free_limit": n.get("disk_free_limit"),
                "disk_free_alarm": bool(n.get("disk_free_alarm", False)),
                "partitions": len(n.get("partitions") or []),
                "uptime": n.get("uptime"),  # ms in newer versions
            }
            status["nodes"].append(row)

    # Aliveness test on default vhost "/"
    ok, alive = _get("/api/aliveness-test/%2F")
    if ok and isinstance(alive, dict):
        status["vhost_aliveness_ok"] = (alive.get("status") == "ok")

    # Optional health checks (if plugin is enabled; safe to ignore failures)
    ok, alarms = _get("/api/health/checks/alarms")
    if ok and isinstance(alarms, dict):
        if alarms.get("status") not in (None, "ok"):
            status["warnings"].append(f"alarms: {alarms.get('status')}")

    ok, localalarms = _get("/api/health/checks/local-alarms")
    if ok and isinstance(localalarms, dict):
        if localalarms.get("status") not in (None, "ok"):
            status["warnings"].append(f"local-alarms: {localalarms.get('status')}")

    return status



# --------------------------- RabbitMQ --------------------------



# --------------------------- MariaDB ---------------------------


def get_mariadb_status() -> Dict[str, Any]:
    """
    Return a rich Galera/MariaDB status payload, e.g.
    {
      ready: bool,
      wsrep_ready: "Yes"/"No"/"Unknown",
      cluster_size: 3,
      wsrep_cluster_size: "3",
      cluster_status: "Primary",
      local_state_comment: "Synced",
      connected: True,
      flow_control_paused: 0.01,
      evs_state: "OPERATIONAL",
      provider_version: "3.45(rXXXX)",
      cluster_name: "pxc-prod",
      cluster_uuid: "1234-...",
      node_name: "mariadb01",
      local_index: 0,
      uptime: 123456,
      threads_connected: 20,
      incoming_addresses: ["10.0.1.81:4567","10.0.1.82:4567","10.0.1.83:4567"],
      nodes: [
        {"node": "10.0.1.81:4567", "reachable": True},
        {"node": "10.0.1.82:4567", "reachable": True},
        {"node": "10.0.1.83:4567", "reachable": False},
      ],
    }
    """
    out: Dict[str, Any] = {
        "wsrep_ready": "Unknown",
        "wsrep_cluster_size": "?",
        "ready": False,
        "cluster_size": None,
        "cluster_status": None,
        "local_state_comment": None,
        "connected": None,
        "flow_control_paused": None,
        "evs_state": None,
        "provider_version": None,
        "cluster_name": None,
        "cluster_uuid": None,
        "node_name": None,
        "local_index": None,
        "uptime": None,
        "threads_connected": None,
        "incoming_addresses": [],
        "nodes": [],
    }

    host = _get_setting("MARIADB_HOST", OS_HOST)
    port = int(_get_setting("MARIADB_PORT", 3306))
    user = _get_setting("MARIADB_USER", "root")

    pwdfile = _read_kolla_passwords()
    password = (
        _get_setting("MARIADB_PASSWORD") or
        os.environ.get("MARIADB_PASSWORD") or
        pwdfile.get("mariadb_root_password") or
        pwdfile.get("mysql_root_password") or
        pwdfile.get("database_password")
    )

    if not _tcp_reachable(host, port, 2.0) or not password:
        return out

    def _fill_from_rows(rows: List[Tuple[str, Any]]) -> None:
        kv = {str(k): str(v) for (k, v) in rows if k}
        # Booleans / enums
        wsrep_ready_val = (kv.get("wsrep_ready") or "").strip().lower()
        ready = wsrep_ready_val in ("on", "1", "true", "yes")
        out["wsrep_ready"] = "Yes" if ready else "No"
        out["ready"] = ready

        out["wsrep_cluster_size"] = kv.get("wsrep_cluster_size") or "?"
        try:
            out["cluster_size"] = int(out["wsrep_cluster_size"])
        except Exception:
            out["cluster_size"] = None

        out["cluster_status"] = kv.get("wsrep_cluster_status")  # e.g., Primary
        out["local_state_comment"] = kv.get("wsrep_local_state_comment")  # e.g., Synced
        out["connected"] = (kv.get("wsrep_connected", "").lower() in ("on", "1", "true", "yes"))
        out["flow_control_paused"] = float(kv.get("wsrep_flow_control_paused", "0") or 0)
        out["evs_state"] = kv.get("wsrep_evs_state")
        out["provider_version"] = kv.get("wsrep_provider_version")
        out["cluster_name"] = kv.get("wsrep_cluster_name")
        out["cluster_uuid"] = kv.get("wsrep_gcomm_uuid")
        out["node_name"] = kv.get("wsrep_node_name")
        try:
            out["local_index"] = int(kv.get("wsrep_local_index", "-1"))
        except Exception:
            out["local_index"] = None

        # Ops quick stats
        try:
            out["uptime"] = int(kv.get("Uptime", "0"))
        except Exception:
            pass
        try:
            out["threads_connected"] = int(kv.get("Threads_connected", "0"))
        except Exception:
            pass

        # Parse peers
        addrs_raw = kv.get("wsrep_incoming_addresses", "") or ""
        addrs = [a.strip() for a in addrs_raw.split(",") if a.strip()]
        out["incoming_addresses"] = addrs
        nodes = []
        for a in addrs:
            # If port missing, Galera uses 4567 (gcomm)
            if ":" in a:
                h, p = a.split(":", 1)
                try:
                    p = int(p)
                except Exception:
                    p = 4567
            else:
                h, p = a, 4567
            nodes.append({"node": f"{h}:{p}", "reachable": _tcp_reachable(h, int(p), 1.0)})
        out["nodes"] = nodes

    # Try PyMySQL first, then MySQLdb as a fallback
    def _query_with_pymysql():
        import pymysql  # type: ignore
        conn = pymysql.connect(host=host, port=port, user=user, password=password, connect_timeout=2, read_timeout=2)
        try:
            with conn.cursor() as cur:
                cur.execute("SHOW STATUS LIKE 'wsrep_%'")
                ws = cur.fetchall()
                cur.execute("SHOW GLOBAL STATUS LIKE 'Threads_connected'")
                ws += cur.fetchall()
                cur.execute("SHOW GLOBAL STATUS LIKE 'Uptime'")
                ws += cur.fetchall()
                cur.execute("SHOW VARIABLES LIKE 'wsrep_provider_version'")
                ws += cur.fetchall()
                cur.execute("SHOW VARIABLES LIKE 'wsrep_node_name'")
                ws += cur.fetchall()
            _fill_from_rows(ws)
        finally:
            conn.close()

    def _query_with_mysqlclient():
        import MySQLdb  # type: ignore
        conn = MySQLdb.connect(host=host, port=port, user=user, passwd=password, connect_timeout=2)
        try:
            cur = conn.cursor()
            cur.execute("SHOW STATUS LIKE 'wsrep_%'")
            ws = cur.fetchall()
            cur.execute("SHOW GLOBAL STATUS LIKE 'Threads_connected'")
            ws += cur.fetchall()
            cur.execute("SHOW GLOBAL STATUS LIKE 'Uptime'")
            ws += cur.fetchall()
            cur.execute("SHOW VARIABLES LIKE 'wsrep_provider_version'")
            ws += cur.fetchall()
            cur.execute("SHOW VARIABLES LIKE 'wsrep_node_name'")
            ws += cur.fetchall()
            _fill_from_rows(ws)
        finally:
            conn.close()

    try:
        _query_with_pymysql()
        return out
    except Exception:
        pass

    try:
        _query_with_mysqlclient()
    except Exception:
        pass

    return out



# --------------------------- Containers ------------------------

def get_container_status() -> List[Dict[str, Any]]:
    return []


# --------------------------- gather ----------------------------

def gather() -> Dict[str, Any]:
    ctx: Dict[str, Any] = {}
    errs: List[str] = []

    try:
        ctx["openstack_services"] = get_openstack_services()
    except Exception as e:
        errs.append(f"openstack_services: {e}")

    try:
        ctx["rabbitmq"] = get_rabbitmq_status()
    except Exception as e:
        errs.append(f"rabbitmq: {e}")

    try:
        ctx["mariadb"] = get_mariadb_status()
    except Exception as e:
        errs.append(f"mariadb: {e}")

    try:
        ctx["containers"] = get_container_status()
    except Exception as e:
        errs.append(f"containers: {e}")

    if errs:
        ctx["errors"] = errs
    return ctx
