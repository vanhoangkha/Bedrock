from langchain_aws import AmazonKnowledgeBasesRetriever
import streamlit as st
from streamlit_chat import message
import boto3
import json
from anthropic import Anthropic
import time

anthropic = Anthropic()

def count_tokens(text):
    return len(anthropic.get_tokenizer().encode(text))

# Setting page title and header
st.set_page_config(page_title="CMC", page_icon=":robot_face:")
st.markdown("<h3 style='text-align: center;'>RoboStock - Your 24/7 AI trading companion</h3>", unsafe_allow_html=True)

# Initialize session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []
if 'cost' not in st.session_state:
    st.session_state['cost'] = []
if 'total_tokens' not in st.session_state:
    st.session_state['total_tokens'] = []
if 'total_cost' not in st.session_state:
    st.session_state['total_cost'] = 0.0

# Sidebar
st.sidebar.title("Sidebar")

clear_button = st.sidebar.button("Clear Conversation", key="clear")
model_name = "Claude-3-Haiku"
model = "anthropic.claude-3-haiku-20240307-v1:0"
# Reset everything
if clear_button:
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    st.session_state['number_tokens'] = []
    st.session_state['model_name'] = []
    st.session_state['cost'] = []
    st.session_state['total_cost'] = 0.0
    st.session_state['total_tokens'] = []
    #counter_placeholder.write(f"Total cost of this conversation: $${st.session_state['total_cost']:.5f}")

def generate_response(prompt):
    st.session_state['messages'].append({"role": "user", "content": prompt})

    bedrock = boto3.client('bedrock-runtime')
    retriever = AmazonKnowledgeBasesRetriever(
        knowledge_base_id="EWVHJIY9AS",
        top_k=3,
        retrieval_config={"vectorSearchConfiguration": 
                          {"numberOfResults": 3,
                           'overrideSearchType': "SEMANTIC",
                           }
                          },
    )
    system_prompt = """
        You are an advanced AI financial advisor with extensive market knowledge and analytical capabilities. Your role is to assist traders and investors with stock analysis, market insights, and trading strategies. Please adhere to the following guidelines:
        1. Expertise: Demonstrate deep understanding of financial markets, trading strategies, technical analysis, and market structures.
        2. Analysis: Provide thorough, data-driven analysis of market trends, specific stocks, or trading strategies as requested.
        3. Explanations: Offer clear, comprehensive explanations suitable for traders of all experience levels. Break down complex concepts when necessary.
        4. Asset Evaluation: When asked, use your knowledge to identify potential trading assets. Provide a detailed list with supporting data and rationale for each recommendation.
        5. Current Information: Ensure all advice and analysis is based on the most up-to-date market information available to you.
        6. Honesty: If you're unsure about something or don't have the necessary information, clearly state this. Do not provide speculative or potentially misleading information.
        7. Language: Provide all responses in Vietnamese.
        8. Adaptability: Tailor your responses to the specific needs and questions of each user, whether they're seeking general market insights or detailed analysis of particular stocks or strategies.
    """
    retrieved_docs = retriever.get_relevant_documents(prompt)
    context = "\n".join([doc.page_content for doc in retrieved_docs])

    query = f"""Human: {system_prompt}. Based on the provided context, provide the answer to the following question:
    <context>{context}</context>
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

    response = bedrock.invoke_model(
        body=json.dumps(request_body),
        modelId=model,
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response['body'].read())
    response_text = response_body['content'][0]['text']

    return response_text, query

# Containers
response_container = st.container()
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You:", key='input', height=100)
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        full_response, query = generate_response(user_input)
        st.session_state['past'].append(user_input)
        
        message_placeholder = st.empty()
        simulated_stream = ""

        # Simulate streaming
        for i in range(len(full_response)):
            simulated_stream += full_response[i]
            message_placeholder.markdown(simulated_stream + "▌")
            time.sleep(0.01)  # Adjust this value to control the speed of the simulated stream
        
        message_placeholder.markdown(full_response)
        
        st.session_state['generated'].append(full_response)
        st.session_state['model_name'].append(model_name)

        total_tokens = count_tokens(query) + count_tokens(full_response)
        st.session_state['total_tokens'].append(total_tokens)

        # Calculate cost (adjust as needed for Claude models)
        cost = total_tokens * 0.002 / 1000  # This is an example, adjust based on actual pricing
        st.session_state['cost'].append(cost)
        st.session_state['total_cost'] += cost

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))
            st.write(
                f"Model used: {st.session_state['model_name'][i]}; Number of tokens: {st.session_state['total_tokens'][i]}; Cost: $${st.session_state['cost'][i]:.5f}")
            #counter_placeholder.write(f"Total cost of this conversation: $${st.session_state['total_cost']:.5f}")