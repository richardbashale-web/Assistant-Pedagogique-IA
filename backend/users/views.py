from rest_framework import generics, status
from .models import Student, Professor, Role, UserProfile, Faculty, AdminCentral, AdminGestionnaire
from .serializers import StudentSerializer, ProfessorSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from .permissions import can_manage_users, user_has_role, assign_role_to_user

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
        serializer.save()

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

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        professor = getattr(request.user, 'professor_profile', None)
        student = getattr(request.user, 'student_profile', None)
        profile = getattr(request.user, 'profile', None)
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "is_staff": request.user.is_staff,
            "is_professor": bool(professor),
            "is_student": bool(student),
            "professor_id": professor.id if professor else None,
            "role": profile.role.nom if profile and profile.role else None,
            "role_display": profile.role.get_nom_display() if profile and profile.role else None,
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
    """Crée un secrétaire facultaire (Admin Gestionnaire seulement)"""
    if not user_has_role(request.user, 'admin_gestionnaire'):
        return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)

    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    nom_complet = request.data.get('nom_complet')
    faculte = request.data.get('faculte')

    if not all([username, email, password, faculte]):
        return Response({"error": "Données manquantes"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(username=username, email=email, password=password)
        profile = UserProfile.objects.create(user=user, nom_complet=nom_complet)
        assign_role_to_user(user, 'secretaire_facultaire')

        admin_gestionnaire_user = request.user
        admin_gestionnaire = AdminGestionnaire.objects.get(user=admin_gestionnaire_user)
        SecretaireFacultaire.objects.create(
            user=user,
            profile=profile,
            admin_gestionnaire=admin_gestionnaire,
            faculte=faculte
        )

        return Response({
            "success": "Secrétaire facultaire créé",
            "user_id": user.id,
            "username": user.username
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
