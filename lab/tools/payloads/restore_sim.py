#!/usr/bin/env python3
"""Isolation-check payload: simulates a restored site's runtime misbehavior.

Runs INSIDE a bwrap namespace (--unshare-all) with a read-only root skeleton,
a cleared environment, a fresh PID namespace and a single writable docroot
mounted at /site. It attempts the actions an unsafe restored site or a
compromised payload would try — external egress (HTTP/SMTP/FTP/webhook
stand-ins), DNS resolution, writes outside its docroot, reads of host files
and inspection of its environment/process table — and reports each outcome
as JSON on stdout. Every hostile attempt is expected to FAIL inside the
namespace; the harness turns observed failures into tested-pass verdicts and
any success into tested-fail.

The first stdout line is the WOV-PAYLOAD-START marker: it lets the harness
distinguish "the payload started and produced bad results" (tested-fail)
from "the namespace never executed the payload" (blocked setup, not a
demonstrated isolation result).

    restore_sim.py --host-file PATH --marker-env NAME
"""
import argparse
import json
import os
import socket
import sys

PREAMBLE = "WOV-PAYLOAD-START"
WORKDIR = "/site"

# Documentation-range stand-ins for lab topology roles plus the external
# services AC-26 requires to stay unreachable (SMTP, webhook/payment).
EGRESS_ATTEMPTS = [
    ("tcp", "192.0.2.10", 80, "source-role http"),
    ("tcp", "198.51.100.20", 443, "storage-s3 https"),
    ("tcp", "198.51.100.30", 21, "storage-ftp control"),
    ("tcp", "203.0.113.5", 25, "external smtp"),
    ("tcp", "203.0.113.9", 443, "payment/webhook https"),
    ("dns", "smtp.example.test", None, "smtp hostname resolution"),
    ("dns", "hooks.example.test", None, "webhook hostname resolution"),
]

WRITE_ATTEMPTS = [
    (f"{WORKDIR}/payload-write.txt", True, "write inside docroot (allowed)"),
    ("/escape-marker.txt", False, "write to filesystem root"),
    ("/etc/payload-marker", False, "write into /etc"),
    ("/usr/payload-marker", False, "write into /usr"),
    (f"{WORKDIR}/../escape2.txt", False, "docroot parent traversal"),
    ("/tmp/payload-marker", False, "write into /tmp"),
    ("/proc/payload-marker", False, "write into /proc"),
]

# Host paths that must not exist inside the narrowed mount namespace: a file
# planted by the harness outside every bind, plus well-known host files.
HOST_READ_ATTEMPTS = [
    ("/etc/shadow", "host account database"),
    ("/etc/hostname", "host identity file"),
    ("/proc/1/root/etc/hostname", "monitor process root"),
]

# Environment variable names the confined payload may legitimately see; the
# harness sets a marker variable outside the sandbox that must never appear.
ENV_ALLOW = {"PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "PWD", "TMPDIR"}


def try_tcp(host, port, timeout=3):
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return {"reached": True}
    except OSError as exc:
        return {"reached": False, "error": f"{type(exc).__name__}:{exc}"}


def try_dns(name):
    try:
        infos = socket.getaddrinfo(name, None)
        return {"resolved": True, "addresses": sorted({i[4][0] for i in infos})}
    except OSError as exc:
        return {"resolved": False, "error": f"{type(exc).__name__}:{exc}"}


def try_write(path):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("payload\n")
        return {"wrote": True}
    except OSError as exc:
        return {"wrote": False, "error": f"{type(exc).__name__}:{exc}"}


def try_read(path, label, shown=None):
    """Attempt to read a host path; report only reachability, never content.
    `shown` masks the reported path so a workstation-private absolute path
    cannot leak into retained evidence."""
    try:
        with open(path, "rb") as fh:
            data = fh.read(64)
        return {"path": shown or path, "label": label, "read": True,
                "bytes": len(data)}
    except OSError as exc:
        return {"path": shown or path, "label": label, "read": False,
                "error": f"{type(exc).__name__}:{exc}"}


def process_table():
    pids = sorted(int(p) for p in os.listdir("/proc") if p.isdigit())
    self_pid = os.getpid()
    return {"pids": pids, "self_pid": self_pid, "count": len(pids),
            "beyond_sandbox": [p for p in pids if p > 2]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host-file", default=None,
                        help="host path planted by the harness; must be unreachable")
    parser.add_argument("--marker-env", default=None,
                        help="env var name set by the harness outside; must be absent")
    args = parser.parse_args()

    print(PREAMBLE, flush=True)
    reads = [try_read(p, l) for p, l in HOST_READ_ATTEMPTS]
    if args.host_file:
        reads.insert(0, try_read(args.host_file,
                                 "harness-planted host sentinel",
                                 shown="<host-sentinel>"))

    env_names = sorted(os.environ)
    result = {
        "netns": os.readlink("/proc/self/ns/net"),
        "mntns": os.readlink("/proc/self/ns/mnt"),
        "pidns": os.readlink("/proc/self/ns/pid"),
        "egress": [],
        "writes": [],
        "reads": reads,
        "env": {
            "names": env_names,
            "marker_env": args.marker_env,
            "marker_env_seen": bool(args.marker_env)
            and args.marker_env in os.environ,
            "unexpected": [n for n in env_names if n not in ENV_ALLOW],
        },
        "procs": process_table(),
    }
    for kind, host, port, label in EGRESS_ATTEMPTS:
        if kind == "tcp":
            outcome = try_tcp(host, port)
            result["egress"].append({"target": f"{host}:{port}", "label": label, **outcome})
        else:
            outcome = try_dns(host)
            result["egress"].append({"target": host, "label": label, **outcome})
    for path, allowed, label in WRITE_ATTEMPTS:
        outcome = try_write(path)
        result["writes"].append({"path": path, "label": label,
                                 "allowed": allowed, **outcome})
    json.dump(result, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
