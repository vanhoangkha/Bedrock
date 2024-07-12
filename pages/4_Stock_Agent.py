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
import pandas as pd
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

# Function to parse and validate response
def parse_response(content):
  try:
      parsed_data = json.loads(content)
      company_name = parsed_data.get('company_name', 'Unknown')
      company_ticker = parsed_data.get('company_ticker', 'Unknown')
      return company_name, company_ticker
  except (json.JSONDecodeError, KeyError):
      return 'Unknown', 'Unknown'

# Function to invoke Bedrock model
def invoke_bedrock_model(prompt,max_tokens=1000):
    bedrock_runtime = boto3.client('bedrock-runtime')
    request_body = {
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens": max_tokens,
      "messages": [
          {"role": "user", "content": prompt}
      ],
      "temperature": 0.1,
      "top_p": 0.9,
    }
  
    response = bedrock_runtime.invoke_model(
      modelId="anthropic.claude-3-haiku-20240307-v1:0",
      contentType="application/json",
      accept="application/json",
      body=json.dumps(request_body)
    )
    response_body = json.loads(response['body'].read().decode())
    return response_body['content'][0]['text']
def get_stock_ticker(input):
    # load company name & company tiker
    with open('tickers.csv', 'r') as file:
        company_data = file.read()        

    initial_prompt = f"""You are a financial data assistant. Extract company name and company ticker from input. 
            Rules:
            - Focus only on Vietnamese companies
            - If given name, provide ticker
            - If given ticker, provide name
            - If both given, confirm them
            - Use "None" for uncertain values
            <context> Vietnamese company list: {json.dumps(company_data)} </context>
            Input: {input}
            Output: JSON with keys 'company_name' and 'company_ticker' only.
            Respond with only the JSON object."""
    initial_response = invoke_bedrock_model(initial_prompt)

    company_name, company_ticker = parse_response(initial_response)    
    # load company data from file
    
    if company_name == 'None' or company_ticker == 'None':
        context_prompt = f"""Given:
            - Partial info: {{company_name: "{company_name}", company_ticker: "{company_ticker}"}}
            - Vietnamese company list: {json.dumps(company_data)}
            Task: Find the most likely Vietnamese company name and ticker. Use closest match if exact match unavailable for company name,
            with company ticker use strict match.
            Output JSON with 'company_name' and 'company_ticker'. Use "None" if unsure.
            Respond with only the JSON object."""
        context_response = invoke_bedrock_model(context_prompt)
        company_name, company_ticker = parse_response(context_response)
    with open("company.json", 'w') as file:
        file.write(str(json.dumps({'company_name': company_name, 'company_ticker': company_ticker})))

    return company_name, company_ticker

# get stock history of the company in 3 years
def get_stock_price(ticker, history=1000):
    with open("company.json", 'a') as file:
        file.write('get stock price for ticker: {ticker}')
    today = date.today()
    start_date = today - timedelta(days=history)
    stock = Vnstock().stock(symbol=ticker, source='VCI')
    data = stock.quote.history(start=start_date.strftime('%Y-%m-%d'),end=today.strftime('%Y-%m-%d'))
    return data

# Function to safely get data and handle exceptions
def safe_get_data(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error getting data: {e}")
        return pd.DataFrame()

# Function to get financial data
def get_financial_data(ticker):
    # Create a stock object for financial data
    stock_finance = Vnstock().stock(symbol=ticker, source='VCI')
    
    # Create a dictionary to store all dataframes
    company_data = {
        'Balance Sheet Yearly': safe_get_data(stock_finance.finance.balance_sheet, period='year', lang='en'),
        'Balance Sheet Quarterly': safe_get_data(stock_finance.finance.balance_sheet, period='quarter', lang='en'),
        'Income Statement Yearly': safe_get_data(stock_finance.finance.income_statement, period='year', lang='en'),
        'Income Statement Quarterly': safe_get_data(stock_finance.finance.income_statement, period='quarter', lang='en'),
        'Cash Flow Yearly': safe_get_data(stock_finance.finance.cash_flow, period='year', lang='en'),
        'Cash Flow Quarterly': safe_get_data(stock_finance.finance.cash_flow, period='quarter', lang='en'),
        'Financial Ratios Yearly': safe_get_data(stock_finance.finance.ratio, period='year', lang='en'),
        'Financial Ratios Quarterly': safe_get_data(stock_finance.finance.ratio, period='quarter', lang='en'),
    }
    return company_data

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
def get_recent_news(ticker):
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

def get_recent_stock_news(ticker):
    # get company name from ticker
    company = Vnstock().stock(symbol=ticker, source='TCBS').company
    company_name = company.profile()['company_name'][0]

    # Define the Google News search URL in Vietnamese
    search_url = f"https://www.google.com/search?q={company_name}+tin+tức&hl=vi&tbm=nws"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }  
    # Send a GET request to the search URL
    response = requests.get(search_url,headers=headers)
    #response.raise_for_status()  # Check for request errors
    
    # Parse the HTML content of the response
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all news article elements
    articles = soup.find_all('div', class_='BVG0Nb')
    
    # Extract and print the titles, URLs, and content of the articles
    content =""
    for article in articles[:5]:
        title = article.find('div', class_='mCBkyc').text
        link = article.find('a')['href']
        print(f"Title: {title}")
        print(f"Link: {link}")
        
        # Get the content of the news article
        content+= '\n\n' + get_article_content(link)
    return "Recent News:\n\n" + content

def get_article_content(url):
    try:
        response = requests.get(url)
        #response.raise_for_status()  # Check for request errors      
        soup = BeautifulSoup(response.text, 'html.parser')        
        # Extract the article text based on common tags (this may need adjustment)
        paragraphs = soup.find_all('p')
        content = ' '.join([p.text for p in paragraphs])       
        return content
    except Exception as e:
        return f"Could not retrieve content: {e}"


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
        You are CRobo Advisor, an AI financial analyst assisting with stock analysis and market insights. Please follow these guidelines:

        1. Provide expert financial market analysis, focusing on clarity and accuracy.
        2. Offer data-driven insights on market trends, stocks, and trading strategies.
        3. Explain concepts clearly, adapting to the user's level of expertise.
        4. When evaluating assets, provide detailed rationales for recommendations.
        5. Base advice on up-to-date market information. For your reference, today's date is 2024 July 12.
        6. Be transparent about uncertainties or limitations in your knowledge.
        7. Respond in Vietnamese.
        8. Tailor responses to each user's specific needs and questions.
        9. Use Markdown formatting, with bold text for key points.
        10. Utilize available tools for data gathering:
            - get company ticker: Extract company name and ticker from user query. 
            - get stock data: Retrieve stock information using company ticker. 
            - get recent stock news: Fetch recent stock news using company ticker.
            - get financial data: Obtain company financial data using company ticker. 

        When analyzing stocks, follow these steps:
        1. Use "get company ticker" to identify the company name and company ticker.
        2. Gather stock data with "get stock data", inputting the company ticker obtained in step 1.
        3. Retrieve recent stock news using "get recent stock news", inputting the company ticker.
        4. Obtain financial data with "get financial data", inputting the company ticker.
        5. Provide a detailed analysis based on the collected information, including numerical data and reasoning to support your conclusions.

        Format your response as follows:
        Question: the input question you must answer
        Thought: you should always think about what to do, Also try to follow steps mentioned above
        Action: the action to take, should be one of [get company ticker, get stock data, get recent stock news, get financial statements]
        Action Input: the input to the action
        Observation: the result of the action
        (Repeat Thought/Action/Observation as needed)
        Thought: I now know the final answer
        Final Answer: Comprehensive response to the user's question
        Here is user's input.

        Question: {input}
        Assistant: {agent_scratchpad}
    """
    zero_shot_agent.agent.llm_chain.prompt.template=prompt
    return zero_shot_agent

tools=[
    Tool(
        name="get company ticker",
        func=get_stock_ticker,
        description="Get the company name and company stock ticker, input the use question to it"
    ),
    Tool(
        name="get stock data",
        func=get_stock_price,
        description="Use when you are asked to evaluate or analyze a stock. This will output historic share price data. You should input the the company ticker to it "
    ),
    Tool(
        name="get recent stock news",
        func=get_recent_stock_news,
        description="Use this to fetch recent news about stocks"
    ),

    Tool(
        name="get financial data",
        func=get_financial_data,
        description="Use this to get balance sheet of the company. With the help of this data companys historic performance can be evaluaated. You should input company ticker to it"
    ) 
 

]

zero_shot_agent = initializeAgent()
if 'chat_history' not in st.session_state: 
    st.session_state.chat_history = [] 

def generate_response(prompt,st_callback):
    # Initialize the session state for messages if it doesn't exist
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    st.session_state['messages'].append({"role": "user", "content": prompt})

    response = zero_shot_agent({
            "input": prompt,
            "chat_history": st.session_state.chat_history,
         },
         callbacks=[st_callback]
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
        st_callback = StreamlitCallbackHandler(st.container())
        response_stream, query = generate_response(user_input,st_callback)
        st.session_state['past'].append(user_input)
        
 