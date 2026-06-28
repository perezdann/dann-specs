# Community Test Reports

This directory contains real-world evaluation reports contributed by users running the `dann-specs` test harness against different models and providers.

## How Reports Are Generated

```bash
cd project/tests
python3 harness/test_runner.py --suite all --count 30 --real-llm
```

The runner automatically saves:
- Detailed JSON: `YYYYMMDD-HHMMSS-provider-suite.json`
- Markdown summary: `YYYYMMDD-HHMMSS-provider-suite.md`

## Viewing the Reports

When GitHub Pages is enabled for this repository (Settings → Pages → Source: `main` / `/docs`), the reports are publicly visible at:

https://perezdann.github.io/dann-specs/reports/

A simple JavaScript viewer (`index.html`) loads `reports-index.json`.

To update the index after adding new reports:

```bash
python3 reports/generate-index.py
git add reports/
git commit -m "Add community test reports"
git push
```

## Contributing

1. Run the test suite with your model(s).
2. Commit the generated report files.
3. (Optional) Run `reports/generate-index.py` and commit the updated index.

Reports help the community understand:
- Which guidelines are consistently followed by different models
- Where the specification needs to be strengthened
- Performance differences across providers

All reports are welcome — local llama.cpp, Groq, OpenAI, Anthropic, etc.
