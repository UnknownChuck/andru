import streamlit as st
from groq import Groq
from github import Github
from gtts import gTTS
import io
import base64
import json
import os

# Page Configuration
st.set_page_config(page_title="Andru Private AI", page_icon="🤖", layout="wide")

# ---------------------------------------------------------
# 1. ANDRU SYSTEM PROMPT (WITH MEMORY & RESEARCH CAPABILITIES)
# ---------------------------------------------------------
ANDRU_SYSTEM_PROMPT = """
You are "Andru", an advanced, intelligent, witty, and private personal AI assistant for Chenuka Basilu.
- Adaptable to any language (Sinhala, Singlish, English). Understand severe typos and spelling mistakes smoothly.
- You remember context, conduct research, and can help save files directly to Chenuka's GitHub repository when requested.
- Keep responses conversational, natural, and precise.
"""

# ---------------------------------------------------------
# 2. AUDIO PLAYER (MULTILINGUAL)
# ---------------------------------------------------------
def play_voice(text):
    try:
        has_sinhala = any('\u0D80' <= c <= '\u0DFF' for c in text)
        lang_code = 'si' if has_sinhala else 'en'
        
        tts = gTTS(text=text, lang=lang_code, slow=False)
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
    # 4. GITHUB TOOLS (Save files directly to repo)
    # ---------------------------------------------------------
    def save_file_to_github(file_path, file_content, commit_message):
        if "GITHUB_TOKEN" in st.secrets:
            try:
                g = Github(st.secrets["GITHUB_TOKEN"])
                user = g.get_user()
                # Assuming repo name is 'andru' or target repo
                repo = user.get_repo("andru") 
                
                try:
                    # Check if file exists, if so update it
                    contents = repo.get_contents(file_path)
                    repo.update_file(contents.path, commit_message, file_content, contents.sha)
                    return True, f"Successfully updated {file_path} on GitHub!"
                except:
                    # Otherwise create new file
                    repo.create_file(file_path, commit_message, file_content)
                    return True, f"Successfully created {file_path} on GitHub!"
            except Exception as e:
                return False, f"GitHub Error: {e}"
        return False, "GITHUB_TOKEN not found."

    # ---------------------------------------------------------
    # 5. MAIN INTERFACE
    # ---------------------------------------------------------
    st.title("🤖 Andru - Personal AI Assistant")
    
    if "GROQ_API_KEY" not in st.secrets:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets!")
        st.stop()

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.write("---")
    st.subheader("⚙️ Quick Tools & Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        # Manual file saver UI
        with st.expander("📁 Save Code/Notes to GitHub Repo"):
            file_name = st.text_input("File Name (e.g., notes.py):")
            file_content = st.text_area("File Content:")
            if st.button("Commit to GitHub"):
                if file_name and file_content:
                    success, msg = save_file_to_github(file_name, file_content, f"Added {file_name} via Andru AI")
                    if success: st.success(msg)
                    else: st.error(msg)
                else:
                    st.warning("Please fill both fields.")
            
    with col2:
        st.write("🎤 **Voice Input:**")
        speech_html = """
        <script>
        function startDictation() {
            if (window.hasOwnProperty('webkitSpeechRecognition')) {
                var recognition = new webkitSpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = "si-LK";
                recognition.start();
                document.getElementById('status').innerText = "🎙️ කතා කරන්න...";

                recognition.onresult = function(e) {
                    var transcript = e.results[0][0].transcript;
                    recognition.stop();
                    document.getElementById('status').innerText = "✅ සාර්ථකයි!";
                    const input = window.parent.document.querySelector('textarea[aria-label="Talk or give commands to Andru..."]');
                    if (input) {
                        input.value = transcript;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                };
            }
        }
        </script>
        <button onclick="startDictation()" style="background-color: #ff4b4b; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-weight: bold;">🎙️ Click & Speak</button>
        <p id="status" style="margin-top:5px; font-size:12px; color:#888;"></p>
        """
        st.components.v1.html(speech_html, height=100)

    user_prompt = st.chat_input("Talk or give commands to Andru...")

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            try:
                sys_prompt = {"role": "system", "content": ANDRU_SYSTEM_PROMPT}
                
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
