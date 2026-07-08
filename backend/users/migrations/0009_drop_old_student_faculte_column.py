from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_admingestionnaire_admin_central_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE users_student
                DROP COLUMN IF EXISTS faculte;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
