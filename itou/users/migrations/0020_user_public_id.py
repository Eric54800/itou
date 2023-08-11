# Generated by Django 4.2.4 on 2023-08-10 10:41

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0019_jobseekerprofile_pe_obfuscated_nir_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, verbose_name="identifiant public opaque, pour les API"),
        ),
    ]
