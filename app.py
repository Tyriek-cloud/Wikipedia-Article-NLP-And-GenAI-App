import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO

# Download NLTK data
nltk.download('punkt')

# Global variable for article text
article_text = ""

# Add Hugging Face API token (for Image Generation)
HF_API_TOKEN = st.secrets["hug"]["NOTIMPORTANT"]  # Streamlit secrets for sensitive data
if not HF_API_TOKEN:
    raise ValueError("Hugging Face API token is missing!")

IMAGE_GEN_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"

# Cache heavy operations like article fetching
@st.cache_data
def fetch_article(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find("div", class_="mw-parser-output")
    paragraphs = content.find_all("p")
    return "\n".join([p.text for p in paragraphs])

def generate_image_cached(prompt, hf_api_token):
    headers = {
        "Authorization": f"Bearer {hf_api_token}",
        "Content-Type": "application/json",
    }
    try:
        # Make the request to Hugging Face API
        response = requests.post(IMAGE_GEN_URL, headers=headers, json={"inputs": prompt})

        # Handle successful response
        if response.status_code == 200:
            image_url = response.json()[0]["url"]
            image_response = requests.get(image_url)
            img = Image.open(BytesIO(image_response.content))
            return img
        else:
            st.sidebar.error(f"Error generating image: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        st.sidebar.error(f"An error occurred: {str(e)}")
        return None

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
