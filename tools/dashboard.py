#!/usr/bin/env python3
"""Generate a static HTML dashboard from logs/*.json."""

from __future__ import annotations

import json
from pathlib import Path


def build_dashboard(log_dir: Path = Path("logs"), out: Path = Path("logs/dashboard.html")) -> Path:
    rows = []
    total = success = 0
    cost_sum = 0.0
    for path in sorted(log_dir.glob("run_*.json")):
        data = json.loads(path.read_text())
        total += 1
        if data.get("overall_success"):
            success += 1
        tokens = data.get("token_usage") or {}
        latency = (data.get("latency_ms") or {}).get("total", "")
        rows.append(
            "<tr>"
            f"<td>{path.name}</td>"
            f"<td>{data.get('planner')}</td>"
            f"<td>{'yes' if data.get('overall_success') else 'no'}</td>"
            f"<td>{tokens.get('total_tokens', '')}</td>"
            f"<td>{latency}</td>"
            f"<td>{(data.get('prompt') or '')[:80]}</td>"
            "</tr>"
        )
        extra = data.get("extra") or {}
        if "total_cost_usd" in extra:
            cost_sum += float(extra["total_cost_usd"])

    rate = f"{(100 * success / total):.1f}%" if total else "n/a"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>PTRA Run Dashboard</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }}
th {{ background: #f4f4f4; }}
.summary {{ margin-bottom: 1rem; }}
</style></head><body>
<h1>Prompt-to-Robot-Actions — Runs</h1>
<div class="summary">
  <strong>Runs:</strong> {total} &
bsp;
  <strong>Success rate:</strong> {rate} &
bsp;
  <strong>Est. cost sum:</strong> ${cost_sum:.4f}
</div>
<table>
<thead><tr>
  <th>File</th><th>Planner</th><th>Success</th><th>Tokens</th><th>Latency ms</th><th>Prompt</th>
</tr></thead>
<tbody>
{''.join(rows) if rows else '<tr><td colspan="6">No logs yet. Run the pipeline first.</td></tr>'}
</tbody></table>
</body></html>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    path = build_dashboard()
    print(f"Dashboard written to {path}")
