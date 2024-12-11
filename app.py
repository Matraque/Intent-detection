import streamlit as st
import requests
import os
import json
import hmac

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.
# Load tools

# Load tools
with open("tools-intent-detection.json", "r", encoding="utf-8") as file:
    tools = json.load(file)

# API configuration
url = 'https://openai-dev-fra-001.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21'
headers = {
    'api-key': os.getenv('API_KEY'),
    'Content-Type': 'application/json'
}

# Mapping function to class
function_mapping = {
    "Creation_dossier_kbis": 'POST',
    "Redaction_non_juridique": 'DRAFT',
    "Redaction_juridique": '0',
    "Resume": '0',
    "Salutations": 'DRAFT',
    "Traduction": 'DRAFT',
    "Information_utilisateur": 'GET',
    "Information_dossier": 'GET',
    "Information_personne_societe": 'GET',
    "Autre_demande": '0'
}

def get_model_response(user_prompt):
    messages = [
        {
            "role": "system",
            "content": ""
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]
    
    data = {
        "model": "gpt-4o",
        "messages": messages,
        "tools": tools,
        "tool_choice": "required"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}", "0"
    else:
        response_data = response.json()
        if 'choices' in response_data:
            reply = response_data["choices"][0]["message"]
            if 'tool_calls' in reply and len(reply['tool_calls']) > 0:
                function_name = reply['tool_calls'][0]['function']['name']
                category = function_mapping.get(function_name, "0")
                return function_name, category
            else:
                return "No function called", "0"
        else:
            return "Unexpected response format.", "0"

# Set page configuration
st.set_page_config(
    page_title="Intent Detection Playground",
    page_icon="🔍",
    layout="centered"
)

# Apply custom CSS for styling
st.markdown(
    """
    <style>
    :root {
        --background-color: #f2f2f2;
        --text-color: #222222;
        --input-background: #e0e0e0;
        --button-background: #4caf50;
        --button-text-color: white;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --background-color: #222222;
            --text-color: #e0e0e0;
            --input-background: #444444;
        }
    }
    body {
        background-color: var(--background-color);
        color: var(--text-color);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stTextInput > div > div > input {
        background-color: var(--input-background);
        border: 1px solid #666;
        border-radius: 5px;
        padding: 10px;
    }
    .stButton > button {
        background-color: var(--button-background);
        color: var(--button-text-color);
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .result-container {
        background-color: var(--input-background);
        color: var(--text-color);
        border-radius: 5px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
    }
    h1 {
        text-align: center;
        color: var(--text-color);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Main content
st.markdown("# Intent Detection Playground", unsafe_allow_html=True)

# Create a form for user input and submit button
with st.form(key='intent_form'):
    user_prompt = st.text_input("Enter your prompt:", placeholder="Enter your prompt here")
    submitted = st.form_submit_button("Submit")

# Display results in a container
if submitted:
    with st.spinner("Processing..."):
        intention, category = get_model_response(user_prompt)
        st.markdown(f"""
            <div class="result-container">
                <h3>Results:</h3>
                <p><strong>Intention:</strong> {intention}</p>
                <p><strong>Category:</strong> {category}</p>
            </div>
        """, unsafe_allow_html=True)