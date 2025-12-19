import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY not found. Please create a `.env` file with your API key:")
    st.code("OPENAI_API_KEY=sk-your-api-key-here", language="bash")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Chat App",
    page_icon="💬",
    layout="centered",
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
    }
    .stChatInputContainer {
        padding-top: 1rem;
    }
    [data-testid="stSidebarContent"] {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Model selection
    model = st.selectbox(
        "Model",
        options=["gpt-5-mini-2025-08-07"],
        index=0,
        help="Select the OpenAI model to use"
    )
    
    st.divider()
    
    # New chat button
    if st.button("🗑️ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.previous_response_id = None
        st.rerun()

# Main chat interface
st.title("💬 Chat")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "previous_response_id" not in st.session_state:
    st.session_state.previous_response_id = None

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Build request parameters for Responses API
        request_params = {
            "model": model,
            "input": prompt,
            "stream": True,
        }
        
        # Use previous_response_id for stateful conversation
        if st.session_state.previous_response_id:
            request_params["previous_response_id"] = st.session_state.previous_response_id
        
        # Create streaming response using Responses API
        stream = client.responses.create(**request_params)
        
        # Stream the response
        response_container = st.empty()
        full_response = ""
        response_id = None
        
        for event in stream:
            # Capture the response ID for stateful conversation
            if hasattr(event, 'id') and event.id:
                response_id = event.id
            
            # Handle different event types
            if event.type == "response.output_text.delta":
                full_response += event.delta
                response_container.markdown(full_response + "▌")
            elif event.type == "response.completed":
                if hasattr(event, 'response') and event.response:
                    response_id = event.response.id
        
        response_container.markdown(full_response)
        
        # Store response ID for next turn
        if response_id:
            st.session_state.previous_response_id = response_id
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

