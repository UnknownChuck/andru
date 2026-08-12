import streamlit as st
from groq import Groq

st.set_page_config(page_title="Andru AI", page_icon="🤖")

# 1. Lock එක (Password Gate)
if "authenticated" not in st.sessions:
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
    # 2. Andru ගේ Chat Screen එක
    st.title("🤖 Hello! I am Andru")
    
    # Groq Key එක රහසිගතව ගන්නවා
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # පරණ කතා ටික පෙන්නනවා
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ඔයා ටයිප් කරන එක Andru ට යවනවා
    if prompt := st.chat_input("Talk to Andru..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            sys_prompt = {"role": "system", "content": "You are Andru, a witty and helpful private AI friend."}
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[sys_prompt] + st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
            
        st.session_state.messages.append({"role": "assistant", "content": reply})
