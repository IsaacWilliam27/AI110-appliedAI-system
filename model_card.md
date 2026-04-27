# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**

---

## 2. Short Reflection

### Limitations and Biases
- The system relies on user behavior data (likes, skips, replay time), so it can overfit to recent habits and create a “filter bubble.”
- If training or seed data overrepresents popular genres/artists, recommendations may under-serve niche styles and emerging artists.
- Cold-start users or songs with little interaction data may receive less accurate recommendations.

### Misuse Risks and Prevention
- **Possible misuse:** artificially boosting tracks (bot-like interactions) to manipulate recommendations.
- **Prevention steps:** rate-limiting, anomaly detection on interaction patterns, account trust scoring, and periodic audits of recommendation outcomes.
- **Privacy risk:** inferring sensitive preferences from listening patterns.
- **Prevention steps:** data minimization, clear consent, and aggregation/anonymization for analytics.

### Reliability Testing Surprise
- I expected stable recommendations from small preference changes, but minor shifts in recent listening history sometimes caused large ranking changes.
- This highlighted the need for smoothing, diversity constraints, and stronger evaluation on consistency over time.

### Collaboration with AI
- AI helped speed up development by suggesting a clearer feature engineering structure (separating short-term vs. long-term preference signals), which improved readability and testing.
- A flawed AI suggestion was to rely too heavily on raw popularity as a fallback, which initially reduced personalization and marginalized niche music; this was corrected by adding diversity and user-similarity weighting.
