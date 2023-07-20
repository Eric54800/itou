# Generated by Django 4.1.8 on 2023-05-12 15:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("institutions", "0002_institution_geocoded_label_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="institution",
            name="kind",
            field=models.CharField(
                choices=[
                    ("DDETS", "Direction départementale de l'emploi, du travail et des solidarités"),
                    ("DREETS", "Direction régionale de l'économie, de l'emploi, du travail et des solidarités"),
                    ("DGEFP", "Délégation générale à l'emploi et à la formation professionnelle"),
                    ("DIHAL", "Délégation interministérielle à l'hébergement et à l'accès au logement"),
                    ("Réseau IAE", "Réseau IAE (Coorace, Emmaüs...)"),
                    ("Autre", "Autre"),
                ],
                default="Autre",
                max_length=20,
                verbose_name="type",
            ),
        ),
    ]
