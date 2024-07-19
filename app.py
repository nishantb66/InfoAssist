from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_bcrypt import Bcrypt
import pickle
import spacy
import nltk
from nltk.corpus import stopwords
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os
import logging
import gunicorn
from waitress import serve

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"
bcrypt = Bcrypt(app)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load spaCy model for additional NLP tasks
nlp = spacy.load("en_core_web_sm")

nltk.download("stopwords")
stop_words = stopwords.words("english")

# *******************************************************************************************************************************
# *******************************************************************************************************************************


# Function to hash passwords
def hash_password(password):
    return bcrypt.generate_password_hash(password).decode("utf-8")


# Function to check passwords
def check_password(hashed_password, password):
    return bcrypt.check_password_hash(hashed_password, password)


# Load credentials
def load_credentials():
    if os.path.exists("credentials.pkl"):
        with open("credentials.pkl", "rb") as file:
            credentials = pickle.load(file)
            return credentials.get("username"), credentials.get("password_hash")
    else:
        default_username = "admin@info"
        default_password_hash = hash_password("ofni@nimda")
        save_credentials(default_username, default_password_hash)
        return default_username, default_password_hash


# Save credentials
def save_credentials(username, password_hash):
    with open("credentials.pkl", "wb") as file:
        pickle.dump({"username": username, "password_hash": password_hash}, file)


# ********************************************************************************************************************************
# ********************************************************************************************************************************


# Load data
def load_data(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    questions, answers = [], []
    for line in lines:
        if line.startswith("Q:"):
            questions.append(line[3:].strip())
        elif line.startswith("A:"):
            answers.append(
                line[3:].strip().replace("\\n", "\n")
            )  # Convert \n back to newlines

    return pd.DataFrame({"question": questions, "answer": answers})


# Load dialogs.txt data
df = load_data("data/dialogs.txt")

# Load sentence transformer model
sentence_model = SentenceTransformer("all-MiniLM-L6-v2")

# Generate embeddings for all questions
question_embeddings = sentence_model.encode(
    df["question"].tolist(), convert_to_tensor=True
)

# Save the embeddings and data
with open("embeddings.pkl", "wb") as emb_file:
    pickle.dump(question_embeddings, emb_file)

with open("faq_data.pkl", "wb") as data_file:
    pickle.dump(df, data_file)

# Load the embeddings, FAQ data, and sentence transformer model
with open("embeddings.pkl", "rb") as emb_file:
    question_embeddings = pickle.load(emb_file)

with open("faq_data.pkl", "rb") as data_file:
    faq_data = pickle.load(data_file)

model = SentenceTransformer("all-MiniLM-L6-v2")


def get_response(query, top_n=5):
    query_embedding = model.encode([query], convert_to_tensor=True)
    similarity = cosine_similarity(query_embedding, question_embeddings)
    top_indices = similarity.argsort()[0][-top_n:][::-1]  # Get top N similar questions
    best_index = top_indices[0]
    similar_questions = faq_data.iloc[top_indices]["question"].tolist()

    answer = faq_data.iloc[best_index]["answer"]
    return answer, similarity.flatten(), similar_questions


# Load admin credentials
admin_username, admin_password_hash = load_credentials()


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # Log the login attempt
    logging.info(f"Login attempt with Username: {username}, Password: {password}")

    if username == admin_username:
        if check_password(admin_password_hash, password):
            logging.info(f"Login successful for Username: {username}")
            session["logged_in"] = True
            return jsonify({"success": True})
    logging.info(f"Login failed for Username: {username}")
    return jsonify({"success": False})


# *******************************************************************************************************************************
# *******************************************************************************************************************************


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("logged_in", None)
    return jsonify({"success": True})


@app.route("/reset_credentials", methods=["POST"])
def reset_credentials():
    global admin_username, admin_password_hash
    data = request.get_json()
    old_password = data.get("oldPassword")
    new_username = data.get("newUsername")
    new_password = data.get("newPassword")

    if check_password(admin_password_hash, old_password):
        admin_username = new_username
        admin_password_hash = hash_password(new_password)
        save_credentials(admin_username, admin_password_hash)
        return jsonify({"success": True})
    return jsonify({"success": False})


# *******************************************************************************************************************************
# *******************************************************************************************************************************


@app.route("/get_answer", methods=["POST"])
def get_answer():
    data = request.get_json()
    question = data.get("question")
    if question.lower() == "quit":
        answer = "Goodbye! Have a nice day!"
        return jsonify({"answer": answer, "quit": True})
    else:
        answer, similarity, similar_questions = get_response(question)
        return jsonify(
            {
                "answer": answer,
                "similarity": similarity.tolist(),
                "similar_questions": similar_questions,
                "quit": False,
            }
        )


@app.route("/get_similar_questions", methods=["POST"])
def get_similar_questions():
    data = request.get_json()
    similarity = data.get("similarity")
    top_indices = sorted(
        range(len(similarity)), key=lambda i: similarity[i], reverse=True
    )[1:6]
    similar_questions = faq_data.iloc[top_indices]["question"].tolist()
    return jsonify({"similar_questions": similar_questions})


@app.route("/get_selected_answer", methods=["POST"])
def get_selected_answer():
    data = request.get_json()
    selected_question = data.get("selected_question")
    answer, _, _ = get_response(
        selected_question
    )  # Ignore the similarity and similar questions
    return jsonify({"answer": answer})


@app.route("/")
def welcome():
    return render_template("chatbot.html")


@app.route("/admin")
def admin():
    if not session.get("logged_in"):
        return redirect(url_for("welcome"))
    return render_template("admin.html")


def update_data():
    global df, question_embeddings, faq_data
    df = load_data("data/dialogs.txt")
    question_embeddings = sentence_model.encode(
        df["question"].tolist(), convert_to_tensor=True
    )
    faq_data = df


@app.route("/add_question", methods=["POST"])
def add_question():
    data = request.get_json()
    new_question = data.get("question")
    new_answer = data.get("answer").replace(
        "\n", "\\n"
    )  # Replace newline characters with \n

    # Append new question and answer to dialogs.txt
    with open("data/dialogs.txt", "a") as file:
        file.write(f"\nQ: {new_question}\nA: {new_answer}\n")

    # Update the DataFrame and embeddings without restarting the server
    update_data()

    return jsonify({"message": "Question added successfully"})


# @app.route("/submit_feedback", methods=["POST"])
# def submit_feedback():
#     data = request.get_json()
#     feedback = data.get("feedback")

#     with open("data/feedback.txt", "a") as file:
#         file.write(feedback + "\n")

#     return jsonify({"success": True})


if __name__ == "__main__":
    update_data()
    serve(app, host="192.168.29.55", port=8080)
