import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import os
import re
import json
import random
import hmac
import hashlib
import secrets
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ============================================================
# PAGE SETTINGS
# ============================================================
st.set_page_config(
    page_title="Emotion Journal & Psychologist Portal",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; color: #1E293B; }
    .stApp { background-color: #F8FAF9 !important; transition: background-color .6s ease; }

    [data-testid="stSidebar"] { background-color: #EBF2EC !important; border-right: 1px solid #D1E0D3 !important; }
    [data-testid="stSidebar"] * { color: #1E293B !important; font-weight: 600 !important; }

    /* hide Streamlit's automatic multipage menu (this app uses its own sidebar radio) */
    [data-testid="stSidebarNav"] { display: none !important; }

    h1, h2, h3, h4 { font-family: 'DM Serif Display', serif !important; color: #0F172A !important; font-weight: 400 !important; }
    h1 { font-size: 2.3rem !important; }

    [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 18px !important; background: rgba(255,255,255,.92); }

    .metric-card { background:#FFF; border-radius:14px; padding:20px; text-align:center;
                   border:1px solid #E2E8F0; box-shadow:0 2px 10px rgba(0,0,0,.03); }

    .stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"] button {
        background-color:#2D5A39 !important; color:#FFF !important; border-radius:30px !important;
        padding:10px 28px !important; font-weight:700 !important; border:none !important;
        box-shadow:0 4px 12px rgba(45,90,57,.2) !important; transition:all .2s ease !important; }
    .stButton>button:hover, .stDownloadButton>button:hover,
    [data-testid="stFormSubmitButton"] button:hover { background-color:#23472D !important; transform:translateY(-1px); }

    /* keep button text white, even inside the sidebar */
    [data-testid="stSidebar"] .stButton>button,
    [data-testid="stSidebar"] .stButton>button *,
    .stButton>button *, .stDownloadButton>button *,
    [data-testid="stFormSubmitButton"] button * { color:#FFFFFF !important; }

    .stTextArea textarea { border-radius:14px !important; border:1px solid #CBD5E1 !important;
        background-color:#FFF !important; color:#0F172A !important; font-size:1rem !important; padding:16px !important; }

    .stInfo { background-color:#E9F5EC !important; border-left:4px solid #2D5A39 !important; border-radius:12px !important; }

    /* hide the zero-height iframe that runs the live-background script */
    .stElementContainer:has(iframe[height="0"]) { display:none; }
</style>
""", unsafe_allow_html=True)

if os.path.isdir("pages"):
    st.sidebar.error("⚠️ An old 'pages' folder was found next to this file. It adds the extra menu items "
                     "(Journal, Mood Analytics, ...) that show 'Please sign in'. Rename it to 'pages_old' "
                     "and restart the app.")

# ============================================================
# CONSTANTS
# ============================================================
EMOTIONS = ["Joyful", "Calm", "Anxious", "Sad", "Angry"]

BG_COLORS = {
    "Joyful": "#FFF1B8", "Calm": "#DDF3E0", "Anxious": "#DCDFF7",
    "Sad": "#D4E8FA", "Angry": "#FADADA", "default": "#F8FAF9",
}
CHART_COLORS = {
    "Joyful": "#F4B400", "Calm": "#43A047", "Anxious": "#7E57C2",
    "Sad": "#42A5F5", "Angry": "#E53935",
}
MOOD_SCORE = {"Angry": 1, "Sad": 2, "Anxious": 3, "Calm": 4, "Joyful": 5}

QUOTES = {
    "Joyful": ["Happiness grows when you notice the little things.", "Let yourself enjoy this moment.",
               "Keep this feeling close and let it brighten your day."],
    "Calm": ["There is strength in slowing down.", "Take a breath and enjoy the quiet moment.",
             "You don't have to rush everything."],
    "Anxious": ["Take one moment at a time. You don't have to solve everything now.",
                "Breathe slowly. You are allowed to pause.", "It is okay to take things one step at a time."],
    "Sad": ["It is okay to have difficult days.", "Be gentle with yourself today.",
            "You don't have to be okay all the time."],
    "Angry": ["Take a pause before reacting.", "Give yourself some space to breathe.",
              "Strong emotions pass. Give yourself time."],
}

MUSIC = {
    "Joyful": "https://www.youtube.com/results?search_query=happy+uplifting+music",
    "Calm": "https://www.youtube.com/results?search_query=calm+relaxing+music",
    "Anxious": "https://www.youtube.com/results?search_query=calming+anxiety+music",
    "Sad": "https://www.youtube.com/results?search_query=comforting+music",
    "Angry": "https://www.youtube.com/results?search_query=relaxing+music",
}

CONSENT_OPTIONS = ["No Access", "Brief Summary Only", "Full Access"]

DB_NAME = "emotion_journal.db"
MEMORY_DIR = "memories"
os.makedirs(MEMORY_DIR, exist_ok=True)
TS_FMT = "%Y-%m-%d %H:%M:%S"
MAX_FAILED = 5
LOCK_MINUTES = 5

# ============================================================
# VERSION-SAFE DISPLAY HELPERS
# ============================================================
def show_image(img, **kw):
    try:
        st.image(img, width="stretch", **kw)
    except Exception:
        st.image(img, use_container_width=True, **kw)

def show_plot(fig):
    try:
        st.plotly_chart(fig, width="stretch")
    except Exception:
        st.plotly_chart(fig, use_container_width=True)

def show_df(df):
    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True)

# ============================================================
# DATABASE
# ============================================================
def now_s():
    return datetime.now().strftime(TS_FMT)

def db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_database():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL,
            salt TEXT NOT NULL,
            pw_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            failed_count INTEGER DEFAULT 0,
            locked_until TEXT
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mood_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal TEXT,
            emotion TEXT,
            date_time TEXT,
            consent_level TEXT DEFAULT 'No Access'
        )""")
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(mood_history)")]
    if "user_id" not in cols:                       # migrate older databases
        conn.execute("ALTER TABLE mood_history ADD COLUMN user_id INTEGER")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS access_grants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            psychologist_id INTEGER NOT NULL,
            granted_at TEXT NOT NULL,
            expires_at TEXT,
            revoked INTEGER DEFAULT 0
        )""")
    conn.execute("UPDATE users SET role='user' WHERE role='patient'")
    conn.commit()
    conn.close()

create_database()

# ============================================================
# ACCOUNTS: SIGN UP / SIGN IN
# ============================================================
USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")

def hash_pw(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return salt.hex(), h.hex()

def create_user(username, display_name, password, confirm, role):
    """Returns (user_dict | None, message)."""
    username = username.strip().lower()
    display_name = display_name.strip()
    if not display_name:
        return None, "Please enter your name."
    if not USERNAME_RE.match(username):
        return None, "Username must be 3-30 characters: lowercase letters, numbers or underscore."
    if len(password) < 8:
        return None, "Password must be at least 8 characters."
    if password != confirm:
        return None, "Passwords do not match."
    if role not in ("user", "psychologist"):
        return None, "Please choose an account type."
    salt, h = hash_pw(password)
    conn = db()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, display_name, role, salt, pw_hash, created_at) VALUES (?,?,?,?,?,?)",
            (username, display_name, role, salt, h, now_s()))
        conn.commit()
        uid = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return None, "That username is already taken. Please choose another."
    conn.close()
    return {"id": uid, "username": username, "name": display_name, "role": role}, "Account created."

def authenticate(username, password):
    """Returns (user_dict | None, message)."""
    username = username.strip().lower()
    generic = "Incorrect username or password."
    conn = db()
    u = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not u:
        hash_pw(password)                            # keep timing similar for unknown users
        conn.close()
        return None, generic
    if u["locked_until"] and u["locked_until"] > now_s():
        conn.close()
        return None, f"Too many failed attempts. Please try again after {u['locked_until'][11:16]}."
    _, h = hash_pw(password, bytes.fromhex(u["salt"]))
    if hmac.compare_digest(h, u["pw_hash"]):
        conn.execute("UPDATE users SET failed_count=0, locked_until=NULL WHERE id=?", (u["id"],))
        conn.commit()
        conn.close()
        return {"id": u["id"], "username": u["username"], "name": u["display_name"], "role": u["role"]}, ""
    failed = (u["failed_count"] or 0) + 1
    locked = None
    if failed >= MAX_FAILED:
        locked = (datetime.now() + timedelta(minutes=LOCK_MINUTES)).strftime(TS_FMT)
        failed = 0
    conn.execute("UPDATE users SET failed_count=?, locked_until=? WHERE id=?", (failed, locked, u["id"]))
    conn.commit()
    conn.close()
    if locked:
        return None, f"Too many failed attempts. Account locked for {LOCK_MINUTES} minutes."
    return None, generic

def get_user(uid):
    conn = db()
    u = conn.execute("SELECT id, username, display_name, role FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    if not u:
        return None
    return {"id": u["id"], "username": u["username"], "name": u["display_name"], "role": u["role"]}

def find_psychologist(username):
    conn = db()
    u = conn.execute("SELECT id, username, display_name FROM users WHERE username=? AND role='psychologist'",
                     (username.strip().lower().lstrip("@"),)).fetchone()
    conn.close()
    return u

# ============================================================
# JOURNAL DATA (always scoped to the signed-in user)
# ============================================================
def save_mood(user_id, journal_text, emotion, consent_level):
    conn = db()
    conn.execute(
        "INSERT INTO mood_history (user_id, journal, emotion, date_time, consent_level) VALUES (?,?,?,?,?)",
        (user_id, journal_text, emotion, now_s(), consent_level))
    conn.commit()
    conn.close()

def load_mood_history(user_id):
    conn = db()
    df = pd.read_sql_query(
        "SELECT id, journal, emotion, date_time, consent_level FROM mood_history "
        "WHERE user_id=? ORDER BY id DESC", conn, params=(int(user_id),))
    conn.close()
    if not df.empty:
        df["date_time"] = pd.to_datetime(df["date_time"])
    return df

def update_consent(user_id, entry_id, level):
    conn = db()
    conn.execute("UPDATE mood_history SET consent_level=? WHERE id=? AND user_id=?",
                 (level, int(entry_id), int(user_id)))
    conn.commit()
    conn.close()

def update_consent_all(user_id, level):
    conn = db()
    conn.execute("UPDATE mood_history SET consent_level=? WHERE user_id=?", (level, int(user_id)))
    conn.commit()
    conn.close()

def count_unclaimed():
    conn = db()
    n = conn.execute("SELECT COUNT(*) AS n FROM mood_history WHERE user_id IS NULL").fetchone()["n"]
    conn.close()
    return n

def claim_unclaimed(user_id):
    conn = db()
    conn.execute("UPDATE mood_history SET user_id=?, consent_level='No Access' WHERE user_id IS NULL",
                 (int(user_id),))
    conn.commit()
    conn.close()

# ============================================================
# PSYCHOLOGIST ACCESS GRANTS
# ============================================================
def grant_access(patient_id, psy_username, days):
    psy = find_psychologist(psy_username)
    if not psy:
        return False, "No psychologist account found with that username."
    expires = (datetime.now() + timedelta(days=days)).strftime(TS_FMT) if days else None
    conn = db()
    conn.execute("UPDATE access_grants SET revoked=1 WHERE patient_id=? AND psychologist_id=? AND revoked=0",
                 (patient_id, psy["id"]))
    conn.execute(
        "INSERT INTO access_grants (patient_id, psychologist_id, granted_at, expires_at) VALUES (?,?,?,?)",
        (patient_id, psy["id"], now_s(), expires))
    conn.commit()
    conn.close()
    return True, f"{psy['display_name']} (@{psy['username']}) can now view your shared entries."

def list_grants(patient_id):
    conn = db()
    rows = conn.execute("""
        SELECT g.id, g.granted_at, g.expires_at, g.revoked, u.display_name, u.username
        FROM access_grants g JOIN users u ON u.id = g.psychologist_id
        WHERE g.patient_id=? ORDER BY g.id DESC""", (patient_id,)).fetchall()
    conn.close()
    return rows

def revoke_grant(patient_id, grant_id):
    conn = db()
    conn.execute("UPDATE access_grants SET revoked=1 WHERE id=? AND patient_id=?", (int(grant_id), patient_id))
    conn.commit()
    conn.close()

def grant_active(row):
    return (not row["revoked"]) and (not row["expires_at"] or row["expires_at"] > now_s())

def patients_for(psy_id):
    conn = db()
    rows = conn.execute("""
        SELECT u.id, u.display_name, u.username, MAX(g.expires_at) AS expires_at
        FROM access_grants g JOIN users u ON u.id = g.patient_id
        WHERE g.psychologist_id=? AND g.revoked=0 AND (g.expires_at IS NULL OR g.expires_at > ?)
        GROUP BY u.id ORDER BY u.display_name""", (psy_id, now_s())).fetchall()
    conn.close()
    return rows

def has_active_grant(psy_id, patient_id):
    conn = db()
    row = conn.execute("""
        SELECT 1 FROM access_grants
        WHERE psychologist_id=? AND patient_id=? AND revoked=0 AND (expires_at IS NULL OR expires_at > ?)
        LIMIT 1""", (psy_id, patient_id, now_s())).fetchone()
    conn.close()
    return row is not None

# ============================================================
# EMOTION DETECTION  (weighted lexicon + phrases + AI model blend)
# ============================================================
MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"
LABEL_MAP = {"joy": "Joyful", "surprise": "Joyful", "neutral": "Calm",
             "fear": "Anxious", "sadness": "Sad", "anger": "Angry", "disgust": "Angry"}

LEX_RAW = {}
def _add(emo, words, w=1.0):
    for x in words.split():
        LEX_RAW.setdefault(x, {})[emo] = w

# Sad
_add("Sad", "sad* cry crying cried tears lonel* unhappy hopeless heartbroken depress* worthless grief", 1.3)
_add("Sad", "upset hurt* miss missing empty disappoint* guilt* regret* bad terrible awful horrible "
            "failed failure fail ignored rejected betray* weary", 1.0)
_add("Sad", "tired exhaust* drain* fatigue*", 0.9)
_add("Sad", "lost down alone sorry", 0.7)
_add("Sad", "argu* fight* fought", 0.6)
_add("Sad", "hectic", 0.2)
# Anxious
_add("Anxious", "anxi* panic* terrified nightmare*", 1.4)
_add("Anxious", "overwhelm*", 1.3)
_add("Anxious", "worr* stress* nervous* scared scary afraid fear* tense uneasy dread* restless deadline* "
                "pressure hectic chaotic swamped insomnia sleepless exam exams", 1.0)
_add("Anxious", "busy rushed rush confus* uncertain", 0.6)
_add("Anxious", "tired exhaust* drain*", 0.3)
# Angry
_add("Angry", "angr* furious rage hate* outrag*", 1.5)
_add("Angry", "annoy* irritat* frustrat* mad resent* unfair disgust* yell* shout* scream* rude insult* "
               "snapp* quarrel* clash*", 1.1)
_add("Angry", "argu* fight* fought blame*", 0.9)
_add("Angry", "upset betray*", 0.3)
# Joyful
_add("Joyful", "amazing wonderful joy* thrill* awesome fantastic celebrat* delight* excit* proud grateful "
               "cheerful blessed laugh* yay hooray", 1.3)
_add("Joyful", "happy happier happiness great love* fun passed glad won win smil* enjoy* cheer* thank*", 1.0)
_add("Joyful", "good better", 0.7)
# Calm
_add("Calm", "calm* peace* relax* serene rested relieved reconcil* resolved", 1.1)
_add("Calm", "content quiet steady balanced cozy gentle comfortable", 0.8)
_add("Calm", "okay fine", 0.5)

PHRASES_RAW = {}
def _addp(emo, phrases, w):
    for p in phrases.split("|"):
        PHRASES_RAW.setdefault(p, {})[emo] = w

_addp("Sad", "felt bad|feel bad|feeling bad|feels bad|not okay|not ok|not fine|not good|let down|broke up|"
             "break up|fell apart|nobody cares|no one cares|nobody understands|no one understands", 1.5)
_addp("Angry", "fed up|sick of|had enough", 1.2)
_addp("Sad", "fed up|sick of|had enough|tired of", 0.4)
_addp("Angry", "tired of", 0.8)
_addp("Sad", "burnt out|burned out|worn out", 1.0)
_addp("Anxious", "burnt out|burned out|worn out", 0.5)
_addp("Anxious", "can't sleep|cant sleep|couldn't sleep|too much", 1.1)
_addp("Anxious", "can't take|cant take", 0.8)
_addp("Sad", "can't take|cant take", 0.8)
_addp("Calm", "calm down|made up|made peace|feel better|feeling better|feels better", 0.9)
_addp("Joyful", "feel better|feeling better|feels better", 0.4)
_addp("Joyful", "looking forward|look forward|can't wait|cant wait", 1.0)

PHRASES = sorted(PHRASES_RAW.items(), key=lambda kv: -len(kv[0]))
EXACT = {k: v for k, v in LEX_RAW.items() if not k.endswith("*")}
STEMS = [(k[:-1], v) for k, v in LEX_RAW.items() if k.endswith("*")]

NEGATIONS = ["not", "no", "never", "don't", "dont", "didn't", "didnt", "isn't", "isnt", "wasn't", "wasnt",
             "can't", "cant", "cannot", "won't", "hardly", "without", "aren't", "doesn't", "doesnt"]
INTENSIFIERS = ["very", "so", "really", "extremely", "super", "too", "totally", "incredibly", "completely"]
DIMINISHERS = ["slightly", "bit", "little", "somewhat", "kinda", "barely"]
BUT_WORDS = {"but", "however", "although", "though"}
ORDER = ["Sad", "Anxious", "Angry", "Joyful", "Calm"]
CLAUSE_SPLIT = re.compile(r"([.!?;\n,]+|\bbut\b|\bhowever\b|\balthough\b|\bthough\b)")

def _lookup(tok):
    if tok in EXACT:
        return EXACT[tok]
    for stem, w in STEMS:
        if tok.startswith(stem):
            return w
    return None

def lexicon_scores(text):
    text = text.lower().replace("’", "'").replace("‘", "'")
    scores = {e: 0.0 for e in EMOTIONS}
    clauses, boost = [], False
    for i, part in enumerate(CLAUSE_SPLIT.split(text)):
        if i % 2 == 1:
            boost = part in BUT_WORDS
        elif part.strip():
            clauses.append((part, boost))
            boost = False
    n = len(clauses)
    for idx, (clause, after_but) in enumerate(clauses):
        pos = 1 + 0.3 * (idx / (n - 1) if n > 1 else 0)
        if after_but:
            pos *= 1.4
        for ph, w in PHRASES:
            k = clause.count(ph)
            if k:
                for e, v in w.items():
                    scores[e] += v * k * pos
                clause = clause.replace(ph, " ")
        toks = re.findall(r"[a-z']+", clause)
        for i, tok in enumerate(toks):
            w = _lookup(tok)
            if not w:
                continue
            prev = toks[max(0, i - 3):i]
            m = 1.0
            if any(t in INTENSIFIERS for t in prev[-2:]):
                m *= 1.5
            if any(t in DIMINISHERS for t in prev[-2:]):
                m *= 0.6
            neg = any(t in NEGATIONS for t in prev)
            for e, v in w.items():
                v = v * m * pos
                if neg:
                    if e == "Joyful":
                        scores["Sad"] += v * 0.8
                    elif e == "Calm":
                        scores["Anxious"] += v * 0.6
                    else:
                        scores["Calm"] += v * 0.6
                else:
                    scores[e] += v
    return scores

def pick_emotion(scores):
    if sum(scores.values()) < 0.5:
        return "Calm"
    best, bv = "Calm", 0.0
    for e in ORDER:
        if scores[e] > bv + 1e-6:
            best, bv = e, scores[e]
    return best

def keyword_emotion(text):
    return pick_emotion(lexicon_scores(text))

@st.cache_resource(show_spinner="Loading emotion AI model (first time only, ~300 MB)...")
def load_local_model():
    try:
        from transformers import pipeline
        return pipeline("text-classification", model=MODEL_NAME, top_k=None,
                        truncation=True, max_length=512)
    except Exception:
        return None

def _combine(results):
    totals = {e: 0.0 for e in EMOTIONS}
    raw = {r["label"].lower(): float(r["score"]) for r in results}
    for label, score in raw.items():
        totals[LABEL_MAP.get(label, "Calm")] += score
    totals["Calm"] = max(0.0, totals["Calm"] - raw.get("neutral", 0.0) * 0.5)
    s = sum(totals.values()) or 1.0
    return {k: v / s for k, v in totals.items()}

def model_probs(text, use_ai):
    if not use_ai:
        return None, ""
    clf = load_local_model()
    if clf is not None:
        try:
            out = clf(text)
            return _combine(out[0] if isinstance(out[0], list) else out), "Deep-learning model (local)"
        except Exception:
            pass
    token = os.environ.get("HF_TOKEN")
    if token:
        try:
            r = requests.post(
                f"https://router.huggingface.co/hf-inference/models/{MODEL_NAME}",
                headers={"Authorization": f"Bearer {token}"}, json={"inputs": text}, timeout=15)
            if r.status_code == 200:
                data = r.json()
                return _combine(data[0] if isinstance(data[0], list) else data), "Deep-learning model (HF API)"
        except Exception:
            pass
    return None, ""

def get_ai_emotion(text, use_ai=True):
    """Returns (emotion, source). Same engine as the live background, blended with the AI model."""
    lex = lexicon_scores(text)
    total = sum(lex.values())
    model, src = model_probs(text, use_ai)
    if model is None:
        return pick_emotion(lex), "Smart keyword engine (offline)"
    if total < 0.5:
        return max(model, key=model.get), src
    lex_n = {e: lex[e] / total for e in EMOTIONS}
    wl = 0.35 + 0.35 * min(1.0, total / 3.0)
    blend = {e: (1 - wl) * model[e] + wl * lex_n[e] for e in EMOTIONS}
    return max(blend, key=blend.get), f"{src} + keyword engine"

ENGINE_JSON = {
    "exact": EXACT,
    "stems": [[s, w] for s, w in STEMS],
    "phrases": [[p, w] for p, w in PHRASES],
}

# ============================================================
# LIVE BACKGROUND (real-time while typing)
# ============================================================
def ambience(initial="default", analyzed_text="", live=False):
    """Recolours the page. live=True re-scores the journal on EVERY keystroke."""
    script = r"""
<script>
(function(){
  const doc = window.parent.document;
  const E = __ENGINE__, COLORS = __COLORS__, INITIAL = __INITIAL__, ANALYZED = __ANALYZED__, LIVE = __LIVE__;
  const NEG = new Set(__NEG__), INT = new Set(__INT__), DIM = new Set(__DIM__), BUT = new Set(__BUT__);
  const ICON = {Sad:'😔', Anxious:'😟', Angry:'😠', Joyful:'😊', Calm:'😌'};
  const ORDER = ['Sad','Anxious','Angry','Joyful','Calm'];
  const ID = Math.random().toString(36).slice(2);

  function lookup(tok){
    if (Object.prototype.hasOwnProperty.call(E.exact, tok)) return E.exact[tok];
    for (const [st, w] of E.stems){ if (tok.startsWith(st)) return w; }
    return null;
  }

  function score(text){
    text = text.toLowerCase().replace(/[’‘]/g, "'");
    const s = {Sad:0, Anxious:0, Angry:0, Joyful:0, Calm:0};
    const parts = text.split(/([.!?;\n,]+|\bbut\b|\bhowever\b|\balthough\b|\bthough\b)/);
    const clauses = []; let boost = false;
    parts.forEach((p, i) => {
      if (i % 2 === 1){ boost = BUT.has(p); }
      else if (p.trim()){ clauses.push([p, boost]); boost = false; }
    });
    const n = clauses.length;
    clauses.forEach(([c, afterBut], idx) => {
      let pos = 1 + 0.3 * (n > 1 ? idx / (n - 1) : 0);
      if (afterBut) pos *= 1.4;
      for (const [ph, w] of E.phrases){
        const k = c.split(ph).length - 1;
        if (k > 0){ for (const e in w) s[e] += w[e] * k * pos; c = c.split(ph).join(' '); }
      }
      const toks = c.match(/[a-z']+/g) || [];
      toks.forEach((tok, i) => {
        const w = lookup(tok); if (!w) return;
        const prev = toks.slice(Math.max(0, i - 3), i), last2 = prev.slice(-2);
        let m = 1;
        if (last2.some(t => INT.has(t))) m *= 1.5;
        if (last2.some(t => DIM.has(t))) m *= 0.6;
        const neg = prev.some(t => NEG.has(t));
        for (const e in w){
          const v = w[e] * m * pos;
          if (neg){
            if (e === 'Joyful') s.Sad += v * 0.8;
            else if (e === 'Calm') s.Anxious += v * 0.6;
            else s.Calm += v * 0.6;
          } else s[e] += v;
        }
      });
    });
    return s;
  }

  function pick(s){
    let tot = 0; ORDER.forEach(e => tot += s[e]);
    if (tot < 0.5) return null;
    let best = 'Calm', bv = 0;
    ORDER.forEach(e => { if (s[e] > bv + 1e-6){ bv = s[e]; best = e; } });
    return best;
  }

  function paint(emo){
    const c = COLORS[emo] || COLORS['default'];
    ['.stApp','[data-testid="stAppViewContainer"]','[data-testid="stMain"]','[data-testid="stHeader"]']
      .forEach(sel => {
        const el = doc.querySelector(sel);
        if (el){
          el.style.setProperty('transition', 'background-color 0.5s ease');
          el.style.setProperty('background-color', c, 'important');
        }
      });
  }

  function chip(label){
    let el = doc.getElementById('emo-live-chip');
    if (!LIVE){ if (el) el.remove(); return; }
    if (!el){
      el = doc.createElement('div'); el.id = 'emo-live-chip';
      el.style.cssText = 'position:fixed;right:18px;bottom:18px;z-index:9999;padding:8px 16px;' +
        'border-radius:999px;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.15);' +
        'font:600 13px sans-serif;color:#0F172A;';
      doc.body.appendChild(el);
    }
    el.textContent = label ? ('Sensing: ' + ICON[label] + ' ' + label) : 'Sensing: …';
  }

  function update(ta){
    const v = ta.value.trim();
    const emo = v ? pick(score(v)) : null;
    paint(emo || 'default');
    chip(emo);
  }

  function attach(){
    if (!LIVE){ chip(null); return; }
    const ta = doc.querySelector('textarea');
    if (!ta || ta.__emoId === ID) return;
    if (ta.__emoH) ta.removeEventListener('input', ta.__emoH);
    ta.__emoId = ID;
    ta.__emoH = () => update(ta);
    ta.addEventListener('input', ta.__emoH);
    const v = ta.value.trim();
    if (v && v !== ANALYZED.trim()) update(ta);
  }

  paint(INITIAL);
  if (LIVE) chip(INITIAL !== 'default' ? INITIAL : null);
  setInterval(attach, 300);
})();
</script>
"""
    def js(x):
        return json.dumps(x).replace("</", "<\\/")
    script = (script.replace("__ENGINE__", js(ENGINE_JSON)).replace("__COLORS__", js(BG_COLORS))
              .replace("__INITIAL__", js(initial)).replace("__ANALYZED__", js(analyzed_text))
              .replace("__LIVE__", "true" if live else "false")
              .replace("__NEG__", js(NEGATIONS)).replace("__INT__", js(INTENSIFIERS))
              .replace("__DIM__", js(DIMINISHERS)).replace("__BUT__", js(sorted(BUT_WORDS))))
    components.html(script, height=0)

# ============================================================
# ANALYTICS HELPERS
# ============================================================
def prepare_periods(df, view):
    d = df.copy()
    d["score"] = d["emotion"].map(MOOD_SCORE)
    code = {"Daily": "D", "Weekly": "W", "Monthly": "M"}[view]
    d["period"] = d["date_time"].dt.to_period(code).dt.start_time
    return d

def mood_label(avg):
    return min(MOOD_SCORE, key=lambda k: abs(MOOD_SCORE[k] - avg))

def brief_summary(text, emotion):
    words = len(text.split())
    excerpt = text.strip().replace("\n", " ")
    excerpt = excerpt[:100] + "..." if len(excerpt) > 100 else excerpt
    return f"Mood: {emotion} · {words} words · \"{excerpt}\""

def shareable_records(df):
    rows = []
    for _, r in df.iterrows():
        if r["consent_level"] == "Full Access":
            rows.append({"Date & Time": r["date_time"].strftime("%Y-%m-%d %H:%M"), "Access": "Full Entry",
                         "Emotion": r["emotion"], "Entry": r["journal"]})
        elif r["consent_level"] == "Brief Summary Only":
            rows.append({"Date & Time": r["date_time"].strftime("%Y-%m-%d %H:%M"), "Access": "Summary Only",
                         "Emotion": r["emotion"], "Entry": brief_summary(r["journal"], r["emotion"])})
    return pd.DataFrame(rows)

# ============================================================
# SIGN IN / SIGN UP SCREEN
# ============================================================
def auth_screen():
    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        st.title("🌿 Emotion Journal")
        st.markdown("Sign in to your private journal, or create a free account.")
        tab_in, tab_up = st.tabs(["🔑 Sign in", "✨ Create account"])

        with tab_in:
            with st.form("signin_form"):
                u = st.text_input("Username", key="si_user")
                p = st.text_input("Password", type="password", key="si_pass")
                go_in = st.form_submit_button("SIGN IN")
            if go_in:
                if not u.strip() or not p:
                    st.warning("Enter your username and password.")
                else:
                    user, msg = authenticate(u, p)
                    if user:
                        st.session_state["user"] = user
                        st.rerun()
                    else:
                        st.error(msg)

        with tab_up:
            with st.form("signup_form"):
                role_label = st.radio("I am a…", ["Journal user", "Psychologist (reviews journals shared with me)"],
                                      horizontal=True)
                name = st.text_input("Full name", placeholder="e.g. Asha Patil")
                uname = st.text_input("Choose a username", placeholder="letters, numbers, underscore")
                pw1 = st.text_input("Password (min 8 characters)", type="password")
                pw2 = st.text_input("Confirm password", type="password")
                go_up = st.form_submit_button("CREATE ACCOUNT")
            if go_up:
                role = "psychologist" if role_label.startswith("Psychologist") else "user"
                user, msg = create_user(uname, name, pw1, pw2, role)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error(msg)

# ============================================================
# AUTH GATE
# ============================================================
raw = st.session_state.get("user")
user = None
if isinstance(raw, dict) and isinstance(raw.get("id"), int):
    try:
        user = get_user(raw["id"])          # make sure the account still exists
    except Exception:
        user = None
if not user:
    st.session_state.pop("user", None)      # clear any stale value from the old pages
    ambience("default")
    auth_screen()
    st.stop()

st.session_state["user"] = user
uid = user["id"]
is_psy = user["role"] == "psychologist"

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("<h2 style='font-size:1.4rem;margin-bottom:5px;'>🌿 Navigation</h2>", unsafe_allow_html=True)
st.sidebar.markdown(f"👤 **{user['name']}**  \n`@{user['username']}` · {user['role'].title()}")

if is_psy:
    app_mode = st.sidebar.radio("Go to", ["🩺 Psychologist Portal"], label_visibility="collapsed")
    use_ai = False
else:
    app_mode = st.sidebar.radio("Go to", [
        "✍️ Journal & Ambience",
        "📊 Mood Timeline & Analytics",
        "📸 Gentle Memory Recall",
        "🔐 Share With Psychologist",
    ], label_visibility="collapsed")
    st.sidebar.markdown("---")
    use_ai = st.sidebar.checkbox("Use deep-learning emotion model (more accurate)", value=True)

    n_old = count_unclaimed()
    if n_old:
        st.sidebar.markdown("---")
        st.sidebar.caption(f"{n_old} older entr{'y' if n_old == 1 else 'ies'} from before accounts existed.")
        if st.sidebar.button("Add them to my account"):
            claim_unclaimed(uid)
            st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sign out"):
    for k in ("user", "amb_emotion", "amb_text"):
        st.session_state.pop(k, None)
    st.rerun()

# ============================================================
# PAGE 1: JOURNAL
# ============================================================
if app_mode == "✍️ Journal & Ambience":
    st.title("🌿 Emotion-Responsive Intelligent Journaling")
    st.markdown("Write freely. The background colour shifts with your emotions **as you type**.")

    with st.container(border=True):
        journal = st.text_area("✍️ Write your thoughts here:", height=200,
                               placeholder="Start writing about your day, your thoughts, or how you feel...")
        st.subheader("🔒 Sharing for this entry")
        consent_level = st.selectbox(
            "Who can see this entry?", CONSENT_OPTIONS, index=0,
            help="Private by default. A psychologist only sees entries you share AND have granted access for.")
        analyze = st.button("🧠 ANALYZE EMOTION")

    if analyze:
        if not journal.strip():
            st.warning("Please write something in your journal first.")
        else:
            with st.spinner("Analyzing your emotions..."):
                emotion, source = get_ai_emotion(journal, use_ai)
            save_mood(uid, journal, emotion, consent_level)
            st.session_state["amb_emotion"] = emotion
            st.session_state["amb_text"] = journal

            st.success("Emotion analysis completed and saved!")
            st.subheader("🤖 AI Emotion Analysis")
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:.75rem;color:#64748B;font-weight:700;text-transform:uppercase;'>Detected emotion</div>
                <div style='font-family:"DM Serif Display",serif;font-size:2.2rem;color:#0F172A;margin-top:5px;'>{emotion}</div>
            </div>""", unsafe_allow_html=True)
            st.caption(f"Method: {source}")

            st.subheader("💬 A Thought for You")
            st.info(random.choice(QUOTES[emotion]))
            st.subheader("🎵 Music Recommendation")
            st.markdown(f"[🎧 Listen to music for a {emotion.lower()} mood]({MUSIC[emotion]})")

    ambience(initial=st.session_state.get("amb_emotion", "default"),
             analyzed_text=st.session_state.get("amb_text", ""), live=True)

# ============================================================
# PAGE 2: ANALYTICS
# ============================================================
elif app_mode == "📊 Mood Timeline & Analytics":
    ambience("default")
    st.title("📊 Your Emotional Journey")
    df = load_mood_history(uid)

    if df.empty:
        st.info("No journal entries yet. Write one in the Journal tab to build your timeline!")
    else:
        view = st.radio("Track by:", ["Daily", "Weekly", "Monthly"], horizontal=True)
        d = prepare_periods(df, view)
        tick_fmt = {"Daily": "%d %b", "Weekly": "Wk of %d %b", "Monthly": "%b %Y"}[view]
        unit = {"Daily": "day", "Weekly": "week", "Monthly": "month"}[view]

        latest_period = d["period"].max()
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total entries", len(d))
        k2.metric(f"Entries this {unit}", int((d["period"] == latest_period).sum()))
        k3.metric("Most common emotion", d["emotion"].mode()[0])
        k4.metric("Average mood", mood_label(d["score"].mean()))

        with st.container(border=True):
            st.subheader(f"📈 {view} Mood Trend")
            avg = d.groupby("period")["score"].mean().reset_index()
            fig = go.Figure(go.Scatter(
                x=avg["period"], y=avg["score"], mode="lines+markers",
                line=dict(color="#2D5A39", width=4, shape="spline", smoothing=0.8),
                marker=dict(size=12, color="#2D5A39", line=dict(width=3, color="white")),
                fill="tozeroy", fillcolor="rgba(45,90,57,0.12)",
                hovertemplate="%{x|" + tick_fmt + "}<br>Mood score: %{y:.1f}<extra></extra>"))
            fig.update_yaxes(range=[0.5, 5.5], tickvals=list(MOOD_SCORE.values()),
                             ticktext=list(MOOD_SCORE.keys()), gridcolor="#E2E8F0")
            fig.update_xaxes(tickformat=tick_fmt, showgrid=False)
            fig.update_layout(template="plotly_white", height=380, margin=dict(l=10, r=10, t=10, b=10),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            show_plot(fig)

        c1, c2 = st.columns([3, 2])
        with c1:
            with st.container(border=True):
                st.subheader(f"🎨 Emotions per {unit}")
                counts = d.groupby(["period", "emotion"]).size().reset_index(name="entries")
                fig2 = px.bar(counts, x="period", y="entries", color="emotion",
                              color_discrete_map=CHART_COLORS, category_orders={"emotion": EMOTIONS})
                fig2.update_traces(marker_line_width=0)
                fig2.update_xaxes(tickformat=tick_fmt, title=None)
                fig2.update_yaxes(title="Entries", dtick=1, gridcolor="#E2E8F0")
                fig2.update_layout(template="plotly_white", barmode="stack", bargap=0.35, height=360,
                                   margin=dict(l=10, r=10, t=10, b=10), legend_title=None,
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                show_plot(fig2)
        with c2:
            with st.container(border=True):
                st.subheader("🍩 Overall Balance")
                share = d["emotion"].value_counts().reset_index()
                share.columns = ["emotion", "entries"]
                fig3 = px.pie(share, names="emotion", values="entries", hole=0.6,
                              color="emotion", color_discrete_map=CHART_COLORS)
                fig3.update_traces(textinfo="percent", textfont_size=14,
                                   marker=dict(line=dict(color="white", width=3)))
                fig3.update_layout(template="plotly_white", height=360, margin=dict(l=10, r=10, t=10, b=10),
                                   legend_title=None, paper_bgcolor="rgba(0,0,0,0)")
                show_plot(fig3)

        with st.container(border=True):
            st.subheader("📜 Past Journal Entries")
            table = df[["date_time", "emotion", "consent_level", "journal"]].rename(columns={
                "date_time": "Date & Time", "emotion": "Emotion",
                "consent_level": "Sharing", "journal": "Entry"})
            show_df(table)

# ============================================================
# PAGE 3: MEMORY RECALL (per-user album)
# ============================================================
elif app_mode == "📸 Gentle Memory Recall":
    ambience("default")
    st.title("📸 Gentle Memory Recall")
    st.markdown("When you feel overwhelmed or anxious, pause and reconnect with a comforting memory.")

    user_dir = os.path.join(MEMORY_DIR, str(uid))
    os.makedirs(user_dir, exist_ok=True)

    with st.container(border=True):
        uploaded = st.file_uploader("Upload a comforting photo or happy memory:",
                                    type=["png", "jpg", "jpeg", "webp"])
        if uploaded is not None:
            show_image(uploaded.getvalue(), caption="Your comforting memory")
            st.success("Take a deep breath. You've navigated hard moments before, and you can get through this.")
            if st.button("💾 Save to my memory album"):
                ext = os.path.splitext(uploaded.name)[1].lower() or ".jpg"
                path = os.path.join(user_dir, f"{datetime.now():%Y%m%d_%H%M%S}{ext}")
                with open(path, "wb") as f:
                    f.write(uploaded.getvalue())
                st.success("Saved to your album!")
        else:
            st.info("Upload an image from a happy day, a trip, or a loved one to anchor yourself in stressful moments.")

    saved = sorted([f for f in os.listdir(user_dir)
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))], reverse=True)
    if saved:
        with st.container(border=True):
            st.subheader("🖼️ My Memory Album")
            if st.button("🌈 Show me a random comforting memory"):
                show_image(os.path.join(user_dir, random.choice(saved)))
            cols = st.columns(3)
            for i, fname in enumerate(saved):
                with cols[i % 3]:
                    show_image(os.path.join(user_dir, fname))

# ============================================================
# PAGE 4: SHARE WITH PSYCHOLOGIST (optional)
# ============================================================
elif app_mode == "🔐 Share With Psychologist":
    ambience("default")
    st.title("🔐 Share With Your Psychologist")
    st.markdown("You are in control. A psychologist sees nothing unless **you** grant access to their account "
                "and mark entries as shared.")

    with st.container(border=True):
        st.subheader("1️⃣ Grant access")
        st.caption("Ask your psychologist to create a *Psychologist* account, then enter their username here.")
        psy_user = st.text_input("Psychologist's username", placeholder="e.g. dr_sharma")
        duration = st.selectbox("Access lasts for", ["7 days", "30 days", "90 days", "Until I revoke it"], index=1)
        if st.button("✅ GRANT ACCESS"):
            if not psy_user.strip():
                st.warning("Please enter the psychologist's username.")
            else:
                days = {"7 days": 7, "30 days": 30, "90 days": 90, "Until I revoke it": 0}[duration]
                ok, msg = grant_access(uid, psy_user, days)
                (st.success if ok else st.error)(msg)

    grants = list_grants(uid)
    if grants:
        with st.container(border=True):
            st.subheader("👥 Access list")
            for g in grants:
                active = grant_active(g)
                c1, c2 = st.columns([4, 1])
                status = "🟢 Active" if active else "⚪ Revoked / expired"
                until = g["expires_at"] or "no expiry"
                c1.markdown(f"**{g['display_name']}** (@{g['username']}) — {status} · until {until}")
                if active and c2.button("Revoke", key=f"rev_{g['id']}"):
                    revoke_grant(uid, g["id"])
                    st.rerun()

    df = load_mood_history(uid)
    with st.container(border=True):
        st.subheader("2️⃣ Choose which entries to share")
        if df.empty:
            st.info("No entries yet.")
        else:
            b1, b2, b3 = st.columns(3)
            if b1.button("Share ALL (full)"):
                update_consent_all(uid, "Full Access"); st.rerun()
            if b2.button("Share ALL (summary)"):
                update_consent_all(uid, "Brief Summary Only"); st.rerun()
            if b3.button("Stop sharing ALL"):
                update_consent_all(uid, "No Access"); st.rerun()

            edit_df = df[["date_time", "emotion", "journal", "consent_level"]].copy().reset_index(drop=True)
            edit_df["id"] = df["id"].values
            edited = st.data_editor(
                edit_df, hide_index=True, key="share_editor",
                column_order=["date_time", "emotion", "journal", "consent_level"],
                disabled=["date_time", "emotion", "journal", "id"],
                column_config={
                    "date_time": st.column_config.DatetimeColumn("Date & Time", format="DD MMM YYYY, HH:mm"),
                    "emotion": "Emotion", "journal": "Entry",
                    "consent_level": st.column_config.SelectboxColumn("Sharing", options=CONSENT_OPTIONS, required=True),
                })
            if st.button("💾 SAVE SHARING CHOICES"):
                changed = edited[edited["consent_level"] != edit_df["consent_level"]]
                for idx, row in changed.iterrows():
                    update_consent(uid, edit_df.loc[idx, "id"], row["consent_level"])
                st.success(f"Updated {len(changed)} entr{'y' if len(changed) == 1 else 'ies'}.")
                st.rerun()

    if not df.empty:
        with st.container(border=True):
            st.subheader("3️⃣ A copy of what is shared")
            report = shareable_records(df)
            if report.empty:
                st.info("No entries are marked as shared yet.")
            else:
                st.caption("This is exactly what an authorised psychologist can see.")
                show_df(report)
                st.download_button("⬇️ Download shared records (CSV)",
                                   report.to_csv(index=False).encode("utf-8"),
                                   file_name="shared_journal_records.csv", mime="text/csv")

# ============================================================
# PAGE 5: PSYCHOLOGIST PORTAL
# ============================================================
elif app_mode == "🩺 Psychologist Portal":
    ambience("default")
    st.title("🩺 Psychologist Portal")
    st.markdown("You can see only the people who granted you access, and only the entries they chose to share.")

    patients = patients_for(uid)
    if not patients:
        st.info("Nobody has shared a journal with you yet. Give them your username "
                f"**@{user['username']}** so they can grant access from *Share With Psychologist*.")
    else:
        labels = {p["id"]: f"{p['display_name']} (@{p['username']})" for p in patients}
        pid = st.selectbox("Shared by", list(labels.keys()), format_func=lambda x: labels[x])

        if not has_active_grant(uid, pid):            # re-check so revoking applies immediately
            st.error("Access has been revoked or has expired.")
            st.stop()

        records = shareable_records(load_mood_history(pid))
        if records.empty:
            st.info("This person has not shared any entries yet.")
        else:
            with st.container(border=True):
                st.subheader("📈 Shared mood summary")
                counts = records["Emotion"].value_counts().reset_index()
                counts.columns = ["Emotion", "Entries"]
                fig = px.bar(counts, x="Emotion", y="Entries", color="Emotion", color_discrete_map=CHART_COLORS)
                fig.update_layout(template="plotly_white", height=300, showlegend=False,
                                  margin=dict(l=10, r=10, t=10, b=10),
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                show_plot(fig)
            with st.container(border=True):
                st.subheader("📜 Shared records")
                show_df(records)
                st.download_button("⬇️ Download records (CSV)", records.to_csv(index=False).encode("utf-8"),
                                   file_name="shared_records.csv", mime="text/csv")
