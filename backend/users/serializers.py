from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction

from .models import Student, Professor, UserProfile
from .permissions import assign_role_to_user


class StudentSerializer(serializers.ModelSerializer):
    # Identifiants du compte Django
    username = serializers.CharField(
        write_only=True,
        required=False
    )

    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8
    )

    # Username visible en lecture
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
        """Vérifie que le matricule n'est pas déjà utilisé."""
        qs = Student.objects.filter(matricule=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ce matricule est déjà attribué à un autre étudiant."
            )

        return value

    def validate_username(self, value):
        """Vérifie l'unicité du username Django."""
        qs = User.objects.filter(username=value)

        if self.instance and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ce nom d'utilisateur est déjà utilisé."
            )

        return value

    def validate_email(self, value):
        """Vérifie que l'email n'est pas déjà utilisé."""
        qs = User.objects.filter(email=value)

        if self.instance and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée."
            )

        return value

    def validate(self, attrs):
        """
        Lors d'une création, username et password sont obligatoires.
        Lors d'une modification, ils deviennent facultatifs.
        """
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

        # Création du compte Django
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=prenom,
            last_name=f"{nom} {postnom}".strip(),
        )

        # Création du profil utilisateur
        nom_complet = " ".join(
            filter(None, [nom, postnom, prenom])
        )

        profile = UserProfile.objects.create(
            user=user,
            nom_complet=nom_complet,
            telephone=telephone,
            est_actif=True,
        )

        # Attribution du rôle
        assign_role_to_user(user, 'etudiant')

        # Création de l'étudiant
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
            # Username
            if username and username != user.username:
                if User.objects.filter(
                    username=username
                ).exclude(pk=user.pk).exists():
                    raise serializers.ValidationError({
                        'username':
                            "Ce nom d'utilisateur est déjà utilisé."
                    })

                user.username = username

            # Password
            if password:
                user.set_password(password)

            # Email
            if 'email' in validated_data:
                user.email = validated_data['email']

            # Prénom
            if 'prenom' in validated_data:
                user.first_name = validated_data['prenom']

            # Nom / postnom
            if (
                'nom' in validated_data
                or 'postnom' in validated_data
            ):
                nom = validated_data.get('nom', instance.nom)
                postnom = validated_data.get(
                    'postnom',
                    instance.postnom
                )

                user.last_name = f"{nom} {postnom}".strip()

            user.save()

            # Mise à jour du UserProfile
            if instance.profile:
                nom_complet = " ".join(
                    filter(
                        None,
                        [
                            validated_data.get(
                                'nom',
                                instance.nom
                            ),
                            validated_data.get(
                                'postnom',
                                instance.postnom
                            ),
                            validated_data.get(
                                'prenom',
                                instance.prenom
                            ),
                        ]
                    )
                )

                instance.profile.nom_complet = nom_complet

                if 'telephone' in validated_data:
                    instance.profile.telephone = validated_data[
                        'telephone'
                    ]

                instance.profile.save()

        return super().update(instance, validated_data)


class ProfessorSerializer(serializers.ModelSerializer):
    # Identifiants du compte Django
    username = serializers.CharField(
        write_only=True,
        required=False
    )

    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8
    )

    # Username visible dans les réponses GET
    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = Professor
        fields = '__all__'

    def validate_username(self, value):
        """Vérifie l'unicité du username Django."""
        qs = User.objects.filter(username=value)

        if self.instance and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ce nom d'utilisateur est déjà utilisé."
            )

        return value

    def validate_email(self, value):
        """Vérifie l'unicité de l'email."""
        qs = User.objects.filter(email=value)

        if self.instance and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée."
            )

        return value

    def validate(self, attrs):
        """
        Création :
            username obligatoire
            password obligatoire

        Modification :
            username facultatif
            password facultatif
        """
        if not self.instance:
            if not attrs.get('username'):
                raise serializers.ValidationError({
                    'username': "Le nom d'utilisateur est obligatoire."
                })

            if not attrs.get('password'):
                raise serializers.ValidationError({
                    'password':
                        "Le mot de passe est obligatoire."
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

        # Création du compte Django
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=prenom,
            last_name=f"{nom} {postnom}".strip(),
        )

        # Création du profil
        nom_complet = " ".join(
            filter(None, [nom, postnom, prenom])
        )

        profile = UserProfile.objects.create(
            user=user,
            nom_complet=nom_complet,
            telephone=telephone,
            est_actif=True,
        )

        # Attribution du rôle professeur
        assign_role_to_user(user, 'professeur')

        # Création du professeur
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
            # Modification du username
            if username and username != user.username:
                if User.objects.filter(
                    username=username
                ).exclude(pk=user.pk).exists():
                    raise serializers.ValidationError({
                        'username':
                            "Ce nom d'utilisateur est déjà utilisé."
                    })

                user.username = username

            # Modification du password
            if password:
                user.set_password(password)

            # Email
            if 'email' in validated_data:
                user.email = validated_data['email']

            # Prénom
            if 'prenom' in validated_data:
                user.first_name = validated_data['prenom']

            # Nom + postnom
            if (
                'nom' in validated_data
                or 'postnom' in validated_data
            ):
                nom = validated_data.get(
                    'nom',
                    instance.nom
                )

                postnom = validated_data.get(
                    'postnom',
                    instance.postnom
                )

                user.last_name = f"{nom} {postnom}".strip()

            user.save()

            # Mise à jour du profil
            if instance.profile:
                nom_complet = " ".join(
                    filter(
                        None,
                        [
                            validated_data.get(
                                'nom',
                                instance.nom
                            ),
                            validated_data.get(
                                'postnom',
                                instance.postnom
                            ),
                            validated_data.get(
                                'prenom',
                                instance.prenom
                            ),
                        ]
                    )
                )

                instance.profile.nom_complet = nom_complet

                if 'telephone' in validated_data:
                    instance.profile.telephone = validated_data[
                        'telephone'
                    ]

                instance.profile.save()

        return super().update(instance, validated_data)