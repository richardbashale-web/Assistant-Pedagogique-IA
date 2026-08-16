from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
try:
    import spacy
except Exception:
    spacy = None
import os
import unicodedata
import re
from users.models import Student, Professor, SecretaireFacultaire
from courses.models import Course, CourseNote
from .models import ChatMessage, Conversation
from .ml_model import get_ml_prediction, get_response_by_tag, get_llm_response, summarize_conversation
from .rag.generation import generate_answer


# Charger le modèle français de SpaCy si disponible (évite d'échouer au démarrage)
nlp = None
if spacy is not None:
    try:
        nlp = spacy.load("fr_core_news_sm")
    except Exception:
        nlp = None

def normalize_text(text):
    """Supprime les accents et met en minuscule pour faciliter la correspondance."""
    if not text:
        return ""
    text = text.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')


def tokenize_text(text):
    normalized = normalize_text(text or "")
    return [token for token in re.findall(r"\w+", normalized) if token]


def is_conversational_message(message):
    tokens = tokenize_text(message)
    if not tokens:
        return False
    conversational_terms = {
        'bonjour', 'salut', 'coucou', 'hello', 'bonsoir', 'allo', 'hey', 'yo', 'slt', 'bjr',
        'merci', 'ok', 'daccord', 'super', 'genial', 'au', 'revoir', 'bye', 'a', 'plus', 'top'
    }
    # Si le premier mot est un terme conversationnel et le message est court (<= 4 mots)
    if len(tokens) <= 4 and (tokens[0] in conversational_terms or any(t in conversational_terms for t in tokens)):
        return True
    return False


def get_user_display_name(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    profile = getattr(user, 'profile', None)
    if profile and getattr(profile, 'nom_complet', None):
        return profile.nom_complet.strip()
    full_name = " ".join(filter(None, [user.first_name.strip() if user.first_name else '', user.last_name.strip() if user.last_name else ''])).strip()
    if full_name:
        return full_name
    return user.username


def extract_requested_professors(raw_message):
    normalized_message = normalize_text(raw_message or "")
    message_tokens = set(tokenize_text(raw_message or ""))
    matched_professors = []

    for professor in Professor.objects.all():
        if not professor.nom:
            continue
        professor_name = normalize_text(professor.nom)
        professor_tokens = set(re.findall(r"\w+", professor_name))
        if not professor_tokens:
            continue
        if professor_name in normalized_message:
            matched_professors.append(professor)
            continue
        if len(professor_tokens) >= 2 and professor_tokens.issubset(message_tokens):
            matched_professors.append(professor)
            continue
        if any(token in professor_tokens for token in message_tokens) and "prof" in normalized_message:
            matched_professors.append(professor)

    return matched_professors


def find_course_notes_for_message(raw_message):
    if not raw_message:
        return []

    normalized_message = normalize_text(raw_message)
    message_tokens = tokenize_text(raw_message)

    query_terms = [
        'cours', 'professeur', 'examen', 'chapitre', 'programme', 'syllabus',
        'definition', 'theorie', 'exercice', 'recursivite', 'python', 'algorithm',
        'algorithme', 'base', 'intelligence', 'programmation', 'variable', 'variables',
        'fonction', 'fonctions', 'struct', 'structure', 'data', 'donnee', 'donnees',
        'systeme', 'information', 'quoi', 'quest', 'explique', 'explication',
        'concept', 'concepts', 'signifie', 'signification', 'definis', 'definir',
        'comprendre', 'question'
    ]
    query_terms = [normalize_text(term) for term in query_terms]

    if len(message_tokens) < 2 and not any(term in normalized_message for term in query_terms):
        return []

    requested_professors = extract_requested_professors(raw_message)
    if requested_professors:
        professor_ids = [prof.id for prof in requested_professors]
        notes = list(CourseNote.objects.filter(professor_id__in=professor_ids).order_by('-updated_at'))
        if notes:
            return notes[:5]

    # Prioritize exact course title matches first.
    for course in Course.objects.all():
        course_title = normalize_text(course.titre)
        if course_title and course_title in normalized_message:
            notes = list(CourseNote.objects.filter(course=course).order_by('-updated_at'))
            if notes:
                return notes[:5]

    candidates = []
    for note in CourseNote.objects.select_related('course', 'professor').all():
        note_prof = normalize_text(note.professor.nom) if note.professor else ""
        note_course = normalize_text(note.course.titre or "")
        note_title = normalize_text(note.title or "")
        search_text = " ".join(
            [note.title or '', note.content or '', note.course.titre or '', note.professor.nom if note.professor else '']
        )
        normalized_note = normalize_text(search_text)
        score = sum(1 for token in message_tokens if token in normalized_note)

        if note_prof and any(token in note_prof for token in message_tokens):
            score += 6
        if note_course and any(token in note_course for token in message_tokens):
            score += 4
        if note_title and any(token in note_title for token in message_tokens):
            score += 3
        if note_course and note_course in normalized_message:
            score += 3

        if score > 0:
            candidates.append((score, note))

    if candidates:
        candidates.sort(key=lambda item: (-item[0], -item[1].id))
        return [note for _, note in candidates][:5]

    # Fallback: return recent notes containing any relevant keyword.
    fallback = []
    for note in CourseNote.objects.order_by('-updated_at')[:50]:
        normalized_note = normalize_text(" ".join([note.title or '', note.content or '']))
        if any(term in normalized_note for term in query_terms):
            fallback.append(note)
            if len(fallback) >= 5:
                break

    return fallback


def extract_text_from_course_note_attachment(note):
    if not note or not getattr(note, 'attachment', None):
        return ""
    try:
        from courses.views import extract_text_from_attachment
        with note.attachment.open('rb') as attachment_file:
            return extract_text_from_attachment(attachment_file)
    except Exception:
        return ""


def build_note_snippet(note, max_length=280):
    text = (note.content or "").strip()
    if not text and getattr(note, 'attachment', None):
        text = extract_text_from_course_note_attachment(note).strip()
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    snippet = text[:max_length].rsplit(' ', 1)[0]
    return snippet + '...'


def split_text_units(text):
    if not text:
        return []
    units = []
    for block in re.split(r'[\n\r]+', text):
        block = block.strip()
        if not block:
            continue
        for sentence in re.split(r'(?<=[.!?;:])\s+|\n+', block):
            sentence = sentence.strip()
            if sentence:
                units.append(sentence)
    return units


def find_relevant_sentences(notes, question):
    question_tokens = set(re.findall(r"\w+", normalize_text(question or "")))
    if not question_tokens:
        return ""

    units = []
    for note in notes:
        text = (note.content or "").strip()
        if not text and getattr(note, 'attachment', None):
            text = extract_text_from_course_note_attachment(note).strip()
        if not text:
            continue
        units.extend(split_text_units(text))

    best_matches = []
    for unit in units:
        normalized_unit = normalize_text(unit)
        score = sum(1 for token in question_tokens if token in normalized_unit)
        if score > 0:
            best_matches.append((score, unit.strip()))

    if best_matches:
        best_matches.sort(key=lambda item: (-item[0], len(item[1])))
        selected = []
        seen = set()
        for _, unit in best_matches:
            if unit not in seen:
                selected.append(unit)
                seen.add(unit)
            if len(selected) >= 2:
                break
        return " ".join(selected)

    first_snippet = build_note_snippet(notes[0]) if notes else ""
    return first_snippet


def get_note_attachment_url(note):
    if not note or not getattr(note, 'attachment', None):
        return None
    try:
        return note.attachment.url
    except Exception:
        return None


def format_notes_response(notes, question="", request=None):
    if not notes:
        return ""
    course_title = notes[0].course.titre
    professor_name = notes[0].professor.nom if notes[0].professor else "le professeur concerné"
    course_label = course_title or "ce cours"
    professor_label = professor_name or "le professeur concerné"

    sentence_answer = find_relevant_sentences(notes, question)
    attachment_url = get_note_attachment_url(notes[0])

    if sentence_answer:
        answer = sentence_answer
        answer += f"\n\nSource : note de cours de {professor_label}."
        return answer

    first_snippet = build_note_snippet(notes[0])
    if first_snippet:
        answer = first_snippet
    elif attachment_url:
        answer = (
            f"Je n'ai pas pu extraire automatiquement le texte de la note du professeur {professor_label} pour le cours {course_label}.\n"
            f"Je joins le fichier source pour que tu puisses le consulter directement."
        )
        return answer
    else:
        answer = (
            f"Je n'ai pas pu extraire automatiquement le texte de la note du professeur {professor_label} pour le cours {course_label}."
        )

    answer += f"\n\nSource : note de cours de {professor_label}."
    return answer


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
                "file": m.file.url if m.file else None,
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
    conv_id = request.data.get('conversation_id')
    if conv_id in ['null', 'undefined', '']:
        conv_id = None
    
    if not raw_message:
        return Response({"error": "Message vide"}, status=400)

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
            title = raw_message[:30] + "..." if len(raw_message) > 30 else raw_message
            conversation = Conversation.objects.create(user=request.user, title=title)
        
        msg_obj = ChatMessage.objects.create(
            conversation=conversation, 
            user=request.user, 
            text=raw_message,
            sender='user'
        )
        conversation.save()

    # --- COUCHE 1 : MACHINE LEARNING (DÉTECTION D'INTENTION) ---
    # Note : le chat étudiant n'accepte que du texte — aucun fichier n'est traité ici.
    reply = ""
    confidence = 0
    intent_tag = ""

    if is_conversational_message(raw_message):
        intent_tag = "conversational"
        confidence = 1.0
    else:
        intent_tag, confidence = get_ml_prediction(raw_message)
        # Éviter que "qui est jul" ou "qui est cr7" soit pris pour une question sur l'identité du bot
        if confidence > 0.6 and "qui est" in raw_message.lower():
            if not any(kw in raw_message.lower() for kw in ["tu", "ton nom", "t'es", "assistant", "bot", "ia"]):
                confidence = 0
                intent_tag = ""

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
        if intent_tag == "conversational":
            user_name = get_user_display_name(request.user)
            lower_msg = raw_message.lower()
            if 'merci' in lower_msg:
                reply = "De rien ! N'hésite pas si tu as d'autres questions."
            elif 'au revoir' in lower_msg or 'bye' in lower_msg:
                reply = f"À bientôt {user_name or ''} ! Bonne journée."
            else:
                reply = f"Bonjour {user_name or ''} ! Comment puis-je t'aider aujourd'hui ?"
        elif intent_tag == "student_lookup":
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

    bot_file = None
    bot_file_name = None

    rag_sources = []
    # --- COUCHE 3.5 : RAG SÉMANTIQUE (PRIORITÉ HAUTE) ---
    if not reply or confidence < 0.6:
        print(f"[RAG] Tentative RAG pour : {raw_message[:120]}")
        rag_answer = generate_answer(raw_message)
        print(f"[RAG] used_rag={rag_answer.get('used_rag')} sources={rag_answer.get('sources')}")

        if rag_answer.get("answer"):
            reply = rag_answer.get("answer", "").strip()
            rag_sources = rag_answer.get("sources", [])
            confidence = 1.0

    # --- COUCHE 4 : NOTES DE COURS PAR MOTS-CLÉS (FALLBACK) ---
    # Utilisé uniquement si le RAG n'a pas trouvé de réponse pertinente.
    notes_for_message = []
    if not reply or confidence < 0.6:
        normalized = normalize_text(raw_message)
        note_keywords = [
            'cours', 'note', 'notes', 'professeur', 'chapitre', 'examen', 'programme',
            'syllabus', 'définition', 'théorie', 'exercice', 'python', 'algorithme',
            'programmation', 'récursivité', 'système', 'information', 'quoi', 'explique',
            'concept', 'signification', 'comprendre', 'question', 'definition'
        ]
        if any(keyword in normalized for keyword in note_keywords):
            notes_for_message = find_course_notes_for_message(raw_message)

        if notes_for_message and (not reply or confidence < 0.6):
            reply = format_notes_response(notes_for_message, raw_message, request=request)
            confidence = max(confidence, 0.75)
            if notes_for_message[0].attachment:
                bot_file = get_note_attachment_url(notes_for_message[0])
                bot_file_name = os.path.basename(notes_for_message[0].attachment.name or bot_file)

    # --- COUCHE 5 : LLM GÉNÉRAL (FALLBACK FINAL) ---
    # Utilisé si ni le RAG ni les mots-clés n'ont produit de réponse.
    if not reply or confidence < 0.35:
        context = f"Etudiant: {student.nom if student else 'Inconnu'}, Niveau: {student.niveau if student else 'N/A'}"
        history_context = build_conversation_prompt_context(conversation)
        llm_reply = get_llm_response(raw_message, context, history=history_context)

        error_keywords = ["surcharge mentale", "désactivée", "erreur", "difficultés techniques", "vérifier la clé", "clé api"]
        if not any(kw in llm_reply.lower() for kw in error_keywords):
            reply = llm_reply
            # Sauvegarder dans la base locale (cache ML)
            import hashlib
            from .ml_model import add_new_intent
            tag_hash = hashlib.md5(raw_message.encode('utf-8')).hexdigest()[:8]
            add_new_intent(f"llm_cache_{tag_hash}", [raw_message], [llm_reply])
        else:
            reply = (
                "Je n'ai pas bien compris ta question, mais je progresse chaque jour ! 🤖\n\n"
                "Tu peux me demander :\n"
                "- Voir la liste des cours disponibles\n"
                "- Recevoir des conseils d'étude\n"
                "- Connaître le nombre d'étudiants"
            )

    # Nettoyer les éventuelles étoiles résiduelles
    if reply:
        reply = reply.replace('**', '')

    # Sauvegarde de la réponse bot
    if request.user.is_authenticated and conversation:
        bot_kwargs = {'conversation': conversation, 'user': request.user, 'text': reply, 'sender': 'bot'}
        if bot_file and notes_for_message and notes_for_message[0].attachment:
            bot_kwargs['file'] = notes_for_message[0].attachment
        bot_msg = ChatMessage.objects.create(**bot_kwargs)
        # Résumé de conversation seulement toutes les 5 réponses du bot (évite un appel LLM à chaque message)
        total_messages = ChatMessage.objects.filter(conversation=conversation, sender='bot').count()
        if total_messages % 5 == 0:
            update_conversation_summary(conversation, student)

    response_data = {
        "response": reply,
        "conversation_id": conversation.id if conversation else None,
        "conversation_title": conversation.title if conversation else None,
        "sources": rag_sources
    }
    if bot_file:
        response_data["file"] = bot_file
        response_data["file_name"] = bot_file_name

    return Response(response_data)


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

