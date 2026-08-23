from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('courses', '0008_course_promotions')]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='professeur',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name='courses',
                to='users.professor',
            ),
        ),
    ]
