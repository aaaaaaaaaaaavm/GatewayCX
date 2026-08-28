"""GX-A1 executable runtime seam for profile-backed bearer adapters.

The reference implementation moves identifiers and byte counts, never payload content.  It is a
deterministic integration aid, not a modem, terminal driver or network protocol.
"""

from __future__ import annotations

import argparse
import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .conformance import validate_bearer_profile
from .diagnostics import FAULT_CODES
from .traffic_store import (
    InMemoryTrafficStore,
    StoredTrafficUnit,
    TrafficStore,
)


@dataclass(frozen=True)
class TrafficUnit:
    """Metadata handed to a bearer after any higher-layer segmentation."""

    traffic_unit_id: str
    payload_bytes: int
    traffic_class: str
    deferred: bool = True


class BearerAdapter(Protocol):
    """Minimal provider-neutral runtime surface used by the GatewayCX service plane."""

    def capabilities(self) -> dict[str, Any]: ...

    def snapshot(self) -> dict[str, Any]: ...

    def submit(self, traffic_unit: TrafficUnit) -> dict[str, Any]: ...

    def set_contact(self, available: bool, offset_s: float) -> dict[str, Any]: ...

    def acquire(self, offset_s: float) -> dict[str, Any]: ...

    def advance(self, offset_s: float) -> dict[str, Any]: ...

    def transmit(self, duration_s: float) -> dict[str, Any]: ...

    def inject_fault(self, fault_code: str, offset_s: float) -> dict[str, Any]: ...

    def clear_faults(self, offset_s: float) -> dict[str, Any]: ...


class ProfileBackedAdapter:
    """Deterministic GX-A1 reference adapter driven by a conformant GX-B1 profile."""

    API_VERSION = "GX-A1/0.1"

    def __init__(
        self,
        profile: dict[str, Any],
        store: TrafficStore | None = None,
    ) -> None:
        errors = validate_bearer_profile(profile)
        if errors:
            raise ValueError(f"invalid GX-B1 profile: {'; '.join(errors)}")
        self._profile = copy.deepcopy(profile)
        self._offset_s = 0.0
        self._contact_available = False
        self._link_state = "unavailable"
        self._ready_at_s: float | None = None
        self._fault_codes: list[str] = []
        self._store = store if store is not None else InMemoryTrafficStore()
        self._link_epoch = 0

    @classmethod
    def from_file(
        cls,
        path: Path,
        store: TrafficStore | None = None,
    ) -> ProfileBackedAdapter:
        profile = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(profile, dict):
            raise ValueError("GX-B1 profile root must be an object")
        return cls(profile, store=store)

    @property
    def bearer_id(self) -> str:
        return str(self._profile["bearer_id"])

    @property
    def queue_bytes(self) -> int:
        return self._store.snapshot()["queue_bytes"]

    def _at(self, offset_s: float) -> None:
        if offset_s + 1e-9 < self._offset_s:
            raise ValueError("adapter offsets must be monotonic")
        self._offset_s = max(self._offset_s, offset_s)

    def _envelope(self, operation: str, status: str, **fields: Any) -> dict[str, Any]:
        return {
            "api_version": self.API_VERSION,
            "bearer_id": self.bearer_id,
            "operation": operation,
            "status": status,
            "observed_offset_s": round(self._offset_s, 6),
            **fields,
        }

    def capabilities(self) -> dict[str, Any]:
        return self._envelope(
            "capabilities",
            "ok",
            profile=copy.deepcopy(self._profile),
            operations=[
                "capabilities",
                "snapshot",
                "submit",
                "set_contact",
                "acquire",
                "advance",
                "transmit",
                "inject_fault",
                "clear_faults",
            ],
            reference_persistence_scope=self._store.persistence_scope,
        )

    def snapshot(self) -> dict[str, Any]:
        performance = self._profile["performance"]
        ledger = self._store.snapshot()
        return self._envelope(
            "snapshot",
            "ok",
            link_state=self._link_state,
            tx_rate_mbps=(
                performance["forward_capacity_mbps"] if self._link_state == "ready" else 0.0
            ),
            rx_rate_mbps=(
                performance["return_capacity_mbps"] if self._link_state == "ready" else 0.0
            ),
            queue_bytes=ledger["queue_bytes"],
            next_contact_utc=None,
            fault_codes=list(self._fault_codes),
            link_epoch=self._link_epoch,
            accepted_bytes=ledger["accepted_bytes"],
            transmitted_bytes=ledger["transmitted_bytes"],
            reference_persistence_scope=self._store.persistence_scope,
        )

    def submit(self, traffic_unit: TrafficUnit) -> dict[str, Any]:
        if not traffic_unit.traffic_unit_id:
            return self._envelope("submit", "rejected", reason="missing_traffic_unit_id")
        if traffic_unit.payload_bytes <= 0:
            return self._envelope("submit", "rejected", reason="invalid_payload_bytes")
        maximum = int(self._profile["performance"]["maximum_traffic_unit_bytes"])
        if traffic_unit.payload_bytes > maximum:
            return self._envelope(
                "submit", "rejected", reason="traffic_unit_too_large", maximum_bytes=maximum
            )
        queue_profile = self._profile["queue"]
        if self._link_state != "ready" and not (
            traffic_unit.deferred and queue_profile["deferred_delivery"]
        ):
            return self._envelope("submit", "rejected", reason="link_unavailable")
        decision = self._store.accept(
            StoredTrafficUnit(
                traffic_unit_id=traffic_unit.traffic_unit_id,
                payload_bytes=traffic_unit.payload_bytes,
                traffic_class=traffic_unit.traffic_class,
                deferred=traffic_unit.deferred,
            ),
            int(queue_profile["durable_bytes"]),
        )
        if decision["status"] != "accepted_pending":
            return self._envelope(
                "submit",
                decision["status"],
                queue_bytes=self.queue_bytes,
                **({"reason": decision["reason"]} if "reason" in decision else {}),
            )
        return self._envelope(
            "submit",
            "accepted_pending",
            traffic_unit_id=traffic_unit.traffic_unit_id,
            accepted_bytes=decision["accepted_bytes"],
            queue_bytes=self.queue_bytes,
        )

    def set_contact(self, available: bool, offset_s: float) -> dict[str, Any]:
        self._at(offset_s)
        self._contact_available = available
        if not available:
            self._link_state = "unavailable"
            self._ready_at_s = None
        return self._envelope(
            "set_contact", "ok", contact_available=available, link_state=self._link_state
        )

    def acquire(self, offset_s: float) -> dict[str, Any]:
        self._at(offset_s)
        if not self._contact_available:
            return self._envelope("acquire", "rejected", reason="contact_unavailable")
        if self._fault_codes:
            return self._envelope("acquire", "rejected", reason="active_fault")
        self._link_state = "acquiring"
        self._ready_at_s = self._offset_s + float(
            self._profile["performance"]["acquisition_max_s"]
        )
        return self._envelope(
            "acquire", "accepted", link_state=self._link_state, ready_at_s=self._ready_at_s
        )

    def advance(self, offset_s: float) -> dict[str, Any]:
        self._at(offset_s)
        transitioned = False
        if (
            self._link_state == "acquiring"
            and self._ready_at_s is not None
            and self._offset_s >= self._ready_at_s
            and self._contact_available
            and not self._fault_codes
        ):
            self._link_state = "ready"
            self._ready_at_s = None
            self._link_epoch += 1
            transitioned = True
        return self._envelope(
            "advance", "ok", link_state=self._link_state, transitioned=transitioned
        )

    def transmit(self, duration_s: float) -> dict[str, Any]:
        if duration_s <= 0:
            raise ValueError("transmit duration must be greater than zero")
        if self._link_state != "ready":
            self._offset_s += duration_s
            return self._envelope(
                "transmit", "blocked", reason="link_not_ready", transmitted_bytes=0
            )
        byte_budget = int(
            float(self._profile["performance"]["forward_capacity_mbps"])
            * 1_000_000
            * duration_s
            / 8
        )
        sent_by_unit = self._store.transmit(byte_budget)
        transmitted = sum(fragment["bytes"] for fragment in sent_by_unit)
        self._offset_s += duration_s
        return self._envelope(
            "transmit",
            "ok",
            transmitted_bytes=transmitted,
            queue_bytes=self.queue_bytes,
            fragments=sent_by_unit,
        )

    def close(self) -> None:
        self._store.close()

    def inject_fault(self, fault_code: str, offset_s: float) -> dict[str, Any]:
        self._at(offset_s)
        definition = FAULT_CODES.get(fault_code)
        if definition is None or definition["category"] != "bearer":
            raise ValueError("fault_code must be a portable GX-O1 bearer code")
        if fault_code not in self._fault_codes:
            self._fault_codes.append(fault_code)
        self._link_state = "unavailable"
        self._contact_available = False
        self._ready_at_s = None
        return self._envelope(
            "inject_fault",
            "ok",
            fault_code=fault_code,
            link_state=self._link_state,
            queue_bytes=self.queue_bytes,
        )

    def clear_faults(self, offset_s: float) -> dict[str, Any]:
        """Reference-test extension; contact and acquisition must still be re-established."""

        self._at(offset_s)
        cleared = list(self._fault_codes)
        self._fault_codes.clear()
        return self._envelope("clear_faults", "ok", cleared_fault_codes=cleared)


def _load_adapters(profile_paths: list[Path]) -> list[ProfileBackedAdapter]:
    return [ProfileBackedAdapter.from_file(path) for path in profile_paths]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profiles", type=Path, nargs="+")
    args = parser.parse_args(argv)
    summaries = [adapter.capabilities() for adapter in _load_adapters(args.profiles)]
    print(json.dumps(summaries, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
