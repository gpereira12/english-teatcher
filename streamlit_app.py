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

# --- DEFINITIVE DARK PRO CSS (The "One Cockpit" Design) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Reset */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }

    /* Fixed Input Dock Simulation */
    .main .block-container {
        padding-bottom: 200px !important;
    }

    /* Premium Bubbles */
    .stChatMessage {
        background-color: transparent !important;
    }

    .bubble {
        padding: 16px 22px;
        border-radius: 24px;
        font-size: 16px;
        line-height: 1.6;
        max-width: 82%;
        margin-bottom: 4px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
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
    }

    /* 
       INJECTION FOR UNIFIED ROUNDED DOCK 
    */
    /* Rounding the Chat Input Container 100% */
    [data-testid="stChatInput"] {
        border-radius: 80px !important;
        padding: 8px !important;
        background-color: #1C1C1E !important;
        border: 1px solid #2C2C2E !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important;
    }

    /* Hide standard avatar display to keep only bubbles */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }

    /* Custom Intelligence Cards in response */
    .intel-box {
        background: rgba(44, 44, 46, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 15px;
        margin-bottom: 12px;
    }
    
    .score-label {
        background: #34C759;
        color: black;
        font-weight: 900;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        text-transform: uppercase;
        margin-bottom: 10px;
        display: inline-block;
    }

    /* Sidebar Clean styling */
    [data-testid="stSidebar"] {
        background-color: #0E0E10 !important;
        border-right: 1px solid #2C2C2E;
    }

    p, span, div, h1, h2, h3, label {
        color: #FFFFFF !important;
    }

    .stCaption {
        color: #8E8E93 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- API & MODEL STABILITY ---
def get_api_key():
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except:
        pass
    return os.getenv("GOOGLE_API_KEY")

api_key = get_api_key()

with st.sidebar:
    st.markdown("### 🎓 English Pro")
    st.caption("Elegance in Acquisition")
    
    if not api_key:
        api_key = st.text_input("Gemini API Key:", type="password")
        if not api_key:
            st.error("🔑 Session Locked. API Key Missing.")
            st.stop()
    
    st.divider()
    scenario = st.selectbox(
        "Simulation Context",
        options=['General Conversation', 'Job Interview', 'Ordering Food', 'Tech Meeting'],
        key="context_key"
    )
    
    if st.button("Reset Session", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- MODEL CONFIGURATION (Fixed 404 Issue) ---
if api_key:
    genai.configure(api_key=api_key)
    
    system_instruction = f"""
    You are a professional British/American English Tutor. Context: '{scenario}'.
    Method: Acquire, Practice, Adjust (APA).
    
    RESPONSE RULES:
    1. Respond naturally as the roleplay character.
    2. Suggest vocabulary and grammar tips (ADJUST).
    3. If audio, give a 'Pronunciation Score' (binary 0-100%).
    4. MUST respond in STRICT JSON.
    
    JSON SCHEMA:
    {{
        "feedback": "Grammar/Vocab fix.",
        "suggestions": ["Natural tip 1", "Natural tip 2"],
        "pronunciation_score": 0,
        "response": "Character response for the chat."
    }}
    """
    # FIX: Use stable model string 'gemini-1.5-flash'
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )

# --- SESSION ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CHAT RENDERING ---
st.title("🎓 English Tutor Pro")
st.caption(f"Scenario: {scenario} • High-Contrast Night Active")

chat_viewport = st.container()
with chat_viewport:
    for msg in st.session_state.messages:
        role = msg["role"]
        bubble_css = "bubble-user" if role == "user" else "bubble-assistant"
        
        with st.chat_message(role):
            if role == "assistant":
                # Render AI Intelligence Data
                intel_block = ""
                if msg.get("feedback") or msg.get("score"):
                    score = msg.get("score", 0)
                    intel_block = f"""
                    <div class="intel-box">
                        {f'<div class="score-label">Speech Accuracy: {score}%</div><br>' if score > 0 else ''}
                        <b>💡 Correction:</b> {msg.get("feedback", "Your English is flawless!")}<br>
                        <b>🌟 Better Phrasing:</b> {", ".join(msg.get("suggestions", []))}
                    </div>
                    """
                st.markdown(f'<div class="bubble {bubble_css}">{intel_block}{msg["content"]}</div>', unsafe_allow_html=True)
                if msg.get("audio"):
                    st.audio(msg.get("audio"), format="audio/mp3")
            else:
                st.markdown(f'<div class="bubble {bubble_css}">{msg["content"]}</div>', unsafe_allow_html=True)

# --- THE UNIFIED COCKPIT (100% Rounding & Integrated Mic) ---
st.markdown("<div style='margin-bottom: 200px;'></div>", unsafe_allow_html=True)

def handle_exchange(prompt_text=None, audio_raw=None):
    # 1. Update State
    entry = prompt_text if prompt_text else "🎤 [Voice Message]"
    st.session_state.messages.append({"role": "user", "content": entry})
    
    # 2. IA Processing
    history = [{"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
    chat = model.start_chat(history=history or None)
    
    try:
        if audio_raw:
            response = chat.send_message([{"mime_type": "audio/wav", "data": audio_raw}, "Analyze my pronunciation and respond to the chat history."])
        else:
            response = chat.send_message(prompt_text)
            
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
    except Exception as e:
        data = {"feedback": "", "suggestions": [], "pronunciation_score": 0, "response": response.text if 'response' in locals() else "Service temporarily offline. Check API Key."}

    # 3. TTS
    buf = io.BytesIO()
    gTTS(text=data["response"], lang='en').write_to_fp(buf)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": data["response"],
        "feedback": data.get("feedback", ""),
        "suggestions": data.get("suggestions", []),
        "score": data.get("pronunciation_score", 0),
        "audio": buf.getvalue()
    })
    st.rerun()

# This is the "Dock"
with st.container():
    # Streamlit places chat_input at the very bottom. 
    # To place mic "inside" visually, we use a Column group just ABOVE it or next to it.
    # However, to meet the "inside the rounded input" requirement:
    
    dock_col1, dock_col2 = st.columns([1, 4])
    
    with dock_col1:
        # Microfone posicionado à esquerda conforme padrão de cockpit unificado
        m_input = st.audio_input("Mic", label_visibility="collapsed")
        if m_input:
            if "last_m" not in st.session_state or st.session_state.last_m != m_input.name:
                st.session_state.last_m = m_input.name
                handle_exchange(audio_raw=m_input.read())
                
    with dock_col2:
        t_input = st.chat_input("Mensagem...")
        if t_input:
            handle_exchange(prompt_text=t_input)

# Custom JS/CSS to force the mic and text input to align into one rounded pill at the bottom
st.markdown("""
<style>
    /* Force the streamlit fixed bottom bar to be transparent so our design shows */
    [data-testid="stChatInputContainer"] {
        background-color: transparent !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)
