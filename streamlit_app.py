import streamlit as st
import os
import io
import json
import time
import base64
from dotenv import load_dotenv

# Try to import new SDK, show error if missing
try:
    from google import genai
    from google.genai import types
except ImportError:
    st.error("❌ `google-genai` SDK not found. Please install: `pip install google-genai`")
    st.stop()
    
from gtts import gTTS

# Load local .env if exists
load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="English Tutor Pro",
    page_icon="🎓",
    layout="centered"
)

# --- JAVASCRIPT DOM INJECTION (MIC LAYOUT FIX) ---
st.markdown("""
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
""", unsafe_allow_html=True)

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

# --- MODEL CONFIGURATION ---
# Models to try in order of preference
CHAT_MODELS = [
    "gemini-3-flash-preview", 
    "gemini-2.0-flash-lite-preview-02-05", # Fast backup
    "gemini-2.0-flash", 
    "gemini-1.5-flash"
]

TTS_MODEL = "gemini-2.5-flash-preview-tts" # Specifically requested

def get_client():
    if not api_key: return None
    # Use v1beta for experimental models
    return genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})

client = get_client()

# --- HELPER FUNCTIONS ---
def generate_audio_native(text, voice_name="Kore"):
    """Uses Gemini 2.5 Flash TTS to generate high-quality audio."""
    try:
        if not client: return None
        
        response = client.models.generate_content(
            model=TTS_MODEL,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )
            )
        )
        # Handle Inline Data
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            if part.inline_data:
                return base64.b64decode(part.inline_data.data)
    except Exception as e:
        print(f"Native TTS Failed: {e}")
    return None # Fallback to gTTS will handle this

def get_chat_response(messages, system_inst, audio=None):
    """Robust chat generation iterating through available models."""
    if not client: return {"response": "No API Key", "error": True}

    last_error = None
    
    # Construct Content for New SDK
    # We transform history to standardized content list
    # Simple stateless for now to ensure reliability of 2.0/3.0
    user_msg = messages[-1]["content"] if not audio else "Analyze audio"
    
    # If using audio, we need 2.0+ models only
    content_payload = user_msg
    if audio:
        # Construct Part with Inline Data
        # We need to encode audio properly if passed as bytes
        # Simplified: Just text for now if fails, but standardizing
        pass

    for model_name in CHAT_MODELS:
        try:
            # Generate!
            # Note: New SDK uses `client.models.generate_content`
            response = client.models.generate_content(
                model=model_name,
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=system_inst,
                    response_mime_type="application/json"
                )
            )
            
            return {
                "text": response.text, 
                "model": model_name,
                "error": False
            }
        except Exception as e:
            err = str(e)
            print(f"Model {model_name} failed: {err}")
            last_error = err
            continue
            
    return {"response": f"All models failed. Last error: {last_error}", "error": True}


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎓 English Pro")
    if not api_key:
        api_key = st.text_input("Gemini API Key", type="password")
        
    st.caption("System Status")
    if api_key:
        st.success(f"🟢 Client: `google-genai` (New SDK)")
        st.info(f"⚡ Target: `{CHAT_MODELS[0]}`")
        st.info(f"🔊 TTS: `{TTS_MODEL}`")
    else:
        st.error("🔴 Offline")

    scenario = st.selectbox("Context", ['General Chat', 'Job Interview'])
    if st.button("Reset"):
        st.session_state.messages = []
        st.rerun()

# --- UI LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    role = msg["role"]
    bubble = "bubble-user" if role == "user" else "bubble-assistant"
    with st.chat_message(role):
        if role == "assistant" and msg.get("feedback"):
             st.markdown(f"<small style='color:#888'>💡 {msg['feedback']}</small>", unsafe_allow_html=True)
             if msg.get("model"):
                 st.markdown(f"<small style='color:#444; font-size: 0.7em'>🤖 {msg['model']}</small>", unsafe_allow_html=True)
        st.markdown(f'<div class="bubble {bubble}">{msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")

# --- EXECUTION ---
def run_chat(txt=None, aud=None):
    user_cont = txt if txt else "🎤 [Audio]"
    st.session_state.messages.append({"role": "user", "content": user_cont})
    
    sys_prompt = f"""
    You are an English Tutor. Roleplay: {scenario}. 
    Method: APA (Acquire, Practice, Adjust).
    JSON Schema: {{ "response": str, "feedback": str, "suggestions": [str] }}
    """
    
    with st.spinner("Thinking..."):
        result = get_chat_response(st.session_state.messages, sys_prompt, aud)
    
    if result.get("error"):
        st.error(result["response"])
        return
        
    raw = result["text"]
    model_used = result["model"]
    
    try:
        data = json.loads(raw)
    except:
        data = {"response": raw, "feedback": "", "suggestions": []}
        
    # AUDIO
    with st.spinner("Speaking..."):
        # Try Native First
        audio_bytes = generate_audio_native(data["response"])
        
        # Fallback to gTTS
        if not audio_bytes:
            print("Fallback to gTTS")
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
        "audio": audio_bytes,
        "model": model_used
    })
    st.rerun()

# --- INPUTS ---
prompt = st.chat_input("Message...")
if prompt:
    run_chat(txt=prompt)

voice = st.audio_input("Mic", label_visibility="collapsed")
if voice:
    if "last_v" not in st.session_state or st.session_state.last_v != voice.name:
        st.session_state.last_v = voice.name
        run_chat(aud=voice.read())
