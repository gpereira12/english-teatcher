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
js_code = """
<script>
    function moveMic() {
        const mic = window.parent.document.querySelector('[data-testid="stAudioInput"]');
        const chatInput = window.parent.document.querySelector('.stChatInputContainer');
        
        if (mic && chatInput) {
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
    setInterval(moveMic, 100);
</script>
"""
st.markdown(js_code, unsafe_allow_html=True)

# --- CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #0E0E10;
        color: white;
        font-family: 'Inter', sans-serif;
    }
    header {visibility: hidden;}
    
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
    
    [data-testid="stChatInputContainer"] {
        background: transparent !important;
        padding-bottom: 20px !important;
    }
    
    [data-testid="stChatInput"] {
        background: #1C1C1E !important;
        border-radius: 30px !important;
        border: 1px solid #333 !important;
        color: white !important;
        padding-right: 50px !important; 
    }
    
    [data-testid="stChatInput"] textarea {
        color: white !important;
    }
    
    [data-testid="stAudioInput"] button {
        background: transparent !important;
        border: none !important;
        color: #00A884 !important;
        padding: 0 !important;
    }
    
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

# --- MODEL ROTATION LOGIC ---
MODELS_TO_TRY = [
    "gemini-2.0-flash", 
    "gemini-1.5-flash", 
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest"
]

def get_chat_response(messages, context_prompt, audio_data=None):
    """
    Tries to get a response from the API, rotating through models if 429/404 occurs.
    """
    last_error = None
    
    if not api_key:
        return {"response": "Please provide an API Key in the sidebar.", "error": True}

    genai.configure(api_key=api_key)

    for model_name in MODELS_TO_TRY:
        try:
            # Create Model
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=context_prompt
            )
            
            chat = model.start_chat(history=[]) # Stateless for simplicity in this fallback logic
            
            # Send Message
            if audio_data:
                response = chat.send_message([{"mime_type": "audio/wav", "data": audio_data}, "Analyze this audio."])
            else:
                # Use only the last user message for stateless retry, or rebuild history if needed.
                # For robustness, we send just the prompt here in rotation.
                user_msg = messages[-1]["content"]
                response = chat.send_message(user_msg)
            
            # If successful, return data
            return {
                "text": response.text, 
                "model_used": model_name,
                "error": False
            }
            
        except Exception as e:
            err_str = str(e)
            print(f"❌ Failed with {model_name}: {err_str}")
            last_error = err_str
            # If it's a 429 (Quota) or 404 (Not Found), we continue loop.
            # If it's something else, we might still want to try others.
            continue
            
    return {"response": f"All models failed. Last error: {last_error}", "error": True}


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎓 English Pro")
    if not api_key:
        api_key = st.text_input("Gemini API Key", type="password")
        
    st.caption("AI Status")
    if api_key:
        st.success(f"🟢 System Online")
    else:
        st.error("🔴 No Key")

    scenario = st.selectbox("Context", ['General Chat', 'Job Interview', 'Coffee Shop'])
    if st.button("Reset"):
        st.session_state.messages = []
        st.rerun()

# --- LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display
for msg in st.session_state.messages:
    role = msg["role"]
    bubble = "bubble-user" if role == "user" else "bubble-assistant"
    with st.chat_message(role):
        if role == "assistant" and msg.get("feedback"):
            st.markdown(f"<small style='color:#888'>💡 {msg['feedback']}</small>", unsafe_allow_html=True)
            if msg.get("model_used"):
                 st.markdown(f"<small style='color:#444; font-size: 0.7em'>🤖 {msg['model_used']}</small>", unsafe_allow_html=True)
        
        st.markdown(f'<div class="bubble {bubble}">{msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")

# --- PROCESSING ---
def run_chat(txt=None, aud=None):
    user_cont = txt if txt else "🎤 [Audio]"
    st.session_state.messages.append({"role": "user", "content": user_cont})
    
    # Context Prompt
    sys_prompt = f"Tutor Roleplay: {scenario}. APA Method. Return JSON with 'response', 'feedback', 'suggestions'."

    with st.spinner("Thinking..."):
        result = get_chat_response(st.session_state.messages, sys_prompt, aud)
    
    if result.get("error"):
        st.error(result["response"])
        return

    raw_text = result["text"]
    model_used = result["model_used"]

    # Parse JSON
    try:
        data = json.loads(raw_text.replace("```json","").replace("```","").strip())
    except:
        data = {"response": raw_text, "feedback": "", "suggestions": []}
        
    # TTS
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
        "audio": audio,
        "model_used": model_used
    })
    
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
