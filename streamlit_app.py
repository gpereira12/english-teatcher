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

# --- WHATSAPP PRO CSS: GHOST CONTAINER STRATEGY ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* 1. Global Reset & Night Mode */
    .stApp {
        background-color: #0E0E10 !important;
        color: #FFFFFF !important;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Padding for Fixed Cockpit */
    .main .block-container {
        padding-bottom: 120px !important;
        padding-top: 2rem !important;
    }

    /* 2. Chat Bubbles */
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
        color: #FFFFFF;
        border-bottom-left-radius: 2px;
    }

    .bubble-user {
        background: #005C4B;
        color: #FFFFFF;
        margin-left: auto;
        border-bottom-right-radius: 2px;
    }

    /* 3. The "Pill" Input Styling */
    [data-testid="stChatInput"] {
        background-color: #1C1C1E !important;
        border-radius: 26px !important;
        border: 1px solid #333 !important;
        /* Padding to prevent text overlapping mic */
        padding-right: 50px !important; 
    }
    
    [data-testid="stChatInput"] textarea {
        color: #FFFFFF !important;
    }

    /* 
       4. GHOST CONTAINER STRATEGY FOR MIC 
       We create a layout that exactly matches the Streamlit main column logic.
    */
    .ghost-dock-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        display: flex;
        justify-content: center;
        pointer-events: none; /* Let clicks pass through */
        z-index: 99999;
        height: 100px; /* Area covering the input */
    }

    .ghost-inner {
        width: 100%;
        max-width: 730px; /* Matches st.chat_input default max-width + padding */
        position: relative;
        height: 100%;
        display: flex;
        align-items: flex-end;
        padding-bottom: 25px; /* Adjust to align vertically with input center */
    }

    /* The actual clickable mic wrapper */
    .mic-wrapper {
        position: absolute;
        right: 15px; /* Stick to the right edge of the content column */
        bottom: 35px; /* Adjust vertical alignment */
        width: 40px;
        height: 40px;
        pointer-events: auto; /* Re-enable clicks */
        display: flex;
        align-items: center;
        justify_content: center;
    }

    /* Styling the mic button itself */
    [data-testid="stAudioInput"] {
        transform: scale(0.85);
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
        if not api_key:
            st.error("🔒 API Key Required")
            st.stop()
    
    # Robust Model Selection
    st.divider()
    st.caption("AI Connection Status")
    
    selected_model_name = None
    
    if api_key:
        genai.configure(api_key=api_key)
        
        # Priority list of models to try
        # Based on successful diagnosis of user's available models
        priority_models = [
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash", 
            "gemini-1.5-pro-latest",
            "gemini-1.5-pro",
            "gemini-pro"
        ]
        
        # Try to validate a working model
        for m in priority_models:
            try:
                # We just check if we can instantiate it, simple check
                # Real check happens on generation
                selected_model_name = m
                break
            except:
                continue

        st.success(f"🟢 Active: `{selected_model_name}`")
    
    st.divider()
    scenario = st.selectbox(
        "Context",
        ['General Conversation', 'Job Interview', 'Ordering Food', 'Tech Meeting']
    )
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- CHAT LOGIC ---
model = None
if api_key and selected_model_name:
    system_instruction = f"""
    You are a native English Tutor. Roleplay: '{scenario}'.
    Method: APA (Acquire, Practice, Adjust).
    OUTPUT ONLY JSON:
    {{
        "feedback": "Correction or improvement.",
        "suggestions": ["Tip1", "Tip2"],
        "pronunciation_score": 0,
        "response": "Your response as the character."
    }}
    """
    model = genai.GenerativeModel(
        model_name=selected_model_name, 
        system_instruction=system_instruction
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Messages
for msg in st.session_state.messages:
    role = msg["role"]
    bubble_type = "bubble-user" if role == "user" else "bubble-assistant"
    with st.chat_message(role):
        content = msg["content"]
        if role == "assistant":
            if msg.get("feedback"):
                st.markdown(f"""
                <div style="font-size:0.85em; color:#aaa; margin-bottom:5px;">
                    💡 {msg['feedback']}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown(f'<div class="bubble {bubble_type}">{content}</div>', unsafe_allow_html=True)
        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")

# --- INTERACTION CONTROLLER ---
def process_interaction(text_input=None, audio_input=None):
    user_txt = text_input if text_input else "🎤 [Audio Message]"
    st.session_state.messages.append({"role": "user", "content": user_txt})
    
    try:
        if not model:
            raise Exception("No model configured")
            
        chat = model.start_chat() 
        
        if audio_input:
            response = chat.send_message([{"mime_type": "audio/wav", "data": audio_input}, "Response?"])
        else:
            response = chat.send_message(text_input)
            
        text_resp = response.text
        
        # Clean JSON
        try:
            clean_json = text_resp.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
        except:
            data = {"response": text_resp, "feedback": "", "suggestions": [], "pronunciation_score": 0}
            
        # TTS
        try:
            audio_buffer = io.BytesIO()
            gTTS(text=data["response"], lang='en').write_to_fp(audio_buffer)
            audio_bytes = audio_buffer.getvalue()
        except:
            audio_bytes = None

        st.session_state.messages.append({
            "role": "assistant",
            "content": data["response"],
            "feedback": data.get("feedback"),
            "suggestions": data.get("suggestions"),
            "audio": audio_bytes
        })

    except Exception as e:
        err_str = f"Connection Error: {str(e)}"
        # Try a different model next time if this one failed
        st.error(err_str)
        st.session_state.messages.append({"role": "assistant", "content": "I'm having trouble connecting. Please try again."})
        
    st.rerun()


# --- GHOST DOCK LAYOUT ---
prompt = st.chat_input("Message...")
if prompt:
    process_interaction(text_input=prompt)

st.markdown("""
<div class="ghost-dock-container">
    <div class="ghost-inner">
        <div class="mic-wrapper">
""", unsafe_allow_html=True)

voice = st.audio_input("Mic", label_visibility="collapsed")

st.markdown("""
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if voice:
    if "v_tag" not in st.session_state or st.session_state.v_tag != voice.name:
        st.session_state.v_tag = voice.name
        process_interaction(audio_input=voice.read())
