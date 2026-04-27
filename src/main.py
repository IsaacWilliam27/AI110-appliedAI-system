"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from pathlib import Path

try:
    from src.recommender import load_songs, recommend_songs
except ImportError:
    from recommender import load_songs, recommend_songs

DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"


def main() -> None:
    songs = load_songs(DATA_PATH)

    # Verification profile: pop / happy
    user_prefs = {
        "genre":                "pop",
        "mood":                 "happy",
        "target_energy":        0.80,
        "target_danceability":  0.85,
        "target_dance_style":   "pop",
        "target_valence":       0.82,
        "target_acousticness":  0.15,
        "likes_acoustic":       False,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\n" + "=" * 60)
    print(f"  Top {len(recommendations)} Recommendations")
    print(f"  Profile : {user_prefs['genre']} / {user_prefs['mood']} / energy {user_prefs['target_energy']}")
    print("=" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n#{rank}  {song['title']} — {song['artist']}")
        print(f"    Score  : {score:.2f}  |  Genre: {song['genre']}  |  Mood: {song['mood']}")
        print("    Reasons:")
        for reason in explanation.split(" | "):
            print(f"      · {reason}")
        print("-" * 60)


if __name__ == "__main__":
    main()
