# Generated by Django 5.1.6 on 2025-03-01 20:10

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('api', '0002_remove_contest_end_datetime_and_more'), ('api', '0003_remove_contest_datetime_range_contest_end_datetime_and_more')]

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contest',
            name='end_datetime',
        ),
        migrations.RemoveField(
            model_name='contest',
            name='start_datetime',
        ),
        migrations.AddField(
            model_name='contest',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='solution',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='task',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='team',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='team',
            name='individual',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contest',
            name='end_datetime',
            field=models.DateTimeField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='contest',
            name='start_datetime',
            field=models.DateTimeField(null=True),
        ),
    ]
