# There are a few librabries that should be installed to make this project run smoothly
# Other librabries are already accessible through an import

!pip install nltk
!pip install beautifulsoup4
!pip install -q streamlit
!pip install pyngrok

# Now to define the Streamlit app (with some modifications)
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import spacy
import nltk
nltk.download('punkt')
from nltk.corpus import stopwords
import heapq
import streamlit as st
from pyngrok import ngrok

# Download spaCy model
spacy.cli.download("en_core_web_sm")

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Summarize  text
def summarize_text(text, num_sentences=10):
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
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

    # All image tags are called in
    img_tags = soup.find_all('img')

    # Extracts image URLs
    image_urls = [urljoin(url, img['src']) for img in img_tags]

    return image_urls

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
            st.write(url)

if __name__ == "__main__":
    main()

# Modification to allow me to access my public IP address from within a Python scrip
public_ip = subprocess.check_output(["wget", "-q", "-O", "-", "ipv4.icanhazip.com"])
public_ip = public_ip.decode("utf-8").strip()

# Runs Streamlit
subprocess.run(["streamlit", "run", "app.py", "&", "npx", "localtunnel", "--port", "8501"])
