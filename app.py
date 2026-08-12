import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import speech_to_text
from github import Github
from gtts import gTTS
import io
import base64

# Page Configuration
st.set_page_config(page_title="Andru Private AI", page_icon="🤖", layout="wide")

# ---------------------------------------------------------
# 1. ANDRU SYSTEM PROMPT
# ---------------------------------------------------------
ANDRU_SYSTEM_PROMPT = """
You are "Andru", a highly intelligent, witty, smooth-talking, and private personal AI assistant.

### Key Context & User Profile:
- User Name: Chenuka Basilu
- Your Role: Chenuka's personal assistant and close friend.
- User Projects & Focus Areas:
  1. Game Development: 2D & 3D games using HTML, JavaScript, Three.js, and Babylon.js.
  2. 3D Modeling & Animation: Asset pipelines and low-poly modeling in Blender.
  3. Cybersecurity & Ethical Hacking: Penetration testing, CTFs, Nmap, Hashcat, John the Ripper.
  4. System Optimization: Legacy hardware tuning (Core 2 Duo/Quad setups, OS optimization).
  5. Creative Writing: Sci-Fi & Fantasy projects like "FOL: Reborn" and "PROJECT NONAME: THE THREE HOLLOWS".
  6. Personal AI (Andru): Self-hosted AI ecosystem with Gemini, Streamlit, ChromaDB, and local speech controls.

### Response Instructions:
- Speak directly to Chenuka in a friendly, intelligent, and natural tone.
- Keep responses short, clear, and natural for voice synthesis.
"""

# ---------------------------------------------------------
# 2. AUDIO PLAYER FUNCTION (RELIABLE VOICE OUTPUT)
# ---------------------------------------------------------
def play_voice(text):
    """Generates audio using gTTS and plays it automatically using HTML5 base64 audio."""
    try:
        tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        audio_bytes = fp.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()
        
        md = f"""
            <audio autoplay style="width: 100%;">
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            Your browser does not support the audio element.
            </audio>
            """
        st.components.v1.html(md, height=50)
    except Exception as e:
        st.error(f"Voice Generation Error: {e}")

# ---------------------------------------------------------
# 3. SECURITY GATE
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Security Gate")
    password_input = st.text_input("Enter Password to talk with Andru:", type="password")
    if st.button("Unlock Andru"):
        if password_input == "asm201":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Wrong password! Access Denied.")
else:
    # ---------------------------------------------------------
    # 4. GITHUB INTEGRATION
    # ---------------------------------------------------------
    def fetch_github_repos():
        if "GITHUB_TOKEN" in st.secrets:
            try:
                g = Github(st.secrets["GITHUB_TOKEN"])
                user = g.get_user()
                return [repo.name for repo in user.get_repos()]
            except Exception as e:
                return [f"GitHub Error: {e}"]
        return ["GitHub Token not configured in Streamlit Secrets."]

    # ---------------------------------------------------------
    # 5. MAIN INTERFACE & GEMINI SETUP
    # ---------------------------------------------------------
    st.title("🤖 Andru - Personal AI Assistant (Gemini Powered)")
    
    # Configure Gemini API Key
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Initialize Gemini Model with System Prompt
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=ANDRU_SYSTEM_PROMPT
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.write("---")
    st.subheader("⚙️ Quick Tools & Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📁 Check My GitHub Repositories"):
            repos = fetch_github_repos()
            st.info(f"Your Repositories: {', '.join(repos)}")
            
    with col2:
        st.write("🎤 **Voice Input:**")
        voice_text = speech_to_text(language='en', start_prompt="🎙️ Start Speaking", stop_prompt="⏹️ Stop & Send", key='voice_input')

    # Text Input
    text_text = st.chat_input("Talk or give commands to Andru...")

    # Determine Active Input
    user_prompt = voice_text if voice_text else text_text

    # Process AI Response
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            # Format chat history for Gemini
            chat_history = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [m["content"]]})
            
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(user_prompt)
            
            reply = response.text
            st.markdown(reply)
            
            # Reliable Audio Output Call
            play_voice(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
