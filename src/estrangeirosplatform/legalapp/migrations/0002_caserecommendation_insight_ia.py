from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legalapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='caserecommendation',
            name='insight_ia',
            field=models.TextField(blank=True, default=''),
        ),
    ]
