# Generated by Django 4.1.5 on 2023-01-23 13:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        models.Q(("kind", "itou_staff"), _negated=True), ("is_staff", False), ("is_superuser", False)
                    ),
                    models.Q(("is_staff", True), ("kind", "itou_staff")),
                    _connector="OR",
                ),
                name="staff_and_superusers",
                violation_error_message="Seul un utilisateur ITOU_STAFF peut avoir is_staff ou is_superuser de vrai.",
            ),
        ),
    ]
