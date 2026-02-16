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

# --- DEFINITIVE WHATSAPP UNIFIED COCKPIT CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* 1. Global Reset & Night Mode */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0.8) !important;
        backdrop-filter: blur(20px);
    }

    /* Padding for Fixed Cockpit */
    .main .block-container {
        padding-bottom: 200px !important;
    }

    /* 2. Chat Bubbles (High Fidelity) */
    .stChatMessage {
        background-color: transparent !important;
        padding-top: 4px !important;
        padding-bottom: 4px !important;
    }

    .bubble {
        padding: 14px 18px;
        border-radius: 18px;
        font-size: 16px;
        line-height: 1.5;
        max-width: 85%;
        margin-bottom: 2px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
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
        background: #005C4B; /* WhatsApp Dark Green but High Contrast */
        color: #FFFFFF;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }

    /* 3. The "One-Bar" WhatsApp Cockpit Simulation */
    /* We style the Chat Input to look like a Pill and integrate the Audio Input */
    
    [data-testid="stChatInputContainer"] {
        background-color: #202123 !important;
        border-radius: 50px !important; /* 100% Rounding */
        border: 1px solid #2C2C2E !important;
        padding: 8px 60px 8px 20px !important; /* Extra padding on right for Mic */
        box-shadow: 0 10px 40px rgba(0,0,0,0.5) !important;
        max-width: 800px !important;
        margin: 0 auto !important;
    }

    [data-testid="stChatInput"] {
        background-color: transparent !important;
        border: none !important;
    }

    /* Positioning the Audio Input INSIDE the right side of the pill area */
    .fixed-mic-container {
        position: fixed;
        bottom: 38px;
        right: calc(50% - 340px); /* Centered relative to the dock */
        z-index: 10001;
        width: 50px;
    }

    /* Adjusting the microphone widget to be stealthy until active */
    [data-testid="stAudioInput"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }

    [data-testid="stAudioInput"] button {
        background-color: transparent !important;
        border: none !important;
        color: #00A884 !important; /* WhatsApp Mic Color */
    }

    /* 4. Intelligence & Feedback */
    .feedback-pill {
        background: rgba(44, 44, 46, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 15px;
        font-size: 0.9rem;
    }

    .accuracy-tag {
        background: #00A884;
        color: white;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 8px;
        display: inline-block;
    }

    /* Sidebar Reset */
    [data-testid="stSidebar"] {
        background-color: #0B0B0C !important;
        border-right: 1px solid #2C2C2E;
    }

    /* Hidden elements */
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

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎓 English Pro")
    st.caption("Elegance & Accuracy")
    
    if not api_key:
        api_key = st.text_input("Gemini API Key:", type="password")
        if not api_key:
            st.error("🔑 Session Locked. API Key Required.")
            st.stop()
    
    st.divider()
    scenario = st.selectbox(
        "Current Scenario",
        options=['General Conversation', 'Job Interview', 'Ordering Food', 'Tech Meeting'],
        key="scenario_select"
    )
    
    if st.button("Clear History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- GEMINI STABLE CONFIG ---
if api_key:
    genai.configure(api_key=api_key)
    
    system_instruction = f"""
    You are a professional native English Tutor. Roleplay context: '{scenario}'.
    Method: APA (Acquire, Practice, Adjust).
    
    RULES:
    1. Respond naturally as the character.
    2. Suggest vocabulary and grammar tips (ADJUST).
    3. If audio is detected, give a 'Pronunciation Score' (0-100%).
    4. MUST respond in STRICT JSON.
    
    OUTPUT JSON FORMAT:
    {{
        "feedback": "Grammar/Vocab evaluation.",
        "suggestions": ["Natural tip 1", "Natural tip 2"],
        "pronunciation_score": 0,
        "response": "Character response."
    }}
    """
    # STABLE MODEL: gemini-1.5-flash (no prefix)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        system_instruction=system_instruction
    )

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CHAT DISPLAY ---
st.title("🎓 English Tutor Pro")
st.caption(f"Practicing: {scenario}")

for msg in st.session_state.messages:
    role = msg["role"]
    bubble_type = "bubble-user" if role == "user" else "bubble-assistant"
    
    with st.chat_message(role):
        if role == "assistant":
            # Intelligence Overlay
            intel_overlay = ""
            if msg.get("feedback") or msg.get("score"):
                p_score = msg.get("score", 0)
                intel_overlay = f"""
                <div class="feedback-pill">
                    {f'<div class="accuracy-tag">Pronunciation: {p_score}%</div><br>' if p_score > 0 else ''}
                    <b>💡 Adjust:</b> {msg.get("feedback", "Excellent phrasal usage!")}<br>
                    <b>🌟 Suggestions:</b> {", ".join(msg.get("suggestions", []))}
                </div>
                """
            st.markdown(f'<div class="bubble {bubble_type}">{intel_overlay}{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")
        else:
            st.markdown(f'<div class="bubble {bubble_type}">{msg["content"]}</div>', unsafe_allow_html=True)

# --- THE WHATSAPP DOCK (UNIFIED INPUT & VOICE) ---

def process_interaction(text_input=None, audio_input=None):
    # 1. Capture User Input
    user_txt = text_input if text_input else "🎤 [Voice Interaction]"
    st.session_state.messages.append({"role": "user", "content": user_txt})
    
    # 2. IA Processing
    history = [{"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
    chat = model.start_chat(history=history or None)
    
    try:
        if audio_input:
            response = chat.send_message([{"mime_type": "audio/wav", "data": audio_input}, "Analyze this audio as the tutor."])
        else:
            response = chat.send_message(text_input)
            
        json_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        json_data = {"feedback": "", "suggestions": [], "pronunciation_score": 0, "response": response.text if 'response' in locals() else "Service error. Please try again."}

    # 3. TTS Generation
    audio_buffer = io.BytesIO()
    gTTS(text=json_data["response"], lang='en').write_to_fp(audio_buffer)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": json_data["response"],
        "feedback": json_data.get("feedback", ""),
        "suggestions": json_data.get("suggestions", []),
        "score": json_data.get("pronunciation_score", 0),
        "audio": audio_buffer.getvalue()
    })
    st.rerun()

# This is the "Dock" Container
st.markdown("<br><br><br>", unsafe_allow_html=True)

with st.container():
    # Native Chat Input - We've styled it to be a 100% rounded Pill
    prompt = st.chat_input("Mensagem...")
    if prompt:
        process_interaction(text_input=prompt)

    # Invisible Container for the Mic, positioned ABSOLUTELY INSIDE the pill on the right
    st.markdown('<div class="fixed-mic-container">', unsafe_allow_html=True)
    voice_file = st.audio_input("Recorder", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if voice_file:
        if "v_tag" not in st.session_state or st.session_state.v_tag != voice_file.name:
            st.session_state.v_tag = voice_file.name
            process_interaction(audio_input=voice_file.read())

# Final CSS adjustment to hide the original chat container background so our "Dock" looks unified
st.markdown("""
<style>
    [data-testid="stChatInputContainer"] {
        padding-top: 0 !important;
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)
