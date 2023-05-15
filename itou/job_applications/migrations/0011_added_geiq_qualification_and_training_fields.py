# Generated by Django 4.1.9 on 2023-05-25 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("job_applications", "0010_jobapplication_prehiring_guidance_days"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobapplication",
            name="planned_training_days",
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, verbose_name="Nombre de jours de formation prévus"
            ),
        ),
        migrations.AddField(
            model_name="jobapplication",
            name="qualification_level",
            field=models.CharField(
                blank=True,
                choices=[
                    ("LEVEL_3", "Niveau 3 (CAP, BEP)"),
                    ("LEVEL_4", "Niveau 4 (BP, Bac général, Techno ou Pro, BT)"),
                    ("LEVEL_5", "Niveau 5 ou + (Bac+2 ou +)"),
                    ("NOT_RELEVANT", "Non concerné"),
                ],
                max_length=40,
                verbose_name="Niveau de qualification",
            ),
        ),
        migrations.AddField(
            model_name="jobapplication",
            name="qualification_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("STATE_DIPLOMA", "Diplôme d'état ou titre homologué"),
                    ("CQP", "CQP"),
                    ("CCN", "Positionnement de CCN"),
                ],
                max_length=20,
                verbose_name="Type de qualification",
            ),
        ),
        migrations.AddConstraint(
            model_name="jobapplication",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("qualification_level", "NOT_RELEVANT"), ("qualification_type", "STATE_DIPLOMA"), _negated=True
                ),
                name="qualification_coherence",
                violation_error_message="Incohérence dans les champs concernant la qualification pour le contrat GEIQ",
            ),
        ),
    ]
