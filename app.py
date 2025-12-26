import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- APP CONFIG ---
st.set_page_config(page_title="Investment Dashboard", layout="wide")

# --- CONNECT TO DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stMetricValue"] { color: #2e7d32; font-size: 1.8rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #555; font-size: 1rem; }
    .stButton>button { 
        background-color: #2e7d32; 
        color: white; border-radius: 8px; border: none; height: 3em; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background-color: #1b5e20; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: LOGIN & ACCESS ---
st.sidebar.title("🔐 User Access")
user_name = st.sidebar.text_input("Username", value="").strip()
password = st.sidebar.text_input("Password", type="password") # Simple check for friends

# Security Check (Optional: Add common password for friends)
if user_name and password == "invest123": # You can change this password
    
    # 1. LOAD DATA FROM CLOUD
    try:
        all_data = conn.read(ttl=0)
    except:
        all_data = pd.DataFrame(columns=["User", "Date", "Cashflow"])

    # 2. FILTER FOR USER
    user_data = all_data[all_data["User"] == user_
