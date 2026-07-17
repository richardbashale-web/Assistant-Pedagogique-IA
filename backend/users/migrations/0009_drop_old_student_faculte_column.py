from django.db import migrations, connection


def drop_old_student_faculte_column(apps, schema_editor):
    """Supprime l'ancienne colonne legacy si elle existe.

    SQLite ne prend pas en charge DROP COLUMN dans les versions utilisées ici,
    donc on rend la migration sûre et sans effet sur cet environnement.
    """
    if schema_editor.connection.vendor != 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(users_student)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'faculte' in columns:
                cursor.execute("ALTER TABLE users_student DROP COLUMN faculte")


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_admingestionnaire_admin_central_and_more'),
    ]

    operations = [
        migrations.RunPython(drop_old_student_faculte_column, migrations.RunPython.noop),
    ]
