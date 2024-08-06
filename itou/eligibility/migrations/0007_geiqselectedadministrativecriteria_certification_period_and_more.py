# Generated by Django 5.0.8 on 2024-09-09 15:22

from django.db import migrations, models

import itou.utils.models


class Migration(migrations.Migration):
    dependencies = [
        ("eligibility", "0006_remove_administrativecriteria_certifiable_and_add_kind"),
    ]

    operations = [
        migrations.AddField(
            model_name="geiqselectedadministrativecriteria",
            name="certification_period",
            field=itou.utils.models.InclusiveDateRangeField(null=True, verbose_name="période de certification"),
        ),
        migrations.AddField(
            model_name="geiqselectedadministrativecriteria",
            name="certified",
            field=models.BooleanField(null=True, verbose_name="certifié par l'API Particulier"),
        ),
        migrations.AddField(
            model_name="geiqselectedadministrativecriteria",
            name="certified_at",
            field=models.DateTimeField(null=True, verbose_name="certifié le"),
        ),
        migrations.AddField(
            model_name="geiqselectedadministrativecriteria",
            name="data_returned_by_api",
            field=models.JSONField(null=True, verbose_name="résultat renvoyé par l'API Particulier"),
        ),
        migrations.AddField(
            model_name="selectedadministrativecriteria",
            name="certification_period",
            field=itou.utils.models.InclusiveDateRangeField(null=True, verbose_name="période de certification"),
        ),
        migrations.AddField(
            model_name="selectedadministrativecriteria",
            name="certified",
            field=models.BooleanField(null=True, verbose_name="certifié par l'API Particulier"),
        ),
        migrations.AddField(
            model_name="selectedadministrativecriteria",
            name="certified_at",
            field=models.DateTimeField(null=True, verbose_name="certifié le"),
        ),
        migrations.AddField(
            model_name="selectedadministrativecriteria",
            name="data_returned_by_api",
            field=models.JSONField(null=True, verbose_name="résultat renvoyé par l'API Particulier"),
        ),
    ]
