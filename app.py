# Now to define the Streamlit app
import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from urllib.parse import urljoin
import spacy

# Download NLTK data
nltk.download('punkt')

# Global variable to hold the article text
# Going to use this to help the bot search an article in real time
article_text = ""

# Summarize text
def summarize_text(text, num_sentences=10):
    sentences = nltk.sent_tokenize(text)
    summary = " ".join(sentences[:num_sentences])
    return summary

# Extract live URLs from the references section
#def extract_live_urls(url):
#    response = requests.get(url)
#    soup = BeautifulSoup(response.text, 'html.parser')

#    references_section = soup.find("span", {"id": "References"})
#     if references_section:
  #       references_list = references_section.find_next(["ol", "ul"])
    #     if references_list:
      #       live_references = []
        #     for li in references_list.find_all('li'):
          #       links = li.find_all('a', href=True)
            #     for link in links:
              #       link_text = link.get_text()
                #     link_url = urljoin(url, link['href'])
                  #   live_references.append((link_text, link_url))
         #    return live_references

 #    return []

# Extracts images
def extract_images(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # All image tags are called 'img'
    img_tags = soup.find_all('img')

    # Extracts image URLs (if available)
    image_urls = [urljoin(url, img['src']) for img in img_tags if img.has_attr('src')]

    return image_urls

# Call Function to communicate with my Wit.ai app
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
        
        # If entities are present, include them in the response
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

        index = cosine_similarities.argsort()[0][-1]
        similarity_score = cosine_similarities[0][index]
        
        if similarity > 0.1:
            return f"From the article: '{question}' is mentioned."
    return "I'm sorry, but I couldn't find an answer in the article."

# Main function
def main():
    st.title("Wikipedia Article Analyzer")

    # Sidebar for user input (if any)
    st.sidebar.header("User Input")
    url_input = st.sidebar.text_input("Enter Wikipedia URL:", "https://en.wikipedia.org/wiki/Statistics")

    # Main content
    if st.button("Analyze"):
        global article_text  # Global variable to hold the article info
        try:
            # Extract and summarize the text
            response = requests.get(url_input)
            response.raise_for_status() # Bad responses
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.find("div", class_="mw-parser-output")
            paragraphs = content.find_all("p")
            full_text = "\n".join([p.text for p in paragraphs])
            article_text = full_text
            summary = summarize_text(full_text)

            # Display summary
            st.subheader("Summary:")
            st.write(summary)

            # Extract live URLs from the references section
            # live_references = extract_live_urls(url_input)
            # st.subheader("Live References:")
            # for text, url in live_references:
              #   st.markdown(f"[{text}]({url})")  # Render as a clickable lin

            # Extract images
            image_urls = extract_images(url_input)
            st.subheader("Image URLs:")
            for idx, url in enumerate(image_urls, start=1):
                st.image(url, caption=f"Image {idx}", use_column_width=True)
                st.write(url)

        except Exception as e:
            st.error(f"Error: {str(e)}")
            
    # The user's method to talk to the Chatbot (Chatbot functionality)
    st.sidebar.header("Beep Boop: Talk with me")
    user_question = st.sidebar.text_input("Ask a question about the article:")

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
    
    if st.sidebar.button("Get Response"):
        if user_question:
            question_type = categorize_question(user_question)
        
        if question_type == "factual":
            answer = search_article(user_question)
            if answer:
                st.sidebar.write("Bot:", answer)
            else:
                response = wit_ai_response(user_question)
                st.sidebar.write("Bot:", response)
        elif question_type == "general":
            response = wit_ai_response(user_question)
            st.sidebar.write("Bot:", response)
        else:
            st.sidebar.write("Bot: I couldn't categorize your question. Please ask something specific.")
        #if user_question:
            # First, the app will search the article for an answer
         #   answer = search_article(user_question)
          #  if answer:
                st.sidebar.write("Bot:", answer)
          #  else:
                # Next, the app will consult Wit.ai if no answer is found
           #     response = wit_ai_response(user_question)
            #    st.sidebar.write("Bot:", response)
      #  else:
        #    st.sidebar.write("Bot: Please ask a question about the article.")

if __name__ == "__main__":
    main()
