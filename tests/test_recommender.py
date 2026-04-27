from pathlib import Path
import pytest
from src.recommender import Song, UserProfile, Recommender, score_song, recommend_songs, load_songs

# --- Shared helpers ---

def make_user(genre="pop", mood="happy", energy=0.8, valence=0.82, acousticness=0.15, likes_acoustic=False):
    return {
        "genre": genre,
        "mood": mood,
        "target_energy": energy,
        "target_valence": valence,
        "target_acousticness": acousticness,
        "likes_acoustic": likes_acoustic,
    }

def make_song(genre="pop", mood="happy", energy=0.8, valence=0.8, acousticness=0.2, id=1):
    return {
        "id": id, "title": "Test Song", "artist": "Test Artist",
        "genre": genre, "mood": mood, "energy": energy,
        "tempo_bpm": 120, "valence": valence,
        "danceability": 0.7, "acousticness": acousticness,
    }


def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# --- score_song ---

def test_score_song_returns_float_and_list():
    """score_song must return a (float, list) tuple."""
    score, reasons = score_song(make_user(), make_song())
    assert isinstance(score, float)
    assert isinstance(reasons, list)

def test_score_song_perfect_match_is_max():
    """All scored features matching exactly should produce a score >= 0.94."""
    user = make_user(genre="pop", mood="happy", energy=0.8, valence=0.8, acousticness=0.2)
    user["target_danceability"] = 0.7  # matches make_song default; enables full danceability score
    song = make_song(genre="pop", mood="happy", energy=0.8, valence=0.8, acousticness=0.2)
    score, _ = score_song(user, song)
    assert score >= 0.94

def test_score_song_no_categorical_match_is_low():
    """A song with no genre or mood match should score below 0.5."""
    user = make_user(genre="pop", mood="happy", energy=0.5)
    song = make_song(genre="metal", mood="aggressive", energy=0.5)
    score, _ = score_song(user, song)
    assert score < 0.5

def test_score_song_always_between_0_and_1():
    """Score must stay in [0.0, 1.0] even when features are far apart."""
    user = make_user(energy=0.1, valence=0.1, acousticness=0.1)
    song = make_song(energy=0.9, valence=0.9, acousticness=0.9)
    score, _ = score_song(user, song)
    assert 0.0 <= score <= 1.0

def test_score_song_genre_match_adds_reason():
    """A genre match must appear in the reasons list."""
    _, reasons = score_song(make_user(genre="pop"), make_song(genre="pop"))
    assert any("genre match" in r for r in reasons)

def test_score_song_genre_mismatch_no_genre_reason():
    """No genre match means no genre reason should be added."""
    _, reasons = score_song(make_user(genre="pop"), make_song(genre="metal"))
    assert not any("genre match" in r for r in reasons)

def test_score_song_mood_match_adds_reason():
    """A mood match must appear in the reasons list."""
    _, reasons = score_song(make_user(mood="happy"), make_song(mood="happy"))
    assert any("mood match" in r for r in reasons)

def test_score_song_mood_outweighs_genre():
    """A mood-only match should score higher than a genre-only match."""
    user = make_user(genre="pop", mood="happy", energy=0.5, valence=0.5, acousticness=0.5)
    genre_only = make_song(genre="pop", mood="chill",   energy=0.5, valence=0.5, acousticness=0.5)
    mood_only  = make_song(genre="lofi", mood="happy",  energy=0.5, valence=0.5, acousticness=0.5)
    score_genre, _ = score_song(user, genre_only)
    score_mood, _  = score_song(user, mood_only)
    assert score_mood > score_genre

def test_score_song_missing_user_key_raises_value_error():
    """Missing required user preference keys should fail fast."""
    user = make_user()
    user.pop("target_valence")
    with pytest.raises(ValueError, match="Missing required user_prefs keys"):
        score_song(user, make_song())

def test_score_song_missing_song_key_raises_value_error():
    """Missing required song keys should fail fast."""
    song = make_song()
    song.pop("energy")
    with pytest.raises(ValueError, match="Missing required song keys"):
        score_song(make_user(), song)

def test_score_song_out_of_range_user_value_raises_value_error():
    """User target values must remain inside [0, 1]."""
    user = make_user(energy=1.4)
    with pytest.raises(ValueError, match="target_energy must be between 0.0 and 1.0"):
        score_song(user, make_song())

def test_score_song_non_numeric_song_value_raises_value_error():
    """Song numeric features must be valid numbers."""
    song = make_song()
    song["danceability"] = "very"
    with pytest.raises(ValueError, match="song.danceability must be a numeric value"):
        score_song(make_user(), song)


# --- recommend_songs ---

def test_recommend_songs_empty_catalog():
    """An empty catalog should return an empty list without crashing."""
    assert recommend_songs(make_user(), songs=[], k=5) == []

def test_recommend_songs_k_larger_than_catalog():
    """k larger than the catalog should return all songs, not raise an error."""
    songs = [make_song(id=i) for i in range(3)]
    assert len(recommend_songs(make_user(), songs, k=99)) == 3

def test_recommend_songs_sorted_descending():
    """Results must be ordered highest score first."""
    user = make_user(genre="pop", mood="happy")
    songs = [
        make_song(genre="metal", mood="aggressive", id=1),
        make_song(genre="pop",   mood="happy",      id=2),
        make_song(genre="lofi",  mood="chill",      id=3),
    ]
    results = recommend_songs(user, songs, k=3)
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)

def test_recommend_songs_k1_returns_best_match():
    """k=1 should return only the single highest-scoring song."""
    user = make_user(genre="pop", mood="happy")
    songs = [
        make_song(genre="metal", mood="aggressive", id=1),
        make_song(genre="pop",   mood="happy",      id=2),
    ]
    results = recommend_songs(user, songs, k=1)
    assert len(results) == 1
    assert results[0][0]["genre"] == "pop"

def test_recommend_songs_result_structure():
    """Each result must be a (dict, float, str) tuple."""
    results = recommend_songs(make_user(), [make_song()], k=1)
    song, score, explanation = results[0]
    assert isinstance(song, dict)
    assert isinstance(score, float)
    assert isinstance(explanation, str)

def test_recommend_songs_invalid_k_zero_raises_value_error():
    """k must be a positive integer."""
    with pytest.raises(ValueError, match="k must be greater than 0"):
        recommend_songs(make_user(), [make_song()], k=0)

def test_recommend_songs_invalid_k_type_raises_type_error():
    """k type validation should reject non-integers."""
    with pytest.raises(TypeError, match="k must be an integer"):
        recommend_songs(make_user(), [make_song()], k="2")

def test_recommender_recommend_invalid_k_raises_value_error():
    """Recommender class should enforce positive k as well."""
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    with pytest.raises(ValueError, match="k must be greater than 0"):
        rec.recommend(user, k=-1)


# --- load_songs ---

DATA = Path(__file__).parent.parent / "data" / "songs.csv"

def test_load_songs_returns_list():
    """load_songs must return a list."""
    assert isinstance(load_songs(DATA), list)

def test_load_songs_correct_count():
    """CSV has 18 songs (10 original + 8 added)."""
    assert len(load_songs(DATA)) == 18

def test_load_songs_numeric_types():
    """Numeric fields must be cast to the correct Python types."""
    song = load_songs(DATA)[0]
    assert isinstance(song["id"],           int)
    assert isinstance(song["tempo_bpm"],    int)
    assert isinstance(song["energy"],       float)
    assert isinstance(song["valence"],      float)
    assert isinstance(song["danceability"], float)
    assert isinstance(song["acousticness"], float)

def test_load_songs_required_keys():
    """Every song dict must contain all expected keys."""
    keys = {"id", "title", "artist", "genre", "mood",
            "energy", "tempo_bpm", "valence", "danceability", "acousticness"}
    for song in load_songs(DATA):
        assert keys.issubset(song.keys())
