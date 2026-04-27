import csv
import json
import re
import streamlit as st
from pathlib import Path

try:
    from src.recommender import load_songs, recommend_songs
    from src.agent import RecommendationAgent
    from src.explainer import generate_explanation
except ImportError:
    from recommender import load_songs, recommend_songs
    from agent import RecommendationAgent
    from explainer import generate_explanation

DATA_PATH     = Path(__file__).parent.parent / "data" / "songs.csv"
PROFILES_PATH = Path(__file__).parent.parent / "data" / "profiles.json"

# ── constants ─────────────────────────────────────────────────────────────────

CATALOG_GENRES = [
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave",
    "indie pop", "hip-hop", "r&b", "classical", "metal",
    "country", "edm", "blues", "folk",
]
CATALOG_MOODS = [
    "happy", "chill", "intense", "relaxed", "focused",
    "moody", "sad", "romantic", "peaceful", "aggressive",
    "nostalgic", "euphoric", "melancholic", "dreamy",
]
DANCE_STYLES = ["none", "hip-hop", "salsa", "ballet", "ballroom", "tap", "contemporary"]

MOOD_EMOJI = {
    "happy": "😊", "chill": "😌", "intense": "⚡", "relaxed": "🌿",
    "focused": "🎯", "moody": "🌙", "sad": "💙", "romantic": "❤️",
    "peaceful": "☁️", "aggressive": "🔥", "nostalgic": "🌅",
    "euphoric": "✨", "melancholic": "🌧️", "dreamy": "🌌",
}

# matches updated recommender.py weights
WEIGHTS = {
    "genre": 0.25, "mood": 0.30, "energy": 0.18,
    "danceability": 0.15, "valence": 0.05, "acousticness": 0.02,
}
LABELS = {
    "genre": "Genre", "mood": "Mood", "energy": "Energy",
    "danceability": "Danceability", "valence": "Positivity", "acousticness": "Acousticness",
}

# ── CSS themes ────────────────────────────────────────────────────────────────

DARK_VARS = """
    --bg:#090914; --surface:#0f0f1e; --card:#14142a; --card-h:#1b1b32;
    --border:rgba(255,255,255,0.07); --border-a:rgba(124,58,237,0.5);
    --t1:#f0f0ff; --t2:#8b8fa8; --t3:#4b5068;
    --sidebar:rgba(255,255,255,0.025); --sdborder:rgba(255,255,255,0.06);
    --input-bg:rgba(255,255,255,0.05); --input-bdr:rgba(255,255,255,0.1);
    --bar-empty:rgba(255,255,255,0.07);
    --score-hi:#10b981; --score-mid:#f59e0b; --score-lo:#ef4444;
    --badge-g-bg:rgba(6,182,212,0.1); --badge-g-fg:#22d3ee; --badge-g-bdr:rgba(6,182,212,0.25);
    --badge-m-bg:rgba(124,58,237,0.12); --badge-m-fg:#a78bfa; --badge-m-bdr:rgba(124,58,237,0.25);
    --active-bg:rgba(124,58,237,0.1); --active-bdr:rgba(124,58,237,0.4); --active-fg:#a78bfa;
    --toggle-bg:rgba(255,255,255,0.07); --toggle-fg:#f0f0ff;
"""
LIGHT_VARS = """
    --bg:#f0f0fa; --surface:#e6e6f4; --card:#ffffff; --card-h:#f7f7ff;
    --border:rgba(0,0,0,0.08); --border-a:rgba(124,58,237,0.45);
    --t1:#0f0f20; --t2:#6b7280; --t3:#9ca3af;
    --sidebar:rgba(0,0,0,0.03); --sdborder:rgba(0,0,0,0.07);
    --input-bg:rgba(0,0,0,0.04); --input-bdr:rgba(0,0,0,0.12);
    --bar-empty:rgba(0,0,0,0.07);
    --score-hi:#059669; --score-mid:#d97706; --score-lo:#dc2626;
    --badge-g-bg:rgba(6,182,212,0.08); --badge-g-fg:#0891b2; --badge-g-bdr:rgba(6,182,212,0.2);
    --badge-m-bg:rgba(124,58,237,0.08); --badge-m-fg:#7c3aed; --badge-m-bdr:rgba(124,58,237,0.2);
    --active-bg:rgba(124,58,237,0.08); --active-bdr:rgba(124,58,237,0.3); --active-fg:#7c3aed;
    --toggle-bg:rgba(0,0,0,0.06); --toggle-fg:#0f0f20;
"""

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*  { font-family:'Inter',sans-serif !important; }
html { %%VARS%% }

.stApp {
    background: linear-gradient(135deg, var(--bg) 0%, var(--surface) 100%) !important;
    min-height: 100vh;
}
#MainMenu, footer, header { visibility:hidden; }
.block-container { padding-top:1.2rem !important; max-width:1060px !important; }

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background:var(--sidebar) !important;
    border-right:1px solid var(--sdborder) !important;
}
[data-testid="stSidebar"] * { color:var(--t2) !important; }
[data-testid="stSidebar"] h4 {
    font-size:.6rem !important; font-weight:700 !important;
    letter-spacing:.14em !important; text-transform:uppercase !important;
    color:var(--t3) !important; margin-bottom:.3rem !important;
}

/* ── animated title ── */
@keyframes grad {
    0%,100% { background-position:0% 50%; }
    50%      { background-position:100% 50%; }
}
.vm-title {
    font-size:2.65rem; font-weight:800; line-height:1.1;
    background:linear-gradient(270deg,#7c3aed,#06b6d4,#10b981,#f59e0b,#7c3aed);
    background-size:400% 400%;
    animation:grad 5s ease infinite;
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    color:transparent !important;
    margin-bottom:.1rem;
}
.vm-sub { color:var(--t2) !important; font-size:.87rem; margin-bottom:1.4rem; }

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background:transparent !important;
    border-bottom:1px solid var(--border) !important;
    gap:0 !important;
}
.stTabs [data-baseweb="tab"] {
    background:transparent !important; color:var(--t2) !important;
    font-size:.83rem !important; font-weight:500 !important;
    border:none !important; border-bottom:2px solid transparent !important;
    padding:.55rem 1.1rem !important;
    transition:color .2s, border-color .2s !important;
}
.stTabs [aria-selected="true"] {
    color:#7c3aed !important; border-bottom-color:#7c3aed !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top:1.1rem !important; }

/* ── song card ── */
.card {
    background:var(--card); border:1px solid var(--border);
    border-radius:18px; padding:1.1rem 1.4rem; margin-bottom:.75rem;
    transition:border-color .2s, transform .2s, box-shadow .2s;
}
.card:hover {
    border-color:var(--border-a); transform:translateY(-2px);
    box-shadow:0 10px 30px rgba(0,0,0,0.2);
}
.rank   { font-size:.6rem; font-weight:700; color:var(--t3); letter-spacing:.13em; text-transform:uppercase; margin-bottom:.18rem; }
.ctitle { font-size:1.08rem; font-weight:700; color:var(--t1); margin-bottom:.04rem; }
.cart   { font-size:.81rem; color:var(--t2); margin-bottom:.5rem; }

/* ── profile card ── */
.pcard {
    background:var(--card); border:1px solid var(--border);
    border-radius:16px; padding:1rem 1.2rem .75rem; margin-bottom:.6rem;
    transition:border-color .2s, box-shadow .2s;
}
.pcard:hover { border-color:var(--border-a); box-shadow:0 6px 20px rgba(0,0,0,0.15); }
.pname { font-size:.95rem; font-weight:700; color:var(--t1); margin-bottom:.3rem; }
.pinfo { font-size:.71rem; color:var(--t2); margin-top:.35rem; }

/* ── badges ── */
.badge { display:inline-block; padding:3px 11px; border-radius:999px; font-size:.67rem; font-weight:600; margin-right:.3rem; margin-bottom:.35rem; }
.bg    { background:var(--badge-g-bg); color:var(--badge-g-fg); border:1px solid var(--badge-g-bdr); }
.bm    { background:var(--badge-m-bg); color:var(--badge-m-fg); border:1px solid var(--badge-m-bdr); }

/* ── score rows ── */
.srow { display:flex; align-items:center; gap:.5rem; margin-bottom:.33rem; }
.slbl { font-size:.67rem; color:var(--t2); width:80px; flex-shrink:0; }
.sbb  { flex:1; height:4px; background:var(--bar-empty); border-radius:2px; overflow:hidden; }
.sbf  { height:100%; border-radius:2px; }
.sv   { font-size:.66rem; color:var(--t3); min-width:30px; text-align:right; flex-shrink:0; white-space:nowrap; }

/* ── active profile pill (sidebar) ── */
.apill {
    display:inline-flex; align-items:center; gap:.4rem;
    background:var(--active-bg); border:1px solid var(--active-bdr);
    border-radius:999px; padding:.28rem .85rem;
    font-size:.72rem; font-weight:600; color:var(--active-fg);
    margin-bottom:.6rem;
}

/* ── toggle button ── */
.toggle-btn {
    display:inline-flex; align-items:center; gap:.4rem;
    background:var(--toggle-bg); border:1px solid var(--border);
    border-radius:999px; padding:.3rem .9rem;
    font-size:.78rem; font-weight:600; color:var(--toggle-fg);
    cursor:pointer; transition:background .2s;
    margin-bottom:.5rem;
}

/* ── section heading ── */
.sh { font-size:.88rem; font-weight:700; color:var(--t1); margin-bottom:.8rem; }

/* ── empty state ── */
.empty-state { color:var(--t3); font-size:.84rem; padding:.8rem 0; }

/* ── beginner tip ── */
.btip {
    background:rgba(124,58,237,0.07); border:1px solid rgba(124,58,237,0.18);
    border-radius:10px; padding:.45rem .75rem; margin-bottom:.55rem;
    font-size:.8rem; color:var(--t1); line-height:1.45;
}

/* ── agent step ── */
.astep {
    border-left:2px solid rgba(124,58,237,0.4); padding:.4rem .75rem;
    margin-bottom:.55rem; font-size:.8rem; color:var(--t2); line-height:1.5;
}
.astep-num { font-size:.6rem; font-weight:700; color:var(--t3);
    letter-spacing:.12em; text-transform:uppercase; margin-bottom:.1rem; }
.astep-name { font-size:.82rem; font-weight:700; color:var(--t1); margin-bottom:.15rem; }

/* ── expander ── */
[data-testid="stExpander"] {
    background:var(--card) !important; border:1px solid var(--border) !important;
    border-radius:14px !important; overflow:hidden; margin-bottom:.75rem;
}
[data-testid="stExpander"] summary {
    color:var(--t1) !important; font-weight:600 !important;
    font-size:.85rem !important; padding:.7rem 1rem !important;
    background:transparent !important;
}
[data-testid="stExpander"] summary:hover { background:var(--card-h) !important; }
[data-testid="stExpander"] summary svg { color:var(--t2) !important; }
[data-testid="stExpanderDetails"] { padding:.25rem 1rem .75rem !important; }

/* ── slider accent ── */
[data-testid="stSlider"] [role="progressbar"] > div {
    background:linear-gradient(90deg,#7c3aed,#06b6d4) !important;
}
[data-testid="stSlider"] [role="slider"] {
    background:#7c3aed !important; border-color:#7c3aed !important;
    box-shadow:0 0 0 4px rgba(124,58,237,.2) !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"] { color:var(--t3) !important; }

/* ── selectbox dropdown ── */
[data-baseweb="popover"] > div {
    background:var(--card) !important; border:1px solid var(--border) !important;
    border-radius:12px !important; box-shadow:0 8px 32px rgba(0,0,0,.35) !important;
}
[data-baseweb="option"] { background:var(--card) !important; color:var(--t1) !important; }
[data-baseweb="option"]:hover,
[data-baseweb="option"][aria-selected="true"] { background:var(--card-h) !important; }

/* ── inputs ── */
.stTextInput > div > div > input,
.stNumberInput input {
    background:var(--input-bg) !important; border:1px solid var(--input-bdr) !important;
    border-radius:10px !important; color:var(--t1) !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput input:focus {
    border-color:rgba(124,58,237,.5) !important;
    box-shadow:0 0 0 2px rgba(124,58,237,.12) !important;
}
label, p, .stMarkdown p { color:var(--t2) !important; }
[data-testid="stCaptionContainer"] p { color:var(--t3) !important; }
.stSelectbox > div { color:var(--t1) !important; }

/* ── buttons ── */
.stButton > button {
    border-radius:10px !important; font-weight:600 !important;
    font-size:.83rem !important; border:1px solid var(--border) !important;
    background:var(--card) !important; color:var(--t1) !important;
    transition:opacity .2s, transform .1s !important;
}
.stButton > button:hover { border-color:var(--border-a) !important; opacity:.9 !important; }
.stButton > button:active { transform:scale(.97) !important; }

.stFormSubmitButton > button {
    background:linear-gradient(135deg,#7c3aed,#5b21b6) !important;
    border:none !important; color:#fff !important; width:100% !important;
    border-radius:10px !important; font-weight:600 !important;
    font-size:.85rem !important; padding:.55rem !important;
}
.stFormSubmitButton > button:hover { opacity:.85 !important; }

hr { border-color:var(--border) !important; margin:.75rem 0 !important; }
.stAlert { border-radius:12px !important; }
"""

# ── data helpers ──────────────────────────────────────────────────────────────

def ensure_dance_style_column() -> None:
    """Adds dance_style column to CSV if missing (one-time migration)."""
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if "dance_style" in fieldnames:
            return
        rows = list(reader)
    fieldnames.append("dance_style")
    for row in rows:
        row["dance_style"] = "none"
    with open(DATA_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def append_song(song_dict: dict) -> None:
    ensure_dance_style_column()
    existing = load_songs(str(DATA_PATH))
    song_dict["id"] = max((s["id"] for s in existing), default=0) + 1
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        fieldnames = list(csv.DictReader(f).fieldnames or [])
    with open(DATA_PATH, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore").writerow(song_dict)

def load_profiles() -> list:
    if not PROFILES_PATH.exists():
        PROFILES_PATH.write_text('{"profiles":[]}')
    return json.loads(PROFILES_PATH.read_text()).get("profiles", [])

def save_profiles(profiles: list) -> None:
    PROFILES_PATH.write_text(json.dumps({"profiles": profiles}, indent=2))

def delete_profile(name: str) -> None:
    save_profiles([p for p in load_profiles() if p["name"] != name])

def apply_profile(p: dict) -> None:
    st.session_state["pref_genre"]        = p.get("genre", "pop")
    st.session_state["pref_mood"]         = p.get("mood", "happy")
    st.session_state["pref_energy"]       = float(p.get("energy", 0.7))
    st.session_state["pref_valence"]      = float(p.get("valence", 0.65))
    st.session_state["pref_danceability"] = float(p.get("danceability", 0.6))
    st.session_state["pref_acousticness"] = float(p.get("acousticness", 0.2))
    st.session_state["active_profile"]    = p["name"]

# ── misc helpers ──────────────────────────────────────────────────────────────

def extract_reason_values(explanation: str) -> dict:
    vals = {}
    for part in explanation.split(" | "):
        m = re.search(r"\(\+([0-9.]+)\)", part)
        if m:
            for key in WEIGHTS:
                if key in part:
                    vals[key] = float(m.group(1))
    return vals

def prefs_from_state() -> dict:
    return {
        "genre":               st.session_state["pref_genre"],
        "mood":                st.session_state["pref_mood"],
        "target_energy":       st.session_state["pref_energy"],
        "target_valence":      st.session_state["pref_valence"],
        "target_danceability": st.session_state["pref_danceability"],
        "target_acousticness": st.session_state["pref_acousticness"],
        "likes_acoustic":      st.session_state["pref_acousticness"] > 0.5,
    }

def score_color(s: float) -> str:
    return "var(--score-hi)" if s >= 0.75 else "var(--score-mid)" if s >= 0.45 else "var(--score-lo)"

def _md_bold(text: str) -> str:
    """Convert **bold** markdown to <strong> so it renders inside raw HTML divs."""
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="VibeMatch", page_icon="🎵", layout="wide")

# ── session state ─────────────────────────────────────────────────────────────

DEFAULTS = {
    "dark_mode":         True,
    "beginner_mode":     True,
    "pref_genre":        "pop",
    "pref_mood":         "happy",
    "pref_energy":       0.70,
    "pref_valence":      0.65,
    "pref_danceability": 0.60,
    "pref_acousticness": 0.20,
    "active_profile":    None,
    "k_count":           5,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS injection ─────────────────────────────────────────────────────────────

theme_vars = DARK_VARS if st.session_state["dark_mode"] else LIGHT_VARS
st.markdown(
    f"<style>{BASE_CSS.replace('%%VARS%%', theme_vars)}</style>",
    unsafe_allow_html=True,
)

# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # theme toggle
    icon = "☀️" if st.session_state["dark_mode"] else "🌙"
    label = f"{icon}  {'Light' if st.session_state['dark_mode'] else 'Dark'} Mode"
    if st.button(label, use_container_width=True):
        st.session_state["dark_mode"] = not st.session_state["dark_mode"]
        st.rerun()

    # beginner mode toggle
    bm_icon  = "🎓" if st.session_state["beginner_mode"] else "🔬"
    bm_label = f"{bm_icon}  {'Beginner Mode ON' if st.session_state['beginner_mode'] else 'Expert Mode ON'}"
    if st.button(bm_label, use_container_width=True):
        st.session_state["beginner_mode"] = not st.session_state["beginner_mode"]
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("#### Your Taste")

    st.selectbox(
        "Genre", CATALOG_GENRES, key="pref_genre",
        help="The style of music you enjoy most — pop, rock, jazz, lofi…",
    )
    st.selectbox(
        "Mood", CATALOG_MOODS, key="pref_mood",
        help="How you want the music to make you feel right now.",
    )
    st.slider(
        "Energy", 0.0, 1.0, step=0.01, key="pref_energy",
        help="0 = very calm and quiet · 1 = super intense and loud",
    )
    st.slider(
        "Positivity", 0.0, 1.0, step=0.01, key="pref_valence",
        help="0 = melancholic/sad tone · 1 = bright/uplifting tone",
    )
    st.slider(
        "Danceability", 0.0, 1.0, step=0.01, key="pref_danceability",
        help="How much do you want to move? 0 = sit still · 1 = dance floor",
    )
    st.slider(
        "Acousticness", 0.0, 1.0, step=0.01, key="pref_acousticness",
        help="0 = electronic/produced sound · 1 = raw acoustic instruments",
    )
    st.slider(
        "Results", 1, 10, key="k_count",
        help="How many song recommendations to show at once.",
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    if st.session_state["active_profile"]:
        st.markdown(
            f'<div class="apill">▶&nbsp; {st.session_state["active_profile"]}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Clear Profile", use_container_width=True):
            for k, v in DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()
    else:
        st.markdown(
            '<p style="font-size:.75rem;color:var(--t3);">No profile loaded — '
            'go to Profiles tab to load one.</p>',
            unsafe_allow_html=True,
        )

# ── main header ───────────────────────────────────────────────────────────────

songs = load_songs(DATA_PATH)

st.markdown('<p class="vm-title">VibeMatch</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="vm-sub">AI-powered music recommendations &nbsp;·&nbsp; '
    'tune your taste, discover your vibe</p>',
    unsafe_allow_html=True,
)

with st.expander("💡 New here? Learn how VibeMatch works"):
    st.markdown("""
**VibeMatch uses AI to match songs to your personal taste in 4 steps:**

1. **Set your taste** — use the sliders on the left to describe your mood, energy, and style.
   *Hover over any slider to see what it means.*

2. **AI scores every song** — each song in our catalog gets a match score from 0.00 to 1.00
   based on genre, mood, energy, danceability, positivity, and acousticness.

3. **Diversity filter** — so you don't get 5 songs from the same artist, the AI spreads results
   across different artists.

4. **Top picks appear** — green score = great match · yellow = decent · red = stretch pick.

**Tips for beginners:**
- Start with Genre and Mood — those have the biggest impact on your results.
- Toggle **Beginner Mode** (sidebar) to see plain-English explanations on every card.
- Save your settings as a **Profile** (Profiles tab) so you can reload them anytime.
- Anyone can **Add a Song** (Add a Song tab) — it appears instantly for all users.
""")

# ── tabs ──────────────────────────────────────────────────────────────────────

tab_discover, tab_add, tab_profiles = st.tabs(
    ["🎵  Discover", "➕  Add a Song", "👤  Profiles"]
)

# ════════════════════════════ TAB 1 · DISCOVER ════════════════════════════════

with tab_discover:
    prefs   = prefs_from_state()
    agent   = RecommendationAgent(songs)
    results, agent_steps = agent.run(prefs, k=st.session_state["k_count"])

    genre = st.session_state["pref_genre"]
    mood  = st.session_state["pref_mood"]

    st.markdown(
        f'<p class="sh">Top {len(results)} picks &nbsp;·&nbsp; {genre} / {mood}</p>',
        unsafe_allow_html=True,
    )

    # ── AI reasoning steps (always available, expanded in beginner mode) ───────
    with st.expander(
        "🤖 How the AI decided",
        expanded=st.session_state.get("beginner_mode", True),
    ):
        for step in agent_steps:
            st.markdown(
                f'<div class="astep">'
                f'<div class="astep-num">Step {step.step_num}</div>'
                f'<div class="astep-name">{step.name}</div>'
                f'{step.summary}'
                f'</div>',
                unsafe_allow_html=True,
            )
        if st.session_state.get("beginner_mode", True):
            st.caption("Switch to Expert Mode (sidebar) to hide this panel.")

    for rank, (song, score, explanation) in enumerate(results, 1):
        sc   = score_color(score)
        icon = MOOD_EMOJI.get(song["mood"], "🎵")
        rv   = extract_reason_values(explanation)

        # beginner-friendly one-liner
        btip_html = ""
        if st.session_state.get("beginner_mode", True):
            exp_mode = "beginner"
            btext = generate_explanation(song, score, prefs, mode=exp_mode)
            btip_html = f'<div class="btip">{_md_bold(btext)}</div>'

        score_label = (
            f"{score*100:.0f}% match"
            if st.session_state.get("beginner_mode", True)
            else f"{score:.2f}"
        )

        rows_html = f"""
<div class="srow">
  <span class="slbl" style="font-weight:700;color:var(--t1);">Overall</span>
  <div class="sbb"><div class="sbf" style="width:{score*100:.0f}%;background:{sc};"></div></div>
  <span class="sv" style="color:{sc};font-weight:700;min-width:64px;">{score_label}</span>
</div>"""
        for key, lbl in LABELS.items():
            val = rv.get(key, 0.0)
            pct = (val / WEIGHTS[key] * 100) if WEIGHTS[key] else 0
            rows_html += f"""
<div class="srow">
  <span class="slbl">{lbl}</span>
  <div class="sbb"><div class="sbf" style="width:{pct:.0f}%;background:rgba(124,58,237,0.45);"></div></div>
  <span class="sv">{val:.2f}</span>
</div>"""

        st.markdown(f"""
<div class="card">
  <div class="rank">#{rank}</div>
  <div class="ctitle">{song['title']}</div>
  <div class="cart">{song['artist']}</div>
  <span class="badge bg">{song['genre']}</span>
  <span class="badge bm">{icon}&nbsp;{song['mood']}</span>
  {btip_html}
  <div style="margin-top:.6rem">{rows_html}</div>
</div>""", unsafe_allow_html=True)

# ════════════════════════════ TAB 2 · ADD A SONG ══════════════════════════════

with tab_add:
    st.markdown('<p class="sh">Add a Song to the Catalog</p>', unsafe_allow_html=True)
    st.caption("Songs you add are available to all users immediately.")

    with st.form("add_song_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            s_title       = st.text_input("Title *")
            s_artist      = st.text_input("Artist *")
            s_genre       = st.selectbox("Genre *",      CATALOG_GENRES)
            s_mood        = st.selectbox("Mood *",       CATALOG_MOODS)
            s_dance_style = st.selectbox("Dance Style",  DANCE_STYLES)
        with c2:
            s_tempo       = st.number_input("Tempo (BPM)", min_value=40, max_value=220, value=120, step=1)
            s_energy      = st.slider("Energy",       0.0, 1.0, 0.70, 0.01, key="fs_e")
            s_valence     = st.slider("Positivity",   0.0, 1.0, 0.65, 0.01, key="fs_v")
            s_dance       = st.slider("Danceability", 0.0, 1.0, 0.60, 0.01, key="fs_d")
            s_acoustic    = st.slider("Acousticness", 0.0, 1.0, 0.20, 0.01, key="fs_a")

        submitted = st.form_submit_button("➕  Add Song", use_container_width=True)

    if submitted:
        if not s_title.strip() or not s_artist.strip():
            st.error("Title and Artist are required.")
        else:
            append_song({
                "title":        s_title.strip(),
                "artist":       s_artist.strip(),
                "genre":        s_genre,
                "mood":         s_mood,
                "energy":       s_energy,
                "tempo_bpm":    s_tempo,
                "valence":      s_valence,
                "danceability": s_dance,
                "acousticness": s_acoustic,
                "dance_style":  s_dance_style,
            })
            st.success(f"✓ **{s_title}** by {s_artist} added to the catalog! Switch to Discover to see it.")

# ════════════════════════════ TAB 3 · PROFILES ════════════════════════════════

with tab_profiles:
    profiles = load_profiles()
    col_list, col_new = st.columns([3, 2], gap="large")

    # ── saved profiles ────────────────────────────────────────────────────────

    with col_list:
        st.markdown('<p class="sh">Saved Profiles</p>', unsafe_allow_html=True)

        if not profiles:
            st.markdown(
                '<p class="empty-state">No profiles yet — create one on the right.</p>',
                unsafe_allow_html=True,
            )
        else:
            for p in profiles:
                is_active   = st.session_state["active_profile"] == p["name"]
                icon        = MOOD_EMOJI.get(p.get("mood", ""), "🎵")
                active_mark = (
                    "&nbsp;<span style='font-size:.62rem;color:var(--active-fg);"
                    "font-weight:700;'>● ACTIVE</span>"
                    if is_active else ""
                )
                border_override = "border-color:var(--border-a);" if is_active else ""

                st.markdown(f"""
<div class="pcard" style="{border_override}">
  <div class="pname">{p['name']}{active_mark}</div>
  <span class="badge bg">{p.get('genre','—')}</span>
  <span class="badge bm">{icon}&nbsp;{p.get('mood','—')}</span>
  <div class="pinfo">
    Energy {p.get('energy',0):.2f} &nbsp;·&nbsp;
    Danceability {p.get('danceability',0):.2f} &nbsp;·&nbsp;
    Acousticness {p.get('acousticness',0):.2f}
  </div>
</div>""", unsafe_allow_html=True)

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Load", key=f"load_{p['name']}", use_container_width=True):
                        apply_profile(p)
                        st.rerun()
                with b2:
                    if st.button("Delete", key=f"del_{p['name']}", use_container_width=True):
                        delete_profile(p["name"])
                        if st.session_state["active_profile"] == p["name"]:
                            st.session_state["active_profile"] = None
                        st.rerun()

    # ── create new profile ────────────────────────────────────────────────────

    with col_new:
        st.markdown('<p class="sh">Create New Profile</p>', unsafe_allow_html=True)

        with st.form("new_profile_form", clear_on_submit=True):
            np_name    = st.text_input("Profile Name *")
            np_genre   = st.selectbox("Genre",       CATALOG_GENRES, key="np_g")
            np_mood    = st.selectbox("Mood",        CATALOG_MOODS,  key="np_m")
            np_energy  = st.slider("Energy",         0.0, 1.0, 0.70, 0.01, key="np_e")
            np_val     = st.slider("Positivity",     0.0, 1.0, 0.65, 0.01, key="np_v")
            np_dance   = st.slider("Danceability",   0.0, 1.0, 0.60, 0.01, key="np_d")
            np_ac      = st.slider("Acousticness",   0.0, 1.0, 0.20, 0.01, key="np_a")
            save_click = st.form_submit_button("💾  Save Profile", use_container_width=True)

        if save_click:
            name = np_name.strip()
            if not name:
                st.error("Profile name is required.")
            elif any(p["name"] == name for p in profiles):
                st.error(f'A profile named "{name}" already exists.')
            else:
                new_p = {
                    "name":         name,
                    "genre":        np_genre,
                    "mood":         np_mood,
                    "energy":       np_energy,
                    "valence":      np_val,
                    "danceability": np_dance,
                    "acousticness": np_ac,
                }
                profiles.append(new_p)
                save_profiles(profiles)
                apply_profile(new_p)
                st.success(f'✓ Profile "{name}" saved and loaded!')
                st.rerun()
