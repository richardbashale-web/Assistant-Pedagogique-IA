from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0004_alter_conversation_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='summary',
            field=models.TextField(blank=True, default=''),
        ),
    ]
