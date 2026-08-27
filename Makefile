.PHONY: scenarios capacity audit test verify

scenarios:
	python -m gatewaycx.cli run-all

capacity:
	python -m gatewaycx.capacity

test:
	python -m unittest discover -s tests -v

audit:
	python -m gatewaycx.cli audit

verify: scenarios capacity audit test
	git diff --exit-code -- results/baseline.json results/S006_capacity_envelope.json
