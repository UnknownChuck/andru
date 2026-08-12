import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

st.set_page_config(page_title="Andru AI", page_icon="🤖")

# 1. Password Lock Gate
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
            st.error("Wrong password! Try again.")
else:
    # 2. Main Andru App
    st.title("🤖 Hello! I am Andru")
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User Input Field
    if prompt := st.chat_input("Talk to Andru..."):
        # Add User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate AI Response
        with st.chat_message("assistant"):
            sys_prompt = {"role": "system", "content": "You are Andru, a witty, natural, personal AI assistant. Keep responses short and conversational for speech."}
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[sys_prompt] + st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)

            # 🔊 JavaScript Auto Text-To-Speech Injector
            clean_reply = reply.replace('"', '\\"').replace('\n', ' ')
            js_tts = f"""
            <script>
                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.cancel(); // Stop any previous speech
                    var msg = new SpeechSynthesisUtterance("{clean_reply}");
                    msg.lang = 'en-US';
                    msg.rate = 1.0;
                    window.speechSynthesis.speak(msg);
                }}
            </script>
            """
            components.html(js_tts, height=0, width=0)

        st.session_state.messages.append({"role": "assistant", "content": reply})
