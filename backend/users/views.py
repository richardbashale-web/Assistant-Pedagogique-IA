from rest_framework import generics, status
from .models import Student, Professor, Role, UserProfile, Faculty, AdminCentral, AdminGestionnaire, SecretaireFacultaire
from .serializers import StudentSerializer, ProfessorSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from .permissions import can_manage_users, user_has_role, assign_role_to_user
from django.db.models import Count
from django.db import transaction
import io
import csv

# 📌 Student Views
class StudentListCreateView(generics.ListCreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not (self.request.user.is_staff or can_manage_users(self.request.user)):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Accès refusé.")
        return super().get_queryset()

    def perform_create(self, serializer):
        if not (self.request.user.is_staff or can_manage_users(self.request.user)):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul un secrétaire ou un administrateur peut créer des étudiants.")
        serializer.save()

class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if not (self.request.user.is_staff or can_manage_users(self.request.user)):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Accès refusé.")
        serializer.save()

    def perform_destroy(self, instance):
        if not (self.request.user.is_staff or can_manage_users(self.request.user)):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Accès refusé.")
        instance.delete()


# 📌 Import en masse des étudiants
class StudentImportView(APIView):
    """
    POST /api/students/import/
    Importe une liste d'étudiants depuis un fichier .xlsx ou .csv.
    Champs attendus dans le fichier : matricule, nom, post_nom, prenom, sexe
    Body (multipart/form-data) : file, faculty_id, promotion, academic_year
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not (request.user.is_staff or can_manage_users(request.user)):
            return Response({'error': 'Permission refusée.'}, status=status.HTTP_403_FORBIDDEN)

        uploaded_file = request.FILES.get('file')
        faculty_id = request.data.get('faculty_id')
        promotion = request.data.get('promotion')
        academic_year = request.data.get('academic_year')

        if not uploaded_file:
            return Response({'error': 'Aucun fichier fourni.'}, status=status.HTTP_400_BAD_REQUEST)
        if not faculty_id:
            return Response({'error': 'faculty_id est requis.'}, status=status.HTTP_400_BAD_REQUEST)
        if not promotion:
            return Response({'error': 'La promotion est requise.'}, status=status.HTTP_400_BAD_REQUEST)
        if not academic_year:
            return Response({'error': "L'année académique est requise."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            faculty = Faculty.objects.get(code=faculty_id)
        except Faculty.DoesNotExist:
            return Response({'error': 'Faculté introuvable.'}, status=status.HTTP_400_BAD_REQUEST)

        # --- Lecture du fichier ---
        filename = uploaded_file.name.lower()
        try:
            rows = self._parse_file(uploaded_file, filename)
        except Exception as e:
            return Response({'error': f'Impossible de lire le fichier : {e}'}, status=status.HTTP_400_BAD_REQUEST)

        # --- Traitement ligne par ligne ---
        created_count = 0
        errors = []

        with transaction.atomic():
            for i, row in enumerate(rows, start=2):  # ligne 2 car la ligne 1 est l'en-tête
                sp = transaction.savepoint()
                try:
                    result = self._process_row(row, i, faculty, promotion, academic_year)
                    if result.get('error'):
                        errors.append({'line': i, 'reason': result['error'], 'data': result.get('data', {})})
                        transaction.savepoint_rollback(sp)
                    else:
                        created_count += 1
                        transaction.savepoint_commit(sp)
                except Exception as e:
                    transaction.savepoint_rollback(sp)
                    errors.append({'line': i, 'reason': str(e), 'data': {}})

        return Response({
            'total_lines': len(rows),
            'created': created_count,
            'errors_count': len(errors),
            'errors': errors,
        }, status=status.HTTP_200_OK)

    def _parse_file(self, uploaded_file, filename):
        """Lit le fichier et retourne une liste de dicts normalisés."""
        if filename.endswith('.xlsx'):
            return self._parse_xlsx(uploaded_file)
        elif filename.endswith('.csv'):
            return self._parse_csv(uploaded_file)
        else:
            raise ValueError('Format de fichier non supporté. Utilisez .xlsx ou .csv')

    def _parse_xlsx(self, uploaded_file):
        try:
            import openpyxl
        except ImportError:
            raise ImportError('openpyxl est requis pour lire les fichiers .xlsx. Installez-le avec : pip install openpyxl')

        wb = openpyxl.load_workbook(uploaded_file, read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = [str(h).strip().lower() if h else '' for h in next(rows_iter)]
        rows = []
        for row in rows_iter:
            if all(v is None or str(v).strip() == '' for v in row):
                continue  # ignorer les lignes vides
            rows.append(dict(zip(headers, [str(v).strip() if v is not None else '' for v in row])))
        return rows

    def _parse_csv(self, uploaded_file):
        content = uploaded_file.read().decode('utf-8-sig')  # utf-8-sig gère le BOM Excel
        reader = csv.DictReader(io.StringIO(content))
        # Normaliser les noms de colonnes
        rows = []
        for row in reader:
            normalized = {k.strip().lower(): (v.strip() if v else '') for k, v in row.items()}
            rows.append(normalized)
        return rows

    def _process_row(self, row, line_num, faculty, promotion, academic_year):
        """Traite une ligne du fichier et crée User + UserProfile + Student."""
        # Mapper les variantes de noms de colonnes
        matricule = (row.get('matricule') or '').strip()
        nom = (row.get('nom') or '').strip()
        post_nom = (row.get('post-nom') or row.get('post_nom') or row.get('postnom') or '').strip()
        prenom = (row.get('prenom') or row.get('prénom') or '').strip()
        sexe = (row.get('sexe') or '').strip().upper()

        # Validation des champs obligatoires
        if not matricule:
            return {'error': 'Matricule manquant.', 'data': row}
        if not nom:
            return {'error': 'Nom manquant.', 'data': row}
        if sexe not in ('M', 'F', ''):
            return {'error': f'Sexe invalide : "{sexe}". Attendu M ou F.', 'data': row}

        # Vérification des doublons de matricule
        if Student.objects.filter(matricule=matricule).exists():
            return {'error': f'Matricule "{matricule}" déjà existant.', 'data': row}

        # Construction du nom complet (nom + post-nom + prénom)
        nom_complet_parts = [p for p in [nom, post_nom, prenom] if p]
        nom_complet = ' '.join(nom_complet_parts)

        # Génération de l'email fictif à partir du matricule
        email_base = matricule.lower().replace(' ', '-')
        email = f'{email_base}@uwb.edu'
        # En cas de collision d'email (rare mais possible)
        if User.objects.filter(email=email).exists() or Student.objects.filter(email=email).exists():
            email = f'{email_base}-{line_num}@uwb.edu'

        # Création du username Django (matricule)
        username = matricule.lower().replace(' ', '-')
        if User.objects.filter(username=username).exists():
            username = f'{username}-{line_num}'

        # Création du compte User avec mot de passe temporaire uwb@1234
        user = User.objects.create_user(
            username=username,
            email=email,
            password='uwb@1234',
            first_name=prenom,
            last_name=f'{nom} {post_nom}'.strip(),
        )

        # Création du UserProfile
        profile = UserProfile.objects.create(
            user=user,
            nom_complet=nom_complet,
            est_actif=True,
        )
        assign_role_to_user(user, 'etudiant')

        # Création de l'étudiant
        Student.objects.create(
            user=user,
            profile=profile,
            nom=nom,
            postnom=post_nom,
            prenom=prenom,
            sexe=sexe,
            email=email,
            niveau=promotion,
            matricule=matricule,
            faculte=faculty,
            academic_year=academic_year,
            is_active=True,
        )

        return {'success': True}


# 📌 Activer / Désactiver un étudiant
class StudentToggleActiveView(APIView):
    """
    PATCH /api/students/<id>/toggle-active/
    Inverse l'état is_active de l'étudiant et du User Django lié.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not (request.user.is_staff or can_manage_users(request.user)):
            return Response({'error': 'Permission refusée.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            student = Student.objects.select_related('user').get(pk=pk)
        except Student.DoesNotExist:
            return Response({'error': 'Étudiant introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        new_state = not student.is_active
        student.is_active = new_state
        student.save(update_fields=['is_active'])

        # Synchroniser avec User.is_active (bloque l'authentification JWT)
        if student.user:
            student.user.is_active = new_state
            student.user.save(update_fields=['is_active'])

        action = 'activé' if new_state else 'désactivé'
        return Response({
            'id': student.pk,
            'is_active': new_state,
            'message': f"L'étudiant a été {action} avec succès.",
        })


# 📌 Professor Views
class ProfessorListCreateView(generics.ListCreateAPIView):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not (self.request.user.is_staff or can_manage_users(self.request.user)):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Accès refusé.")
        return super().get_queryset()

    def perform_create(self, serializer):
        if not (self.request.user.is_staff or can_manage_users(self.request.user)):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul un secrétaire ou un administrateur peut créer des professeurs.")
        
        email = self.request.data.get('email', '')
        nom = self.request.data.get('nom', '')
        username = self.request.data.get('username') or (email.split('@')[0] if email else None)
        password = self.request.data.get('password') or 'Professeur123!'

        user = None
        profile = None
        if username and email:
            if not User.objects.filter(username=username).exists() and not User.objects.filter(email=email).exists():
                user = User.objects.create_user(username=username, email=email, password=password)
                profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'nom_complet': nom})
                assign_role_to_user(user, 'professeur')
            elif User.objects.filter(email=email).exists():
                user = User.objects.filter(email=email).first()
                if user:
                    profile = getattr(user, 'profile', None)

        secretaire = SecretaireFacultaire.objects.filter(user=self.request.user).first()
        if secretaire:
            if not secretaire.faculte:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Aucune faculté n'est associée à ce secrétaire.")
            serializer.save(user=user, profile=profile, enregistre_par=secretaire, faculte=secretaire.faculte)
            return
        serializer.save(user=user, profile=profile, enregistre_par=None)


class ProfessorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if not (self.request.user.is_staff or can_manage_users(self.request.user)):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Accès refusé.")
        serializer.save()

    def perform_destroy(self, instance):
        if not (self.request.user.is_staff or can_manage_users(self.request.user)):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Accès refusé.")
        instance.delete()


class ProfessorToggleActiveView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        professor = Professor.objects.filter(pk=pk).first()
        if not professor or not can_manage_users(request.user):
            return Response({'error': 'Permission refusée.'}, status=status.HTTP_403_FORBIDDEN)
        secretaire = SecretaireFacultaire.objects.filter(user=request.user).first()
        if secretaire and professor.faculte_id != secretaire.faculte_id:
            return Response({'error': 'Cet enseignant ne fait pas partie de votre faculté.'}, status=status.HTTP_403_FORBIDDEN)
        professor.is_active = not professor.is_active
        professor.save(update_fields=['is_active'])
        if professor.user:
            professor.user.is_active = professor.is_active
            professor.user.save(update_fields=['is_active'])
        return Response({'is_active': professor.is_active})

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        professor = getattr(request.user, 'professor_profile', None)
        student = getattr(request.user, 'student_profile', None)
        profile = getattr(request.user, 'profile', None)
        secretaire = SecretaireFacultaire.objects.filter(user=request.user).first()
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "is_staff": request.user.is_staff,
            "is_professor": bool(professor),
            "is_student": bool(student),
            "professor_id": professor.id if professor else None,
            "role": profile.role.nom if profile and profile.role else None,
            "role_display": profile.role.get_nom_display() if profile and profile.role else None,
            "faculte": secretaire.faculte.code if secretaire and secretaire.faculte else None,
            "faculte_nom": secretaire.faculte.nom if secretaire and secretaire.faculte else None,
        })


# Gestion des rôles et permissions

@api_view(['POST'])
@permission_classes([IsAdminUser])
def initialize_roles(request):
    """Initialise les rôles et permissions du système"""
    try:
        init_roles()
        return Response({"success": "Rôles et permissions initialisés avec succès"})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_roles(request):
    """Liste tous les rôles disponibles"""
    roles = Role.objects.all().values('id', 'nom', 'description')
    return Response(list(roles))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_role(request):
    """Retourne le rôle de l'utilisateur connecté"""
    try:
        profile = request.user.profile
        return Response({
            "username": request.user.username,
            "role": profile.role.nom if profile.role else None,
            "role_display": profile.role.get_nom_display() if profile.role else None,
            "is_admin": request.user.is_staff,
        })
    except UserProfile.DoesNotExist:
        return Response({"error": "Profil utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_role(request):
    """Assigne un rôle à un utilisateur (Admin Central et Admin Gestionnaire)"""
    if not can_manage_users(request.user):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)

    user_id = request.data.get('user_id')
    username = request.data.get('username')
    role_nom = request.data.get('role_nom')

    try:
        if user_id:
            user = User.objects.get(id=user_id)
        elif username:
            user = User.objects.get(username=username)
        else:
            return Response({"error": "user_id ou username requis"}, status=status.HTTP_400_BAD_REQUEST)

        if assign_role_to_user(user, role_nom):
            return Response({"success": f"Rôle {role_nom} assigné à {user.username}"})
        return Response({"error": "Rôle non trouvé"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users_by_role(request):
    """Liste tous les utilisateurs d'un rôle spécifique (Admin Central et Admin Gestionnaire)"""
    role_nom = request.GET.get('role_nom')
    if not role_nom:
        return Response({"error": "role_nom requis"}, status=status.HTTP_400_BAD_REQUEST)

    is_central = user_has_role(request.user, 'admin_central') or request.user.is_staff
    is_gestionnaire = user_has_role(request.user, 'admin_gestionnaire')

    if not (is_central or is_gestionnaire):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)

    if is_gestionnaire and role_nom != 'secretaire_facultaire':
        return Response({"error": "L'administrateur gestionnaire ne peut lister que les secrétaires facultaires"}, status=status.HTTP_403_FORBIDDEN)

    queryset = UserProfile.objects.filter(role__nom=role_nom)
    
    if is_gestionnaire:
        # filter secretaries that were created by or belong to this admin_gestionnaire
        queryset = queryset.filter(secretaire__admin_gestionnaire__user=request.user)

    if role_nom == 'secretaire_facultaire':
        users_list = []
        for profile in queryset:
            sec = getattr(profile, 'secretaire', None)
            users_list.append({
                'user__id': profile.user.id,
                'user__username': profile.user.username,
                'user__email': profile.user.email,
                'nom_complet': profile.nom_complet,
                'est_actif': profile.est_actif,
                'faculte': sec.faculte.nom if sec and sec.faculte else None,
                'faculte_code': sec.faculte.code if sec and sec.faculte else None,
            })
        return Response(users_list)

    users = queryset.values(
        'user__id', 'user__username', 'user__email', 'nom_complet', 'est_actif'
    )
    return Response(list(users))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_admin_gestionnaire(request):
    """Crée un administrateur gestionnaire (Admin Central seulement)"""
    if not (user_has_role(request.user, 'admin_central') or request.user.is_superuser):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)

    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    nom_complet = request.data.get('nom_complet')

    if not all([username, email, password]):
        return Response({"error": "Données manquantes"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Utilisateur déjà existant"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(username=username, email=email, password=password)
        profile = UserProfile.objects.create(user=user, nom_complet=nom_complet)
        assign_role_to_user(user, 'admin_gestionnaire')

        admin_central_user = request.user
        try:
            admin_central = AdminCentral.objects.get(user=admin_central_user)
        except AdminCentral.DoesNotExist:
            # Si l'utilisateur superuser / admin central n'a pas encore de profil AdminCentral,
            # créer un enregistrement manquant pour permettre la relation.
            admin_central_profile = getattr(admin_central_user, 'profile', None)
            if admin_central_profile is None:
                admin_central_profile = UserProfile.objects.create(
                    user=admin_central_user,
                    nom_complet=admin_central_user.get_full_name() or admin_central_user.username
                )
            admin_central, _ = AdminCentral.objects.get_or_create(
                user=admin_central_user,
                defaults={'profile': admin_central_profile}
            )

        AdminGestionnaire.objects.create(user=user, profile=profile, admin_central=admin_central)

        return Response({
            "success": "Administrateur gestionnaire créé",
            "user_id": user.id,
            "username": user.username
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_secretaire(request):
    """Crée un secrétaire facultaire (Admin Gestionnaire ou Admin Central)"""
    if not (user_has_role(request.user, 'admin_gestionnaire') or user_has_role(request.user, 'admin_central') or request.user.is_superuser):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)

    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    nom_complet = request.data.get('nom_complet')
    faculte_code = request.data.get('faculte')

    if not all([username, email, password, faculte_code]):
        return Response({"error": "Données manquantes"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Nom d'utilisateur déjà pris"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        faculty = Faculty.objects.get(code=faculte_code)
    except Faculty.DoesNotExist:
        return Response({"error": "Faculté introuvable"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(username=username, email=email, password=password)
        profile = UserProfile.objects.create(user=user, nom_complet=nom_complet)
        assign_role_to_user(user, 'secretaire_facultaire')

        admin_gestionnaire = AdminGestionnaire.objects.filter(user=request.user).first()
        SecretaireFacultaire.objects.create(
            user=user,
            profile=profile,
            admin_gestionnaire=admin_gestionnaire,
            faculte=faculty
        )

        return Response({
            "success": "Secrétaire facultaire créé",
            "user_id": user.id,
            "username": user.username
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# --- Modifier / Supprimer / Activer-Désactiver un Admin Gestionnaire ---

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_admin_gestionnaire(request, user_id):
    """Modifie un administrateur gestionnaire (Admin Central seulement)"""
    if not (user_has_role(request.user, 'admin_central') or request.user.is_superuser):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)

    try:
        gestionnaire = AdminGestionnaire.objects.select_related('user', 'profile').get(user_id=user_id)
    except AdminGestionnaire.DoesNotExist:
        return Response({"error": "Gestionnaire introuvable"}, status=status.HTTP_404_NOT_FOUND)

    nom_complet = request.data.get('nom_complet')
    email = request.data.get('email')

    if email and User.objects.filter(email=email).exclude(pk=gestionnaire.user_id).exists():
        return Response({"error": "Cet email est déjà utilisé"}, status=status.HTTP_400_BAD_REQUEST)

    if nom_complet is not None:
        gestionnaire.profile.nom_complet = nom_complet
        gestionnaire.profile.save(update_fields=['nom_complet'])
    if email is not None:
        gestionnaire.user.email = email
        gestionnaire.user.save(update_fields=['email'])

    return Response({
        "success": "Gestionnaire modifié",
        "user_id": gestionnaire.user.id,
        "nom_complet": gestionnaire.profile.nom_complet,
        "email": gestionnaire.user.email,
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_admin_gestionnaire(request, user_id):
    """Supprime un administrateur gestionnaire (Admin Central seulement)"""
    if not (user_has_role(request.user, 'admin_central') or request.user.is_superuser):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)

    try:
        gestionnaire = AdminGestionnaire.objects.select_related('user').get(user_id=user_id)
    except AdminGestionnaire.DoesNotExist:
        return Response({"error": "Gestionnaire introuvable"}, status=status.HTTP_404_NOT_FOUND)

    gestionnaire.user.delete()  # cascade : supprime aussi le profil et l'admin gestionnaire
    return Response({"success": "Gestionnaire supprimé"})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_admin_gestionnaire_active(request, user_id):
    """Active/désactive un administrateur gestionnaire (Admin Central seulement)"""
    if not (user_has_role(request.user, 'admin_central') or request.user.is_superuser):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)

    try:
        gestionnaire = AdminGestionnaire.objects.select_related('user', 'profile').get(user_id=user_id)
    except AdminGestionnaire.DoesNotExist:
        return Response({"error": "Gestionnaire introuvable"}, status=status.HTTP_404_NOT_FOUND)

    new_state = not gestionnaire.profile.est_actif
    gestionnaire.profile.est_actif = new_state
    gestionnaire.profile.save(update_fields=['est_actif'])
    gestionnaire.user.is_active = new_state
    gestionnaire.user.save(update_fields=['is_active'])

    action = 'activé' if new_state else 'désactivé'
    return Response({
        "is_active": new_state,
        "message": f"Le gestionnaire a été {action} avec succès.",
    })


# --- Modifier / Supprimer / Activer-Désactiver un Secrétaire Facultaire ---

def _can_manage_secretaire(request_user, secretaire):
    """Un admin central peut tout gérer ; un admin gestionnaire seulement ses propres secrétaires."""
    is_central = user_has_role(request_user, 'admin_central') or request_user.is_superuser
    is_gestionnaire = user_has_role(request_user, 'admin_gestionnaire')
    if not (is_central or is_gestionnaire):
        return False, "Permission refusée"
    if is_gestionnaire and not is_central:
        if not secretaire.admin_gestionnaire or secretaire.admin_gestionnaire.user_id != request_user.id:
            return False, "Permission refusée"
    return True, None


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_secretaire(request, user_id):
    """Modifie un secrétaire facultaire (Admin Gestionnaire ou Admin Central)"""
    try:
        secretaire = SecretaireFacultaire.objects.select_related('user', 'profile', 'admin_gestionnaire__user').get(user_id=user_id)
    except SecretaireFacultaire.DoesNotExist:
        return Response({"error": "Secrétaire introuvable"}, status=status.HTTP_404_NOT_FOUND)

    allowed, error = _can_manage_secretaire(request.user, secretaire)
    if not allowed:
        return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)

    nom_complet = request.data.get('nom_complet')
    email = request.data.get('email')
    faculte_code = request.data.get('faculte')

    if email and User.objects.filter(email=email).exclude(pk=secretaire.user_id).exists():
        return Response({"error": "Cet email est déjà utilisé"}, status=status.HTTP_400_BAD_REQUEST)

    if nom_complet is not None:
        secretaire.profile.nom_complet = nom_complet
        secretaire.profile.save(update_fields=['nom_complet'])
    if email is not None:
        secretaire.user.email = email
        secretaire.user.save(update_fields=['email'])
    if faculte_code:
        try:
            secretaire.faculte = Faculty.objects.get(code=faculte_code)
            secretaire.save(update_fields=['faculte'])
        except Faculty.DoesNotExist:
            return Response({"error": "Faculté introuvable"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "success": "Secrétaire modifié",
        "user_id": secretaire.user.id,
        "nom_complet": secretaire.profile.nom_complet,
        "email": secretaire.user.email,
        "faculte": secretaire.faculte.code if secretaire.faculte else None,
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_secretaire(request, user_id):
    """Supprime un secrétaire facultaire (Admin Gestionnaire ou Admin Central)"""
    try:
        secretaire = SecretaireFacultaire.objects.select_related('user', 'admin_gestionnaire__user').get(user_id=user_id)
    except SecretaireFacultaire.DoesNotExist:
        return Response({"error": "Secrétaire introuvable"}, status=status.HTTP_404_NOT_FOUND)

    allowed, error = _can_manage_secretaire(request.user, secretaire)
    if not allowed:
        return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)

    secretaire.user.delete()  # cascade : supprime aussi le profil et le secrétaire
    return Response({"success": "Secrétaire supprimé"})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_secretaire_active(request, user_id):
    """Active/désactive un secrétaire facultaire (Admin Gestionnaire ou Admin Central)"""
    try:
        secretaire = SecretaireFacultaire.objects.select_related('user', 'profile', 'admin_gestionnaire__user').get(user_id=user_id)
    except SecretaireFacultaire.DoesNotExist:
        return Response({"error": "Secrétaire introuvable"}, status=status.HTTP_404_NOT_FOUND)

    allowed, error = _can_manage_secretaire(request.user, secretaire)
    if not allowed:
        return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)

    new_state = not secretaire.profile.est_actif
    secretaire.profile.est_actif = new_state
    secretaire.profile.save(update_fields=['est_actif'])
    secretaire.user.is_active = new_state
    secretaire.user.save(update_fields=['is_active'])

    action = 'activé' if new_state else 'désactivé'
    return Response({
        "is_active": new_state,
        "message": f"Le secrétaire a été {action} avec succès.",
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_professors(request):
    """Liste les professeurs (accessible à tous les administrateurs)"""
    if not can_manage_users(request.user):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)

    professors = Professor.objects.values(
        'id', 'nom', 'email', 'specialite', 'faculte'
    )
    return Response(list(professors))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_students(request):
    """Liste les étudiants (accessible à tous les administrateurs)"""
    if not can_manage_users(request.user):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)

    students = Student.objects.values(
        'id', 'nom', 'email', 'niveau', 'faculte', 'matricule'
    )
    return Response(list(students))


# Endpoints pour les Facultés

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_faculties(request):
    """Liste toutes les facultés disponibles"""
    faculties = Faculty.objects.all().values('code', 'nom', 'description', 'doyen', 'email')
    return Response(list(faculties))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_faculty(request, faculty_code):
    """Récupère les détails d'une faculté"""
    try:
        faculty = Faculty.objects.get(code=faculty_code)
        return Response({
            'code': faculty.code,
            'nom': faculty.nom,
            'description': faculty.description,
            'doyen': faculty.doyen,
            'email': faculty.email,
            'telephone': faculty.telephone,
            'adresse': faculty.adresse,
        })
    except Faculty.DoesNotExist:
        return Response({"error": "Faculté non trouvée"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_faculty_professors(request, faculty_code):
    """Récupère tous les professeurs d'une faculté"""
    try:
        faculty = Faculty.objects.get(code=faculty_code)
        professors = Professor.objects.filter(faculte=faculty).values(
            'id', 'nom', 'email', 'specialite', 'telephone'
        )
        return Response({
            'faculte': faculty.nom,
            'professeurs': list(professors)
        })
    except Faculty.DoesNotExist:
        return Response({"error": "Faculté non trouvée"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_faculty_students(request, faculty_code):
    """Récupère tous les étudiants d'une faculté"""
    try:
        faculty = Faculty.objects.get(code=faculty_code)
        students = Student.objects.filter(faculte=faculty).values(
            'id', 'nom', 'email', 'niveau', 'matricule'
        )
        return Response({
            'faculte': faculty.nom,
            'etudiants': list(students)
        })
    except Faculty.DoesNotExist:
        return Response({"error": "Faculté non trouvée"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_faculty(request, faculty_code):
    """Met à jour partiellement les informations d'une faculté."""
    if not (request.user.is_staff or can_manage_users(request.user)):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)
    try:
        faculty = Faculty.objects.get(code=faculty_code)
    except Faculty.DoesNotExist:
        return Response({"error": "Faculté non trouvée"}, status=status.HTTP_404_NOT_FOUND)

    updatable_fields = ['nom', 'description', 'doyen', 'email', 'telephone', 'adresse']
    for field in updatable_fields:
        if field in request.data:
            setattr(faculty, field, request.data[field])
    faculty.save()

    return Response({
        'code': faculty.code,
        'nom': faculty.nom,
        'description': faculty.description,
        'doyen': faculty.doyen,
        'email': faculty.email,
        'telephone': faculty.telephone,
        'adresse': faculty.adresse,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Retourne les statistiques adaptées au rôle de l'utilisateur connecté."""
    user = request.user
    try:
        profile = user.profile
        role = profile.role.nom if profile.role else None
    except UserProfile.DoesNotExist:
        role = None

    is_central = user_has_role(user, 'admin_central') or user.is_superuser

    # ── Admin Central ────────────────────────────────────────────────────────
    if is_central:
        total_users = User.objects.count()
        total_gestionnaires = AdminGestionnaire.objects.count()
        total_secretaires = SecretaireFacultaire.objects.count()
        total_professors = Professor.objects.count()
        total_students = Student.objects.count()
        total_faculties = Faculty.objects.count()
        total_roles = Role.objects.count()

        # Répartition étudiants par faculté
        students_by_faculty = list(
            Student.objects.values('faculte__nom').annotate(count=Count('id'))
            .order_by('-count')
        )
        professors_by_faculty = list(
            Professor.objects.values('faculte__nom').annotate(count=Count('id'))
            .order_by('-count')
        )

        return Response({
            'role': 'admin_central',
            'stats': [
                {'label': 'Utilisateurs totaux', 'value': total_users, 'icon': '👥', 'color': '#6366f1'},
                {'label': 'Gestionnaires', 'value': total_gestionnaires, 'icon': '💼', 'color': '#8b5cf6'},
                {'label': 'Secrétaires', 'value': total_secretaires, 'icon': '📋', 'color': '#06b6d4'},
                {'label': 'Professeurs', 'value': total_professors, 'icon': '👨‍🏫', 'color': '#10b981'},
                {'label': 'Étudiants', 'value': total_students, 'icon': '🎓', 'color': '#f59e0b'},
                {'label': 'Facultés', 'value': total_faculties, 'icon': '🏢', 'color': '#ec4899'},
            ],
            'charts': {
                'students_by_faculty': students_by_faculty,
                'professors_by_faculty': professors_by_faculty,
            }
        })

    # ── Admin Gestionnaire ───────────────────────────────────────────────────
    if role == 'admin_gestionnaire':
        gestionnaire = AdminGestionnaire.objects.filter(user=user).first()
        if gestionnaire:
            secretaires = SecretaireFacultaire.objects.filter(admin_gestionnaire=gestionnaire)
            nb_secretaires = secretaires.count()
            # Facultés distinctes gérées
            faculties = Faculty.objects.filter(secretaires__admin_gestionnaire=gestionnaire).distinct()
            nb_faculties = faculties.count()
            # Professeurs enregistrés par ces secrétaires
            nb_professors = Professor.objects.filter(enregistre_par__in=secretaires).count()

            secretaires_list = []
            for sec in secretaires:
                secretaires_list.append({
                    'nom': sec.profile.nom_complet or sec.user.username,
                    'faculte': sec.faculte.nom if sec.faculte else '-',
                    'nb_professors': Professor.objects.filter(enregistre_par=sec).count(),
                })
        else:
            nb_secretaires = nb_faculties = nb_professors = 0
            secretaires_list = []

        return Response({
            'role': 'admin_gestionnaire',
            'stats': [
                {'label': 'Mes Secrétaires', 'value': nb_secretaires, 'icon': '📋', 'color': '#06b6d4'},
                {'label': 'Facultés gérées', 'value': nb_faculties, 'icon': '🏢', 'color': '#6366f1'},
                {'label': 'Professeurs inscrits', 'value': nb_professors, 'icon': '👨‍🏫', 'color': '#10b981'},
            ],
            'charts': {
                'secretaires': secretaires_list,
            }
        })

    # ── Secrétaire Facultaire ────────────────────────────────────────────────
    if role == 'secretaire_facultaire':
        secretaire = SecretaireFacultaire.objects.filter(user=user).first()
        if secretaire:
            faculte = secretaire.faculte
            nb_professors = Professor.objects.filter(faculte=faculte).count()
            from courses.models import Course, CourseNote
            nb_courses = Course.objects.filter(faculte=faculte).count()
            nb_students = Student.objects.filter(faculte=faculte).count()

            professors_list = list(
                Professor.objects.filter(faculte=faculte)
                .values('nom', 'specialite', 'email')[:10]
            )
        else:
            nb_professors = nb_courses = nb_students = 0
            professors_list = []
            faculte = None

        return Response({
            'role': 'secretaire_facultaire',
            'faculte': faculte.nom if faculte else '-',
            'stats': [
                {'label': 'Professeurs', 'value': nb_professors, 'icon': '👨‍🏫', 'color': '#10b981'},
                {'label': 'Cours disponibles', 'value': nb_courses, 'icon': '📚', 'color': '#6366f1'},
                {'label': 'Étudiants inscrits', 'value': nb_students, 'icon': '🎓', 'color': '#f59e0b'},
            ],
            'charts': {
                'professors': professors_list,
            }
        })

    # ── Professeur ───────────────────────────────────────────────────────────
    if role == 'professeur':
        professor = Professor.objects.filter(user=user).first()
        if professor:
            from courses.models import Course, CourseNote
            nb_courses = Course.objects.filter(enseignants=professor).count()
            nb_notes = CourseNote.objects.filter(professor=professor).count()
            courses_list = list(
                Course.objects.filter(enseignants=professor)
                .values('id', 'titre', 'date_creation')[:10]
            )
            recent_notes = list(
                CourseNote.objects.filter(professor=professor)
                .values('title', 'created_at')[:5]
            )
        else:
            nb_courses = nb_notes = 0
            courses_list = recent_notes = []

        return Response({
            'role': 'professeur',
            'stats': [
                {'label': 'Mes cours', 'value': nb_courses, 'icon': '📚', 'color': '#6366f1'},
                {'label': 'Notes publiées', 'value': nb_notes, 'icon': '📝', 'color': '#10b981'},
            ],
            'charts': {
                'courses': courses_list,
                'recent_notes': recent_notes,
            }
        })

    # ── Étudiant ─────────────────────────────────────────────────────────────
    if role == 'etudiant' or (not role and not user.is_staff):
        student = Student.objects.filter(user=user).first()
        from chatbot.models import Conversation
        nb_conversations = Conversation.objects.filter(user=user).count() if user else 0
        from courses.models import Course
        nb_courses = Course.objects.count()  # visible courses
        if student and student.faculte:
            nb_courses_faculty = Course.objects.filter(faculte=student.faculte).count()
        else:
            nb_courses_faculty = 0

        return Response({
            'role': 'etudiant',
            'student': {
                'nom': student.nom if student else user.username,
                'niveau': student.niveau if student else '-',
                'faculte': student.faculte.nom if student and student.faculte else '-',
                'matricule': student.matricule if student else '-',
            },
            'stats': [
                {'label': 'Conversations IA', 'value': nb_conversations, 'icon': '💬', 'color': '#6366f1'},
                {'label': 'Cours disponibles', 'value': nb_courses, 'icon': '📚', 'color': '#10b981'},
                {'label': 'Cours de ma faculté', 'value': nb_courses_faculty, 'icon': '🏢', 'color': '#f59e0b'},
            ],
            'charts': {}
        })

    # Fallback
    return Response({'role': role or 'unknown', 'stats': [], 'charts': {}})