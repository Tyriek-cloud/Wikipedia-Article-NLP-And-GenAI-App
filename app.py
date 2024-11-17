import streamlit as st
import requests
from bs4 import BeautifulSoup
from nltk import sent_tokenize
from fuzzywuzzy import process
from transformers import pipeline
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

# Initialize Hugging Face pipelines in session state
if "qa_pipeline" not in st.session_state:
    st.session_state.qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad", tokenizer="distilbert-base-cased", framework="pt")
if "generator" not in st.session_state:
    st.session_state.generator = pipeline("text-generation", model="tiiuae/falcon-40b-instruct")

qa_pipeline = st.session_state.qa_pipeline
generator = st.session_state.generator

@st.cache_data
def load_and_summarize_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find("div", class_="mw-parser-output")
        paragraphs = content.find_all("p")
        full_text = "\n".join([p.text for p in paragraphs])
        summary = summarize_text(full_text)
        return full_text, summary
    except Exception as e:
        return None, str(e)

def async_generate_image(prompt):
    with ThreadPoolExecutor() as executor:
        future = executor.submit(generate_image, prompt)
        return future.result()

def main():
    st.title("Wikipedia Article Analyzer")

    # User input
    url_input = st.sidebar.text_input("Enter Wikipedia URL:", "https://en.wikipedia.org/wiki/Statistics")

    with st.spinner('Analyzing article...'):
        if st.button("Analyze"):
            article_text, summary = load_and_summarize_article(url_input)
            if article_text:
                st.subheader("Summary:")
                st.write(summary)
            else:
                st.error("Error analyzing article.")
                
    # User interactions
    user_question = st.sidebar.text_input("Ask a question:")

    if user_question:
        response = handle_user_question(user_question)
        st.sidebar.write("Bot:", response)

    image_prompt = st.sidebar.text_input("Enter a prompt to generate an image:")
    if image_prompt:
        st.sidebar.write(f"Generating image for: {image_prompt}...")
        image = async_generate_image(image_prompt)
        if image:
            st.image(image, caption=f"Generated image for: {image_prompt}", use_column_width=True)

if __name__ == "__main__":
    main()
