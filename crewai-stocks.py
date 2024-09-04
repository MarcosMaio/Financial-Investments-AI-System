# Import das Libs
import os
from datetime import datetime, timedelta, date

import yfinance as yf

import numpy as np

np.float_ = np.float64

import requests
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults

from crewai_tools import tool

import streamlit as st

# Carregando variáveis de ambiente
load_dotenv()

# Importando o modelo de linguagem
openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key is None:
    raise ValueError("OPENAI_API_KEY não encontrada. Verifique seu arquivo .env")

llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=openai_api_key)

# Função para converter datas
def convert_dates(start_date_str, end_date_str):
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else (date.today() - timedelta(days=365)).date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today().date()
        return start_date, end_date
    except ValueError as e:
        print(f"Invalid date format: {e}")
        return date.today() - timedelta(days=365), date.today()  # Valores padrão

# Função para buscar preços das ações e retornar um resumo
def fetch_stock_price(ticker, start_date_str, end_date_str):
    try:
        start_date, end_date = convert_dates(start_date_str, end_date_str)
        start_date_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, (datetime, date)) else start_date
        end_date_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, (datetime, date)) else end_date
        
        # Baixar os dados das ações
        stock = yf.download(ticker, start=start_date_str, end=end_date_str)
        if stock.empty:
            raise ValueError(f"No price data found for {ticker}.")
        
        # Criar um resumo dos dados
        stock_summary = {
            'ticker': ticker,
            'start_price': stock['Adj Close'].iloc[0],
            'end_price': stock['Adj Close'].iloc[-1],
            'high': stock['Adj Close'].max(),
            'low': stock['Adj Close'].min(),
            'trend': 'up' if stock['Adj Close'].iloc[-1] > stock['Adj Close'].iloc[0] else 'down' if stock['Adj Close'].iloc[-1] < stock['Adj Close'].iloc[0] else 'stable'
        }
        return stock_summary
    except Exception as e:
        print(f"Error fetching stock data for {ticker}: {str(e)}")
        return None

# Criando Finance Tool
finance_tool = Tool(
    name="Fetch Stock Prices",
    description="Fetch stock prices from a specific date range for a company",
    func=lambda ticker, start_date_str, end_date_str: fetch_stock_price(
        ticker, 
        start_date_str, 
        end_date_str
    )
)

def stock_price_task(ticker, start_date_str, end_date_str):
    return fetch_stock_price(ticker, start_date_str, end_date_str)

stockPriceAnalyst = Agent(
    role="Senior Stock Price Analyst",
    goal="Find the {ticker} company stock price and analyze trends",
    backstory="""You're highly experienced in analyzing the price of a specific stock
    and make predictions about its future price.""",
    verbose=True,
    llm=llm,
    max_iter=5,
    memory=True,
    tools=[finance_tool],
    allow_delegation=False
)

getStockPrice = Task(
    description="Analyze the stock {ticker} company price history from {start_date} to {end_date} and create a trend analysis of up, down or stable",
    expected_output="""Specify the current trend stock price - up, down or stable. eg. stock='AAPL, price UP'""",
    agent=stockPriceAnalyst,
    func=stock_price_task
)

# Configuração da API da Finnhub
finnhub_api_key = os.getenv("FINNHUB_API_KEY")

def fetch_finnhub_data(ticker):
    base_url = f"https://finnhub.io/api/v1/stock/metric?symbol={ticker}&metric=all&token={finnhub_api_key}"
    response = requests.get(base_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching Finnhub data: {response.status_code}")
        return None

def risk_assessment(ticker):
    finnhub_data = fetch_finnhub_data(ticker)
    
    if not finnhub_data:
        risks = {
            "market_risk": "High",
            "operational_risk": "Medium",
            "regulatory_risk": "Low",
            "esg_risk": "Medium"
        }
        analysis = "Data not available, default risk values applied."
    else:
        beta = finnhub_data["metric"].get("beta", 1)  
        market_risk = "High" if beta > 1 else "Low"
        
        operational_risk = "Medium"  
        regulatory_risk = "Low"
        esg_risk = "Medium"
        
        risks = {
            "market_risk": market_risk,
            "operational_risk": operational_risk,
            "regulatory_risk": regulatory_risk,
            "esg_risk": esg_risk
        }
        
        analysis = f"Market risk based on beta is {market_risk}. Additional analysis needed for other risks."

    return risks, analysis

risk_tool = Tool(
    name="Risk Assessment",
    description="Evaluates various risks associated with investing in a specific company",
    func=lambda ticker, *args: risk_assessment(ticker)
)

riskAnalyst = Agent(
    role="Risk Analyst",
    goal="Identify and evaluate the various risks associated with investing in the {ticker} company",
    backstory="""You are a seasoned risk analyst, proficient in identifying and assessing market, operational, regulatory, and ESG risks that could impact investment decisions.""",
    verbose=True,
    llm=llm,
    max_iter=5,
    memory=True,
    tools=[risk_tool], 
    allow_delegation=False
)

get_risks = Task(
    description="Evaluate the different types of risks associated with investing in {ticker}.",
    expected_output="""A comprehensive risk assessment report detailing market, operational, regulatory, and ESG risks.""",
    agent=riskAnalyst
)

# Ferramenta de Busca

@tool('DuckDuckGoSearch')
def search(search_query: str):
    """Search the web for information on a given topic"""
    search_tool = DuckDuckGoSearchResults(backend='news', num_results=10)
    return search_tool(search_query)

newsAnalyst = Agent(
    role="Stock News Analyst",
    goal="""Create a short summary of the market news related to the stock {ticker} company about the date history from {start_date} to {end_date}. Specify the current trend - up, down or sideways with the news context. For each requested stock asset, specify a number between 0 and 100, where 0 is extreme fear and 100 is extreme greed.""",
    backstory="""
    You're highly experienced in analyzing the market trends and news and have tracked assets for more than 10 years.
    You're also a master-level analyst in traditional markets and have a deep understanding of human psychology.
    You understand news, their titles, and information, but you look at those with a healthy dose of skepticism.
    You also consider the source of the news articles.
    """,
    verbose=True,
    llm=llm,
    max_iter=5,
    memory=True,
    tools=[search],
    allow_delegation=False
)

get_news = Task(
    description= """Take the stock and always include BTC to it (if not requested).
    Use the search tool to search each one individually. 

    Use the date history from {start_date} to {end_date}.

    Compose the results into a helpful report""",
    expected_output = """A summary of the overall market and one sentence summary for each requested asset. 
    Include a fear/greed score for each asset based on the news. Use format:
    <STOCK ASSET>
    <SUMMARY BASED ON NEWS>
    <TREND PREDICTION>
    <FEAR/GREED SCORE>
""",
    agent= newsAnalyst
)

stockAnalystWrite = Agent(
    role = "Senior Stock Analysts Writer",
    goal= """Analyze the trends in price, risk analysis, and news and write an insightful, compelling, and informative 3-paragraph long newsletter based on the stock report and price trend.""",
    backstory= """You're widely accepted as the best stock analyst in the market. You understand complex concepts and create compelling stories
    and narratives that resonate with wider audiences. 

    You understand macro factors and combine multiple theories - e.g., cycle theory and fundamental analyses. 
    You're able to hold multiple opinions when analyzing anything.
""",
    verbose = True,
    llm=llm,
    max_iter = 10,
    memory=True,
    allow_delegation = True
)

writeAnalyses = Task(
    description = """Use the stock price trend, risk analysis, and stock news report to create a comprehensive analysis and write the newsletter about the specific company.
    Focus on the stock price trend, news, fear/greed score, and risk assessment. What are the near future considerations?
    Include the previous analyses of stock trend, news summary, and detailed risk assessment in your final report.
""",
    expected_output= """An eloquent 3 paragraphs newsletter formatted as markdown in an easy-to-read manner. It should contain:

    - 3 bullet executive summary 
    - Introduction - set the overall picture and spark interest
    - Main part - provides the core analysis including the news summary, risk assessment, and fear/greed scores
    - Summary - key facts and concrete future trend prediction - up, down, or sideways.
    Avoid any signatures or author names.
""",
    agent = stockAnalystWrite,
    context = [getStockPrice, get_news, get_risks]
)


crew = Crew(
    agents = [stockPriceAnalyst, newsAnalyst, riskAnalyst, stockAnalystWrite],
    tasks = [getStockPrice, get_news, get_risks, writeAnalyses],
    verbose = True,
    process= Process.hierarchical,
    full_output=True,
    share_crew=False,
    manager_llm=llm,
    max_iter=10
)

companies = {
    "Select a company": "",
    "Apple Inc.": "AAPL",
    "Microsoft Corp.": "MSFT",
    "Google LLC": "GOOGL",
    "Amazon.com Inc.": "AMZN",
    "Tesla Inc.": "TSLA",
    "Meta Platforms Inc.": "META",
    "NVIDIA Corporation": "NVDA",
    "Berkshire Hathaway Inc.": "BRK.B",
    "Johnson & Johnson": "JNJ",
    "Visa Inc.": "V",
    "Procter & Gamble Co.": "PG",
    "Walmart Inc.": "WMT",
    "UnitedHealth Group Incorporated": "UNH",
    "Mastercard Incorporated": "MA",
    "The Home Depot, Inc.": "HD",
    "Pfizer Inc.": "PFE",
    "Cisco Systems, Inc.": "CSCO",
    "IBM Corporation": "IBM",
    "Intel Corporation": "INTC",
    "Adobe Inc.": "ADBE",
    "Oracle Corporation": "ORCL",
    "Salesforce.com Inc.": "CRM",
    "PayPal Holdings Inc.": "PYPL",
    "Bank of America Corp": "BAC",
    "Walt Disney Company": "DIS",
    "Netflix Inc.": "NFLX",
    "CVS Health Corporation": "CVS",
    "AbbVie Inc.": "ABBV",
    "Texas Instruments Incorporated": "TXN",
    "Qualcomm Incorporated": "QCOM",
    "General Electric Company": "GE",
    "Wells Fargo & Co": "WFC",
    "Verizon Communications Inc.": "VZ",
    "Shopify Inc.": "SHOP",
    "Uber Technologies Inc.": "UBER",
    "Spotify Technology S.A.": "SPOT",
    "Snap Inc.": "SNAP",
    "Square Inc.": "SQ",
    "Zoom Video Communications Inc.": "ZM",
    "Slack Technologies Inc.": "WORK",
    "Twitter Inc.": "TWTR"
}

# Configuração da interface

def run_research():
    st.sidebar.header('Company Research Tool')
    st.sidebar.write("Select a company from the dropdown menu to run the research.")

    with st.sidebar:
        st.header('Enter the company name to research')

        with st.form(key='research_form'):
            company_name = st.selectbox("Select the company", list(companies.keys()))
            start_date = st.date_input("Start Date", datetime.now().date() - timedelta(days=366))
            end_date = st.date_input("End Date", datetime.now().date())
            submit_button = st.form_submit_button(label="Run Research")

    if submit_button:
        if not company_name or companies[company_name] == "":
            st.error("Please select a company")
            return 

        if end_date < start_date:
            st.error("End date should be after the start date")
            return  

        today = datetime.now().date()
        if end_date > today or start_date > today:
            st.error("Dates should be before today")
            return 

        ticker = companies[company_name]
        
        # Executa o processo do Crew
        try:
            results = crew.kickoff(inputs={
                'ticker': ticker,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            })
            
            # Exibir o resultado na seção principal
            st.header(f"Research Results for {company_name} ({ticker})")
            st.write(results['final_output'])

        except Exception as e:
            st.error(f"An error occurred during research: {str(e)}")
            
            
run_research()