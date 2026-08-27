.PHONY: scenarios capacity placement admission handover updates preposition black-start conformance audit test verify

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

updates:
	python -m gatewaycx.update_delivery

preposition:
	python -m gatewaycx.preposition

black-start:
	python -m gatewaycx.black_start

conformance:
	python -m gatewaycx.conformance profiles/bearers/*.json

test:
	python -m unittest discover -s tests -v

audit:
	python -m gatewaycx.cli audit

verify: scenarios capacity placement admission handover updates preposition black-start conformance audit test
	git diff --exit-code -- results/baseline.json results/S006_capacity_envelope.json results/S007_service_placement.json results/S009_admission.json results/S010_handover.json results/S011_update_delivery.json results/S012_prepositioning.json results/S013_black_start.json
