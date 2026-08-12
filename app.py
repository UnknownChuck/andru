import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
from streamlit_mic_recorder import speech_to_text
from github import Github

# Page Configuration
st.set_page_config(page_title="Andru Private AI", page_icon="🤖", layout="wide")

# ---------------------------------------------------------
# 1. ANDRU SYSTEM PROMPT & PERSONAL KNOWLEDGE BASE
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
  6. Personal AI (Andru): Self-hosted AI ecosystem with Groq, Streamlit, ChromaDB, and local speech controls.

### Response Instructions:
- Speak directly to Chenuka in a friendly, intelligent, and natural tone.
- When answering via voice, keep responses concise, highly structured, and conversational.
- Actively assist with code, project architecture, email summaries, and GitHub repository checks.
"""

# ---------------------------------------------------------
# 2. SECURITY GATE (PASSWORD CHECK)
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
    # 3. HELPER FUNCTIONS (TTS & GITHUB INTEGRATION)
    # ---------------------------------------------------------
    def speak_text_web(text):
        """Injects HTML5/JS Web Speech API for high volume, smooth, realistic human voice."""
        clean_text = text.replace('"', '\\"').replace("'", "\\'").replace('\n', ' ')
        js_code = f"""
        <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                var msg = new SpeechSynthesisUtterance("{clean_text}");
                msg.volume = 1.0;  // Maximum Volume
                msg.rate = 1.0;    // Natural Speed
                msg.pitch = 1.0;   # Human Pitch
                
                var voices = window.speechSynthesis.getVoices();
                for (var i = 0; i < voices.length; i++) {{
                    if (voices[i].lang.includes('en') || voices[i].lang.includes('en-US')) {{
                        msg.voice = voices[i];
                        break;
                    }}
                }}
                window.speechSynthesis.speak(msg);
            }}
        </script>
        """
        components.html(js_code, height=0, width=0)

    def fetch_github_repos():
        """Fetches repositories if GITHUB_TOKEN is provided in Secrets."""
        if "GITHUB_TOKEN" in st.secrets:
            try:
                g = Github(st.secrets["GITHUB_TOKEN"])
                user = g.get_user()
                return [repo.name for repo in user.get_repos()]
            except Exception as e:
                return [f"GitHub Error: {e}"]
        return ["GitHub Token not configured in Streamlit Secrets."]

    # ---------------------------------------------------------
    # 4. MAIN INTERFACE
    # ---------------------------------------------------------
    st.title("🤖 Andru - Personal AI Assistant")
    
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
        # User Message
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Assistant Message
        with st.chat_message("assistant"):
            sys_prompt = {"role": "system", "content": ANDRU_SYSTEM_PROMPT}
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[sys_prompt] + st.session_state.messages
            )
            
            reply = response.choices[0].message.content
            st.markdown(reply)
            
            # Auto-play high quality smooth Voice
            speak_text_web(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
