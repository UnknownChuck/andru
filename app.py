import streamlit as st
from groq import Groq
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS
import io

st.set_page_config(page_title="Andru AI", page_icon="🤖")

# 1. Lock (Password Gate)
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
    # 2. Andru UI
    st.title("🤖 Hello! I am Andru")
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 🎤 Voice Input Section
    st.write("---")
    st.write("🎤 **Click below to speak to Andru:**")
    voice_text = speech_to_text(language='en', start_prompt="🎙️ Start Recording", stop_prompt="⏹️ Stop & Send", key='voice_input')

    # Text Input Section
    text_text = st.chat_input("Or type to Andru...")

    # Choose Input (Voice or Text)
    user_prompt = voice_text if voice_text else text_text

    if user_prompt:
        # Add User Message
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Get AI Response
        with st.chat_message("assistant"):
            sys_prompt = {"role": "system", "content": "You are Andru, a witty, helpful private AI friend. Keep replies concise for voice chat."}
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[sys_prompt] + st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)

            # 🔊 Voice Output (Audio reply)
            tts = gTTS(text=reply, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp, format='audio/mp3')

        st.session_state.messages.append({"role": "assistant", "content": reply})
