from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
try:
    import spacy
except Exception:
    spacy = None
import unicodedata
from users.models import Student, Professor, SecretaireFacultaire
from courses.models import Course, CourseNote
from .models import ChatMessage, Conversation
from .ml_model import get_ml_prediction, get_response_by_tag, get_llm_response, summarize_conversation


# Charger le modèle français de SpaCy si disponible (évite d'échouer au démarrage)
nlp = None
if spacy is not None:
    try:
        nlp = spacy.load("fr_core_news_sm")
    except Exception:
        nlp = None

def normalize_text(text):
    """Supprime les accents et met en minuscule pour faciliter la correspondance."""
    if not text: return ""
    text = text.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')


def find_course_notes_for_message(raw_message):
    if not raw_message:
        return []

    message_lower = raw_message.lower()
    normalized_message = normalize_text(raw_message)
    if 'note' not in message_lower and 'notes' not in message_lower:
        query_terms = [
            'cours', 'professeur', 'examen', 'chapitre', 'programme', 'syllabus',
            'définition', 'théorie', 'exercice', 'récursivité', 'python', 'algorithm',
            'algorithme', 'base', 'intelligence', 'programmation', 'variable', 'variables',
            'fonction', 'fonctions', 'struct', 'structure', 'data', 'donnée', 'données',
            'système', 'information', 'systèm', 'information', 'quoi', 'qu’est', 'quest',
            'explique', 'explication', 'concept', 'concepts', 'signifie', 'signification',
            'définis', 'définir', 'comprendre', 'comprendre'
        ]
        if not any(term in message_lower for term in query_terms):
            return []

    matched_notes = []

    for course in Course.objects.all():
        course_title = normalize_text(course.titre)
        if course_title and course_title in normalized_message:
            matched_notes = list(CourseNote.objects.filter(course=course).order_by('-updated_at'))
            if matched_notes:
                return matched_notes[:5]

    for course in Course.objects.all():
        notes = list(CourseNote.objects.filter(course=course).order_by('-updated_at'))
        if not notes:
            continue
        note_text = " ".join((note.content or "") for note in notes[:3]).lower()
        if not note_text:
            continue

        score = 0
        if normalize_text(course.titre) and normalize_text(course.titre) in normalized_message:
            score += 5
        for keyword in [
            'récursivité', 'python', 'algorithme', 'programmation', 'cours', 'définition',
            'théorie', 'exercice', 'problème', 'concept', 'chapitre', 'variable', 'variables',
            'fonction', 'fonctions', 'structure', 'donnée', 'données', 'système', 'information',
            'information', 'quoi', 'explique', 'concepts', 'signification', 'comprendre'
        ]:
            if keyword in note_text:
                score += 2
        if score >= 2:
            matched_notes.extend(notes[:2])

    if matched_notes:
        return matched_notes[:5]

    fallback_notes = list(CourseNote.objects.order_by('-updated_at')[:5])
    return fallback_notes


def format_notes_response(notes):
    if not notes:
        return ""
    course_title = notes[0].course.titre
    professor_name = notes[0].professor.nom if notes[0].professor else "le professeur concerné"
    course_label = course_title or "ce cours"
    professor_label = professor_name or "le professeur concerné"
    parts = [
        f"D’après les notes de {professor_label} pour le cours {course_label}, voici ce qui a été enregistré :"
    ]
    for note in notes[:5]:
        snippet = (note.content or "").strip()
        if len(snippet) > 220:
            snippet = snippet[:220].rsplit(' ', 1)[0] + '...'
        if snippet:
            parts.append(f"- {note.title}: {snippet}")
        else:
            parts.append(f"- {note.title}: contenu à consulter dans la note.")
    parts.append(
        f"Si la réponse n'est pas assez précise, je peux aussi vérifier une information externe pour le cours {course_label}."
    )
    return "\n".join(parts)


def get_conversation_message_lines(conversation, max_messages=40):
    if not conversation:
        return []
    messages = list(ChatMessage.objects.filter(conversation=conversation)
                    .order_by('timestamp')
                    .values_list('sender', 'text'))
    if not messages:
        return []
    recent = messages[-max_messages:]
    lines = []
    for sender, text in recent:
        if not text:
            continue
        role = 'Étudiant' if sender == 'user' else 'Assistant'
        lines.append(f"{role}: {text}")
    return lines


def build_conversation_prompt_context(conversation, max_messages=12):
    if not conversation:
        return ""

    lines = []
    if conversation.summary:
        lines.append("Résumé de la conversation :")
        lines.append(conversation.summary)
        lines.append("")

    recent_lines = get_conversation_message_lines(conversation, max_messages)
    if recent_lines:
        lines.append("Historique récent de la conversation :")
        lines.extend(recent_lines)

    return "\n".join(lines).strip()


def update_conversation_summary(conversation, student=None):
    if not conversation:
        return

    history_lines = get_conversation_message_lines(conversation, max_messages=60)
    if not history_lines:
        return

    history = "\n".join(history_lines)
    context = f"Etudiant: {student.nom if student else 'Inconnu'}, Niveau: {student.niveau if student else 'N/A'}"
    summary = summarize_conversation(history, context)
    if summary:
        conversation.summary = summary
        conversation.save(update_fields=['summary'])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_conversations(request):
    """Récupère la liste des conversations de l'utilisateur."""
    conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
    data = [
        {"id": c.id, "title": c.title, "updated_at": c.updated_at.strftime('%d/%m %H:%M')}
        for c in conversations
    ]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history(request):
    """Récupère l'historique des messages d'une conversation spécifique."""
    conv_id = request.GET.get('conversation_id')
    if not conv_id:
        return Response({"error": "ID de conversation manquant"}, status=400)
    
    try:
        conversation = Conversation.objects.get(id=conv_id, user=request.user)
        messages = ChatMessage.objects.filter(conversation=conversation).order_by('timestamp')
        
        data = [
            {
                "id": m.id,
                "text": m.text,
                "sender": m.sender,
                "file": request.build_absolute_uri(m.file.url) if m.file else None,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]
        return Response(data)
    except (Conversation.DoesNotExist, ValueError):
        return Response({"error": "Conversation introuvable"}, status=404)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conv_id):
    """Supprime une conversation et tout son historique."""
    try:
        conversation = Conversation.objects.get(id=conv_id, user=request.user)
        conversation.delete()
        return Response({"success": "Conversation supprimée."})
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation introuvable"}, status=404)

@api_view(['POST'])
@permission_classes([AllowAny])
def chatbot_response(request):
    raw_message = request.data.get('message', '').strip()
    uploaded_file = request.FILES.get('file')
    conv_id = request.data.get('conversation_id')
    if conv_id in ['null', 'undefined', '']:
        conv_id = None
    
    if not raw_message and not uploaded_file:
        return Response({"error": "Message et fichier vides"}, status=400)

    # Validation des types de fichiers autorisés
    ALLOWED_EXTENSIONS = ('.pdf',)
    if uploaded_file:
        name = uploaded_file.name.lower()
        if not any(name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            return Response({"error": "Type de fichier non autorisé."}, status=400)

    # Gestion de la conversation
    conversation = None
    msg_obj = None
    if request.user.is_authenticated:
        if conv_id:
            try:
                conversation = Conversation.objects.get(id=conv_id, user=request.user)
            except (Conversation.DoesNotExist, ValueError):
                pass
        
        if not conversation:
            title_text = raw_message if raw_message else "Fichier envoyé"
            title = title_text[:30] + "..." if len(title_text) > 30 else title_text
            conversation = Conversation.objects.create(user=request.user, title=title)
        
        msg_obj = ChatMessage.objects.create(
            conversation=conversation, 
            user=request.user, 
            text=raw_message, 
            file=uploaded_file,
            sender='user'
        )
        conversation.save()

    # --- COUCHE 1 : MACHINE LEARNING (DÉTECTION D'INTENTION) ---
    reply = ""
    confidence = 0
    intent_tag = ""
    
    if raw_message:
        intent_tag, confidence = get_ml_prediction(raw_message)
    elif uploaded_file:
        # Forcer le passage au LLM si c'est seulement une image
        confidence = 0 
    else:
        reply = "J'ai bien reçu ton fichier ! Peux-tu me préciser ce que tu attends que j'en fasse ?"
        confidence = 1.0

    # Identification de l'étudiant
    student = None
    if request.user.is_authenticated:
        try:
            student = request.user.student_profile
        except (Student.DoesNotExist, AttributeError):
            student = None

    # --- COUCHE 2 : LOGIQUE MÉTIER & PERSONNALISATION ---
    if confidence > 0.6:  # Augmenté pour éviter les faux positifs (ex: gitbash)
        # On ne garde que les réponses métiers spécifiques
        if intent_tag == "student_lookup":
            count = Student.objects.count()
            reply = f"Nous comptons actuellement {count} étudiants inscrits sur la plateforme ! 🎓"
        elif intent_tag == "course_info":
            courses = Course.objects.all()
            titles = [f"- {c.titre} ({c.professeur})" for c in courses]
            reply = "Voici les cours disponibles :\n" + "\n".join(titles)
        elif intent_tag == "recommandation" and student:
            niv = student.niveau.lower()
            c = Course.objects.order_by('?').first()
            if "l1" in niv: c = Course.objects.filter(titre__icontains="base").first() or c
            elif "l2" in niv: c = Course.objects.filter(titre__icontains="python").first() or c
            elif "l3" in niv: c = Course.objects.filter(titre__icontains="intelligence").first() or c
            reply = f"Vu que tu es en {student.niveau}, je te suggère : {c.titre}. C'est parfait pour toi !"
        else:
            reply = get_response_by_tag(intent_tag)
    
    # --- COUCHE 3 : RÈGLES MÉTIER ET RECHERCHE ---
    if not reply:
        norm_msg = normalize_text(raw_message)
        matched_course = None
        for course in Course.objects.all():
            if normalize_text(course.titre) in norm_msg:
                matched_course = course
                break
        if matched_course:
            reply = f"Tu parles du cours de {matched_course.titre} ? Il est dispensé par le professeur {matched_course.professeur}."

    # --- COUCHE 3.5 : NOTES DE COURS (PRIORITÉ ABSOLUE) ---
    notes_for_message = []
    if raw_message:
        normalized = normalize_text(raw_message)
        note_keywords = ['cours', 'note', 'notes', 'professeur', 'chapitre', 'examen', 'programme', 'syllabus', 'définition', 'théorie', 'exercice', 'python', 'algorithme', 'programmation', 'récursivité', 'système', 'information', 'quoi', 'explique', 'concept', 'signification', 'comprendre', 'question', 'definition']
        if any(keyword in normalized for keyword in note_keywords):
            notes_for_message = find_course_notes_for_message(raw_message)

    if not reply and notes_for_message:
        reply = format_notes_response(notes_for_message)

    # --- COUCHE 4 : PRO LLM FALLBACK (Multimodal) ---
    if not reply or confidence < 0.35 or uploaded_file:
        context = f"Etudiant: {student.nom if student else 'Inconnu'}, Niveau: {student.niveau if student else 'N/A'}"
        history_context = build_conversation_prompt_context(conversation)
        
        # Passer le chemin du fichier à l'IA pour analyse visuelle
        img_path = msg_obj.file.path if msg_obj and msg_obj.file else None
        llm_reply = get_llm_response(raw_message, context, history=history_context, image_path=img_path)
        
        error_keywords = ["surcharge mentale", "désactivée", "erreur", "difficultés techniques", "vérifier la clé", "clé api"]
        if not any(kw in llm_reply.lower() for kw in error_keywords):
            reply = llm_reply
            
            # Sauvegarder dans la base locale (cache)
            import hashlib
            from .ml_model import add_new_intent
            tag_hash = hashlib.md5(raw_message.encode('utf-8')).hexdigest()[:8]
            add_new_intent(f"llm_cache_{tag_hash}", [raw_message], [llm_reply])
        else:
            reply = ("Je n'ai pas bien compris ta question, mais je progresse chaque jour ! 🤖\n\n"
                    "Tu peux me demander :\n"
                    "- Voir la liste des cours disponibles\n"
                    "- Recevoir des conseils d'étude\n"
                    "- Connaître le nombre d'étudiants")

    # Nettoyer les éventuelles étoiles résiduelles
    if reply:
        reply = reply.replace('**', '')

    # Sauvegarde de la réponse bot
    if request.user.is_authenticated and conversation:
        bot_msg = ChatMessage.objects.create(conversation=conversation, user=request.user, text=reply, sender='bot')
        # Résumé de conversation seulement toutes les 5 réponses du bot (évite un appel LLM à chaque message)
        total_messages = ChatMessage.objects.filter(conversation=conversation, sender='bot').count()
        if total_messages % 5 == 0:
            update_conversation_summary(conversation, student)

    return Response({
        "response": reply,
        "conversation_id": conversation.id if conversation else None,
        "conversation_title": conversation.title if conversation else None
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_progress(request):
    """
    Retourne le suivi des étudiants avec leur activité chatbot.
    - Admin Central / Admin Gestionnaire : tous les étudiants
    - Secrétaire Facultaire : uniquement les étudiants de sa faculté
    - Professeur : uniquement les étudiants de sa faculté
    """
    from users.models import UserProfile

    user = request.user
    profile = getattr(user, 'profile', None)
    role = profile.role.nom if profile and profile.role else None

    # Déterminer le filtre de faculté selon le rôle
    faculte_filter = None
    if role == 'secretaire_facultaire':
        secretaire = SecretaireFacultaire.objects.filter(user=user).first()
        if secretaire:
            faculte_filter = secretaire.faculte
    elif role == 'professeur':
        professor = Professor.objects.filter(user=user).first()
        if professor:
            faculte_filter = professor.faculte

    # Construire le queryset
    if faculte_filter:
        students_qs = Student.objects.filter(faculte=faculte_filter)
    else:
        # Admin central / gestionnaire : tous les étudiants
        students_qs = Student.objects.all()

    result = []
    for student in students_qs:
        if student.user:
            convs = Conversation.objects.filter(user=student.user)
            conv_count = convs.count()
            last_conv = convs.order_by('-updated_at').first()
            last_msg = None
            if last_conv:
                last_msg_obj = ChatMessage.objects.filter(
                    conversation=last_conv, sender='user'
                ).order_by('-timestamp').first()
                last_msg = last_msg_obj.text if last_msg_obj else None
        else:
            conv_count = 0
            last_conv = None
            last_msg = None

        result.append({
            'student_id': student.id,
            'nom': student.nom,
            'niveau': student.niveau,
            'matricule': student.matricule or '-',
            'faculte': student.faculte.nom if student.faculte else '-',
            'conversations_count': conv_count,
            'last_conversation_title': last_conv.title if last_conv else None,
            'last_message': last_msg,
        })

    return Response(result)

