from __future__ import annotations

from typing import Dict, Any, Literal, Tuple

ScoringMode = Literal["skull_king", "rascal"]

def _accuracy(bid: int, tricks: int) -> int:
    return abs(int(tricks) - int(bid))

def calc_bonus(b: Dict[str, Any]) -> int:
    # bonus_override if you want a manual override
    if b.get("bonus_override") is not None:
        return int(b["bonus_override"])

    bonus = 0
    bonus += 10 * int(bool(b.get("has_14_green")))
    bonus += 10 * int(bool(b.get("has_14_yellow")))
    bonus += 10 * int(bool(b.get("has_14_purple")))
    bonus += 20 * int(bool(b.get("has_14_black")))

    bonus += 20 * max(0, int(b.get("mermaid_taken_by_pirate", 0)))
    bonus += 30 * max(0, int(b.get("pirate_taken_by_skullking", 0)))
    bonus += 40 * max(0, int(b.get("skullking_taken_by_mermaid", 0)))
    return bonus

def base_score(mode: ScoringMode, cards_dealt: int, bid: int, tricks: int, rascal_load: str | None) -> int:
    bid, tricks, cards_dealt = int(bid), int(tricks), int(cards_dealt)
    acc = _accuracy(bid, tricks)

    if mode == "skull_king":
        if acc == 0:
            return (10 * cards_dealt) if bid == 0 else (20 * bid)
        return (-10 * cards_dealt) if bid == 0 else (-10 * acc)

    # rascal
    potential = 10 * cards_dealt
    if rascal_load == "cannonball":
        return (15 * cards_dealt) if acc == 0 else 0
    if acc == 0:
        return potential
    if acc == 1:
        return potential // 2
    return 0

def loot_bonus_for_round(alliances: list[list[str]], exact: Dict[str, bool]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for a, b in alliances:
        if exact.get(a, False) and exact.get(b, False):
            out[a] = out.get(a, 0) + 20
            out[b] = out.get(b, 0) + 20
    return out

def score_round_for_player(
    mode: ScoringMode,
    cards_dealt: int,
    player_result: Dict[str, Any],
    loot_bonus: int,
) -> Tuple[int, int, int]:
    bid = int(player_result.get("bid", 0))
    tricks = int(player_result.get("tricks", 0))
    rascal_load = player_result.get("rascal_load")
    bonuses = player_result.get("bonuses", {})

    acc = _accuracy(bid, tricks)
    base = base_score(mode, cards_dealt, bid, tricks, rascal_load)
    bonus = calc_bonus(bonuses)

    if mode == "skull_king":
        bonus = bonus if acc == 0 else 0
        loot = loot_bonus if acc == 0 else 0
        return base, bonus + loot, base + bonus + loot

    # rascal scaling (standard): full/half/none, cannonball exact-only handled in base and here
    if rascal_load == "cannonball":
        bonus = bonus if acc == 0 else 0
        loot = loot_bonus if acc == 0 else 0
        return base, bonus + loot, base + bonus + loot

    factor = 1.0 if acc == 0 else (0.5 if acc == 1 else 0.0)
    scaled_bonus = int(bonus * factor)
    scaled_loot = int(loot_bonus * factor)
    return base, scaled_bonus + scaled_loot, base + scaled_bonus + scaled_loot
