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
    page_title="BeConfident | English Tutor",
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
""", unsafe_allow_name=True)

# --- GERENCIAMENTO DE API KEY ---
def get_api_key():
    # 1. Tenta st.secrets
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except:
        pass
    
    # 2. Tenta variável de ambiente local
    env_key = os.getenv("GOOGLE_API_KEY")
    if env_key:
        return env_key
    
    # 3. Fallback: Input na Sidebar
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
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )

# --- ESTADO DA SESSÃO ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- INTERFACE DE CHAT ---
st.title("🎓 BeConfident")
st.caption(f"Praticando: **{scenario}**")

# Mostrar histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            # Bloco de Feedback (Adjust)
            if msg.get("feedback"):
                with st.expander("🔍 Adjust (Feedback)", expanded=False):
                    st.info(msg["feedback"])
            
            # Resposta Principal (Practice)
            st.write(msg["content"])
            
            # Áudio se existir
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")
        else:
            st.write(msg["content"])

# --- LÓGICA DE INPUT ---
if prompt := st.chat_input("Digite sua mensagem em inglês..."):
    # Adicionar mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Gerar resposta da IA
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Criar histórico para o Gemini
                chat = model.start_chat(history=[
                    {"role": m["role"] if m["role"] != "assistant" else "model", 
                     "parts": [m["content"]]} 
                    for m in st.session_state.messages[:-1]
                ])
                
                response = chat.send_message(prompt)
                
                # Parsing do JSON da resposta
                raw_content = response.text.strip()
                # Limpar possíveis markdown code blocks do JSON
                if raw_content.startswith("```json"):
                    raw_content = raw_content.replace("```json", "", 1).replace("```", "", 1).strip()
                
                try:
                    res_json = json.loads(raw_content)
                    feedback = res_json.get("feedback", "")
                    assistant_text = res_json.get("response", "I'm sorry, I couldn't process that.")
                except:
                    # Fallback caso não venha JSON válido
                    feedback = "Perfect! Keep going."
                    assistant_text = raw_content

                # UI: Feedback
                with st.expander("🔍 Adjust (Feedback)", expanded=True):
                    st.info(feedback)
                
                # UI: Texto da Resposta
                st.write(assistant_text)
                
                # Áudio (gTTS)
                audio_buffer = io.BytesIO()
                try:
                    tts = gTTS(text=assistant_text, lang='en', tld='com')
                    tts.write_to_fp(audio_buffer)
                    st.audio(audio_buffer, format="audio/mp3")
                    audio_data = audio_buffer.getvalue()
                except Exception as e:
                    st.error(f"Erro no áudio: {e}")
                    audio_data = None

                # Salvar na sessão
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text,
                    "feedback": feedback,
                    "audio": audio_data
                })
                
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")
