
# InfoAssist Bot

This project is an NLP-Transformer based chatbot built using Flask. The chatbot is capable of answering questions based on a predefined dataset.

## Project Structure

```
InfoAssist/
├── app.py
├── credentials.pkl
├── embeddings.pkl
├── faq_data.pkl
├── README.md
├── requirements.txt
├── tempCodeRunnerFile.py
├── Updates.txt
├── data/
│   └── dialogs.txt
├── static/
│   ├── apple-touch-icon.png
│   ├── chatbot.js
│   ├── favicon-16x16.png
│   ├── favicon-32x32.png
│   ├── favicon.ico
│   ├── logo.png
│   └── site.webmanifest
└── templates/
    ├── admin.html
    └── chatbot.html
```

## Features

- User authentication with hashed passwords
- Admin interface for managing credentials and FAQs
- Dynamic loading of FAQs and updating embeddings
- NLP capabilities using spaCy and NLTK
- Sentence similarity using SentenceTransformer
- RESTful API for getting answers and managing data

## Capabilities

- Responds to user queries based on a predefined dataset
- Provides the most relevant answer along with similar questions
- Allows adding new FAQs without restarting the server
- Simple and intuitive web interface for interaction

## Limitations

- Limited to the predefined dataset in `dialogs.txt`
- No real-time learning or update of the model based on interactions
- Basic user authentication with no role management

## Pre-trained Model

This project uses the `all-MiniLM-L6-v2` model from SentenceTransformer. It is a pre-trained model optimized for semantic similarity tasks. The model is efficient and provides a good balance between performance and speed.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nishantb66/InfoAssist.git
   cd InfoAssist
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download the necessary NLTK data:
   ```python
   import nltk
   nltk.download('stopwords')
   ```

## Usage

1. Run the Flask application:
   ```bash
   python app.py
   ```

2. Access the chatbot interface by navigating to `http://127.0.0.1:8080` in your web browser or you can also host in a specific IP as its WSGI server ready.

## Files

- `app.py`: The main application file.
- `credentials.pkl`: Pickled file storing admin credentials.
- `embeddings.pkl`: Pickled file storing question embeddings.
- `faq_data.pkl`: Pickled file storing FAQ data.
- `README.md`: This readme file.
- `requirements.txt`: File listing the dependencies.
- `Updates.txt`: File containing updates or changes.
- `data/dialogs.txt`: File containing dialog questions and answers.
- `static/`: Directory for static files like images and JavaScript.
- `templates/`: Directory for HTML templates.


## License

This project is licensed under the MIT License.
