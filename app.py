import streamlit as st
from google import genai
from google.genai import types
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
# 2. AUDIO PLAYER FUNCTION
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
# 3. HELPER FOR GEMINI GENERATION WITH DYNAMIC FALLBACK
# ---------------------------------------------------------
def generate_with_fallback(client, contents, system_prompt):
    """Dynamically finds an active model or tries safe fallbacks to avoid 404 errors."""
    models_to_try = []
    
    # 1. Try to query available models dynamically
    try:
        all_models = [
            m.name for m in client.models.list() 
            if hasattr(m, 'supported_generation_methods') and 'generateContent' in m.supported_generation_methods
        ]
        flash_models = [m for m in all_models if 'flash' in m]
        models_to_try = flash_models + all_models
    except Exception:
        pass

    # 2. Add standard static fallback models if dynamic fetch fails
    models_to_try.extend(["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"])
    
    # Remove duplicates preserving order
    seen = set()
    unique_models = [x for x in models_to_try if not (x in seen or seen.add(x))]

    last_err = None
    for model_name in unique_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
            )
            return response.text
        except Exception as e:
            last_err = e
            continue
            
    raise last_err

# ---------------------------------------------------------
# 4. SECURITY GATE
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
    # 5. GITHUB INTEGRATION
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
    # 6. MAIN INTERFACE & GEMINI SETUP
    # ---------------------------------------------------------
    st.title("🤖 Andru - Personal AI Assistant")
    
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Please add GEMINI_API_KEY to Streamlit Secrets!")
        st.stop()

    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

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
                # Format conversation history
                contents = []
                for m in st.session_state.messages:
                    role = "user" if m["role"] == "user" else "model"
                    contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=m["content"])]
                        )
                    )

                # Generate response using auto-fallback
                reply = generate_with_fallback(client, contents, ANDRU_SYSTEM_PROMPT)
                
                st.markdown(reply)
                play_voice(reply)

                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as err:
                st.error(f"Gemini API Error: {err}")
