__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
import streamlit as st
import utils
import time
import os

st.set_page_config(
    page_title="ISC-CodeConnect",
    page_icon="images/code-connect.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.image("images/code-connect.png", width=200)


def main():
    if "genai_api_key" not in st.session_state:
        genai_api_key_placeholder = st.empty()
        genai_api_key = genai_api_key_placeholder.text_input(
            "IBM WatsonX API Key", type="password"
        )
        if not genai_api_key:
            st.info("Please add your IBM WatsonX API key to continue.")
            st.stop()
        else:
            genai_api_key_placeholder.empty()
            st.session_state.genai_api_key = genai_api_key

    with st.sidebar:
        st.image("images/code-connect.png", width=300)
        st.title("Welcome to ISC-CodeConnect!")

        st.markdown(
            "ISC-CodeConnect is an advanced platform built using IBM WatsonX. "
            "It answers questions related to ISC Github Repositories."
            "Choose ISC repositories, and let CodeConnect hatch profound insights from repositories, all powered by cutting-edge IBM WatsonX Gen AI"
        )

        user_repo = st.multiselect(
            "Please select ISC repository",
            ["Global Schema", "PRM", "Sales", "Global Core"],
        )
        if not user_repo:
            st.info("Please select ISC repositories to continue.")
        else:
            st.session_state.user_repo = user_repo

        if st.button("Process"):
            if "embedder" not in st.session_state:
                embedder = utils.Embedder(st.session_state.user_repo)
                st.session_state.embedder = embedder
                ## Chunk and Create DB
                with st.spinner(
                    "Processing your repositories. This may take some time.."
                ):
                    if "clone_paths" not in st.session_state:
                        clone_paths = st.session_state.embedder.process_repo_files()
                        st.session_state.clone_paths = clone_paths
                        st.session_state.conversation_chain = (
                            st.session_state.embedder.get_conversation_chain(
                                gen_ai_key=st.session_state.genai_api_key,
                                clone_paths=st.session_state.clone_paths,
                            )
                        )
                        st.success("Processing completed. Ready to take your questions")
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello. I am ISC CodeConnect - Your personalized ISC Code assistant! How may I assist you today?",
            }
        ]
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

        # Accept user input
    if prompt := st.chat_input("Type your question here."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user", avatar="images/user.png"):
            st.markdown(prompt)

        with st.spinner("Thinking...."):
            # Display assistant response in chat message container
            response = st.session_state.embedder.retrieve_results(
                prompt, st.session_state.conversation_chain
            )
            # Add assistant response to chat history
            message = {"role": "assistant", "content": response}
            st.session_state.messages.append(message)

        with st.chat_message("assistant"):
            st.markdown(response)


if __name__ == "__main__":
    main()
