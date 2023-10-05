# Generated by Django 5.0.7 on 2024-08-06 09:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cities", "0001_initial"),
        ("companies", "0005_company_rdv_insertion_id"),
        ("jobs", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="company",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="created_company_set",
                to=settings.AUTH_USER_MODEL,
                verbose_name="créé par",
            ),
        ),
        migrations.AlterField(
            model_name="company",
            name="insee_city",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to="cities.city"
            ),
        ),
        migrations.AlterField(
            model_name="companymembership",
            name="updated_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="updated_companymembership_set",
                to=settings.AUTH_USER_MODEL,
                verbose_name="mis à jour par",
            ),
        ),
        migrations.AlterField(
            model_name="jobdescription",
            name="appellation",
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to="jobs.appellation"),
        ),
        migrations.AlterField(
            model_name="jobdescription",
            name="location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to="cities.city",
                verbose_name="localisation du poste",
            ),
        ),
        migrations.AlterField(
            model_name="siaeconvention",
            name="reactivated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="reactivated_siae_convention_set",
                to=settings.AUTH_USER_MODEL,
                verbose_name="réactivée manuellement par",
            ),
        ),
    ]
