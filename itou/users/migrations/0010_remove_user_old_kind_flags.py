# Generated by Django 4.1.5 on 2023-01-16 08:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_alter_user_kind"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="is_job_seeker",
        ),
        migrations.RemoveField(
            model_name="user",
            name="is_prescriber",
        ),
        migrations.RemoveField(
            model_name="user",
            name="is_siae_staff",
        ),
        migrations.RemoveField(
            model_name="user",
            name="is_labor_inspector",
        ),
    ]
