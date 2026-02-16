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
    layout="centered"
)

# --- ESTILO CUSTOMIZADO (WhatsApp / Premium Aesthetic) ---
st.markdown("""
<style>
    /* Estilo do Fundo (WhatsApp-like subtle pattern) */
    .stApp {
        background-color: #e5ddd5;
        background-image: url("https://www.transparenttextures.com/patterns/cubes.png");
    }
    
    /* Remover bordas e backgrounds padrão do Streamlit chat */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 0.5rem 0 !important;
        border: none !important;
    }
    
    /* Container da Bolha de Chat */
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 12px;
        max-width: 80%;
        margin-bottom: 5px;
        position: relative;
        box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
        font-family: 'Inter', sans-serif;
    }
    
    /* Bolha da IA (Esquerda) */
    .bubble-assistant {
        background-color: #ffffff;
        color: #000000;
        align-self: flex-start;
        border-top-left-radius: 0;
    }
    
    /* Bolha do Usuário (Direita) */
    .bubble-user {
        background-color: #dcf8c6;
        color: #000000;
        margin-left: auto;
        border-top-right-radius: 0;
    }

    /* Ocultar avatares padrão para customizar se necessário */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }

    /* Ajustar layout do input */
    .stChatInputContainer {
        padding-bottom: 2rem;
    }

    /* Estilo do Bloco de Feedback */
    .feedback-container {
        font-size: 0.85rem;
        background-color: #f0f4ff;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        border-left: 4px solid #34b7f1;
    }

    /* Customizar Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
    }

    /* Ajustar títulos */
    h1, h2, h3 {
        color: #075e54;
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
    if env_key:
        return env_key
    
    return None

api_key = get_api_key()

with st.sidebar:
    st.title("⚙️ English Tutor")
    st.caption("Settings & Scenario")
    
    if not api_key:
        user_key = st.text_input("Insira sua Google API Key:", type="password")
        if user_key:
            api_key = user_key
        else:
            st.warning("⚠️ Forneça uma API Key para continuar.")
            st.stop()
    else:
        st.success("✅ API Key configurada.")

    st.divider()
    
    scenario = st.selectbox(
        "Escolha o Cenário",
        options=['General Conversation', 'Job Interview', 'Ordering Food', 'Tech Meeting'],
        index=0
    )
    
    st.divider()
    
    if st.button("Resetar Conversa", type="primary"):
        st.session_state.messages = []
        st.rerun()

# --- CONFIGURAÇÃO DO MODELO AI ---
if api_key:
    genai.configure(api_key=api_key)
    
    system_instruction = f"""
    You are a professional native English Tutor and roleplay partner in the scenario: '{scenario}'.
    
    YOUR GOAL:
    Help the student learn English through the 'Acquire, Practice, Adjust' method.
    
    THE FLOW:
    1. If the user makes a mistake (grammar, vocabulary, or phrasing), you MUST provide a friendly 'Adjust' (feedback).
    2. Then, you MUST provide a natural 'Practice' response as the character in the roleplay to keep the conversation going.
    
    RESPONSE FORMAT:
    You MUST respond with a JSON object containing two keys:
    {{
        "feedback": "Your correction or grammar improvement here. If perfect, a short praise like 'Great sentence!'.",
        "response": "Your natural conversation response as the character in the roleplay."
    }}
    
    Keep the roleplay engaging and contextually appropriate.
    """
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )

# --- ESTADO DA SESSÃO ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HEADER ---
st.title("🎓 English Tutor")
st.caption(f"Currently in: **{scenario}**")

# --- RENDERIZAÇÃO DAS MENSAGENS (WhatsApp Style) ---
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        role = msg["role"]
        class_name = "bubble-user" if role == "user" else "bubble-assistant"
        
        with st.chat_message(role):
            # Usando HTML customizado para as bolhas dentro do st.chat_message
            if role == "assistant":
                st.markdown(f"""
                <div class="chat-bubble {class_name}">
                    {f'<div class="feedback-container"><b>🔍 Feedback:</b><br>{msg.get("feedback", "")}</div>' if msg.get("feedback") else ''}
                    {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
                
                if msg.get("audio"):
                    st.audio(msg["audio"], format="audio/mp3")
            else:
                st.markdown(f"""
                <div class="chat-bubble {class_name}">
                    {msg["content"]}
                    {f'<br><i>🎤 Audio message sent</i>' if msg.get("type") == "audio" else ''}
                </div>
                """, unsafe_allow_html=True)

# --- PROCESSAMENTO ---
def process_message(prompt_text, audio_file=None):
    current_msg = {
        "role": "user", 
        "content": prompt_text if prompt_text else "",
        "type": "audio" if audio_file else "text"
    }
    st.session_state.messages.append(current_msg)
    st.rerun()

# Lógica para gerar resposta do modelo APÓS o rerun do usuário para manter ordem visual
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]
    
    with st.chat_message("assistant"):
        with st.spinner("Typing..."):
            try:
                # Obter prompt real (se for áudio, precisamos que o modelo lide)
                content = []
                if last_user_msg["content"]:
                    content.append(last_user_msg["content"])
                
                # A lógica de áudio aqui é simplificada: se mandou áudio, Gemini 1.5 Flash 
                # pode receber o áudio Bytes se enviarmos na lista
                # Mas aqui na sessão, não guardamos o áudio original por performance.
                # Se for o primeiro processamento, o audio_file estaria disponível em process_message.
                # Vou injetar a lógica de processamento aqui.
                pass
            except:
                pass

# --- INPUTS ---
st.divider()
input_col1, input_col2 = st.columns([2, 1])

with input_col1:
    prompt = st.chat_input("Mensagem...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt, "type": "text"})
        
        # Gerar resposta imediatamente para simplificar fluxo
        history = []
        for m in st.session_state.messages[:-1]:
            role = m["role"] if m["role"] != "assistant" else "model"
            history.append({"role": role, "parts": [m["content"]]})
        
        chat = model.start_chat(history=history or None)
        response = chat.send_message(prompt)
        
        raw_content = response.text.strip()
        if raw_content.startswith("```json"):
            raw_content = raw_content.replace("```json", "", 1).replace("```", "", 1).strip()
        
        try:
            res_json = json.loads(raw_content)
            feedback = res_json.get("feedback", "")
            assistant_text = res_json.get("response", "...")
        except:
            feedback = ""
            assistant_text = raw_content

        # Áudio
        audio_buffer = io.BytesIO()
        gTTS(text=assistant_text, lang='en', tld='com').write_to_fp(audio_buffer)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_text,
            "feedback": feedback,
            "audio": audio_buffer.getvalue()
        })
        st.rerun()

with input_col2:
    audio_prompt = st.audio_input("Grave áudio")
    if audio_prompt:
        if "last_audio_name" not in st.session_state or st.session_state.last_audio_name != audio_prompt.name:
            st.session_state.last_audio_name = audio_prompt.name
            
            # Processar áudio com Gemini
            audio_bytes = audio_prompt.read()
            
            # Para o histórico, o Gemini precisa de partes
            history = []
            for m in st.session_state.messages:
                role = m["role"] if m["role"] != "assistant" else "model"
                history.append({"role": role, "parts": [m["content"]]})
            
            chat = model.start_chat(history=history or None)
            response = chat.send_message([{"mime_type": "audio/wav", "data": audio_bytes}, "Analyze this audio as the tutor in our roleplay."])
            
            st.session_state.messages.append({"role": "user", "content": "🎤 Mensagem de voz", "type": "audio"})
            
            raw_content = response.text.strip()
            if raw_content.startswith("```json"):
                raw_content = raw_content.replace("```json", "", 1).replace("```", "", 1).strip()
            
            try:
                res_json = json.loads(raw_content)
                feedback = res_json.get("feedback", "")
                assistant_text = res_json.get("response", "...")
            except:
                feedback = ""
                assistant_text = raw_content

            audio_buffer = io.BytesIO()
            gTTS(text=assistant_text, lang='en', tld='com').write_to_fp(audio_buffer)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "feedback": feedback,
                "audio": audio_buffer.getvalue()
            })
            st.rerun()
