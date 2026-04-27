import math
from typing import List, Dict, Tuple, Optional
from operator import itemgetter
from dataclasses import dataclass


def _require_keys(payload: Dict, required: List[str], name: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Missing required {name} keys: {', '.join(missing)}")


def _coerce_unit_interval(value, field_name: str) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a numeric value") from exc
    if not 0.0 <= num <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")
    return num


def _validate_k(k: int) -> None:
    if not isinstance(k, int):
        raise TypeError("k must be an integer")
    if k <= 0:
        raise ValueError("k must be greater than 0")

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    dance_style: str = "none"

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


def _gaussian_sim(song_val: float, target: float, sigma: float = 0.25) -> float:
    """Gaussian kernel similarity — 1.0 at zero difference, decays smoothly with distance."""
    if sigma <= 0:
        raise ValueError("sigma must be greater than 0")
    return math.exp(-((song_val - target) ** 2) / (2 * sigma ** 2))


def _profile_to_prefs(user: UserProfile) -> Dict:
    """Convert a UserProfile dataclass to the user_prefs dict format expected by score_song."""
    return {
        "genre": user.favorite_genre,
        "mood": user.favorite_mood,
        "target_energy": user.target_energy,
        "target_valence": 0.5,
        "target_acousticness": 1.0 if user.likes_acoustic else 0.2,
    }


def _diversify(sorted_songs: List[Song], k: int) -> List[Song]:
    """Prefer artist variety; fill remaining slots with same-artist songs so k is always met."""
    seen_artists, primary, fallback = set(), [], []
    for song in sorted_songs:
        if song.artist not in seen_artists:
            primary.append(song)
            seen_artists.add(song.artist)
        else:
            fallback.append(song)
    return (primary + fallback)[:k]


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        _validate_k(k)
        prefs = _profile_to_prefs(user)
        scored = [(s, score_song(prefs, vars(s))[0]) for s in self.songs]
        sorted_songs = [s for s, _ in sorted(scored, key=lambda x: x[1], reverse=True)]
        return _diversify(sorted_songs, k)

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        prefs = _profile_to_prefs(user)
        score, reasons = score_song(prefs, vars(song))
        return f"Score: {score:.2f} | " + " | ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with numeric fields cast to int or float."""
    import csv
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    int(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
                "dance_style":  row.get("dance_style", "none"),
            })
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return a weighted similarity score (0.0–1.00) and a list of reason strings for one song."""
    _require_keys(
        user_prefs,
        ["genre", "mood", "target_energy", "target_valence", "target_acousticness"],
        "user_prefs",
    )
    _require_keys(
        song,
        ["genre", "mood", "energy", "danceability", "valence", "acousticness"],
        "song",
    )

    _coerce_unit_interval(user_prefs["target_energy"], "target_energy")
    _coerce_unit_interval(user_prefs["target_valence"], "target_valence")
    _coerce_unit_interval(user_prefs["target_acousticness"], "target_acousticness")
    _coerce_unit_interval(user_prefs.get("target_danceability", 0.5), "target_danceability")
    _coerce_unit_interval(song["energy"], "song.energy")
    _coerce_unit_interval(song["danceability"], "song.danceability")
    _coerce_unit_interval(song["valence"], "song.valence")
    _coerce_unit_interval(song["acousticness"], "song.acousticness")

    score = 0.0
    reasons = []

    # --- Categorical matching ---
    if song["genre"] == user_prefs["genre"]:
        score += 0.25
        reasons.append(f"genre match (+0.25): both are '{song['genre']}'")

    if song["mood"] == user_prefs["mood"]:
        score += 0.30
        reasons.append(f"mood match (+0.30): both are '{song['mood']}'")

    target_dance_style = user_prefs.get("target_dance_style", "none")
    if target_dance_style != "none" and song.get("dance_style") == target_dance_style:
        score += 0.07
        reasons.append(f"dance style match (+0.07): both are '{song['dance_style']}'")

    # --- Numeric similarity: Gaussian kernel (1.0 at zero diff, decays smoothly) ---
    energy_sim = _gaussian_sim(song["energy"], user_prefs["target_energy"])
    score += energy_sim * 0.18
    reasons.append(f"energy score (+{energy_sim * 0.18:.2f}): song={song['energy']}, target={user_prefs['target_energy']}")

    dance_sim = _gaussian_sim(song["danceability"], user_prefs.get("target_danceability", 0.5))
    score += dance_sim * 0.15
    reasons.append(f"danceability score (+{dance_sim * 0.15:.2f}): song={song['danceability']}, target={user_prefs.get('target_danceability', 0.5)}")

    valence_sim = _gaussian_sim(song["valence"], user_prefs["target_valence"])
    score += valence_sim * 0.05
    reasons.append(f"valence score (+{valence_sim * 0.05:.2f}): song={song['valence']}, target={user_prefs['target_valence']}")

    acousticness_sim = _gaussian_sim(song["acousticness"], user_prefs["target_acousticness"])
    score += acousticness_sim * 0.02
    reasons.append(f"acousticness score (+{acousticness_sim * 0.02:.2f}): song={song['acousticness']}, target={user_prefs['target_acousticness']}")

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort by score descending, and return the top k as (song, score, explanation) tuples."""
    _validate_k(k)
    scored = [
        (song, score, " | ".join(reasons))
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    ]
    return sorted(scored, key=itemgetter(1), reverse=True)[:k]
