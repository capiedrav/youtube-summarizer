# Generated by Django 5.1 on 2025-04-11 01:25

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='YTSummary',
            fields=[
                ('video_id', models.CharField(default=None, max_length=22, primary_key=True, serialize=False)),
                ('url', models.URLField(default=None, validators=[django.core.validators.RegexValidator(message='Enter a valid youtube url.', regex='^(https?://)?(www\\.)?(youtube\\.com|youtu\\.be)/(watch\\?v=)([a-z]|[A-Z]|[0-9]|[\\-_])+$')])),
                ('video_text', models.TextField(default=None)),
                ('video_summary', models.TextField(default=None)),
                ('created_on', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
