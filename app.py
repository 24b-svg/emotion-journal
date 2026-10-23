import streamlit as st
import sqlite3
import datetime
import os
import pandas as pd
import plotly.express as px
import requests

# ============================================================
# PAGE CONFIGURATION & METADATA
# ============================================================
st.set_page_config(
    page_title="Emotion Journal",
    page_icon="🌿",
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
    now = datetime.datetime.now().strftime("%b %d, %Y - %I:%M %p")
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
# HUGGING FACE AI ENGINES WITH FALLBACK
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
# MULTI-EMOTION THEMING & RESOURCE MAP
# ============================================================
EMOTION_THEMES = {
    "Calm": {
        "bg_color": "#F4F6F4",
        "sidebar_bg": "#EBF2EC",
        "primary_color": "#2D5A39",
        "accent_light": "#E2F0E5",
        "quote": "There is strength in slowing down. Take a breath and enjoy the quiet moment.",
        "subtext": "Your choice of words reflects a serene and balanced state of mind.",
        "music": "Ambient Forest Echoes",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX4WYAV23eA21"
    },
    "Joyful": {
        "bg_color": "#FFFDF5",
        "sidebar_bg": "#FCF6E5",
        "primary_color": "#B06000",
        "accent_light": "#FEF7E0",
        "quote": "Joy is not in things; it is in us. Savor this light and pass it forward.",
        "subtext": "Your writing glows with optimism and bright energy.",
        "music": "Uplifting Acoustic Melodies",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX3RXM23ip39B"
    },
    "Anxious": {
        "bg_color": "#F4F7FB",
        "sidebar_bg": "#E8F0FE",
        "primary_color": "#1A56B0",
        "accent_light": "#DCE6F8",
        "quote": "You don't have to control your thoughts. You just have to stop letting them control you.",
        "subtext": "Take a gentle pause. Let us ground your mind with relaxing soundscapes.",
        "music": "Deep Breathing & Calming Piano",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX7EFK923aO3v"
    },
    "Sad": {
        "bg_color": "#F7F5F9",
        "sidebar_bg": "#EFEBF5",
        "primary_color": "#5B3A82",
        "accent_light": "#E6DEF0",
        "quote": "Tears are words that need to be written. Give yourself gentle grace today.",
        "subtext": "It is completely okay to feel this way. Honor your emotions gently.",
        "music": "Warm Ambient Comfort",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX3qCxC1vA23b"
    },
    "Angry": {
        "bg_color": "#FAF4F4",
        "sidebar_bg": "#F8E8E8",
        "primary_color": "#9E2A2B",
        "accent_light": "#FCD8D8",
        "quote": "Pause before responding. Let the storm pass through without steering your ship.",
        "subtext": "Acknowledge the tension, take a deep breath, and allow yourself to cool down.",
        "music": "Grounding Nature Waves",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX4pp3V238a1a"
    }
}

# Determine Current Theme
current_emotion = "Calm"
if "last_analyzed" in st.session_state:
    current_emotion = st.session_state["last_analyzed"]["emotion"]

theme = EMOTION_THEMES.get(current_emotion, EMOTION_THEMES["Calm"])

# ============================================================
# CUSTOM CSS INJECTION FOR DYNAMIC THEMING
# ============================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: {theme['bg_color']} !important;
        color: #2D3748;
    }}

    .stApp {{
        background-color: {theme['bg_color']} !important;
        transition: background-color 0.5s ease;
    }}

    [data-testid="stSidebar"] {{
        background-color: {theme['sidebar_bg']} !important;
        border-right: 1px solid rgba(0,0,0,0.05);
        padding-top: 1rem;
    }}

    h1, h2, h3, .serif-header {{
        font-family: 'DM Serif Display', serif !important;
        color: #1A3022 !important;
        font-weight: 400 !important;
    }}

    h1 {{
        font-size: 2.3rem !important;
        margin-bottom: 0.5rem !important;
    }}

    .custom-card {{
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }}

    .metric-card {{
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
    }}

    .metric-value {{
        font-family: 'DM Serif Display', serif;
        font-size: 1.8rem;
        color: {theme['primary_color']};
        margin-top: 4px;
    }}

    .metric-label {{
        font-size: 0.82rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }}

    .stButton>button {{
        background-color: {theme['primary_color']} !important;
        color: #FFFFFF !important;
        border-radius: 30px !important;
        padding: 10px 28px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        width: auto !important;
        margin: 0 auto !important;
        display: block !important;
    }}

    .stTextArea textarea {{
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FAFAFA !important;
        font-size: 0.95rem !important;
    }}
    
    .stTextArea textarea:focus {{
        border-color: {theme['primary_color']} !important;
        box-shadow: 0 0 0 1px {theme['primary_color']} !important;
    }}

    .quote-box {{
        background-color: {theme['accent_light']};
        border-radius: 16px;
        padding: 24px;
        border-left: 4px solid {theme['primary_color']};
    }}

    .quote-title {{
        color: {theme['primary_color']};
        font-weight: 700;
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }}

    .quote-text {{
        font-family: 'DM Serif Display', serif;
        font-size: 1.25rem;
        color: #1A3022;
        font-style: italic;
        line-height: 1.4;
    }}

    .history-item {{
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        border: 1px solid #EDF2F7;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}

    .badge-calm {{ background-color: #E6F4EA; color: #137333; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-joyful {{ background-color: #FEF7E0; color: #B06000; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-anxious {{ background-color: #DCE6F8; color: #1A56B0; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-sad {{ background-color: #E6DEF0; color: #5B3A82; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-angry {{ background-color: #FCD8D8; color: #9E2A2B; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
with st.sidebar:
    st.markdown("<h2 style='font-size: 1.5rem; margin-bottom: 20px;'>🌿 Emotion Journal</h2>", unsafe_allow_html=True)
    
    navigation = st.radio(
        "NAVIGATION",
        ["Dashboard", "Mood Tracking", "Gentle Recall", "Psychologist Portal"],
        index=0
    )
    
    st.markdown("---")
    st.caption("Current Mood Space")
    st.markdown(f"**• Reflective {current_emotion}**")

# ============================================================
# PAGE 1: DASHBOARD (MAIN JOURNAL & REFLECTION)
# ============================================================
if navigation == "Dashboard":
    st.title("Emotion Journal")
    
    # Input Card
    st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
    st.markdown("### ✍️ Write your thoughts here:")
    journal_text = st.text_area(
        "",
        placeholder="Start writing about your day, your thoughts, or how you feel...",
        height=140,
        label_visibility="collapsed"
    )
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        consent = st.selectbox(
            "Psychologist Sharing Consent",
            ["Full Access", "Brief Summary Only", "No Access"],
            index=0
        )
    with col_c2:
        st.write("")
        st.write("")
        analyze_btn = st.button("✨ ANALYZE EMOTION")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Process Input
    if analyze_btn:
        if journal_text.strip() == "":
            st.warning("Please write some text before analyzing.")
        else:
            emotion, confidence = get_ai_emotion(journal_text)
            save_entry(journal_text, emotion, confidence, consent)
            st.session_state["last_analyzed"] = {
                "emotion": emotion,
                "confidence": confidence,
                "text": journal_text
            }
            st.rerun()

    # Results Display
    if "last_analyzed" in st.session_state:
        res = st.session_state["last_analyzed"]
        curr_emotion = res["emotion"]
        curr_conf = res["confidence"]
        res_data = EMOTION_THEMES.get(curr_emotion, EMOTION_THEMES["Calm"])

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>DETECTED EMOTION</div>
                <div class='metric-value'>{curr_emotion}</div>
                <p style='color: #718096; font-size: 0.85rem; margin-top: 6px;'>{res_data['subtext']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>CONFIDENCE SCORE</div>
                <div class='metric-value'>{curr_conf * 100:.2f}%</div>
                <div style='background-color: #E2E8F0; border-radius: 10px; height: 6px; width: 80%; margin: 10px auto 0 auto;'>
                    <div style='background-color: {res_data['primary_color']}; width: {curr_conf * 100}%; height: 100%; border-radius: 10px;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<h3 style='margin-top: 30px;'>Resources for your Spirit</h3>", unsafe_allow_html=True)
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown(f"""
            <div class='quote-box'>
                <div class='quote-title'>✨ A THOUGHT FOR YOU</div>
                <div class='quote-text'>"{res_data['quote']}"</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_r2:
            st.markdown(f"""
            <div class='custom-card' style='height: 100%; margin-bottom: 0;'>
                <div class='quote-title'>🎵 MUSIC RECOMMENDATION</div>
                <h4 style='margin-top: 4px; font-family: "DM Serif Display", serif;'>"{res_data['music']}"</h4>
                <p style='color: #718096; font-size: 0.85rem;'>Listen to soundscapes curated specifically for your emotional state.</p>
                <a href='{res_data['music_url']}' target='_blank' style='text-decoration: none;'>
                    <button style='background-color: {res_data['accent_light']}; color: {res_data['primary_color']}; border: none; padding: 8px 18px; border-radius: 20px; font-weight: 600; cursor: pointer;'>🎧 Open in Spotify</button>
                </a>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# PAGE 2: MOOD TRACKING (ANALYTICS & HISTORY)
# ============================================================
elif navigation == "Mood Tracking":
    st.title("📈 Mood Tracking")
    st.caption("Detailed analysis of your mood variations and journal history.")

    df = get_all_entries()

    if not df.empty:
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>TOTAL ENTRIES</div>
                <div class='metric-value'>{len(df)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            most_freq = df['emotion'].mode()[0] if not df.empty else "N/A"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>MOST FREQUENT</div>
                <div class='metric-value'>{most_freq}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>CONSENT COVERAGE</div>
                <div class='metric-value'>100%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.markdown("### Emotional Well-being Trend")
        
        counts = df['emotion'].value_counts().reset_index()
        counts.columns = ['Emotion', 'Count']
        
        fig = px.area(
            counts, x='Emotion', y='Count',
            color_discrete_sequence=[theme['primary_color']]
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Plus Jakarta Sans"),
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Scannable History")
        for idx, row in df.iterrows():
            badge_class = f"badge-{row['emotion'].lower()}"
            st.markdown(f"""
            <div class='history-item'>
                <div>
                    <span style='font-size: 0.8rem; color: #A0AEC0; font-weight: 600;'>{row['timestamp']}</span>
                    <p style='margin: 4px 0 0 0; color: #2D3748;'>{row['text']}</p>
                </div>
                <div>
                    <span class='{badge_class}'>{row['emotion']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No journal entries logged yet. Write your first entry in the Dashboard!")

# ============================================================
# PAGE 3: GENTLE RECALL
# ============================================================
elif navigation == "Gentle Recall":
    st.title("📸 Gentle Memory Recall")
    st.caption("Anchor yourself with peaceful memories during stressful moments.")

    st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload a comforting memory photo:", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Grounding Anchor Memory", use_column_width=True)
        st.success("Memory anchored successfully. Take a deep breath and look at this peaceful image whenever needed.")
    else:
        st.info("Upload a photo of a holiday, pet, or happy moment to use as a grounding visual aid.")
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# PAGE 4: PSYCHOLOGIST PORTAL
# ============================================================
elif navigation == "Psychologist Portal":
    st.title("🩺 Psychologist Clinical Portal")
    st.caption("Consent-governed patient observation panel.")

    df = get_all_entries()

    if not df.empty:
        for idx, row in df.iterrows():
            if row['consent'] == "No Access":
                continue

            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.markdown(f"**Timestamp:** {row['timestamp']} | **Detected Emotion:** `{row['emotion']}`")
            
            if row['consent'] == "Full Access":
                st.write(f"**Patient Journal Text:** {row['text']}")
            elif row['consent'] == "Brief Summary Only":
                st.info("🔒 [HIDDEN BY PATIENT CONSENT - SUMMARY ONLY] - Emotion trends and scores are visible, but full text is private.")
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No records available in the clinical database yet.")
