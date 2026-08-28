"""Generate deterministic SVG views of the GatewayCX architecture and committed results."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
INK = "#0b1220"
PANEL = "#121d31"
LINE = "#31415f"
TEXT = "#edf4ff"
MUTED = "#9fb0c9"
BLUE = "#4f8cff"
CYAN = "#31d2c2"
GOLD = "#ffbf47"
RED = "#ff6b6b"


def load(name: str) -> dict[str, Any]:
    data = json.loads((ROOT / "results" / name).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{name} root must be an object")
    return data


def esc(value: Any) -> str:
    return html.escape(str(value))


def text(x: float, y: float, value: Any, size: int = 24, fill: str = TEXT,
         anchor: str = "start", weight: int = 400) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-family="Inter,Segoe UI,Arial,sans-serif" '
        f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{esc(value)}</text>'
    )


def rect(x: float, y: float, width: float, height: float, fill: str,
         radius: float = 18, stroke: str = "none", stroke_width: float = 0) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    )


def line(x1: float, y1: float, x2: float, y2: float, stroke: str = LINE,
         width: float = 4, marker: bool = False, dash: str | None = None) -> str:
    marker_attr = ' marker-end="url(#arrow)"' if marker else ""
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
        f'stroke-width="{width}" stroke-linecap="round"{marker_attr}{dash_attr}/>'
    )


def svg(width: int, height: int, title_value: str, body: list[str]) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">',
            f'<title id="title">{esc(title_value)}</title>',
            '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" '
            'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#4f8cff"/>'
            '</marker></defs>',
            rect(0, 0, width, height, INK, radius=0),
            *body,
            "</svg>",
            "",
        ]
    )


def write(name: str, rendered: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    (FIGURES / name).write_text(rendered, encoding="utf-8")


def architecture() -> None:
    body = [
        text(80, 82, "ONE INTERNET, TWO AUTONOMOUS REGIONS", 34, TEXT, weight=700),
        text(80, 120, "ordinary IP when continuous · durable delivery when interrupted", 21, MUTED),
    ]
    columns = [
        (80, "EARTH REGION", "Internet + cloud", "DNS · identity · services", BLUE),
        (455, "CISLUNAR BACKBONE", "optical + RF", "GX-A1 adapters · DTN", CYAN),
        (830, "LUNAR REGION", "routing + access", "habitats · landers · crews", GOLD),
        (1205, "LUNAR COMPUTE", "cache + replicas", "local services · data centre", RED),
    ]
    for x, heading, main, detail, color in columns:
        body.extend(
            [
                rect(x, 220, 315, 300, PANEL, stroke=color, stroke_width=3),
                rect(x + 24, 248, 72, 8, color, radius=4),
                text(x + 24, 300, heading, 19, color, weight=700),
                text(x + 24, 370, main, 29, TEXT, weight=650),
                text(x + 24, 415, detail, 18, MUTED),
            ]
        )
    for x1, x2 in ((395, 455), (770, 830), (1145, 1205)):
        body.append(line(x1, 370, x2 - 10, 370, BLUE, 5, marker=True))
        body.append(line(x2 - 5, 410, x1 + 5, 410, CYAN, 3, marker=True, dash="10 10"))
    body.extend(
        [
            rect(80, 590, 1440, 92, "#0e1829", stroke=LINE, stroke_width=2),
            text(110, 628, "DESIGN RULE", 17, CYAN, weight=700),
            text(110, 662, "same names and identities · same applications · no vendor owns the service plane", 23, TEXT),
        ]
    )
    write("architecture-overview.svg", svg(1600, 760, "GatewayCX system architecture", body))


def latency() -> None:
    baseline = load("baseline.json")
    rows = []
    for item in baseline["results"]:
        rows.append((item["scenario_id"], item["title"], float(item["elapsed_s"])))
    maximum = max(value for _, _, value in rows)
    body = [
        text(80, 82, "AVOIDABLE DISTANCE IS THE FIRST OPTIMISATION", 34, TEXT, weight=700),
        text(80, 120, "elapsed time from the deterministic baseline · logarithmic labels avoided", 21, MUTED),
    ]
    y = 230
    for index, (scenario_id, title_value, value) in enumerate(rows):
        color = (BLUE, CYAN, GOLD)[index]
        width = max(8, 1050 * value / maximum)
        body.extend(
            [
                text(80, y, scenario_id, 20, color, weight=700),
                text(180, y, title_value, 21, TEXT),
                rect(180, y + 28, 1050, 38, "#18253b", radius=8),
                rect(180, y + 28, width, 38, color, radius=8),
                text(1260, y + 58, f"{value:.3f} s", 25, TEXT, weight=650),
            ]
        )
        y += 150
    body.extend(
        [
            text(80, 710, "MODEL BOUNDARY", 16, RED, weight=700),
            text(265, 710, "scenario assumptions, not a measured lunar user experience", 19, MUTED),
        ]
    )
    write("baseline-latency.svg", svg(1600, 780, "GatewayCX baseline elapsed-time comparison", body))


def bearer_window() -> None:
    result = load("S016_adapter_probe.json")
    total = float(result["inputs"]["traffic_unit_bytes"] * result["inputs"]["traffic_unit_count"])
    body = [
        text(80, 82, "ONE ADAPTER SURFACE, DIFFERENT BEARER CAPACITY", 34, TEXT, weight=700),
        text(80, 120, "first 100 ms after acquisition · 7,995,392 accepted bytes", 21, MUTED),
    ]
    for index, adapter in enumerate(result["adapters"]):
        y = 235 + index * 220
        sent = float(adapter["first_window"]["transmitted_bytes"])
        queued = float(adapter["first_window"]["queued_after_bytes"])
        sent_width = 1050 * sent / total
        queue_width = 1050 * queued / total
        body.extend(
            [
                text(80, y, adapter["media"].upper(), 22, (CYAN, GOLD)[index], weight=700),
                text(240, y, adapter["bearer_id"], 20, MUTED),
                rect(240, y + 32, sent_width, 70, (CYAN, GOLD)[index], radius=10),
                rect(240 + sent_width, y + 32, queue_width, 70, "#263550", radius=10),
                text(260, y + 78, f"{sent/1_000_000:.2f} MB sent", 22, INK, weight=700),
                text(1320, y + 78, f"{queued/1_000_000:.2f} MB queued", 21, TEXT, anchor="end"),
            ]
        )
    body.extend(
        [
            rect(240, 660, 34, 20, CYAN, radius=4),
            text(290, 678, "transmitted", 18, MUTED),
            rect(460, 660, 34, 20, "#263550", radius=4),
            text(510, 678, "still queued", 18, MUTED),
            text(80, 735, "ASSUMED PROFILE VALUES · BYTE-BUDGET TEST · NO TERMINAL OR LINK", 17, RED, weight=700),
        ]
    )
    write("s016-bearer-window.svg", svg(1600, 800, "S016 bearer capacity comparison", body))


def durable_restart() -> None:
    result = load("S017_durable_restart.json")
    checkpoints = [
        ("seed before transmit", result["seed_process"]["before_transmit"]),
        ("seed exit", result["seed_process"]["before_exit"]),
        ("recovery entry", result["recovery_process"]["after_restart"]),
        ("recovery exit", result["recovery_process"]["final"]),
    ]
    total = float(result["inputs"]["accepted_bytes"])
    body = [
        text(80, 82, "TRAFFIC PROGRESS SURVIVES A CLEAN PROCESS RESTART", 34, TEXT, weight=700),
        text(80, 120, "SQLite traffic ledger · same accepted bytes before and after restart", 21, MUTED),
    ]
    for index, (label, values) in enumerate(checkpoints):
        y = 205 + index * 125
        sent = float(values["transmitted_bytes"])
        queued = float(values["queue_bytes"])
        sent_width = 1000 * sent / total
        queue_width = 1000 * queued / total
        body.extend(
            [
                text(80, y + 38, label, 20, TEXT),
                rect(350, y, sent_width, 60, BLUE, radius=8),
                rect(350 + sent_width, y, queue_width, 60, GOLD, radius=8),
                text(1380, y + 39, f"{sent/1_000_000:.2f} / {queued/1_000_000:.2f} MB", 20, MUTED, anchor="end"),
            ]
        )
        if index == 1:
            body.append(line(320, y + 92, 1410, y + 92, RED, 2, dash="8 8"))
            body.append(text(1410, y + 115, "process boundary", 16, RED, anchor="end", weight=700))
    body.extend(
        [
            rect(350, 720, 34, 20, BLUE, radius=4),
            text(400, 738, "transmitted", 18, MUTED),
            rect(570, 720, 34, 20, GOLD, radius=4),
            text(620, 738, "queued", 18, MUTED),
            text(80, 795, "CLEAN RESTART ONLY · NOT POWER-LOSS OR FLIGHT-STORAGE QUALIFICATION", 17, RED, weight=700),
        ]
    )
    write("s017-durable-restart.svg", svg(1600, 850, "S017 cross-process durable restart", body))


def authenticated_binding() -> None:
    result = load("S019_authenticated_transport.json")
    observations = result["observations"]
    body = [
        text(80, 82, "AUTHENTICATE THE CALLER · PRESERVE REPLAY STATE", 34, TEXT, weight=700),
        text(80, 120, "S019 local reference binding · HMAC-SHA256 · clean restart", 21, MUTED),
    ]
    stages = [
        (80, "SERVICE CLIENT", "client ID + sequence", "sign canonical request", BLUE),
        (455, "TRUST CHECK", "verify request MAC", "reject wrong key / change", CYAN),
        (830, "REPLAY LEDGER", "last sequence only", "survives server restart", GOLD),
        (1205, "GX-A1 ADAPTER", "dispatch operation", "payload-blind ledger", RED),
    ]
    for x, heading, main, detail, color in stages:
        body.extend(
            [
                rect(x, 215, 315, 260, PANEL, stroke=color, stroke_width=3),
                rect(x + 24, 243, 72, 8, color, radius=4),
                text(x + 24, 295, heading, 19, color, weight=700),
                text(x + 24, 355, main, 24, TEXT, weight=650),
                text(x + 24, 400, detail, 18, MUTED),
            ]
        )
    for x1, x2 in ((395, 455), (770, 830), (1145, 1205)):
        body.append(line(x1, 345, x2 - 10, 345, BLUE, 5, marker=True))
    checks = [
        ("MODIFIED", observations["tampered_request_error"]),
        ("WRONG KEY", observations["wrong_key_error"]),
        ("REPLAY", observations["restart_replay_error"]),
    ]
    for index, (label, outcome) in enumerate(checks):
        x = 80 + index * 390
        body.extend(
            [
                rect(x, 550, 350, 88, "#0e1829", stroke=LINE, stroke_width=2),
                text(x + 22, 584, label, 16, RED, weight=700),
                text(x + 22, 618, outcome, 19, TEXT),
            ]
        )
    body.extend(
        [
            text(80, 715, "BOUNDARY", 16, RED, weight=700),
            text(205, 715, "no confidentiality · no PKI · no independent adapter · no flight claim", 19, MUTED),
        ]
    )
    write(
        "s019-authenticated-binding.svg",
        svg(1600, 780, "S019 authenticated GX-A1 reference binding", body),
    )


def transaction_recovery() -> None:
    result = load("S020_abrupt_restart.json")
    observations = result["observations"]
    stages = [
        ("STABLE COMMIT", observations["stable_snapshot"], BLUE, "seed closes cleanly"),
        ("KILL BEFORE COMMIT", observations["after_precommit_kill"], GOLD, "new row rolls back"),
        ("KILL AFTER COMMIT", observations["after_postcommit_kill"], CYAN, "new row survives"),
        ("RECOVERED WRITE", observations["final_snapshot"], RED, "store accepts work"),
    ]
    maximum = max(float(values["accepted_bytes"]) for _, values, _, _ in stages)
    body = [
        text(80, 82, "COMMIT IS THE RECOVERY BOUNDARY", 34, TEXT, weight=700),
        text(80, 120, "S020 coordinated SIGKILL probe · SQLite WAL · synchronous FULL", 21, MUTED),
    ]
    for index, (label, values, color, note) in enumerate(stages):
        y = 195 + index * 125
        width = 960 * float(values["accepted_bytes"]) / maximum
        body.extend(
            [
                text(80, y + 38, label, 18, color, weight=700),
                rect(355, y, 960, 62, "#18253b", radius=8),
                rect(355, y, width, 62, color, radius=8),
                text(380, y + 40, f'{values["accepted_bytes"]:,} committed bytes', 20, INK, weight=700),
                text(1510, y + 40, note, 18, MUTED, anchor="end"),
            ]
        )
    body.extend(
        [
            text(80, 730, "BOUNDARY", 16, RED, weight=700),
            text(205, 730, "coordinated process kill · not electrical power loss or storage qualification", 19, MUTED),
        ]
    )
    write(
        "s020-transaction-recovery.svg",
        svg(1600, 790, "S020 transaction-boundary recovery", body),
    )


def independent_adapter() -> None:
    result = load("S021_independent_adapter.json")
    observations = result["observations"]
    body = [
        text(80, 82, "ONE CONTRACT, TWO SEPARATE CODE PATHS", 34, TEXT, weight=700),
        text(80, 120, "S021 authenticated local interoperability · no shared runtime imports", 21, MUTED),
    ]
    stages = [
        (80, "GATEWAYCX CLIENT", "authenticated_rpc", "build + verify envelope", BLUE),
        (455, "GX-A1 BINDING", observations["rpc_version"], "canonical JSONL + HMAC", CYAN),
        (830, "STANDALONE SERVER", "standard library only", "distinct implementation ID", GOLD),
        (1205, "SEPARATE LEDGER", observations["persistence_scope"], "restart retains progress", RED),
    ]
    for x, heading, main, detail, color in stages:
        body.extend(
            [
                rect(x, 215, 315, 270, PANEL, stroke=color, stroke_width=3),
                rect(x + 24, 243, 72, 8, color, radius=4),
                text(x + 24, 295, heading, 18, color, weight=700),
                text(x + 24, 355, main, 22, TEXT, weight=650),
                text(x + 24, 405, detail, 16, MUTED),
            ]
        )
    for x1, x2 in ((395, 455), (770, 830), (1145, 1205)):
        body.append(line(x1, 350, x2 - 10, 350, BLUE, 5, marker=True))
    body.extend(
        [
            rect(80, 560, 1440, 94, "#0e1829", stroke=LINE, stroke_width=2),
            text(110, 596, "OBSERVED", 16, CYAN, weight=700),
            text(
                110,
                632,
                f'{observations["transmitted_bytes"]:,} bytes transmitted · duplicate recognised · ledger reopened',
                22,
                TEXT,
            ),
            text(80, 730, "BOUNDARY", 16, RED, weight=700),
            text(205, 730, "same project · bounded subset · no supplier, terminal or physical link", 19, MUTED),
        ]
    )
    write(
        "s021-independent-adapter.svg",
        svg(1600, 790, "S021 independent-code adapter interoperability", body),
    )


def lunar_orbit_envelope() -> None:
    result = load("S022_lunar_orbits.json")
    synchronous = result["synchronous_case"]
    shells = result["relay_shells"]
    body = [
        text(80, 82, "A LUNAR RELAY SHELL IS NOT LUNAR GEO", 34, TEXT, weight=700),
        text(80, 120, "S022 two-body screen · ideal equatorial coverage only", 21, MUTED),
        text(80, 195, "MOON-SYNCHRONOUS RADIUS", 18, CYAN, weight=700),
    ]
    scale = 640 / float(synchronous["two_body_synchronous_radius_km"])
    hill_width = float(synchronous["approximate_hill_radius_km"]) * scale
    sync_width = float(synchronous["two_body_synchronous_radius_km"]) * scale
    body.extend(
        [
            rect(80, 230, 640, 54, "#18253b", radius=8),
            rect(80, 230, hill_width, 54, GOLD, radius=8),
            line(80 + sync_width, 215, 80 + sync_width, 302, RED, 5),
            text(80, 330, f'Hill screen  {synchronous["approximate_hill_radius_km"]:,.0f} km', 19, GOLD),
            text(720, 330, f'synchronous  {synchronous["two_body_synchronous_radius_km"]:,.0f} km', 19, RED, anchor="end"),
            text(830, 195, "IDEAL EQUATORIAL SATELLITE COUNT", 18, CYAN, weight=700),
        ]
    )
    maximum = max(int(item["ideal_equatorial_satellites_min"]) for item in shells)
    for index, item in enumerate(shells):
        y = 235 + index * 92
        count = int(item["ideal_equatorial_satellites_min"])
        width = 500 * count / maximum
        color = (BLUE, CYAN, GOLD, RED)[index]
        body.extend(
            [
                text(830, y + 34, f'{item["altitude_km"]:,.0f} km', 18, TEXT),
                rect(970, y, width, 50, color, radius=7),
                text(1495, y + 34, str(count), 21, TEXT, anchor="end", weight=700),
            ]
        )
    body.extend(
        [
            rect(80, 520, 640, 132, "#0e1829", stroke=LINE, stroke_width=2),
            text(110, 560, "SCREEN RESULT", 16, RED, weight=700),
            text(110, 600, "synchronous radius / Hill radius", 20, MUTED),
            text(110, 635, f'{synchronous["synchronous_to_hill_ratio"]:.3f}  → outside', 28, RED, weight=700),
            text(80, 730, "BOUNDARY", 16, RED, weight=700),
            text(205, 730, "zero elevation · no poles, terrain, link budget, failures or multi-body propagation", 19, MUTED),
        ]
    )
    write(
        "s022-lunar-orbit-envelope.svg",
        svg(1600, 790, "S022 lunar relay orbit envelope", body),
    )


def ground_offload() -> None:
    result = load("S023_ground_offload.json")
    shared = result["shared_pool"]
    separated = result["separated_pools"]
    pipelines = result["relay_pipeline_cases"]
    body = [
        text(80, 82, "PROTECT DEEP-SPACE CAPACITY BY SEPARATING LUNAR DEMAND", 32, TEXT, weight=700),
        text(80, 120, "S023 synthetic service units · not mission schedules or antenna hours", 21, MUTED),
        text(80, 195, "SHARED POOL", 18, RED, weight=700),
        rect(80, 225, 600, 62, BLUE, radius=8),
        rect(80 + 600 * shared["served_units"] / shared["offered_units"], 225,
             600 * shared["backlog_units"] / shared["offered_units"], 62, RED, radius=8),
        text(100, 265, f'{shared["served_units"]:.0f} served', 20, INK, weight=700),
        text(660, 265, f'{shared["backlog_units"]:.0f} backlog', 18, TEXT, anchor="end"),
        text(820, 195, "SEPARATED POOLS", 18, CYAN, weight=700),
        rect(820, 225, 320, 62, CYAN, radius=8),
        rect(1160, 225, 280, 62, GOLD, radius=8),
        text(840, 265, f'deep space {separated["deep_space"]["served_units"]:.0f}', 19, INK, weight=700),
        text(1180, 265, f'lunar {separated["lunar"]["served_units"]:.0f}', 19, INK, weight=700),
        text(80, 390, "RELAY PIPELINE DELIVERY", 18, CYAN, weight=700),
    ]
    for index, case in enumerate(pipelines):
        y = 430 + index * 82
        body.extend([
            text(80, y + 32, case["name"].replace("_", " "), 17, TEXT),
            rect(600, y, 700, 48, "#18253b", radius=7),
            rect(600, y, 700 * case["delivered_units"] / 80, 48, (RED, GOLD, CYAN)[index], radius=7),
            text(1360, y + 32, f'{case["delivered_units"]:.0f} delivered', 18, MUTED),
        ])
    body.extend([text(80, 730, "BOUNDARY", 16, RED, weight=700),
                 text(205, 730, "synthetic isolation model · no DSN, provider or mission data", 19, MUTED)])
    write("s023-ground-offload.svg", svg(1600, 790, "S023 ground-network offload", body))


def simulation_ceiling() -> None:
    ephemeris = load("S024_ephemeris.json")
    links = load("S025_link_budgets.json")
    datacentre = load("S026_datacentre_trade.json")
    economics = load("S027_economics.json")
    medium = next(case for case in ephemeris["cases"] if case["constellation"] == "medium_inclined_8")
    ka = next(case for case in links["rf_classes"] if case["class"] == "dwe_ka_band")
    surface = next(case for case in datacentre["configurations"] if case["configuration"] == "surface_shielded")
    economic = next(case for case in economics["cases"] if case["utilisation"] == 0.8 and case["optical_availability"] == 0.9)
    panels = [
        (80, "EPHEMERIS + FAILURE", "3 / 3 sites routed", f'{medium["single_satellite_failure"]["sites"]["far_side_equator"]["availability_fraction"]:.0%} far-side sampled availability', BLUE),
        (455, "RF / OPTICAL LINKS", f'{ka["clear"]["margin_db"]:.2f} dB Ka margin', f'{ka["degraded"]["margin_db"]:.2f} dB with +6 dB loss', CYAN),
        (830, "LUNAR COMPUTE", f'{surface["outputs"]["facility_power_kw"]:.2f} kW facility', f'{surface["outputs"]["radiator_area_m2"]:.2f} m² radiator class', GOLD),
        (1205, "UNIT ECONOMICS", f'${economic["cost_per_delivered_bit_usd"]:.2e} / bit', "synthetic 80% utilisation case", RED),
    ]
    body = [
        text(80, 82, "FROM UNMODELLED ROWS TO EXECUTABLE SENSITIVITIES", 32, TEXT, weight=700),
        text(80, 120, "S024–S027 · architecture classes, not hardware or market evidence", 21, MUTED),
    ]
    for x, heading, main_value, detail, color in panels:
        body.extend([
            rect(x, 215, 315, 330, PANEL, stroke=color, stroke_width=3),
            rect(x + 24, 245, 72, 8, color, radius=4),
            text(x + 24, 300, heading, 17, color, weight=700),
            text(x + 24, 385, main_value, 26, TEXT, weight=650),
            text(x + 24, 440, detail, 17, MUTED),
        ])
    body.extend([
        rect(80, 610, 1440, 82, "#0e1829", stroke=LINE, stroke_width=2),
        text(110, 644, "EVIDENCE RULE", 16, RED, weight=700),
        text(110, 677, "replace assumptions with controlled inputs; never relabel a model as a measurement", 21, TEXT),
    ])
    write("s024-s027-simulation-ceiling.svg", svg(1600, 760, "GatewayCX S024 to S027 simulation ceiling", body))


def regional_fault_lab() -> None:
    result = load("S028_regional_fault_lab.json")
    recovery = result["experiments"]["storage_recovery"]
    experiments = [
        ("X07", "IDENTITY", "stale → expiry → revocation", BLUE),
        ("X08", "CONSISTENCY", "fail closed · merge · escrow", CYAN),
        ("X14", "UPDATE", "digest · A/B · migration rollback", GOLD),
        ("X16", "BLACK START", "5 child processes · no Earth", RED),
        ("X18", "RECOVERY", f'{recovery["restored_rows"]} exact rows restored', BLUE),
    ]
    body = [
        text(80, 82, "THE LUNAR REGION NOW FAILS IN EXECUTABLE SOFTWARE", 32, TEXT, weight=700),
        text(80, 120, "S028 · real signatures, payloads, SQLite transactions, processes and corruption", 21, MUTED),
    ]
    for index, (identifier, heading, detail, color) in enumerate(experiments):
        x = 80 + index * 300
        body.extend([
            rect(x, 220, 270, 300, PANEL, stroke=color, stroke_width=3),
            text(x + 24, 275, identifier, 18, color, weight=700),
            text(x + 24, 340, heading, 21, TEXT, weight=700),
            text(x + 24, 405, detail, 15, MUTED),
            text(x + 24, 475, "PASS", 22, color, weight=700),
        ])
    body.extend([
        rect(80, 600, 1440, 90, "#0e1829", stroke=LINE, stroke_width=2),
        text(110, 636, "BOUNDARY", 16, RED, weight=700),
        text(110, 672, "reference software · no production PKI, flight services, electrical start or raw-device qualification", 20, TEXT),
    ])
    write("s028-regional-fault-lab.svg", svg(1600, 760, "S028 executable regional fault laboratory", body))


def main() -> int:
    architecture()
    latency()
    bearer_window()
    durable_restart()
    authenticated_binding()
    transaction_recovery()
    independent_adapter()
    lunar_orbit_envelope()
    ground_offload()
    simulation_ceiling()
    regional_fault_lab()
    print("wrote 11 GatewayCX SVG figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
