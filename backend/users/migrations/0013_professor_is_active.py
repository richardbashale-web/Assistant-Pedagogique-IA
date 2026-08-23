from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('users', '0011_alter_professor_options_and_more')]
    operations = [
        migrations.AddField(
            model_name='professor',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Compte actif'),
        ),
    ]
