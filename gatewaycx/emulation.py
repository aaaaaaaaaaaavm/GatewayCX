"""Repeatable socket-level HTTPS experiment for the GatewayCX native-Internet baseline.

The relay delays TCP payload bytes in each direction. It does not delay the local client-to-relay
TCP handshake, so the experiment observes real TLS 1.3 and HTTP/1.1 behaviour but is not a
packet-level Earth–Moon link emulator. That boundary is included in every generated record.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import http.server
import json
import platform
import queue
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .model import SPEED_OF_LIGHT_KM_S


@dataclass(frozen=True)
class EmulationConfig:
    distance_km: float = 384_400.0
    capacity_mbps: float = 100.0
    object_bytes: int = 65_536

    def validate(self) -> None:
        if self.distance_km < 0:
            raise ValueError("distance_km must be non-negative")
        if self.capacity_mbps <= 0:
            raise ValueError("capacity_mbps must be greater than zero")
        if self.object_bytes < 0:
            raise ValueError("object_bytes must be non-negative")

    @property
    def one_way_delay_s(self) -> float:
        return self.distance_km / SPEED_OF_LIGHT_KM_S


class _OriginHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "GatewayCXOrigin/0.1"

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        object_bytes = int(getattr(self.server, "object_bytes"))
        body = b"G" * object_bytes
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *args: object) -> None:
        return


class _ThreadingHTTPServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class DelayedByteRelay:
    """Bidirectional TCP relay with propagation and first-order serialization delay."""

    def __init__(self, target: tuple[str, int], one_way_delay_s: float, capacity_mbps: float):
        self.target = target
        self.one_way_delay_s = one_way_delay_s
        self.capacity_mbps = capacity_mbps
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen()
        self._listener.settimeout(0.2)
        self._stop = threading.Event()
        self._workers: list[threading.Thread] = []
        self._accept_thread = threading.Thread(target=self._accept, daemon=True)

    @property
    def address(self) -> tuple[str, int]:
        host, port = self._listener.getsockname()
        return str(host), int(port)

    def start(self) -> None:
        self._accept_thread.start()

    def close(self) -> None:
        self._stop.set()
        with contextlib.suppress(OSError):
            self._listener.close()
        self._accept_thread.join(timeout=1.0)
        for worker in self._workers:
            worker.join(timeout=1.0)

    def _accept(self) -> None:
        while not self._stop.is_set():
            try:
                client, _ = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            worker = threading.Thread(target=self._serve_connection, args=(client,), daemon=True)
            self._workers.append(worker)
            worker.start()

    def _serve_connection(self, client: socket.socket) -> None:
        try:
            upstream = socket.create_connection(self.target, timeout=5.0)
        except OSError:
            client.close()
            return
        threads = [
            threading.Thread(target=self._pump, args=(client, upstream), daemon=True),
            threading.Thread(target=self._pump, args=(upstream, client), daemon=True),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        client.close()
        upstream.close()

    def _pump(self, source: socket.socket, destination: socket.socket) -> None:
        pending: queue.Queue[tuple[float, bytes] | None] = queue.Queue()

        def send_scheduled() -> None:
            link_available_at = 0.0
            try:
                while True:
                    item = pending.get()
                    if item is None:
                        with contextlib.suppress(OSError):
                            destination.shutdown(socket.SHUT_WR)
                        return
                    received_at, data = item
                    serialization_s = len(data) * 8.0 / (
                        self.capacity_mbps * 1_000_000.0
                    )
                    link_available_at = max(received_at, link_available_at) + serialization_s
                    arrival_at = link_available_at + self.one_way_delay_s
                    time.sleep(max(0.0, arrival_at - time.monotonic()))
                    destination.sendall(data)
            except (ConnectionError, OSError):
                return

        sender = threading.Thread(target=send_scheduled, daemon=True)
        sender.start()
        try:
            while not self._stop.is_set():
                data = source.recv(65_536)
                if not data:
                    pending.put(None)
                    break
                pending.put((time.monotonic(), data))
        except (ConnectionError, OSError):
            pending.put(None)
        sender.join()


def _create_certificate(directory: Path) -> tuple[Path, Path]:
    if shutil.which("openssl") is None:
        raise RuntimeError("openssl is required for the HTTPS emulation")
    certificate = directory / "gatewaycx-cert.pem"
    key = directory / "gatewaycx-key.pem"
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-sha256",
            "-days", "1", "-subj", "/CN=gatewaycx.test", "-addext",
            "subjectAltName=DNS:gatewaycx.test", "-keyout", str(key), "-out", str(certificate),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return certificate, key


def _curl_transfers(url: str, certificate: Path, port: int, count: int) -> list[dict[str, Any]]:
    if shutil.which("curl") is None:
        raise RuntimeError("curl is required for the HTTPS emulation")
    command = [
        "curl", "--silent", "--show-error", "--noproxy", "*", "--tlsv1.3",
        "--tls-max", "1.3", "--cacert", str(certificate), "--resolve",
        f"gatewaycx.test:{port}:127.0.0.1", "--write-out", "%{json}\\n",
    ]
    for _ in range(count):
        command.extend(["--output", "/dev/null", url])
    completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
    return [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]


def _selected_metrics(raw: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "http_code", "http_version", "num_connects", "size_download", "ssl_verify_result",
        "time_connect", "time_appconnect", "time_starttransfer", "time_total",
    )
    return {key: raw[key] for key in keys}


def _first_version_line(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.splitlines()[0]


def run_https_experiment(config: EmulationConfig) -> dict[str, Any]:
    config.validate()
    with tempfile.TemporaryDirectory(prefix="gatewaycx-https-") as temporary_directory:
        temporary = Path(temporary_directory)
        certificate, key = _create_certificate(temporary)
        server = _ThreadingHTTPServer(("127.0.0.1", 0), _OriginHandler)
        server.object_bytes = config.object_bytes  # type: ignore[attr-defined]
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        context.load_cert_chain(certificate, key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        relay = DelayedByteRelay(
            ("127.0.0.1", int(server.server_port)), config.one_way_delay_s, config.capacity_mbps
        )
        relay.start()
        _, relay_port = relay.address
        url = f"https://gatewaycx.test:{relay_port}/object"
        try:
            cold = _curl_transfers(url, certificate, relay_port, 1)[0]
            reuse_pair = _curl_transfers(url, certificate, relay_port, 2)
        finally:
            relay.close()
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=1.0)

    record: dict[str, Any] = {
        "study_id": "S004",
        "title": "Unmodified HTTPS through a delayed cislunar byte relay",
        "evidence_class": "MEASUREMENT",
        "configuration": {
            **asdict(config),
            "one_way_delay_s": round(config.one_way_delay_s, 9),
            "ideal_round_trip_s": round(2 * config.one_way_delay_s, 9),
        },
        "protocol_under_test": "TLS 1.3 and HTTP/1.1 over a TCP byte stream",
        "client": "unmodified curl",
        "environment": {
            "generated_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "curl": _first_version_line(["curl", "--version"]),
            "openssl": _first_version_line(["openssl", "version"]),
        },
        "measurements": {
            "cold_connection": _selected_metrics(cold),
            "reuse_sequence_first": _selected_metrics(reuse_pair[0]),
            "reuse_sequence_second": _selected_metrics(reuse_pair[1]),
        },
        "checks": {
            "all_http_200": all(item["http_code"] == 200 for item in (cold, *reuse_pair)),
            "certificate_verified": all(
                item["ssl_verify_result"] == 0 for item in (cold, *reuse_pair)
            ),
            "second_request_reused_connection": reuse_pair[1]["num_connects"] == 0,
            "second_request_skipped_new_tls_handshake": reuse_pair[1]["time_appconnect"] == 0,
        },
        "limitations": [
            "The client-to-relay TCP handshake is local and is not delayed.",
            "The relay delays byte chunks; it does not emulate packets, loss, jitter or congestion control.",
            "The origin is a loopback test server, not a remote lunar or terrestrial endpoint.",
            "The measurement validates compatibility behaviour, not flight or hardware performance.",
        ],
    }
    record["checks"]["experiment_passed"] = all(record["checks"].values())
    return record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distance-km", type=float, default=384_400.0)
    parser.add_argument("--capacity-mbps", type=float, default=100.0)
    parser.add_argument("--object-bytes", type=int, default=65_536)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    record = run_https_experiment(
        EmulationConfig(args.distance_km, args.capacity_mbps, args.object_bytes)
    )
    rendered = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(rendered, end="")
    return 0 if record["checks"]["experiment_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
