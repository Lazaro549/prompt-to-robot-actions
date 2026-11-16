# Demo capture guide

Use this to produce a short GIF or terminal recording for the README.

## Option A — terminal (asciinema / vhs)

```bash
pip install -e ".[dev]"
python -m examples.vision_agent_demo
python -m src.cli run "Pick the red cube and place it on the table" --backend composite
python tools/dashboard.py
```

Record with [asciinema](https://asciinema.org/) or [charmbracelet/vhs](https://github.com/charmbracelet/vhs).

## Option B — expected console output (fallback if no GIF yet)

```text
PROMPT: Inspect the area, then pick the red cube...
VISION (initial): Detected: red cube (id=red_cube, conf=0.94) at (1.50, 0.50, 0.10); blue cube ...

PLAN:
  1. inspect({'target': 'current_area'})
  2. pick({'object_id': 'red_cube'})
  3. place({'x': 0.0, 'y': 0.0, 'z': 0.1})

EXECUTION:
  ✓ inspect: Detected: red cube ...
  ✓ pick: [MoveIt-mock] Pick pipeline complete for red_cube
  ✓ place: [MoveIt-mock] Place pipeline complete for red_cube
```

Paste a real GIF path in README when available: `docs/demo.gif`.
