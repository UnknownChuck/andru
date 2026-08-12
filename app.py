import streamlit as st
from groq import Groq
from streamlit_mic_recorder import speech_to_text
from github import Github
from gtts import gTTS
import io
import base64

# Page Configuration
st.set_page_config(page_title="Andru Private AI", page_icon="🤖", layout="wide")

# ---------------------------------------------------------
# 1. ANDRU SYSTEM PROMPT (LANGUAGE & SPELLING TOLERANCE)
# ---------------------------------------------------------
ANDRU_SYSTEM_PROMPT = """
You are "Andru", a highly intelligent, witty, smooth-talking, and private personal AI assistant.

### Context Understanding & Robustness Instructions:
- You are extremely adaptable to any language (English, Singlish, Sinhala, etc.).
- You MUST understand the user even if there are severe spelling mistakes, typos, or slang. Always grasp the underlying intent smoothly without complaining about grammar or spelling.
- Keep responses conversational, concise, natural, and straight to the point (ideal for voice output).

### Key User Profile:
- User Name: Chenuka Basilu
- Your Role: Chenuka's personal assistant and close friend.
- User Focus Areas: Game Dev (HTML/JS/3D), Blender 3D, Cybersecurity (Nmap/Hashcat), System Tuning, Creative Writing ("FOL: Reborn").
"""

# ---------------------------------------------------------
# 2. RELIABLE AUDIO PLAYER
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
    # 5. MAIN INTERFACE & GROQ SETUP
    # ---------------------------------------------------------
    st.title("🤖 Andru - Personal AI Assistant")
    
    if "GROQ_API_KEY" not in st.secrets:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets!")
        st.stop()

    # Initialize Groq Client
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

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
            try:
                sys_prompt = {"role": "system", "content": ANDRU_SYSTEM_PROMPT}
                
                # Using Llama-3.3-70b for ultimate accuracy, spelling tolerance and speed
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[sys_prompt] + st.session_state.messages
                )
                
                reply = response.choices[0].message.content
                st.markdown(reply)
                
                play_voice(reply)

                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as err:
                st.error(f"Groq API Error: {err}")
