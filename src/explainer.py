"""
Few-shot explanation generator.

Two explanation modes are defined via few-shot example sets:
  - "beginner": warm, emoji-rich, plain-English sentences
  - "expert":   terse numeric summary matching the scoring weights

Output measurably differs from both the raw reason-string baseline and from
each other — different vocabulary, structure, and information emphasis.
"""
from typing import Dict, List

# ── Few-shot examples ─────────────────────────────────────────────────────────
# Each example is a feature fingerprint + the target output string for that mode.
# _nearest_shot() selects the example whose booleans best match the actual song.

_BEGINNER_SHOTS: List[Dict] = [
    {
        "genre_match": True,  "mood_match": True,
        "energy_hi": True,  "acoustic_hi": False, "score_hi": True,
        "output": "Everything clicks — same genre, same mood, and it'll get you moving.",
    },
    {
        "genre_match": True,  "mood_match": True,
        "energy_hi": False, "acoustic_hi": True,  "score_hi": True,
        "output": "Genre and mood are spot-on, with a soft acoustic feel that suits your taste.",
    },
    {
        "genre_match": True,  "mood_match": False,
        "energy_hi": True,  "acoustic_hi": False, "score_hi": False,
        "output": "Right genre with great energy — the mood is a bit off but it's a solid pick.",
    },
    {
        "genre_match": False, "mood_match": True,
        "energy_hi": True,  "acoustic_hi": False, "score_hi": False,
        "output": "The mood hits just right and the energy is strong — genre is different but it'll feel good.",
    },
    {
        "genre_match": False, "mood_match": True,
        "energy_hi": False, "acoustic_hi": True,  "score_hi": False,
        "output": "The mood resonates and it's nicely mellow — genre is different, but chill vibes carry through.",
    },
    {
        "genre_match": False, "mood_match": False,
        "energy_hi": False, "acoustic_hi": False, "score_hi": False,
        "output": "A bit of a stretch — different genre and mood, but the numeric features were close.",
    },
]

_EXPERT_SHOTS: List[Dict] = [
    {
        "genre_match": True,  "mood_match": True,
        "energy_hi": True,  "acoustic_hi": False, "score_hi": True,
        "output": "genre(+0.25) mood(+0.30) energy↑ danceability↑ — full categorical match.",
    },
    {
        "genre_match": True,  "mood_match": True,
        "energy_hi": False, "acoustic_hi": True,  "score_hi": True,
        "output": "genre(+0.25) mood(+0.30) energy↓ acousticness↑ — categorical match; numeric mixed.",
    },
    {
        "genre_match": True,  "mood_match": False,
        "energy_hi": True,  "acoustic_hi": False, "score_hi": False,
        "output": "genre(+0.25) mood(miss) energy↑ — partial; mood penalty limits ceiling.",
    },
    {
        "genre_match": False, "mood_match": True,
        "energy_hi": True,  "acoustic_hi": False, "score_hi": False,
        "output": "genre(miss) mood(+0.30) energy↑ — mood dominant; genre mismatch.",
    },
    {
        "genre_match": False, "mood_match": True,
        "energy_hi": False, "acoustic_hi": True,  "score_hi": False,
        "output": "genre(miss) mood(+0.30) energy↓ acousticness↑ — mood saves score.",
    },
    {
        "genre_match": False, "mood_match": False,
        "energy_hi": False, "acoustic_hi": False, "score_hi": False,
        "output": "genre(miss) mood(miss) — numeric contributions only; low ceiling.",
    },
]


def _featurize(song: Dict, score: float, user_prefs: Dict) -> Dict:
    return {
        "genre_match": song.get("genre") == user_prefs.get("genre"),
        "mood_match":  song.get("mood")  == user_prefs.get("mood"),
        "energy_hi":   song.get("energy", 0.5) > 0.6,
        "acoustic_hi": song.get("acousticness", 0.3) > 0.5,
        "score_hi":    score >= 0.70,
    }


def _nearest_shot(feats: Dict, shots: List[Dict]) -> Dict:
    """Select the few-shot example whose boolean flags best match feats."""
    keys = ("genre_match", "mood_match", "energy_hi", "acoustic_hi", "score_hi")
    return min(shots, key=lambda s: sum(feats[k] != s[k] for k in keys))


def generate_explanation(
    song: Dict,
    score: float,
    user_prefs: Dict,
    mode: str = "beginner",
) -> str:
    """
    Return a natural-language explanation for one recommendation.

    mode="beginner" → warm, emoji-annotated, plain English
    mode="expert"   → terse numeric shorthand

    The output measurably differs between modes: beginner uses full sentences
    and percentage framing; expert uses arrow notation and parenthetical deltas.
    Both differ from the raw baseline reason-string produced by score_song().
    """
    feats    = _featurize(song, score, user_prefs)
    shots    = _BEGINNER_SHOTS if mode == "beginner" else _EXPERT_SHOTS
    template = _nearest_shot(feats, shots)["output"]
    genre    = song.get("genre", "?")
    mood     = song.get("mood", "?")
    pct      = f"{score * 100:.0f}%"

    if mode == "beginner":
        if score >= 0.85:
            star = "🌟"
        elif score >= 0.65:
            star = "✅"
        elif score >= 0.45:
            star = "🟡"
        else:
            star = "🔴"
        return f"{star} **{pct} match** — {template}"
    else:
        return f"[{score:.3f}] {template} | genre={genre}, mood={mood}"
