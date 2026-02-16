import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
import io
import json
import time
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

# --- JAVASCRIPT DOM INJECTION (THE REAL FIX) ---
# This script moves the Audio Input INSIDE the Chat Input Container
# ensuring they always move together and align perfectly.
js_code = """
<script>
    function moveMic() {
        const mic = window.parent.document.querySelector('[data-testid="stAudioInput"]');
        const chatInput = window.parent.document.querySelector('.stChatInputContainer');
        
        if (mic && chatInput) {
            // Check if already moved
            if (!chatInput.contains(mic)) {
                chatInput.appendChild(mic);
                mic.style.position = 'absolute';
                mic.style.right = '15px';
                mic.style.bottom = '15px';
                mic.style.zIndex = '10002';
                mic.style.transform = 'scale(0.9)';
            }
        }
    }
    
    // Run repeatedly to catch re-renders
    setInterval(moveMic, 100);
</script>
"""
st.markdown(js_code, unsafe_allow_html=True)

# --- CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Dark Mode Global */
    .stApp {
        background-color: #0E0E10;
        color: white;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide top header decoration */
    header {visibility: hidden;}
    
    /* Chat Bubbles */
    .stChatMessage {
        background: transparent;
        padding: 5px 0;
    }
    
    .bubble {
        padding: 10px 15px;
        border-radius: 18px;
        font-size: 15px;
        line-height: 1.4;
        max-width: 85%;
    }
    
    .bubble-assistant {
        background: #1C1C1E;
        color: white;
        border-bottom-left-radius: 4px;
        border: 1px solid #333;
    }
    
    .bubble-user {
        background: #005C4B;
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    
    /* INPUT CONTAINER STYLING */
    /* We make the sidebar transparent so only the pill is visible */
    [data-testid="stChatInputContainer"] {
        background: transparent !important;
        padding-bottom: 20px !important;
    }
    
    /* THE PILL */
    [data-testid="stChatInput"] {
        background: #1C1C1E !important;
        border-radius: 30px !important;
        border: 1px solid #333 !important;
        color: white !important;
        padding-right: 50px !important; /* Space for Mic */
    }
    
    [data-testid="stChatInput"] textarea {
        color: white !important;
    }
    
    /* MIC BUTTON STYLE */
    [data-testid="stAudioInput"] button {
        background: transparent !important;
        border: none !important;
        color: #00A884 !important;
        padding: 0 !important;
    }
    
    /* Hide Avatars */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- API SETUP ---
def get_api_key():
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except: pass
    return os.getenv("GOOGLE_API_KEY")

api_key = get_api_key()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎓 English Pro")
    if not api_key:
        api_key = st.text_input("Gemini API Key", type="password")
        
    st.caption("AI Status")
    if api_key:
        genai.configure(api_key=api_key)
        # FORCE USE 2.0-FLASH as confirmed available
        target_model = "gemini-2.0-flash"
        st.success(f"🟢 Active: `{target_model}`")
    else:
        target_model = None
        st.error("🔴 No Key")

    scenario = st.selectbox("Context", ['General Chat', 'Job Interview', 'Coffee Shop'])
    if st.button("Reset"):
        st.session_state.messages = []
        st.rerun()

# --- LOGIC ---
if nav := st.session_state.get("messages", []):
    pass
else:
    st.session_state.messages = []

# Display
for msg in st.session_state.messages:
    role = msg["role"]
    bubble = "bubble-user" if role == "user" else "bubble-assistant"
    with st.chat_message(role):
        if role == "assistant" and msg.get("feedback"):
            st.markdown(f"<small style='color:#888'>💡 {msg['feedback']}</small>", unsafe_allow_html=True)
        st.markdown(f'<div class="bubble {bubble}">{msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")

# --- PROCESSING ---
def run_chat(txt=None, aud=None):
    user_cont = txt if txt else "🎤 [Audio]"
    st.session_state.messages.append({"role": "user", "content": user_content})
    
    try:
        model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction=f"Tutor Roleplay: {scenario}. APA Method. Return JSON with 'response', 'feedback', 'suggestions'."
        )
        chat = model.start_chat()
        
        if aud:
            response = chat.send_message([{"mime_type": "audio/wav", "data": aud}, "Analyze this audio."])
        else:
            response = chat.send_message(txt)
            
        try:
            data = json.loads(response.text.replace("```json","").replace("```","").strip())
        except:
            data = {"response": response.text, "feedback": "", "suggestions": []}
            
        try:
            buf = io.BytesIO()
            gTTS(text=data["response"], lang='en').write_to_fp(buf)
            audio = buf.getvalue()
        except:
            audio = None
            
        st.session_state.messages.append({
            "role": "assistant",
            "content": data["response"],
            "feedback": data.get("feedback"),
            "audio": audio
        })
        
    except Exception as e:
        err = str(e)
        if "429" in err:
            st.warning("⏳ Quota Exceeded (Free Tier). Please wait a moment.")
        else:
            st.error(f"⚠️ API Error: {err}")
            
    st.rerun()

# --- INPUTS ---
# 1. Chat Input (Bottom)
prompt = st.chat_input("Message...")
if prompt:
    run_chat(txt=prompt)

# 2. Audio Input (Hidden initially, moved by JS)
voice = st.audio_input("Mic", label_visibility="collapsed")
if voice:
    if "last_v" not in st.session_state or st.session_state.last_v != voice.name:
        st.session_state.last_v = voice.name
        run_chat(aud=voice.read())
