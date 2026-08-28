"""Loopback JSON-lines process binding for the exploratory GX-A1 bearer adapter."""

from __future__ import annotations

import argparse
import json
import socket
from pathlib import Path
from typing import Any

from .bearer_adapter import ProfileBackedAdapter, TrafficUnit
from .traffic_store import SQLiteTrafficStore


RPC_VERSION = "GX-A1-JSONL/0.1"
MAX_REQUEST_BYTES = 1_000_000


class AdapterRPCServer:
    """One-request-per-connection loopback TCP binding for a GX-A1 adapter."""

    def __init__(
        self,
        adapter: ProfileBackedAdapter,
        host: str = "127.0.0.1",
        port: int = 0,
        port_file: Path | None = None,
    ) -> None:
        self.adapter = adapter
        self.host = host
        self.port = port
        self.port_file = port_file
        self._stop = False

    def _reply(
        self,
        request_id: str | None,
        ok: bool,
        **fields: Any,
    ) -> dict[str, Any]:
        return {
            "rpc_version": RPC_VERSION,
            "request_id": request_id,
            "ok": ok,
            **fields,
        }

    def dispatch(self, request: Any) -> dict[str, Any]:
        if not isinstance(request, dict):
            return self._reply(None, False, error="request_must_be_object")
        request_id = request.get("request_id")
        operation = request.get("operation")
        arguments = request.get("arguments", {})
        if not isinstance(request_id, str) or not request_id:
            return self._reply(None, False, error="invalid_request_id")
        if not isinstance(arguments, dict):
            return self._reply(request_id, False, error="arguments_must_be_object")
        try:
            if operation == "capabilities":
                result = self.adapter.capabilities()
            elif operation == "snapshot":
                result = self.adapter.snapshot()
            elif operation == "submit":
                result = self.adapter.submit(
                    TrafficUnit(
                        traffic_unit_id=str(arguments["traffic_unit_id"]),
                        payload_bytes=int(arguments["payload_bytes"]),
                        traffic_class=str(arguments["traffic_class"]),
                        deferred=bool(arguments.get("deferred", True)),
                    )
                )
            elif operation == "set_contact":
                result = self.adapter.set_contact(
                    bool(arguments["available"]), float(arguments["offset_s"])
                )
            elif operation == "acquire":
                result = self.adapter.acquire(float(arguments["offset_s"]))
            elif operation == "advance":
                result = self.adapter.advance(float(arguments["offset_s"]))
            elif operation == "transmit":
                result = self.adapter.transmit(float(arguments["duration_s"]))
            elif operation == "inject_fault":
                result = self.adapter.inject_fault(
                    str(arguments["fault_code"]), float(arguments["offset_s"])
                )
            elif operation == "clear_faults":
                result = self.adapter.clear_faults(float(arguments["offset_s"]))
            elif operation == "shutdown":
                self._stop = True
                result = {"operation": "shutdown", "status": "accepted"}
            else:
                return self._reply(request_id, False, error="unknown_operation")
        except (KeyError, TypeError, ValueError) as exc:
            return self._reply(request_id, False, error="invalid_arguments", detail=str(exc))
        return self._reply(request_id, True, result=result)

    def serve(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((self.host, self.port))
            bound_host, bound_port = listener.getsockname()
            if self.port_file is not None:
                self.port_file.parent.mkdir(parents=True, exist_ok=True)
                self.port_file.write_text(f"{bound_host}:{bound_port}\n", encoding="utf-8")
            listener.listen(8)
            while not self._stop:
                connection, _ = listener.accept()
                with connection:
                    received = bytearray()
                    while len(received) <= MAX_REQUEST_BYTES:
                        chunk = connection.recv(65_536)
                        if not chunk:
                            break
                        received.extend(chunk)
                        if b"\n" in chunk:
                            break
                    request_id: str | None = None
                    if len(received) > MAX_REQUEST_BYTES:
                        response = self._reply(None, False, error="request_too_large")
                    else:
                        try:
                            request = json.loads(received.split(b"\n", 1)[0].decode("utf-8"))
                            if isinstance(request, dict) and isinstance(
                                request.get("request_id"), str
                            ):
                                request_id = request["request_id"]
                            response = self.dispatch(request)
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            response = self._reply(request_id, False, error="invalid_json")
                    connection.sendall(
                        (json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode(
                            "utf-8"
                        )
                    )
        if self.port_file is not None:
            self.port_file.unlink(missing_ok=True)
        self.adapter.close()


class AdapterRPCClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._sequence = 0

    def call(self, operation: str, **arguments: Any) -> dict[str, Any]:
        self._sequence += 1
        request_id = f"rpc-{self._sequence:04d}"
        request = {
            "request_id": request_id,
            "operation": operation,
            "arguments": arguments,
        }
        with socket.create_connection((self.host, self.port), timeout=5) as connection:
            connection.sendall((json.dumps(request, sort_keys=True) + "\n").encode("utf-8"))
            response_bytes = bytearray()
            while b"\n" not in response_bytes:
                chunk = connection.recv(65_536)
                if not chunk:
                    break
                response_bytes.extend(chunk)
        response = json.loads(response_bytes.split(b"\n", 1)[0].decode("utf-8"))
        if response.get("request_id") != request_id:
            raise RuntimeError("GX-A1 RPC response request_id mismatch")
        return response


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--port-file", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args(argv)
    adapter = ProfileBackedAdapter.from_file(
        args.profile,
        store=SQLiteTrafficStore(args.database),
    )
    if args.host != "127.0.0.1":
        parser.error("the reference binding is restricted to 127.0.0.1")
    AdapterRPCServer(
        adapter,
        host=args.host,
        port=args.port,
        port_file=args.port_file,
    ).serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
