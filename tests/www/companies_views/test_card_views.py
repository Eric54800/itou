import pytest
from django.template.defaultfilters import urlencode
from django.urls import reverse
from django.utils.html import escape
from pytest_django.asserts import assertContains, assertNotContains

from itou.companies.enums import ContractType
from itou.jobs.models import Appellation
from itou.utils.urls import add_url_params
from tests.cities.factories import create_city_vannes
from tests.companies.factories import (
    CompanyFactory,
    CompanyWithMembershipAndJobsFactory,
    JobDescriptionFactory,
)
from tests.jobs.factories import create_test_romes_and_appellations
from tests.users.factories import JobSeekerFactory
from tests.utils.test import assert_previous_step, assertSnapshotQueries, parse_response_to_soup


class TestCardView:
    OTHER_TAB_ID = "autres-metiers"
    APPLY = "Postuler"

    @pytest.fixture(autouse=True)
    def setup_method(self, client):
        create_test_romes_and_appellations(("N1101", "N1105", "N1103", "N4105"))
        self.vannes = create_city_vannes()

    def test_card(self, client):
        company = CompanyFactory(with_membership=True)
        url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        response = client.get(url)
        assert response.context["siae"] == company
        assertContains(response, escape(company.display_name))
        assertContains(response, company.email)
        assertContains(response, company.phone)
        assertNotContains(response, self.OTHER_TAB_ID)
        assertContains(response, self.APPLY)

    def test_card_no_active_members(self, client, snapshot):
        company = CompanyFactory(with_membership=False, for_snapshot=True, pk=100)
        url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        response = client.get(url)
        soup = parse_response_to_soup(response, selector="#main")
        assert str(soup) == snapshot()

    def test_card_tally_url_with_user(self, client, snapshot):
        company = CompanyFactory(with_membership=False, for_snapshot=True, pk=100)
        url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        user = JobSeekerFactory(pk=10)
        client.force_login(user)
        response = client.get(url)
        soup = parse_response_to_soup(response, selector=".c-box--action")
        assert str(soup) == snapshot()

    def test_card_tally_url_no_user(self, client, snapshot):
        company = CompanyFactory(with_membership=False, for_snapshot=True, pk=100)
        url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        response = client.get(url)
        soup = parse_response_to_soup(response, selector=".c-box--action")
        assert str(soup) == snapshot()

    def test_card_no_active_jobs(self, client, snapshot):
        company = CompanyFactory(name="les petits jardins", with_membership=True)
        job_description = JobDescriptionFactory(
            company=company,
            custom_name="Plaquiste",
            location=self.vannes,
            contract_type=ContractType.PERMANENT,
            is_active=False,
        )
        url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        response = client.get(url)

        nav_tabs_soup = parse_response_to_soup(response, selector=".s-tabs-01__nav")
        assert str(nav_tabs_soup) == snapshot(name="nav-tabs")

        tab_content_soup = parse_response_to_soup(
            response,
            selector=".tab-content",
            replace_in_attr=[
                (
                    "href",
                    f"/company/job_description/{job_description.pk}/card",
                    "/company/job_description/[PK of JobDescription]/card",
                ),
                ("href", f"?back_url=/company/{company.pk}/card", "?back_url=/company/[PK of Company]/card"),
                ("href", f"/apply/{company.pk}/start", "/apply/[PK of Company]/start"),
            ],
        )
        assert str(tab_content_soup) == snapshot(name="tab-content")

        assertContains(response, self.APPLY)

    def test_card_no_other_jobs(self, client, snapshot):
        company = CompanyFactory(name="les petits jardins", with_membership=True)
        job_description = JobDescriptionFactory(
            company=company,
            custom_name="Plaquiste",
            location=self.vannes,
            contract_type=ContractType.PERMANENT,
        )
        url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        response = client.get(url)

        nav_tabs_soup = parse_response_to_soup(response, selector=".s-tabs-01__nav")
        assert str(nav_tabs_soup) == snapshot(name="nav-tabs")

        tab_content_soup = parse_response_to_soup(
            response,
            selector=".tab-content",
            replace_in_attr=[
                (
                    "href",
                    f"/company/job_description/{job_description.pk}/card",
                    "/company/job_description/[PK of JobDescription]/card",
                ),
                ("href", f"?back_url=/company/{company.pk}/card", "?back_url=/company/[PK of Company]/card"),
                ("href", f"/apply/{company.pk}/start", "/apply/[PK of Company]/start"),
            ],
        )
        assert str(tab_content_soup) == snapshot(name="tab-content")

        assertContains(response, self.APPLY)

    def test_card_active_and_other_jobs(self, client, snapshot):
        company = CompanyFactory(name="les petits jardins", with_membership=True)
        # Job appellation must be different, the factory picks one at random.
        app1, app2 = Appellation.objects.filter(code__in=["12001", "12007"]).order_by("code")
        active_job_description = JobDescriptionFactory(
            company=company,
            custom_name="Plaquiste",
            location=self.vannes,
            contract_type=ContractType.PERMANENT,
            appellation=app1,
        )
        other_job_description = JobDescriptionFactory(
            company=company,
            custom_name="Peintre",
            location=self.vannes,
            contract_type=ContractType.PERMANENT,
            appellation=app2,
            is_active=False,
        )
        url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        response = client.get(url)

        nav_tabs_soup = parse_response_to_soup(response, selector=".s-tabs-01__nav")
        assert str(nav_tabs_soup) == snapshot(name="nav-tabs")

        tab_content_soup = parse_response_to_soup(
            response,
            selector=".tab-content",
            replace_in_attr=[
                (
                    "href",
                    f"/company/job_description/{active_job_description.pk}/card",
                    "/company/job_description/[PK of JobDescription]/card",
                ),
                (
                    "href",
                    f"/company/job_description/{other_job_description.pk}/card",
                    "/company/job_description/[PK of JobDescription]/card",
                ),
                ("href", f"?back_url=/company/{company.pk}/card", "?back_url=/company/[PK of Company]/card"),
                ("href", f"/apply/{company.pk}/start", "/apply/[PK of Company]/start"),
            ],
        )
        assert str(tab_content_soup) == snapshot(name="tab-content")

        assertContains(response, self.APPLY)

    def test_block_job_applications(self, client, snapshot):
        company = CompanyFactory(block_job_applications=True)
        job_description = JobDescriptionFactory(
            company=company,
            custom_name="Plaquiste",
            location=self.vannes,
            contract_type=ContractType.PERMANENT,
        )
        url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        response = client.get(url)

        nav_tabs_soup = parse_response_to_soup(response, selector=".s-tabs-01__nav")
        assert str(nav_tabs_soup) == snapshot(name="nav-tabs")

        tab_content_soup = parse_response_to_soup(
            response,
            selector=".tab-content",
            replace_in_attr=[
                (
                    "href",
                    f"/company/job_description/{job_description.pk}/card",
                    "/company/job_description/[PK of JobDescription]/card",
                ),
                ("href", f"?back_url=/company/{company.pk}/card", "?back_url=/company/[PK of Company]/card"),
                ("href", f"/apply/{company.pk}/start", "/apply/[PK of Company]/start"),
            ],
        )
        assert str(tab_content_soup) == snapshot(name="tab-content")

        assertNotContains(response, self.APPLY)

    def test_card_flow(self, client):
        company = CompanyFactory(with_jobs=True)
        list_url = reverse("search:employers_results")
        company_card_base_url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        company_card_initial_url = add_url_params(
            company_card_base_url,
            {"back_url": list_url},
        )
        response = client.get(company_card_initial_url)
        assert_previous_step(response, list_url, back_to_list=True)

        # Has link to job description
        job = company.job_description_through.first()
        job_description_link = f"{job.get_absolute_url()}?back_url={urlencode(list_url)}"
        assertContains(response, job_description_link)

        # Job description card has link back to list again
        response = client.get(job_description_link)
        assert_previous_step(response, list_url, back_to_list=True)
        # And also a link to the company card with a return link to list_url (the same as the first visited page)
        company_card_url_other_formatting = f"{company_card_base_url}?back_url={urlencode(list_url)}"
        assertContains(response, company_card_url_other_formatting)

    def test_company_card_render_markdown(self, client):
        company = CompanyFactory(
            description="*Lorem ipsum*, **bold** and [link](https://beta.gouv.fr).",
            provided_support="* list 1\n* list 2\n\n1. list 1\n2. list 2",
        )
        company_card_url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        response = client.get(company_card_url)
        attrs = 'target="_blank" rel="noopener" aria-label="Ouverture dans un nouvel onglet"'
        assertContains(
            response,
            f'<p><em>Lorem ipsum</em>, <strong>bold</strong> and <a href="https://beta.gouv.fr" {attrs}>link</a>.</p>',
        )
        assertContains(
            response, "<ul>\n<li>list 1</li>\n<li>list 2</li>\n</ul>\n<ol>\n<li>list 1</li>\n<li>list 2</li>\n</ol>"
        )

    def test_company_card_render_markdown_forbidden_tags(self, client):
        company = CompanyFactory(
            description='# Gros titre\n<script></script>\n<span class="font-size:200px;">Gros texte</span>',
        )
        company_card_url = reverse("companies_views:card", kwargs={"siae_id": company.pk})
        response = client.get(company_card_url)
        assertContains(response, "Gros titre\n\n<p>Gros texte</p>")


class TestJobDescriptionCardView:
    @pytest.fixture(autouse=True)
    def setup_method(self, client):
        create_test_romes_and_appellations(["N1101"])

    def test_job_description_card(self, client, snapshot):
        company = CompanyWithMembershipAndJobsFactory()
        job_description = company.job_description_through.first()
        job_description.description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
        job_description.open_positions = 1234
        job_description.save()
        url = reverse("companies_views:job_description_card", kwargs={"job_description_id": job_description.pk})
        with assertSnapshotQueries(snapshot):
            response = client.get(url)
        assert response.context["job"] == job_description
        assert response.context["siae"] == company
        assertContains(response, job_description.description)
        assertContains(response, escape(job_description.display_name))
        assertContains(response, escape(company.display_name))
        OPEN_POSITION_TEXT = "1234 postes ouverts au recrutement"
        assertContains(response, OPEN_POSITION_TEXT)

        job_description.is_active = False
        job_description.save()
        response = client.get(url)
        assertContains(response, job_description.description)
        assertContains(response, escape(job_description.display_name))
        assertContains(response, escape(company.display_name))
        assertNotContains(response, OPEN_POSITION_TEXT)

        # Check other jobs
        assert response.context["others_active_jobs"].count() == 3
        for other_active_job in response.context["others_active_jobs"]:
            assertContains(response, other_active_job.display_name, html=True)

        response = client.get(add_url_params(url, {"back_url": reverse("companies_views:job_description_list")}))
        assert_previous_step(response, reverse("companies_views:job_description_list"), back_to_list=True)

    def test_job_description_card_render_markdown(self, client):
        company = CompanyWithMembershipAndJobsFactory()
        job_description = company.job_description_through.first()
        job_description.description = "*Lorem ipsum*, **bold** and [link](https://beta.gouv.fr)."
        job_description.profile_description = "* list 1\n* list 2\n\n1. list 1\n2. list 2"
        job_description.save()
        url = reverse("companies_views:job_description_card", kwargs={"job_description_id": job_description.pk})
        response = client.get(url)
        attrs = 'target="_blank" rel="noopener" aria-label="Ouverture dans un nouvel onglet"'
        assertContains(
            response,
            f'<p><em>Lorem ipsum</em>, <strong>bold</strong> and <a href="https://beta.gouv.fr" {attrs}>link</a>.</p>',
        )
        assertContains(
            response,
            "<ul>\n<li>list 1</li>\n<li>list 2</li>\n</ul>\n<ol>\n<li>list 1</li>\n<li>list 2</li>\n</ol>",
        )

    def test_job_description_card_render_markdown_links(self, client):
        company = CompanyWithMembershipAndJobsFactory()
        job_description = company.job_description_through.first()
        job_description.description = "www.lien1.com\nhttps://lien2.com\n[test](https://lien3.com)\n[test2](lien4.bzh)\ntest@admin.com\nftp://lien5.com"
        job_description.save()
        url = reverse("companies_views:job_description_card", kwargs={"job_description_id": job_description.pk})
        response = client.get(url)
        attrs = 'target="_blank" rel="noopener" aria-label="Ouverture dans un nouvel onglet"'
        assertContains(
            response,
            f"""<p><a href="http://www.lien1.com" {attrs}>www.lien1.com</a><br>
<a href="https://lien2.com" {attrs}>https://lien2.com</a><br>
<a href="https://lien3.com" {attrs}>test</a><br>
<a href="https://lien4.bzh" {attrs}>test2</a><br>
<a href="mailto:test@admin.com" {attrs}>test@admin.com</a><br>
<a href="https://ftp://lien5.com" {attrs}>ftp://lien5.com</a></p>""",  # allowing only HTTP and HTTPS protocols
        )

    def test_job_description_card_render_markdown_forbidden_tags(self, client):
        company = CompanyWithMembershipAndJobsFactory()
        job_description = company.job_description_through.first()
        job_description.description = (
            '# Gros titre\n<script></script>\n<span class="font-size:200px;">Gros texte</span>'
        )
        job_description.save()
        url = reverse("companies_views:job_description_card", kwargs={"job_description_id": job_description.pk})
        response = client.get(url)
        assertContains(response, "Gros titre\n\n<p>Gros texte</p>")

    def test_card_tally_url_with_user(self, client, snapshot):
        job_description = JobDescriptionFactory(
            pk=42,
            company__pk=100,
            company__for_snapshot=True,
        )
        url = reverse("companies_views:job_description_card", kwargs={"job_description_id": job_description.pk})
        client.force_login(JobSeekerFactory(pk=10))
        response = client.get(url)
        soup = parse_response_to_soup(response, selector=".c-box--action")
        assert str(soup) == snapshot(name="without_other_jobs")
        # Create other job_description
        JobDescriptionFactory(company=job_description.company)
        response = client.get(url)
        soup = parse_response_to_soup(response, selector=".c-box--action")
        assert str(soup) == snapshot(name="with_other_jobs")
        # Check link consistency
        assert parse_response_to_soup(response, selector="#recrutements")

    def test_card_tally_url_no_user(self, client, snapshot):
        job_description = JobDescriptionFactory(
            pk=42,
            company__pk=100,
            company__for_snapshot=True,
        )
        url = reverse("companies_views:job_description_card", kwargs={"job_description_id": job_description.pk})
        response = client.get(url)
        soup = parse_response_to_soup(response, selector=".c-box--action")
        assert str(soup) == snapshot()
