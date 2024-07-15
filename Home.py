import streamlit as st
import streamlit.components.v1 as components
import Libs as glib 
import base

def generate_response(prompt):
    if base.get_num_tokens(prompt) >= 1000000:
        st.error("Conversation length too long. Please keep it under 1000000 tokens.")
        st.button(
            "🗑 Clear Chat History",
            on_click=base.clear_chat_history,
            key="clear_chat_history",
        )
        st.stop()

    response = glib.call_claude_sonet_stream(prompt)
    return response

st.set_page_config(page_title="CMCTS", page_icon="img/favicon.ico", layout="wide")

base.init_home_state()
base.init_slidebar()
base.init_dialog()
base.init_animation()

if prompt := st.chat_input():
    st.session_state.show_animation = False
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message(
        "user",
        avatar="https://raw.githubusercontent.com/sahirmaharaj/exifa/main/img/user.gif",
    ):
        st.write(prompt)

if st.session_state.messages[-1]["role"] != "assistant":
    st.session_state.show_animation = False

    with st.chat_message(
        "user",
        avatar="https://cdn.haitrieu.com/wp-content/uploads/2022/12/Icon-Dai-hoc-CMC.png",
    ):
        response = generate_response(prompt)
        full_response = st.write_stream(response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)
