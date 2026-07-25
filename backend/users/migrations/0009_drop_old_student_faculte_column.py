from django.db import migrations, connection


def drop_old_student_faculte_column(apps, schema_editor):
    """Supprime l'ancienne colonne legacy si elle existe."""
    if schema_editor.connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE users_student DROP COLUMN IF EXISTS faculte;")



class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_admingestionnaire_admin_central_and_more'),
    ]

    operations = [
        migrations.RunPython(drop_old_student_faculte_column, migrations.RunPython.noop),
    ]
