import os
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from chatbot.models import Intent, Pattern, Response
from django.conf import settings

INTENTS_PATH = os.path.join(settings.BASE_DIR, 'chatbot', 'intents.json')

def run():
    print("Loading intents from:", INTENTS_PATH)
    if not os.path.exists(INTENTS_PATH):
        print("File does not exist.")
        return

    with open(INTENTS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for intent_data in data.get("intents", []):
        tag = intent_data.get("tag")
        intent, created = Intent.objects.get_or_create(tag=tag)
        if created:
            print(f"Created Intent: {tag}")
        
        for pattern_text in intent_data.get("patterns", []):
            Pattern.objects.get_or_create(intent=intent, text=pattern_text)
            
        for response_text in intent_data.get("responses", []):
            Response.objects.get_or_create(intent=intent, text=response_text)
            
    print("Done loading intents.")

if __name__ == '__main__':
    run()
