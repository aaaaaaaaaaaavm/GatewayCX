# Results

`baseline.json` is generated from every `scenarios/S*.json` file by:

```bash
python -m gatewaycx.cli run-all
```

The file is committed so a change to code or assumptions produces a visible diff. It contains no
generation timestamp, which makes an unchanged run byte-for-byte reproducible.

All present results have evidence class `MODEL`. They are not observations of a real network.

