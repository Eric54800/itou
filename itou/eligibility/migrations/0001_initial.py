# Generated by Django 5.0.3 on 2024-03-23 08:25

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("companies", "0001_initial"),
        ("prescribers", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AdministrativeCriteria",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "level",
                    models.CharField(
                        choices=[("1", "Niveau 1"), ("2", "Niveau 2")],
                        default="1",
                        max_length=1,
                        verbose_name="niveau",
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="nom")),
                ("desc", models.CharField(blank=True, max_length=255, verbose_name="description")),
                ("written_proof", models.CharField(blank=True, max_length=255, verbose_name="justificatif")),
                (
                    "written_proof_url",
                    models.URLField(blank=True, verbose_name="lien d'aide à propos du justificatif"),
                ),
                ("ui_rank", models.PositiveSmallIntegerField(default=32767)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="date de création"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="créé par",
                    ),
                ),
                (
                    "written_proof_validity",
                    models.CharField(
                        blank=True, default="", max_length=255, verbose_name="durée de validité du justificatif"
                    ),
                ),
            ],
            options={
                "verbose_name": "critère administratif IAE",
                "verbose_name_plural": "critères administratifs IAE",
                "ordering": ["level", "ui_rank"],
            },
        ),
        migrations.CreateModel(
            name="EligibilityDiagnosis",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "author_kind",
                    models.CharField(
                        choices=[("prescriber", "Prescripteur habilité"), ("employer", "Employeur"), ("geiq", "GEIQ")],
                        default="prescriber",
                        max_length=10,
                        verbose_name="type de l'auteur",
                    ),
                ),
                (
                    "author_siae",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="companies.company",
                        verbose_name="SIAE de l'auteur",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, verbose_name="date de création"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, db_index=True, verbose_name="date de modification"),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="auteur"
                    ),
                ),
                (
                    "author_prescriber_organization",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="prescribers.prescriberorganization",
                        verbose_name="organisation du prescripteur de l'auteur",
                    ),
                ),
                (
                    "job_seeker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="eligibility_diagnoses",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="demandeur d'emploi",
                    ),
                ),
                ("expires_at", models.DateTimeField(db_index=True, verbose_name="date d'expiration")),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "diagnostic d'éligibilité IAE",
                "verbose_name_plural": "diagnostics d'éligibilité IAE",
            },
        ),
        migrations.CreateModel(
            name="SelectedAdministrativeCriteria",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="date de création"),
                ),
                (
                    "administrative_criteria",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="administrative_criteria_through",
                        to="eligibility.administrativecriteria",
                    ),
                ),
                (
                    "eligibility_diagnosis",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="selected_administrative_criteria",
                        to="eligibility.eligibilitydiagnosis",
                    ),
                ),
            ],
            options={
                "verbose_name": "critère administratif IAE sélectionné",
                "verbose_name_plural": "critères administratifs IAE sélectionnés",
                "unique_together": {("eligibility_diagnosis", "administrative_criteria")},
            },
        ),
        migrations.AddField(
            model_name="eligibilitydiagnosis",
            name="administrative_criteria",
            field=models.ManyToManyField(
                blank=True,
                through="eligibility.SelectedAdministrativeCriteria",
                to="eligibility.administrativecriteria",
                verbose_name="critères administratifs",
            ),
        ),
        migrations.CreateModel(
            name="GEIQAdministrativeCriteria",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="nom")),
                ("desc", models.CharField(blank=True, max_length=255, verbose_name="description")),
                ("written_proof", models.CharField(blank=True, max_length=255, verbose_name="justificatif")),
                (
                    "written_proof_url",
                    models.URLField(blank=True, verbose_name="lien d'aide à propos du justificatif"),
                ),
                (
                    "written_proof_validity",
                    models.CharField(
                        blank=True, default="", max_length=255, verbose_name="durée de validité du justificatif"
                    ),
                ),
                ("ui_rank", models.PositiveSmallIntegerField(default=32767)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="date de création"),
                ),
                (
                    "annex",
                    models.CharField(
                        choices=[
                            ("0", "Aucune annexe associée"),
                            ("1", "Annexe 1"),
                            ("2", "Annexe 2"),
                            ("1+2", "Annexes 1 et 2"),
                        ],
                        default="1",
                        max_length=3,
                        verbose_name="annexe",
                    ),
                ),
                (
                    "level",
                    models.CharField(
                        blank=True,
                        choices=[("1", "Niveau 1"), ("2", "Niveau 2")],
                        max_length=1,
                        null=True,
                        verbose_name="niveau",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="créé par",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="eligibility.geiqadministrativecriteria",
                        verbose_name="critère parent",
                    ),
                ),
                ("slug", models.SlugField(blank=True, max_length=100, null=True, verbose_name="référence courte")),
                ("api_code", models.CharField(verbose_name="code API")),
            ],
            options={
                "verbose_name": "critère administratif GEIQ",
                "verbose_name_plural": "critères administratifs GEIQ",
                "ordering": [models.OrderBy(models.F("level"), nulls_last=True), "ui_rank"],
            },
        ),
        migrations.CreateModel(
            name="GEIQEligibilityDiagnosis",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "author_kind",
                    models.CharField(
                        choices=[("prescriber", "Prescripteur habilité"), ("employer", "Employeur"), ("geiq", "GEIQ")],
                        default="prescriber",
                        max_length=10,
                        verbose_name="type de l'auteur",
                    ),
                ),
                (
                    "author_geiq",
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to={"kind": "GEIQ"},
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="geiq_eligibilitydiagnosis_set",
                        to="companies.company",
                        verbose_name="GEIQ de l'auteur",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, verbose_name="date de création"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, db_index=True, verbose_name="date de modification"),
                ),
                ("expires_at", models.DateTimeField(db_index=True, verbose_name="date d'expiration")),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="auteur"
                    ),
                ),
                (
                    "author_prescriber_organization",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="prescribers.prescriberorganization",
                        verbose_name="organisation du prescripteur de l'auteur",
                    ),
                ),
                (
                    "job_seeker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="geiq_eligibility_diagnoses",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="demandeur d'emploi",
                    ),
                ),
            ],
            options={
                "verbose_name": "diagnostic d'éligibilité GEIQ",
                "verbose_name_plural": "diagnostics d'éligibilité GEIQ",
            },
        ),
        migrations.CreateModel(
            name="GEIQSelectedAdministrativeCriteria",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="date de création"),
                ),
                (
                    "administrative_criteria",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="administrative_criteria_through",
                        to="eligibility.geiqadministrativecriteria",
                    ),
                ),
                (
                    "eligibility_diagnosis",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="selected_administrative_criteria",
                        to="eligibility.geiqeligibilitydiagnosis",
                    ),
                ),
            ],
            options={
                "verbose_name": "critère administratif GEIQ sélectionné",
                "verbose_name_plural": "critères administratifs GEIQ sélectionnés",
                "unique_together": {("eligibility_diagnosis", "administrative_criteria")},
            },
        ),
        migrations.AddField(
            model_name="geiqeligibilitydiagnosis",
            name="administrative_criteria",
            field=models.ManyToManyField(
                blank=True,
                through="eligibility.GEIQSelectedAdministrativeCriteria",
                to="eligibility.geiqadministrativecriteria",
                verbose_name="critères administratifs GEIQ",
            ),
        ),
        migrations.AddConstraint(
            model_name="geiqadministrativecriteria",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("annex", "1"), ("level__isnull", True)),
                    models.Q(("annex", "2"), ("level__isnull", False)),
                    models.Q(("annex", "0"), ("level__isnull", True)),
                    ("annex", "1+2"),
                    _connector="OR",
                ),
                name="ac_level_annex_coherence",
                violation_error_message="Incohérence entre l'annexe du critère administratif et son niveau",
            ),
        ),
        migrations.AddConstraint(
            model_name="geiqeligibilitydiagnosis",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("author_geiq__isnull", False),
                        ("author_kind", "geiq"),
                        ("author_prescriber_organization__isnull", True),
                    ),
                    models.Q(
                        ("author_geiq__isnull", True),
                        ("author_kind", "prescriber"),
                        ("author_prescriber_organization__isnull", False),
                    ),
                    _connector="OR",
                ),
                name="author_kind_coherence",
                violation_error_message="Le diagnostic d'éligibilité GEIQ ne peut avoir 2 structures pour auteur",
            ),
        ),
    ]
