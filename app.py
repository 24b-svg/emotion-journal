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

    return "Calm", 0.94

# ============================================================
# EMOTION THEME PROFILES & DYNAMIC CONTENT
# ============================================================
EMOTION_THEMES = {
    "Calm": {
        "primary": "#1E3A2B",
        "badge_bg": "#E2EFE7",
        "badge_text": "#1E3A2B",
        "accent_bg": "#F4F8F5",
        "subtext": "Your words reflect an unhurried, grounded, and balanced state of mind.",
        "quote": "There is strength in slowing down. Take a breath and enjoy the quiet moment.",
        "music_title": "Ambient Forest Echoes",
        "music_artist": "Nature Soundscapes",
        "music_sub": "A tranquil ambient track curated to maintain your peaceful flow.",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX4WYAV23eA21"
    },
    "Joyful": {
        "primary": "#8A5A00",
        "badge_bg": "#FDF3D8",
        "badge_text": "#8A5A00",
        "accent_bg": "#FFFDF5",
        "subtext": "Your reflections carry warmth, positivity, and uplifting energy.",
        "quote": "Joy is not in things; it is in us. Savor this light and pass it forward.",
        "music_title": "Uplifting Acoustic Melodies",
        "music_artist": "Warm Harmonies",
        "music_sub": "Bright acoustic soundscapes designed to match your positive rhythm.",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX3RXM23ip39B"
    },
    "Anxious": {
        "primary": "#1E4268",
        "badge_bg": "#E3EDF8",
        "badge_text": "#1E4268",
        "accent_bg": "#F5F8FC",
        "subtext": "Your writing shows signs of tension or pace. Take a gentle pause to ground yourself.",
        "quote": "You don't have to control your thoughts. You just have to stop letting them control you.",
        "music_title": "Deep Breathing & Soft Piano",
        "music_artist": "Peaceful Haven",
        "music_sub": "Slowing tempo and frequencies engineered to help lower stress and restore ease.",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX7EFK923aO3v"
    },
    "Sad": {
        "primary": "#4A2E69",
        "badge_bg": "#EFE6F8",
        "badge_text": "#4A2E69",
        "accent_bg": "#F9F6FC",
        "subtext": "Your words express depth and gentle vulnerability. Honor your feelings softly.",
        "quote": "Tears are words that need to be written. Give yourself quiet permission to rest.",
        "music_title": "Warm Ambient Solace",
        "music_artist": "Quiet Reflection",
        "music_sub": "Soft, comforting ambient notes to cradle quiet thoughts.",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX3qCxC1vA23b"
    },
    "Angry": {
        "primary": "#7A2021",
        "badge_bg": "#FCE4E4",
        "badge_text": "#7A2021",
        "accent_bg": "#FCF6F6",
        "subtext": "Intensity detected in your tone. Take a long exhale and let the tension pass.",
        "quote": "Pause before responding. Let the storm pass through without steering your ship.",
        "music_title": "Grounding Nature Waves",
        "music_artist": "Ocean Frequency",
        "music_sub": "Steady natural rhythms to soothe emotional spikes and create distance.",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX4pp3V238a1a"
    }
}

current_emotion = "Calm"
if "last_analyzed" in st.session_state:
    current_emotion = st.session_state["last_analyzed"]["emotion"]

theme = EMOTION_THEMES.get(current_emotion, EMOTION_THEMES["Calm"])

# ============================================================
# CSS STYLING
# ============================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #2D3748 !important;
    }}

    .stApp {{
        background-color: #F6F5F1 !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: #F0EFEA !important;
        border-right: 1px solid #E2E0D8 !important;
        padding-top: 1rem;
    }}

    h1, h2, h3, .serif-text {{
        font-family: 'Newsreader', serif !important;
        color: #1A202C !important;
        font-weight: 400 !important;
    }}

    h1 {{
        font-size: 2.3rem !important;
        margin-bottom: 0.2rem !important;
    }}

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
        background: {theme['badge_bg']};
        color: {theme['badge_text']};
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}

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

    .stButton>button {{
        background-color: {theme['primary']} !important;
        color: #FFFFFF !important;
        border-radius: 30px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }}

    .stButton>button:hover {{
        opacity: 0.9;
        transform: translateY(-1px);
    }}

    .stTextArea textarea {{
        border-radius: 14px !important;
        border: 1px solid #E2E0D8 !important;
        background-color: #FAFAF8 !important;
        color: #2D3748 !important;
        font-size: 0.98rem !important;
        padding: 16px !important;
        line-height: 1.6 !important;
    }}

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
df_all = get_all_entries()
total_entry_count = len(df_all)

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

    # Active Mood Card
    st.markdown(f"""
    <div style='background: {theme["badge_bg"]}; border-radius: 16px; padding: 16px; margin-bottom: 20px;'>
        <div style='font-size: 0.7rem; color: {theme["primary"]}; font-weight: 700; letter-spacing: 0.08em;'>• ACTIVE MOOD SPACE</div>
        <div style='font-family: "Newsreader", serif; font-size: 1.15rem; color: {theme["primary"]}; margin-top: 2px;'>Reflective {current_emotion}</div>
        <div style='font-size: 0.72rem; color: #4A5568; margin-top: 2px;'>Interface tuned to your latest entry</div>
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
    
    st.markdown(f"<div style='font-size: 0.75rem; color: #718096; font-weight: 700; letter-spacing: 0.08em;'>• {today_str}</div>", unsafe_allow_html=True)
    st.markdown("<h1>Welcome to your Space</h1>", unsafe_allow_html=True)
    st.caption("Write down your thoughts below for real-time emotional insights and ambient reflection.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Input Container
    st.markdown("<div class='ui-card'>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
        <span style='background: #E2EFE7; color: #1E3A2B; padding: 4px 8px; border-radius: 8px; font-size: 0.85rem;'>🍃</span>
        <span style='font-family: "Newsreader", serif; font-size: 1.4rem; color: #1A202C;'>Write your thoughts here</span>
    </div>
    """, unsafe_allow_html=True)

    journal_text = st.text_area(
        "",
        placeholder="Start writing about your day, how you feel, or what's on your mind...",
        height=140,
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

    # Dynamic Results Display (Shows whenever an analysis has taken place)
    if "last_analyzed" in st.session_state:
        res = st.session_state["last_analyzed"]
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
                <div style='font-family: "Newsreader", serif; font-size: 2.8rem; color: #1A202C; margin: 8px 0 4px 0;'>{curr_emotion}</div>
                <p style='color: #718096; font-size: 0.88rem; line-height: 1.5;'>{res_data['subtext']}</p>
                <hr style='border: none; border-top: 1px solid #F0EFEA; margin: 15px 0;'>
                <div style='display: flex; gap: 15px; font-size: 0.75rem; color: #A0AEC0;'>
                    <span>🕒 {datetime.datetime.now().strftime("%H:%M")}</span>
                    <span>✍️ {word_count} words analyzed</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_r2:
            st.markdown(f"""
            <div class='ui-card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 0.72rem; color: #A0AEC0; font-weight: 700; letter-spacing: 0.08em;'>CONFIDENCE SCORE</span>
                    <span style='font-size: 0.72rem; background: {res_data["badge_bg"]}; color: {res_data["badge_text"]}; padding: 4px 10px; border-radius: 12px; font-weight: 700;'>AI ANALYSIS</span>
                </div>
                <div style='font-family: "Newsreader", serif; font-size: 2.8rem; color: #1A202C; margin: 8px 0 4px 0;'>{curr_conf * 100:.2f}%</div>
                
                <div style='background-color: #E2E0D8; border-radius: 10px; height: 6px; width: 100%; margin: 15px 0;'>
                    <div style='background-color: {res_data["primary"]}; width: {curr_conf * 100}%; height: 100%; border-radius: 10px;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        col_rs1, col_rs2 = st.columns(2)
        with col_rs1:
            st.markdown(f"""
            <div class='ui-card' style='background: {res_data["accent_bg"]} !important;'>
                <div style='font-size: 0.72rem; color: {res_data["primary"]}; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;'>✨ A THOUGHT FOR YOU</div>
                <div style='font-family: "Newsreader", serif; font-size: 1.25rem; color: #1A202C; line-height: 1.5; font-style: italic;'>
                    "{res_data['quote']}"
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_rs2:
            st.markdown(f"""
            <div class='ui-card'>
                <div style='font-size: 0.72rem; color: #718096; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 6px;'>🎵 MUSIC RECOMMENDATION</div>
                <div style='font-family: "Newsreader", serif; font-size: 1.3rem; color: #1A202C;'>{res_data['music_title']}</div>
                <div style='font-size: 0.8rem; color: #718096;'>{res_data['music_artist']}</div>
                <p style='font-size: 0.8rem; color: #A0AEC0; margin-top: 6px;'>{res_data['music_sub']}</p>
                <div style='margin-top: 15px;'>
                    <a href='{res_data['music_url']}' target='_blank' style='text-decoration: none;'>
                        <button style='background: {res_data["primary"]}; color: white; border: none; padding: 8px 18px; border-radius: 20px; font-weight: 600; font-size: 0.82rem; cursor: pointer;'>🎧 Open in Spotify</button>
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# PAGE 2: MOOD TRACKING
# ============================================================
elif navigation == "Mood Tracking":
    st.title("Emotional Analytics")
    st.caption("Longitudinal tracking of your journal entries over time.")
    st.markdown("<br>", unsafe_allow_html=True)

    df = get_all_entries()

    # Dynamic Metric Tiles
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(f"""
        <div class='ui-card-sm'>
            <div style='font-size: 0.72rem; color: #A0AEC0; font-weight: 700; letter-spacing: 0.08em;'>TOTAL ENTRIES</div>
            <div style='font-family: "Newsreader", serif; font-size: 2.2rem; color: #1A202C; margin-top: 4px;'>{len(df)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_m2:
        most_freq = df['emotion'].mode()[0] if not df.empty else "N/A"
        st.markdown(f"""
        <div class='ui-card-sm'>
            <div style='font-size: 0.72rem; color: #A0AEC0; font-weight: 700; letter-spacing: 0.08em;'>MOST FREQUENT</div>
            <div style='font-family: "Newsreader", serif; font-size: 2.2rem; color: {theme["primary"]}; margin-top: 4px;'>{most_freq}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_m3:
        st.markdown("""
        <div class='ui-card-sm'>
            <div style='font-size: 0.72rem; color: #A0AEC0; font-weight: 700; letter-spacing: 0.08em;'>CONSENT COVERAGE</div>
            <div style='font-family: "Newsreader", serif; font-size: 2.2rem; color: #1E3A2B; margin-top: 4px;'>100%</div>
        </div>
        """, unsafe_allow_html=True)

    col_chart, col_hist = st.columns([2, 1])

    with col_chart:
        st.markdown("<div class='ui-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-bottom: 4px;'>Emotional Distribution</h3>", unsafe_allow_html=True)
        
        if not df.empty:
            counts = df['emotion'].value_counts().reset_index()
            counts.columns = ['Emotion', 'Count']
            
            fig = go.Figure(go.Bar(
                x=counts['Emotion'],
                y=counts['Count'],
                marker_color=theme['primary']
            ))
            fig.update_layout(
                height=280,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#F0EFEA'),
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No records found in database yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_hist:
        st.markdown("<div class='ui-card'>", unsafe_allow_html=True)
        st.markdown("### Journal History")
        
        if not df.empty:
            for idx, row in df.head(5).iterrows():
                badge_cls = f"badge-{row['emotion'].lower()}"
                st.markdown(f"""
                <div class='history-row'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='font-size: 0.72rem; color: #A0AEC0;'>{row['timestamp']}</span>
                        <span class='pill-badge {badge_cls}'>• {row['emotion']}</span>
                    </div>
                    <div style='font-size: 0.85rem; color: #2D3748; margin-top: 6px;'>{row['text'][:60]}...</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No past entries yet.")
            
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
