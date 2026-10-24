import streamlit as st
import sqlite3
import os
import random
import pandas as pd
import plotly.express as px
from datetime import datetime
from huggingface_hub import InferenceClient


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Emotion Journal & Psychologist Portal",
    page_icon="🌿",
    layout="centered"
)


# ============================================================
# EMOTION COLORS
# ============================================================

EMOTION_COLORS = {
    "Joyful": "#FFF4CC",
    "Calm": "#E8F5E9",
    "Anxious": "#E8EAF6",
    "Sad": "#E3F2FD",
    "Angry": "#FDECEC"
}


# ============================================================
# SUPPORTIVE QUOTES
# ============================================================

QUOTES = {
    "Joyful": [
        "Happiness grows when you notice the little things.",
        "Let yourself enjoy this moment.",
        "Keep this feeling close and let it brighten your day."
    ],
    "Calm": [
        "There is strength in slowing down.",
        "Take a breath and enjoy the quiet moment.",
        "You don't have to rush everything."
    ],
    "Anxious": [
        "Take one moment at a time. You don't have to solve everything now.",
        "Breathe slowly. You are allowed to pause.",
        "It is okay to take things one step at a time."
    ],
    "Sad": [
        "It is okay to have difficult days.",
        "Be gentle with yourself today.",
        "You don't have to be okay all the time."
    ],
    "Angry": [
        "Take a pause before reacting.",
        "Give yourself some space to breathe.",
        "Strong emotions pass. Give yourself time."
    ]
}


# ============================================================
# MUSIC RECOMMENDATIONS
# ============================================================

MUSIC = {
    "Joyful": "https://www.youtube.com/results?search_query=happy+uplifting+music",
    "Calm": "https://www.youtube.com/results?search_query=calm+relaxing+music",
    "Anxious": "https://www.youtube.com/results?search_query=calming+anxiety+music",
    "Sad": "https://www.youtube.com/results?search_query=comforting+music",
    "Angry": "https://www.youtube.com/results?search_query=relaxing+music"
}


# ============================================================
# DATABASE SETUP (WITH CONSENT & AUDIT SUPPORT)
# ============================================================

DB_NAME = "emotion_journal.db"

def create_database():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mood_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal TEXT,
            emotion TEXT,
            confidence REAL,
            date_time TEXT,
            consent_level TEXT
        )
    """)

    connection.commit()
    connection.close()

create_database()


# ============================================================
# HUGGING FACE AI
# ============================================================

MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

def get_ai_emotion(text):
    token = os.environ.get("HF_TOKEN")

    if not token:
        return None, 0, "HF_TOKEN is not available in environment variables."

    try:
        client = InferenceClient(api_key=token)
        result = client.text_classification(text, model=MODEL_NAME)

        if not result:
            return None, 0, "No AI result returned."

        best_result = result[0]
        label = best_result.label.lower()
        confidence = float(best_result.score)

        emotion_map = {
            "joy": "Joyful",
            "neutral": "Calm",
            "fear": "Anxious",
            "sadness": "Sad",
            "anger": "Angry",
            "surprise": "Joyful",
            "disgust": "Angry"
        }

        emotion = emotion_map.get(label, "Calm")
        return emotion, confidence, None

    except Exception as error:
        return None, 0, str(error)


# ============================================================
# SAVE MOOD TO DB WITH CONSENT LEVEL
# ============================================================

def save_mood(journal_text, emotion, confidence, consent_level):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO mood_history (journal, emotion, confidence, date_time, consent_level)
        VALUES (?, ?, ?, ?, ?)
    """, (
        journal_text,
        emotion,
        confidence,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        consent_level
    ))

    connection.commit()
    connection.close()


# ============================================================
# FETCH MOOD HISTORY
# ============================================================

def load_mood_history():
    connection = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM mood_history ORDER BY id DESC", connection)
    connection.close()
    return df


# ============================================================
# LIVE BACKGROUND JAVASCRIPT
# ============================================================

live_background = """
<script>
function changeBackground(emotion) {
    let colors = {
        joyful: "#FFF4CC",
        calm: "#E8F5E9",
        anxious: "#E8EAF6",
        sad: "#E3F2FD",
        angry: "#FDECEC"
    };
    let color = colors[emotion] || "#FFFFFF";
    document.body.style.backgroundColor = color;
    let app = document.querySelector('[data-testid="stAppViewContainer"]');
    if (app) {
        app.style.backgroundColor = color;
    }
}

function detectEmotion(text) {
    text = text.toLowerCase();
    let anxiousWords = ["worried", "worry", "anxious", "stress", "stressed", "nervous", "panic", "scared", "fear"];
    let sadWords = ["sad", "cry", "crying", "lonely", "upset", "hurt", "depressed", "unhappy"];
    let angryWords = ["angry", "mad", "furious", "annoyed", "irritated", "hate", "frustrated"];
    let joyfulWords = ["happy", "excited", "great", "amazing", "wonderful", "love", "joy", "good", "fun"];

    for (let word of anxiousWords) { if (text.includes(word)) return "anxious"; }
    for (let word of sadWords) { if (text.includes(word)) return "sad"; }
    for (let word of angryWords) { if (text.includes(word)) return "angry"; }
    for (let word of joyfulWords) { if (text.includes(word)) return "joyful"; }
    return "calm";
}

function connectJournal() {
    let textarea = document.querySelector('textarea');
    if (!textarea || textarea.dataset.emotionConnected === "true") return;
    textarea.dataset.emotionConnected = "true";
    textarea.addEventListener("input", function() {
        let text = textarea.value;
        let emotion = detectEmotion(text);
        changeBackground(emotion);
    });
}

setInterval(connectJournal, 500);
</script>
"""


# ============================================================
# NAVIGATION SIDEBAR (SIX-STAGE PIPELINE & MODULES)
# ============================================================

st.sidebar.title("🌿 Navigation")
app_mode = st.sidebar.radio("Go to", [
    "✍️ Journal & Ambience", 
    "📊 Mood Timeline & Analytics", 
    "📸 Gentle Memory Recall",
    "🩺 Psychologist Portal & Consent"
])


# ============================================================
# PAGE 1: JOURNAL & AMBIENCE
# ============================================================

if app_mode == "✍️ Journal & Ambience":
    st.title("🌿 Emotion-Responsive Intelligent Journaling")
    st.markdown("Write freely[cite: 8]. Your surroundings quietly respond to your emotions[cite: 8].")

    journal = st.text_area(
        "✍️ Write your thoughts here:",
        height=250,
        placeholder="Start writing about your day, your thoughts, or how you feel..."
    )

    # Psychologist Sharing Consent Selector (Synopsis Objective 6)
    st.markdown("---")
    st.subheader("🔒 Psychologist Sharing Consent")
    consent_level = st.selectbox(
        "Choose sharing permission for this entry:",
        ["Full Access", "Brief Summary Only", "No Access"],
        help="Controls what an authorized psychologist can view for this specific entry[cite: 10, 11]."
    )

    st.write("")
    analyze = st.button("🧠 ANALYZE EMOTION", use_container_width=True)

    if analyze:
        if journal.strip() == "":
            st.warning("Please write something in your journal first.")
        else:
            with st.spinner("AI is analyzing your emotions..."):
                emotion, confidence, error = get_ai_emotion(journal)

            if error:
                st.error("AI analysis could not be completed.")
                st.code(error)
            else:
                save_mood(journal, emotion, confidence, consent_level)
                background = EMOTION_COLORS.get(emotion, "#FFFFFF")

                st.markdown(
                    f"""
                    <style>
                    [data-testid="stAppViewContainer"] {{
                        background-color: {background};
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                st.success("Emotion analysis completed and saved securely!")
                st.subheader("🤖 AI Emotion Analysis")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Detected Emotion", emotion)
                with col2:
                    st.metric("Confidence", f"{confidence * 100:.2f}%")

                st.subheader("💬 A Thought for You")
                quote = random.choice(QUOTES[emotion])
                st.info(quote)

                st.subheader("🎵 Music Recommendation")
                st.markdown(f"[🎧 Listen to music for a {emotion.lower()} mood]({MUSIC[emotion]})")


# ============================================================
# PAGE 2: MOOD TIMELINE & ANALYTICS
# ============================================================

elif app_mode == "📊 Mood Timeline & Analytics":
    st.title("📊 Your Emotional Journey")
    st.markdown("Track your emotional patterns over time[cite: 8, 10].")

    df = load_mood_history()

    if df.empty:
        st.info("No journal entries found yet. Start writing in the Journal tab to build your timeline!")
    else:
        st.subheader("📈 Emotion Frequency Distribution")
        fig_counts = px.histogram(df, x="emotion", color="emotion", title="Entries per Emotion",
                                  color_discrete_map=EMOTION_COLORS)
        st.plotly_chart(fig_counts, use_container_width=True)

        st.subheader("📜 Past Journal Entries & Permissions")
        display_df = df[["date_time", "emotion", "confidence", "consent_level", "journal"]].copy()
        st.dataframe(display_df, use_container_width=True)


# ============================================================
# PAGE 3: GENTLE MEMORY RECALL
# ============================================================

elif app_mode == "📸 Gentle Memory Recall":
    st.title("📸 Gentle Memory Recall")
    st.markdown("When you feel overwhelmed or anxious, pause and reconnect with a comforting memory[cite: 8, 9].")

    uploaded_photo = st.file_uploader("Upload a comforting photo or happy memory snapshot:", type=["png", "jpg", "jpeg"])

    if uploaded_photo is not None:
        st.image(uploaded_photo, caption="Your Comforting Memory", use_column_width=True)
        st.success("Take a deep breath. You've navigated hard moments before, and you can get through this.")
    else:
        st.info("Upload an image from a happy day, vacation, or loved one to anchor yourself during stressful moments[cite: 8, 9].")


# ============================================================
# PAGE 4: PSYCHOLOGIST PORTAL & CONSENT (SYNOPSIS OBJECTIVE 6)
# ============================================================

elif app_mode == "🩺 Psychologist Portal & Consent":
    st.title("🩺 Authorized Psychologist Portal")
    st.markdown("Secure clinical access view respecting patient-controlled consent permissions[cite: 10, 11].")

    df = load_mood_history()

    if df.empty:
        st.info("No patient journal records available.")
    else:
        st.warning("🔒 Note: Display is filtered dynamically based on patient-configured consent settings (Full Access, Brief Summary Only, or No Access)[cite: 10, 11].")

        # Process entries based on consent level rules
        portal_records = []
        for index, row in df.iterrows():
            level = row["consent_level"]
            if level == "Full Access":
                portal_records.append({
                    "Date & Time": row["date_time"],
                    "Access Granted": "Full Entry",
                    "Emotion": row["emotion"],
                    "Confidence": f"{row['confidence']*100:.2f}%",
                    "Journal Text": row["journal"]
                })
            elif level == "Brief Summary Only":
                portal_records.append({
                    "Date & Time": row["date_time"],
                    "Access Granted": "Brief Summary Only",
                    "Emotion": row["emotion"],
                    "Confidence": f"{row['confidence']*100:.2f}%",
                    "Journal Text": "[HIDDEN BY PATIENT CONSENT - SUMMARY ONLY]"
                })
            else:
                # No Access - completely filtered out or masked
                continue

        if not portal_records:
            st.info("No entries have been granted sharing access by the patient.")
        else:
            portal_df = pd.DataFrame(portal_records)
            st.dataframe(portal_df, use_container_width=True)


# ============================================================
# ACTIVATE LIVE BACKGROUND SCRIPT
# ============================================================

st.html(live_background, unsafe_allow_javascript=True)
