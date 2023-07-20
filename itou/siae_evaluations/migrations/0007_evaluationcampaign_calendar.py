# Generated by Django 4.1.9 on 2023-06-05 21:21

import django.db.models.deletion
from django.db import migrations, models

import itou.utils.validators


class Migration(migrations.Migration):
    dependencies = [
        ("siae_evaluations", "0006_evaluatedsiae_final_reviewed_at_only_after_reviewed_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="Calendar",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, null=True, verbose_name="nom")),
                ("html", models.TextField(verbose_name="contenu")),
            ],
            options={
                "verbose_name": "calendrier",
            },
        ),
        migrations.AddField(
            model_name="evaluationcampaign",
            name="calendar",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="siae_evaluations.calendar",
                validators=[itou.utils.validators.validate_html],
                verbose_name="calendrier",
            ),
        ),
    ]
