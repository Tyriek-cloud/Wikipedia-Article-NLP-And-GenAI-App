import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from urllib.parse import urljoin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download NLTK data (you might want to do this once)
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')  # For POS tagging
nltk.download('named_entities')  # For named entity recognition

# Global variable to hold the article text
article_text = ""

# Summarize text
def summarize_text(text, num_sentences=10):
    sentences = nltk.sent_tokenize(text)
    summary = " ".join(sentences[:num_sentences])
    return summary

# Extract images
def extract_images(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    img_tags = soup.find_all('img')
    image_urls = [urljoin(url, img['src']) for img in img_tags if img.has_attr('src')]
    return image_urls

# Call Function to communicate with Wit.ai app
def wit_ai_response(message):
    access_token = st.secrets["wit"]["access_token"]
    if not access_token:
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
        intents = data.get('intents', [])
        entities = data.get('entities', {})

        if intents:
            intent_name = intents[0]['name']
            return f"I understand you're asking about {intent_name}. How can I assist you further?"
        
        if entities:
            entity_name = next(iter(entities))  # Get the first entity
            return f"I see you're interested in {entity_name}. Let me help you with that."
            
        return data.get('msg', 'Sorry, I didn\'t understand that.')
    else:
        return 'Error: Could not contact Wit.ai.'

# This is the function that parses the article to answer the user's question
def search_article(question):
    global article_text
    if article_text:
        sentences = nltk.sent_tokenize(article_text)
        vectorizer = TfidfVectorizer().fit_transform(sentences + [question])
        vectors = vectorizer.toarray()
        cosine_similarities = cosine_similarity(vectors[-1], vectors[:-1])

        top_n = 3
        index = cosine_similarities.argsort()[0][-1]
        similarity_score = cosine_similarities[0][index]
        
        if similarity_score > 0.1:
            return f"From the article: '{sentences[index]}'"
    
    return "I'm sorry, but I couldn't find an answer in the article."

# Categorize the user's question
def categorize_question(question):
    factual_keywords = ["what", "who", "when", "where", "how many", "define"]
    general_keywords = ["opinion", "suggest", "recommend", "feel"]

    question_lower = question.lower()
    
    if any(keyword in question_lower for keyword in factual_keywords):
        return "factual"
    elif any(keyword in question_lower for keyword in general_keywords):
        return "general"
    else:
        return "other"

# Analyze the question for entities using NLTK
def analyze_question(question):
    tokens = nltk.word_tokenize(question)
    pos_tags = nltk.pos_tag(tokens)
    named_entities = nltk.ne_chunk(pos_tags, binary=True)  # Binary flag for named entity recognition
    entities = []
    
    for subtree in named_entities:
        if hasattr(subtree, 'label'):
            entity = ' '.join([leaf[0] for leaf in subtree.leaves()])
            entities.append((entity, subtree.label()))

    noun_phrases = [' '.join([token for token, tag in pos_tags if tag.startswith('NN')])]
    return entities, noun_phrases

# Main function
def main():
    st.title("Wikipedia Article Analyzer")

    # Sidebar for user input (if any)
    st.sidebar.header("User Input")
    url_input = st.sidebar.text_input("Enter Wikipedia URL:", "https://en.wikipedia.org/wiki/Statistics")

    # Main content
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

    # User's method to talk to the chatbot
    st.sidebar.header("Beep Boop: Talk with me")
    user_question = st.sidebar.text_input("Ask a question about the article:")

    if user_question:
        question_type = categorize_question(user_question)
        
        if question_type == "factual":
            answer = search_article(user_question)
            st.sidebar.write("Bot:", answer)
        elif question_type == "general":
            response = wit_ai_response(user_question)
            st.sidebar.write("Bot:", response)
        else:
            st.sidebar.write("Bot: I couldn't categorize your question. Please ask something specific.")

        # Analyze question for entities
        entities, noun_phrases = analyze_question(user_question)
        if entities:
            st.sidebar.write("Bot: I found these entities in your question:", entities)

if __name__ == "__main__":
    main()
