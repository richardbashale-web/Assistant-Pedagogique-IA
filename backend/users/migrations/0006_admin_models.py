from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_role_userprofile'),
    ]

    operations = [
        # D'abord créer les modèles administrateurs sans ForeignKey
        migrations.CreateModel(
            name='AdminCentral',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_nomination', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('profile', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admin_central', to='users.userprofile')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admin_central_profile', to='auth.user')),
            ],
            options={
                'verbose_name': 'Admin Central',
                'verbose_name_plural': 'Admins Centraux',
            },
        ),
        migrations.CreateModel(
            name='AdminGestionnaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_nomination', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('profile', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admin_gestionnaire', to='users.userprofile')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admin_gestionnaire_profile', to='auth.user')),
            ],
            options={
                'verbose_name': 'Admin Gestionnaire',
                'verbose_name_plural': 'Admins Gestionnaires',
            },
        ),
        migrations.CreateModel(
            name='SecretaireFacultaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('faculte', models.CharField(max_length=100)),
                ('date_nomination', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('profile', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='secretaire', to='users.userprofile')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='secretaire_profile', to='auth.user')),
            ],
            options={
                'verbose_name': 'Secrétaire Facultaire',
                'verbose_name_plural': 'Secrétaires Facultaires',
            },
        ),
        # Puis ajouter les ForeignKey
        migrations.AddField(
            model_name='admingestionnaire',
            name='admin_central',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gestionnaires_geres', to='users.admincentral'),
        ),
        migrations.AddField(
            model_name='secretairefacultaire',
            name='admin_gestionnaire',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='secretaires_geres', to='users.admingestionnaire'),
        ),
        # Modifier Professor et Student
        migrations.AddField(
            model_name='professor',
            name='profile',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='professor', to='users.userprofile'),
        ),
        migrations.AddField(
            model_name='professor',
            name='faculte',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='professor',
            name='telephone',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='professor',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='professor',
            name='enregistre_par',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='professeurs_enregistres', to='users.secretairefacultaire'),
        ),
        migrations.AddField(
            model_name='student',
            name='profile',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student', to='users.userprofile'),
        ),
        migrations.AddField(
            model_name='student',
            name='matricule',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='student',
            name='faculte',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='student',
            name='notes',
            field=models.TextField(blank=True),
        ),
    ]
