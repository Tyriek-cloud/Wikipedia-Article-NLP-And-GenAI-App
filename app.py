import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep

# Download NLTK data
nltk.download('punkt')

# Global variable for article text
article_text = ""

# Add Hugging Face API token (not needed for Craiyon)
HF_API_TOKEN = st.secrets["hug"]["NOTIMPORTANT"]  # Streamlit secrets for sensitive data
if not HF_API_TOKEN:
    raise ValueError("Hugging Face API token is missing!")

# Cache heavy operations like article fetching and image generation
@st.cache_data
def fetch_article(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find("div", class_="mw-parser-output")
    paragraphs = content.find_all("p")
    return "\n".join([p.text for p in paragraphs])

def generate_image_using_selenium(prompt):
    # Set up Selenium WebDriver (Ensure you have ChromeDriver installed)
    driver = webdriver.Chrome(executable_path="/path/to/chromedriver")  # Replace with correct path to chromedriver

    # Open Craiyon website
    driver.get("https://www.craiyon.com/")
    
    # Find the input field and type the prompt
    input_box = driver.find_element(By.XPATH, "//input[@name='prompt']")
    input_box.send_keys(prompt)
    input_box.send_keys(Keys.RETURN)
    
    # Wait for the image generation to complete
    sleep(10)  # Adjust this depending on how long it takes Craiyon to generate the image
    
    # Find the generated image element (XPath may change depending on Craiyon's page structure)
    image_element = driver.find_element(By.XPATH, "//img[@class='generated-img']")
    image_url = image_element.get_attribute("src")
    
    # Download the image using the URL
    img_data = requests.get(image_url).content
    img = Image.open(BytesIO(img_data))
    
    # Close the browser window
    driver.quit()

    return img

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
            try:
                image = generate_image_using_selenium(image_prompt)
                st.image(image, caption=f"Generated image for: {image_prompt}", use_column_width=True)
            except Exception as e:
                st.sidebar.write(f"Error generating image: {e}")

if __name__ == "__main__":
    main()
