
import streamlit as st
from google import genai

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

for model in client.models.list():
    if "flash" in model.name.lower():
        print(model.name)
