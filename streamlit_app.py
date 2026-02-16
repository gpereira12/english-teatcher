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
    page_title="English Tutor",
    page_icon="🎓",
    layout="wide" # Wider layout for better chat feel
)

# --- ESTILO PREMIUM (High-Contrast Apple + WhatsApp) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    .stApp {
        background-color: #FFFFFF !important; /* Pure White for High Contrast */
        background-image: none !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 1px solid #E9ECEF;
    }

    /* Chat Container */
    .chat-container {
        padding-bottom: 120px; /* Space for fixed input */
    }

    /* Bubble Styles */
    .bubble {
        padding: 12px 18px;
        border-radius: 18px;
        font-size: 16px;
        line-height: 1.4;
        max-width: 75%;
        margin-bottom: 8px;
        position: relative;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        display: inline-block;
    }

    .bubble-assistant {
        background-color: #F0F2F5; /* Soft Gray */
        color: #1C1E21;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
        border: 1px solid #E4E6EB;
    }

    .bubble-user {
        background-color: #007AFF; /* Apple Blue for better contrast than green on white */
        color: #FFFFFF;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        text-align: left;
    }

    /* WhatsApp Custom Bubble Alignment */
    .stChatMessage {
        background-color: transparent !important;
        display: flex !important;
        flex-direction: column !important;
    }

    /* Adjusting Streamlit internal padding */
    .stChatMessage [data-testid="stMarkdownContainer"] {
        width: 100%;
    }

    /* Feedback & Scores */
    .feedback-box {
        background: rgba(0, 0, 0, 0.05);
        border-left: 4px solid #007AFF;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-size: 0.9rem;
    }

    .badge {
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 8px;
        display: inline-block;
    }

    .badge-pronunciation { background-color: #34C759; color: white; }

    /* Bottom Dock Integration */
    .input-dock {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        background: #F0F2F5;
        padding: 10px 20px;
        border-radius: 50px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        z-index: 1000;
        border: 1px solid #E4E6EB;
    }

    /* Styling the native st.audio_input to look integrated */
    [data-testid="stAudioInput"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        width: auto !important;
    }

    /* Typography Overrides */
    h1, h2, h3 { color: #1C1E21; font-weight: 700; }
    
    /* Remove default Streamlit Chat Input if we were using it */
    /* st.chat_input { display: none !important; } */

    /* Custom Input Bar simulation */
    .unified-input {
        background: white;
        border-radius: 25px;
        border: 1px solid #E4E6EB;
        padding: 8px 15px;
        flex-grow: 1;
        margin-right: 10px;
        outline: none;
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

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🎓 English Tutor")
    st.caption("Strategic Learning with AI")
    
    if not api_key:
        api_key = st.text_input("Enter Gemini API Key:", type="password")
        if not api_key:
            st.warning("Locked. API Key required.")
            st.stop()
    
    st.divider()
    scenario = st.selectbox(
        "Current Scenario",
        options=['General Conversation', 'Job Interview', 'Ordering Food', 'Tech Meeting'],
        key="selected_scenario"
    )
    
    if st.button("Clear History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- GEMINI SETUP ---
if api_key:
    genai.configure(api_key=api_key)
    
    system_instruction = f"""
    You are a high-level English Tutor. Roleplay Scenario: {scenario}.
    
    CONSTRAINTS:
    1. Respond as the character in the situation.
    2. Provide correction (ADJUST) for any grammar/vocab slips.
    3. If user sends audio, analyze pronunciation and give a score (0-100).
    4. Suggest natural idioms/phrasings.
    
    OUTPUT FORMAT (ALWAYS JSON):
    {{
        "correction": "Grammar feedback if needed",
        "suggestions": ["Natural phrasing 1", "Natural phrasing 2"],
        "pronunciation_score": 0,
        "response": "The character response in the chat"
    }}
    """
    
    # Use full specific name to avoid NotFound issues
    model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash",
        system_instruction=system_instruction
    )

# --- SESSÃO ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CHAT UI ---
st.title("🎓 English Tutor")
st.caption(f"Practicing: {scenario}")

for msg in st.session_state.messages:
    role = msg["role"]
    bubble_class = "bubble-user" if role == "user" else "bubble-assistant"
    
    with st.chat_message(role):
        if role == "assistant":
            # Smart Components
            feedback_html = ""
            if msg.get("correction") or msg.get("pronunciation_score"):
                p_score = msg.get("pronunciation_score", 0)
                feedback_html = f"""
                <div class="feedback-box">
                    {f'<div class="badge badge-pronunciation">Pronunciation: {p_score}%</div><br>' if p_score > 0 else ''}
                    <b>💡 Correction:</b> {msg.get("correction", "Excellent!")}<br>
                    <b>✨ Suggestions:</b> {", ".join(msg.get("suggestions", []))}
                </div>
                """
            
            st.markdown(f'<div class="bubble {bubble_class}">{feedback_html}{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")
        else:
            st.markdown(f'<div class="bubble {bubble_class}">{msg["content"]}</div>', unsafe_allow_html=True)

# --- UNIFIED INPUT BAR (WhatsApp Style) ---
# Since Streamlit inputs at the bottom are hard to "merge" perfectly inside one HTML div,
# we use a clean column layout that mimics the unified feel.

st.markdown("<br><br><br><br>", unsafe_allow_html=True) # Cushion for bottom dock

# Container para os inputs
input_container = st.container()

def handle_response(user_input, audio_data=None):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": user_input if user_input else "🎤 [Voice Message]"})
    
    # 2. IA Call
    history = []
    for m in st.session_state.messages[:-1]:
        history.append({"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]})
    
    chat = model.start_chat(history=history or None)
    
    try:
        if audio_data:
            response = chat.send_message([{"mime_type": "audio/wav", "data": audio_data}, "Analyze my speaking and respond."])
        else:
            response = chat.send_message(user_input)
            
        res_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(res_text)
    except Exception as e:
        data = {"correction": "", "suggestions": [], "pronunciation_score": 0, "response": "Sorry, I had an error: " + str(e)}

    # 3. TTS
    audio_buffer = io.BytesIO()
    gTTS(text=data["response"], lang='en').write_to_fp(audio_buffer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": data["response"],
        "correction": data.get("correction", ""),
        "suggestions": data.get("suggestions", []),
        "pronunciation_score": data.get("pronunciation_score", 0),
        "audio": audio_buffer.getvalue()
    })
    st.rerun()

# Layout do Input na parte inferior
with st.container():
    st.write("---")
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Chat Input original do Streamlit é fixado no fundo por padrão.
        # Vamos usá-lo, mas customizar seu CSS para arredondar mais.
        text_input = st.chat_input("Type your message in English...")
        if text_input:
            handle_response(text_input)
            
    with col2:
        # Microphone integrated as much as possible
        audio_input = st.audio_input("Record")
        if audio_input:
            if "last_audio" not in st.session_state or st.session_state.last_audio != audio_input.name:
                st.session_state.last_audio = audio_input.name
                handle_response(None, audio_input.read())

# Overriding to make chat_input rounded
st.markdown("""
<style>
    [data-testid="stChatInput"] {
        border-radius: 30px !important;
        background-color: #F0F2F5 !important;
        border: 1px solid #E4E6EB !important;
    }
</style>
""", unsafe_allow_html=True)
