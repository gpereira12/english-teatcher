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
    page_title="English Tutor | Pro",
    page_icon="🎓",
    layout="wide"
)

# --- THEME: APPLE DARK PREMIUM (High Contrast) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* 1. Reset e Contraste Global */
    .stApp {
        background-color: #0E0E10 !important; /* Deep Dark */
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] {
        background-color: rgba(14, 14, 16, 0.8) !important;
        backdrop-filter: blur(20px);
    }

    /* 2. Sidebar Premium */
    [data-testid="stSidebar"] {
        background-color: #1C1C1E !important;
        border-right: 1px solid #2C2C2E;
    }
    
    .sidebar-content {
        color: #FFFFFF;
    }

    /* 3. Títulos e Textos (Fixed Visibility) */
    h1, h2, h3, p, span, label {
        color: #FFFFFF !important;
    }
    
    .stCaption {
        color: #8E8E93 !important; /* Apple Gray */
    }

    /* 4. Chat Bubbles (WhatsApp Style High-End) */
    .stChatMessage {
        background-color: transparent !important;
        padding: 0.8rem 0 !important;
    }

    .bubble {
        padding: 16px 20px;
        border-radius: 24px;
        font-size: 16px;
        line-height: 1.5;
        max-width: 80%;
        margin-bottom: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        position: relative;
    }

    .bubble-assistant {
        background: #1C1C1E;
        color: #FFFFFF;
        align-self: flex-start;
        border: 1px solid #2C2C2E;
        border-bottom-left-radius: 4px;
    }

    .bubble-user {
        background: linear-gradient(135deg, #007AFF 0%, #0056B3 100%);
        color: #FFFFFF;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        font-weight: 400;
    }

    /* 5. Feedback Card (Advanced UI) */
    .feedback-card {
        background: rgba(44, 44, 46, 0.8);
        border-radius: 16px;
        padding: 14px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .score-tag {
        background: #34C759;
        color: white;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 10px;
        display: inline-block;
    }

    /* 6. Unified Input Cockpit (Fixed at Bottom) */
    .input-wrapper {
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        width: 85%;
        max-width: 900px;
        display: flex;
        gap: 12px;
        z-index: 9999;
    }

    /* Custom Input overrides */
    [data-testid="stChatInput"] {
        border-radius: 30px !important;
        border: 1px solid #2C2C2E !important;
        background-color: #1C1C1E !important;
        color: white !important;
    }

    /* Hide standard chat elements to avoid mess */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- GERENCIAMENTO DE API KEY ---
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
    st.caption("AI-Powered Language Growth")
    
    if not api_key:
        api_key = st.text_input("Gemini API Key:", type="password")
        if not api_key:
            st.error("🔑 API Key Required to start.")
            st.stop()
    else:
        st.success("Tutor Ready")
    
    st.divider()
    scenario = st.selectbox(
        "Simulation Scenario",
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
    
    INSTRUCTIONS:
    1. Respond naturally as the character.
    2. Provide high-quality correction for any mistakes.
    3. If audio is sent, provide a Pronunciation Score (0-100%).
    
    JSON SCHEMA (STRICT):
    {{
        "feedback": "Grammar/Vocab help.",
        "suggestions": ["Natural alternative 1"],
        "pronunciation_score": 0,
        "response": "Character response."
    }}
    """
    model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash",
        system_instruction=system_instruction
    )

# --- CHAT ENGINE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Header
st.title("🎓 English Tutor Pro")
st.caption(f"Scenario: {scenario} • High-Contrast Mode Active")

# Display Messages
chat_area = st.container()
with chat_area:
    for msg in st.session_state.messages:
        role = msg["role"]
        bubble_type = "bubble-user" if role == "user" else "bubble-assistant"
        
        with st.chat_message(role):
            if role == "assistant":
                # Render Intelligence Data
                intel_html = ""
                if msg.get("feedback") or msg.get("pronunciation_score"):
                    score = msg.get("pronunciation_score", 0)
                    intel_html = f"""
                    <div class="feedback-card">
                        {f'<div class="score-tag">Speech: {score}%</div><br>' if score > 0 else ''}
                        <b>💡 Correction:</b> {msg.get("feedback", "Excellent work!")}<br>
                        <b>🌟 Suggestions:</b> {", ".join(msg.get("suggestions", []))}
                    </div>
                    """
                st.markdown(f'<div class="bubble {bubble_type}">{intel_html}{msg["content"]}</div>', unsafe_allow_html=True)
                if msg.get("audio"):
                    st.audio(msg["audio"], format="audio/mp3")
            else:
                st.markdown(f'<div class="bubble {bubble_type}">{msg["content"]}</div>', unsafe_allow_html=True)

# --- INTEGRATED INPUT COCKPIT ---
st.markdown("<div style='margin-bottom: 120px;'></div>", unsafe_allow_html=True)

def handle_chat_flow(text=None, audio_bytes=None):
    # 1. Clear session logic for input repeat prevention
    user_text = text if text else "🎤 Audio Message"
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    # 2. AI Call
    history = [{"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
    chat = model.start_chat(history=history or None)
    
    try:
        if audio_bytes:
            response = chat.send_message([{"mime_type": "audio/wav", "data": audio_bytes}, "Evaluate my speaking and continue the roleplay."])
        else:
            response = chat.send_message(text)
        
        raw = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
    except:
        data = {"feedback": "", "suggestions": [], "pronunciation_score": 0, "response": response.text if 'response' in locals() else "Connection issue. Try again."}

    # 3. TTS
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

# Layout do Cockpit
cols = st.columns([4, 1])
with cols[0]:
    user_txt = st.chat_input("Type your message...")
    if user_txt:
        handle_chat_flow(text=user_txt)
with cols[1]:
    # Custom Audio Input with waves and controls
    voice_input = st.audio_input("Voice Input", label_visibility="collapsed")
    if voice_input:
        if "audio_tag" not in st.session_state or st.session_state.audio_tag != voice_input.name:
            st.session_state.audio_tag = voice_input.name
            handle_chat_flow(audio_bytes=voice_input.read())
