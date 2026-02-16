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
    page_title="English Tutor | BeConfident",
    page_icon="🎓",
    layout="centered"
)

# --- ESTILO DESIGN PREMIUM (Apple Premium + WhatsApp Layout) ---
st.markdown("""
<style>
    /* Tipografia Apple */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'SF Pro Display', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Fundo Imersivo */
    .stApp {
        background-color: #F2F2F7; /* Apple Gray */
        background-image: radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
                          radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
                          radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        background-attachment: fixed;
    }

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.3);
    }

    /* Bolhas de Chat Premium */
    .stChatMessage {
        background-color: transparent !important;
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }

    .bubble {
        padding: 12px 18px;
        border-radius: 20px;
        font-size: 15px;
        line-height: 1.5;
        max-width: 85%;
        margin-bottom: 2px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        position: relative;
        transition: transform 0.2s ease;
    }

    .bubble:hover {
        transform: translateY(-1px);
    }

    /* WhatsApp Layout: Left (Assistant) */
    .bubble-assistant {
        background: rgba(255, 255, 255, 0.95);
        color: #1C1C1E;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
        border: 1px solid rgba(0,0,0,0.05);
    }

    /* WhatsApp Layout: Right (User) */
    .bubble-user {
        background: linear-gradient(135deg, #34C759 0%, #30B053 100%); /* Apple Green */
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }

    /* Blocos de Feedback (Adjust) */
    .feedback-card {
        background: rgba(0, 122, 255, 0.08); /* Apple Blue subtle */
        border-left: 3px solid #007AFF;
        padding: 12px;
        border-radius: 12px;
        margin-bottom: 12px;
        font-size: 0.9rem;
        color: #1C1C1E;
    }

    .score-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .score-high { background-color: #34C759; color: white; }
    .score-mid { background-color: #FF9500; color: white; }
    .score-low { background-color: #FF3B30; color: white; }

    /* Estilo do Título Header */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        color: white;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }

    /* Botão Reset Custom */
    .stButton>button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    /* Hidden Streamlit Elements */
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
    env_key = os.getenv("GOOGLE_API_KEY")
    return env_key if env_key else None

api_key = get_api_key()

with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/007AFF/university.png", width=60)
    st.title("English Tutor")
    st.caption("Elegance & Accuracy")
    
    if not api_key:
        user_key = st.text_input("Google API Key:", type="password")
        if user_key:
            api_key = user_key
        else:
            st.warning("Please provide an API Key.")
            st.stop()
    else:
        st.success("API Key Active")

    st.divider()
    
    scenario = st.selectbox(
        "Training Scenario",
        options=['General Conversation', 'Job Interview', 'Ordering Food', 'Tech Meeting'],
        index=0
    )
    
    if st.button("Reset Session", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- CONFIGURAÇÃO DO MODELO AI ---
if api_key:
    genai.configure(api_key=api_key)
    
    system_instruction = f"""
    You are a professional native English Tutor and roleplay partner in the scenario: '{scenario}'.
    
    METHODOLOGY: Acquire, Practice, Adjust (APA).
    
    GOAL: 
    1. Act as a character in the roleplay.
    2. Provide high-quality correction for every user interaction.
    3. Suggest better vocabulary/phrasings.
    4. If audio input is detected, estimate the 'Pronunciation Score' (0-100%).
    
    RESPONSE STRUCTURE (STRICT JSON):
    {{
        "feedback": "Grammar corrections and improvements.",
        "suggestions": ["Better alternative 1", "Better alternative 2"],
        "pronunciation_score": 85,
        "pronunciation_feedback": "Detailed feedback on pronunciation/flow (if audio was sent).",
        "response": "Your natural character response in English."
    }}
    
    Important: Always keep the conversation alive. The JSON must be valid.
    """
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )

# --- ESTADO DA SESSÃO ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HEADER ---
st.markdown('<div class="main-header"><h1>🎓 English Tutor</h1><p>Master English with AI Roleplay</p></div>', unsafe_allow_html=True)

# --- CHAT DISPLAY ---
for msg in st.session_state.messages:
    role = msg["role"]
    bubble_class = "bubble-user" if role == "user" else "bubble-assistant"
    
    with st.chat_message(role):
        if role == "assistant":
            # Bloco de Inteligência (Adjust)
            feedback_html = ""
            if msg.get("feedback") or msg.get("pronunciation_score"):
                p_score = msg.get("pronunciation_score", 0)
                score_class = "score-high" if p_score >= 80 else "score-mid" if p_score >= 50 else "score-low"
                
                feedback_html = f"""
                <div class="feedback-card">
                    {f'<div class="score-badge {score_class}">Pronunciation: {p_score}%</div>' if p_score > 0 else ''}
                    <b>🔍 Feedback:</b> {msg.get("feedback", "Everything looks great!")}<br>
                    {f'<b>💡 Suggestions:</b><br>• ' + '<br>• '.join(msg.get("suggestions", [])) if msg.get("suggestions") else ''}
                </div>
                """
            
            st.markdown(f'<div class="bubble {bubble_class}">{feedback_html}{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")
        else:
            st.markdown(f'<div class="bubble {bubble_class}">{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("type") == "audio":
                st.caption("🎤 Voice message sent")

# --- LÓGICA DE INPUT ---
st.divider()
c1, c2 = st.columns([3, 1])

with c1:
    prompt = st.chat_input("Enter your message...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt, "type": "text"})
        
        # IA Processing
        history = [{"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
        chat = model.start_chat(history=history or None)
        response = chat.send_message(prompt)
        
        try:
            res_json = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        except:
            res_json = {"feedback": "", "suggestions": [], "pronunciation_score": 0, "response": response.text}

        # TTS
        audio_buffer = io.BytesIO()
        gTTS(text=res_json["response"], lang='en', tld='com').write_to_fp(audio_buffer)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": res_json["response"],
            "feedback": res_json["feedback"],
            "suggestions": res_json.get("suggestions", []),
            "pronunciation_score": res_json.get("pronunciation_score", 0),
            "audio": audio_buffer.getvalue()
        })
        st.rerun()

with c2:
    audio_file = st.audio_input("Record Voice")
    if audio_file:
        if "last_audio_file" not in st.session_state or st.session_state.last_audio_file != audio_file.name:
            st.session_state.last_audio_file = audio_file.name
            
            audio_bytes = audio_file.read()
            st.session_state.messages.append({"role": "user", "content": "[Voice Message]", "type": "audio"})
            
            # IA Processing with Audio
            history = [{"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
            chat = model.start_chat(history=history or None)
            
            content = [{"mime_type": "audio/wav", "data": audio_bytes}, "Analyze my pronunciation and respond to the conversation."]
            response = chat.send_message(content)
            
            try:
                res_json = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            except:
                res_json = {"feedback": "", "suggestions": [], "pronunciation_score": 75, "response": response.text}

            # TTS
            audio_buffer = io.BytesIO()
            gTTS(text=res_json["response"], lang='en', tld='com').write_to_fp(audio_buffer)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": res_json["response"],
                "feedback": res_json["feedback"],
                "suggestions": res_json.get("suggestions", []),
                "pronunciation_score": res_json.get("pronunciation_score", 0),
                "audio": audio_buffer.getvalue()
            })
            st.rerun()
