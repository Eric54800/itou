from datetime import datetime

import httpx
import pytest
import respx
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError
from django.urls import reverse
from django.utils.timezone import get_current_timezone
from pytest_django.asserts import assertContains, assertMessages, assertNotContains, assertRedirects

from itou.job_applications import models as job_applications_models
from itou.prescribers.enums import PrescriberAuthorizationStatus, PrescriberOrganizationKind
from itou.prescribers.management.commands.merge_organizations import organization_merge_into
from itou.prescribers.models import PrescriberOrganization
from itou.utils.mocks.api_entreprise import ETABLISSEMENT_API_RESULT_MOCK, INSEE_API_RESULT_MOCK
from tests.common_apps.organizations.tests import assert_set_admin_role__creation, assert_set_admin_role__removal
from tests.eligibility.factories import GEIQEligibilityDiagnosisFactory
from tests.job_applications import factories as job_applications_factories
from tests.prescribers.factories import (
    PrescriberMembershipFactory,
    PrescriberOrganizationFactory,
    PrescriberOrganizationWith2MembershipFactory,
    PrescriberOrganizationWithMembershipFactory,
)
from tests.users.factories import EmployerFactory, ItouStaffFactory, PrescriberFactory


class TestPrescriberOrganizationManager:
    def test_get_accredited_orgs_for(self):
        departmental_council_org = PrescriberOrganizationFactory(authorized=True, kind=PrescriberOrganizationKind.DEPT)

        # An org accredited by a departmental council:
        # - is in the same department
        # - is accredited BRSA
        accredited_org = PrescriberOrganizationFactory(
            authorized=True,
            department=departmental_council_org.department,
            kind=PrescriberOrganizationKind.ODC,
            is_brsa=True,
        )

        other_org = PrescriberOrganizationFactory(
            authorized=True,
            department=departmental_council_org.department,
            kind=PrescriberOrganizationKind.CAP_EMPLOI,
        )

        # `expected_num` orgs should be accredited by the departmental council.
        accredited_orgs = PrescriberOrganization.objects.get_accredited_orgs_for(departmental_council_org)
        assert accredited_org == accredited_orgs.first()

        # No orgs should be accredited by the other org.
        accredited_orgs = PrescriberOrganization.objects.get_accredited_orgs_for(other_org)
        assert accredited_orgs.count() == 0

    def test_create_organization(self, django_capture_on_commit_callbacks, mailoutbox):
        """
        Test `create_organization`.
        """
        with django_capture_on_commit_callbacks(execute=True):
            PrescriberOrganization.objects.create_organization(
                {
                    "siret": "11122233300000",
                    "name": "Ma petite entreprise",
                    "authorization_status": PrescriberAuthorizationStatus.NOT_REQUIRED,
                },
            )
        assert 1 == PrescriberOrganization.objects.count()
        assert len(mailoutbox) == 0

        with django_capture_on_commit_callbacks(execute=True):
            org = PrescriberOrganization.objects.create_organization(
                {
                    "siret": "11122233300001",
                    "name": "Ma seconde entreprise",
                    "authorization_status": PrescriberAuthorizationStatus.NOT_SET,
                },
            )
        assert 2 == PrescriberOrganization.objects.count()
        assert len(mailoutbox) == 1
        assert str(org.pk) in mailoutbox[0].body


class TestPrescriberOrganizationModel:
    def test_accept_survey_url(self):
        org = PrescriberOrganizationFactory(kind=PrescriberOrganizationKind.PE, department="57")
        url = org.accept_survey_url
        assert url.startswith(f"{settings.TALLY_URL}/r/")
        assert f"idorganisation={org.pk}" in url
        assert "region=Grand+Est" in url
        assert "departement=57" in url

        # Ensure that the URL does not break when there is no department.
        org = PrescriberOrganizationFactory(kind=PrescriberOrganizationKind.CAP_EMPLOI, department="")
        url = org.accept_survey_url
        assert url.startswith(f"{settings.TALLY_URL}/r/")
        assert f"idorganisation={org.pk}" in url
        assert "region=" in url
        assert "departement=" in url

    def test_clean_siret(self):
        """
        Test that a SIRET number is required only for non-PE organizations.
        """
        org = PrescriberOrganizationFactory.build(siret="", kind=PrescriberOrganizationKind.PE)
        org.clean_siret()
        with pytest.raises(ValidationError):
            org = PrescriberOrganizationFactory.build(siret="", kind=PrescriberOrganizationKind.CAP_EMPLOI)
            org.clean_siret()

    def test_clean_code_safir_pole_emploi(self):
        """
        Test that a code SAFIR can only be set for PE agencies.
        """
        org = PrescriberOrganizationFactory.build(code_safir_pole_emploi="12345", kind=PrescriberOrganizationKind.PE)
        org.clean_code_safir_pole_emploi()
        with pytest.raises(ValidationError):
            org = PrescriberOrganizationFactory.build(
                code_safir_pole_emploi="12345", kind=PrescriberOrganizationKind.CAP_EMPLOI
            )
            org.clean_code_safir_pole_emploi()

    def test_has_pending_authorization_proof(self):
        org = PrescriberOrganizationFactory(
            kind=PrescriberOrganizationKind.OTHER,
            authorization_status=PrescriberAuthorizationStatus.NOT_SET,
        )
        assert org.has_pending_authorization()
        assert org.has_pending_authorization_proof()

        org = PrescriberOrganizationFactory(
            kind=PrescriberOrganizationKind.CAP_EMPLOI,
            authorization_status=PrescriberAuthorizationStatus.NOT_SET,
        )
        assert org.has_pending_authorization()
        assert not org.has_pending_authorization_proof()

    def test_active_admin_members(self):
        """
        Test that if a user is admin of org_1 and regular user
        of org2 he is not considered as admin of org_2.
        """
        org_1 = PrescriberOrganizationWithMembershipFactory()
        org_1_admin_user = org_1.members.first()
        org_2 = PrescriberOrganizationWithMembershipFactory()
        org_2.members.add(org_1_admin_user)

        assert org_1_admin_user in org_1.active_admin_members
        assert org_1_admin_user not in org_2.active_admin_members

    def test_active_members(self):
        org = PrescriberOrganizationWith2MembershipFactory(membership2__is_active=False)
        active_user_with_active_membership = org.members.first()
        active_user_with_inactive_membership = org.members.last()
        inactive_user_with_active_membership = PrescriberMembershipFactory(organization=org, user__is_active=False)

        assert active_user_with_active_membership in org.active_members
        assert active_user_with_inactive_membership not in org.active_members
        assert inactive_user_with_active_membership not in org.active_members

        # Deactivate a membership
        active_user_with_active_membership.is_active = False
        active_user_with_active_membership.save()

        assert active_user_with_active_membership not in org.active_members

    def test_add_or_activate_member(self):
        org = PrescriberOrganizationFactory()
        assert 0 == org.members.count()
        admin_user = PrescriberFactory()
        org.add_or_activate_member(admin_user)
        assert 1 == org.memberships.count()
        assert org.memberships.get(user=admin_user).is_admin

        other_user = PrescriberFactory()
        org.add_or_activate_member(other_user)
        assert 2 == org.memberships.count()
        assert not org.memberships.get(user=other_user).is_admin

        org.memberships.filter(user=other_user).update(is_active=False)
        org.add_or_activate_member(other_user)
        assert org.memberships.get(user=other_user).is_active

        non_prescriber = EmployerFactory()
        with pytest.raises(ValidationError):
            org.add_or_activate_member(non_prescriber)

    def test_merge_two_organizations(self):
        job_application_1 = job_applications_factories.JobApplicationSentByPrescriberOrganizationFactory(
            eligibility_diagnosis=None
        )
        organization_1 = job_application_1.sender_prescriber_organization

        job_application_2 = job_applications_factories.JobApplicationSentByPrescriberOrganizationFactory(
            eligibility_diagnosis=None
        )
        organization_2 = job_application_2.sender_prescriber_organization

        geiq_diagnosis = GEIQEligibilityDiagnosisFactory(
            from_prescriber=True, author_prescriber_organization=organization_1
        )

        count_job_applications = job_applications_models.JobApplication.objects.count()
        assert PrescriberOrganization.objects.count() == 2
        assert count_job_applications == 2
        organization_merge_into(organization_1.id, organization_2.id, wet_run=True)
        assert count_job_applications == job_applications_models.JobApplication.objects.count()
        assert PrescriberOrganization.objects.count() == 1
        geiq_diagnosis.refresh_from_db()
        assert geiq_diagnosis.author_prescriber_organization_id == organization_2.pk

    @respx.mock
    def test_update_prescriber_with_api_entreprise(self, settings):
        settings.API_INSEE_BASE_URL = "https://insee.fake"
        settings.API_INSEE_SIRENE_BASE_URL = "https://entreprise.fake"
        settings.API_INSEE_CONSUMER_KEY = "foo"
        settings.API_INSEE_CONSUMER_SECRET = "bar"

        siret = ETABLISSEMENT_API_RESULT_MOCK["etablissement"]["siret"]
        respx.post(f"{settings.API_INSEE_BASE_URL}/token").mock(
            return_value=httpx.Response(200, json=INSEE_API_RESULT_MOCK)
        )
        respx.get(f"{settings.API_INSEE_SIRENE_BASE_URL}/siret/{siret}").mock(
            return_value=httpx.Response(200, json=ETABLISSEMENT_API_RESULT_MOCK)
        )

        organization = PrescriberOrganizationFactory(siret=siret, is_head_office=False)
        old_updated_at = organization.updated_at

        # No update required
        call_command("update_prescriber_organizations_with_api_entreprise", verbosity=0, days=7)
        organization.refresh_from_db()
        assert organization.updated_at == old_updated_at
        assert organization.is_head_office is False

        # Force updated of latest records
        call_command("update_prescriber_organizations_with_api_entreprise", verbosity=0, days=0)
        organization.refresh_from_db()
        assert organization.updated_at > old_updated_at
        assert organization.is_head_office is True


class TestPrescriberOrganizationQuerySet:
    def test_member_required(self):
        organization = PrescriberOrganizationFactory()
        user = PrescriberFactory()
        assert PrescriberOrganization.objects.member_required(user).count() == 0

        organization.add_or_activate_member(user)
        assert PrescriberOrganization.objects.member_required(user).get() == organization

        membership = organization.memberships.get()
        membership.is_active = False
        membership.save(update_fields=("is_active",))

        assert PrescriberOrganization.objects.member_required(user).count() == 0


class TestPrescriberOrganizationAdmin:
    ACCEPT_BUTTON_LABEL = "Valider l'habilitation"
    REFUSE_BUTTON_LABEL = "Refuser l'habilitation"
    ACCEPT_AFTER_REFUSAL_BUTTON_LABEL = "Annuler le refus et valider l'habilitation"
    FORMSETS_PAYLOAD = {
        "prescribermembership_set-TOTAL_FORMS": 1,
        "prescribermembership_set-INITIAL_FORMS": 0,
        "utils-pksupportremark-content_type-object_id-TOTAL_FORMS": 1,
        "utils-pksupportremark-content_type-object_id-INITIAL_FORMS": 0,
    }

    @pytest.fixture(autouse=True)
    def setup_method(self):
        # super user
        self.superuser = ItouStaffFactory(is_superuser=True)

        # staff user with permissions
        self.user = ItouStaffFactory()
        content_type = ContentType.objects.get_for_model(PrescriberOrganization)
        permission = Permission.objects.get(content_type=content_type, codename="change_prescriberorganization")
        self.user.user_permissions.add(permission)

    def test_refuse_prescriber_habilitation_by_superuser(self, client):
        client.force_login(self.superuser)

        prescriber_organization = PrescriberOrganizationFactory(
            authorized=True,
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertContains(response, self.REFUSE_BUTTON_LABEL)

        post_data = {
            "id": prescriber_organization.pk,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": prescriber_organization.kind,
            "name": prescriber_organization.name,
            "siret": prescriber_organization.siret,
            "_authorization_action_refuse": "Refuser+l'habilitation",
            **self.FORMSETS_PAYLOAD,
        }

        response = client.post(url, data=post_data)
        assert response.status_code == 302

        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert not updated_prescriber_organization.is_authorized
        assert updated_prescriber_organization.kind == PrescriberOrganizationKind.OTHER
        assert updated_prescriber_organization.authorization_updated_by == self.superuser
        assert updated_prescriber_organization.authorization_status == PrescriberAuthorizationStatus.REFUSED

    def test_refuse_prescriber_habilitation_error(self, client):
        client.force_login(self.superuser)

        prescriber_organization = PrescriberOrganizationFactory(
            authorized=True,
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
        )
        PrescriberOrganizationFactory(
            kind=PrescriberOrganizationKind.OTHER,
            siret=prescriber_organization.siret,
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertContains(response, self.REFUSE_BUTTON_LABEL)

        post_data = {
            "id": prescriber_organization.pk,
            "siret": prescriber_organization.siret,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": prescriber_organization.kind,
            "name": prescriber_organization.name,
            "_authorization_action_refuse": "Refuser+l'habilitation",
            **self.FORMSETS_PAYLOAD,
        }

        response = client.post(url, data=post_data)
        assert response.status_code == 302
        assertMessages(
            response,
            [
                messages.Message(
                    messages.ERROR,
                    "Impossible de refuser cette habilitation: cela changerait son type vers “Autre” "
                    "et une autre organisation de type “Autre” a le même SIRET.",
                )
            ],
        )

        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert updated_prescriber_organization.is_authorized
        assert updated_prescriber_organization.kind == PrescriberOrganizationKind.PE
        assert updated_prescriber_organization.authorization_updated_by is None
        assert updated_prescriber_organization.authorization_status == PrescriberAuthorizationStatus.VALIDATED

    def test_refuse_prescriber_habilitation_pending_status(self, client):
        client.force_login(self.user)

        prescriber_organization = PrescriberOrganizationFactory(
            authorized=True,
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
            authorization_status=PrescriberAuthorizationStatus.NOT_SET,
            is_authorized=False,
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertContains(response, self.REFUSE_BUTTON_LABEL)

        post_data = {
            "id": prescriber_organization.pk,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": prescriber_organization.kind,
            "name": prescriber_organization.name,
            "_authorization_action_refuse": "Refuser+l'habilitation",
            **self.FORMSETS_PAYLOAD,
        }

        response = client.post(url, data=post_data)
        assert response.status_code == 302

        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert not updated_prescriber_organization.is_authorized
        assert updated_prescriber_organization.kind == PrescriberOrganizationKind.OTHER
        assert updated_prescriber_organization.authorization_updated_by == self.user
        assert updated_prescriber_organization.authorization_status == PrescriberAuthorizationStatus.REFUSED

    def test_refuse_prescriber_habilitation_not_pending_status(self, client):
        client.force_login(self.user)

        prescriber_organization = PrescriberOrganizationFactory(
            authorized=True,
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertNotContains(response, self.REFUSE_BUTTON_LABEL)

        post_data = {
            "id": prescriber_organization.pk,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": prescriber_organization.kind,
            "name": prescriber_organization.name,
            "_authorization_action_refuse": "Refuser+l'habilitation",
            **self.FORMSETS_PAYLOAD,
        }

        response = client.post(url, data=post_data)
        assert response.status_code == 403

        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert updated_prescriber_organization.is_authorized == prescriber_organization.is_authorized
        assert updated_prescriber_organization.kind == prescriber_organization.kind
        assert updated_prescriber_organization.authorization_updated_by is None
        assert updated_prescriber_organization.authorization_status == prescriber_organization.authorization_status

    def test_accept_prescriber_habilitation_by_superuser(self, client):
        client.force_login(self.superuser)

        prescriber_organization = PrescriberOrganizationFactory(
            authorized=True,
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertContains(response, self.ACCEPT_BUTTON_LABEL)

        post_data = {
            "id": prescriber_organization.pk,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": prescriber_organization.kind,
            "name": prescriber_organization.name,
            "_authorization_action_validate": "Valider+l'habilitation",
            **self.FORMSETS_PAYLOAD,
        }

        response = client.post(url, data=post_data)
        assert response.status_code == 302

        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert updated_prescriber_organization.is_authorized
        assert updated_prescriber_organization.kind == prescriber_organization.kind
        assert updated_prescriber_organization.authorization_updated_by == self.superuser
        assert updated_prescriber_organization.authorization_status == PrescriberAuthorizationStatus.VALIDATED

    def test_accept_prescriber_habilitation_pending_status(self, client):
        client.force_login(self.user)

        prescriber_organization = PrescriberOrganizationFactory(
            authorized=True,
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
            authorization_status=PrescriberAuthorizationStatus.NOT_SET,
            is_authorized=False,
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertContains(response, self.ACCEPT_BUTTON_LABEL)

        post_data = {
            "id": prescriber_organization.pk,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": prescriber_organization.kind,
            "name": prescriber_organization.name,
            "_authorization_action_validate": "Valider+l'habilitation",
            **self.FORMSETS_PAYLOAD,
        }

        response = client.post(url, data=post_data)
        assert response.status_code == 302

        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert updated_prescriber_organization.is_authorized
        assert updated_prescriber_organization.kind == prescriber_organization.kind
        assert updated_prescriber_organization.authorization_updated_by == self.user
        assert updated_prescriber_organization.authorization_status == PrescriberAuthorizationStatus.VALIDATED

    def test_accept_prescriber_habilitation_refused_status(self, client):
        client.force_login(self.user)

        prescriber_organization = PrescriberOrganizationFactory(
            authorized=True,
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
            authorization_status=PrescriberAuthorizationStatus.REFUSED,
            is_authorized=False,
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertContains(response, self.ACCEPT_AFTER_REFUSAL_BUTTON_LABEL)

        post_data = {
            "id": prescriber_organization.pk,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": prescriber_organization.kind,
            "name": prescriber_organization.name,
            "_authorization_action_validate": "Valider+l'habilitation",
            **self.FORMSETS_PAYLOAD,
        }

        response = client.post(url, data=post_data)
        assert response.status_code == 302

        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert updated_prescriber_organization.is_authorized
        assert updated_prescriber_organization.kind == prescriber_organization.kind
        assert updated_prescriber_organization.authorization_updated_by == self.user
        assert updated_prescriber_organization.authorization_status == PrescriberAuthorizationStatus.VALIDATED

    def test_accept_prescriber_habilitation_other_status(self, client):
        client.force_login(self.user)

        prescriber_organization = PrescriberOrganizationFactory(
            authorized=True,
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assert response.status_code == 200

        post_data = {
            "id": prescriber_organization.pk,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": prescriber_organization.kind,
            "name": prescriber_organization.name,
            "_authorization_action_refuse": "Refuser+l'habilitation",
            **self.FORMSETS_PAYLOAD,
        }

        response = client.post(url, data=post_data)
        assert response.status_code == 403

        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert updated_prescriber_organization.is_authorized == prescriber_organization.is_authorized
        assert updated_prescriber_organization.kind == prescriber_organization.kind
        assert updated_prescriber_organization.authorization_updated_by is None
        assert updated_prescriber_organization.authorization_status == prescriber_organization.authorization_status

    def test_prescriber_habilitation_readonly_user(self, client):
        ro_user = ItouStaffFactory()
        content_type = ContentType.objects.get_for_model(PrescriberOrganization)
        permission = Permission.objects.get(content_type=content_type, codename="view_prescriberorganization")
        ro_user.user_permissions.add(permission)
        client.force_login(ro_user)

        prescriber_organization = PrescriberOrganizationFactory(
            siret="83987278500010",
            department="14",
            post_code="14000",
            with_pending_authorization=True,
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertNotContains(response, self.ACCEPT_BUTTON_LABEL)
        assertNotContains(response, self.REFUSE_BUTTON_LABEL)
        assertNotContains(response, self.ACCEPT_AFTER_REFUSAL_BUTTON_LABEL)

        prescriber_organization.authorization_status = PrescriberAuthorizationStatus.REFUSED
        prescriber_organization.save()

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertNotContains(response, self.ACCEPT_BUTTON_LABEL)
        assertNotContains(response, self.REFUSE_BUTTON_LABEL)
        assertNotContains(response, self.ACCEPT_AFTER_REFUSAL_BUTTON_LABEL)

    def test_accept_prescriber_habilitation_odc_to_is_brsa(self, client):
        client.force_login(self.user)

        prescriber_organization = PrescriberOrganizationFactory(
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
            authorization_status=PrescriberAuthorizationStatus.NOT_SET,
            kind=PrescriberOrganizationKind.ODC,
            is_authorized=False,
            is_brsa=False,
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertContains(response, self.ACCEPT_BUTTON_LABEL)

        assert not prescriber_organization.is_brsa
        post_data = {
            "id": prescriber_organization.pk,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": prescriber_organization.kind,
            "name": prescriber_organization.name,
            "siret": prescriber_organization.siret,
            "_authorization_action_validate": "Valider+l'habilitation",
            **self.FORMSETS_PAYLOAD,
        }

        response = client.post(url, data=post_data)
        assert response.status_code == 302

        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert updated_prescriber_organization.is_authorized
        assert updated_prescriber_organization.kind == prescriber_organization.kind
        assert updated_prescriber_organization.authorization_updated_by == self.user
        assert updated_prescriber_organization.authorization_status == PrescriberAuthorizationStatus.VALIDATED
        assert updated_prescriber_organization.is_brsa

    def test_prevent_prescriber_habilitation_organization_type_other(self, client):
        client.force_login(self.user)

        prescriber_organization = PrescriberOrganizationFactory(
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
            authorization_status=PrescriberAuthorizationStatus.NOT_SET,
            is_authorized=False,
            kind=PrescriberOrganizationKind.OTHER,
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        response = client.get(url)
        assertContains(response, self.ACCEPT_BUTTON_LABEL)

        post_data = {
            "id": prescriber_organization.pk,
            "siret": prescriber_organization.siret,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": prescriber_organization.kind,
            "name": prescriber_organization.name,
            "_authorization_action_validate": "Valider+l'habilitation",
            **self.FORMSETS_PAYLOAD,
        }

        # cannot validate an organization typed "Other"
        response = client.post(url, data=post_data)
        assert response.status_code == 302
        assertMessages(
            response,
            [
                messages.Message(
                    messages.ERROR,
                    "Pour habiliter cette organisation, vous devez sélectionner un type différent de “Autre”.",
                )
            ],
        )

        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert updated_prescriber_organization.authorization_status == PrescriberAuthorizationStatus.NOT_SET

        # can validate it with changed type
        post_data["kind"] = PrescriberOrganizationKind.PE
        response = client.post(url, data=post_data)

        assert response.status_code == 302
        updated_prescriber_organization = PrescriberOrganization.objects.get(pk=prescriber_organization.pk)
        assert updated_prescriber_organization.is_authorized
        assert updated_prescriber_organization.kind == PrescriberOrganizationKind.PE
        assert updated_prescriber_organization.authorization_updated_by == self.user
        assert updated_prescriber_organization.authorization_status == PrescriberAuthorizationStatus.VALIDATED

    def test_prevent_setting_prescriber_organization_to_other_once_accepted(self, client):
        client.force_login(self.user)

        prescriber_organization = PrescriberOrganizationFactory(
            authorized=True,
            siret="83987278500010",
            department="14",
            post_code="14000",
            authorization_updated_at=datetime.now(tz=get_current_timezone()),
        )

        url = reverse("admin:prescribers_prescriberorganization_change", args=[prescriber_organization.pk])
        post_data = {
            "id": prescriber_organization.pk,
            "siret": prescriber_organization.siret,
            "post_code": prescriber_organization.post_code,
            "department": prescriber_organization.department,
            "kind": PrescriberOrganizationKind.OTHER,
            "name": prescriber_organization.name,
            **self.FORMSETS_PAYLOAD,
        }

        response = client.post(url, data=post_data)
        assert response.status_code == 200
        expected_msg = "Cette organisation a été habilitée. Vous devez sélectionner un type différent de “Autre”."
        assert len(response.context["errors"]) == 1
        assert response.context["errors"][0] == [expected_msg]


class TestUpdateRefusedPrescriberOrganizationKindManagementCommands:
    def test_update_kind(self):
        # Prescriber organization - one sample per authorization status
        # One refused prescriber organizations without duplicated siret which will be
        # updated in this subset
        for authorization_status in list(PrescriberAuthorizationStatus):
            PrescriberOrganizationFactory(authorization_status=authorization_status)

        # Prescriber organization - Authorization Status = Refused - with duplicated siret
        # These Prescriber organization kind won't be updated into Other, because
        # of unicity constraint on (siret,kind)
        PrescriberOrganizationFactory(
            authorization_status=PrescriberAuthorizationStatus.REFUSED,
            siret="83987278500010",
            kind=PrescriberOrganizationKind.CHRS,
        )
        PrescriberOrganizationFactory(
            authorization_status=PrescriberAuthorizationStatus.REFUSED,
            siret="83987278500010",
            kind=PrescriberOrganizationKind.CHU,
        )

        # Controls before execution
        assert len(PrescriberAuthorizationStatus) + 2 == PrescriberOrganization.objects.all().count()
        assert (
            3
            == PrescriberOrganization.objects.filter(
                authorization_status=PrescriberAuthorizationStatus.REFUSED
            ).count()
        )
        assert 0 == PrescriberOrganization.objects.filter(kind=PrescriberOrganizationKind.OTHER).count()

        # Update refused prescriber organizations without duplicated siret
        call_command("update_refused_prescriber_organizations_kind")

        # Controls after execution
        assert len(PrescriberAuthorizationStatus) + 2 == PrescriberOrganization.objects.all().count()
        assert (
            3
            == PrescriberOrganization.objects.filter(
                authorization_status=PrescriberAuthorizationStatus.REFUSED
            ).count()
        )
        assert 1 == PrescriberOrganization.objects.filter(kind=PrescriberOrganizationKind.OTHER).count()


@pytest.mark.parametrize("organization_kind", PrescriberOrganizationKind)
def test_organization_kind_to_PE_typologie_prescripteur(organization_kind):
    # If you add a new value to PrescriberOrganizationKind:
    # can this kind be sent to PoleEmploi or should it be considered as "sensitive" ?
    # Cf PE_SENSITIVE_PRESCRIBER_KINDS variable
    EXPECTED_TYPOLOGIE = {
        PrescriberOrganizationKind.AFPA: "AFPA",
        PrescriberOrganizationKind.ASE: "Autre",
        PrescriberOrganizationKind.CAARUD: "Autre",
        PrescriberOrganizationKind.CADA: "CADA",
        PrescriberOrganizationKind.CAF: "CAF",
        PrescriberOrganizationKind.CAP_EMPLOI: "CAP_EMPLOI",
        PrescriberOrganizationKind.CAVA: "CAVA",
        PrescriberOrganizationKind.CCAS: "CCAS",
        PrescriberOrganizationKind.CHRS: "CHRS",
        PrescriberOrganizationKind.CHU: "CHU",
        PrescriberOrganizationKind.CIDFF: "Autre",
        PrescriberOrganizationKind.CPH: "CPH",
        PrescriberOrganizationKind.CSAPA: "Autre",
        PrescriberOrganizationKind.DEPT: "DEPT",
        PrescriberOrganizationKind.E2C: "E2C",
        PrescriberOrganizationKind.EPIDE: "EPIDE",
        PrescriberOrganizationKind.HUDA: "HUDA",
        PrescriberOrganizationKind.ML: "ML",
        PrescriberOrganizationKind.MSA: "MSA",
        PrescriberOrganizationKind.OACAS: "OACAS",
        PrescriberOrganizationKind.OCASF: "OCASF",
        PrescriberOrganizationKind.ODC: "ODC",
        PrescriberOrganizationKind.OIL: "OIL",
        PrescriberOrganizationKind.OHPD: "OHPD",
        PrescriberOrganizationKind.ORIENTEUR: "Orienteur",
        PrescriberOrganizationKind.OTHER: "Autre",
        PrescriberOrganizationKind.PE: "PE",
        PrescriberOrganizationKind.PENSION: "Autre",
        PrescriberOrganizationKind.PIJ_BIJ: "PIJ_BIJ",
        PrescriberOrganizationKind.PJJ: "Autre",
        PrescriberOrganizationKind.PLIE: "PLIE",
        PrescriberOrganizationKind.PREVENTION: "Autre",
        PrescriberOrganizationKind.RS_FJT: "RS_FJT",
        PrescriberOrganizationKind.SPIP: "Autre",
    }
    assert organization_kind.to_PE_typologie_prescripteur() == EXPECTED_TYPOLOGIE[organization_kind]


def test_validated_odc_is_brsa_constraint():
    organization = PrescriberOrganizationFactory(
        kind=PrescriberOrganizationKind.ODC,
        authorized=True,
    )
    assert organization.is_brsa
    with pytest.raises(IntegrityError):
        PrescriberOrganization.objects.filter(pk=organization.pk).update(is_brsa=False)


def test_prevent_validated_authorization_if_other_constraint():
    organization = PrescriberOrganizationFactory(kind=PrescriberOrganizationKind.OTHER)
    with pytest.raises(IntegrityError):
        PrescriberOrganization.objects.filter(pk=organization.pk).update(
            authorization_status=PrescriberAuthorizationStatus.VALIDATED
        )


def test_deactivate_last_admin(admin_client, mailoutbox):
    organization = PrescriberOrganizationWithMembershipFactory()
    membership = organization.memberships.first()
    assert membership.is_admin

    change_url = reverse("admin:prescribers_prescriberorganization_change", args=[organization.pk])
    response = admin_client.get(change_url)
    assert response.status_code == 200

    response = admin_client.post(
        change_url,
        data={
            "id": organization.id,
            "siret": organization.siret,
            "kind": organization.kind.value,
            "name": organization.name,
            "phone": organization.phone,
            "email": organization.email,
            "code_safir_poleAemploi": "",
            "description": organization.description,
            "address_line_1": organization.address_line_1,
            "address_line_2": organization.address_line_2,
            "post_code": organization.post_code,
            "city": organization.city,
            "department": organization.department,
            "coords": "",
            "prescribermembership_set-TOTAL_FORMS": "2",
            "prescribermembership_set-INITIAL_FORMS": "1",
            "prescribermembership_set-MIN_NUM_FORMS": "0",
            "prescribermembership_set-MAX_NUM_FORMS": "1000",
            "prescribermembership_set-0-id": membership.pk,
            "prescribermembership_set-0-organization": organization.pk,
            "prescribermembership_set-0-user": membership.user.pk,
            # prescribermembership_set-0-is_admin is absent
            "utils-pksupportremark-content_type-object_id-TOTAL_FORMS": 1,
            "utils-pksupportremark-content_type-object_id-INITIAL_FORMS": 0,
            "_continue": "Enregistrer+et+continuer+les+modifications",
        },
    )
    assertRedirects(response, change_url, fetch_redirect_response=False)
    response = admin_client.get(change_url)
    assertContains(
        response,
        (
            "Vous venez de supprimer le dernier administrateur de la structure. "
            "Les membres restants risquent de solliciter le support."
        ),
    )

    assert_set_admin_role__removal(membership.user, organization, mailoutbox)


def test_delete_admin(admin_client, mailoutbox):
    organization = PrescriberOrganizationWithMembershipFactory()
    membership = organization.memberships.first()
    assert membership.is_admin

    change_url = reverse("admin:prescribers_prescriberorganization_change", args=[organization.pk])
    response = admin_client.get(change_url)
    assert response.status_code == 200

    response = admin_client.post(
        change_url,
        data={
            "id": organization.id,
            "siret": organization.siret,
            "kind": organization.kind.value,
            "name": organization.name,
            "phone": organization.phone,
            "email": organization.email,
            "code_safir_poleAemploi": "",
            "description": organization.description,
            "address_line_1": organization.address_line_1,
            "address_line_2": organization.address_line_2,
            "post_code": organization.post_code,
            "city": organization.city,
            "department": organization.department,
            "coords": "",
            "prescribermembership_set-TOTAL_FORMS": "2",
            "prescribermembership_set-INITIAL_FORMS": "1",
            "prescribermembership_set-MIN_NUM_FORMS": "0",
            "prescribermembership_set-MAX_NUM_FORMS": "1000",
            "prescribermembership_set-0-id": membership.pk,
            "prescribermembership_set-0-organization": organization.pk,
            "prescribermembership_set-0-user": membership.user.pk,
            "prescribermembership_set-0-is_admin": "on",
            "prescribermembership_set-0-DELETE": "on",
            "utils-pksupportremark-content_type-object_id-TOTAL_FORMS": 1,
            "utils-pksupportremark-content_type-object_id-INITIAL_FORMS": 0,
            "_continue": "Enregistrer+et+continuer+les+modifications",
        },
    )
    assertRedirects(response, change_url, fetch_redirect_response=False)
    response = admin_client.get(change_url)

    assert_set_admin_role__removal(membership.user, organization, mailoutbox)


def test_add_admin(admin_client, mailoutbox):
    organization = PrescriberOrganizationWithMembershipFactory()
    membership = organization.memberships.first()
    prescriber = PrescriberFactory()
    assert membership.is_admin

    change_url = reverse("admin:prescribers_prescriberorganization_change", args=[organization.pk])
    response = admin_client.get(change_url)
    assert response.status_code == 200

    response = admin_client.post(
        change_url,
        data={
            "id": organization.id,
            "siret": organization.siret,
            "kind": organization.kind.value,
            "name": organization.name,
            "phone": organization.phone,
            "email": organization.email,
            "code_safir_poleAemploi": "",
            "description": organization.description,
            "address_line_1": organization.address_line_1,
            "address_line_2": organization.address_line_2,
            "post_code": organization.post_code,
            "city": organization.city,
            "department": organization.department,
            "coords": "",
            "prescribermembership_set-TOTAL_FORMS": "2",
            "prescribermembership_set-INITIAL_FORMS": "1",
            "prescribermembership_set-MIN_NUM_FORMS": "0",
            "prescribermembership_set-MAX_NUM_FORMS": "1000",
            "prescribermembership_set-0-id": membership.pk,
            "prescribermembership_set-0-organization": organization.pk,
            "prescribermembership_set-0-user": membership.user.pk,
            "prescribermembership_set-0-is_admin": "on",
            "prescribermembership_set-1-organization": organization.pk,
            "prescribermembership_set-1-user": prescriber.pk,
            "prescribermembership_set-1-is_admin": "on",
            "utils-pksupportremark-content_type-object_id-TOTAL_FORMS": 1,
            "utils-pksupportremark-content_type-object_id-INITIAL_FORMS": 0,
            "_continue": "Enregistrer+et+continuer+les+modifications",
        },
    )
    assertRedirects(response, change_url, fetch_redirect_response=False)
    response = admin_client.get(change_url)

    assert_set_admin_role__creation(prescriber, organization, mailoutbox)


def test_prescriber_kinds_are_alphabetically_sorted():
    assert PrescriberOrganizationKind.choices == sorted(
        PrescriberOrganizationKind.choices,
        key=lambda c: (
            c[0] == PrescriberOrganizationKind.OTHER,  # OTHER kind should be last
            c[1].lower(),
        ),
    )
