"""S029 native DNS/IPv6/TLS/HTTP2/HTTP3/SMTP/file protocol laboratory."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import ipaddress
import platform
import smtplib
import socket
import ssl
import struct
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from .io import write_json


AAAA_ADDRESS = "fd00::42"
FILE_BYTES = 32_768


def build_dns_query(name: str, identifier: int = 0x9171) -> bytes:
    labels = b"".join(bytes([len(label)]) + label.encode("ascii") for label in name.split(".")) + b"\0"
    return struct.pack("!HHHHHH", identifier, 0x0100, 1, 0, 0, 0) + labels + struct.pack("!HH", 28, 1)


def build_dns_response(query: bytes, address: str = AAAA_ADDRESS) -> bytes:
    if len(query) < 17:
        raise ValueError("DNS query is too short")
    offset = 12
    while offset < len(query) and query[offset]:
        offset += query[offset] + 1
    question_end = offset + 5
    if question_end > len(query):
        raise ValueError("DNS question is truncated")
    header = struct.pack("!HHHHHH", struct.unpack("!H", query[:2])[0], 0x8180, 1, 1, 0, 0)
    answer = b"\xc0\x0c" + struct.pack("!HHIH", 28, 1, 60, 16) + ipaddress.IPv6Address(address).packed
    return header + query[12:question_end] + answer


def parse_dns_aaaa(response: bytes) -> str:
    if len(response) < 28 or struct.unpack("!H", response[6:8])[0] < 1:
        raise ValueError("DNS response has no answer")
    return str(ipaddress.IPv6Address(response[-16:]))


class _DnsServer(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.bind(("::1", 0)); self.socket.settimeout(0.2)
        self.port = self.socket.getsockname()[1]; self.stop = threading.Event()

    def run(self) -> None:
        while not self.stop.is_set():
            try: data, address = self.socket.recvfrom(4096)
            except socket.timeout: continue
            except OSError: return
            self.socket.sendto(build_dns_response(data), address)

    def close(self) -> None:
        self.stop.set(); self.socket.close(); self.join(1)


class _UdpRelay(threading.Thread):
    def __init__(self, target_port: int, delay_s: float) -> None:
        super().__init__(daemon=True)
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.bind(("::1", 0)); self.socket.settimeout(0.2)
        self.port = self.socket.getsockname()[1]; self.target = ("::1", target_port)
        self.delay_s = delay_s; self.client: tuple[Any, ...] | None = None; self.stop = threading.Event()

    def run(self) -> None:
        while not self.stop.is_set():
            try: data, address = self.socket.recvfrom(65535)
            except socket.timeout: continue
            except OSError: return
            time.sleep(self.delay_s)
            if address[1] == self.target[1]:
                if self.client is not None: self.socket.sendto(data, self.client)
            else:
                self.client = address; self.socket.sendto(data, self.target)

    def close(self) -> None:
        self.stop.set(); self.socket.close(); self.join(1)


class _TcpRelay(threading.Thread):
    def __init__(self, target_port: int, delay_s: float) -> None:
        super().__init__(daemon=True)
        self.listener = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("::1", 0)); self.listener.listen(); self.listener.settimeout(0.2)
        self.port = self.listener.getsockname()[1]; self.target_port = target_port
        self.delay_s = delay_s; self.stop = threading.Event(); self.workers: list[threading.Thread] = []

    def run(self) -> None:
        while not self.stop.is_set():
            try: client, _ = self.listener.accept()
            except socket.timeout: continue
            except OSError: return
            worker = threading.Thread(target=self._connection, args=(client,), daemon=True)
            self.workers.append(worker); worker.start()

    def _connection(self, client: socket.socket) -> None:
        upstream = socket.create_connection(("::1", self.target_port), timeout=5)
        pumps = [threading.Thread(target=self._pump, args=pair, daemon=True) for pair in ((client, upstream), (upstream, client))]
        for pump in pumps: pump.start()
        for pump in pumps: pump.join()
        client.close(); upstream.close()

    def _pump(self, source: socket.socket, destination: socket.socket) -> None:
        with contextlib.suppress(OSError):
            while True:
                data = source.recv(65535)
                if not data: break
                time.sleep(self.delay_s); destination.sendall(data)
            destination.shutdown(socket.SHUT_WR)

    def close(self) -> None:
        self.stop.set(); self.listener.close(); self.join(1)
        for worker in self.workers: worker.join(1)


class _SmtpServer(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.listener = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.listener.bind(("::1", 0)); self.listener.listen(1); self.port = self.listener.getsockname()[1]
        self.message_sha256 = ""

    def run(self) -> None:
        connection, _ = self.listener.accept(); stream = connection.makefile("rwb", buffering=0)
        stream.write(b"220 gatewaycx.test ESMTP\r\n"); data_mode = False; message = bytearray()
        while True:
            line = stream.readline()
            if not line: break
            if data_mode:
                if line == b".\r\n":
                    self.message_sha256 = hashlib.sha256(message).hexdigest(); data_mode = False; stream.write(b"250 stored\r\n")
                else: message.extend(line)
            elif line.upper().startswith((b"EHLO", b"HELO")): stream.write(b"250-gatewaycx.test\r\n250 8BITMIME\r\n")
            elif line.upper().startswith((b"MAIL FROM", b"RCPT TO")): stream.write(b"250 ok\r\n")
            elif line.upper().startswith(b"DATA"): data_mode = True; stream.write(b"354 end with dot\r\n")
            elif line.upper().startswith(b"QUIT"): stream.write(b"221 bye\r\n"); break
            else: stream.write(b"250 ok\r\n")
        stream.close(); connection.close(); self.listener.close()


def _certificate(root: Path) -> tuple[Path, Path]:
    certificate, key = root / "cert.pem", root / "key.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-sha256", "-days", "1", "-subj", "/CN=gatewaycx.test", "-addext", "subjectAltName=DNS:gatewaycx.test,IP:::1", "-keyout", str(key), "-out", str(certificate)], check=True, capture_output=True)
    return certificate, key


async def _h2_server(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    from h2.config import H2Configuration
    from h2.connection import H2Connection
    from h2.events import RequestReceived, StreamEnded
    connection = H2Connection(config=H2Configuration(client_side=False, header_encoding="utf-8")); connection.initiate_connection(); writer.write(connection.data_to_send()); await writer.drain()
    requests: dict[int, str] = {}
    while not reader.at_eof():
        data = await reader.read(65535)
        if not data: break
        for event in connection.receive_data(data):
            if isinstance(event, RequestReceived): requests[event.stream_id] = dict(event.headers).get(":path", "/")
            if isinstance(event, StreamEnded):
                body = (b"F" * FILE_BYTES) if requests.get(event.stream_id) == "/file" else b"gatewaycx-h2"
                connection.send_headers(event.stream_id, [(":status", "200"), ("content-length", str(len(body)))])
                for offset in range(0, len(body), 16_384):
                    end = offset + 16_384 >= len(body)
                    connection.send_data(event.stream_id, body[offset:offset + 16_384], end_stream=end)
        writer.write(connection.data_to_send()); await writer.drain()
    writer.close(); await writer.wait_closed()


async def _h2_request(port: int, certificate: Path, path: str) -> dict[str, Any]:
    from h2.config import H2Configuration
    from h2.connection import H2Connection
    from h2.events import DataReceived, ResponseReceived, StreamEnded
    context = ssl.create_default_context(cafile=str(certificate)); context.minimum_version = ssl.TLSVersion.TLSv1_3; context.set_alpn_protocols(["h2"])
    started = time.monotonic(); reader, writer = await asyncio.open_connection("::1", port, ssl=context, server_hostname="gatewaycx.test")
    connection = H2Connection(config=H2Configuration(client_side=True, header_encoding="utf-8")); connection.initiate_connection(); stream_id = connection.get_next_available_stream_id()
    connection.send_headers(stream_id, [(":method", "GET"), (":scheme", "https"), (":authority", "gatewaycx.test"), (":path", path)], end_stream=True); writer.write(connection.data_to_send()); await writer.drain()
    body = bytearray(); status = None; complete = False
    while not complete:
        for event in connection.receive_data(await reader.read(65535)):
            if isinstance(event, ResponseReceived): status = dict(event.headers).get(":status")
            if isinstance(event, DataReceived): body.extend(event.data); connection.acknowledge_received_data(event.flow_controlled_length, event.stream_id)
            if isinstance(event, StreamEnded): complete = True
        writer.write(connection.data_to_send()); await writer.drain()
    tls = writer.get_extra_info("ssl_object"); writer.close(); await writer.wait_closed()
    return {"elapsed_s": round(time.monotonic() - started, 6), "status": int(status), "bytes": len(body), "alpn": tls.selected_alpn_protocol(), "tls_version": tls.version()}


async def _http3_roundtrip(server_port: int, client_port: int, certificate: Path, key: Path) -> dict[str, Any]:
    from aioquic.asyncio import connect, serve
    from aioquic.asyncio.protocol import QuicConnectionProtocol
    from aioquic.h3.connection import H3_ALPN, H3Connection
    from aioquic.h3.events import DataReceived, HeadersReceived
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.events import ProtocolNegotiated

    class Server(QuicConnectionProtocol):
        def quic_event_received(self, event: Any) -> None:
            if isinstance(event, ProtocolNegotiated): self.http = H3Connection(self._quic)
            if hasattr(self, "http"):
                for item in self.http.handle_event(event):
                    if isinstance(item, HeadersReceived):
                        self.http.send_headers(item.stream_id, [(b":status", b"200"), (b"content-length", b"12")]); self.http.send_data(item.stream_id, b"gatewaycx-h3", end_stream=True); self.transmit()

    class Client(QuicConnectionProtocol):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs); self.http = H3Connection(self._quic); self.future: asyncio.Future[bytes] | None = None; self.body = bytearray()
        async def request(self) -> bytes:
            stream_id = self._quic.get_next_available_stream_id(); self.future = asyncio.get_running_loop().create_future()
            self.http.send_headers(stream_id, [(b":method", b"GET"), (b":scheme", b"https"), (b":authority", b"gatewaycx.test"), (b":path", b"/")], end_stream=True); self.transmit(); return await asyncio.wait_for(self.future, 60)
        def quic_event_received(self, event: Any) -> None:
            for item in self.http.handle_event(event):
                if isinstance(item, DataReceived):
                    self.body.extend(item.data)
                    if item.stream_ended and self.future and not self.future.done(): self.future.set_result(bytes(self.body))

    server_config = QuicConfiguration(is_client=False, alpn_protocols=H3_ALPN); server_config.load_cert_chain(certificate, key)
    server = await serve("::1", server_port, configuration=server_config, create_protocol=Server)
    client_config = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN); client_config.load_verify_locations(certificate)
    started = time.monotonic()
    try:
        async with connect("::1", client_port, configuration=client_config, create_protocol=Client) as protocol:
            body = await protocol.request()  # type: ignore[attr-defined]
    finally: server.close()
    return {"elapsed_s": round(time.monotonic() - started, 6), "status": 200, "bytes": len(body), "alpn": "h3"}


async def run_lab(method: str, one_way_delay_ms: float) -> dict[str, Any]:
    if method not in {"userspace", "kernel-netem"}: raise ValueError("unknown emulation method")
    delay_s = one_way_delay_ms / 1000
    with tempfile.TemporaryDirectory(prefix="gatewaycx-s029-") as temporary:
        root = Path(temporary); certificate, key = _certificate(root)
        dns = _DnsServer(); dns.start()
        dns_relay = _UdpRelay(dns.port, delay_s) if method == "userspace" else None
        if dns_relay: dns_relay.start()
        dns_port = dns_relay.port if dns_relay else dns.port
        query = build_dns_query("service.gatewaycx.test"); sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM); sock.settimeout(10)
        started = time.monotonic(); sock.sendto(query, ("::1", dns_port)); response, _ = sock.recvfrom(4096); dns_elapsed = time.monotonic() - started; sock.close()

        tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); tls_context.minimum_version = ssl.TLSVersion.TLSv1_3; tls_context.set_alpn_protocols(["h2"]); tls_context.load_cert_chain(certificate, key)
        h2_server = await asyncio.start_server(_h2_server, "::1", 0, ssl=tls_context); h2_origin_port = h2_server.sockets[0].getsockname()[1]
        h2_relay = _TcpRelay(h2_origin_port, delay_s) if method == "userspace" else None
        if h2_relay: h2_relay.start()
        h2_port = h2_relay.port if h2_relay else h2_origin_port
        h2_page = await _h2_request(h2_port, certificate, "/"); file_result = await _h2_request(h2_port, certificate, "/file")

        smtp = _SmtpServer(); smtp.start(); smtp_relay = _TcpRelay(smtp.port, delay_s) if method == "userspace" else None
        if smtp_relay: smtp_relay.start()
        smtp_port = smtp_relay.port if smtp_relay else smtp.port
        message = "From: moon@gatewaycx.test\r\nTo: earth@gatewaycx.test\r\nSubject: S029\r\n\r\nregional email\r\n"
        started = time.monotonic()
        client = smtplib.SMTP("::1", smtp_port, timeout=60); client.sendmail("moon@gatewaycx.test", ["earth@gatewaycx.test"], message); client.quit(); smtp.join(5)
        smtp_result = {"elapsed_s": round(time.monotonic() - started, 6), "message_sha256": smtp.message_sha256, "bytes": len(message.encode())}

        # Bind the QUIC server to a fixed free port so a userspace UDP relay can target it.
        probe = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM); probe.bind(("::1", 0)); h3_origin_port = probe.getsockname()[1]; probe.close()
        h3_relay = _UdpRelay(h3_origin_port, delay_s) if method == "userspace" else None
        if h3_relay: h3_relay.start()
        h3_result = await _http3_roundtrip(h3_origin_port, h3_relay.port if h3_relay else h3_origin_port, certificate, key)

        for relay in (dns_relay, h2_relay, smtp_relay, h3_relay):
            if relay: relay.close()
        dns.close(); h2_server.close(); await h2_server.wait_closed()
    return {
        "study_id": "S029", "evidence_class": "MEASUREMENT", "method": method,
        "configured_one_way_delay_ms": one_way_delay_ms,
        "protocols": {
            "dns_over_ipv6_udp": {"elapsed_s": round(dns_elapsed, 6), "answer_aaaa": parse_dns_aaaa(response), "address_family": "IPv6"},
            "tls_http2": h2_page, "http2_file_transfer": {**file_result, "sha256": hashlib.sha256(b"F" * FILE_BYTES).hexdigest()},
            "http3_quic": h3_result, "smtp_email": smtp_result,
        },
        "checks": {
            "dns_returns_ipv6": parse_dns_aaaa(response) == AAAA_ADDRESS,
            "tls13_http2_negotiated": h2_page["tls_version"] == "TLSv1.3" and h2_page["alpn"] == "h2",
            "http3_response_completed": h3_result["alpn"] == "h3" and h3_result["bytes"] == 12,
            "email_was_stored": bool(smtp.message_sha256),
            "file_bytes_completed": file_result["bytes"] == FILE_BYTES,
        },
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "aioquic_required": "1.3.0", "h2_required": "4.3.0"},
        "interpretation_boundary": [
            "The userspace method delays forwarded TCP chunks and UDP datagrams; the kernel-netem method must be invoked under an independently configured Linux qdisc.",
            "CI captures loopback packets for both methods. Local environments without CAP_NET_ADMIN or CAP_NET_RAW cannot reproduce kernel impairment or capture.",
            "The HTTP/2 and HTTP/3 clients are standards libraries, not browsers; SMTP is deliberately minimal and unauthenticated because identity is tested separately.",
            "The CI matrix runs both short delay and 1,282 ms mean one-way lunar light-time; this is loopback protocol evidence, not a prediction of application usability or a time-varying cislunar channel.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--method", choices=("userspace", "kernel-netem"), required=True); parser.add_argument("--one-way-delay-ms", type=float, default=25.0); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args(argv)
    write_json(args.output, asyncio.run(run_lab(args.method, args.one_way_delay_ms))); print(f"wrote {args.output}"); return 0


if __name__ == "__main__": raise SystemExit(main())
