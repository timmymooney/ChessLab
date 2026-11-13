import streamlit as st

# configure the app
st.set_page_config(
    page_title="ChessLab",
    page_icon="♟️",
    layout="wide"
)

# app header
st.title("♟️ ChessLab")
st.write("Analyse your Chess.com games and improve your chess!")

st.divider()

# username input
username = st.text_input(
    "Enter your Chess.com username",
    placeholder="e.g. hikaru"
)

# analyse button
if st.button("Analyse my games"):
    if username:
        st.success(f"Welcome to ChessLab, {username}!")
    else:
        st.warning("Please enter a valid Chess.com username.")