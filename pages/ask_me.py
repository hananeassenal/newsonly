import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq

# Set up Streamlit page
st.set_page_config(page_icon="💬", layout="wide", page_title="chat with me")

# Check if the user is logged in
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("You need to be logged in to view this page.")
    st.write("[Login](login.py)")
    st.stop()

# Hardcoded Groq API key
groq_api_key = "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"

# Initialize Groq client with the API key
client = Groq(api_key=groq_api_key)

# Function to retrieve and process documents from URL
def retrieve_document_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            if soup.title:
                st.success(f"Document content retrieved and processed from {url}")
                return soup.get_text()
            else:
                st.error("Failed to find valid content in the document. Please check the URL.")
                return None
        else:
            st.error(f"Error retrieving content from {url}. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error retrieving content from {url}: {str(e)}")
        return None

# UI Layout
st.title("Groq Q&A Chatbot")
url = st.text_input("Enter URL of the document to analyze:")

if st.button("Retrieve and Analyze"):
    if url:
        document_content = retrieve_document_content(url)
        if document_content:
            st.session_state.document_content = document_content  # Store document content in session state
            st.success("Document content retrieved successfully.")
        else:
            st.warning("Failed to retrieve document content. Please check the URL.")
    else:
        st.warning("Please enter a valid URL.")

user_question = st.text_input("Ask a question about the document:")

if st.button("Get Answer"):
    if 'document_content' in st.session_state:
        try:
            chat_completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "user", "content": user_question},
                    {"role": "system", "content": "Document context: " + st.session_state.document_content}
                ],
                max_tokens=500,
                stream=True
            )
            full_answer = ""
            for chunk in chat_completion:
                if chunk.choices[0].delta.content:
                    full_answer += chunk.choices[0].delta.content
            st.write(full_answer)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please retrieve and process a document first.")
