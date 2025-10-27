import streamlit as st
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

"""
提供session能力
"""
def setDefaultEnv():
    if "base_url" not in st.session_state:
        st.session_state['base_url'] = os.getenv('OPENAI_BASE_URL')

    if "api_key" not in st.session_state:
        st.session_state['api_key'] = os.getenv('OPENAI_API_KEY')

def getBaseUrl():
    base_url = (
        st.session_state.base_url
        if "base_url" in st.session_state
        else "https://api.openai.com/v1"
    )
    return base_url

def getApiKey():
    api_key = (
        st.session_state.api_key
        if "api_key" in st.session_state and st.session_state.api_key != ""
        else None
    )
    return api_key