# Generated by Django 4.0.1 on 2022-01-25 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("approvals", "0023_remove_approval_create_employee_record"),
    ]

    operations = [
        migrations.AlterField(
            model_name="suspension",
            name="reason",
            field=models.CharField(
                choices=[
                    ("CONTRACT_SUSPENDED", "Contrat de travail suspendu depuis plus de 15 jours"),
                    ("CONTRACT_BROKEN", "Contrat de travail rompu"),
                    ("FINISHED_CONTRACT", "Contrat de travail terminé"),
                    (
                        "APPROVAL_BETWEEN_CTA_MEMBERS",
                        "Situation faisant l'objet d'un accord entre les acteurs membres du CTA (Comité technique d'animation)",
                    ),
                    ("CONTRAT_PASSERELLE", "Bascule dans l'expérimentation contrat passerelle"),
                    ("SICKNESS", "Arrêt pour longue maladie"),
                    ("MATERNITY", "Congé de maternité"),
                    ("INCARCERATION", "Incarcération"),
                    (
                        "TRIAL_OUTSIDE_IAE",
                        "Période d'essai auprès d'un employeur ne relevant pas de l'insertion par l'activité économique",
                    ),
                    ("DETOXIFICATION", "Période de cure pour désintoxication"),
                    (
                        "FORCE_MAJEURE",
                        "Raison de force majeure conduisant le salarié à quitter son emploi ou toute autre situation faisant l'objet d'un accord entre les acteurs membres du CTA",
                    ),
                ],
                default="CONTRACT_SUSPENDED",
                max_length=30,
                verbose_name="Motif",
            ),
        ),
    ]
