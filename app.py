# Now to define the Streamlit app
import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from urllib.parse import urljoin
from nltk.corpus import stopwords
from dotenv import load_dotenv
import os
import heapq

# Loading any necessary environment variables from .env file
load_dotenv()

# Download NLTK data
nltk.download('punkt')

# Summarize text
def summarize_text(text, num_sentences=10):
    sentences = nltk.sent_tokenize(text)
    summary = " ".join(sentences[:num_sentences])
    return summary

# Extract live URLs from the references section
def extract_live_urls(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    references_section = soup.find("span", {"id": "References"})
    if references_section:
        references = references_section.find_next("ul")
        if references:
            urls = [a['href'] for a in references.find_all('a', href=True)]
            return urls

    return []

# Extracts images
def extract_images(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # All image tags are called 'img'
    img_tags = soup.find_all('img')

    # Extracts image URLs
    image_urls = [urljoin(url, img['src']) for img in img_tags]

    return image_urls

# Call Function to communicate with my Wit.ai app
def wit_ai_response(message):
    # access_token = os.getenv('WIT_AI_ACCESS_TOKEN')
    token = st.secrets[wit]["QDG4IKACZ7H7UKCLOJQJZQ4MVPXXTURM"]
    if not token:
        return 'Error: Access token is not set.'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'v': '20220217',  # API version date
        'q': message
    }
    
    response = requests.get('https://api.wit.ai/message', headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        # Process the response as needed, here we'll just return the message text
        return data.get('msg', 'Sorry, I didn\'t understand that.')
    else:
        return 'Error: Could not contact Wit.ai.'

# Main function
def main():
    st.title("Wikipedia Article Analyzer")

    # Sidebar for user input (if any)
    st.sidebar.header("User Input")
    url_input = st.sidebar.text_input("Enter Wikipedia URL:", "https://en.wikipedia.org/wiki/Statistics")

    # Main content
    if st.button("Analyze"):
        # Extract and summarize the text
        response = requests.get(url_input)
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find("div", class_="mw-parser-output")
        paragraphs = content.find_all("p")
        full_text = "\n".join([p.text for p in paragraphs])
        summary = summarize_text(full_text)

        # Display summary
        st.subheader("Summary:")
        st.write(summary)

        # Extract live URLs from the references section
        live_urls = extract_live_urls(url_input)
        st.subheader("Live URLs from References:")
        for url in live_urls:
            st.write(url)

        # Extract images
        image_urls = extract_images(url_input)
        st.subheader("Image URLs:")
        for idx, url in enumerate(image_urls, start=1):
            # st.write(url)
            st.image(url, caption=f"Image {idx}", use_column_width=True)
            
    # The user's method to talk to the Chatbot (Chatbot functionality)
    st.sidebar.header("Beep Boop: Talk with me")
    user_question = st.sidebar.text_input("Ask a question about the article:")
    
    if st.sidebar.button("Get Response"):
        if user_question:
            response = wit_ai_response(user_question)
            st.sidebar.write("Bot:", response)

if __name__ == "__main__":
    main()
