from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from .state_store import load_state, save_state, reset_state
from .scoring import score_round_for_player, loot_bonus_for_round

import io
import os
import csv
import json
import re
from datetime import datetime
from fastapi.responses import StreamingResponse


app = FastAPI(title="Skull King Scorekeeper Lite")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/state")
def get_state():
    return load_state()

@app.post("/api/new_game")
def new_game(payload: dict):
    name = str(payload.get("name", "")).strip() or "Current Game"
    scoring_mode = payload.get("scoring_mode", "skull_king")
    rounds = int(payload.get("rounds", 10))
    players = payload.get("players", [])
    if not isinstance(players, list) or not all(isinstance(p, str) and p.strip() for p in players):
        raise HTTPException(400, "players must be a list of names")
    players = [p.strip() for p in players]
    return reset_state(name, scoring_mode, rounds, players)

@app.put("/api/round/{round_num}")
def set_round(round_num: int, payload: dict):
    st = load_state()
    if round_num < 1 or round_num > int(st["rounds"]):
        raise HTTPException(400, "round out of range")

    # payload: { "results": { "Alice": {...}, "Bob": {...} }, "alliances": [[A,B],...] }
    results = payload.get("results", {})
    alliances = payload.get("alliances", [])
    if not isinstance(results, dict):
        raise HTTPException(400, "results must be an object keyed by player name")
    if not isinstance(alliances, list):
        raise HTTPException(400, "alliances must be a list")

    # Store
    st["round_results"][str(round_num)] = results
    st["loot_alliances"][str(round_num)] = alliances
    save_state(st)
    return {"ok": True}
def compute_scoreboard(st: dict) -> dict:
    mode = st["scoring_mode"]
    players = st["players"]
    rounds = int(st["rounds"])

    totals = {p: 0 for p in players}
    per_round = []

    for n in range(1, rounds + 1):
        rd_key = str(n)
        cards_dealt = n
        results = st["round_results"].get(rd_key, {})
        alliances = st["loot_alliances"].get(rd_key, [])

        exact = {
            p: (int(results.get(p, {}).get("bid", 0)) == int(results.get(p, {}).get("tricks", 0)))
            for p in players
        }
        loot_map = loot_bonus_for_round(alliances, exact)

        rows = []
        for p in players:
            pr = results.get(p)
            if not pr:
                continue
            base, bonus, total = score_round_for_player(mode, cards_dealt, pr, loot_map.get(p, 0))
            totals[p] += total
            rows.append({
                "player": p,
                "bid": pr.get("bid", 0),
                "tricks": pr.get("tricks", 0),
                "base": base,
                "bonus": bonus,
                "round_points": total,
                "running_total": totals[p],
            })

        per_round.append({"round": n, "cards_dealt": cards_dealt, "rows": rows})

    leaderboard = sorted(
        [{"player": p, "total": totals[p]} for p in players],
        key=lambda x: x["total"],
        reverse=True,
    )

    return {
        "state": {
            "name": st["name"],
            "scoring_mode": mode,
            "rounds": rounds,
            "players": players
        },
        "leaderboard": leaderboard,
        "rounds": per_round
    }

@app.get("/api/scoreboard")
def scoreboard():
    st = load_state()
    return compute_scoreboard(st)

def _safe_filename(name: str) -> str:
    name = name.strip() or "game"
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name[:60]

@app.get("/api/export")
def export(format: str = "json", save: bool = True):
    """
    format: json | csv
    save: if True, also writes a copy into DATA_DIR (e.g., ./data/)
    """
    st = load_state()
    sb = compute_scoreboard(st)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"skullking_{_safe_filename(st.get('name','game'))}_{ts}"
    data_dir = os.getenv("DATA_DIR", os.path.join(os.getcwd(), "data"))
    os.makedirs(data_dir, exist_ok=True)

    fmt = (format or "json").lower().strip()

    if fmt == "csv":
        # CSV rows: one row per (round, player)
        output = io.StringIO()
        w = csv.writer(output)
        w.writerow(["game", st.get("name",""), "mode", st.get("scoring_mode",""), "rounds", st.get("rounds","")])
        w.writerow([])
        w.writerow(["round", "player", "bid", "tricks", "base", "bonus", "round_points", "running_total"])

        for r in sb["rounds"]:
            for row in r["rows"]:
                w.writerow([
                    r["round"],
                    row["player"],
                    row["bid"],
                    row["tricks"],
                    row["base"],
                    row["bonus"],
                    row["round_points"],
                    row["running_total"],
                ])

        w.writerow([])
        w.writerow(["FINAL TOTALS"])
        w.writerow(["player", "total"])
        for x in sb["leaderboard"]:
            w.writerow([x["player"], x["total"]])

        csv_bytes = output.getvalue().encode("utf-8")

        if save:
            path = os.path.join(data_dir, base + ".csv")
            with open(path, "wb") as f:
                f.write(csv_bytes)

        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{base}.csv"'},
        )

    # default json
    payload = {
        "exported_at": ts,
        "state": st,
        "scoreboard": sb
    }
    json_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

    if save:
        path = os.path.join(data_dir, base + ".json")
        with open(path, "wb") as f:
            f.write(json_bytes)

    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{base}.json"'},
    )
