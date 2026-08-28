.PHONY: scenarios disruption capacity placement admission handover updates preposition black-start diagnostics integrated adapters conformance audit test verify

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

conformance:
	python -m gatewaycx.conformance profiles/bearers/*.json

test:
	python -m unittest discover -s tests -v

audit:
	python -m gatewaycx.cli audit

verify: scenarios disruption capacity placement admission handover updates preposition black-start diagnostics integrated adapters conformance audit test
	git diff --exit-code -- results/baseline.json results/S005_disruption.json results/S006_capacity_envelope.json results/S007_service_placement.json results/S009_admission.json results/S010_handover.json results/S011_update_delivery.json results/S012_prepositioning.json results/S013_black_start.json results/S014_diagnostic_trace.json results/S015_integrated_replay.json results/S016_adapter_probe.json profiles/diagnostics/gx-o1-fault-codes.json
