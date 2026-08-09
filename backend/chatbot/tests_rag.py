from django.test import SimpleTestCase

from chatbot.rag.ingestion import chunk_text
from chatbot.rag.generation import build_prompt


class RagCoreTests(SimpleTestCase):
    def test_chunk_text_returns_non_empty_chunks(self):
        text = (
            "Le machine learning est une branche de l'intelligence artificielle. "
            "Il permet aux systèmes d'apprendre à partir de données. "
            "Les modèles peuvent ensuite faire des prédictions sur de nouvelles observations."
        )

        chunks = chunk_text(text, chunk_size=12, overlap=3)

        self.assertTrue(chunks)
        self.assertTrue(all(chunk.strip() for chunk in chunks))
        self.assertGreaterEqual(len(chunks), 1)

    def test_build_prompt_includes_strict_instruction(self):
        question = "Explique le concept de RAG"
        chunks = [{"text": "Le RAG combine recherche et génération."}]

        prompt = build_prompt(question, chunks)

        self.assertIn("Contexte fourni", prompt)
        self.assertIn("uniquement", prompt.lower())
        self.assertIn(question, prompt)
