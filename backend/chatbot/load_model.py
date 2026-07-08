import pickle

# charger modèle
with open("chatbot/model.pkl", "rb") as f:
    model = pickle.load(f)

with open("chatbot/vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)