# Generated by Django 5.0.7 on 2024-08-06 09:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("approvals", "0003_alter_approval_updated_at"),
        ("companies", "0005_company_rdv_insertion_id"),
        ("eligibility", "0004_geiqadministrativecriteria_certifiable"),
        ("prescribers", "0004_poleemploi_to_francetravail"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="approval",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to=settings.AUTH_USER_MODEL,
                verbose_name="créé par",
            ),
        ),
        migrations.AlterField(
            model_name="approval",
            name="eligibility_diagnosis",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to="eligibility.eligibilitydiagnosis",
                verbose_name="diagnostic d'éligibilité",
            ),
        ),
        migrations.AlterField(
            model_name="approval",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="approvals",
                to=settings.AUTH_USER_MODEL,
                verbose_name="demandeur d'emploi",
            ),
        ),
        migrations.AlterField(
            model_name="prolongation",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)ss_created",
                to=settings.AUTH_USER_MODEL,
                verbose_name="créé par",
            ),
        ),
        migrations.AlterField(
            model_name="prolongation",
            name="declared_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)ss_declared",
                to=settings.AUTH_USER_MODEL,
                verbose_name="déclarée par",
            ),
        ),
        migrations.AlterField(
            model_name="prolongation",
            name="declared_by_siae",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to="companies.company",
                verbose_name="SIAE du déclarant",
            ),
        ),
        migrations.AlterField(
            model_name="prolongation",
            name="prescriber_organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to="prescribers.prescriberorganization",
                verbose_name="organisation du prescripteur habilité",
            ),
        ),
        migrations.AlterField(
            model_name="prolongation",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)ss_updated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="modifié par",
            ),
        ),
        migrations.AlterField(
            model_name="prolongation",
            name="validated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)ss_validated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="prescripteur habilité qui a autorisé cette prolongation",
            ),
        ),
        migrations.AlterField(
            model_name="prolongationrequest",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)ss_created",
                to=settings.AUTH_USER_MODEL,
                verbose_name="créé par",
            ),
        ),
        migrations.AlterField(
            model_name="prolongationrequest",
            name="declared_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)ss_declared",
                to=settings.AUTH_USER_MODEL,
                verbose_name="déclarée par",
            ),
        ),
        migrations.AlterField(
            model_name="prolongationrequest",
            name="declared_by_siae",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to="companies.company",
                verbose_name="SIAE du déclarant",
            ),
        ),
        migrations.AlterField(
            model_name="prolongationrequest",
            name="prescriber_organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to="prescribers.prescriberorganization",
                verbose_name="organisation du prescripteur habilité",
            ),
        ),
        migrations.AlterField(
            model_name="prolongationrequest",
            name="processed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)s_processed",
                to=settings.AUTH_USER_MODEL,
                verbose_name="traité par",
            ),
        ),
        migrations.AlterField(
            model_name="prolongationrequest",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)ss_updated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="modifié par",
            ),
        ),
        migrations.AlterField(
            model_name="prolongationrequest",
            name="validated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)ss_validated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="prescripteur habilité qui a autorisé cette prolongation",
            ),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="approvals_suspended_set",
                to=settings.AUTH_USER_MODEL,
                verbose_name="créé par",
            ),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="siae",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="approvals_suspended",
                to="companies.company",
                verbose_name="SIAE",
            ),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to=settings.AUTH_USER_MODEL,
                verbose_name="mis à jour par",
            ),
        ),
    ]
