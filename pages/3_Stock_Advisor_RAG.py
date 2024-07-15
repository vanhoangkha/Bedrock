from langchain_community.retrievers import AmazonKnowledgeBasesRetriever
import streamlit as st
from streamlit_chat import message
import boto3
import json
from anthropic import Anthropic
import base

anthropic = Anthropic()
knowledge_base_id=('EWVHJIY9AS'),
#knowledge_base_id="DMYEBQYJNN", 
model_name = "Claude-3-Haiku"
modelId = "anthropic.claude-3-haiku-20240307-v1:0"
# anthropic.claude-3-5-sonnet-20240620-v1:0

st.set_page_config(page_title="CMC Stock Advisor", page_icon="img/favicon.ico", layout="wide")

def count_tokens(text):
    return len(anthropic.get_tokenizer().encode(text))

st.markdown("<h3 style='text-align: center;'>RoboStock - Your 24/7 AI financial companion</h3>", unsafe_allow_html=True)

base.init_stock_advisor()
base.init_slidebar()
base.init_animation()

clear_button = st.sidebar.button("Clear Conversation", key="clear")
if clear_button:
    base.clear_stock_advisor()

def generate_response(prompt):
    # Initialize the session state for messages if it doesn't exist
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    st.session_state['messages'].append({"role": "user", "content": prompt})

    bedrock_runtime = boto3.client('bedrock-runtime')
    retriever = AmazonKnowledgeBasesRetriever(
        knowledge_base_id=knowledge_base_id[0], 
        top_k=3,
        retrieval_config={"vectorSearchConfiguration": 
                          {"numberOfResults": 3,
                           'overrideSearchType': "SEMANTIC",
                           }
                          },
    )
    
    retrieved_docs = retriever.get_relevant_documents(prompt+" 2024")
    context = "\n".join([doc.page_content for doc in retrieved_docs])
    conversation_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state['messages']])

    query = f"""Human: {base.system_prompt}. Based on the provided context, provide the answer to the following question:
    <context>{context}</context>
    <conversation_history>{conversation_history}</conversation_history>
    <question>{prompt} </question>
    Remember, while you can offer analysis and insights, you should not make definitive predictions about future market movements or provide personalized financial advice.
    Assistant: 
    """
 
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": [
            {"role": "user", "content": query}
        ],
        "temperature": 0.7,
        "top_p": 1,
    }

    response = bedrock_runtime.invoke_model_with_response_stream(
        body=json.dumps(request_body),
        modelId=modelId,
        contentType="application/json",
        accept="application/json"
    )

    return response.get('body'), query


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
        "assistant",
        avatar="https://cdn.haitrieu.com/wp-content/uploads/2022/12/Icon-Dai-hoc-CMC.png",
    ):
        response_stream, query = generate_response(prompt)
        
        message_placeholder = st.empty()
        full_response = ""

        # Process the streaming response
        for event in response_stream:
            chunk = event.get('chunk')
            if chunk:
                chunk_obj = json.loads(chunk.get('bytes').decode())
                if 'delta' in chunk_obj:
                    delta_obj = chunk_obj.get('delta', None)
                    if delta_obj:
                        text = delta_obj.get('text', None)
                        if text:
                            full_response += text
                            message_placeholder.markdown(full_response + "▌")

        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)
