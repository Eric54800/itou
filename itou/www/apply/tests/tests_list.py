from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from pytest_django.asserts import assertContains, assertNumQueries

from itou.approvals.factories import SuspensionFactory
from itou.cities.factories import create_city_saint_andre
from itou.eligibility.enums import AdministrativeCriteriaLevel
from itou.eligibility.factories import EligibilityDiagnosisFactory
from itou.eligibility.models import AdministrativeCriteria
from itou.job_applications.enums import SenderKind
from itou.job_applications.factories import (
    JobApplicationFactory,
    JobApplicationSentByJobSeekerFactory,
    JobApplicationSentByPrescriberFactory,
)
from itou.job_applications.models import JobApplication, JobApplicationWorkflow
from itou.jobs.factories import create_test_romes_and_appellations
from itou.jobs.models import Appellation
from itou.prescribers.factories import PrescriberMembershipFactory, PrescriberOrganizationWithMembershipFactory
from itou.siaes.factories import SiaeFactory, SiaeJobDescriptionFactory
from itou.users.factories import PrescriberFactory
from itou.utils.test import TestCase, format_html
from itou.utils.widgets import DuetDatePickerWidget


class ProcessListTest(TestCase):
    def setUp(self):
        """
        Create three organizations with two members each:
        - pole_emploi: job seekers agency.
        - l_envol: an emergency center for homeless people.
        - hit_pit: a boxing gym looking for boxers.

        Pole Emploi prescribers:
        - Thibault
        - laurie

        L'envol prescribers:
        - Audrey
        - Manu

        Hit Pit staff:
        - Eddie
        """

        # Pole Emploi
        pole_emploi = PrescriberOrganizationWithMembershipFactory(
            authorized=True, name="Pôle emploi", membership__user__first_name="Thibault"
        )
        PrescriberMembershipFactory(organization=pole_emploi, user__first_name="Laurie")
        thibault_pe = pole_emploi.members.get(first_name="Thibault")
        laurie_pe = pole_emploi.members.get(first_name="Laurie")

        # L'Envol
        l_envol = PrescriberOrganizationWithMembershipFactory(name="L'Envol", membership__user__first_name="Manu")
        PrescriberMembershipFactory(organization=l_envol, user__first_name="Audrey")
        audrey_envol = l_envol.members.get(first_name="Audrey")

        # Hit Pit
        hit_pit = SiaeFactory(name="Hit Pit", with_membership=True, membership__user__first_name="Eddie")
        eddie_hit_pit = hit_pit.members.get(first_name="Eddie")

        # Now send applications
        for i, state in enumerate(JobApplicationWorkflow.states):
            creation_date = timezone.now() - timezone.timedelta(days=i)
            job_application = JobApplicationSentByPrescriberFactory(
                to_siae=hit_pit,
                state=state,
                created_at=creation_date,
                sender=thibault_pe,
                sender_prescriber_organization=pole_emploi,
                eligibility_diagnosis=None,
            )

        maggie = job_application.job_seeker
        maggie.save(update_fields={"first_name": "Maggie"})
        JobApplicationSentByPrescriberFactory(
            to_siae=hit_pit,
            sender=laurie_pe,
            sender_prescriber_organization=pole_emploi,
            job_seeker=maggie,
            eligibility_diagnosis=None,
        )

        self.prescriber_base_url = reverse("apply:list_for_prescriber")
        self.job_seeker_base_url = reverse("apply:list_for_job_seeker")
        self.siae_base_url = reverse("apply:list_for_siae")
        self.prescriber_exports_url = reverse("apply:list_for_prescriber_exports")
        self.siae_exports_url = reverse("apply:list_for_siae_exports")

        # Variables available for unit tests
        self.pole_emploi = pole_emploi
        self.hit_pit = hit_pit
        self.l_envol = l_envol
        self.thibault_pe = thibault_pe
        self.laurie_pe = laurie_pe
        self.eddie_hit_pit = eddie_hit_pit
        self.audrey_envol = audrey_envol
        self.maggie = maggie


####################################################
################### Job Seeker #####################  # noqa E266
####################################################


class ProcessListJobSeekerTest(ProcessListTest):
    def test_list_for_job_seeker_view(self):
        """
        Maggie wants to see job applications sent for her.
        """
        self.client.force_login(self.maggie)
        response = self.client.get(self.job_seeker_base_url)

        # Count job applications used by the template
        total_applications = len(response.context["job_applications_page"].object_list)

        # Result page should contain all SIAE's job applications.
        assert total_applications == self.maggie.job_applications.count()

    def test_list_for_job_seeker_view_filtered_by_state(self):
        """
        Provide a list of job applications sent by a job seeker
        and filtered by a state.
        """
        self.client.force_login(self.maggie)
        expected_state = self.maggie.job_applications.last().state
        params = urlencode({"states": [expected_state]}, True)
        url = f"{self.job_seeker_base_url}?{params}"
        response = self.client.get(url)

        # Count job applications used by the template
        applications = response.context["job_applications_page"].object_list

        # Result page should only contain job applications which status
        # matches the one selected by the user.
        assert len(applications) == 1
        assert applications[0].state == expected_state

    def test_list_for_job_seeker_view_filtered_by_dates(self):
        """
        Provide a list of job applications sent by a job seeker
        and filtered by dates
        """
        now = timezone.now()

        for diff_day in [7, 5, 3, 0]:
            JobApplicationSentByJobSeekerFactory(
                created_at=now - timezone.timedelta(days=diff_day), job_seeker=self.maggie
            )

        self.client.force_login(self.maggie)

        date_format = DuetDatePickerWidget.INPUT_DATE_FORMAT

        start_date = now - timezone.timedelta(days=5)
        end_date = now - timezone.timedelta(days=1)
        query = urlencode(
            {
                "start_date": timezone.localdate(start_date).strftime(date_format),
                "end_date": timezone.localdate(end_date).strftime(date_format),
            }
        )
        url = f"{self.job_seeker_base_url}?{query}"
        response = self.client.get(url)
        applications = response.context["job_applications_page"].object_list

        assert len(applications) == 2
        assert applications[0].created_at >= start_date
        assert applications[0].created_at <= end_date


###################################################
#################### SIAE #########################  # noqa E266
###################################################


class ProcessListSiaeTest(ProcessListTest):
    def test_list_for_siae_view(self):
        """
        Eddie wants to see a list of job applications sent to his SIAE.
        """
        city = create_city_saint_andre()
        create_test_romes_and_appellations(["N4105"], appellations_per_rome=2)
        appellations = Appellation.objects.all()[:2]
        job1 = SiaeJobDescriptionFactory(siae=self.hit_pit, appellation=appellations[0], location=city)
        job2 = SiaeJobDescriptionFactory(siae=self.hit_pit, appellation=appellations[1], location=city)
        for job_application in JobApplication.objects.all():
            job_application.selected_jobs.set([job1, job2])
        self.client.force_login(self.eddie_hit_pit)
        with self.assertNumQueries(
            1  # fetch django session
            + 1  # fetch user
            + 3  # check for membership & infos
            #
            # SiaeFilterJobApplicationsForm:
            + 1  # get list of senders (distinct sender_id)
            + 1  # get list of job seekers (distinct job_seeker_id)
            + 1  # get list of administrative criteria
            + 1  # get list of job application
            + 1  # prefetch selected jobs
            + 1  # prefetch jobs appellation
            + 1  # select distinct sender_prescriber_organization
            #
            # Paginate the job applications queryset:
            + 1  # has_suspended_approval subquery
            + 1  # select job applications with annotations
            + 1  # prefetch selected jobs
            + 1  # prefetch jobs appellation
            + 1  # prefetch jobs location
            + 1  # prefetch approvals
            #
            # Render template:
            + 1  # context processor: user siae membership
            # 6 job applications
            + 6
            * (
                1  # select poleemploiapproval (latest_pe_approval)
                + 1  # select latest eligibility diagnosis (job_application.eligibility_diagnosis_by_siae_required)
                + 1  # select last valid diagnosis made by prescriber (does not exist)
                + 1  # select last valid diagnosis made by siae (exists)
            )
            + 3  # update session
        ):
            response = self.client.get(self.siae_base_url)

        total_applications = len(response.context["job_applications_page"].object_list)

        # Result page should contain all SIAE's job applications.
        assert total_applications == self.hit_pit.job_applications_received.not_archived().count()

    def test_list_rdv_insertion_promo(self):
        self.client.force_login(self.eddie_hit_pit)
        response = self.client.get(self.siae_base_url)
        promo_text = "Besoin d'un outil de prise de RDV par mail et/ou SMS"
        self.assertContains(response, promo_text)

        # Check with an other SIAE without applications - the promo is there too
        other_siae = SiaeFactory(with_membership=True)
        self.client.force_login(other_siae.members.first())
        response = self.client.get(self.siae_base_url)
        self.assertContains(response, "Aucune candidature pour le moment.")
        self.assertContains(response, promo_text)

    def test_list_for_siae_view__filtered_by_one_state(self):
        """
        Eddie wants to see only accepted job applications.
        """
        self.client.force_login(self.eddie_hit_pit)
        state_accepted = JobApplicationWorkflow.STATE_ACCEPTED
        params = urlencode({"states": [state_accepted]}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)

        applications = response.context["job_applications_page"].object_list

        assert len(applications) == 1
        assert applications[0].state == state_accepted

    def test_list_for_siae_view__filtered_by_many_states(self):
        """
        Eddie wants to see NEW and PROCESSING job applications.
        """
        self.client.force_login(self.eddie_hit_pit)
        job_applications_states = [JobApplicationWorkflow.STATE_NEW, JobApplicationWorkflow.STATE_PROCESSING]
        params = urlencode({"states": job_applications_states}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)

        applications = response.context["job_applications_page"].object_list

        assert len(applications) == 3
        assert applications[0].state.name in job_applications_states

    def test_list_for_siae_view__filtered_by_dates(self):
        """
        Eddie wants to see job applications sent at a specific date.
        """
        self.client.force_login(self.eddie_hit_pit)
        date_format = DuetDatePickerWidget.INPUT_DATE_FORMAT
        job_applications = self.hit_pit.job_applications_received.not_archived().order_by("created_at")
        jobs_in_range = job_applications[3:]
        start_date = jobs_in_range[0].created_at

        # Negative indexing is not allowed in querysets
        end_date = jobs_in_range[len(jobs_in_range) - 1].created_at
        query = urlencode(
            {
                "start_date": timezone.localdate(start_date).strftime(date_format),
                "end_date": timezone.localdate(end_date).strftime(date_format),
            }
        )
        url = f"{self.siae_base_url}?{query}"
        response = self.client.get(url)
        applications = response.context["job_applications_page"].object_list

        assert len(applications) == 5
        assert applications[0].created_at >= start_date
        assert applications[0].created_at <= end_date

    def test_list_for_siae_view__empty_dates_in_params(self):
        """
        Our form uses a Datepicker that adds empty start and end dates
        in the HTTP query if they are not filled in by the user.
        Make sure the template loads all available job applications if fields are empty.
        """
        self.client.force_login(self.eddie_hit_pit)
        url = f"{self.siae_base_url}?start_date=&end_date="
        response = self.client.get(url)
        total_applications = len(response.context["job_applications_page"].object_list)

        assert total_applications == self.hit_pit.job_applications_received.not_archived().count()

    def test_view__filtered_by_sender_organization_name(self):
        """
        Eddie wants to see applications sent by Pôle emploi.
        """
        self.client.force_login(self.eddie_hit_pit)
        sender_organization = self.pole_emploi
        params = urlencode({"sender_organizations": [sender_organization.id]}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)

        applications = response.context["job_applications_page"].object_list

        assert len(applications) == 8
        assert applications[0].sender_prescriber_organization.id == sender_organization.id

    def test_view__filtered_by_sender_name(self):
        """
        Eddie wants to see applications sent by a member of Pôle emploi.
        """
        self.client.force_login(self.eddie_hit_pit)
        sender = self.thibault_pe
        params = urlencode({"senders": [sender.id]}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)

        applications = response.context["job_applications_page"].object_list

        assert len(applications) == 7
        assert applications[0].sender.id == sender.id

    def test_view__filtered_by_job_seeker_name(self):
        """
        Eddie wants to see Maggie's job applications.
        """
        self.client.force_login(self.eddie_hit_pit)
        job_seekers_ids = [self.maggie.id]
        params = urlencode({"job_seekers": job_seekers_ids}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)

        applications = response.context["job_applications_page"].object_list

        assert len(applications) == 2
        assert applications[0].job_seeker.id in job_seekers_ids

    def test_view__filtered_by_many_organization_names(self):
        """
        Eddie wants to see applications sent by Pôle emploi and L'Envol.
        """
        self.client.force_login(self.eddie_hit_pit)
        senders_ids = [self.pole_emploi.id, self.l_envol.id]
        params = urlencode({"sender_organizations": [self.thibault_pe.id, self.audrey_envol.id]}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)

        applications = response.context["job_applications_page"].object_list

        assert len(applications) == 8
        assert applications[0].sender_prescriber_organization.id in senders_ids

    def test_view__filtered_by_pass_state(self):
        """
        Eddie wants to see applications with a suspended or in progress IAE PASS.
        """
        now = timezone.now()
        yesterday = (now - timezone.timedelta(days=1)).date()
        self.client.force_login(self.eddie_hit_pit)

        params = urlencode(
            {
                "states": [JobApplicationWorkflow.STATE_ACCEPTED, JobApplicationWorkflow.STATE_NEW],
                "pass_iae_active": True,
            },
            True,
        )
        response = self.client.get(f"{self.siae_base_url}?{params}")
        assert len(response.context["job_applications_page"].object_list) == 0

        job_application = JobApplicationFactory(
            with_approval=True,
            state=JobApplicationWorkflow.STATE_ACCEPTED,
            hiring_start_at=yesterday,
            approval__start_at=yesterday,
            to_siae=self.hit_pit,
        )
        response = self.client.get(f"{self.siae_base_url}?{params}")
        applications = response.context["job_applications_page"].object_list
        assert len(applications) == 1
        assert job_application in applications

        params = urlencode(
            {
                "states": [JobApplicationWorkflow.STATE_ACCEPTED, JobApplicationWorkflow.STATE_NEW],
                "pass_iae_suspended": True,
            },
            True,
        )
        response = self.client.get(f"{self.siae_base_url}?{params}")
        assert len(response.context["job_applications_page"].object_list) == 0

        SuspensionFactory(
            approval=job_application.approval,
            start_at=yesterday,
            end_at=now + timezone.timedelta(days=2),
        )
        response = self.client.get(f"{self.siae_base_url}?{params}")

        applications = response.context["job_applications_page"].object_list
        assert len(applications) == 1
        assert job_application in applications

    def test_view__filtered_by_eligibility_validated(self):
        """
        Eddie wants to see applications of job seeker for whom
        the diagnosis of eligibility has been validated.
        """
        self.client.force_login(self.eddie_hit_pit)

        params = urlencode({"eligibility_validated": True})
        url = f"{self.siae_base_url}?{params}"

        response = self.client.get(url)
        assert len(response.context["job_applications_page"].object_list) == 0

        EligibilityDiagnosisFactory(job_seeker=self.maggie)

        response = self.client.get(url)
        # Maggie has two applications, one created in the state loop and the other created by SentByPrescriberFactory
        assert len(response.context["job_applications_page"].object_list) == 2

    def test_view__filtered_by_administrative_criteria(self):
        """
        Eddie wants to see applications of job seeker for whom
        the diagnosis of eligibility has been validated with specific criteria.
        """
        self.client.force_login(self.eddie_hit_pit)

        diagnosis = EligibilityDiagnosisFactory(job_seeker=self.maggie)

        level1_criterion = AdministrativeCriteria.objects.filter(level=AdministrativeCriteriaLevel.LEVEL_1).first()
        level2_criterion = AdministrativeCriteria.objects.filter(level=AdministrativeCriteriaLevel.LEVEL_2).first()
        level1_other_criterion = AdministrativeCriteria.objects.filter(
            level=AdministrativeCriteriaLevel.LEVEL_1
        ).last()

        diagnosis.administrative_criteria.add(level1_criterion)
        diagnosis.administrative_criteria.add(level2_criterion)
        diagnosis.save()

        # Filter by level1 criterion
        params = urlencode({"criteria": [level1_criterion.pk]}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)
        applications = response.context["job_applications_page"].object_list
        assert len(applications) == 2

        # Filter by level2 criterion
        params = urlencode({"criteria": [level2_criterion.pk]}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)
        applications = response.context["job_applications_page"].object_list
        assert len(applications) == 2

        # Filter by two criteria
        params = urlencode({"criteria": [level1_criterion.pk, level2_criterion.pk]}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)
        applications = response.context["job_applications_page"].object_list
        assert len(applications) == 2

        # Filter by other criteria
        params = urlencode({"criteria": [level1_other_criterion.pk]}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)
        applications = response.context["job_applications_page"].object_list
        assert len(applications) == 0

    def test_view__filtered_by_jobseeker_department(self):
        """
        Eddie wants to see applications of job seeker who live in given department.
        """
        self.client.force_login(self.eddie_hit_pit)

        # Maggie moves to Department 37
        self.maggie.post_code = "37000"
        self.maggie.save()

        params = urlencode({"departments": ["37"]}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)
        applications = response.context["job_applications_page"].object_list

        # Maggie has two applications and is the only one living in department 37.
        assert len(applications) == 2

    def test_view__filtered_by_selected_job(self):
        """
        Eddie wants to see applications with a given job appellation.
        """
        self.client.force_login(self.eddie_hit_pit)

        create_test_romes_and_appellations(["M1805", "N1101"], appellations_per_rome=2)
        (appellation1, appellation2) = Appellation.objects.all().order_by("?")[:2]
        JobApplicationSentByJobSeekerFactory(to_siae=self.hit_pit, selected_jobs=[appellation1])
        JobApplicationSentByJobSeekerFactory(to_siae=self.hit_pit, selected_jobs=[appellation2])

        params = urlencode({"selected_jobs": [appellation1.pk]}, True)
        url = f"{self.siae_base_url}?{params}"
        response = self.client.get(url)
        applications = response.context["job_applications_page"].object_list

        assert len(applications) == 1
        assert appellation1 in [job_desc.appellation for job_desc in applications[0].selected_jobs.all()]


####################################################
################### Prescriber #####################  # noqa E266
####################################################


class ProcessListPrescriberTest(ProcessListTest):
    def test_list_for_prescriber_view(self):
        """
        Connect as Thibault to see a list of job applications
        sent by his organization (Pôle emploi).
        """
        self.client.force_login(self.thibault_pe)
        response = self.client.get(self.prescriber_base_url)

        # Count job applications used by the template
        total_applications = len(response.context["job_applications_page"].object_list)

        assert total_applications == self.pole_emploi.jobapplication_set.count()

    def test_list_for_prescriber_pe_exports_view(self):
        self.client.force_login(self.thibault_pe)
        response = self.client.get(self.prescriber_exports_url)

        assert 200 == response.status_code
        assertContains(response, "Toutes les candidatures")
        assert format_html(response, id="besoin-dun-chiffre") == [
            '<div class="card my-4" id="besoin-dun-chiffre">\n'
            ' <div class="card-body">\n'
            '  <p class="card-title">\n'
            '   <i class="ri-information-line mr-1">\n'
            "   </i>\n"
            "   <b>\n"
            "    Besoin d'un chiffre ?\n"
            "   </b>\n"
            "  </p>\n"
            '  <p class="card-text">\n'
            '   <span class="text-primary">\n'
            "    Accédez aux données de votre agence (non nominatives) compilées, "
            "calculées et mises à jour quotidiennement :\n"
            "   </span>\n"
            "  </p>\n"
            "  <ul>\n"
            "   <li>\n"
            '    <a href="/stats/pe/state/main" rel="noopener" target="_blank">\n'
            "     Voir les données de l'ensemble de l'état des candidatures orientées\n"
            "    </a>\n"
            "   </li>\n"
            "   <li>\n"
            '    <a href="/stats/pe/conversion/main" rel="noopener" target="_blank">\n'
            "     Voir les données du taux de transformation des candidatures\n"
            "    </a>\n"
            "   </li>\n"
            "  </ul>\n"
            "  <p>\n"
            "  </p>\n"
            " </div>\n"
            "</div>\n",
        ]

    def test_list_for_prescriber_exports_view(self):
        self.client.force_login(self.audrey_envol)
        response = self.client.get(self.prescriber_exports_url)
        assert 200 == response.status_code
        assert format_html(response, id="besoin-dun-chiffre") == []  # no link to pilotage

    def test_list_for_prescriber_exports_download_view(self):
        """
        Connect as Thibault to see a list of available job applications exports
        """
        self.client.force_login(self.thibault_pe)

        response = self.client.get(self.prescriber_exports_url)
        sample_date = response.context["job_applications_by_month"][0]["month"]
        month_identifier = sample_date.strftime("%Y-%d")
        download_url = reverse(
            "apply:list_for_prescriber_exports_download", kwargs={"month_identifier": month_identifier}
        )

        response = self.client.get(download_url)

        assert 200 == response.status_code
        assert "spreadsheetml" in response.get("Content-Type")

    def test_view__filtered_by_state(self):
        """
        Thibault wants to filter a list of job applications
        by the default initial state.
        """
        self.client.force_login(self.thibault_pe)
        expected_state = JobApplicationWorkflow.initial_state
        params = urlencode({"states": [expected_state]}, True)
        url = f"{self.prescriber_base_url}?{params}"
        response = self.client.get(url)

        applications = response.context["job_applications_page"].object_list
        assert len(applications) == 2
        assert applications[0].state == expected_state

    def test_view__filtered_by_sender_name(self):
        """
        Thibault wants to see job applications sent by his colleague Laurie.
        He filters results using her full name.
        """
        self.client.force_login(self.thibault_pe)
        sender_id = self.laurie_pe.id
        params = urlencode({"senders": sender_id})
        url = f"{self.prescriber_base_url}?{params}"
        response = self.client.get(url)

        applications = response.context["job_applications_page"].object_list
        assert len(applications) == 1
        assert applications[0].sender.id == sender_id

    def test_view__filtered_by_job_seeker_name(self):
        """
        Thibault wants to see Maggie's job applications.
        """
        self.client.force_login(self.thibault_pe)
        job_seekers_ids = [self.maggie.id]
        params = urlencode({"job_seekers": job_seekers_ids}, True)
        url = f"{self.prescriber_base_url}?{params}"
        response = self.client.get(url)

        applications = response.context["job_applications_page"].object_list
        assert len(applications) == 2
        assert applications[0].job_seeker.id in job_seekers_ids

    def test_view__filtered_by_siae_name(self):
        """
        Thibault wants to see applications sent to Hit Pit.
        """
        self.client.force_login(self.thibault_pe)
        to_siaes_ids = [self.hit_pit.pk]
        params = urlencode({"to_siaes": to_siaes_ids}, True)
        url = f"{self.prescriber_base_url}?{params}"
        response = self.client.get(url)

        applications = response.context["job_applications_page"].object_list
        assert len(applications) == 8
        assert applications[0].to_siae.pk in to_siaes_ids


def test_list_for_unauthorized_prescriber_view(client):
    prescriber = PrescriberFactory()
    JobApplicationFactory(
        job_seeker_with_address=True,
        job_seeker__first_name="Supersecretname",
        job_seeker__last_name="Unknown",
        job_seeker__created_by=PrescriberFactory(),  # to check for useless queries
        sender=prescriber,
        sender_kind=SenderKind.PRESCRIBER,
    )
    client.force_login(prescriber)
    url = reverse("apply:list_for_prescriber")
    with assertNumQueries(
        1  # fetch django session
        + 1  # fetch user
        + 1  # check for membeship
        + 1  # get list of senders (distinct sender_id)
        + 1  # get list of job seekers (distinct job_seeker_id)
        + 1  # get list of administrative criteria
        + 3  # get list of job application + prefetch of job descriptions + prefetch of approvals
        + 1  # get list of siaes (distinct)
        + 3  # count, list & prefetch of job application
        + 1  # check user membership again
        + 3  # update session
    ):
        response = client.get(url)

    assertContains(response, "<b>S… U…</b>", html=True)
    # Unfortunately, the job seeker's name is available in the filters
    # assertNotContains(response, "Supersecretname")


####################################################
################### Prescriber export list #########
####################################################


class ProcessListExportsPrescriberTest(ProcessListTest):
    def test_list_for_prescriber_exports_view(self):
        """
        Connect as Thibault to see a list of available job applications exports
        """
        self.client.force_login(self.thibault_pe)
        response = self.client.get(self.prescriber_exports_url)

        assert 200 == response.status_code
        assertContains(response, "Toutes les candidatures")

    def test_list_for_prescriber_exports_as_siae_view(self):
        """
        Connect as a SIAE and try to see the prescriber export -> redirected
        """
        self.client.force_login(self.eddie_hit_pit)
        response = self.client.get(self.prescriber_exports_url)

        assert 302 == response.status_code


####################################################
################### SIAE export list #########
####################################################


class ProcessListExportsSiaeTest(ProcessListTest):
    def test_list_for_siae_exports_view(self):
        """
        Connect as a SIAE to see a list of available job applications exports
        """
        self.client.force_login(self.eddie_hit_pit)
        response = self.client.get(self.siae_exports_url)

        assert 200 == response.status_code
        assertContains(response, "Toutes les candidatures")
        assert format_html(response, id="besoin-dun-chiffre") == [
            '<div class="card my-4" id="besoin-dun-chiffre">\n'
            ' <div class="card-body">\n'
            '  <p class="card-title">\n'
            '   <i class="ri-information-line mr-1">\n'
            "   </i>\n"
            "   <b>\n"
            "    Besoin d'un chiffre ?\n"
            "   </b>\n"
            "  </p>\n"
            '  <p class="card-text">\n'
            '   <span class="text-primary">\n'
            "    Accédez aux\n"
            '    <a href="/stats/siae/hiring" rel="noopener" target="_blank">\n'
            "     données de recrutement de votre structure\n"
            "    </a>\n"
            "    (non nominatives) compilées, calculées et mises à jour quotidiennement.\n"
            "   </span>\n"
            "  </p>\n"
            " </div>\n"
            "</div>\n",
        ]

    def test_list_for_siae_exports_as_prescriber_view(self):
        """
        Connect as Thibault and try to see the siae export -> redirected
        """
        self.client.force_login(self.thibault_pe)
        response = self.client.get(self.siae_exports_url)

        assert 404 == response.status_code


####################################################
################### Prescriber export download #########
####################################################


class ProcessListExportsDownloadPrescriberTest(ProcessListTest):
    def test_list_for_prescriber_exports_download_view(self):
        """
        Connect as Thibault to download a XLSX export of available job applications
        """
        self.client.force_login(self.thibault_pe)
        download_url = reverse("apply:list_for_prescriber_exports_download")

        response = self.client.get(download_url)

        assert 200 == response.status_code
        assert "spreadsheetml" in response.get("Content-Type")

    def test_list_for_prescriber_exports_download_view_by_month(self):
        """
        Connect as Thibault to download a CSV export of available job applications
        """
        self.client.force_login(self.thibault_pe)

        response = self.client.get(self.prescriber_exports_url)
        sample_date = response.context["job_applications_by_month"][0]["month"]
        month_identifier = sample_date.strftime("%Y-%d")
        download_url = reverse(
            "apply:list_for_prescriber_exports_download", kwargs={"month_identifier": month_identifier}
        )

        response = self.client.get(download_url)

        assert 200 == response.status_code
        assert "spreadsheetml" in response.get("Content-Type")

    def test_list_for_siae_exports_download_view(self):
        """
        Connect as Thibault and attempt to download a XLSX export of available job applications from SIAE
        """
        self.client.force_login(self.thibault_pe)

        response = self.client.get(self.prescriber_exports_url)
        sample_date = response.context["job_applications_by_month"][0]["month"]
        month_identifier = sample_date.strftime("%Y-%d")
        download_url = reverse("apply:list_for_siae_exports_download", kwargs={"month_identifier": month_identifier})

        response = self.client.get(download_url)

        assert 404 == response.status_code


####################################################
################### Prescriber export download #########
####################################################


class ProcessListExportsDownloadSiaeTest(ProcessListTest):
    def test_list_for_siae_exports_download_view(self):
        """
        Connect as Thibault to download a XLSX export of available job applications
        """
        self.client.force_login(self.eddie_hit_pit)
        download_url = reverse("apply:list_for_siae_exports_download")

        response = self.client.get(download_url)

        assert 200 == response.status_code
        assert "spreadsheetml" in response.get("Content-Type")

    def test_list_for_siae_exports_download_view_by_month(self):
        """
        Connect as Thibault to download a CSV export of available job applications
        """
        self.client.force_login(self.eddie_hit_pit)

        response = self.client.get(self.siae_exports_url)
        sample_date = response.context["job_applications_by_month"][0]["month"]
        month_identifier = sample_date.strftime("%Y-%d")
        download_url = reverse("apply:list_for_siae_exports_download", kwargs={"month_identifier": month_identifier})

        response = self.client.get(download_url)

        assert 200 == response.status_code
        assert "spreadsheetml" in response.get("Content-Type")

    def test_list_for_prescriber_exports_download_view(self):
        """
        Connect as SIAE and attempt to download a XLSX export of available job applications from prescribers
        """
        self.client.force_login(self.eddie_hit_pit)

        response = self.client.get(self.siae_exports_url)
        sample_date = response.context["job_applications_by_month"][0]["month"]
        month_identifier = sample_date.strftime("%Y-%d")
        download_url = reverse(
            "apply:list_for_prescriber_exports_download", kwargs={"month_identifier": month_identifier}
        )

        response = self.client.get(download_url)

        assert 302 == response.status_code
