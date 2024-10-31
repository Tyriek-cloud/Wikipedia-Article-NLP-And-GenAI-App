import os
import subprocess

# Install requirements
subprocess.run(['pip', 'install', '-r', 'requirements.txt'])

# Download spaCy model
subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
