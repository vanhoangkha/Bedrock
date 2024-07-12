from langchain_community.retrievers import AmazonKnowledgeBasesRetriever
import streamlit as st
from streamlit_chat import message
import boto3
import json
from anthropic import Anthropic
import time
from langchain.prompts.chat import ChatPromptTemplate
from langchain.llms.bedrock import Bedrock
from langchain_community.chat_models import BedrockChat
from datetime import date
from datetime import datetime, timedelta
from pandas_datareader import data as pdr
import os
from vnstock3 import Vnstock
from bs4 import BeautifulSoup
import re
import requests

from langchain.callbacks import StreamlitCallbackHandler

anthropic = Anthropic()
knowledge_base_id=("EWVHJIY9AS"),

def count_tokens(text):
    return len(anthropic.get_tokenizer().encode(text))

# Setting page title and header
st.set_page_config(page_title="CMC Stock Agent", page_icon=":robot_face:")
st.markdown("<h1 style='text-align: center;'>RoboStock - Your 24/7 AI assistant</h1>", unsafe_allow_html=True)

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

model_name = "Claude-3-Haiku"
modelId = "anthropic.claude-3-haiku-20240307-v1:0"

# Sidebar
st.sidebar.title("Sidebar")

clear_button = st.sidebar.button("Clear Conversation", key="clear")
model_name = "Claude-3-Haiku"
modelId = "anthropic.claude-3-haiku-20240307-v1:0"
# anthropic.claude-3-5-sonnet-20240620-v1:0
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
def get_llm():      
    model_kwargs_claude = {"temperature": 0.0, "top_p": .5, "max_tokens_to_sample": 2000}
    llm = Bedrock(
        credentials_profile_name=os.environ.get("BWB_PROFILE_NAME"), #sets the profile name to use for AWS credentials (if not the default)
        region_name=os.environ.get("BWB_REGION_NAME"), #sets the region name (if not the default)
        endpoint_url=os.environ.get("BWB_ENDPOINT_URL"), #sets the endpoint URL (if necessary)
        model_id="anthropic.claude-v2", #set the foundation model
        model_kwargs=model_kwargs_claude,
        streaming=True)

    return llm

def get_stock_ticker(question):
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
    retrieved_docs = retriever.get_relevant_documents(question+ " công ty")
    context = "\n".join([doc.page_content for doc in retrieved_docs])
    query = f"""Human: Given the user request, what is the comapany name and the company stock ticker ?: 
    <context>{context}</context>
    Question: {question}?"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": [
            {"role": "user", "content": query}
        ],
        "temperature": 0.7,
        "top_p": 1,
    }

    response = bedrock_runtime.invoke_model(
        body=json.dumps(request_body),
        modelId=modelId,
        contentType="application/json",
        accept="application/json"
    )
    return response.get('body'), question

def get_stock_price(ticker, history=500):
    today = date.today()
    start_date = today - timedelta(days=history)
    stock = Vnstock().stock(symbol=ticker.upper(), source='VCI')
    data = stock.quote.history(start=start_date.strftime('%Y-%m-%d'),end=today.strftime('%Y-%m-%d'))
    return data

def get_financial_statements(ticker):
    stock = Vnstock().stock(symbol=ticker.upper(), source='VCI')
    data = stock.finance.balance_sheet(period='year', lang='en')
    return data

# Script to scrap top5 googgle news for given company name
def google_query(search_term):
    if "news" not in search_term:
        search_term=search_term+" stock news"
    url=f"https://www.google.com/search?q={search_term}&cr=countryIN"
    url=re.sub(r"\s","+",url)
    return url
def get_recent_stock_news(ticker):
    # time.sleep(4) #To avoid rate limit error
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    company = Vnstock().stock(symbol=ticker.upper(), source='TCBS').company
    company_name = company.profile()['company_name'][0]
    g_query=google_query(company_name)
    res=requests.get(g_query,headers=headers).text
    soup=BeautifulSoup(res,"html.parser")
    news=[]
    for n in soup.find_all("div","n0jPhd ynAwRc tNxQIb nDgy9d"):
        news.append(n.text)
    for n in soup.find_all("div","IJl0Z"):
        news.append(n.text)

    if len(news)>6:
        news=news[:4]
    else:
        news=news
    news_string=""
    for i,n in enumerate(news):
        news_string+=f"{i}. {n}\n"
    top5_news="Recent News:\n\n"+news_string
    
    return top5_news

from langchain.agents import load_tools
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
def initializeAgent():
    zero_shot_agent=initialize_agent(
    llm=get_llm(),
    agent="zero-shot-react-description",
    tools=tools,
    verbose=True,
    max_iteration=4,
    return_intermediate_steps=True,
    handle_parsing_errors=True,
    output_key="output",
)
    prompt = """
    You are an advanced AI financial advisor with extensive market knowledge and analytical capabilities. Your name is CRobo Advisor. The current date is July 2024. Your role is to assist traders and investors with stock analysis, market insights, and trading strategies. Please adhere to the following guidelines:
    1. Expertise: Demonstrate deep understanding of financial markets, trading strategies, technical analysis, and market structures.
    2. Analysis: Provide thorough, data-driven analysis of market trends, specific stocks, or trading strategies as requested.
    3. Explanations: Offer clear, comprehensive explanations suitable for traders of all experience levels. Break down complex concepts when necessary.
    4. Asset Evaluation: When asked, use your knowledge to identify potential trading assets. Provide a detailed list with supporting data and rationale for each recommendation.
    5. Current Information: Ensure all advice and analysis is based on the most up-to-date market information available to you. If you need to access real-time data, inform the user and proceed to retrieve the latest information.
    6. Honesty: If you're unsure about something or don't have the necessary information, clearly state this. Do not provide speculative or potentially misleading information.
    7. Language: Provide all responses in Vietnamese.
    8. Adaptability: Tailor your responses to the specific needs and questions of each user, whether they're seeking general market insights or detailed analysis of particular stocks or strategies.
    9. Markdown Format: Provide all responses in Markdown format, highlighting key points using bold text.
    10. Tools: Use the following tools to gather necessary data:
        - get company ticker: Use when you need to extract company name and stock ticker. Input the human query to it.
        - get stock data: Use when you are asked to evaluate or analyze a stock. Input the stock ticker to it.
        - get recent news: Use this to fetch recent news about stocks. Input the stock ticker to it.
        - get financial statements: Use this to get financial statements of the company. Input the stock ticker to it.
    11. Steps: Follow these steps to provide a comprehensive response:
        - Step 1: Use "get company ticker" tool to get the company name and stock ticker. Output: company name and stock ticker.
        - Step 2: Use "get stock data" tool to gather stock info. Output: Stock data.
        - Step 3: Use "get recent news" tool to search for latest stock-related news. Output: Stock news.
        - Step 4: Use "get financial statements" tool to get company's balance sheet. Output: Balance sheet.
        - Step 5: Analyze the stock based on gathered data and give detailed analysis for investment choice. Provide numbers and reasons to justify your answer. Output: Detailed stock analysis.

    Use the following format:
    Question: the input question you must answer
    Thought: you should always think about what to do, Also try to follow steps mentioned above
    Action: the action to take, should be one of [get company ticker, get stock data, get recent news, get financial statements]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Question: {input}

    Assistant:
    {agent_scratchpad}
    """
    zero_shot_agent.agent.llm_chain.prompt.template=prompt
    return zero_shot_agent

tools=[
    Tool(
        name="get company ticker",
        func=get_stock_ticker,
        description="Get the company stock ticker"
    ),
    Tool(
        name="get stock data",
        func=get_stock_price,
        description="Use when you are asked to evaluate or analyze a stock. This will output historic share price data. You should input the the stock ticker to it "
    ),
    Tool(
        name="get recent news",
        func=get_recent_stock_news,
        description="Use this to fetch recent news about stocks"
    ),

    Tool(
        name="get financial statements",
        func=get_financial_statements,
        description="Use this to get balance sheet of the company. With the help of this data companys historic performance can be evaluaated. You should input stock ticker to it"
    ) 
 

]

zero_shot_agent = initializeAgent()
if 'chat_history' not in st.session_state: 
    st.session_state.chat_history = [] 

def generate_response(prompt):
    # Initialize the session state for messages if it doesn't exist
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    st.session_state['messages'].append({"role": "user", "content": prompt})

    response = zero_shot_agent({
            "input": prompt,
            "chat_history": st.session_state.chat_history,
         },
        )
    return response.get('body'), prompt

# Containers
response_container = st.container()
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You:", key='input', height=100)
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        response_stream, query = generate_response(user_input)
        st.session_state['past'].append(user_input)
        
        message_placeholder = st.empty()
        full_response = ""

        # Process the streaming response
        if response_stream:
            for event in response_stream:
                if event:
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