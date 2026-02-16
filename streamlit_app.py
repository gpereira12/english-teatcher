import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
import io
import json
import traceback
from dotenv import load_dotenv

# Load local .env if exists
load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="English Tutor Pro",
    page_icon="🎓",
    layout="centered"
)

# --- WHATSAPP PRO CSS: BOTTOM DOCK ANCHOR ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Reset */
    .stApp {
        background-color: #0E0E10 !important;
        color: #FFFFFF !important;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Padding for Fixed Dock */
    .main .block-container {
        padding-bottom: 120px !important;
    }

    /* Chat Bubbles */
    .stChatMessage {
        background-color: transparent !important;
        padding: 5px 0 !important;
    }

    .bubble {
        padding: 10px 16px;
        border-radius: 16px;
        font-size: 15px;
        line-height: 1.4;
        max-width: 80%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    .bubble-assistant {
        background: #1C1C1E;
        color: white;
        border-bottom-left-radius: 2px;
    }

    .bubble-user {
        background: #005C4B;
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 2px;
    }

    /* Input Pill */
    [data-testid="stChatInput"] {
        background-color: #1C1C1E !important;
        border-radius: 26px !important;
        border: 1px solid #333 !important;
        padding-right: 50px !important; 
    }
    
    [data-testid="stChatInput"] textarea {
        color: white !important;
    }

    /* 
       ANCHORED MIC DOCK 
       Position: Fixed at bottom of Viewport (0px).
       Width: 100% to match screen.
       Flexbox: Center content to match chat input.
       Z-Index: High to sit on top.
    */
    .mic-anchor-dock {
        position: fixed;
        bottom: 20px; /* Aligned with standard st.chat_input bottom margin */
        left: 0;
        width: 100%;
        height: 0; /* Don't block clicks elsewhere */
        display: flex;
        justify-content: center; /* Center horizontally */
        z-index: 999999;
        pointer-events: none; /* Let clicks pass */
    }

    .mic-inner-wrapper {
        width: 700px; /* Approximate max-width of chat input */
        max-width: 95%; /* Responsive safety */
        position: relative;
        height: 0;
    }

    .mic-button-container {
        position: absolute;
        right: 10px; /* 10px from right edge of the input pill */
        bottom: 12px; /* Push up from the very bottom to align with text center */
        width: 40px;
        height: 40px;
        pointer-events: auto; /* Enable mic click */
        display: flex;
        align-items: center;
        justify_content: center;
    }

    /* Mic Button Style */
    [data-testid="stAudioInput"] {
        transform: scale(0.9);
    }
    [data-testid="stAudioInput"] button {
        background: transparent !important;
        border: none !important;
        color: #00A884 !important;
    }
    
    /* Hide Avatars */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- API KEY & MODEL MANAGEMENT ---
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
    
    if not api_key:
        api_key = st.text_input("Gemini API Key:", type="password")
    
    st.divider()
    
    model = None
    if api_key:
        genai.configure(api_key=api_key)
        
        # AGGRESSIVE MODEL DISCOVERY
        # 1. Try list of known stable models
        candidates = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash-001",
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "gemini-pro",
            "gemini-1.0-pro"
        ]
        
        active_model = None
        
        # Try to find one that works by instantiating
        for m in candidates:
            try:
                # Just define it, don't generate yet (lazy check)
                model = genai.GenerativeModel(m)
                active_model = m
                break
            except:
                continue
        
        if active_model:
            st.success(f"🟢 Connected: `{active_model}`")
        else:
            st.error("🔴 No compatible Gemini model found.")
    
    st.divider()
    scenario = st.selectbox("Context", ['General Conversation', 'Job Interview', 'Ordering Food'])

    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Messages
for msg in st.session_state.messages:
    role = msg["role"]
    bubble = "bubble-user" if role == "user" else "bubble-assistant"
    with st.chat_message(role):
        if role == "assistant" and msg.get("feedback"):
             st.markdown(f"<small style='color:#ccc'>💡 {msg['feedback']}</small>", unsafe_allow_html=True)
        st.markdown(f'<div class="bubble {bubble}">{msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")

# --- INTERACTION ---
def process(txt=None, aud=None):
    user_content = txt if txt else "🎤 [Audio]"
    st.session_state.messages.append({"role": "user", "content": user_content})
    
    try:
        if not model:
            raise Exception("Model not initialized. Check API Key.")

        # Prepare Chat
        chat = model.start_chat()
        
        # Send
        if aud:
            response = chat.send_message([{"mime_type": "audio/wav", "data": aud}, "Analyze pronunciation."])
        else:
            response = chat.send_message(txt)
            
        # Parse JSON
        try:
            clean = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
        except:
            data = {"response": response.text, "feedback": "", "suggestions": []}
            
        # TTS
        try:
            buf = io.BytesIO()
            gTTS(text=data["response"], lang='en').write_to_fp(buf)
            audio_bytes = buf.getvalue()
        except:
            audio_bytes = None

        st.session_state.messages.append({
            "role": "assistant",
            "content": data["response"],
            "feedback": data.get("feedback"),
            "audio": audio_bytes
        })

    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
        # Print FULL TRACEBACK to terminal for debugging
        print(traceback.format_exc())
    
    st.rerun()

# --- LAYOUT ANCHOR ---
prompt = st.chat_input("Message...")
if prompt:
    process(txt=prompt)

# DOCK ANCHOR (Outside form)
st.markdown("""
<div class="mic-anchor-dock">
    <div class="mic-inner-wrapper">
        <div class="mic-button-container">
""", unsafe_allow_html=True)
# MIC WIDGET
voice = st.audio_input("Mic", label_visibility="collapsed")
st.markdown("</div></div></div>", unsafe_allow_html=True)

if voice:
    if "v_tag" not in st.session_state or st.session_state.v_tag != voice.name:
        st.session_state.v_tag = voice.name
        process(aud=voice.read())
