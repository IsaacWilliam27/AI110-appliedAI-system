"""
RecommendationAgent — multi-step reasoning with observable intermediate steps.

Each step in the pipeline is captured as an AgentStep so the UI can display
exactly what the AI considered at every stage of the decision-making process.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple

try:
    from src.recommender import score_song
except ImportError:
    from recommender import score_song


@dataclass
class AgentStep:
    """One observable reasoning step in the recommendation pipeline."""
    step_num: int
    name: str
    summary: str   # plain-English sentence for beginners
    detail: Any    # structured data for the expandable expert view


class RecommendationAgent:
    """
    Transparent recommendation agent.

    Runs the same scoring logic as recommend_songs() but records every
    intermediate decision so the UI can surface 'how the AI decided'.
    """

    def __init__(self, songs: List[Dict]):
        self.songs = songs
        self.steps: List[AgentStep] = []

    def run(
        self, user_prefs: Dict, k: int = 5
    ) -> Tuple[List[Tuple[Dict, float, str]], List["AgentStep"]]:
        self.steps = []

        # ── Step 1: Parse preferences ──────────────────────────────────────────
        genre = user_prefs.get("genre", "?")
        mood  = user_prefs.get("mood", "?")
        energy_pct = f"{user_prefs.get('target_energy', 0.7):.0%}"
        dance_pct  = f"{user_prefs.get('target_danceability', 0.6):.0%}"
        self.steps.append(AgentStep(
            step_num=1,
            name="Parse Your Preferences",
            summary=(
                f"You want **{genre}** music that feels **{mood}**. "
                f"Energy target: {energy_pct}, danceability target: {dance_pct}."
            ),
            detail={k: v for k, v in user_prefs.items()},
        ))

        # ── Step 2: Score every song ───────────────────────────────────────────
        n = len(self.songs)
        if n == 0:
            self.steps.append(AgentStep(
                step_num=2,
                name="Score Every Song",
                summary="The catalog is empty — nothing to score.",
                detail={"songs_evaluated": 0},
            ))
            self.steps.append(AgentStep(
                step_num=3, name="Apply Diversity",
                summary="No songs to diversify.",
                detail={},
            ))
            self.steps.append(AgentStep(
                step_num=4, name="Final Ranking",
                summary="No results to rank.",
                detail={"results": []},
            ))
            return [], self.steps

        scored: List[Tuple[Dict, float, List[str]]] = []
        for song in self.songs:
            s, reasons = score_song(user_prefs, song)
            scored.append((song, s, reasons))
        scored.sort(key=lambda x: x[1], reverse=True)

        top3 = [
            {"title": s["title"], "artist": s["artist"], "score": round(sc, 3)}
            for s, sc, _ in scored[:3]
        ]
        self.steps.append(AgentStep(
            step_num=2,
            name="Score Every Song",
            summary=(
                f"Evaluated all **{n} songs** across 6 features "
                f"(genre, mood, energy, danceability, positivity, acousticness). "
                f"Highest candidate: **{top3[0]['title']}** "
                f"({top3[0]['score']:.2f}/1.00)."
            ),
            detail={"songs_evaluated": n, "top_candidates_before_diversity": top3},
        ))

        # ── Step 3: Diversity filter ───────────────────────────────────────────
        seen: set = set()
        primary, fallback = [], []
        for item in scored:
            artist = item[0]["artist"]
            if artist not in seen:
                primary.append(item)
                seen.add(artist)
            else:
                fallback.append(item)
        diverse = (primary + fallback)[:k]

        unique_in_result = len({s["artist"] for s, _, _ in diverse})
        self.steps.append(AgentStep(
            step_num=3,
            name="Apply Diversity",
            summary=(
                f"Avoided repeating artists — final {len(diverse)} picks come from "
                f"**{unique_in_result} different artists** "
                f"(out of {len(seen)} unique artists in the full catalog)."
            ),
            detail={
                "unique_artists_in_catalog": len(seen),
                "unique_artists_in_result":  unique_in_result,
                "songs_selected": len(diverse),
            },
        ))

        # ── Step 4: Final ranking ──────────────────────────────────────────────
        final = [(s, sc, " | ".join(r)) for s, sc, r in diverse]
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        podium = [
            {
                "rank":   i + 1,
                "medal":  medals.get(i + 1, ""),
                "title":  s["title"],
                "artist": s["artist"],
                "score":  round(sc, 3),
            }
            for i, (s, sc, _) in enumerate(final[:3])
        ]
        best = podium[0]
        self.steps.append(AgentStep(
            step_num=4,
            name="Final Ranking",
            summary=(
                f"Top recommendation: {best['medal']} **{best['title']}** "
                f"by {best['artist']} — match score **{best['score']:.2f}** / 1.00."
            ),
            detail={"top_results": podium},
        ))

        return final, self.steps
