from django.db import migrations, models


def copy_existing_professor(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    for course in Course.objects.exclude(professeur__isnull=True):
        course.enseignants.add(course.professeur_id)


class Migration(migrations.Migration):
    dependencies = [('courses', '0009_course_professeur_optional')]

    operations = [
        migrations.AddField(
            model_name='course',
            name='enseignants',
            field=models.ManyToManyField(blank=True, related_name='cours_attribues', to='users.professor'),
        ),
        migrations.RunPython(copy_existing_professor, migrations.RunPython.noop),
    ]
