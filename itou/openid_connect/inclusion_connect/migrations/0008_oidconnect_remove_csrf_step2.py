# Generated by Django 4.1.9 on 2023-06-12 11:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inclusion_connect", "0007_oidconnect_remove_csrf_step1"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="inclusionconnectstate",
            name="csrf",
        ),
    ]
