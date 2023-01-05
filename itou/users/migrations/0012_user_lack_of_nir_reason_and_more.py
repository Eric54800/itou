# Generated by Django 4.1.5 on 2023-01-05 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0011_user_staff_and_superusers"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="lack_of_nir_reason",
            field=models.CharField(
                blank=True,
                choices=[
                    ("TEMPORARY_NUMBER", "Numéro temporaire (NIA/NTT)"),
                    ("NO_NIR", "Pas de numéro de sécurité sociale"),
                    ("NIR_ASSOCIATED_TO_OTHER", "Le numéro de sécurité sociale est associé à quelqu'un d'autre"),
                ],
                help_text="Indiquez la raison de l'absence de NIR.",
                max_length=30,
                verbose_name="Pas de NIR ?",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                check=models.Q(("lack_of_nir_reason", ""), ("nir__isnull", True), _connector="OR"),
                name="user_lack_of_nir_reason_or_nir",
                violation_error_message=(
                    "Un utilisateur ayant un NIR ne peut avoir un motif justifiant l'absence de son NIR."
                ),
            ),
        ),
    ]
