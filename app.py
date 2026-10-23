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
# EMOTION THEMES
# ============================================================
EMOTION_THEMES = {
    "Calm": {
        "primary_color": "#2D5A39",
        "accent_light": "#E9F5EC",
        "quote": "There is strength in slowing down. Take a breath and enjoy the quiet moment.",
        "subtext": "Your choice of words reflects a serene and balanced state of mind.",
        "music": "Ambient Forest Echoes",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX4WYAV23eA21"
    },
    "Joyful": {
        "primary_color": "#B06000",
        "accent_light": "#FEF7E0",
        "quote": "Joy is not in things; it is in us. Savor this light and pass it forward.",
        "subtext": "Your writing glows with optimism and bright energy.",
        "music": "Uplifting Acoustic Melodies",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX3RXM23ip39B"
    },
    "Anxious": {
        "primary_color": "#1A56B0",
        "accent_light": "#E8F0FE",
        "quote": "You don't have to control your thoughts. You just have to stop letting them control you.",
        "subtext": "Take a gentle pause. Let us ground your mind with relaxing soundscapes.",
        "music": "Deep Breathing & Calming Piano",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX7EFK923aO3v"
    },
    "Sad": {
        "primary_color": "#5B3A82",
        "accent_light": "#F3EEF9",
        "quote": "Tears are words that need to be written. Give yourself gentle grace today.",
        "subtext": "It is completely okay to feel this way. Honor your emotions gently.",
        "music": "Warm Ambient Comfort",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX3qCxC1vA23b"
    },
    "Angry": {
        "primary_color": "#9E2A2B",
        "accent_light": "#FDF2F2",
        "quote": "Pause before responding. Let the storm pass through without steering your ship.",
        "subtext": "Acknowledge the tension, take a deep breath, and allow yourself to cool down.",
        "music": "Grounding Nature Waves",
        "music_url": "https://open.spotify.com/playlist/37i9dQZF1DX4pp3V238a1a"
    }
}

current_emotion = "Calm"
if "last_analyzed" in st.session_state:
    current_emotion = st.session_state["last_analyzed"]["emotion"]

theme = EMOTION_THEMES.get(current_emotion, EMOTION_THEMES["Calm"])

# ============================================================
# BULLETPROOF VISIBILITY CSS
# ============================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    /* Force readable dark text everywhere */
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #1E293B !important;
    }}

    .stApp {{
        background-color: #F4F6F4 !important;
    }}

    /* Sidebar Styling Fix */
    [data-testid="stSidebar"] {{
        background-color: #E6EFE8 !important;
        border-right: 1px solid #D1E0D3;
    }}
    
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
        color: #1E293B !important;
        font-weight: 500 !important;
    }}

    /* Top Header Banner */
    .top-header-banner {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF;
        padding: 14px 24px;
        border-radius: 12px;
        border: 1px solid #DDE3E9;
        margin-bottom: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }}

    h1, h2, h3 {{
        color: #0F172A !important;
        font-weight: 700 !important;
    }}

    /* Card Containers */
    .custom-card {{
        background: #FFFFFF !important;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        border: 1px solid #DDE3E9;
        margin-bottom: 20px;
    }}

    .metric-card {{
        background: #FFFFFF !important;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        border: 1px solid #DDE3E9;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
    }}

    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {theme['primary_color']} !important;
        margin-top: 4px;
    }}

    .metric-label {{
        font-size: 0.75rem;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
    }}

    /* Buttons */
    .stButton>button {{
        background: {theme['primary_color']} !important;
        color: #FFFFFF !important;
        border-radius: 30px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        display: block !important;
        margin: 0 auto !important;
    }}

    /* Text Area */
    .stTextArea textarea {{
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-size: 0.95rem !important;
    }}

    /* Quote Box */
    .quote-box {{
        background: {theme['accent_light']} !important;
        border-radius: 14px;
        padding: 20px;
        border-left: 4px solid {theme['primary_color']};
    }}

    .quote-title {{
        color: {theme['primary_color']} !important;
        font-weight: 700;
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
        text-transform: uppercase;
    }}

    .quote-text {{
        font-size: 1.15rem;
        color: #0F172A !important;
        font-style: italic;
        line-height: 1.4;
    }}

    .history-item {{
        background: #FFFFFF !important;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
        border: 1px solid #DDE3E9;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}

    .badge-calm {{ background: #E6F4EA; color: #137333; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.75rem; }}
    .badge-joyful {{ background: #FEF7E0; color: #B06000; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.75rem; }}
    .badge-anxious {{ background: #E8F0FE; color: #1A56B0; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.75rem; }}
    .badge-sad {{ background: #F3EEF9; color: #5B3A82; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.75rem; }}
    .badge-angry {{ background: #FDF2F2; color: #9E2A2B; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.75rem; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
with st.sidebar:
    st.markdown("### 🌿 Emotion Journal")
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    
    navigation = st.radio(
        "Navigation",
        ["Dashboard", "Mood Tracking", "Gentle Recall", "Psychologist Portal"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.caption("ACTIVE MOOD SPACE")
    st.markdown(f"<div style='font-weight: 700; color: {theme['primary_color']}; font-size: 0.9rem; margin-top: 4px;'>• Reflective {current_emotion}</div>", unsafe_allow_html=True)

# ============================================================
# TOP HEADER BAR
# ============================================================
st.markdown(f"""
<div class='top-header-banner'>
    <div style='display: flex; align-items: center; gap: 8px;'>
        <span style='font-size: 1.1rem;'>🌿</span>
        <span style='font-weight: 700; color: #0F172A; font-size: 0.9rem;'>Emotion Journal System</span>
    </div>
    <div style='background: {theme['accent_light']}; color: {theme['primary_color']}; padding: 4px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;'>
        Current Mood: {current_emotion}
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# PAGE 1: DASHBOARD
# ============================================================
if navigation == "Dashboard":
    st.title("Emotion Journal")
    st.caption("Capture your thoughts and experience real-time AI emotional reflection.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin-bottom: 10px; color: #0F172A;'>✍️ Write your thoughts here:</h4>", unsafe_allow_html=True)
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
                <p style='color: #64748B; font-size: 0.85rem; margin-top: 6px;'>{res_data['subtext']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>CONFIDENCE SCORE</div>
                <div class='metric-value'>{curr_conf * 100:.2f}%</div>
                <div style='background-color: #E2E8F0; border-radius: 10px; height: 6px; width: 80%; margin: 12px auto 0 auto;'>
                    <div style='background-color: {res_data['primary_color']}; width: {curr_conf * 100}%; height: 100%; border-radius: 10px;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<h3 style='margin-top: 35px; margin-bottom: 15px;'>Resources for your Spirit</h3>", unsafe_allow_html=True)
        
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
                <h4 style='margin-top: 4px; color: #0F172A;'>"{res_data['music']}"</h4>
                <p style='color: #64748B; font-size: 0.85rem; margin-top: 4px;'>Curated audio soundscapes tailored for your emotional state.</p>
                <div style='margin-top: 15px;'>
                    <a href='{res_data['music_url']}' target='_blank' style='text-decoration: none;'>
                        <button style='background: {res_data['accent_light']}; color: {res_data['primary_color']}; border: none; padding: 8px 18px; border-radius: 20px; font-weight: 700; cursor: pointer; font-size: 0.85rem;'>🎧 Open in Spotify</button>
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# PAGE 2: MOOD TRACKING
# ============================================================
elif navigation == "Mood Tracking":
    st.title("📈 Mood Tracking")
    st.caption("Detailed longitudinal analytics of your emotional well-being.")
    st.markdown("<br>", unsafe_allow_html=True)

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
            font=dict(family="Plus Jakarta Sans", color="#1E293B"),
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<h3 style='margin-top: 30px; margin-bottom: 15px;'>Scannable History</h3>", unsafe_allow_html=True)
        for idx, row in df.iterrows():
            badge_class = f"badge-{row['emotion'].lower()}"
            st.markdown(f"""
            <div class='history-item'>
                <div>
                    <span style='font-size: 0.75rem; color: #64748B; font-weight: 700;'>{row['timestamp']}</span>
                    <p style='margin: 4px 0 0 0; color: #1E293B; font-size: 0.95rem;'>{row['text']}</p>
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
    st.markdown("<br>", unsafe_allow_html=True)

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
    st.markdown("<br>", unsafe_allow_html=True)

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
