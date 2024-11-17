import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from urllib.parse import urljoin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from fuzzywuzzy import process
from transformers import pipeline
from PIL import Image
from io import BytesIO
import time

# Download NLTK data
nltk.download('punkt')

# Initialize Hugging Face pipelines (keeping these models cached)
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad", tokenizer="distilbert-base-cased", framework="pt")
generator = pipeline("text-generation", model="tiiuae/falcon-40b-instruct")

# Global variables
article_text = ""
conversation_history = []

# Simple FAQ dictionary
faq = {
    "what is statistics?": "Statistics is the study of data: how to collect, summarize and interpret it.",
    "what is machine learning?": "Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to learn from data.",
}

# Add Hugging Face API token (for Falcon-40B-Instruct and Image Generation)
HF_API_TOKEN = st.secrets["hug"]["NOTIMPORTANT"]  # Streamlit secrets for sensitive data
if not HF_API_TOKEN:
    raise ValueError("Hugging Face API token is missing!")

HF_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-40b-instruct"
IMAGE_GEN_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"

# Cache heavy operations like article fetching and image generation
@st.cache_data
def fetch_article(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find("div", class_="mw-parser-output")
    paragraphs = content.find_all("p")
    return "\n".join([p.text for p in paragraphs])

@st.cache_resource
def generate_image_cached(prompt, hf_api_token):
    headers = {
        "Authorization": f"Bearer {hf_api_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(IMAGE_GEN_URL, headers=headers, json={"inputs": prompt})

    if response.status_code == 200:
        image_url = response.json()[0]["url"]
        image_response = requests.get(image_url)
        img = Image.open(BytesIO(image_response.content))
        return img
    else:
        st.sidebar.write(f"Error generating image: {response.status_code}, {response.text}")
        return None

# Helper function to query Falcon-40B-Instruct for general questions
def query_falcon_model(question):
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(HF_API_URL, headers=headers, json={"inputs": question})

    if response.status_code == 200:
        answer = response.json()[0]['generated_text']
        return answer
    else:
        return f"Sorry, there was an error: {response.status_code}"

# Function to answer from the article using Hugging Face's QA pipeline
def answer_from_article(question):
    global article_text
    if article_text:
        result = qa_pipeline({
            "context": article_text,
            "question": question
        })
        return result["answer"]
    else:
        return "No article loaded to answer from."

# Summarize text
def summarize_text(text, num_sentences=10):
    sentences = nltk.sent_tokenize(text)
    summary = " ".join(sentences[:num_sentences])  # Limit to the number of sentences specified
    return summary

# Extract images from the article
def extract_images(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    img_tags = soup.find_all('img')
    image_urls = [urljoin(url, img['src']) for img in img_tags if img.has_attr('src')]
    return image_urls

# Fuzzy matching for FAQs
def get_faq_answer(question):
    question_lower = question.lower().strip()
    closest_match = process.extractOne(question_lower, faq.keys())
    if closest_match and closest_match[1] > 70:  # Threshold for fuzzy match confidence
        return faq[closest_match[0]]
    return None

# Handle ambiguous questions
def handle_ambiguous_question(question):
    ambiguous_keywords = ["could you elaborate", "what do you mean", "please clarify"]
    for keyword in ambiguous_keywords:
        if keyword in question.lower():
            return "Could you please clarify your question?"
    return None

# Handle user question (both article-based and general)
def handle_user_question(user_question):
    normalized_question = user_question.lower().strip()

    # First check if it's an FAQ
    faq_answer = get_faq_answer(user_question)
    if faq_answer:
        return faq_answer

    # Handle ambiguous questions
    ambiguous_response = handle_ambiguous_question(user_question)
    if ambiguous_response:
        return ambiguous_response

    # If article text is available, try answering from the article
    if article_text:
        article_response = answer_from_article(user_question)
        if article_response != "No article loaded to answer from.":
            return article_response
    
    # If it's a general question, ask Falcon-40B-Instruct
    return query_falcon_model(user_question)

# Save conversation history for context
def append_to_history(user_question, bot_answer):
    conversation_history.append({
        "user": user_question,
        "bot": bot_answer
    })
    # Keep history size manageable
    if len(conversation_history) > 10:
        conversation_history.pop(0)  # Remove the earliest entry

def get_conversation_history():
    return " ".join([f"User: {item['user']} Bot: {item['bot']}" for item in conversation_history])

# Main function
def main():
    st.title("Wikipedia Article Analyzer")

    # Sidebar for user input (if any)
    st.sidebar.header("User Input")
    url_input = st.sidebar.text_input("Enter Wikipedia URL:", "https://en.wikipedia.org/wiki/Statistics")

    # Main content
    with st.spinner('Analyzing article...'):
        if st.button("Analyze"):
            global article_text
            try:
                article_text = fetch_article(url_input)  # Fetch article with caching
                summary = summarize_text(article_text)

                st.subheader("Summary:")
                st.write(summary)

                image_urls = extract_images(url_input)
                st.subheader("Image URLs:")
                for idx, url in enumerate(image_urls, start=1):
                    st.image(url, caption=f"Image {idx}", use_column_width=True)
                    st.write(url)

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # User's method to talk to the chatbot
    st.sidebar.header("Beep Boop: Talk with me")
    user_question = st.sidebar.text_input("Ask a question:")

    if user_question:
        with st.spinner("Processing your question..."):
            response = handle_user_question(user_question)
            st.sidebar.write("Bot:", response)

            # Save the conversation history for context in future responses
            append_to_history(user_question, response)

    # User's method to generate images (Move this to a separate section in the sidebar)
    st.sidebar.header("Image Generation")
    image_prompt = st.sidebar.text_input("Enter a prompt to generate an image:")

    if image_prompt:
        with st.spinner("Generating image..."):
            image = generate_image_cached(image_prompt, HF_API_TOKEN)
            if image:
                st.image(image, caption=f"Generated image for: {image_prompt}", use_column_width=True)
            else:
                st.sidebar.write("Sorry, there was an error generating the image.")

if __name__ == "__main__":
    main()
