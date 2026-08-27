.PHONY: scenarios capacity placement admission handover conformance audit test verify

scenarios:
	python -m gatewaycx.cli run-all

capacity:
	python -m gatewaycx.capacity

placement:
	python -m gatewaycx.placement

admission:
	python -m gatewaycx.admission

handover:
	python -m gatewaycx.handover

conformance:
	python -m gatewaycx.conformance profiles/bearers/*.json

test:
	python -m unittest discover -s tests -v

audit:
	python -m gatewaycx.cli audit

verify: scenarios capacity placement admission handover conformance audit test
	git diff --exit-code -- results/baseline.json results/S006_capacity_envelope.json results/S007_service_placement.json results/S009_admission.json results/S010_handover.json
