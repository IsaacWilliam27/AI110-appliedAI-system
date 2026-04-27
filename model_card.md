# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**

---

## 2. Intended Use

VibeMatch 1.0 generates a ranked list of song recommendations from a small catalog based on a user's declared taste profile. It is designed for classroom exploration of how content-based recommender systems work — not for real-world deployment.

The system assumes the user can describe what they want before listening: a preferred genre, a mood they are in, and a rough sense of how energetic they want the music to feel. It does not learn from listening history, skips, or replays. Every recommendation is based entirely on the profile the user provides upfront.

---

## 3. How the Model Works

Imagine you tell a friend: "I want something lofi, focused, and not too intense." Your friend mentally scans their playlist and gives each song a rating based on how well it fits what you described. VibeMatch does the same thing, just with numbers.

For every song in the catalog, the system checks five things:

1. **Does the genre match?** If yes, the song earns a bonus of 0.25 points.
2. **Does the mood match?** If yes, the song earns a larger bonus of 0.35 points — mood is weighted higher because it reflects why you are listening, not just what you like in general.
3. **How close is the energy level?** The closer the song's energy is to your target, the more points it earns (up to 0.25). A song at exactly your target gets the full amount; a song far away gets much less.
4. **How close is the emotional tone (valence)?** Same idea — closeness earns up to 0.10 points.
5. **How close is the acoustic texture?** Songs that match your preference for organic versus electronic sound earn up to 0.05 points.

All five contributions are added together into a final score between 0.0 and 1.0. The songs are then sorted from highest to lowest score, and the top five are returned with a plain-language explanation of exactly why each one was chosen.

The key change from the starter logic was replacing a single `energy` key with three separate numeric targets (energy, valence, acousticness), which gives the scoring function a much richer picture of what the user actually wants.

---

## 4. Data

The catalog contains 18 songs stored in `data/songs.csv`. The original starter file had 10 songs; 8 more were added to expand genre and mood coverage.

**Genres represented:** pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, r&b, classical, metal, country, edm, blues, folk (15 total)

**Moods represented:** happy, chill, intense, relaxed, focused, moody, sad, romantic, peaceful, aggressive, nostalgic, euphoric, melancholic, dreamy (14 total)

Each song has five numeric features (energy, tempo, valence, danceability, acousticness) alongside its genre and mood labels. All numeric values were assigned to be internally consistent — for example, the metal song has the highest energy and lowest valence in the dataset, and the classical song has the highest acousticness.

Parts of musical taste that are still missing from the dataset include lyrics and language, artist familiarity, listening context (time of day, activity), cultural and regional music styles, and sub-genre distinctions (there is one "rock" song but no distinction between indie rock, classic rock, or punk).

---

## 5. Strengths

The system works best for users with clear, consistent preferences that map cleanly onto genre and mood labels. Testing with a pop/happy profile immediately surfaced Sunrise City (pop, happy, energy 0.82) as the top result with a score of 0.99 — exactly what a human would pick by hand. The lofi/focused profile correctly ranked Focus Flow first with a perfect score of 1.00, since every one of its features matched the target precisely.

The scoring also handles partial matches gracefully. Rooftop Lights scored second for a pop/happy user even though its genre is "indie pop" — because its mood and numeric features were close enough to compensate. This mirrors how real recommendations work: a near-miss on one feature does not disqualify a song if everything else fits.

The explanation output is a particular strength. Every recommendation comes with a line-by-line breakdown showing exactly which features contributed points and by how much, which makes it easy to understand and debug.

---

## 6. Limitations and Bias

**Features not considered:** The system ignores tempo entirely in its scoring, even though the dataset has tempo values. It also ignores danceability despite storing it. Lyrics, language, artist identity, and production era are not captured at all.

**Catalog bias:** The 18-song dataset skews toward Western, English-language genres. Latin, African, Asian, and electronic sub-genres are absent or barely represented. A user whose taste sits outside the represented genres will receive recommendations driven entirely by numeric similarity, with no categorical bonus available to them — giving them structurally lower scores than users whose genre is in the catalog.

**Mood label subjectivity:** Labels like "chill" and "relaxed" or "focused" and "peaceful" overlap significantly in meaning but are treated as completely different by the system. A user who enters "relaxed" gets no mood bonus for a song labeled "chill," even if those songs are nearly identical in feel.

**Exact-match brittleness:** Categorical matching is binary — "indie pop" and "pop" are treated as completely unrelated. A more forgiving system would give partial credit for similar genres.

**No diversity enforcement:** The top results can cluster around a single genre or artist. In the lofi/focused test, three of the top five results were lofi tracks. A real system would spread recommendations across more variety.

---

## 7. Evaluation

Three user profiles were tested against the full 18-song catalog:

**Profile 1 — pop / happy / energy 0.80**
Expected Sunrise City at #1. Result: Sunrise City scored 0.99 and ranked first. Rooftop Lights (indie pop, happy) ranked second at 0.73 — surprising at first, but correct because the mood bonus outweighed the genre miss. Gym Hero ranked third despite a genre match because its mood ("intense") did not match and its energy (0.93) was further from the target than Rooftop Lights.

**Profile 2 — lofi / focused / energy 0.40**
Expected Focus Flow at #1. Result: Focus Flow scored exactly 1.00 — a perfect match on all five features. The next two results were also lofi tracks (Midnight Coding, Library Rain), which revealed the clustering limitation described above.

**Profile 3 — metal / aggressive / energy 0.97**
Only Iron Collapse matched both genre and mood. It ranked first clearly. What was interesting: the #2 result was Storm Runner (rock, intense) — not a categorical match, but its high energy (0.91) brought it close numerically. This confirmed that numeric features do meaningful work when no categorical match is available.

A suite of 19 automated tests was written covering return types, score ranges, sort order, empty inputs, and CSV loading — all passing.

---

## 8. Future Work

- **Partial genre matching:** Treat "indie pop" as a close relative of "pop" rather than a completely different category, using a similarity table or genre hierarchy.
- **Diversity enforcement:** After scoring, apply a penalty if two consecutive results share the same artist or genre, so the top 5 spans more of the catalog.
- **Tempo as a preference:** Add `target_tempo` to the user profile. Tempo is particularly useful for activity-based listening (running, studying, sleeping).
- **Multiple mood support:** Allow the user to specify more than one acceptable mood (e.g., "focused or chill"), so near-miss moods are not completely penalised.
- **Implicit profile learning:** Track which recommended songs the user accepts or skips and adjust weights automatically over time.
- **Larger, real-world dataset:** Replace the hand-crafted 18-song catalog with a real dataset (e.g., from the Spotify API) to test whether the scoring logic holds up at scale.

---

## 9. Personal Reflection

Building this system made it clear that the hardest part of a recommender is not the ranking logic — sorting a list by score is trivial — it is deciding what to measure and how much each measurement should matter. The choice to weight mood above genre, for example, is a design value judgment, not a mathematical fact. Someone else could make the opposite choice and produce a system that feels equally reasonable.

The most unexpected discovery was how much explanatory power just two features — energy and mood — provide. Before building this, I assumed you would need many features to capture something as personal as musical taste. But in testing, the energy distance alone was often enough to separate good recommendations from bad ones. That made me think about how Spotify's "Discover Weekly" probably does something similar at a much larger scale, and how the feeling that it "knows you" is really just a weighted distance calculation run against millions of songs instead of eighteen.

It also changed how I think about fairness in recommendation systems. A user whose favourite genre is not in the catalog is quietly penalised — not because the system is malicious, but because the data does not represent them. That invisible gap between what the data covers and who the users actually are is one of the most important problems in real AI systems, and this small simulation made that concrete in a way that is easy to see and reason about.
