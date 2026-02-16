import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
import io
import json
import traceback # Added for debugging
from dotenv import load_dotenv

# Load local .env if exists
load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="English Tutor Pro",
    page_icon="🎓",
    layout="centered"
)

# --- WHATSAPP PRO CSS: ULTIMATE INTEGRATION ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* 1. Global Reset & Night Mode */
    .stApp {
        background-color: #0E0E10 !important; /* Pure Dark Gray */
        color: #FFFFFF !important;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    [data-testid="stHeader"] {
        background-color: rgba(14,14,16,0.8) !important;
        backdrop-filter: blur(20px);
    }

    /* Padding for Fixed Cockpit */
    .main .block-container {
        padding-bottom: 220px !important;
    }

    /* 2. Chat Bubbles */
    .stChatMessage {
        background-color: transparent !important;
        padding-top: 5px !important;
        padding-bottom: 5px !important;
    }

    .bubble {
        padding: 12px 16px;
        border-radius: 18px;
        font-size: 15px;
        line-height: 1.5;
        max-width: 85%;
        margin-bottom: 4px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
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
        background: #005C4B; /* WhatsApp Green */
        color: #FFFFFF;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }

    /* 3. The "One-Bar" WhatsApp Cockpit Simulation */
    
    /* This targets the container of the chat input */
    [data-testid="stChatInputContainer"] {
        background-color: transparent !important; /* Make container transparent so we see the input only */
        padding-bottom: 20px !important;
        /* We force specific styling on the INNER elements */
    }

    /* Target the text area wrapper (the pill) */
    [data-testid="stChatInput"] {
        background-color: #1C1C1E !important;
        border-radius: 40px !important; /* 100% Rounding */
        border: 1px solid #3A3A3C !important;
        padding-right: 60px !important; /* Space for mic */
    }
    
    /* Target the text area itself */
    [data-testid="stChatInput"] textarea {
        color: white !important;
        caret-color: #00A884 !important;
    }

    /* 
       4. ABSOLUTE MICROPHONE POSITIONING 
       This is the key hack. We position the separate audio_input container ON TOP of the chat input
    */
    .fixed-mic-wrapper {
        position: fixed;
        bottom: 30px; /* Adjust based on chat_input heigth */
        left: 50%;
        transform: translateX(260px); /* Move 260px to the right from center */
        z-index: 99999;
        width: 45px;
        height: 45px;
        display: flex;
        align-items: center;
        justify_content: center;
        pointer-events: auto; /* Ensure clickable */
    }
    
    /* On mobile/smaller screens, adjust slightly */
    @media (max-width: 700px) {
        .fixed-mic-wrapper {
            transform: translateX(35vw); /* Responsive positioning */
        }
    }

    /* Style the audio button to look like an icon inside */
    [data-testid="stAudioInput"] {
        transform: scale(0.9);
    }
    
    [data-testid="stAudioInput"] button {
        background-color: transparent !important;
        border: none !important;
        color: #8E8E93 !important; /* Disabled gray */
    }
    
    [data-testid="stAudioInput"] button:hover {
        color: #00A884 !important; /* WhatsApp Green hover */
    }
    
    /* Feedback Box */
    .feedback-box {
        background: rgba(44, 44, 46, 0.5);
        border: 1px solid #3A3A3C;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 10px;
        font-size: 0.9em;
    }
    
    .accuracy {
        color: #30D158;
        font-weight: bold;
    }

    /* Hide standard elements */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }
    
    /* Hide top padding */
    .block-container {
        padding-top: 2rem !important;
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
            st.error("🔑 API Key Required.")
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
    You are a native English Tutor. Roleplay context: '{scenario}'.
    Method: APA (Acquire, Practice, Adjust).
    
    RULES:
    1. Respond naturally as the character.
    2. Suggest vocabulary and grammar tips (ADJUST).
    3. If audio, give a 'Pronunciation Score' (0-100%).
    4. MUST respond in STRICT JSON.
    
    OUTPUT JSON FORMAT:
    {{
        "feedback": "Correction.",
        "suggestions": ["Tip 1"],
        "pronunciation_score": 0,
        "response": "Character response."
    }}
    """
    # Use standard stable model name
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", 
            system_instruction=system_instruction
        )
    except Exception as e:
        st.error(f"Error configuring model: {e}")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CHAT DISPLAY ---
st.title("🎓 English Tutor Pro")

# Container for chat messages so they scroll above the fixed bar
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        role = msg["role"]
        bubble_type = "bubble-user" if role == "user" else "bubble-assistant"
        
        with st.chat_message(role):
            if role == "assistant":
                # Intelligence
                intel = ""
                if msg.get("feedback") or msg.get("score"):
                    score = msg.get("score", 0)
                    intel = f"""
                    <div class="feedback-box">
                        {f'<span class="accuracy">Speech: {score}%</span><br>' if score > 0 else ''}
                        <b>💡 Fix:</b> {msg.get("feedback", "Good!")}<br>
                        <b>🌟 Tip:</b> {", ".join(msg.get("suggestions", []))}
                    </div>
                    """
                st.markdown(f'<div class="bubble {bubble_type}">{intel}{msg["content"]}</div>', unsafe_allow_html=True)
                if msg.get("audio"):
                    st.audio(msg["audio"], format="audio/mp3")
            else:
                st.markdown(f'<div class="bubble {bubble_type}">{msg["content"]}</div>', unsafe_allow_html=True)

# --- THE WHATSAPP DOCK (UNIFIED INPUT & VOICE) ---

def process_interaction(text_input=None, audio_input=None):
    # 1. Capture User Input
    user_txt = text_input if text_input else "🎤 [Voice Message]"
    st.session_state.messages.append({"role": "user", "content": user_txt})
    
    # 2. IA Processing
    history = [{"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
    
    try:
        chat = model.start_chat(history=history or None)
        
        if audio_input:
            response = chat.send_message([{"mime_type": "audio/wav", "data": audio_input}, "Analyze pronunciation."])
        else:
            response = chat.send_message(text_input)
            
        json_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        # Catch and display exact error
        err_msg = f"API Error: {str(e)}"
        print(traceback.format_exc()) # Log to console
        json_data = {"feedback": "System Error", "suggestions": [], "pronunciation_score": 0, "response": err_msg}

    # 3. TTS Generation
    try:
        audio_buffer = io.BytesIO()
        gTTS(text=json_data["response"], lang='en').write_to_fp(audio_buffer)
        audio_data = audio_buffer.getvalue()
    except:
        audio_data = None
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": json_data["response"],
        "feedback": json_data.get("feedback", ""),
        "suggestions": json_data.get("suggestions", []),
        "score": json_data.get("pronunciation_score", 0),
        "audio": audio_data
    })
    st.rerun()

# --- LAYOUT HACK ---
# 1. Standard Chat Input (Fixed at bottom)
prompt = st.chat_input("Message...")
if prompt:
    process_interaction(text_input=prompt)

# 2. Absolute Mic Button (Inside the input area)
# We use a container that stays fixed relative to viewport
st.markdown('<div class="fixed-mic-wrapper">', unsafe_allow_html=True)
voice_file = st.audio_input("Voice", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

if voice_file:
    if "v_tag" not in st.session_state or st.session_state.v_tag != voice_file.name:
        st.session_state.v_tag = voice_file.name
        process_interaction(audio_input=voice_file.read())
