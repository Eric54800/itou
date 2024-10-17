# Generated by Django 5.0.3 on 2024-03-23 08:23

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import itou.siae_evaluations.models
import itou.utils.models
import itou.utils.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("companies", "0001_initial"),
        ("eligibility", "0001_initial"),
        ("files", "0001_initial"),
        ("institutions", "0001_initial"),
        ("job_applications", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Calendar",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, null=True, verbose_name="nom")),
                ("html", models.TextField(validators=[itou.utils.validators.validate_html], verbose_name="contenu")),
                ("adversarial_stage_start", models.DateField(verbose_name="début de la phase contradictoire")),
            ],
            options={
                "verbose_name": "calendrier",
            },
        ),
        migrations.CreateModel(
            name="EvaluationCampaign",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="nom de la campagne d'évaluation")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="date de création"),
                ),
                (
                    "percent_set_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="date de paramétrage de la sélection"),
                ),
                (
                    "evaluations_asked_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="date de notification du contrôle aux Siaes"
                    ),
                ),
                (
                    "ended_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="date de clôture de la campagne"),
                ),
                ("evaluated_period_start_at", models.DateField(verbose_name="date de début de la période contrôlée")),
                ("evaluated_period_end_at", models.DateField(verbose_name="date de fin de la période contrôlée")),
                (
                    "chosen_percent",
                    models.PositiveIntegerField(
                        default=30,
                        validators=[
                            django.core.validators.MinValueValidator(20),
                            django.core.validators.MaxValueValidator(40),
                        ],
                        verbose_name="pourcentage de sélection",
                    ),
                ),
                (
                    "institution",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluation_campaigns",
                        to="institutions.institution",
                        validators=[itou.siae_evaluations.models.validate_institution],
                        verbose_name="DDETS IAE responsable du contrôle",
                    ),
                ),
                (
                    "submission_freeze_notified_at",
                    models.DateTimeField(
                        editable=False,
                        help_text="Date de dernière notification des DDETS après blocage des soumissions SIAE",
                        null=True,
                        verbose_name="notification des DDETS après blocage des soumissions SIAE",
                    ),
                ),
                (
                    "calendar",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="siae_evaluations.calendar",
                        verbose_name="calendrier",
                    ),
                ),
            ],
            options={
                "verbose_name": "campagne",
                "ordering": ["-name", "institution__name"],
            },
        ),
        migrations.CreateModel(
            name="EvaluatedSiae",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "evaluation_campaign",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluated_siaes",
                        to="siae_evaluations.evaluationcampaign",
                        verbose_name="contrôle",
                    ),
                ),
                ("reviewed_at", models.DateTimeField(blank=True, null=True, verbose_name="contrôlée le")),
                (
                    "final_reviewed_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="contrôle définitif le"),
                ),
                (
                    "notification_reason",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("DELAY", "Non respect des délais"),
                            ("INVALID_PROOF", "Pièce justificative incorrecte"),
                            ("MISSING_PROOF", "Pièce justificative manquante"),
                            ("OTHER", "Autre"),
                        ],
                        max_length=255,
                        null=True,
                        verbose_name="raison principale",
                    ),
                ),
                ("notification_text", models.TextField(blank=True, null=True, verbose_name="commentaire")),
                ("notified_at", models.DateTimeField(blank=True, null=True, verbose_name="notifiée le")),
                ("reminder_sent_at", models.DateTimeField(blank=True, null=True, verbose_name="rappel envoyé le")),
                (
                    "submission_freezed_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="transmission bloquée pour la SIAE le"),
                ),
                (
                    "siae",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluated_siaes",
                        to="companies.company",
                        verbose_name="SIAE",
                    ),
                ),
            ],
            options={
                "verbose_name": "entreprise contrôlée",
                "verbose_name_plural": "entreprises contrôlées",
                "unique_together": {("evaluation_campaign", "siae")},
            },
        ),
        migrations.CreateModel(
            name="EvaluatedJobApplication",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "labor_inspector_explanation",
                    models.TextField(blank=True, verbose_name="commentaires de l'inspecteur du travail"),
                ),
                (
                    "evaluated_siae",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluated_job_applications",
                        to="siae_evaluations.evaluatedsiae",
                        verbose_name="SIAE évaluée",
                    ),
                ),
                (
                    "job_application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluated_job_applications",
                        to="job_applications.jobapplication",
                        verbose_name="candidature",
                    ),
                ),
            ],
            options={
                "verbose_name": "auto-prescription",
            },
        ),
        migrations.CreateModel(
            name="Sanctions",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "training_session",
                    models.TextField(
                        blank=True,
                        verbose_name="détails de la participation à une session de présentation de "
                        "l’auto-prescription",
                    ),
                ),
                (
                    "suspension_dates",
                    itou.utils.models.InclusiveDateRangeField(
                        blank=True, null=True, verbose_name="retrait de la capacité d’auto-prescription"
                    ),
                ),
                (
                    "subsidy_cut_percent",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(100),
                        ],
                        verbose_name="pourcentage de retrait de l’aide au poste",
                    ),
                ),
                (
                    "subsidy_cut_dates",
                    itou.utils.models.InclusiveDateRangeField(
                        blank=True, null=True, verbose_name="dates de retrait de l’aide au poste"
                    ),
                ),
                (
                    "deactivation_reason",
                    models.TextField(blank=True, verbose_name="explication du déconventionnement de la structure"),
                ),
                (
                    "no_sanction_reason",
                    models.TextField(blank=True, verbose_name="explication de l’absence de sanction"),
                ),
                (
                    "evaluated_siae",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="siae_evaluations.evaluatedsiae",
                        verbose_name="SIAE évaluée",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "sanctions",
            },
        ),
        migrations.CreateModel(
            name="EvaluatedAdministrativeCriteria",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uploaded_at", models.DateTimeField(blank=True, null=True, verbose_name="téléversé le")),
                (
                    "administrative_criteria",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluated_administrative_criteria",
                        to="eligibility.administrativecriteria",
                        verbose_name="critère administratif",
                    ),
                ),
                (
                    "evaluated_job_application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluated_administrative_criteria",
                        to="siae_evaluations.evaluatedjobapplication",
                        verbose_name="candidature évaluée",
                    ),
                ),
                ("submitted_at", models.DateTimeField(blank=True, null=True, verbose_name="transmis le")),
                (
                    "review_state",
                    models.CharField(
                        choices=[
                            ("PENDING", "En attente"),
                            ("ACCEPTED", "Validé"),
                            ("REFUSED", "Problème constaté"),
                            ("REFUSED_2", "Problème constaté (x2)"),
                        ],
                        default="PENDING",
                        max_length=10,
                        verbose_name="vérification",
                    ),
                ),
                (
                    "proof",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="files.file"
                    ),
                ),
            ],
            options={
                "verbose_name": "critère administratif",
                "verbose_name_plural": "critères administratifs",
                "ordering": ["evaluated_job_application", "administrative_criteria"],
                "unique_together": {("administrative_criteria", "evaluated_job_application")},
            },
        ),
        migrations.AddConstraint(
            model_name="sanctions",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("subsidy_cut_dates__isnull", True), ("subsidy_cut_percent__isnull", True)),
                    models.Q(("subsidy_cut_dates__isnull", False), ("subsidy_cut_percent__isnull", False)),
                    _connector="OR",
                ),
                name="subsidy_cut_consistency",
                violation_error_message="Le pourcentage et la date de début de retrait de l’aide au poste doivent "
                "être renseignés.",
            ),
        ),
        migrations.AddConstraint(
            model_name="evaluatedsiae",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("final_reviewed_at__isnull", True),
                    models.Q(("final_reviewed_at__gte", models.F("reviewed_at")), ("reviewed_at__isnull", False)),
                    _connector="OR",
                ),
                name="final_reviewed_at_only_after_reviewed_at",
                violation_error_message="Impossible d'avoir une date de contrôle définitif sans une date de premier "
                "contrôle antérieure",
            ),
        ),
    ]
