from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CourseNote


@receiver(post_save, sender=CourseNote)
def feed_knowledge_base(sender, instance, created, **kwargs):
    """
    Chaque fois qu'un professeur crée ou modifie une note de cours,
    on injecte automatiquement son contenu dans la base de connaissances ML.
    """
    try:
        from chatbot.ml_model import add_new_intent

        tag = f"coursenote_{instance.id}"
        
        # Patterns : titre de la note + combinaisons avec le titre du cours
        course_title = instance.course.titre if instance.course else ""
        note_title = instance.title or ""
        patterns = []
        if note_title:
            patterns.append(note_title.lower())
        if course_title:
            patterns.append(course_title.lower())
            if note_title:
                patterns.append(f"{course_title.lower()} {note_title.lower()}")
                patterns.append(f"cours {course_title.lower()}")
                patterns.append(f"note de {course_title.lower()}")

        # Réponse : contenu de la note
        content = (instance.content or "").strip()
        if len(content) > 500:
            content = content[:500].rsplit(' ', 1)[0] + '...'

        professor_name = instance.professor.nom if instance.professor else "le professeur"
        response_text = (
            f"📘 Note de {professor_name} — {course_title} : {note_title}\n\n{content}"
            if content
            else f"📘 Note de {professor_name} — {course_title} : {note_title}\n(Pas de contenu textuel)"
        )

        if patterns:
            add_new_intent(tag, patterns, [response_text])
            print(f"[Signal] Base ML mise à jour avec la note : {tag}")
    except Exception as e:
        print(f"[Signal] Erreur lors de la mise à jour ML: {e}")
