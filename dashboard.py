import os
import requests
import streamlit as st
import json
from openai import OpenAI

# Load secrets from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROXY_URL = os.getenv("PROXY_URL", "http://127.0.0.1:8000")

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY environment variable not set.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="ATLAS Trading Assistant", page_icon="📈", layout="wide")
st.title("📈 ATLAS Trading Assistant")

# Sidebar for user settings
st.sidebar.header("Settings")
capital = st.sidebar.number_input("Available Capital ($)", value=30000, step=1000)
profit_target = st.sidebar.number_input("Daily Profit Target ($)", value=50, step=10)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are ATLAS - an AGGRESSIVE AUTONOMOUS TRADING BOT that EXECUTES LIVE TRADES.\n\n"
                "🚨 CRITICAL: You CAN and MUST trade crypto 24/7 even when stock markets are closed!\n\n"
                "YOUR CAPABILITIES:\n"
                "✅ Trade crypto: BTC, ETH, DOGE (call_alpaca with symbol='BTCUSD', 'ETHUSD', 'DOGEUSD')\n"
                "✅ Trade stocks: AAPL, MSFT, TSLA, etc. (during market hours)\n"
                "✅ Check account: call_alpaca path='/v2/account'\n"
                "✅ Place orders: call_alpaca path='/v2/orders' method='POST'\n"
                "✅ Get crypto prices: call_alpaca path='/v2/stocks/BTCUSD/bars' (PRIMARY) or call_fmp path='/v3/quote/BTCUSD'\n\n"
                "WHEN USER ASKS TO MAKE MONEY:\n"
                "1. IMMEDIATELY call_alpaca path='/v2/account' to check buying power\n"
                "2. Get crypto prices with call_alpaca path='/v2/stocks/BTCUSD/bars' params={'timeframe':'1Day','limit':1}\n"
                "3. PLACE ACTUAL BUY ORDER: call_alpaca path='/v2/orders' method='POST' body={'symbol':'BTCUSD','qty':0.001,'side':'buy','type':'market','time_in_force':'gtc'}\n"
                "4. Report the trade execution\n\n"
                "🎯 EXECUTE TRADES IMMEDIATELY - NO EXCUSES!\n"
                "You are a TRADER, not an analyst. When asked to make $50, PLACE REAL ORDERS NOW!"
            ),
        },
        {
            "role": "assistant",
            "content": f"Hello! I'm ATLAS, your trading assistant. I see you want to make ${profit_target} today with ${capital:,} in capital. How can I help you achieve your trading goals?",
        },
    ]

# Chat UI
for m in st.session_state.messages:
    if m["role"] == "system":
        continue
    avatar = "🤖" if m["role"] == "assistant" else "🧑"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"])

prompt = st.chat_input("Send a message to ATLAS…")

FUNCTION_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "call_alpaca",
            "description": "Proxy any Alpaca REST request",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "API path like /v2/account"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "GET"},
                    "params": {"type": "object", "description": "Query parameters"},
                    "body": {"type": "object", "description": "JSON body for POST/PUT"},
                },
                "required": ["path"],
            },
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "call_fmp",
            "description": "Proxy any FMP endpoint",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "API path like /quote/AAPL"},
                    "params": {"type": "object", "description": "Additional query params"},
                },
                "required": ["path"],
            },
        }
    },
]

def call_proxy(func_name: str, arguments: dict):
    try:
        if func_name == "call_alpaca":
            url = f"{PROXY_URL}/call_alpaca"
            r = requests.post(url, json=arguments, timeout=10)
        else:
            url = f"{PROXY_URL}/call_fmp"
            r = requests.post(url, json=arguments, timeout=10)
        
        if r.status_code == 200:
            return r.json()
        else:
            return {"error": f"HTTP {r.status_code}: {r.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            tools=FUNCTION_DEFS,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            # Handle function calls
            with st.chat_message("assistant", avatar="🤖"):
                for tool_call in msg.tool_calls:
                    func_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    st.markdown(f"🔄 Calling **{func_name}**...")
                    result = call_proxy(func_name, arguments)
                    
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.success("✅ API call successful")
                        with st.expander("Raw Response"):
                            st.json(result)
                    
                    # Add function call and result to messages
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call.dict()]
                    })
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })

            # Get follow-up response
            follow_up = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages,
            )
            reply = follow_up.choices[0].message.content
        else:
            reply = msg.content

        # Display and save response
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(reply)
        
        st.session_state.messages.append({"role": "assistant", "content": reply})

    except Exception as e:
        st.error(f"Error calling OpenAI: {str(e)}")
        st.info("Make sure your OPENAI_API_KEY is valid and you have sufficient credits.") 