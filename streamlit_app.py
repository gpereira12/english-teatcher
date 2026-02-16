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

# --- ESTILO CUSTOMIZADO (Apple-Aesthetics) ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .main .block-container {
        padding-top: 2rem;
    }
    .stChatMessage {
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .feedback-box {
        background-color: #f0f4ff;
        border-left: 5px solid #4a90e2;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
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
    st.title("⚙️ Configurações")
    
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
    
    # Escolha de Cenário
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
    
    # Instrução do Sistema
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
    
    # Using 'gemini-1.5-flash' which is the stable name. 
    # v1beta error usually happens if the model name is incorrect or library is outdated.
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )

# --- ESTADO DA SESSÃO ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- INTERFACE DE CHAT ---
st.title("🎓 English Tutor")
st.caption(f"Praticando: **{scenario}**")

# Mostrar histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            if msg.get("feedback"):
                with st.expander("🔍 Adjust (Feedback)", expanded=False):
                    st.info(msg["feedback"])
            
            st.write(msg["content"])
            
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")
        else:
            st.write(msg["content"])
            if msg.get("type") == "audio":
                st.info("🎤 Audio message sent")

# --- LÓGICA DE PROCESSAMENTO ---
def process_message(prompt_text, audio_file=None):
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt_text if prompt_text else "[Audio Message]",
        "type": "audio" if audio_file else "text"
    })
    
    with st.chat_message("user"):
        if prompt_text:
            st.write(prompt_text)
        if audio_file:
            st.audio(audio_file)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Se houver áudio, enviamos para o Gemini transcrever/responder diretamente
                content = []
                if prompt_text:
                    content.append(prompt_text)
                if audio_file:
                    # Carregar áudio para o Gemini
                    audio_bytes = audio_file.read()
                    content.append({
                        "mime_type": "audio/wav", # Streamlit audio_input uses wav/webp/mp3 depending on browser, but generally wav
                        "data": audio_bytes
                    })
                
                # Chat History
                history = []
                for m in st.session_state.messages[:-1]:
                    role = m["role"] if m["role"] != "assistant" else "model"
                    history.append({"role": role, "parts": [m["content"]]})
                
                chat = model.start_chat(history=history)
                response = chat.send_message(content)
                
                raw_content = response.text.strip()
                if raw_content.startswith("```json"):
                    raw_content = raw_content.replace("```json", "", 1).replace("```", "", 1).strip()
                
                try:
                    res_json = json.loads(raw_content)
                    feedback = res_json.get("feedback", "")
                    assistant_text = res_json.get("response", "I'm sorry, I couldn't process that.")
                except:
                    feedback = "Great! Keep practicing."
                    assistant_text = raw_content

                # UI: Feedback
                with st.expander("🔍 Adjust (Feedback)", expanded=True):
                    st.info(feedback)
                
                # UI: Texto da Resposta
                st.write(assistant_text)
                
                # Áudio (gTTS)
                audio_buffer = io.BytesIO()
                tts = gTTS(text=assistant_text, lang='en', tld='com')
                tts.write_to_fp(audio_buffer)
                st.audio(audio_buffer, format="audio/mp3")
                
                # Salvar na sessão
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text,
                    "feedback": feedback,
                    "audio": audio_buffer.getvalue()
                })
                
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")

# --- INPUTS ---
# Colunas para botões de texto e áudio
col1, col2 = st.columns([1, 1])

with col1:
    prompt = st.chat_input("Digite sua mensagem em inglês...")
    if prompt:
        process_message(prompt)

with col2:
    # st.audio_input is available in Streamlit 1.34+
    try:
        audio_prompt = st.audio_input("Grave seu áudio")
        if audio_prompt:
            # Para evitar duplicidade no rerun do streamlit
            # Usamos um controle simples
            if "last_audio" not in st.session_state or st.session_state.last_audio != audio_prompt.name:
                st.session_state.last_audio = audio_prompt.name
                process_message(None, audio_prompt)
    except Exception as e:
        # Fallback se a versão do Streamlit for antiga ou der erro
        st.caption("Recurso de áudio indisponível nesta versão do Streamlit.")
