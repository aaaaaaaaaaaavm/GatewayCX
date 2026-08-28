.PHONY: scenarios disruption capacity placement admission handover updates preposition black-start diagnostics integrated adapters durable transport authenticated abrupt independent orbits offload ephemeris links datacentre economics regional-faults figures conformance audit test verify

scenarios:
	python -m gatewaycx.cli run-all

disruption:
	python -m gatewaycx.disruption

capacity:
	python -m gatewaycx.capacity

placement:
	python -m gatewaycx.placement

admission:
	python -m gatewaycx.admission

handover:
	python -m gatewaycx.handover

updates:
	python -m gatewaycx.update_delivery

preposition:
	python -m gatewaycx.preposition

black-start:
	python -m gatewaycx.black_start

diagnostics:
	python -m gatewaycx.diagnostics
	python -m gatewaycx.diagnostics --validate results/S014_diagnostic_trace.json

integrated:
	python -m gatewaycx.integrated_replay

adapters:
	python -m gatewaycx.adapter_probe

durable:
	python -m gatewaycx.durable_restart

transport:
	python -m gatewaycx.adapter_transport_probe

authenticated:
	python -m gatewaycx.authenticated_transport_probe

abrupt:
	python -m gatewaycx.abrupt_restart

independent:
	python -m gatewaycx.independent_adapter_probe

orbits:
	python -m gatewaycx.lunar_orbits

offload:
	python -m gatewaycx.ground_offload

ephemeris:
	python -m gatewaycx.ephemeris

links:
	python -m gatewaycx.link_budgets

datacentre:
	python -m gatewaycx.datacentre_trade

economics:
	python -m gatewaycx.economics

regional-faults:
	python -m gatewaycx.regional_fault_lab

figures:
	python tools/generate_figures.py

conformance:
	python -m gatewaycx.conformance profiles/bearers/*.json

test:
	python -m unittest discover -s tests -v

audit:
	python -m gatewaycx.cli audit

verify: scenarios disruption capacity placement admission handover updates preposition black-start diagnostics integrated adapters durable transport authenticated abrupt independent orbits offload ephemeris links datacentre economics regional-faults figures conformance audit test
	git diff --exit-code -- results/baseline.json results/S005_disruption.json results/S006_capacity_envelope.json results/S007_service_placement.json results/S009_admission.json results/S010_handover.json results/S011_update_delivery.json results/S012_prepositioning.json results/S013_black_start.json results/S014_diagnostic_trace.json results/S015_integrated_replay.json results/S016_adapter_probe.json results/S017_durable_restart.json results/S018_adapter_transport.json results/S019_authenticated_transport.json results/S020_abrupt_restart.json results/S021_independent_adapter.json results/S022_lunar_orbits.json results/S023_ground_offload.json results/S024_ephemeris.json results/S025_link_budgets.json results/S026_datacentre_trade.json results/S027_economics.json results/S028_regional_fault_lab.json profiles/diagnostics/gx-o1-fault-codes.json figures/*.svg
