"""
Fichier de migration pour ajouter les modèles de rôles et permissions
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_professor'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(choices=[('admin_central', 'Administrateur Central'), ('admin_gestionnaire', 'Administrateur Gestionnaire'), ('professeur', 'Professeur'), ('secretaire_facultaire', 'Secrétaire Facultaire'), ('etudiant', 'Étudiant')], max_length=50, unique=True)),
                ('description', models.TextField()),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Rôle',
                'verbose_name_plural': 'Rôles',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_complet', models.CharField(blank=True, max_length=100)),
                ('telephone', models.CharField(blank=True, max_length=20)),
                ('adresse', models.TextField(blank=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('est_actif', models.BooleanField(default=True)),
                ('role', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='utilisateurs', to='users.role')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='auth.user')),
            ],
            options={
                'verbose_name': 'Profil Utilisateur',
                'verbose_name_plural': 'Profils Utilisateurs',
            },
        ),
    ]


    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(choices=[('admin_central', 'Administrateur Central'), ('admin_gestionnaire', 'Administrateur Gestionnaire'), ('professeur', 'Professeur'), ('secretaire_facultaire', 'Secrétaire Facultaire'), ('etudiant', 'Étudiant')], max_length=50, unique=True)),
                ('description', models.TextField()),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Rôle',
                'verbose_name_plural': 'Rôles',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_complet', models.CharField(blank=True, max_length=100)),
                ('telephone', models.CharField(blank=True, max_length=20)),
                ('adresse', models.TextField(blank=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('est_actif', models.BooleanField(default=True)),
                ('role', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='utilisateurs', to='users.role')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='auth.user')),
            ],
            options={
                'verbose_name': 'Profil Utilisateur',
                'verbose_name_plural': 'Profils Utilisateurs',
            },
        ),
    ]
