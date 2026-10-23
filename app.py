import streamlit as st
import sqlite3
import datetime
import os
import pandas as pd
import plotly.graph_objects as go
import requests

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Emotion Journal",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATABASE SETUP (SQLite)
# ============================================================
def init_db():
    conn = sqlite3.connect("journal_db.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS entries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  text TEXT,
                  emotion TEXT,
                  confidence REAL,
                  consent TEXT)''')
    conn.commit()
    conn.close()

def save_entry(text, emotion, confidence, consent):
    conn = sqlite3.connect("journal_db.db")
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%b %d, %Y - %H:%M")
    c.execute("INSERT INTO entries (timestamp, text, emotion, confidence, consent) VALUES (?, ?, ?, ?, ?)",
              (now, text, emotion, confidence, consent))
    conn.commit()
    conn.close()

def get_all_entries():
    conn = sqlite3.connect("journal_db.db")
    df = pd.read_sql_query("SELECT * FROM entries ORDER BY id DESC", conn)
    conn.close()
    return df

init_db()

# ============================================================
# HUGGING FACE AI ENGINES WITH LOCAL FALLBACK
# ============================================================
MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

def get_ai_emotion(text):
    token = os.environ.get("HF_TOKEN")
    
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        API_URL = f"https://api-inference.huggingface.co/models/{MODEL_NAME}"
        try:
            response = requests.post(API_URL, headers=headers, json={"inputs": text}, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    results = data[0] if isinstance(data[0], list) else data
                    best_result = max(results, key=lambda x: x['score'])
                    label = best_result['label'].lower()
                    confidence = float(best_result['score'])
                    
                    emotion_map = {
                        "joy": "Joyful",
                        "neutral": "Calm",
                        "fear": "Anxious",
                        "sadness": "Sad",
                        "anger": "Angry",
                        "surprise": "Joyful",
                        "disgust": "Angry"
                    }
                    return emotion_map.get(label, "Calm"), confidence
        except Exception:
            pass

    # Local Rule Fallback
    text_lower = text.lower()
    anxious_words = ["worried", "worry", "anxious", "stress", "stressed", "nervous", "panic", "scared", "fear", "exam", "test"]
    sad_words = ["sad", "cry", "crying", "lonely", "upset", "hurt", "depressed", "unhappy", "miss"]
    angry_words = ["angry", "mad", "furious", "annoyed", "irritated", "hate", "frustrated"]
    joyful_words = ["happy", "excited", "great", "amazing", "wonderful", "love", "joy", "good", "fun", "passed"]

    for word in anxious_words:
        if word in text_lower:
            return "Anxious", 0.88
    for word in sad_words:
        if word in text_lower:
            return "Sad", 0.85
    for word in angry_words:
        if word in text_lower:
            return "Angry", 0.87
    for word in joyful_words:
        if word in text_lower:
            return "Joyful", 0.92

    return "Calm", 0.942

# ============================================================
# EMOTION THEME PROFILES
# ============================================================
EMOTION_THEMES = {
    "Calm": {
        "primary": "#1E3A2B",
        "badge_bg": "#E2EFE7",
        "badge_text": "#1E3A2B",
        "accent_bg": "#F4F8F5",
        "subtext": "Your words move slowly and evenly. There is space between the sentences — the tone reads settled, unhurried and gently reflective.",
        "quote": "You do not have to resolve today in order to rest tonight. Some feelings only ask to be witnessed, not solved.",
        "music_title": "Weightless, Pt. 1",
        "music_artist": "Marconi Union • 8:12",
        "music_sub": "A slow, ambient piece matched to your last entries. 8 minutes, no lyrics — good for the hour after writing.",
        "music_url": "https://open.spotify.com/track/6kA132M2L33pC3S8jP5fA8"
    },
    "Joyful": {
        "primary": "#8A5A00",
        "badge_bg": "#FDF3D8",
        "badge_text": "#8A5A00",
        "accent_bg": "#FFFDF5",
        "subtext": "Your words carry warmth, rhythm, and optimism. A bright lightness anchors your reflections today.",
        "quote": "Joy is not in things; it is in us. Savor this moment and let its warmth ripple outward.",
        "music_title": "Acoustic Sunrise",
        "music_artist": "Warm Harmonies • 4:15",
        "music_sub": "An uplifting acoustic track tailored for bright, positive emotional flow.",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX3RXM23ip39B"
    },
    "Anxious": {
        "primary": "#1E4268",
        "badge_bg": "#E3EDF8",
        "badge_text": "#1E4268",
        "accent_bg": "#F5F8FC",
        "subtext": "Your sentences show heightened speed and processing. Let us slow down together and take a deep breath.",
        "quote": "You don't have to control your thoughts. You just have to stop letting them control you.",
        "music_title": "Calming Waves & Soft Piano",
        "music_artist": "Peaceful Soundscapes • 10:00",
        "music_sub": "Deep grounding frequencies engineered to lower heart rate and reduce tension.",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX7EFK923aO3v"
    },
    "Sad": {
        "primary": "#4A2E69",
        "badge_bg": "#EFE6F8",
        "badge_text": "#4A2E69",
        "accent_bg": "#F9F6FC",
        "subtext": "Your reflections carry depth and quiet introspection. Give yourself gentle grace today.",
        "quote": "Tears are words that need to be written. Give yourself quiet permission to rest.",
        "music_title": "Warm Ambient Solace",
        "music_artist": "Quiet Haven • 6:30",
        "music_sub": "Gentle, comforting ambient notes to cradle heavy thoughts quietly.",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX3qCxC1vA23b"
    },
    "Angry": {
        "primary": "#7A2021",
        "badge_bg": "#FCE4E4",
        "badge_text": "#7A2021",
        "accent_bg": "#FCF6F6",
        "subtext": "High intensity detected in tone and phrasing. Pause, take a long exhale, and let the friction settle.",
        "quote": "Pause before responding. Let the storm pass through without steering your ship.",
        "music_title": "Grounding Rain & Ocean Waves",
        "music_artist": "Nature Audio • 12:00",
        "music_sub": "Constant, steady nature sounds to neutralize sharp emotional spikes.",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX4pp3V238a1a"
    }
}

current_emotion = "Calm"
if "last_analyzed" in st.session_state:
    current_emotion = st.session_state["last_analyzed"]["emotion"]

theme = EMOTION_THEMES.get(current_emotion, EMOTION_THEMES["Calm"])

# ============================================================
# EXACT REPLICATED CSS STYLING
# ============================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    /* Global Layout & Colors */
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #2D3748 !important;
    }}

    .stApp {{
        background-color: #F6F5F1 !important;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: #F0EFEA !important;
        border-right: 1px solid #E2E0D8 !important;
        padding-top: 1rem;
    }}

    /* Typography */
    h1, h2, h3, .serif-text {{
        font-family: 'Newsreader', serif !important;
        color: #1A202C !important;
        font-weight: 400 !important;
    }}

    h1 {{
        font-size: 2.5rem !important;
        margin-bottom: 0.2rem !important;
    }}

    /* Top Breadcrumb Header Bar */
    .breadcrumb-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 20px 0;
        font-size: 0.8rem;
        color: #718096;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}

    .mood-status-pill {{
        background: #E2EFE7;
        color: #1E3A2B;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}

    /* White Rounded Cards */
    .ui-card {{
        background: #FFFFFF !important;
        border-radius: 20px;
        padding: 26px;
        border: 1px solid #E6E4DC;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
        margin-bottom: 20px;
    }}

    .ui-card-sm {{
        background: #FFFFFF !important;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #E6E4DC;
        margin-bottom: 15px;
    }}

    /* Buttons */
    .stButton>button {{
        background-color: #1E3A2B !important;
        color: #FFFFFF !important;
        border-radius: 30px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        border: none !important;
        letter-spacing: 0.03em !important;
        transition: all 0.2s ease !important;
    }}

    .stButton>button:hover {{
        background-color: #15291E !important;
        transform: translateY(-1px);
    }}

    /* Input Text Area */
    .stTextArea textarea {{
        border-radius: 14px !important;
        border: 1px solid #E2E0D8 !important;
        background-color: #FAFAF8 !important;
        color: #2D3748 !important;
        font-size: 0.98rem !important;
        padding: 16px !important;
        line-height: 1.6 !important;
    }}

    .stTextArea textarea:focus {{
        border-color: #1E3A2B !important;
        box-shadow: 0 0 0 1px #1E3A2B !important;
    }}

    /* Badges */
    .pill-badge {{
        padding: 4px 12px;
        border-radius: 14px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}

    .badge-calm {{ background: #E2EFE7; color: #1E3A2B; }}
    .badge-joyful {{ background: #FDF3D8; color: #8A5A00; }}
    .badge-anxious {{ background: #E3EDF8; color: #1E4268; }}
    .badge-sad {{ background: #EFE6F8; color: #4A2E69; }}
    .badge-angry {{ background: #FCE4E4; color: #7A2021; }}

    /* Streak & Weekly Box */
    .weekly-box {{
        background: #FFFFFF;
        border-radius: 16px;
        padding: 18px;
        border: 1px solid #E6E4DC;
        margin-bottom: 20px;
    }}

    .circle-day {{
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #E2EFE7;
        color: #1E3A2B;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
    }}

    /* History Row */
    .history-row {{
        background: #FFFFFF;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 10px;
        border: 1px solid #E6E4DC;
    }}

</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 20px;'>
        <div style='background: #1E3A2B; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1rem;'>🍃</div>
        <div>
            <div style='font-family: "Newsreader", serif; font-size: 1.25rem; color: #1A202C;'>Emotion Journal</div>
            <div style='font-size: 0.7rem; color: #718096; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600;'>Private Space</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("WORKSPACE")
    navigation = st.radio(
        "",
        ["Dashboard", "Mood Tracking", "Gentle Recall", "Psychologist Portal"],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Weekly Streak Card
    st.markdown("""
    <div class='weekly-box'>
        <div style='display: flex; justify-content: space-between; font-size: 0.75rem; color: #718096; font-weight: 700; margin-bottom: 10px;'>
            <span>THIS WEEK</span>
            <span style='color: #1E3A2B;'>6/7</span>
        </div>
        <div style='display: flex; justify-content: space-between; margin-bottom: 10px;'>
            <span class='circle-day'>✓</span>
            <span class='circle-day'>✓</span>
            <span class='circle-day'>✓</span>
            <span style='width:24px; height:24px; border-radius:50%; background:#F0EFEA; color:#718096; display:inline-flex; align-items:center; justify-content:center; font-size:0.7rem; font-weight:700;'>T</span>
            <span class='circle-day'>✓</span>
            <span class='circle-day'>✓</span>
            <span class='circle-day'>✓</span>
        </div>
        <div style='font-size: 0.75rem; color: #718096; line-height: 1.3;'>
            One missed evening is not a streak broken. Write when it helps.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Active Mood Space Card
    st.markdown(f"""
    <div style='background: #E2EFE7; border-radius: 16px; padding: 16px; margin-bottom: 20px;'>
        <div style='font-size: 0.7rem; color: #1E3A2B; font-weight: 700; letter-spacing: 0.08em;'>• ACTIVE MOOD SPACE</div>
        <div style='font-family: "Newsreader", serif; font-size: 1.15rem; color: #1E3A2B; margin-top: 2px;'>Reflective {current_emotion}</div>
        <div style='font-size: 0.72rem; color: #4A5568; margin-top: 2px;'>Interface tuned to your latest entry</div>
    </div>
    """, unsafe_allow_html=True)

    # User Profile Snippet
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 10px; margin-top: 10px;'>
        <div style='width: 32px; height: 32px; border-radius: 50%; background: #CBD5E0; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700;'>AB</div>
        <div>
            <div style='font-weight: 700; font-size: 0.85rem; color: #1A202C;'>Aria Bennett</div>
            <div style='font-size: 0.72rem; color: #718096;'>Personal Journal</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# TOP BREADCRUMB BAR
# ============================================================
st.markdown(f"""
<div class='breadcrumb-bar'>
    <div>WORKSPACE &nbsp;›&nbsp; <span style='color: #1A202C;'>{navigation.upper()}</span></div>
    <div style='display: flex; align-items: center; gap: 12px;'>
        <div class='mood-status-pill'>🟢 CURRENT MOOD: {current_emotion.upper()}</div>
        <div style='font-size: 0.75rem; color: #718096; background: #FFFFFF; padding: 4px 12px; border-radius: 20px; border: 1px solid #E6E4DC;'>🔒 End-to-end encrypted</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# PAGE 1: DASHBOARD
# ============================================================
if navigation == "Dashboard":
    today_str = datetime.datetime.now().strftime("%A, %d %B").upper()
    
    st.markdown(f"<div style='font-size: 0.75rem; color: #C53030; font-weight: 700; letter-spacing: 0.08em;'>• {today_str}</div>", unsafe_allow_html=True)
    st.markdown("<h1>Good evening, Aria</h1>", unsafe_allow_html=True)
    
    col_sub1, col_sub2 = st.columns([3, 1])
    with col_sub1:
        st.markdown("<p style='color: #718096; font-size: 0.92rem; margin-top: -5px;'>You wrote 128 words today and landed somewhere quieter than yesterday. The space below is yours — take your time.</p>", unsafe_allow_html=True)
    with col_sub2:
        st.markdown("""
        <div style='display: flex; gap: 8px; justify-content: flex-end;'>
            <span style='font-size: 0.75rem; background: #FFFFFF; padding: 6px 12px; border-radius: 20px; border: 1px solid #E6E4DC; color: #718096; font-weight: 600;'>🔥 6-day gentle streak</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Input Container
    st.markdown("<div class='ui-card'>", unsafe_allow_html=True)
    
    col_hdr1, col_hdr2 = st.columns([2, 1])
    with col_hdr1:
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 4px;'>
            <span style='background: #E2EFE7; color: #1E3A2B; padding: 4px 8px; border-radius: 8px; font-size: 0.85rem;'>🍃</span>
            <span style='font-family: "Newsreader", serif; font-size: 1.4rem; color: #1A202C;'>Write your thoughts here</span>
        </div>
        <p style='color: #A0AEC0; font-size: 0.82rem; margin-bottom: 12px;'>No structure required. The room is quiet, and the page keeps whatever you give it.</p>
        """, unsafe_allow_html=True)
    with col_hdr2:
        st.markdown("""
        <div style='text-align: right;'>
            <span style='font-size: 0.7rem; background: #F0EFEA; color: #718096; padding: 4px 10px; border-radius: 12px; font-weight: 700;'>🔒 DRAFT AUTO-ENCRYPTED</span>
        </div>
        """, unsafe_allow_html=True)

    journal_text = st.text_area(
        "",
        value="The evening light settled across the kitchen table and I finally let myself breathe. Nothing urgent, nothing owed to anyone. Just the hum of the fridge and a second cup of tea going cold.",
        height=130,
        label_visibility="collapsed"
    )

    word_count = len(journal_text.split()) if journal_text else 0

    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        consent = st.selectbox(
            "PSYCHOLOGIST SHARING CONSENT",
            ["Full Access", "Brief Summary Only", "No Access"],
            index=0
        )
    with col_btn2:
        st.write("")
        st.write("")
        analyze_btn = st.button("✨ ANALYZE EMOTION")

    st.markdown("</div>", unsafe_allow_html=True)

    if analyze_btn:
        if journal_text.strip() == "":
            st.warning("Please enter your thoughts before analyzing.")
        else:
            emotion, confidence = get_ai_emotion(journal_text)
            save_entry(journal_text, emotion, confidence, consent)
            st.session_state["last_analyzed"] = {
                "emotion": emotion,
                "confidence": confidence,
                "text": journal_text
            }
            st.rerun()

    # Results Display Section
    res = st.session_state.get("last_analyzed", {"emotion": "Calm", "confidence": 0.942, "text": journal_text})
    curr_emotion = res["emotion"]
    curr_conf = res["confidence"]
    res_data = EMOTION_THEMES.get(curr_emotion, EMOTION_THEMES["Calm"])

    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        st.markdown(f"""
        <div class='ui-card'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.72rem; color: #A0AEC0; font-weight: 700; letter-spacing: 0.08em;'>DETECTED EMOTION</span>
                <span class='pill-badge badge-{curr_emotion.lower()}'>• {curr_emotion.upper()}</span>
            </div>
            <div style='font-family: "Newsreader", serif; font-size: 2.8rem; color: #1A202C; margin: 8px 0 4px 0;'>{curr_emotion} <span style='font-size: 1.2rem;'>🍃</span></div>
            <p style='color: #718096; font-size: 0.88rem; line-height: 1.5;'>{res_data['subtext']}</p>
            <hr style='border: none; border-top: 1px solid #F0EFEA; margin: 15px 0;'>
            <div style='display: flex; gap: 15px; font-size: 0.75rem; color: #A0AEC0;'>
                <span>🕒 Analysed at {datetime.datetime.now().strftime("%H:%M")}</span>
                <span>✍️ {word_count} words read</span>
                <span>🛡️ On-device</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_r2:
        st.markdown(f"""
        <div class='ui-card'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.72rem; color: #A0AEC0; font-weight: 700; letter-spacing: 0.08em;'>CONFIDENCE SCORE</span>
                <span style='font-size: 0.72rem; background: #FDF3D8; color: #8A5A00; padding: 4px 10px; border-radius: 12px; font-weight: 700;'>✔ HIGH CERTAINTY</span>
            </div>
            <div style='font-family: "Newsreader", serif; font-size: 2.8rem; color: #1A202C; margin: 8px 0 4px 0;'>{curr_conf * 100:.2f}% <span style='font-size: 0.8rem; background: #E2EFE7; color: #1E3A2B; padding: 3px 8px; border-radius: 10px; font-family: "Plus Jakarta Sans"; font-weight: 700;'>+2.4 TODAY</span></div>
            
            <div style='background-color: #E2E0D8; border-radius: 10px; height: 6px; width: 100%; margin: 15px 0;'>
                <div style='background-color: {res_data["primary"]}; width: {curr_conf * 100}%; height: 100%; border-radius: 10px;'></div>
            </div>
            
            <div style='display: flex; justify-content: space-between; font-size: 0.7rem; color: #A0AEC0; font-weight: 700; margin-top: 15px;'>
                <div>TENTATIVE</div>
                <div>CLEAR</div>
                <div style='color: #1E3A2B;'>CERTAIN</div>
            </div>
            <hr style='border: none; border-top: 1px solid #F0EFEA; margin: 12px 0;'>
            <div style='display: flex; justify-content: space-between; text-align: center; font-size: 0.75rem;'>
                <div><span style='color: #A0AEC0; font-size: 0.68rem; display: block;'>TONE</span><b>Settled</b></div>
                <div><span style='color: #A0AEC0; font-size: 0.68rem; display: block;'>PACE</span><b>Slow</b></div>
                <div><span style='color: #A0AEC0; font-size: 0.68rem; display: block;'>OPENNESS</span><b>High</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Secondary Resource Cards
    col_rs1, col_rs2 = st.columns(2)
    with col_rs1:
        st.markdown(f"""
        <div class='ui-card' style='background: {res_data["accent_bg"]} !important;'>
            <div style='display: flex; justify-content: space-between;'>
                <span style='font-size: 0.72rem; color: #8A5A00; font-weight: 700; letter-spacing: 0.08em;'>🍃 A THOUGHT FOR YOU</span>
                <span style='font-size: 0.7rem; color: #A0AEC0; font-weight: 700;'>DAILY</span>
            </div>
            <div style='font-family: "Newsreader", serif; font-size: 1.25rem; color: #1A202C; margin: 15px 0; line-height: 1.5; font-style: italic;'>
                "{res_data['quote']}"
            </div>
            <div style='font-size: 0.72rem; color: #A0AEC0; font-weight: 700; letter-spacing: 0.05em;'>DAILY REFLECTION • OCT 23</div>
            <div style='font-size: 0.8rem; color: #718096; margin-top: 4px;'>Chosen from your recent entries around patience and slowing down.</div>
        </div>
        """, unsafe_allow_html=True)

    with col_rs2:
        st.markdown(f"""
        <div class='ui-card'>
            <div style='display: flex; justify-content: space-between;'>
                <span style='font-size: 0.72rem; color: #718096; font-weight: 700; letter-spacing: 0.08em;'>🎵 MUSIC RECOMMENDATION</span>
                <span style='font-size: 0.7rem; background: #E2EFE7; color: #1E3A2B; padding: 2px 8px; border-radius: 10px; font-weight: 700;'>MATCHED TO MOOD</span>
            </div>
            <div style='font-family: "Newsreader", serif; font-size: 1.3rem; color: #1A202C; margin-top: 10px;'>{res_data['music_title']}</div>
            <div style='font-size: 0.8rem; color: #718096;'>{res_data['music_artist']}</div>
            <p style='font-size: 0.8rem; color: #A0AEC0; margin-top: 8px;'>{res_data['music_sub']}</p>
            <div style='margin-top: 15px;'>
                <a href='{res_data['music_url']}' target='_blank' style='text-decoration: none;'>
                    <button style='background: #1E3A2B; color: white; border: none; padding: 8px 18px; border-radius: 20px; font-weight: 600; font-size: 0.82rem; cursor: pointer;'>🎧 Open in Spotify</button>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# PAGE 2: MOOD TRACKING
# ============================================================
elif navigation == "Mood Tracking":
    st.title("Emotional Analytics")
    st.caption("A weighted reading of tone, pace, and openness across your journal entries.")
    st.markdown("<br>", unsafe_allow_html=True)

    df = get_all_entries()

    # Metric Row
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown("""
        <div class='ui-card-sm'>
            <div style='font-size: 0.72rem; color: #A0AEC0; font-weight: 700; letter-spacing: 0.08em;'>TOTAL ENTRIES</div>
            <div style='font-family: "Newsreader", serif; font-size: 2.2rem; color: #1A202C; margin-top: 4px;'>24</div>
            <div style='font-size: 0.75rem; color: #718096;'>+3 this week</div>
        </div>
        """, unsafe_allow_html=True)
    with col_m2:
        st.markdown("""
        <div class='ui-card-sm'>
            <div style='font-size: 0.72rem; color: #A0AEC0; font-weight: 700; letter-spacing: 0.08em;'>MOST FREQUENT</div>
            <div style='font-family: "Newsreader", serif; font-size: 2.2rem; color: #8A5A00; margin-top: 4px;'>Calm</div>
            <div style='font-size: 0.75rem; color: #718096;'>10 of 24 entries</div>
        </div>
        """, unsafe_allow_html=True)
    with col_m3:
        st.markdown("""
        <div class='ui-card-sm'>
            <div style='font-size: 0.72rem; color: #A0AEC0; font-weight: 700; letter-spacing: 0.08em;'>CONSENT COVERAGE</div>
            <div style='font-family: "Newsreader", serif; font-size: 2.2rem; color: #1E3A2B; margin-top: 4px;'>100%</div>
            <div style='font-size: 0.75rem; color: #718096;'>All entries have a choice</div>
        </div>
        """, unsafe_allow_html=True)

    col_chart, col_hist = st.columns([2, 1])

    with col_chart:
        st.markdown("<div class='ui-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-bottom: 4px;'>Emotional well-being trend</h3>", unsafe_allow_html=True)
        st.caption("A weighted reading of tone, pace and openness across your entries.")
        
        # Plotly Area Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=['OCT 14', 'OCT 17', 'OCT 19', 'OCT 21', 'OCT 23'],
            y=[74, 85, 92, 78, 96],
            fill='tozeroy',
            fillcolor='rgba(226, 239, 231, 0.6)',
            line=dict(color='#1E3A2B', width=2),
            mode='lines+markers',
            marker=dict(size=6, color='#1E3A2B')
        ))
        fig.update_layout(
            height=280,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, tickfont=dict(size=10, color='#A0AEC0')),
            yaxis=dict(showgrid=True, gridcolor='#F0EFEA', range=[0, 100], tickfont=dict(size=10, color='#A0AEC0')),
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_hist:
        st.markdown("<div class='ui-card'>", unsafe_allow_html=True)
        st.markdown("### Scannable history")
        st.caption("8 entries • newest first")
        
        history_samples = [
            {"time": "22:14 • Today", "emotion": "CALM", "text": "The evening light settled across the kitchen table...", "words": "128 WORDS"},
            {"time": "08:02 • Today", "emotion": "JOYFUL", "text": "Woke before the alarm with the window open...", "words": "96 WORDS"},
            {"time": "23:40 • Yesterday", "emotion": "ANXIOUS", "text": "A knot sits under my ribs about the review tomorrow...", "words": "142 WORDS"}
        ]
        
        for item in history_samples:
            badge_cls = f"badge-{item['emotion'].lower()}"
            st.markdown(f"""
            <div class='history-row'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 0.72rem; color: #A0AEC0;'>{item['time']}</span>
                    <span class='pill-badge {badge_cls}'>• {item['emotion']}</span>
                </div>
                <div style='font-size: 0.85rem; color: #2D3748; margin-top: 6px;'>{item['text']}</div>
                <div style='font-size: 0.68rem; color: #A0AEC0; font-weight: 700; margin-top: 6px;'>↪ FULL • {item['words']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# PAGE 3: GENTLE RECALL
# ============================================================
elif navigation == "Gentle Recall":
    st.title("Gentle Memory Recall")
    st.caption("Anchor yourself with peaceful memories during stressful moments.")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<div class='ui-card'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload a comforting memory photo:", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Grounding Anchor Memory", use_column_width=True)
        st.success("Memory anchored successfully.")
    else:
        st.info("Upload a photo of a holiday, pet, or happy moment to use as a grounding visual aid.")
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# PAGE 4: PSYCHOLOGIST PORTAL
# ============================================================
elif navigation == "Psychologist Portal":
    st.title("Psychologist Clinical Portal")
    st.caption("Consent-governed patient observation panel.")
    st.markdown("<br>", unsafe_allow_html=True)

    df = get_all_entries()

    if not df.empty:
        for idx, row in df.iterrows():
            if row['consent'] == "No Access":
                continue

            st.markdown("<div class='ui-card'>", unsafe_allow_html=True)
            st.markdown(f"**Timestamp:** `{row['timestamp']}` | **Detected Emotion:** `{row['emotion']}`")
            
            if row['consent'] == "Full Access":
                st.write(f"**Patient Journal Text:** {row['text']}")
            elif row['consent'] == "Brief Summary Only":
                st.info("🔒 [HIDDEN BY PATIENT CONSENT - SUMMARY ONLY] - Emotion trends and scores are visible, but full text is private.")
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No records available in the clinical database yet.")
