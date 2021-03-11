# Generated by Django 3.1.7 on 2021-03-09 09:10

import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import itou.utils.models


class Migration(migrations.Migration):

    dependencies = [
        ("siaes", "0044_auto_20210202_1142"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("approvals", "0011_suspension_create_trigger"),
    ]

    operations = [
        migrations.AlterField(
            model_name="approval",
            name="end_at",
            field=models.DateField(db_index=True, default=django.utils.timezone.localdate, verbose_name="Date de fin"),
        ),
        migrations.AlterField(
            model_name="approval",
            name="start_at",
            field=models.DateField(
                db_index=True, default=django.utils.timezone.localdate, verbose_name="Date de début"
            ),
        ),
        migrations.AlterField(
            model_name="poleemploiapproval",
            name="birthdate",
            field=models.DateField(default=django.utils.timezone.localdate, verbose_name="Date de naissance"),
        ),
        migrations.AlterField(
            model_name="poleemploiapproval",
            name="end_at",
            field=models.DateField(db_index=True, default=django.utils.timezone.localdate, verbose_name="Date de fin"),
        ),
        migrations.AlterField(
            model_name="poleemploiapproval",
            name="start_at",
            field=models.DateField(
                db_index=True, default=django.utils.timezone.localdate, verbose_name="Date de début"
            ),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="end_at",
            field=models.DateField(db_index=True, default=django.utils.timezone.localdate, verbose_name="Date de fin"),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="start_at",
            field=models.DateField(
                db_index=True, default=django.utils.timezone.localdate, verbose_name="Date de début"
            ),
        ),
        migrations.CreateModel(
            name="Prolongation",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "start_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="Date de début"
                    ),
                ),
                (
                    "end_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="Date de fin"
                    ),
                ),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("COMPLETE_TRAINING", "Fin d'une formation (6 mois maximum)"),
                            ("RQTH", "RQTH (12 mois maximum)"),
                            ("SENIOR", "50 ans et plus (12 mois maximum)"),
                            (
                                "PARTICULAR_DIFFICULTIES",
                                "Difficultés particulières qui font obstacle à l'insertion durable dans l’emploi "
                                "(12 mois maximum dans la limite de 5 ans)",
                            ),
                        ],
                        default="COMPLETE_TRAINING",
                        max_length=30,
                        verbose_name="Motif",
                    ),
                ),
                ("reason_explanation", models.TextField(blank=True, verbose_name="Explications supplémentaires")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(blank=True, null=True, verbose_name="Date de modification")),
                (
                    "approval",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="approvals.approval", verbose_name="PASS IAE"
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approvals_prolongations_created_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Créé par",
                    ),
                ),
                (
                    "declared_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approvals_prolongation_declared_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Déclarée par",
                    ),
                ),
                (
                    "declared_by_siae",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="siaes.siae",
                        verbose_name="SIAE du déclarant",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Mis à jour par",
                    ),
                ),
                (
                    "validated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approvals_prolongations_validated_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Prescripteur habilité qui a autorisé cette prolongation",
                    ),
                ),
            ],
            options={
                "verbose_name": "Prolongation",
                "verbose_name_plural": "Prolongations",
                "ordering": ["-start_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="prolongation",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=(
                    (
                        itou.utils.models.DateRange(
                            "start_at",
                            "end_at",
                            django.contrib.postgres.fields.ranges.RangeBoundary(
                                inclusive_lower=True, inclusive_upper=False
                            ),
                        ),
                        "&&",
                    ),
                    ("approval", "="),
                ),
                name="exclude_overlapping_prolongations",
            ),
        ),
    ]
