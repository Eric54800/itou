# Generated by Django 2.2.9 on 2020-01-30 18:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("approvals", "0001_initial"), ("job_applications", "0016_auto_20200129_1445")]

    operations = [
        migrations.AddField(
            model_name="jobapplication",
            name="approval",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="approvals.Approval",
                verbose_name="PASS IAE",
            ),
        ),
        migrations.AddField(
            model_name="jobapplication",
            name="approval_number_sent_by_email",
            field=models.BooleanField(default=False, verbose_name="PASS IAE envoyé par email"),
        ),
        migrations.AddField(
            model_name="jobapplication",
            name="approval_delivery_mode",
            field=models.CharField(
                blank=True,
                choices=[("automatic", "Automatique"), ("manual", "Manuel")],
                max_length=30,
                verbose_name="Mode d'attribution du PASS IAE",
            ),
        ),
    ]
