from typing import List, Dict, Tuple, Optional
from operator import itemgetter
from dataclasses import dataclass

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

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

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
            })
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return a weighted similarity score (0.0–1.00) and a list of reason strings for one song."""
    score = 0.0
    reasons = []

    # --- Categorical matching ---
    if song["genre"] == user_prefs["genre"]:
        score += 0.25
        reasons.append(f"genre match (+0.25): both are '{song['genre']}'")

    if song["mood"] == user_prefs["mood"]:
        score += 0.35
        reasons.append(f"mood match (+0.35): both are '{song['mood']}'")

    # --- Numeric similarity: 1.0 - abs(song_value - target) ---
    energy_sim = 1.0 - abs(song["energy"] - user_prefs["target_energy"])
    score += energy_sim * 0.25
    reasons.append(f"energy score (+{energy_sim * 0.25:.2f}): song={song['energy']}, target={user_prefs['target_energy']}")

    valence_sim = 1.0 - abs(song["valence"] - user_prefs["target_valence"])
    score += valence_sim * 0.10
    reasons.append(f"valence score (+{valence_sim * 0.10:.2f}): song={song['valence']}, target={user_prefs['target_valence']}")

    acousticness_sim = 1.0 - abs(song["acousticness"] - user_prefs["target_acousticness"])
    score += acousticness_sim * 0.05
    reasons.append(f"acousticness score (+{acousticness_sim * 0.05:.2f}): song={song['acousticness']}, target={user_prefs['target_acousticness']}")

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort by score descending, and return the top k as (song, score, explanation) tuples."""
    scored = [
        (song, score, " | ".join(reasons))
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    ]
    return sorted(scored, key=itemgetter(1), reverse=True)[:k]
