import pytest
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.urls import reverse

from itou.communications import registry as notifications_registry
from itou.communications.models import DisabledNotification, NotificationSettings
from tests.institutions.factories import LaborInspectorFactory
from tests.users.factories import (
    EmployerFactory,
    ItouStaffFactory,
    JobSeekerFactory,
    PrescriberFactory,
)
from tests.utils.test import TestCase, assertSnapshotQueries


@pytest.mark.usefixtures("unittest_compatibility")
class EditUserNotificationsTest(TestCase):
    def test_staff_user_not_allowed(self):
        staff_user = ItouStaffFactory()
        self.client.force_login(staff_user)
        url = reverse("dashboard:edit_user_notifications")
        response = self.client.get(url)
        assert response.status_code == 404

    def test_labor_inspector_not_allowed(self):
        labor_inspector = LaborInspectorFactory(membership=True)
        self.client.force_login(labor_inspector)
        url = reverse("dashboard:edit_user_notifications")
        response = self.client.get(url)
        assert response.status_code == 404

    def test_employer_allowed(self):
        employer = EmployerFactory(with_company=True)
        self.client.force_login(employer)
        url = reverse("dashboard:edit_user_notifications")
        with assertSnapshotQueries(self.snapshot(name="view queries")):
            response = self.client.get(url)
        assert response.status_code == 200

    def test_prescriber_allowed(self):
        prescriber = PrescriberFactory(membership=True)
        self.client.force_login(prescriber)
        url = reverse("dashboard:edit_user_notifications")
        with assertSnapshotQueries(self.snapshot(name="view queries")):
            response = self.client.get(url)
        assert response.status_code == 200

    def test_solo_adviser_allowed(self):
        solo_adviser = PrescriberFactory(membership=False)
        self.client.force_login(solo_adviser)
        url = reverse("dashboard:edit_user_notifications")
        with assertSnapshotQueries(self.snapshot(name="view queries")):
            response = self.client.get(url)
        assert response.status_code == 200

    def test_job_seeker_allowed(self):
        job_seeker = JobSeekerFactory()
        self.client.force_login(job_seeker)
        url = reverse("dashboard:edit_user_notifications")
        with assertSnapshotQueries(self.snapshot(name="view queries")):
            response = self.client.get(url)
        assert response.status_code == 200

    def test_employer_create_update_notification_settings(self):
        employer = EmployerFactory(with_company=True)
        company = employer.company_set.first()
        self.client.force_login(employer)
        url = reverse("dashboard:edit_user_notifications")

        # Fetch available notifications for this user/company
        available_notifications = [
            notification
            for notification in notifications_registry
            if notification(employer, company).is_manageable_by_user()
        ]

        # No notification settings defined by default
        assert not NotificationSettings.objects.exists()
        assert not DisabledNotification.objects.exists()

        with assertSnapshotQueries(self.snapshot(name="view queries - enable all notifications")):
            response = self.client.post(
                url, data={notification.__name__: "on" for notification in available_notifications}
            )
        assert response.status_code == 302
        assert response["Location"] == "/dashboard/"
        self.assertQuerySetEqual(
            NotificationSettings.objects.all(),
            [
                NotificationSettings.objects.get(
                    user=employer,
                    structure_type=ContentType.objects.get_for_model(company),
                    structure_pk=company.pk,
                    disabled_notifications__isnull=True,
                )
            ],
        )
        assert not DisabledNotification.objects.exists()

        # Update, disable all notifications
        with assertSnapshotQueries(self.snapshot(name="view queries - disable all notifications")):
            # Send data to bind to the form, otherwise is_valid() returns False
            response = self.client.post(url, {"foo": "bar"})
        assert response.status_code == 302
        assert response["Location"] == "/dashboard/"
        self.assertQuerySetEqual(
            NotificationSettings.objects.all(),
            [
                NotificationSettings.objects.annotate(Count("disabled_notifications")).get(
                    user=employer,
                    structure_type=ContentType.objects.get_for_model(company),
                    structure_pk=company.pk,
                    disabled_notifications__count=len(available_notifications),
                )
            ],
        )
        assert DisabledNotification.objects.count() == len(available_notifications)

    def test_prescriber_create_update_notification_settings(self):
        prescriber = PrescriberFactory(membership=True)
        organization = prescriber.prescriberorganization_set.first()
        self.client.force_login(prescriber)
        url = reverse("dashboard:edit_user_notifications")

        # Fetch available notifications for this user/organization
        available_notifications = [
            notification
            for notification in notifications_registry
            if notification(prescriber, organization).is_manageable_by_user()
        ]

        # No notification settings defined by default
        assert not NotificationSettings.objects.exists()
        assert not DisabledNotification.objects.exists()

        with assertSnapshotQueries(self.snapshot(name="view queries - enable all notifications")):
            response = self.client.post(
                url, data={notification.__name__: "on" for notification in available_notifications}
            )
        assert response.status_code == 302
        assert response["Location"] == "/dashboard/"
        self.assertQuerySetEqual(
            NotificationSettings.objects.all(),
            [
                NotificationSettings.objects.get(
                    user=prescriber,
                    structure_type=ContentType.objects.get_for_model(organization),
                    structure_pk=organization.pk,
                    disabled_notifications__isnull=True,
                )
            ],
        )
        assert not DisabledNotification.objects.exists()

        # Update, disable all notifications
        with assertSnapshotQueries(self.snapshot(name="view queries - disable all notifications")):
            # Send data to bind to the form, otherwise is_valid() returns False
            response = self.client.post(url, {"foo": "bar"})
        assert response.status_code == 302
        assert response["Location"] == "/dashboard/"
        self.assertQuerySetEqual(
            NotificationSettings.objects.all(),
            [
                NotificationSettings.objects.annotate(Count("disabled_notifications")).get(
                    user=prescriber,
                    structure_type=ContentType.objects.get_for_model(organization),
                    structure_pk=organization.pk,
                    disabled_notifications__count=len(available_notifications),
                )
            ],
        )
        assert DisabledNotification.objects.count() == len(available_notifications)

    def test_solo_adviser_create_update_notification_settings(self):
        solo_adviser = PrescriberFactory(membership=False)
        self.client.force_login(solo_adviser)
        url = reverse("dashboard:edit_user_notifications")

        # Fetch available notifications for this user
        available_notifications = [
            notification
            for notification in notifications_registry
            if notification(solo_adviser).is_manageable_by_user()
        ]

        # No notification settings defined by default
        assert not NotificationSettings.objects.exists()
        assert not DisabledNotification.objects.exists()

        with assertSnapshotQueries(self.snapshot(name="view queries - enable all notifications")):
            response = self.client.post(
                url, data={notification.__name__: "on" for notification in available_notifications}
            )
        assert response.status_code == 302
        assert response["Location"] == "/dashboard/"
        self.assertQuerySetEqual(
            NotificationSettings.objects.all(),
            [
                NotificationSettings.objects.get(
                    user=solo_adviser,
                    structure_type=None,
                    structure_pk=None,
                    disabled_notifications__isnull=True,
                )
            ],
        )
        assert not DisabledNotification.objects.exists()

        # Update, disable all notifications
        with assertSnapshotQueries(self.snapshot(name="view queries - disable all notifications")):
            # Send data to bind to the form, otherwise is_valid() returns False
            response = self.client.post(url, {"foo": "bar"})
        assert response.status_code == 302
        assert response["Location"] == "/dashboard/"
        self.assertQuerySetEqual(
            NotificationSettings.objects.all(),
            [
                NotificationSettings.objects.annotate(Count("disabled_notifications")).get(
                    user=solo_adviser,
                    structure_type=None,
                    structure_pk=None,
                    disabled_notifications__count=len(available_notifications),
                )
            ],
        )
        assert DisabledNotification.objects.count() == len(available_notifications)

    def test_job_seeker_create_update_notification_settings(self):
        job_seeker = JobSeekerFactory()
        self.client.force_login(job_seeker)
        url = reverse("dashboard:edit_user_notifications")

        # Fetch available notifications for this user
        available_notifications = [
            notification for notification in notifications_registry if notification(job_seeker).is_manageable_by_user()
        ]

        # No notification settings defined by default
        assert not NotificationSettings.objects.exists()
        assert not DisabledNotification.objects.exists()

        with assertSnapshotQueries(self.snapshot(name="view queries - enable all notifications")):
            response = self.client.post(
                url, data={notification.__name__: "on" for notification in available_notifications}
            )
        assert response.status_code == 302
        assert response["Location"] == "/dashboard/"
        self.assertQuerySetEqual(
            NotificationSettings.objects.all(),
            [
                NotificationSettings.objects.get(
                    user=job_seeker,
                    structure_type=None,
                    structure_pk=None,
                    disabled_notifications__isnull=True,
                )
            ],
        )
        assert not DisabledNotification.objects.exists()

        # Update, disable all notifications
        with assertSnapshotQueries(self.snapshot(name="view queries - disable all notifications")):
            # Send data to bind to the form, otherwise is_valid() returns False
            response = self.client.post(url, {"foo": "bar"})
        assert response.status_code == 302
        assert response["Location"] == "/dashboard/"
        self.assertQuerySetEqual(
            NotificationSettings.objects.all(),
            [
                NotificationSettings.objects.annotate(Count("disabled_notifications")).get(
                    user=job_seeker,
                    structure_type=None,
                    structure_pk=None,
                    disabled_notifications__count=len(available_notifications),
                )
            ],
        )
        assert DisabledNotification.objects.count() == len(available_notifications)
