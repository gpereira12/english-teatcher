import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
import io
import json
from dotenv import load_dotenv

# Load local .env if exists
load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="English Tutor Pro",
    page_icon="🎓",
    layout="centered"
)

# --- DEFINITIVE ULTIMATE PREMIUM CSS (High Contrast + Unified Input) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* 1. Reset Global & Ultra-High Contrast */
    .stApp {
        background-color: #000000 !important; /* Unified pitch black */
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }

    /* 2. Chat Area Padding for Bottom Cockpit */
    .main .block-container {
        padding-bottom: 180px !important;
    }

    /* 3. High Contrast Bubbles (WhatsApp Reimagined) */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
    }

    .bubble {
        padding: 14px 20px;
        border-radius: 20px;
        font-size: 16px;
        line-height: 1.55;
        max-width: 85%;
        margin-bottom: 2px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }

    .bubble-assistant {
        background: #1C1C1E; /* Apple Dark Gray */
        color: #FFFFFF;
        align-self: flex-start;
        border: 1px solid #2C2C2E;
        border-bottom-left-radius: 4px;
    }

    .bubble-user {
        background: #007AFF; /* Apple Blue (High Contrast on Black) */
        color: #FFFFFF;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        font-weight: 500;
    }

    /* 4. Unified Bottom Cockpit (Pill Design) */
    .input-dock {
        position: fixed;
        bottom: 25px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 700px;
        background: #1C1C1E;
        border-radius: 80px; /* 100% Rounding */
        padding: 10px 25px;
        border: 1px solid #2C2C2E;
        display: flex;
        align-items: center;
        gap: 15px;
        z-index: 1000;
        box-shadow: 0 -10px 30px rgba(0,0,0,0.5);
    }

    /* Custom Input overrides to hide borders & round 100% */
    [data-testid="stChatInput"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        border-radius: 50px !important;
    }

    [data-testid="stChatInput"] textarea {
        background-color: #2C2C2E !important;
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        padding-left: 20px !important;
    }

    /* Make Audio Input look like it belongs inside the pill */
    [data-testid="stAudioInput"] {
        border-radius: 50px !important;
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* 5. Feedback intelligence cards */
    .intel-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 12px;
        display: block;
    }

    .score-badge {
        background: #34C759;
        color: black;
        font-weight: 800;
        padding: 2px 10px;
        border-radius: 6px;
        font-size: 0.7rem;
        text-transform: uppercase;
        margin-bottom: 8px;
        display: inline-block;
    }

    /* 6. Typography Visibility */
    p, span, div, h1, h2, h3, label {
        color: #FFFFFF !important;
    }
    
    .stCaption {
        color: #8E8E93 !important;
    }

    /* Hide standard avatars */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- API KEY MANAGEMENT ---
def get_api_key():
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except:
        pass
    return os.getenv("GOOGLE_API_KEY")

api_key = get_api_key()

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.markdown("### 🎓 English Tutor Pro")
    st.caption("Elegance & Accuracy")
    
    if not api_key:
        api_key = st.text_input("Gemini API Key:", type="password")
        if not api_key:
            st.error("🔑 Access Denied. API Key Required.")
            st.stop()
    
    st.divider()
    scenario = st.selectbox(
        "Current Scenario",
        options=['General Conversation', 'Job Interview', 'Ordering Food', 'Tech Meeting'],
        key="scenario_val"
    )
    
    if st.button("Reset Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- AI SETUP ---
if api_key:
    genai.configure(api_key=api_key)
    
    system_instruction = f"""
    You are a professional native English Tutor using the method 'Acquire, Practice, Adjust'.
    Roleplay scenario: '{scenario}'.
    
    YOUR GOAL: 
    1. Act as a character in the roleplay.
    2. Provide correction for any mistakes.
    3. If audio input is detected, estimate the 'Pronunciation Score' (0-100%).
    
    RESPONSE FORMAT (STRICT JSON):
    {{
        "feedback": "Grammar corrections and improvements.",
        "suggestions": ["Better alternative 1", "Better alternative 2"],
        "pronunciation_score": 0,
        "response": "Your character response."
    }}
    
    Always maintain a professional yet engaging tone.
    """
    
    model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash",
        system_instruction=system_instruction
    )

# --- SESSION MGMT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- MAIN INTERFACE ---
st.title("🎓 English Tutor Pro")
st.caption(f"Currently practicing: **{scenario}**")

# Message Loop
for msg in st.session_state.messages:
    role = msg["role"]
    bubble_class = "bubble-user" if role == "user" else "bubble-assistant"
    
    with st.chat_message(role):
        if role == "assistant":
            # Display Intelligence (Feedback/Suggestions)
            intel_html = ""
            if msg.get("feedback") or msg.get("pronunciation_score"):
                p_score = msg.get("pronunciation_score", 0)
                intel_html = f"""
                <div class="intel-card">
                    {f'<div class="score-badge">Speech Accuracy: {p_score}%</div><br>' if p_score > 0 else ''}
                    <b>💡 Adjust:</b> {msg.get("feedback", "Everything is perfect!")}<br>
                    <b>✨ Practice:</b> {", ".join(msg.get("suggestions", []))}
                </div>
                """
            st.markdown(f'<div class="bubble {bubble_class}">{intel_html}{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("audio"):
                st.audio(msg.get("audio"), format="audio/mp3")
        else:
            st.markdown(f'<div class="bubble {bubble_class}">{msg["content"]}</div>', unsafe_allow_html=True)

# --- DEFINITIVE UNIFIED INPUT FLOW ---
# In Streamlit, native inputs are best placed at the end to be standard.
# However, to meet the "one-bar" design, we group them closely.

def run_process(text=None, audio_bytes=None):
    # 1. Capture User Interaction
    user_entry = text if text else "🎤 [Voice Input]"
    st.session_state.messages.append({"role": "user", "content": user_entry})
    
    # 2. IA Call with history
    history = [{"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
    chat = model.start_chat(history=history or None)
    
    try:
        if audio_bytes:
            response = chat.send_message([{"mime_type": "audio/wav", "data": audio_bytes}, "Analyze this audio as the tutor in our roleplay scenario."])
        else:
            response = chat.send_message(text)
            
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_text)
    except Exception as e:
        data = {"feedback": "Error processing answer.", "suggestions": [], "pronunciation_score": 0, "response": response.text if 'response' in locals() else str(e)}

    # 3. TTS Generation
    audio_buffer = io.BytesIO()
    gTTS(text=data["response"], lang='en').write_to_fp(audio_buffer)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": data["response"],
        "feedback": data.get("feedback", ""),
        "suggestions": data.get("suggestions", []),
        "pronunciation_score": data.get("pronunciation_score", 0),
        "audio": audio_buffer.getvalue()
    })
    st.rerun()

# Layout of the "Unified" Bar at the bottom
st.write("---")
# Use a column layout that feels like a single bar
col_input, col_mic = st.columns([4, 1.2], gap="small")

with col_input:
    # This input is natively stuck to the bottom, but the columns above mimic the layout request.
    entry = st.chat_input("Mensagem...")
    if entry:
        run_process(text=entry)

with col_mic:
    # Integrated mic feeling
    mic_entry = st.audio_input("Record Voice", label_visibility="collapsed")
    if mic_entry:
        # Check to avoid multiple processing of same audio object
        if "last_v" not in st.session_state or st.session_state.last_v != mic_entry.name:
            st.session_state.last_v = mic_entry.name
            run_process(audio_bytes=mic_entry.read())
