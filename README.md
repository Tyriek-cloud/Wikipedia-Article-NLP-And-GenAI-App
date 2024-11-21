# Wikipedia-Article-NLP-And-GenAI-App

Wikipedia Article Analyzer: https://wikipedia-article-analyzer-nlp-app-app-ggh9suyycuva5j6wybe5pa.streamlit.app/

<img width="879" alt="image" src="https://github.com/user-attachments/assets/3a6488be-1e0d-46d4-8903-850771c8c6f0">

This project is designed to scrape articles from Wikipedia. By default, the Streamlit application will display the Wikipedia Statistics page (https://en.wikipedia.org/wiki/Statistics). The user will have the option to insert their own Wikipedia URLs. The end goal is to use Natural Language Processing to create a summary (with an emphasis on important and easily digestable details) from Wikipedia articles and display important images/pictures/graphics from each of the articles.

The user can now also interact with an Image Generator (powered by Stable Diffusion). The Image Generator is an ongoing/work-in progress feature. The app's author will be continuously training the external model and the application to produce better results.

# Summary

The application generates a summary of 10+ sentences. The sentences are intended to pull crucial facts about the article. As opposed to reading an entire article, this can save a user time.

The user can now utilize an Image Generator. The idea is that the user can take information that is being summarized in the articles and "visualize the summary" using the image generation feature. It is sometimes useful to look at pictures as opposed to text when learning (or at least that has been the author's experience).

# Image URLs

This will pull in links to images from the Wikipedia article. These URLs are clickable and will generate a seperate webpage. The images can then be copied for personal use.

# IMPORTANT DISCLAIMERS

The structure of the Wikiepedia article may impact whether a summary is actually generated. Image URLs are always pulled in.

The original base code for this app was written in Google Colab: https://colab.research.google.com/drive/1RDKGcidcVlpzs2kT-9SB0WKN2NaA4sft?usp=sharing. Mid-project, I realized that the "spacy" library would be compatible on Google Colab but not on Streamlit.io. Overall, the project continues to evolve and deviate from the base Jupyter Notebook.

So I researched solutions to modify the tokenization and other features of the application.

The Image Generator is currently a work-in-progress. It will be improved over time.
