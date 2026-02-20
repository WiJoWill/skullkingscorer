from __future__ import annotations

import json
import os
from typing import Any, Dict

DEFAULT_STATE: Dict[str, Any] = {
    "name": "Current Game",
    "scoring_mode": "skull_king",  # or "rascal"
    "rounds": 10,
    "players": [],
    "round_results": {},  # str(round_num) -> { player_name -> result_obj }
    "loot_alliances": {}, # str(round_num) -> [ [playerA, playerB], ... ]
}

def _path() -> str:
    data_dir = os.getenv("DATA_DIR", os.path.join(os.getcwd(), "data"))
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "state.json")

def load_state() -> Dict[str, Any]:
    p = _path()
    if not os.path.exists(p):
        save_state(DEFAULT_STATE)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state: Dict[str, Any]) -> None:
    p = _path()
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)

def reset_state(name: str, scoring_mode: str, rounds: int, players: list[str]) -> Dict[str, Any]:
    st = {
        "name": name,
        "scoring_mode": scoring_mode,
        "rounds": int(rounds),
        "players": players,
        "round_results": {},
        "loot_alliances": {},
    }
    save_state(st)
    return st
