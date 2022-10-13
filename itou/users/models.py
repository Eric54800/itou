import time
import uuid
from collections import Counter

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.postgres.fields import CIEmailField
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Count
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from itou.approvals.models import Approval, PoleEmploiApproval
from itou.asp.models import (
    AllocationDuration,
    Commune,
    Country,
    EducationLevel,
    EmployerType,
    LaneExtension,
    LaneType,
    RSAAllocation,
)
from itou.common_apps.address.departments import REGIONS, department_from_postcode
from itou.common_apps.address.format import format_address
from itou.common_apps.address.models import AddressMixin
from itou.institutions.enums import InstitutionKind
from itou.institutions.models import Institution
from itou.prescribers.enums import PrescriberAuthorizationStatus, PrescriberOrganizationKind
from itou.prescribers.models import PrescriberOrganization
from itou.siaes.models import Siae
from itou.utils import constants as global_constants
from itou.utils.apis.exceptions import AddressLookupError
from itou.utils.validators import validate_birthdate, validate_nir, validate_pole_emploi_id

from .enums import IdentityProvider, Kind, Title


class ApprovalAlreadyExistsError(Exception):
    pass


class ItouUserManager(UserManager):
    def get_duplicated_pole_emploi_ids(self):
        """
        Returns an array of `pole_emploi_id` used more than once:

            ['6666666A', '7777777B', '8888888C', '...']

        Performs this kind of SQL (with extra filters):

            select pole_emploi_id, count(*)
            from users_user
            group by pole_emploi_id, birthdate
            having count(*) > 1

        Used in the `deduplicate_job_seekers` management command.
        Implemented as a manager method to make unit testing easier.
        """
        return (
            self.values("pole_emploi_id")
            .filter(is_job_seeker=True)
            # Skip empty `pole_emploi_id`.
            .exclude(pole_emploi_id="")
            # Skip 31 cases where `00000000` was used as the `pole_emploi_id`.
            .exclude(pole_emploi_id="00000000")
            # Group by.
            .values("pole_emploi_id")
            .annotate(num_of_duplications=Count("pole_emploi_id"))
            .filter(num_of_duplications__gt=1)
            .values_list("pole_emploi_id", flat=True)
        )

    def get_duplicates_by_pole_emploi_id(self, prefetch_related_lookups=None):
        """
        Find duplicates with the same `pole_emploi_id` and `birthdate`
        and returns a dict:

            {
                '5589555S': [<User: a>, <User: b>],
                '7744222A': [<User: x>, <User: y>, <User: z>],
                ...
            }

        Used in the `deduplicate_job_seekers` management command.
        Implemented as a manager method to make unit testing easier.
        """
        users = self.filter(pole_emploi_id__in=self.get_duplicated_pole_emploi_ids())
        if prefetch_related_lookups:
            users = users.prefetch_related(*prefetch_related_lookups)

        result = dict()
        for user in users:
            result.setdefault(user.pole_emploi_id, []).append(user)

        pe_id_to_remove = []

        for pe_id, duplicates in result.items():

            same_birthdate = all(user.birthdate == duplicates[0].birthdate for user in duplicates)

            if not same_birthdate:

                # Two users with the same `pole_emploi_id` but a different
                # `birthdate` are not guaranteed to be duplicates.
                if len(duplicates) == 2:
                    pe_id_to_remove.append(pe_id)
                    continue

                # Keep only users with the same most common birthdate.
                list_of_birthdates = [u.birthdate for u in duplicates]
                c = Counter(list_of_birthdates)
                most_common_birthdate = c.most_common(1)[0][0]

                duplicates_with_same_birthdate = [u for u in duplicates if u.birthdate == most_common_birthdate]

                if len(duplicates_with_same_birthdate) == 1:
                    # We stop if there is only one user left.
                    pe_id_to_remove.append(pe_id)
                else:
                    result[pe_id] = duplicates_with_same_birthdate

        for pe_id in pe_id_to_remove:
            del result[pe_id]

        return result


class User(AbstractUser, AddressMixin):
    """
    Custom user model.

    Default fields are listed here:
    https://github.com/django/django/blob/f3901b5899d746dc5b754115d94ce9a045b4db0a/django/contrib/auth/models.py#L321

    Auth is managed with django-allauth.

    To retrieve SIAEs this user belongs to:
        self.siae_set.all()
        self.siaemembership_set.all()

    To retrieve prescribers this user belongs to:
        self.prescriberorganization_set.all()
        self.prescribermembership_set.all()


    The User model has a "companion" model in the `external_data` app,
    for third-party APIs data import concerns (class `JobSeekerExternalData`).

    At the moment, only users (job seekers) connected via PE Connect
    have external data stored.

    More details in `itou.external_data.models` module
    """

    # Used for validation of birth country / place
    INSEE_CODE_FRANCE = Country._CODE_FRANCE  # pylint: disable=protected-access

    REASON_FORGOTTEN = "FORGOTTEN"
    REASON_NOT_REGISTERED = "NOT_REGISTERED"
    REASON_CHOICES = (
        (REASON_FORGOTTEN, "Identifiant Pôle emploi oublié"),
        (REASON_NOT_REGISTERED, "Non inscrit auprès de Pôle emploi"),
    )

    ERROR_EMAIL_ALREADY_EXISTS = "Cet e-mail existe déjà."
    ERROR_MUST_PROVIDE_BIRTH_PLACE = "Si le pays de naissance est la France, la commune de naissance est obligatoire"
    ERROR_BIRTH_COMMUNE_WITH_FOREIGN_COUNTRY = (
        "Il n'est pas possible de saisir une commune de naissance hors de France"
    )

    title = models.CharField(
        max_length=3,
        verbose_name="Civilité",
        blank=True,
        default="",
        choices=Title.choices,
    )

    birthdate = models.DateField(
        verbose_name="Date de naissance",
        null=True,
        blank=True,
        validators=[validate_birthdate],
    )
    birth_place = models.ForeignKey(
        "asp.Commune",
        verbose_name="Commune de naissance",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    birth_country = models.ForeignKey(
        "asp.Country",
        verbose_name="Pays de naissance",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    email = CIEmailField(
        "Adresse e-mail",
        blank=True,
        db_index=True,
        # Empty values are stored as NULL if both `null=True` and `unique=True` are set.
        # This avoids unique constraint violations when saving multiple objects with blank values.
        null=True,
        unique=True,
    )
    phone = models.CharField(verbose_name="Téléphone", max_length=20, blank=True)

    is_job_seeker = models.BooleanField(verbose_name="Demandeur d'emploi", default=False)
    is_prescriber = models.BooleanField(verbose_name="Prescripteur", default=False)
    is_siae_staff = models.BooleanField(verbose_name="Employeur (SIAE)", default=False)
    # Members of DDETS, DREETS or DGEFP institution have their own dashboard.
    is_labor_inspector = models.BooleanField(
        verbose_name="Inspecteur du travail (DDETS, DREETS, DGEFP)", default=False
    )

    # Don’t need to specify db_index because unique implies the creation of an index.
    nir = models.CharField(
        verbose_name="NIR", max_length=15, validators=[validate_nir], null=True, blank=True, unique=True
    )

    # The two following Pôle emploi fields are reserved for job seekers.
    # They are used in the process of delivering an approval.
    # They depend on each other: one or the other must be filled but not both.

    # Pôle emploi ID is not guaranteed to be unique.
    # At least, we haven't received any confirmation of its uniqueness.
    # It looks like it pre-dates the national merger and may be unique
    # by user and by region…
    pole_emploi_id = models.CharField(
        verbose_name="Identifiant Pôle emploi",
        help_text="7 chiffres suivis d'une 1 lettre ou d'un chiffre.",
        max_length=8,
        validators=[validate_pole_emploi_id, MinLengthValidator(8)],
        blank=True,
    )
    lack_of_pole_emploi_id_reason = models.CharField(
        verbose_name="Pas d'identifiant Pôle emploi ?",
        help_text=mark_safe(
            (
                "Indiquez la raison de l'absence d'identifiant Pôle emploi.<br>"
                "Renseigner l'identifiant Pôle emploi des candidats inscrits "
                "permet d'instruire instantanément votre demande.<br>"
                "Dans le cas contraire un délai de deux jours est nécessaire "
                "pour effectuer manuellement les vérifications d’usage."
            )
        ),
        max_length=30,
        choices=REASON_CHOICES,
        blank=True,
    )
    resume_link = models.URLField(max_length=500, verbose_name="Lien vers un CV", blank=True)

    identity_provider = models.CharField(
        max_length=20,
        verbose_name="Fournisseur d'identité (SSO)",
        default=IdentityProvider.DJANGO,
        choices=IdentityProvider.choices,
    )

    has_completed_welcoming_tour = models.BooleanField(verbose_name="Parcours de bienvenue effectué", default=False)

    created_by = models.ForeignKey(
        "self",
        verbose_name="Créé par",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    external_data_source_history = models.JSONField(
        verbose_name="Information sur la source des champs",
        blank=True,
        null=True,
        # TODO(alaurent) We could create a custom encode/decoder to store and read enums instead of strings.
        # It would also allow to have real datetimes when reading the field value.
        encoder=DjangoJSONEncoder,
    )

    objects = ItouUserManager()

    def __str__(self):
        return str(self.email)

    def clean(self):
        """
        Validation for FS
        Mainly coherence checks for birth country / place.
        Must be non blocking if these fields are not provided.
        """
        # If birth country is France, then birth place must be provided
        if self.birth_country and self.birth_country.code == self.INSEE_CODE_FRANCE and not self.birth_place:
            raise ValidationError(self.ERROR_MUST_PROVIDE_BIRTH_PLACE)

        # If birth country is not France, do not fill a birth place (no ref file)
        if self.birth_country and self.birth_country.code != self.INSEE_CODE_FRANCE and self.birth_place:
            raise ValidationError(self.ERROR_BIRTH_COMMUNE_WITH_FOREIGN_COUNTRY)

    def save(self, *args, **kwargs):
        # Update department from postal code (if possible).
        self.department = department_from_postcode(self.post_code)
        self.validate_unique()

        # TODO(rsebille): Replace by a UniqueConstraint once the data have been cleaned
        user_kinds = [self.is_job_seeker, self.is_prescriber, self.is_siae_staff, self.is_labor_inspector]
        if user_kinds.count(True) > 1:
            raise ValidationError("A User can not have more than one kind")

        super().save(*args, **kwargs)

    def can_edit_email(self, user):
        return user.is_handled_by_proxy and user.is_created_by(self) and not user.has_verified_email

    def can_edit_personal_information(self, user):
        if self.pk == user.pk:  # I am me
            return True

        if self.is_prescriber:
            if self.is_prescriber_with_authorized_org:
                return user.is_handled_by_proxy
            else:
                return user.is_handled_by_proxy and user.is_created_by(self)
        elif self.is_siae_staff:
            return user.is_handled_by_proxy

        return False

    def can_view_personal_information(self, user):
        if self.can_edit_personal_information(user):  # If we can edit them then we can view them
            return True

        if user.is_job_seeker:  # Restrict display of personal information to job seeker
            if self.is_prescriber:
                if self.is_prescriber_with_authorized_org:
                    return True
                else:
                    return user.is_handled_by_proxy and user.is_created_by(self)
            elif self.is_siae_staff:
                return True

        return False

    def can_add_nir(self, job_seeker):
        return (self.is_prescriber_with_authorized_org or self.is_siae_staff) and (job_seeker and not job_seeker.nir)

    def is_created_by(self, user):
        return bool(self.created_by_id and self.created_by_id == user.pk)

    @property
    def has_sso_provider(self):
        return self.identity_provider != IdentityProvider.DJANGO or self.is_peamu

    @cached_property
    def has_verified_email(self):
        return self.emailaddress_set.filter(email=self.email, verified=True).exists()

    @cached_property
    def latest_approval(self):
        if not self.is_job_seeker:
            return None
        approvals = Approval.objects.filter(user=self).order_by("-start_at")
        if not approvals:
            return None
        if approvals.valid().exists():
            return approvals.valid().first()
        approval = sorted(
            approvals, key=lambda x: (-time.mktime(x.end_at.timetuple()), time.mktime(x.start_at.timetuple()))
        )[0]
        if approval.waiting_period_has_elapsed:
            return None
        return approval

    @cached_property
    def latest_pe_approval(self):
        if not self.is_job_seeker:
            return None
        approval_numbers = Approval.objects.filter(user=self).values_list("number", flat=True)
        pe_approvals = PoleEmploiApproval.objects.find_for(self).exclude(number__in=approval_numbers)
        if not pe_approvals:
            return None
        pe_approval = sorted(
            pe_approvals, key=lambda x: (-time.mktime(x.end_at.timetuple()), time.mktime(x.start_at.timetuple()))
        )[0]
        if pe_approval.waiting_period_has_elapsed:
            return None
        return pe_approval

    @property
    def latest_common_approval(self):
        """
        Rationale:
        - if there is a latest PASS IAE that is valid, it is returned.
        - if there is no PASS IAE, we return the longest PE Approval whatever its state.
        - if there is no PASS nor PE Approval, or the waiting period for those is over, return nothing.
        - if the latest PASS IAE is invalid:
          * but still in waiting period:
            > return a valid PE Approval if there is one
            > else, return the PASS in waiting period.
          * if outdated, we consider there's no PASS. Return the latest PE approval, if any.
        """
        if (
            self.latest_approval
            and self.latest_approval.is_in_waiting_period
            and self.latest_pe_approval
            and self.latest_pe_approval.is_valid
        ):
            return self.latest_pe_approval

        return self.latest_approval or self.latest_pe_approval

    @property
    def has_valid_common_approval(self):
        return (self.latest_approval and self.latest_approval.is_valid()) or (
            self.latest_pe_approval and self.latest_pe_approval.is_valid()
        )

    @property
    def has_common_approval_in_waiting_period(self):
        return (self.latest_approval and not self.latest_approval.is_valid()) or (
            self.latest_pe_approval and not self.latest_pe_approval.is_valid()
        )

    @property
    def has_no_common_approval(self):
        return not self.latest_approval and not self.latest_pe_approval

    def approval_can_be_renewed_by(self, siae, sender_prescriber_organization):
        """
        An approval in waiting period can only be bypassed if the prescriber is authorized
        or if the structure is not a SIAE.
        """
        is_sent_by_authorized_prescriber = (
            sender_prescriber_organization is not None and sender_prescriber_organization.is_authorized
        )

        # Only diagnoses made by authorized prescribers are taken into account.
        has_valid_diagnosis = self.has_valid_diagnosis()
        return (
            self.has_common_approval_in_waiting_period
            and siae.is_subject_to_eligibility_rules
            and not (is_sent_by_authorized_prescriber or has_valid_diagnosis)
        )

    def get_or_create_approval(self):
        """
        Returns an existing valid Approval or create a new entry from
        a pre-existing valid PoleEmploiApproval by copying its data.
        """
        # FIXME(vperron): move this method and all the other approval-related code to JobSeekerProfile.
        if not self.has_valid_common_approval:
            raise RuntimeError("Invalid approval.")
        if self.latest_approval and self.latest_approval.is_valid():
            return self.latest_approval
        pe_approval = self.latest_pe_approval
        if Approval.objects.filter(number=pe_approval.number).exists():
            raise ApprovalAlreadyExistsError()
        approval_from_pe = Approval(
            start_at=pe_approval.start_at,
            end_at=pe_approval.end_at,
            user=self,
            number=pe_approval.number,
        )
        approval_from_pe.save()
        return approval_from_pe

    @property
    def is_handled_by_proxy(self):
        if self.is_job_seeker and self.created_by and not self.last_login:
            return True
        return False

    @cached_property
    def is_peamu(self):
        social_accounts = self.socialaccount_set.all()
        # We have to do all this in python to benefit from prefetch_related.
        return len([sa for sa in social_accounts if sa.provider == "peamu"]) >= 1

    @cached_property
    def peamu_id_token(self):
        if not self.is_peamu:
            return None
        return self.socialaccount_set.filter(provider="peamu").get().extra_data["id_token"]

    @cached_property
    def is_prescriber_with_org(self):
        return self.is_prescriber and self.prescribermembership_set.filter(is_active=True).exists()

    @cached_property
    def is_prescriber_with_authorized_org(self):
        return (
            self.is_prescriber
            and self.prescriberorganization_set.filter(is_authorized=True, members__is_active=True).exists()
        )

    def is_prescriber_of_authorized_organization(self, organization_id):
        return self.prescriberorganization_set.filter(
            pk=organization_id,
            is_authorized=True,
            prescribermembership__is_active=True,
        ).exists()

    @property
    def has_external_data(self):
        return self.is_job_seeker and hasattr(self, "jobseekerexternaldata")

    @property
    def has_jobseeker_profile(self):
        return self.is_job_seeker and hasattr(self, "jobseeker_profile")

    def has_valid_diagnosis(self, for_siae=None):
        return self.eligibility_diagnoses.has_considered_valid(job_seeker=self, for_siae=for_siae)

    def joined_recently(self):
        time_since_date_joined = timezone.now() - self.date_joined
        return time_since_date_joined.days < 7

    @property
    def has_pole_emploi_email(self):
        return self.email and self.email.endswith(global_constants.POLE_EMPLOI_EMAIL_SUFFIX)

    @cached_property
    def is_siae_staff_with_siae(self):
        """
        Useful to identify users deactivated as member of a SIAE
        and without any membership left.
        They are in a "dangling" status: still active (membership-wise) but unable to login
        because not member of any SIAE.
        """
        return self.is_siae_staff and self.siaemembership_set.filter(is_active=True).exists()

    def active_or_in_grace_period_siae_memberships(self):
        """
        Return the siae memberships accessible to the employer, which means either active
        or in grace period, with a minimum of database queries.
        """
        # Unfortunately we need two queries here, no solution was found to combine both
        # `siae_set.active_or_in_grace_period()` and `siaemembership_set.active()` in a single query.
        user_siae_set_pks = self.siae_set.active_or_in_grace_period().values_list("pk", flat=True)
        memberships = (
            self.siaemembership_set.active().select_related("siae").filter(siae__pk__in=user_siae_set_pks).all()
        )
        return memberships

    def can_create_siae_antenna(self, parent_siae):
        """
        Only admin employers can create an antenna for their SIAE.

        For SIAE structures (AI, ACI...) the convention has to be present to link the parent SIAE and its antenna.
        In some edge cases (e.g. SIAE created by staff and not yet officialized) the convention is absent,
        in that case we must absolutely not allow any antenna to be created.

        For non SIAE structures (GEIQ, EA...) the convention logic is not implemented thus no convention ever exists.
        Antennas cannot be freely created by the user as the EA system authorities do not allow any non official SIRET
        to be used.

        Finally, for OPCS it has been decided for now to disallow it; those structures are strongly attached to
        a given territory and thus would not need to join others.
        """
        return (
            self.is_siae_staff
            and parent_siae.is_active
            and parent_siae.has_admin(self)
            and parent_siae.should_have_convention
            and parent_siae.convention is not None
        )

    def can_view_stats_dashboard_widget(self, current_org):
        """
        Whether a stats section should be displayed on the user's dashboard.

        It should be displayed if one or more stats sections are available for the user.
        """
        return (
            self.can_view_stats_siae_etp(current_org=current_org)
            or self.can_view_stats_siae_hiring(current_org=current_org)
            or self.can_view_stats_cd(current_org=current_org)
            or self.can_view_stats_pe(current_org=current_org)
            or self.can_view_stats_ddets(current_org=current_org)
            or self.can_view_stats_dreets(current_org=current_org)
            or self.can_view_stats_dgefp(current_org=current_org)
        )

    def _can_view_stats_siae(self, current_org):
        """
        Users of a SIAE can view their SIAE data and only theirs.
        This internal method is not supposed to be called directly and is only used to share code between
        actual callable methods `can_view_stats_siae_*`.
        """
        return (
            self.is_siae_staff
            and isinstance(current_org, Siae)
            and current_org.has_member(self)
            # Metabase expects a filter on the SIAE ASP id (technically `siae.convention.asp_id`) which is why
            # we require a convention object to exist here.
            # Some SIAE don't have a convention (SIAE created by support, GEIQ, EA...).
            and current_org.convention is not None
        )

    def can_view_stats_siae_etp(self, current_org):
        return self._can_view_stats_siae(current_org) and self.pk in settings.STATS_SIAE_USER_PK_WHITELIST

    def can_view_stats_siae_hiring(self, current_org):
        return self._can_view_stats_siae(current_org)

    def can_view_stats_cd(self, current_org):
        """
        Users of a real CD can view the confidential CD stats for their department only.

        CD as in "Conseil Départemental".

        Unfortunately the `PrescriberOrganizationKind.DEPT` kind contains not only the real CD but also some random
        organizations authorized by some CD.
        When such a random non-CD org is registered, it is not authorized yet, thus will be filtered out correctly.
        Later, our staff will authorize the random non-CD org, flag it as `is_brsa` and change its kind to `OTHER`.
        Sometimes our staff makes human errors and forgets to flag it as `is_brsa` or to change its kind.
        Hence we take extra precautions to filter out these edge cases to ensure we never ever show sensitive stats to
        a non-CD organization of the `DEPT` kind.
        """
        return (
            self.is_prescriber
            and isinstance(current_org, PrescriberOrganization)
            and current_org.kind == PrescriberOrganizationKind.DEPT
            and current_org.is_authorized
            and current_org.authorization_status == PrescriberAuthorizationStatus.VALIDATED
            and not current_org.is_brsa
        )

    def get_stats_cd_department(self, current_org):
        """
        Get department that the user has the permission to view for the CD stats page.
        CD as in "Conseil Départemental".
        """
        if not self.can_view_stats_cd(current_org=current_org):
            raise PermissionDenied
        return current_org.department

    def can_view_stats_pe(self, current_org):
        return (
            self.is_prescriber
            and isinstance(current_org, PrescriberOrganization)
            and current_org.kind == PrescriberOrganizationKind.PE
            and current_org.is_authorized
            and current_org.authorization_status == PrescriberAuthorizationStatus.VALIDATED
        )

    def get_stats_pe_departments(self, current_org):
        if not self.can_view_stats_pe(current_org=current_org):
            raise PermissionDenied
        if current_org.is_drpe:
            return REGIONS[current_org.region]
        return [current_org.department]

    def can_view_stats_ddets(self, current_org):
        """
        Users of a DDETS can view the confidential DDETS stats of their department only.
        DDETS as in "Directions départementales de l’emploi, du travail et des solidarités".
        """
        return (
            self.is_labor_inspector
            and isinstance(current_org, Institution)
            and current_org.kind == InstitutionKind.DDETS
        )

    def get_stats_ddets_department(self, current_org):
        """
        Get department that the user has the permission to view for the DDETS stats page.
        DDETS as in "Directions départementales de l’emploi, du travail et des solidarités".
        """
        if not self.can_view_stats_ddets(current_org=current_org):
            raise PermissionDenied
        return current_org.department

    def can_view_stats_dreets(self, current_org):
        """
        Users of a DREETS can view the confidential DREETS stats of their region only.
        DREETS as in "Directions régionales de l’économie, de l’emploi, du travail et des solidarités".
        """
        return (
            self.is_labor_inspector
            and isinstance(current_org, Institution)
            and current_org.kind == InstitutionKind.DREETS
        )

    def get_stats_dreets_region(self, current_org):
        """
        Get region that the user has the permission to view for the DREETS stats page.
        DREETS as in "Directions régionales de l’économie, de l’emploi, du travail et des solidarités".
        """
        if not self.can_view_stats_dreets(current_org=current_org):
            raise PermissionDenied
        return current_org.region

    def can_view_stats_dgefp(self, current_org):
        """
        Users of the DGEFP institution can view the confidential DGEFP stats for all regions and departments.
        """
        return (
            self.is_labor_inspector
            and isinstance(current_org, Institution)
            and current_org.kind == InstitutionKind.DGEFP
        )

    def update_external_data_source_history_field(self, provider, field, value) -> bool:
        """
        Attempts to update the history json data for a field inside
        `external_data_source_history`, and returns a boolean if the user data was modified,
        so that the database save() can be performed later on

        We store a history of the various data sources for the user information
        inside `external_data_source_history`. It can look like:
        Since we only append data, they should all be chronologically sorted
        [
            {"field_name": "first_name", "source": "FRANCE_CONNECT", "created_at": "…", "value": "Jean-Michel"},
            {"field_name": "birth_date", "source": "PE_CONNECT", "created_at": "…", "value": "…"},
            …

        """
        now = timezone.now()
        has_performed_update = False

        if not self.external_data_source_history:
            self.external_data_source_history = []

        try:
            field_history = list(filter(lambda d: d["field_name"] == field, self.external_data_source_history))
            current_value = field_history[-1]["value"]
        except IndexError:
            current_value = None
        if current_value != value:
            self.external_data_source_history.append(
                {
                    "field_name": field,
                    "source": provider.value,
                    "created_at": now,
                    "value": value,
                }
            )
            has_performed_update = True
        return has_performed_update

    @cached_property
    def last_accepted_job_application(self):
        if not self.is_job_seeker:
            return None

        # Some candidates may not have accepted job applications
        # Assuming its the case can lead to issues downstream
        return self.job_applications.accepted().with_accepted_at().order_by("-accepted_at", "-hiring_start_at").first()

    @cached_property
    def jobseeker_hash_id(self):
        """
        Obfuscation of internal user id provided to ASP
        """
        if not self.is_job_seeker:
            return None

        salt = salted_hmac(key_salt="job_seeker.id", value=self.id, secret=settings.SECRET_KEY)
        return salt.hexdigest()[:30]

    def last_hire_was_made_by_siae(self, siae):
        if not self.is_job_seeker:
            return False
        return self.last_accepted_job_application and self.last_accepted_job_application.to_siae == siae

    @classmethod
    def create_job_seeker_by_proxy(cls, proxy_user, **fields):
        """
        Used when a "prescriber" user creates another user of kind "job seeker".

        Minimum required keys in `fields` are:
            {
                "email": "foo@foo.com",
                "first_name": "Foo",
                "last_name": "Foo",
            }
        """
        username = cls.generate_unique_username()
        fields["is_job_seeker"] = True
        fields["created_by"] = proxy_user
        user = cls.objects.create_user(
            username,
            email=fields.pop("email"),
            password=cls.objects.make_random_password(),
            **fields,
        )
        return user

    @classmethod
    def create_job_seeker_from_pole_emploi_approval(cls, proxy_user, email, pole_emploi_approval):
        """Uses the data from a PoleEmploiApproval to create a job seeker"""
        job_seeker_data = {
            "email": email,
            "first_name": pole_emploi_approval.first_name,
            "last_name": pole_emploi_approval.last_name,
            "birthdate": pole_emploi_approval.birthdate,
            "pole_emploi_id": pole_emploi_approval.pole_emploi_id,
        }
        return cls.create_job_seeker_by_proxy(proxy_user, **job_seeker_data)

    @classmethod
    def generate_unique_username(cls):
        """
        `AbstractUser.username` is a required field. It is not used in Itou but
         it is still required in places like `User.objects.create_user()` etc.

        We used to rely on `allauth.utils.generate_unique_username` to populate
        it with a random username but it often failed causing errors in Sentry.

        We now use a UUID4.
        """
        return uuid.uuid4().hex

    @classmethod
    def nir_already_exists(cls, nir, exclude_pk=None):
        queryset = cls.objects.filter(nir=nir)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        return queryset.exists()

    @classmethod
    def email_already_exists(cls, email, exclude_pk=None):
        """
        RFC 5321 Part 2.4 states that only the domain portion of an email
        is case-insensitive. Consider toto@toto.com and TOTO@toto.com as
        the same email.
        """
        queryset = cls.objects.filter(email__iexact=email)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        return queryset.exists()

    @staticmethod
    def clean_pole_emploi_fields(cleaned_data):
        """
        Validate Pôle emploi fields that depend on each other.
        Only for users with the `is_job_seeker` flag set to True.
        It must be used in forms and modelforms that manipulate job seekers.
        """
        pole_emploi_id = cleaned_data["pole_emploi_id"]
        lack_of_pole_emploi_id_reason = cleaned_data["lack_of_pole_emploi_id_reason"]
        # One or the other must be filled.
        if not pole_emploi_id and not lack_of_pole_emploi_id_reason:
            raise ValidationError("Renseignez soit un identifiant Pôle emploi, soit la raison de son absence.")
        # If both are filled, `pole_emploi_id` takes precedence (Trello #1724).
        if pole_emploi_id and lack_of_pole_emploi_id_reason:
            # Take advantage of the fact that `cleaned_data` is passed by sharing:
            # the object is shared between the caller and the called routine.
            cleaned_data["lack_of_pole_emploi_id_reason"] = ""

    # TODO(alaurent) Maybe replace with a field in db
    @property
    def kind(self):
        if self.is_job_seeker:
            return Kind.JOB_SEEKER
        elif self.is_prescriber:
            return Kind.PRESCREIBER
        elif self.is_siae_staff:
            return Kind.SIAE_STAFF
        elif self.is_labor_inspector:
            return Kind.LABOR_INSPECTOR
        else:
            raise ValueError("User has no valid kind")

    def get_kind_display(self):
        return self.kind.label


def get_allauth_account_user_display(user):
    return user.email


class JobSeekerProfile(models.Model):
    """
    Specific information about the job seeker

    Instead of augmenting the 'User' model, additional data is collected in a "profile" object.

    This user profile has 2 main parts:

    1 - Job seeker "administrative" situation

    These fields are part of the mandatory fields for EmployeeRecord processing:
    - education level
    - various social allowances flags and durations

    2 - Job seeker address in HEXA address format:

    The SNA (Service National de l'Adresse) has several certification / validation
    norms to verify french addresses:
    - Hexacle: house number level
    - Hexaposte: zip code level
    - Hexavia: street level
    + many others...

    For the employee record domain, this means that the job seeker address has to be
    formatted in a very specific way to be accepted as valid by ASP backend.

    These conversions and formatting processes are almost automatic,
    but absolutely not 100% error-proof.

    Formatted addresses are stored in this model, avoiding multiple calls to the
    reverse geocoding API at processing time.

    This kind of address are at the moment only used by the employee_record app,
    but their usage could be extended to other domains should the need arise.

    Note that despite the name, addresses of this model are not fully compliant
    with Hexa norms (but compliant enough to be accepted by ASP backend).
    """

    ERROR_NOT_RESOURCELESS_IF_OETH_OR_RQTH = "La personne n'est pas considérée comme sans ressources si OETH ou RQTH"
    ERROR_EMPLOYEE_WITH_UNEMPLOYMENT_PERIOD = (
        "La personne ne peut avoir de période sans emploi si actuellement employée"
    )
    ERROR_UNEMPLOYED_BUT_RQTH_OR_OETH = (
        "La personne ne peut être considérée comme sans emploi si employée OETH ou RQTH"
    )

    ERROR_HEXA_LANE_TYPE = "Le type de voie est obligatoire"
    ERROR_HEXA_LANE_NAME = "Le nom de voie est obligatoire"
    ERROR_HEXA_POST_CODE = "Le code postal est obligatoire"
    ERROR_HEXA_COMMUNE = "La commune INSEE est obligatoire"
    ERROR_HEXA_LOOKUP_COMMUNE = "Impossible de trouver la commune à partir du code INSEE"

    ERROR_JOBSEEKER_TITLE = "La civilité du demandeur d'emploi est obligatoire"
    ERROR_JOBSEEKER_EDUCATION_LEVEL = "Le niveau de formation du demandeur d'emploi est obligatoire"
    ERROR_JOBSEEKER_PE_FIELDS = "L'identifiant et la durée d'inscription à Pôle emploi vont de pair"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name="Demandeur d'emploi",
        related_name="jobseeker_profile",
    )

    education_level = models.CharField(
        max_length=2,
        verbose_name="Niveau de formation (ASP)",
        blank=True,
        choices=EducationLevel.choices,
    )

    resourceless = models.BooleanField(verbose_name="Sans ressource", default=False)

    rqth_employee = models.BooleanField(verbose_name="Titulaire de la RQTH", default=False)
    oeth_employee = models.BooleanField(verbose_name="Bénéficiaire de la loi handicap (OETH)", default=False)

    pole_emploi_since = models.CharField(
        max_length=2,
        verbose_name="Inscrit à Pôle emploi depuis",
        blank=True,
        choices=AllocationDuration.choices,
    )

    unemployed_since = models.CharField(
        max_length=2,
        verbose_name="Sans emploi depuis",
        blank=True,
        choices=AllocationDuration.choices,
    )

    previous_employer_kind = models.CharField(
        max_length=2,
        verbose_name="Précédent employeur",
        blank=True,
        choices=EmployerType.choices,
    )

    # Despite the name of this field in the ASP model (salarieBenefRSA),
    # this field is not a boolean, but has 3 different options
    # See asp.models.RSAAllocation for details
    has_rsa_allocation = models.CharField(
        max_length=6,
        verbose_name="Salarié bénéficiaire du RSA",
        choices=RSAAllocation.choices,
        default=RSAAllocation.NO,
    )

    rsa_allocation_since = models.CharField(
        max_length=2,
        verbose_name="Allocataire du RSA depuis",
        blank=True,
        choices=AllocationDuration.choices,
    )

    ass_allocation_since = models.CharField(
        max_length=2,
        verbose_name="Allocataire de l'ASS depuis",
        blank=True,
        choices=AllocationDuration.choices,
    )

    aah_allocation_since = models.CharField(
        max_length=2,
        verbose_name="Allocataire de l'AAH depuis",
        blank=True,
        choices=AllocationDuration.choices,
    )

    ata_allocation_since = models.CharField(
        max_length=2,
        verbose_name="Allocataire de l'ATA depuis",
        blank=True,
        choices=AllocationDuration.choices,
    )

    # Jobseeker address in Hexa format

    hexa_lane_number = models.CharField(max_length=10, verbose_name="Numéro de la voie", blank=True, default="")
    hexa_std_extension = models.CharField(
        max_length=1,
        verbose_name="Extension de voie",
        blank=True,
        default="",
        choices=LaneExtension.choices,
    )
    # No need to set blank=True, this field is never used with a text choice
    hexa_non_std_extension = models.CharField(
        max_length=10,
        verbose_name="Extension de voie (non-repertoriée)",
        blank=True,
        default="",
    )
    hexa_lane_type = models.CharField(
        max_length=4,
        verbose_name="Type de voie",
        blank=True,
        choices=LaneType.choices,
    )
    hexa_lane_name = models.CharField(max_length=120, verbose_name="Nom de la voie", blank=True)
    hexa_additional_address = models.CharField(max_length=32, verbose_name="Complément d'adresse", blank=True)
    hexa_post_code = models.CharField(max_length=6, verbose_name="Code postal", blank=True)
    hexa_commune = models.ForeignKey(
        Commune,
        verbose_name="Commune (ref. ASP)",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "Profil demandeur d'emploi"
        verbose_name_plural = "Profils demandeur d'emploi"

    def __str__(self):
        return str(self.user)

    def _clean_job_seeker_details(self):
        # Title is not mandatory for User, but it is for ASP
        if not self.user.title:
            raise ValidationError(self.ERROR_JOBSEEKER_TITLE)

        # Birth place an country are checked in User.clean()
        self.user.clean()

        if not self.education_level:
            raise ValidationError(self.ERROR_JOBSEEKER_EDUCATION_LEVEL)

    def _clean_job_seeker_situation(self):
        if self.previous_employer_kind and self.unemployed_since:
            raise ValidationError(self.ERROR_EMPLOYEE_WITH_UNEMPLOYMENT_PERIOD)

        # NOTE(fvergez): Seems to be a major source of 500 errors
        # Not really needed here, checks are done at form level
        # if bool(self.pole_emploi_since) != bool(self.user.pole_emploi_id):
        #   raise ValidationError(self.ERROR_JOBSEEKER_PE_FIELDS)

        # Social allowances fields are not mandatory
        # However we may add some coherence check later on

    def _clean_job_seeker_hexa_address(self):
        # Check if any fields of the hexa address is filled
        if not any(
            [
                self.hexa_lane_number,
                self.hexa_std_extension,
                self.hexa_non_std_extension,
                self.hexa_lane_type,
                self.hexa_lane_name,
                self.hexa_additional_address,
                self.hexa_post_code,
                self.hexa_commune,
            ]
        ):
            # Nothing to check
            return

        # if any 'hexa' field is given, then check all mandatory fields
        # (all or nothing)
        if not self.hexa_lane_type:
            raise ValidationError(self.ERROR_HEXA_LANE_TYPE)

        if not self.hexa_lane_name:
            raise ValidationError(self.ERROR_HEXA_LANE_NAME)

        if not self.hexa_post_code:
            raise ValidationError(self.ERROR_HEXA_POST_CODE)

        if not self.hexa_commune:
            raise ValidationError(self.ERROR_HEXA_COMMUNE)

    #  This used to be the `clean` method for the global model validation
    #  when using forms.
    #  However, building forms with ModelForm objects and a *subset* of
    #  the model fields is really troublesome when using a global validator.
    #  (forms are calling model.clean() at every validation).
    #  This method is triggered manually.
    def clean_model(self):
        """
        Global model validation. Used to be the `clean` method.
        """
        # see partial validation methods above
        self._clean_job_seeker_details()
        self._clean_job_seeker_situation()
        self._clean_job_seeker_hexa_address()

    def update_hexa_address(self):
        """
        This method tries to fill the HEXA address fields based the current address of the job seeker (`User` model).

        Conversion from standard itou address to HEXA is making sync geo API calls.

        Calling this method should be done in a (multiple) try/except block.

        Raises `UnknownCommuneError` or `AddressLookupError` instead of `ValidationError`:
            - not a validation part
            - easier to pinpoint issues on frontend side (and correctly notify user)

        Using this method can block user from completing an employee record creation.

        If anything goes wrong here, it must "fail fast" and notify the user in the most accurate way possible.
        """
        result, error = format_address(self.user)

        if error:
            raise ValidationError(error)

        # Fill matching fields
        self.hexa_lane_type = result.get("lane_type")
        self.hexa_lane_number = result.get("number")
        self.hexa_std_extension = result.get("std_extension", "")
        self.hexa_non_std_extension = result.get("non_std_extension")
        self.hexa_lane_name = result.get("lane")
        self.hexa_post_code = result.get("post_code")
        self.hexa_additional_address = result.get("additional_address")

        # Special field: Commune object contains both city name and INSEE code
        insee_code = result.get("insee_code")

        # This may raise an asp.exceptions.UnknownCommuneError : let it crash if needed
        try:
            self.hexa_commune = Commune.by_insee_code(insee_code)
        except AddressLookupError:
            raise ValidationError(f"Impossible de trouver la commune correspondate: code INSEE {insee_code}")

        self.save()

        return self

    def clear_hexa_address(self):
        """
        Wipe hexa address fields and updates the profile in DB.

        Use with caution:
            clearing HEXA addresses of a job seeker can block employee record update notifications transfer.
        """
        self.hexa_lane_type = ""
        self.hexa_lane_number = ""
        self.hexa_std_extension = ""
        self.hexa_non_std_extension = ""
        self.hexa_lane_name = ""
        self.hexa_additional_address = ""
        self.hexa_post_code = ""
        self.hexa_commune = None

        self.save()

    @property
    def is_employed(self):
        # `previous_employer_kind` field is not needed for ASP processing
        return not self.unemployed_since

    @property
    def has_ass_allocation(self):
        return bool(self.ass_allocation_since)

    @property
    def has_aah_allocation(self):
        return bool(self.aah_allocation_since)

    @property
    def has_ata_allocation(self):
        return bool(self.ata_allocation_since)

    @property
    def has_social_allowance(self):
        return bool(
            self.has_rsa_allocation != RSAAllocation.NO
            or self.has_ass_allocation
            or self.has_aah_allocation
            or self.has_ata_allocation
        )

    @property
    def hexa_address_filled(self):
        return bool(self.hexa_lane_name and self.hexa_lane_type and self.hexa_post_code and self.hexa_commune)

    @property
    def hexa_address_display(self):
        if self.hexa_address_filled:
            result = ""
            if self.hexa_lane_number:
                result += f"{self.hexa_lane_number} "
            if self.hexa_std_extension:
                result += f"{self.hexa_std_extension} "
            elif self.hexa_non_std_extension:
                result += f"{self.hexa_non_std_extension} "
            if self.hexa_lane_type:
                result += f"{self.get_hexa_lane_type_display()} "

            result += f"{self.hexa_lane_name} - {self.hexa_post_code} {self.hexa_commune.name}"
            return result

        return "Adresse HEXA incomplète"
