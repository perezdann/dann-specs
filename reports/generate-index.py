#!/usr/bin/env python3
"""Regenerates reports-index.json from all JSON reports in the reports/ folder."""
import json
from pathlib import Path
from datetime import datetime

def main():
    reports_dir = Path(__file__).parent
    index_path = reports_dir / "reports-index.json"

    reports = []
    for json_file in sorted(reports_dir.glob("*.json")):
        try:
            data = json.load(open(json_file))
            reports.append({
                "timestamp": data.get("timestamp", json_file.stem),
                "provider": data.get("provider", "unknown"),
                "suite": data.get("suite", "unknown"),
                "total_tests": data.get("total_tests", 0),
                "passed": data.get("passed", 0),
                "average_score": data.get("average_score", 0),
                "filename": json_file.name,
                "config_used": data.get("config_used", {})
            })
        except Exception as e:
            print(f"Skipping {json_file}: {e}")

    index = {
        "generated": datetime.now().isoformat(),
        "total_reports": len(reports),
        "reports": reports
    }

    json.dump(index, open(index_path, "w"), indent=2)
    print(f"Generated {index_path} with {len(reports)} reports")

if __name__ == "__main__":
    main()
