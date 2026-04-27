#!/usr/bin/env python3
"""
Evaluation harness for the VibeMatch recommendation system.

Runs predefined test cases and prints a pass/fail summary with
confidence ratings (how far from the threshold each check landed).

Usage:
    python -m tests.eval_harness
    python tests/eval_harness.py
"""
import sys
from pathlib import Path
from typing import List, Tuple, Any

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.recommender import recommend_songs, score_song, load_songs

# ── Helpers ───────────────────────────────────────────────────────────────────

def _song(id, title, artist, genre, mood, energy, bpm, valence, dance, acoustic):
    return {
        "id": id, "title": title, "artist": artist,
        "genre": genre, "mood": mood, "energy": energy,
        "tempo_bpm": bpm, "valence": valence,
        "danceability": dance, "acousticness": acoustic,
    }

def _user(genre, mood, energy=0.7, valence=0.65, dance=0.6, acoustic=0.2):
    return {
        "genre": genre, "mood": mood,
        "target_energy": energy, "target_valence": valence,
        "target_danceability": dance, "target_acousticness": acoustic,
    }

# ── Test cases ────────────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "name": "Pop/Happy — top result must be pop+happy",
        "user": _user("pop", "happy", energy=0.8, valence=0.8, dance=0.7, acoustic=0.2),
        "songs": [
            _song(1, "Pop Banger",   "A", "pop",   "happy",      0.8, 120, 0.8, 0.7, 0.2),
            _song(2, "Metal Storm",  "B", "metal", "aggressive", 0.9, 180, 0.2, 0.3, 0.05),
        ],
        "checks": [("top_genre", "pop"), ("top_mood", "happy"), ("min_score", 0.90)],
    },
    {
        "name": "Lofi/Chill — acoustic preference rewarded",
        "user": _user("lofi", "chill", energy=0.3, valence=0.5, dance=0.4, acoustic=0.9),
        "songs": [
            _song(3, "Lofi Rain",   "C", "lofi", "chill",   0.3, 75,  0.5, 0.4, 0.9),
            _song(4, "Club Banger", "D", "edm",  "euphoric", 0.95, 140, 0.9, 0.95, 0.05),
        ],
        "checks": [("top_genre", "lofi"), ("top_mood", "chill"), ("min_score", 0.85)],
    },
    {
        "name": "Empty catalog — returns []",
        "user": _user("pop", "happy"),
        "songs": [],
        "checks": [("empty", True)],
    },
    {
        "name": "k > catalog — returns all songs without error",
        "user": _user("pop", "happy"),
        "songs": [_song(5, "Song A", "X", "pop", "happy", 0.8, 120, 0.8, 0.7, 0.2)],
        "k": 99,
        "checks": [("result_count", 1)],
    },
    {
        "name": "Mood outweighs genre — mood-only match ranked above genre-only",
        "user": _user("pop", "happy", energy=0.5, valence=0.5, dance=0.5, acoustic=0.5),
        "songs": [
            _song(6, "Genre Only", "E", "pop",  "chill", 0.5, 100, 0.5, 0.5, 0.5),
            _song(7, "Mood Only",  "F", "lofi", "happy", 0.5, 100, 0.5, 0.5, 0.5),
        ],
        "checks": [("top_mood", "happy")],
    },
    {
        "name": "Score always in [0, 1] — extreme mismatch",
        "user": _user("classical", "peaceful", energy=0.05, valence=0.05, dance=0.05, acoustic=0.05),
        "songs": [
            _song(8, "Extreme Metal", "G", "metal", "aggressive", 0.99, 200, 0.99, 0.99, 0.99),
        ],
        "checks": [("score_range", (0.0, 1.0))],
    },
    {
        "name": "Results sorted descending — 3 songs",
        "user": _user("pop", "happy", energy=0.8, valence=0.8, dance=0.7, acoustic=0.2),
        "songs": [
            _song(9,  "Best",   "H", "pop",   "happy",      0.8, 120, 0.8, 0.7, 0.2),
            _song(10, "Decent", "I", "pop",   "chill",      0.6, 100, 0.6, 0.5, 0.4),
            _song(11, "Worst",  "J", "metal", "aggressive", 0.9, 180, 0.2, 0.3, 0.05),
        ],
        "checks": [("sorted_desc", True)],
    },
    {
        "name": "Perfect match score >= 0.94",
        "user": {
            "genre": "pop", "mood": "happy",
            "target_energy": 0.8, "target_valence": 0.8,
            "target_danceability": 0.7, "target_acousticness": 0.2,
        },
        "songs": [
            _song(12, "Perfect", "K", "pop", "happy", 0.8, 120, 0.8, 0.7, 0.2),
        ],
        "checks": [("min_score", 0.94)],
    },
    {
        "name": "No categorical match — score < 0.5",
        "user": _user("pop", "happy", energy=0.5, valence=0.5, dance=0.5, acoustic=0.5),
        "songs": [
            _song(13, "Mismatch", "L", "metal", "aggressive", 0.5, 120, 0.5, 0.5, 0.5),
        ],
        "checks": [("max_score", 0.5)],
    },
    {
        "name": "Live catalog loads and has at least 10 songs",
        "catalog": True,
        "checks": [("catalog_min_size", 10)],
    },
]

# ── Check evaluators ──────────────────────────────────────────────────────────

def _evaluate_check(
    check_type: str,
    check_val: Any,
    results: list,
    catalog_songs: list,
) -> Tuple[bool, str]:
    """Return (passed, detail_string)."""

    if check_type == "top_genre":
        if not results:
            return False, "result list is empty"
        actual = results[0][0]["genre"]
        return actual == check_val, f"top genre = '{actual}' (expected '{check_val}')"

    if check_type == "top_mood":
        if not results:
            return False, "result list is empty"
        actual = results[0][0]["mood"]
        return actual == check_val, f"top mood = '{actual}' (expected '{check_val}')"

    if check_type == "min_score":
        if not results:
            return False, "result list is empty"
        score = results[0][1]
        margin = score - check_val
        return score >= check_val, f"score = {score:.4f} (min {check_val:.2f}, margin {margin:+.4f})"

    if check_type == "max_score":
        if not results:
            return False, "result list is empty"
        score = results[0][1]
        margin = check_val - score
        return score < check_val, f"score = {score:.4f} (max {check_val:.2f}, margin {margin:+.4f})"

    if check_type == "empty":
        passed = len(results) == 0
        return passed, f"result count = {len(results)} (expected 0)"

    if check_type == "result_count":
        passed = len(results) == check_val
        return passed, f"result count = {len(results)} (expected {check_val})"

    if check_type == "score_range":
        lo, hi = check_val
        all_ok = all(lo <= sc <= hi for _, sc, _ in results)
        out_of_range = [(s["title"], round(sc, 4)) for s, sc, _ in results if not (lo <= sc <= hi)]
        return all_ok, f"all in [{lo},{hi}]" if all_ok else f"out of range: {out_of_range}"

    if check_type == "sorted_desc":
        scores = [sc for _, sc, _ in results]
        is_sorted = scores == sorted(scores, reverse=True)
        return is_sorted, f"scores = {[round(s, 3) for s in scores]}"

    if check_type == "catalog_min_size":
        n = len(catalog_songs)
        return n >= check_val, f"catalog size = {n} (min {check_val})"

    return False, f"unknown check type '{check_type}'"


# ── Runner ────────────────────────────────────────────────────────────────────

_W = 62  # print column width


def run_evaluation() -> int:
    """Run all test cases; return exit code (0=all pass, 1=failures)."""
    print("=" * _W)
    print("  VibeMatch — Evaluation Harness")
    print("=" * _W)

    catalog_songs: list = []
    if (ROOT / "data" / "songs.csv").exists():
        catalog_songs = load_songs(ROOT / "data" / "songs.csv")

    total = passed = failed = 0

    for case in TEST_CASES:
        name = case["name"]
        print(f"\n>>  {name}")

        if case.get("catalog"):
            results = []
        else:
            user  = case["user"]
            songs = case.get("songs", [])
            k     = case.get("k", 5)
            results = recommend_songs(user, songs, k=k)

        for check_type, check_val in case["checks"]:
            total += 1
            ok, detail = _evaluate_check(check_type, check_val, results, catalog_songs)
            status = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            else:
                failed += 1
            print(f"   [{status}] {check_type}: {detail}")

    print("\n" + "=" * _W)
    pct = passed / total * 100 if total else 0
    print(f"  Results: {passed}/{total} checks passed  ({pct:.0f}%)")
    if failed == 0:
        print("  Status : ALL PASS")
    else:
        print(f"  Status : {failed} FAILURE(S)")
    print("=" * _W)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_evaluation())
