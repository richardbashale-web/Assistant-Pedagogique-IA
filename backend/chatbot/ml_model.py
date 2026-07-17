import json
import os
import unicodedata
import base64
import mimetypes
import random
import re
import pickle
import requests
from django.conf import settings

# Chemins des fichiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH = os.path.join(BASE_DIR, 'intents.json')
MODEL_PKL = os.path.join(BASE_DIR, 'chatbot_v2.pkl')

def normalize_text(text):
    """Prétraitement avancé pour le NLP."""
    if not text: return []
    text = text.lower().strip()
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')
    # Garder seulement les mots (lettres et chiffres)
    words = re.findall(r'\w+', text)
    return words

class TFIDFClassifier:
    def __init__(self):
        self.vocabulary = []
        self.idf = {}
        self.tag_centroids = {}
        self.tags = []

    def fit(self, patterns_data):
        """
        Entraîne le modèle TF-IDF sur patterns_data: List of (words_list, tag)
        """
        all_docs = [p[0] for p in patterns_data]
        self.tags = list(set([p[1] for p in patterns_data]))
        
        # 1. Vocabulaire
        unique_words = set()
        for doc in all_docs:
            unique_words.update(doc)
        self.vocabulary = sorted(list(unique_words))

        # 2. IDF (version pure Python, sans dépendance à NumPy)
        N = len(all_docs)
        for word in self.vocabulary:
            df = sum(1 for doc in all_docs if word in doc)
            self.idf[word] = (N + 1) / (df + 1)  # version simplifiée de l'IDF
            
        # 3. Vectorisation TF-IDF
        vectors = []
        for doc in all_docs:
            vectors.append(self.transform(doc))
            
        # 4. Centroïdes par Tag
        for tag in self.tags:
            tag_vecs = [vectors[i] for i, p in enumerate(patterns_data) if p[1] == tag]
            if tag_vecs:
                centroid = []
                if tag_vecs:
                    vector_length = len(tag_vecs[0])
                    for idx in range(vector_length):
                        centroid.append(sum(vec[idx] for vec in tag_vecs) / len(tag_vecs))
                self.tag_centroids[tag] = centroid

    def transform(self, words):
        vec = [0.0] * len(self.vocabulary)
        if not words: return vec
        
        # TF
        counts = {}
        for w in words:
            counts[w] = counts.get(w, 0) + 1
            
        for w, count in counts.items():
            if w in self.vocabulary:
                idx = self.vocabulary.index(w)
                tf = count / len(words)
                vec[idx] = tf * self.idf[w]
        return vec

    def predict(self, text):
        words = normalize_text(text)
        user_vec = self.transform(words)
        
        best_tag = None
        max_sim = -1
        
        for tag, centroid in self.tag_centroids.items():
            # Similarité Cosinus (version pure Python)
            norm_u = sum(value * value for value in user_vec) ** 0.5
            norm_c = sum(value * value for value in centroid) ** 0.5
            if norm_u == 0 or norm_c == 0:
                sim = 0
            else:
                dot = sum(u * c for u, c in zip(user_vec, centroid))
                sim = dot / (norm_u * norm_c)
            
            if sim > max_sim:
                max_sim = sim
                best_tag = tag
        
        return best_tag, max_sim

# --- Moteur Global ---
_engine = None

def train_and_save():
    global _engine
    try:
        with open(INTENTS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        patterns_data = []
        for intent in data["intents"]:
            for pattern in intent["patterns"]:
                words = normalize_text(pattern)
                if words:
                    patterns_data.append((words, intent["tag"]))
        
        _engine = TFIDFClassifier()
        _engine.fit(patterns_data)
        
        with open(MODEL_PKL, 'wb') as f:
            pickle.dump(_engine, f)
        return True
    except Exception as e:
        print(f"Erreur d'entraînement: {e}")
        return False

def get_ml_prediction(text):
    global _engine
    if _engine is None:
        if os.path.exists(MODEL_PKL):
            with open(MODEL_PKL, 'rb') as f:
                _engine = pickle.load(f)
        else:
            train_and_save()
    
    if _engine:
        tag, confidence = _engine.predict(text)
        if confidence > 0.35:
            return tag, confidence
    return None, 0

# --- Apprentissage Automatique ---
def add_new_pattern(tag, pattern):
    """Ajoute dynamiquement une phrase au modèle et ré-entraîne."""
    try:
        with open(INTENTS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for intent in data["intents"]:
            if intent["tag"] == tag:
                if pattern not in intent["patterns"]:
                    intent["patterns"].append(pattern)
                    break
        
        with open(INTENTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        train_and_save()
        return True
    except:
        return False

# --- PRO LEVEL : Gemini LLM Connector ---

def _gemini_generate_text(parts):
    """
    Appelle l'API Gemini avec un budget temps strict de 13s au total
    pour garantir une réponse côté client en moins de 15s.
    Priorité : modèles les plus rapides et stables d'abord.
    """
    import time
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not gemini_key:
        return None

    # Budget total de 13s pour laisser 2s de marge réseau/Django
    TOTAL_BUDGET_S = 13
    start = time.monotonic()

    # Priorité : modèles actuellement disponibles chez Gemini
    models_to_try = [
        ("gemini-2.5-flash", 12),
        ("gemini-2.5-flash-lite", 10),
    ]

    for model_name, model_timeout in models_to_try:
        elapsed = time.monotonic() - start
        remaining = TOTAL_BUDGET_S - elapsed
        if remaining <= 1:
            # Budget épuisé — ne pas lancer un autre appel réseau
            break
        timeout = min(model_timeout, remaining)
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model_name}:generateContent?key={gemini_key}"
            )
            response = requests.post(
                url,
                json={"contents": [{"parts": parts}]},
                timeout=timeout
            )
            if response.status_code == 200:
                try:
                    payload = response.json()
                    return payload['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError, TypeError) as exc:
                    print(f"Réponse Gemini inattendue ({model_name}): {exc}")
            print(f"Échec Gemini ({model_name}): {response.status_code} — {response.text[:200]}")
        except requests.exceptions.Timeout:
            print(f"Timeout Gemini ({model_name}) après {timeout:.1f}s — modèle suivant")
        except Exception as e:
            print(f"Exception Gemini ({model_name}): {e}")

    return None


def get_llm_response(prompt, context="", history="", image_path=None):
    """
    Connecte le bot à l'API Gemini de Google.
    """
    system_prompt = (
        "Tu es BashAi, un assistant IA pédagogique expert multimodale conçu par Richard Bashale Kanku. "
        "RÈGLE CRUCIALE : Ne te présente JAMAIS (ne dis pas ton nom ni ton créateur) et ne fais pas de salutations répétitives. "
        "Réponds directement à la question de l'étudiant de manière concise et professionnelle. "
        "Utilise toujours l'historique de la conversation pour te souvenir du contexte et ne dis jamais que tu n'as pas de mémoire personnelle. "
        f"Infos étudiant : {context}"
    )

    if history:
        prompt_text = (
            f"{system_prompt}\n\nHistorique de la conversation :\n{history}\n\nClient : {prompt}"
        )
    else:
        prompt_text = f"{system_prompt}\n\nClient : {prompt}"

    parts = [{"text": prompt_text}]
    if image_path and os.path.exists(image_path):
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type and mime_type.startswith('image'):
            with open(image_path, "rb") as f:
                parts.append({"inline_data": {"mime_type": mime_type, "data": base64.b64encode(f.read()).decode('utf-8')}})

    llm_text = _gemini_generate_text(parts)
    if llm_text:
        return llm_text

    return ("Désolé, je rencontre des difficultés techniques avec l'IA Gemini. "
            "Veuillez vérifier la clé API Gemini dans les réglages. 🛠️")


def summarize_conversation(history, context=""):
    if not history:
        return ""

    system_prompt = (
        "Tu es BashAi, un assistant IA pédagogique expert multimodale. "
        "Ne dis jamais que tu n'as pas de mémoire personnelle. "
        "Résume l'historique de conversation ci-dessous en 2 ou 3 phrases claires et utiles pour le contexte futur. "
        "Ne présente pas ton identité et évite les détails superflus. "
        f"Infos étudiant : {context}"
    )
    prompt_text = (
        f"{system_prompt}\n\nHistorique :\n{history}\n\nRésumé :"
    )
    parts = [{"text": prompt_text}]
    summary = _gemini_generate_text(parts)
    if summary:
        return summary.strip()

    return history.strip()[:1000]

def get_response_by_tag(tag):
    """Récupère une réponse aléatoire pour un tag donné dans intents.json."""
    try:
        with open(INTENTS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for intent in data["intents"]:
            if intent["tag"] == tag:
                return random.choice(intent["responses"])
    except:
        pass
    return "Je comprends, mais je n'ai pas de réponse précise pour ce sujet."