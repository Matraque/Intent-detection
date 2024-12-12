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
            del st.session_state["password"]
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

import streamlit as st
import json
import requests
import os

# Set a universal page config at the top
st.set_page_config(
    page_title="Poly Intent Detection",
    page_icon="🛣️",
    layout="centered"
)

# Load data from JSON for the first app
def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# App function for the first app
def app1():
    data = load_data('data.json')

    st.title("Intent-Workflow Documentation")
    st.write("""
        Présentation de la relation entre une intention et son workflow, le système prompt et les tools associés à chaque workflow et l'API prompt associé à chaque tool.
    """)

    selected_intention = st.selectbox(
        "Select an Intention", 
        [i['name'] for i in data['intentions']]
    )

    # Display the selected intention's details
    for intention in data['intentions']:
        if intention['name'] == selected_intention:
            st.header(f"Intent: {intention['name']}")
            st.write(f"**Description:** {intention['description']}")

            category = intention['category']
            st.subheader(f"Workflow : {category['name']}")
            st.write(f"**System Prompt:** {category['system_prompt']}")

            st.subheader("Tools")
            for tool in category['tools']:
                with st.expander(tool['name']):
                    st.write(f"**API Prompt:** {tool['api_prompt']}")

# Load tools for the second app
with open("tools-intent-detection.json", "r", encoding="utf-8") as file:
    tools = json.load(file)

# API configuration for the second app
url = st.secrets["url"]
headers = {
    'api-key': st.secrets["key"],
    'Content-Type': 'application/json'
}

# Mapping function to class for the second app
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

# Function to get model response for the second app
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
    
    data_request = {
        "model": "gpt-4o",
        "messages": messages,
        "tools": tools,
        "tool_choice": "required"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data_request))
    
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

# App function for the second app
def intent_detection():
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
                    <p><strong>Workflow:</strong> {category}</p>
                </div>
            """, unsafe_allow_html=True)
        
    st.markdown('<p style="text-align: right; color: gray; font-size: 0.8em;">Fait avec ❤️ par Mathieu</p>', unsafe_allow_html=True)

# Main function to run the combined app
def main():
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Intentions", "Playground"])

    if page == "Intentions":
        app1()
    elif page == "Playground":
        intent_detection()

# Run the app
if __name__ == "__main__":
    main()