# Generated by Django 4.0.2 on 2022-06-01 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="InclusionConnectState",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("csrf", models.CharField(max_length=12, unique=True)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
