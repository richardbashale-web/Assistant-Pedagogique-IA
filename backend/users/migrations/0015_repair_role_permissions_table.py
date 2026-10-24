from django.db import migrations


def ensure_role_permissions_table(apps, schema_editor):
    role_model = apps.get_model('users', 'Role')
    permissions_field = role_model._meta.get_field('permissions')
    through_model = permissions_field.remote_field.through
    table_name = through_model._meta.db_table

    existing_tables = schema_editor.connection.introspection.table_names()
    if table_name not in existing_tables:
        schema_editor.create_model(through_model)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_alter_professor_postnom_alter_student_postnom'),
    ]

    operations = [
        migrations.RunPython(
            ensure_role_permissions_table,
            migrations.RunPython.noop,
        ),
    ]
