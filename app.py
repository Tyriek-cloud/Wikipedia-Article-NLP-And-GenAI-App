import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO

# Download NLTK data
nltk.download('punkt')

# Global variable
article_text = ""

# Add Hugging Face API token (for Image Generation)
HF_API_TOKEN = st.secrets["hug"]["NOTIMPORTANT"]
if not HF_API_TOKEN:
    raise ValueError("Hugging Face API token is missing!")
IMAGE_GEN_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"

# Summarize text
def summarize_text(text, num_sentences=10):
    sentences = nltk.sent_tokenize(text)
    summary = " ".join(sentences[:num_sentences])
    return summary

# Extract images from the article
def extract_images(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    img_tags = soup.find_all('img')
    image_urls = [urljoin(url, img['src']) for img in img_tags if img.has_attr('src')]
    return image_urls

# Generate an image from a prompt using Hugging Face's Stable Diffusion
def generate_image(prompt):
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    # Request the image generation
    response = requests.post(IMAGE_GEN_URL, headers=headers, json={"inputs": prompt})

    if response.status_code == 200:
        # Extract image URL from the response
        image_url = response.json()[0]["url"]
        image_response = requests.get(image_url)
        img = Image.open(BytesIO(image_response.content))
        return img
    else:
        st.sidebar.write(f"Error generating image: {response.status_code}, {response.text}")
        return None

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
                response = requests.get(url_input)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                content = soup.find("div", class_="mw-parser-output")
                paragraphs = content.find_all("p")
                full_text = "\n".join([p.text for p in paragraphs])
                article_text = full_text
                summary = summarize_text(full_text)

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
        st.sidebar.write(f"Generating image for prompt: {image_prompt}...")
        image = generate_image(image_prompt)
        if image:
            st.image(image, caption=f"Generated image for: {image_prompt}", use_column_width=True)
        else:
            st.sidebar.write("Sorry, there was an error generating the image.")

if __name__ == "__main__":
    main()
