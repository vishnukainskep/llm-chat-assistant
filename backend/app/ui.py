import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/ask"

st.title("🤖 Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    with st.chat_message("user"):
        st.write(user_input)

    response = requests.post(
        API_URL,
        json={"user_input": user_input}
    )

    bot_reply = response.json()["response"]

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply
    })
    with st.chat_message("assistant"):
        st.write(bot_reply)