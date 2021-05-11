# Generated by Django 3.2 on 2021-04-28 14:29

from django.conf import settings
from django.db import migrations

from itou.prescribers.management.commands.merge_organizations import organization_delete, organization_merge_into


def cleanup_brsa_organizations(apps, schema_editor):
    # This calls could break in the future because the called function doesn't
    # use the existing SQL schema (as provided in argument) so we will have to
    # squash (or reset) migrations.
    merge_list = [
        # (from, to)
        (4187, 3945),
        (4353, 2105),
        (4325, 1705),
        (3855, 1705),
        (3442, 4544),
        (2167, None),
        (2489, None),
        (2895, None),
        (3724, None),
        (1105, 3036),
        (4575, 3632),
        (4208, 2954),
        (4567, 3176),
        (3160, 1618),
        (2475, 2841),
        (2922, 2723),  # 2723 À habiliter
        (2782, 2452),
        (4221, 2452),
        (3455, 1314),
        (3015, 2879),
        (2342, 3202),
        (2249, 3148),
        (3679, 3356),
        (3007, 1878),
        (2141, 2910),
        (3375, 2978),
        (1729, 2619),
        (3582, 3220),
        (3762, 3645),
        (2514, 3540),
        (4297, 2109),
        (2526, 2984),
        (2519, 3542),
        (2552, 3414),
        (2953, 3840),
        (3854, 3840),
        (3915, 3652),
        (4709, 3652),
        (3023, 3012),
        (3052, 2796),
        (3451, 3876),
        (4130, 2465),
        # Not validated by Zo
        (4606, 2784),
        (4672, 3663),
        (4781, 1113),
    ]
    for from_id, to_id in merge_list:
        if to_id:
            organization_merge_into(from_id, to_id)
        else:
            organization_delete(from_id)


def remove_dept_brsa(apps, schema_editor):
    PrescriberOrganization = apps.get_model("prescribers", "PrescriberOrganization")
    PrescriberOrganization.objects.filter(kind="DEPT_BRSA").update(kind="OTHER", is_brsa=True)


class Migration(migrations.Migration):

    dependencies = [
        ("prescribers", "0028_prescriberorganization_is_brsa"),
    ]

    # Data migration for PROD only
    operations = (
        [
            migrations.RunPython(cleanup_brsa_organizations),
            migrations.RunPython(remove_dept_brsa),
        ]
        if settings.ITOU_ENVIRONMENT == "PROD"
        else []
    )
