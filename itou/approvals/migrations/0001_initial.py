# Generated by Django 4.1.4 on 2023-01-02 12:46

import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import itou.utils.models
import itou.utils.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("siaes", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Approval",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "number",
                    models.CharField(
                        help_text="12 caractères alphanumériques.",
                        max_length=12,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[0-9a-zA-Z]*$", "Seuls les caractères alphanumériques sont autorisés."
                            ),
                            django.core.validators.MinLengthValidator(12),
                        ],
                        verbose_name="numéro",
                    ),
                ),
                (
                    "start_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="date de début"
                    ),
                ),
                (
                    "end_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="date de fin"
                    ),
                ),
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
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="approvals",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="demandeur d'emploi",
                    ),
                ),
                (
                    "pe_notification_time",
                    models.DateTimeField(blank=True, null=True, verbose_name="date de notification à PE"),
                ),
                (
                    "pe_notification_endpoint",
                    models.CharField(
                        blank=True,
                        choices=[("rech_individu", "Recherche Individu"), ("maj_pass", "Mise A Jour Pass Iae")],
                        max_length=32,
                        null=True,
                        verbose_name="dernier endpoint de l'API PE contacté",
                    ),
                ),
                (
                    "pe_notification_status",
                    models.CharField(
                        choices=[
                            ("notification_pending", "Pending"),
                            ("notification_success", "Success"),
                            ("notification_error", "Error"),
                            ("notification_should_retry", "Should Retry"),
                        ],
                        default="notification_pending",
                        max_length=32,
                        verbose_name="état de la notification à PE",
                    ),
                ),
                (
                    "pe_notification_exit_code",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("S000", "Aucun individu trouvé"),
                            ("S001", "Individu trouvé"),
                            ("S002", "Plusieurs individu trouvés"),
                            ("R010", "NIR Certifié absent"),
                            ("R011", "NIR Certifié incorrect"),
                            ("R020", "Nom de naissance absente"),
                            ("R021", "Nom de naissance incorrect"),
                            ("R030", "Prénom absent"),
                            ("R031", "Prénom incorrect"),
                            ("R040", "Date de naissance absente"),
                            ("R041", "Date de naissance incorrecte"),
                            ("R042", "Date de naissance invalide"),
                            ("S000", "Suivi délégué installé"),
                            ("S001", "SD non installé : Identifiant national individu obligatoire"),
                            ("S002", "SD non installé : Code traitement obligatoire"),
                            ("S003", "SD non installé : Code traitement erroné"),
                            ("S004", "SD non installé : Erreur lors de la recherche de la TDV référente"),
                            ("S005", "SD non installé : Identifiant régional de l’individu obligatoire"),
                            ("S006", "SD non installé : Code Pôle Emploi de l’individu obligatoire"),
                            ("S007", "SD non installé : Individu inexistant en base"),
                            ("S008", "SD non installé : Individu radié"),
                            ("S009", "SD non installé : Inscription incomplète de l’individu "),
                            ("S010", "SD non installé : PEC de l’individu inexistante en base"),
                            ("S011", "SD non installé : Demande d’emploi de l’individu inexistante en base"),
                            ("S012", "SD non installé : Suivi principal de l’individu inexistant en base"),
                            ("S013", "SD non installé : Référent suivi principal non renseigné en base"),
                            ("S014", "SD non installé : Structure suivi principal non renseignée en base"),
                            ("S015", "SD non installé : Suivi délégué déjà en cours"),
                            ("S016", "SD non installé : Problème lors de la recherche du dernier suivi délégué"),
                            ("S017", "SD non installé : Type de suivi de l’individu non EDS»"),
                            ("S018", "SD non installé : Type de SIAE obligatoire"),
                            ("S019", "SD non installé : Type de SIAE erroné"),
                            ("S020", "SD non installé : Statut de la réponse obligatoire"),
                            ("S021", "SD non installé : Statut de la réponse erroné"),
                            ("S022", "SD non installé : Refus du PASS IAE"),
                            ("S023", "SD non installé : Date de début du PASS IAE obligatoire"),
                            ("S024", "SD non installé : Date de début du PASS IAE dans le futur"),
                            ("S025", "SD non installé : Date de fin du PASS IAE obligatoire"),
                            ("S026", "SD non installé : Date fin PASS IAE non strictement sup à date début"),
                            ("S027", "SD non installé : Numéro du PASS IAE obligatoire"),
                            ("S028", "SD non installé : Origine de la candidature obligatoire"),
                            ("S029", "SD non installé : Origine de la candidature erronée"),
                            ("S031", "SD non installé : Numéro SIRET SIAE obligatoire"),
                            ("S032", "SD non installé : Organisme générique inexistant dans réf partenaire"),
                            ("S033", "SD non installé : Conseiller prescripteur inexistant en base"),
                            ("S034", "SD non installé : Structure prescripteur inexistante en base"),
                            ("S035", "SD non installé : Type de structure du prescripteur erroné"),
                            ("S036", "SD non installé : Pas de lien entre structure prescripteur et partenaire"),
                            ("S037", "SD non installé : Organisme générique inexistant en base"),
                            ("S038", "SD non installé : Correspondant du partenaire inexistant en base"),
                            ("S039", "SD non installé : Structure correspondant inexistante en base"),
                            ("S040", "SD non installé : Structure correspondant inexistante dans réf des struct"),
                            ("S041", "SD non installé : Structure de suivi non autorisée"),
                            ("S042", "SD non installé : Adresse du correspondant inexistante en base"),
                            ("S043", "SD non installé : Commune du correspondant inexistante en base"),
                            ("E_ERR_D98_D_PR_PROBLEME_TECHNIQUE", "Problème technique inconnu"),
                            ("E_ERR_EX042_PROBLEME_DECHIFFREMEMENT", "Erreur lors du déchiffrement du NIR chiffré"),
                        ],
                        max_length=64,
                        null=True,
                        verbose_name="dernier code de sortie constaté",
                    ),
                ),
            ],
            options={
                "verbose_name": "PASS IAE",
                "verbose_name_plural": "PASS IAE",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PoleEmploiApproval",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "start_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="date de début"
                    ),
                ),
                (
                    "end_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="date de fin"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="date de création"),
                ),
                ("pe_structure_code", models.CharField(max_length=5, verbose_name="code structure Pôle emploi")),
                ("number", models.CharField(max_length=12, unique=True, verbose_name="numéro")),
                ("pole_emploi_id", models.CharField(max_length=8, verbose_name="identifiant Pôle emploi")),
                ("first_name", models.CharField(max_length=150, verbose_name="prénom")),
                ("last_name", models.CharField(max_length=150, verbose_name="nom")),
                ("birth_name", models.CharField(max_length=150, verbose_name="nom de naissance")),
                (
                    "birthdate",
                    models.DateField(default=django.utils.timezone.localdate, verbose_name="date de naissance"),
                ),
                ("nir", models.CharField(blank=True, max_length=15, null=True, verbose_name="NIR")),
                ("ntt_nia", models.CharField(blank=True, max_length=40, null=True, verbose_name="NTT ou NIA")),
                (
                    "pe_notification_endpoint",
                    models.CharField(
                        blank=True,
                        choices=[("rech_individu", "Recherche Individu"), ("maj_pass", "Mise A Jour Pass Iae")],
                        max_length=32,
                        null=True,
                        verbose_name="dernier endpoint de l'API PE contacté",
                    ),
                ),
                (
                    "pe_notification_status",
                    models.CharField(
                        choices=[
                            ("notification_pending", "Pending"),
                            ("notification_success", "Success"),
                            ("notification_error", "Error"),
                            ("notification_should_retry", "Should Retry"),
                        ],
                        default="notification_pending",
                        max_length=32,
                        verbose_name="état de la notification à PE",
                    ),
                ),
                (
                    "pe_notification_exit_code",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("S000", "Aucun individu trouvé"),
                            ("S001", "Individu trouvé"),
                            ("S002", "Plusieurs individu trouvés"),
                            ("R010", "NIR Certifié absent"),
                            ("R011", "NIR Certifié incorrect"),
                            ("R020", "Nom de naissance absente"),
                            ("R021", "Nom de naissance incorrect"),
                            ("R030", "Prénom absent"),
                            ("R031", "Prénom incorrect"),
                            ("R040", "Date de naissance absente"),
                            ("R041", "Date de naissance incorrecte"),
                            ("R042", "Date de naissance invalide"),
                            ("S000", "Suivi délégué installé"),
                            ("S001", "SD non installé : Identifiant national individu obligatoire"),
                            ("S002", "SD non installé : Code traitement obligatoire"),
                            ("S003", "SD non installé : Code traitement erroné"),
                            ("S004", "SD non installé : Erreur lors de la recherche de la TDV référente"),
                            ("S005", "SD non installé : Identifiant régional de l’individu obligatoire"),
                            ("S006", "SD non installé : Code Pôle Emploi de l’individu obligatoire"),
                            ("S007", "SD non installé : Individu inexistant en base"),
                            ("S008", "SD non installé : Individu radié"),
                            ("S009", "SD non installé : Inscription incomplète de l’individu "),
                            ("S010", "SD non installé : PEC de l’individu inexistante en base"),
                            ("S011", "SD non installé : Demande d’emploi de l’individu inexistante en base"),
                            ("S012", "SD non installé : Suivi principal de l’individu inexistant en base"),
                            ("S013", "SD non installé : Référent suivi principal non renseigné en base"),
                            ("S014", "SD non installé : Structure suivi principal non renseignée en base"),
                            ("S015", "SD non installé : Suivi délégué déjà en cours"),
                            ("S016", "SD non installé : Problème lors de la recherche du dernier suivi délégué"),
                            ("S017", "SD non installé : Type de suivi de l’individu non EDS»"),
                            ("S018", "SD non installé : Type de SIAE obligatoire"),
                            ("S019", "SD non installé : Type de SIAE erroné"),
                            ("S020", "SD non installé : Statut de la réponse obligatoire"),
                            ("S021", "SD non installé : Statut de la réponse erroné"),
                            ("S022", "SD non installé : Refus du PASS IAE"),
                            ("S023", "SD non installé : Date de début du PASS IAE obligatoire"),
                            ("S024", "SD non installé : Date de début du PASS IAE dans le futur"),
                            ("S025", "SD non installé : Date de fin du PASS IAE obligatoire"),
                            ("S026", "SD non installé : Date fin PASS IAE non strictement sup à date début"),
                            ("S027", "SD non installé : Numéro du PASS IAE obligatoire"),
                            ("S028", "SD non installé : Origine de la candidature obligatoire"),
                            ("S029", "SD non installé : Origine de la candidature erronée"),
                            ("S031", "SD non installé : Numéro SIRET SIAE obligatoire"),
                            ("S032", "SD non installé : Organisme générique inexistant dans réf partenaire"),
                            ("S033", "SD non installé : Conseiller prescripteur inexistant en base"),
                            ("S034", "SD non installé : Structure prescripteur inexistante en base"),
                            ("S035", "SD non installé : Type de structure du prescripteur erroné"),
                            ("S036", "SD non installé : Pas de lien entre structure prescripteur et partenaire"),
                            ("S037", "SD non installé : Organisme générique inexistant en base"),
                            ("S038", "SD non installé : Correspondant du partenaire inexistant en base"),
                            ("S039", "SD non installé : Structure correspondant inexistante en base"),
                            ("S040", "SD non installé : Structure correspondant inexistante dans réf des struct"),
                            ("S041", "SD non installé : Structure de suivi non autorisée"),
                            ("S042", "SD non installé : Adresse du correspondant inexistante en base"),
                            ("S043", "SD non installé : Commune du correspondant inexistante en base"),
                            ("E_ERR_D98_D_PR_PROBLEME_TECHNIQUE", "Problème technique inconnu"),
                            ("E_ERR_EX042_PROBLEME_DECHIFFREMEMENT", "Erreur lors du déchiffrement du NIR chiffré"),
                        ],
                        max_length=64,
                        null=True,
                        verbose_name="dernier code de sortie constaté",
                    ),
                ),
                (
                    "pe_notification_time",
                    models.DateTimeField(blank=True, null=True, verbose_name="date de notification à PE"),
                ),
                (
                    "siae_kind",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("EI", "Entreprise d'insertion"),
                            ("AI", "Association intermédiaire"),
                            ("ACI", "Atelier chantier d'insertion"),
                            ("ETTI", "Entreprise de travail temporaire d'insertion"),
                            ("EITI", "Entreprise d'insertion par le travail indépendant"),
                            ("GEIQ", "Groupement d'employeurs pour l'insertion et la qualification"),
                            ("EA", "Entreprise adaptée"),
                            ("EATT", "Entreprise adaptée de travail temporaire"),
                            ("OPCS", "Organisation porteuse de la clause sociale"),
                        ],
                        max_length=6,
                        null=True,
                        verbose_name="type de la SIAE",
                    ),
                ),
                (
                    "siae_siret",
                    models.CharField(
                        blank=True,
                        max_length=14,
                        null=True,
                        validators=[itou.utils.validators.validate_siret],
                        verbose_name="siret de la SIAE",
                    ),
                ),
            ],
            options={
                "verbose_name": "agrément Pôle emploi",
                "verbose_name_plural": "agréments Pôle emploi",
                "ordering": ["-start_at"],
            },
        ),
        migrations.AddIndex(
            model_name="poleemploiapproval",
            index=models.Index(fields=["pole_emploi_id", "birthdate"], name="pe_id_and_birthdate_idx"),
        ),
        migrations.CreateModel(
            name="Suspension",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "start_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="date de début"
                    ),
                ),
                (
                    "end_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="date de fin"
                    ),
                ),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("CONTRACT_SUSPENDED", "Contrat de travail suspendu depuis plus de 15 jours"),
                            ("CONTRACT_BROKEN", "Contrat de travail rompu"),
                            ("FINISHED_CONTRACT", "Contrat de travail terminé"),
                            (
                                "APPROVAL_BETWEEN_CTA_MEMBERS",
                                "Situation faisant l'objet d'un accord entre les acteurs membres du CTA (Comité "
                                "technique d'animation)",
                            ),
                            ("CONTRAT_PASSERELLE", "Bascule dans l'expérimentation contrat passerelle"),
                            ("SICKNESS", "Arrêt pour longue maladie"),
                            ("MATERNITY", "Congé de maternité"),
                            ("INCARCERATION", "Incarcération"),
                            (
                                "TRIAL_OUTSIDE_IAE",
                                "Période d'essai auprès d'un employeur ne relevant pas de l'insertion par l'activité "
                                "économique",
                            ),
                            ("DETOXIFICATION", "Période de cure pour désintoxication"),
                            (
                                "FORCE_MAJEURE",
                                "Raison de force majeure conduisant le salarié à quitter son emploi ou toute autre "
                                "situation faisant l'objet d'un accord entre les acteurs membres du CTA",
                            ),
                        ],
                        default="CONTRACT_SUSPENDED",
                        max_length=30,
                        verbose_name="motif",
                    ),
                ),
                ("reason_explanation", models.TextField(blank=True, verbose_name="explications supplémentaires")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="date de création"),
                ),
                ("updated_at", models.DateTimeField(blank=True, null=True, verbose_name="date de modification")),
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
                        related_name="approvals_suspended_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="créé par",
                    ),
                ),
                (
                    "siae",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approvals_suspended",
                        to="siaes.siae",
                        verbose_name="SIAE",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="mis à jour par",
                    ),
                ),
            ],
            options={
                "verbose_name": "suspension",
                "ordering": ["-start_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="suspension",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=(
                    (
                        itou.utils.models.DateRange(
                            "start_at",
                            "end_at",
                            django.contrib.postgres.fields.ranges.RangeBoundary(
                                inclusive_lower=True, inclusive_upper=True
                            ),
                        ),
                        "&&",
                    ),
                    ("approval", "="),
                ),
                name="exclude_overlapping_suspensions",
                violation_error_message="La période chevauche une suspension existante pour ce PASS IAE.",
            ),
        ),
        migrations.CreateModel(
            name="Prolongation",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "start_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="date de début"
                    ),
                ),
                (
                    "end_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="date de fin"
                    ),
                ),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("SENIOR_CDI", "CDI conclu avec une personne de plus de 57\u202fans"),
                            ("COMPLETE_TRAINING", "Fin d'une formation"),
                            ("RQTH", "RQTH"),
                            ("SENIOR", "50\u202fans et plus"),
                            (
                                "PARTICULAR_DIFFICULTIES",
                                "Difficultés particulières qui font obstacle à l'insertion durable dans l’emploi",
                            ),
                            ("HEALTH_CONTEXT", "Contexte sanitaire"),
                        ],
                        default="COMPLETE_TRAINING",
                        max_length=30,
                        verbose_name="motif",
                    ),
                ),
                ("reason_explanation", models.TextField(blank=True, verbose_name="explications supplémentaires")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="date de création"),
                ),
                ("updated_at", models.DateTimeField(blank=True, null=True, verbose_name="date de modification")),
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
                        verbose_name="créé par",
                    ),
                ),
                (
                    "declared_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approvals_prolongation_declared_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="déclarée par",
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
                        verbose_name="mis à jour par",
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
                        verbose_name="prescripteur habilité qui a autorisé cette prolongation",
                    ),
                ),
            ],
            options={
                "verbose_name": "prolongation",
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
                violation_error_message="La période chevauche une prolongation existante pour ce PASS IAE.",
            ),
        ),
        migrations.CreateModel(
            name="OriginalPoleEmploiApproval",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "start_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="date de début"
                    ),
                ),
                (
                    "end_at",
                    models.DateField(
                        db_index=True, default=django.utils.timezone.localdate, verbose_name="date de fin"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="date de création"),
                ),
                ("pe_structure_code", models.CharField(max_length=5, verbose_name="code structure Pôle emploi")),
                ("number", models.CharField(max_length=15, unique=True, verbose_name="numéro")),
                ("pole_emploi_id", models.CharField(max_length=8, verbose_name="identifiant Pôle emploi")),
                ("first_name", models.CharField(max_length=150, verbose_name="prénom")),
                ("last_name", models.CharField(max_length=150, verbose_name="nom")),
                ("birth_name", models.CharField(max_length=150, verbose_name="nom de naissance")),
                (
                    "birthdate",
                    models.DateField(default=django.utils.timezone.localdate, verbose_name="date de naissance"),
                ),
                ("nir", models.CharField(blank=True, max_length=15, null=True, verbose_name="NIR")),
                ("ntt_nia", models.CharField(blank=True, max_length=40, null=True, verbose_name="NTT ou NIA")),
                ("merged", models.BooleanField()),
            ],
            options={
                "db_table": "merged_approvals_poleemploiapproval",
                "ordering": ["-start_at"],
                "verbose_name": "agrément Pôle emploi original",
                "verbose_name_plural": "agréments Pôle emploi originaux",
            },
        ),
        migrations.AddIndex(
            model_name="originalpoleemploiapproval",
            index=models.Index(fields=["pole_emploi_id", "birthdate"], name="merged_pe_id_and_birthdate_idx"),
        ),
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION update_approval_end_at()
                    RETURNS TRIGGER
                    LANGUAGE plpgsql
                    AS $$
                    BEGIN
                        --
                        -- When a suspension is inserted/updated/deleted, the end date
                        -- of its approval is automatically pushed back or forth.
                        --
                        -- See:
                        -- https://www.postgresql.org/docs/12/triggers.html
                        -- https://www.postgresql.org/docs/12/plpgsql-trigger.html#PLPGSQL-TRIGGER-AUDIT-EXAMPLE
                        --
                        IF (TG_OP = 'DELETE') THEN
                            -- At delete time, the approval's end date is pushed back.
                            UPDATE approvals_approval
                            SET end_at = end_at - (OLD.end_at - OLD.start_at)
                            WHERE id = OLD.approval_id;
                        ELSIF (TG_OP = 'INSERT') THEN
                            -- At insert time, the approval's end date is pushed forward.
                            UPDATE approvals_approval
                            SET end_at = end_at + (NEW.end_at - NEW.start_at)
                            WHERE id = NEW.approval_id;
                        ELSIF (TG_OP = 'UPDATE') THEN
                            -- At update time, the approval's end date is first reset before
                            -- being pushed forward, e.g.:
                            --     * step 1 "create new 90 days suspension":
                            --         * extend approval: approval.end_date + 90 days
                            --     * step 2 "edit 60 days instead of 90 days":
                            --         * reset approval: approval.end_date - 90 days
                            --         * extend approval: approval.end_date + 60 days
                            UPDATE approvals_approval
                            SET end_at = end_at - (OLD.end_at - OLD.start_at) + (NEW.end_at - NEW.start_at)
                            WHERE id = NEW.approval_id;
                        END IF;
                        RETURN NULL;
                    END;
                $$;

                CREATE TRIGGER trigger_update_approval_end_at
                AFTER INSERT OR UPDATE OR DELETE ON approvals_suspension
                FOR EACH ROW
                EXECUTE FUNCTION update_approval_end_at();
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS trigger_update_approval_end_at ON approvals_suspension;
                DROP FUNCTION IF EXISTS update_approval_end_at();
            """,
        ),
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION update_approval_end_at_for_prolongation()
                    RETURNS TRIGGER
                    LANGUAGE plpgsql
                    AS $$
                    BEGIN
                        --
                        -- When a prolongation is inserted/updated/deleted, the end date
                        -- of its approval is automatically pushed back or forth.
                        --
                        -- See:
                        -- https://www.postgresql.org/docs/12/triggers.html
                        -- https://www.postgresql.org/docs/12/plpgsql-trigger.html#PLPGSQL-TRIGGER-AUDIT-EXAMPLE
                        --
                        IF (TG_OP = 'DELETE') THEN
                            -- At delete time, the approval's end date is pushed back if the prolongation
                            -- was validated.
                            UPDATE approvals_approval
                            SET end_at = end_at - (OLD.end_at - OLD.start_at)
                            WHERE id = OLD.approval_id;
                        ELSIF (TG_OP = 'INSERT') THEN
                            -- At insert time, the approval's end date is pushed forward if the prolongation
                            -- is validated.
                            UPDATE approvals_approval
                            SET end_at = end_at + (NEW.end_at - NEW.start_at)
                            WHERE id = NEW.approval_id;
                        ELSIF (TG_OP = 'UPDATE') THEN
                            -- At update time, the approval's end date is first reset before
                            -- being pushed forward.
                            UPDATE approvals_approval
                            SET end_at = end_at - (OLD.end_at - OLD.start_at) + (NEW.end_at - NEW.start_at)
                            WHERE id = NEW.approval_id;
                        END IF;
                        RETURN NULL;
                    END;
                $$;

                CREATE TRIGGER trigger_update_approval_end_at_for_prolongation
                AFTER INSERT OR UPDATE OR DELETE ON approvals_prolongation
                FOR EACH ROW
                EXECUTE FUNCTION update_approval_end_at_for_prolongation();
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS trigger_update_approval_end_at_for_prolongation ON approvals_prolongation;
                DROP FUNCTION IF EXISTS update_approval_end_at_for_prolongation();
            """,
        ),
    ]
