# Skull King Scorekeeper (Lite)

A lightweight **Skull King** scoring record app that keeps **only the current game** (no historical games).  
Run it locally (Windows/macOS/Linux), in Docker, or deploy to AWS.

- ✅ One active game at a time (Start/Reset overwrites the previous game)
- ✅ Editable round entry (bid, tricks, bonus override, optional loot alliances)
- ✅ Supports **Skull King** scoring and **Rascal** scoring
- ✅ Export results to **JSON** or **CSV** (and optionally save files on disk)

---

## Demo / Usage Flow

1. **Start / Reset** a game with:
   - Game name
   - Scoring mode (`skull_king` or `rascal`)
   - Rounds (e.g., 10)
   - Players (comma-separated)
2. **Enter / Edit round**
   - Choose round number
   - Fill **Bid** + **Tricks**
   - Optionally fill **Bonus Override** (total bonus points for that player that round)
   - Optionally add **Loot alliances** (pairs)
   - Click **Save Round**
3. View totals in **Scoreboard**
4. Download/export results:
   - **Download JSON** (full state + computed scoreboard)
   - **Download CSV** (round-by-round rows + final totals)

---

## Scoring Notes

This project implements scoring rules from the Skull King rulebook (including Rascal scoring variants and loot alliance bonus rules where applicable).

Bonus handling in this Lite UI uses **Bonus Override** (manual total bonus points per player per round) to keep the UI simple.

---

## Repository Structure
```bash
skullking-scorekeeper-lite/
  app/
    main.py
    scoring.py
    state_store.py
    templates/index.html
    static/app.js
    static/styles.css
  requirements.txt
  Dockerfile
  README.md

```

---

## Requirements

- Python **3.11+** (recommended)
- OR Docker (for container deployment)

---

## Run Locally (Python)

### macOS / Linux
```bash
cd skullking-scorekeeper-lite
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
### Windows (PowerShell)
```bash
cd skullking-scorekeeper-lite
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
---
### Run with Docker
```bash
docker build -t skullking-lite .
docker run -p 8000:8000 -e DATA_DIR=/app/data -v skullking_data:/app/data skullking-lite
```

### Open:

- http://localhost:8000

### Notes:

- ```-v skullking_data:/app/data``` keeps state.json and exported files persistent across container restarts.

---
### Export / Save results

The UI provides:

- Download JSON

- Download CSV

You can also call export endpoints directly:

- JSON: ```GET /api/export?format=json&save=true```

- CSV: ```GET /api/export?format=csv&save=true```

If ```save=true```, the server also writes a timestamped copy into ```DATA_DIR``` (default ```./data/```):

- ```skullking_<game>_<timestamp>.json```

- ```skullking_<game>_<timestamp>.csv```

---
### API quick reference
```GET /api/state```

Returns the current stored game state.

```POST /api/new_game```

Overwrites current state with a new game.

Example payload:

```{json}
{
  "name": "Friday night",
  "scoring_mode": "skull_king",
  "rounds": 10,
  "players": ["Alice", "Bob", "Carol"]
}
```

```PUT /api/round/{round_num}```

Saves results for a round.

Example payload:
```
{
  "results": {
    "Alice": { "bid": 1, "tricks": 1, "bonuses": { "bonus_override": 20 } },
    "Bob":   { "bid": 0, "tricks": 0, "bonuses": {} }
  },
  "alliances": [
    ["Alice", "Bob"]
  ]
}
```
```GET /api/scoreboard```

Returns computed leaderboard + per-round breakdown.

```GET /api/export?format=json|csv&save=true|false```

Downloads JSON/CSV export (and optionally writes to disk).

---
### Deploy notes (AWS)

This app is container-friendly:

1. Build & push the Docker image (ECR or GHCR)

2. Run it on:

    - Lightsail Container Service (simplest)

    - ECS Fargate (more control)

3. Set environment variables:

    -  ```DATA_DIR=/app/data```

4. Add persistent storage if you want state/exports to survive redeploys (volume/EFS/etc.)

### Roadmap ideas

- Bonus UI (14s + character bonuses) instead of manual Bonus Override

- Multi-room support (separate games by room code) while still avoiding long-term history

- Desktop “one-click” packaging (PyInstaller or Electron wrapper)

---
### License
- MIT