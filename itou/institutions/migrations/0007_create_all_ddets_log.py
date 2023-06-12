# Generated by Django 4.1.8 on 2023-06-12 14:25

from django.db import migrations

from itou.institutions.enums import InstitutionKind
from itou.institutions.models import Institution, InstitutionMembership
from itou.users.models import User


PILOTAGE_INSTITUTION_SHARED_USER_ID = 322971


def create_all_ddets_log(apps, _schema_editor):
    pilotage_user = User.objects.filter(pk=PILOTAGE_INSTITUTION_SHARED_USER_ID).first()
    if pilotage_user is None:
        return
    if not pilotage_user.is_labor_inspector:
        return

    for ddets_iae in Institution.objects.filter(kind=InstitutionKind.DDETS_IAE):
        if Institution.objects.filter(kind=InstitutionKind.DDETS_LOG, department=ddets_iae.department).exists():
            continue
        ddets_log = Institution(
            kind=InstitutionKind.DDETS_LOG,
            department=ddets_iae.department,
            name=ddets_iae.name,
        )
        ddets_log.save()
        # `ddets_log.members.add(pilotage_user)` sets is_admin to False ¯\_(ツ)_/¯
        membership = InstitutionMembership(institution=ddets_log, user=pilotage_user, is_admin=True)
        membership.save()


def delete_all_ddets_log(apps, _schema_editor):
    Institution.objects.filter(kind=InstitutionKind.DDETS_LOG).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("institutions", "0006_update_institution_kind"),
    ]

    operations = [
        migrations.RunPython(create_all_ddets_log, delete_all_ddets_log, elidable=True),
    ]
