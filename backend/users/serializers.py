from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction

from .models import Student, Professor, UserProfile
from .permissions import assign_role_to_user


class StudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8
    )

    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = Student
        fields = '__all__'
        extra_kwargs = {
            'matricule': {'required': True},
        }

    def validate_matricule(self, value):
        qs = Student.objects.filter(matricule=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ce matricule est déjà attribué à un autre étudiant."
            )

        return value

    def validate_username(self, value):
        qs = User.objects.filter(username=value)

        if self.instance and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ce nom d'utilisateur est déjà utilisé."
            )

        return value

    def validate_email(self, value):
        qs = User.objects.filter(email=value)

        if self.instance and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée."
            )

        return value

    def validate(self, attrs):
        if not self.instance:
            if not attrs.get('username'):
                raise serializers.ValidationError({
                    'username': "Le nom d'utilisateur est obligatoire."
                })

            if not attrs.get('password'):
                raise serializers.ValidationError({
                    'password': "Le mot de passe est obligatoire."
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')

        email = validated_data.get('email', '')
        prenom = validated_data.get('prenom', '')
        nom = validated_data.get('nom', '')
        postnom = validated_data.get('postnom', '')
        telephone = validated_data.get('telephone', '')

        # Créer le compte Django.
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=prenom,
            last_name=f"{nom} {postnom}".strip(),
        )

        # Créer le profil.
        nom_complet = " ".join(
            filter(None, [nom, postnom, prenom])
        )

        profile = UserProfile.objects.create(
            user=user,
            nom_complet=nom_complet or username,
            telephone=telephone,
            est_actif=True,
        )

        # Attribuer et vérifier le rôle étudiant.
        assign_role_to_user(user, 'etudiant')
        profile.refresh_from_db()

        if not profile.role or profile.role.nom != 'etudiant':
            raise serializers.ValidationError(
                "Impossible d'attribuer le rôle étudiant à ce compte."
            )

        # Créer l'étudiant seulement si le rôle est correct.
        student = Student.objects.create(
            user=user,
            profile=profile,
            **validated_data
        )

        return student

    @transaction.atomic
    def update(self, instance, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)

        user = instance.user

        if user:
            if username and username != user.username:
                if User.objects.filter(
                    username=username
                ).exclude(pk=user.pk).exists():
                    raise serializers.ValidationError({
                        'username':
                            "Ce nom d'utilisateur est déjà utilisé."
                    })

                user.username = username

            if password:
                user.set_password(password)

            if 'email' in validated_data:
                user.email = validated_data['email']

            if 'prenom' in validated_data:
                user.first_name = validated_data['prenom']

            if 'nom' in validated_data or 'postnom' in validated_data:
                nom = validated_data.get('nom', instance.nom)
                postnom = validated_data.get('postnom', instance.postnom)
                user.last_name = f"{nom} {postnom}".strip()

            user.save()

            if instance.profile:
                nom_complet = " ".join(
                    filter(
                        None,
                        [
                            validated_data.get('nom', instance.nom),
                            validated_data.get('postnom', instance.postnom),
                            validated_data.get('prenom', instance.prenom),
                        ]
                    )
                )

                instance.profile.nom_complet = nom_complet

                if 'telephone' in validated_data:
                    instance.profile.telephone = validated_data['telephone']

                instance.profile.save()

        return super().update(instance, validated_data)

class ProfessorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8
    )

    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = Professor
        fields = '__all__'
        extra_kwargs = {
            'sexe': {'required': False, 'allow_blank': True},
        }

    def validate_username(self, value):
        qs = User.objects.filter(username=value)

        if self.instance and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ce nom d'utilisateur est déjà utilisé."
            )

        return value

    def validate_email(self, value):
        qs = User.objects.filter(email=value)

        if self.instance and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée."
            )

        return value

    def validate_sexe(self, value):
        return value or 'M'

    def validate(self, attrs):
        if not self.instance:
            if not attrs.get('username'):
                raise serializers.ValidationError({
                    'username': "Le nom d'utilisateur est obligatoire."
                })

            if not attrs.get('password'):
                raise serializers.ValidationError({
                    'password': "Le mot de passe est obligatoire."
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')

        email = validated_data.get('email', '')
        prenom = validated_data.get('prenom', '')
        nom = validated_data.get('nom', '')
        postnom = validated_data.get('postnom', '')
        telephone = validated_data.get('telephone', '')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=prenom,
            last_name=f"{nom} {postnom}".strip(),
        )

        nom_complet = " ".join(
            filter(None, [nom, postnom, prenom])
        )

        profile = UserProfile.objects.create(
            user=user,
            nom_complet=nom_complet or username,
            telephone=telephone,
            est_actif=True,
        )

        # Attribuer et vérifier le rôle avant de créer le professeur.
        assign_role_to_user(user, 'professeur')
        profile.refresh_from_db()

        if not profile.role or profile.role.nom != 'professeur':
            raise serializers.ValidationError(
                "Impossible d'attribuer le rôle professeur à ce compte."
            )

        professor = Professor.objects.create(
            user=user,
            profile=profile,
            **validated_data
        )

        return professor

    @transaction.atomic
    def update(self, instance, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)

        user = instance.user

        if user:
            if username and username != user.username:
                if User.objects.filter(
                    username=username
                ).exclude(pk=user.pk).exists():
                    raise serializers.ValidationError({
                        'username':
                            "Ce nom d'utilisateur est déjà utilisé."
                    })

                user.username = username

            if password:
                user.set_password(password)

            if 'email' in validated_data:
                user.email = validated_data['email']

            if 'prenom' in validated_data:
                user.first_name = validated_data['prenom']

            if 'nom' in validated_data or 'postnom' in validated_data:
                nom = validated_data.get('nom', instance.nom)
                postnom = validated_data.get('postnom', instance.postnom)
                user.last_name = f"{nom} {postnom}".strip()

            user.save()

            if instance.profile:
                nom_complet = " ".join(
                    filter(
                        None,
                        [
                            validated_data.get('nom', instance.nom),
                            validated_data.get('postnom', instance.postnom),
                            validated_data.get('prenom', instance.prenom),
                        ]
                    )
                )

                instance.profile.nom_complet = nom_complet

                if 'telephone' in validated_data:
                    instance.profile.telephone = validated_data['telephone']

                instance.profile.save()

        return super().update(instance, validated_data)
