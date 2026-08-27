.PHONY: scenarios audit test verify

scenarios:
	python -m gatewaycx.cli run-all

test:
	python -m unittest discover -s tests -v

audit:
	python -m gatewaycx.cli audit

verify: scenarios audit test
	git diff --exit-code -- results/baseline.json
