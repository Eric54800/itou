"""
Embedding Metabase dashboards:
Metabase dashboards can be included securely in the app via a signed URL
See an embedding sample at:
https://github.com/metabase/embedding-reference-apps/blob/master/django/embedded_analytics/user_stats/views.py

Some dashboards have sensitive information and the user should not be able to view data of other departments
than their own, other regions than their own, or other SIAE than their own.

For those dashboards, some filters such as department and/or region and/or SIAE id should be locked on metabase side.
Go to https://stats.inclusion.beta.gouv.fr/dashboard/XXX then "Partage"
then "Partager et intégrer" then "Intégrer ce dashboard dans une application" then inside "Paramètres" on the right,
make sure that the correct filters are "Verrouillé".

"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt

from itou.analytics.models import StatsDashboardVisit
from itou.common_apps.address.departments import (
    DEPARTMENT_TO_REGION,
    DEPARTMENTS,
    REGIONS,
    format_region_and_department_for_matomo,
    format_region_for_matomo,
)
from itou.utils import constants as global_constants
from itou.utils.apis.metabase import (
    ASP_SIAE_FILTER_KEY,
    C1_SIAE_FILTER_KEY,
    DEPARTMENT_FILTER_KEY,
    IAE_NETWORK_FILTER_KEY,
    METABASE_DASHBOARDS,
    REGION_FILTER_KEY,
    get_view_name,
    metabase_embedded_url,
)
from itou.utils.perms.institution import get_current_institution_or_404
from itou.utils.perms.prescriber import get_current_org_or_404
from itou.utils.perms.siae import get_current_siae_or_404


def get_stats_siae_etp_current_org(request):
    current_org = get_current_siae_or_404(request)
    if not request.user.can_view_stats_siae_etp(current_org=current_org):
        raise PermissionDenied
    return current_org


def get_stats_siae_current_org(request):
    current_org = get_current_siae_or_404(request)
    if not request.user.can_view_stats_siae(current_org=current_org):
        raise PermissionDenied
    return current_org


def get_stats_ddets_department(request):
    current_org = get_current_institution_or_404(request)
    if not request.user.can_view_stats_ddets(current_org=current_org):
        raise PermissionDenied
    department = request.user.get_stats_ddets_department(current_org=current_org)
    return department


def get_stats_dreets_region(request):
    current_org = get_current_institution_or_404(request)
    if not request.user.can_view_stats_dreets(current_org=current_org):
        raise PermissionDenied
    region = request.user.get_stats_dreets_region(current_org=current_org)
    return region


def ensure_stats_dgefp_permission(request):
    current_org = get_current_institution_or_404(request)
    if not request.user.can_view_stats_dgefp(current_org=current_org):
        raise PermissionDenied


def get_params_for_departement(department):
    return {
        DEPARTMENT_FILTER_KEY: DEPARTMENTS[department],
        REGION_FILTER_KEY: DEPARTMENT_TO_REGION[department],
    }


def get_params_for_region(region):
    departments = [DEPARTMENTS[dpt] for dpt in REGIONS[region]]
    params = {
        DEPARTMENT_FILTER_KEY: departments,
        REGION_FILTER_KEY: region,
    }
    return params


def get_params_for_whole_country():
    return {
        DEPARTMENT_FILTER_KEY: list(DEPARTMENTS.values()),
        REGION_FILTER_KEY: list(REGIONS.keys()),
    }


def render_stats(request, context, params=None, template_name="stats/stats.html"):
    if params is None:
        params = {}
    view_name = get_view_name(request)
    metabase_dashboard = METABASE_DASHBOARDS.get(view_name)
    tally_popup_form_id = None
    tally_embed_form_id = None
    if settings.TALLY_URL and metabase_dashboard:
        tally_popup_form_id = metabase_dashboard.get("tally_popup_form_id")
        tally_embed_form_id = metabase_dashboard.get("tally_embed_form_id")

    base_context = {
        "iframeurl": metabase_embedded_url(request=request, params=params),
        "stats_base_url": settings.METABASE_SITE_URL,
        "tally_popup_form_id": tally_popup_form_id,
        "tally_embed_form_id": tally_embed_form_id,
    }

    # Key value pairs in context override preexisting pairs in base_context.
    base_context.update(context)

    matomo_custom_url = request.resolver_match.route  # e.g. "stats/pe/delay/main"
    if suffix := base_context.pop("matomo_custom_url_suffix", None):
        # E.g. `/stats/ddets/iae/Provence-Alpes-Cote-d-Azur/04---Alpes-de-Haute-Provence`
        matomo_custom_url += f"/{suffix}"
    base_context["matomo_custom_url"] = matomo_custom_url

    if request.user.is_authenticated and metabase_dashboard:
        siae_pk = request.session.get(global_constants.ITOU_SESSION_CURRENT_SIAE_KEY)
        prescriber_org_pk = request.session.get(global_constants.ITOU_SESSION_CURRENT_PRESCRIBER_ORG_KEY)
        institution_pk = request.session.get(global_constants.ITOU_SESSION_CURRENT_INSTITUTION_KEY)
        user_kind = request.user.kind
        department = base_context.get("department")
        region = DEPARTMENT_TO_REGION[department] if department else base_context.get("region")
        dashboard_id = metabase_dashboard.get("dashboard_id")
        StatsDashboardVisit.objects.create(
            dashboard_id=dashboard_id,
            dashboard_name=view_name,
            department=department,
            region=region,
            current_siae_id=siae_pk,
            current_prescriber_organization_id=prescriber_org_pk,
            current_institution_id=institution_pk,
            user_kind=user_kind,
            user_id=request.user.pk,
        )

    return render(request, template_name, base_context)


def stats_public(request):
    """
    Public basic stats (signed and embedded version)
    """
    context = {
        "page_title": "Statistiques",
        "is_stats_public": True,
    }
    return render_stats(request=request, context=context)


@xframe_options_exempt
def stats_pilotage(request, dashboard_id):
    """
    All these dashboard are publicly available on `PILOTAGE_SITE_URL`.
    We do it because we want to allow users to download chart data which
    is only possible via embedded dashboards and not via regular public dashboards.
    """
    if dashboard_id not in settings.PILOTAGE_DASHBOARDS_WHITELIST:
        raise PermissionDenied

    context = {
        "iframeurl": metabase_embedded_url(dashboard_id=dashboard_id, with_title=True),
    }
    return render_stats(request=request, context=context, template_name="stats/stats_pilotage.html")


@login_required
def stats_siae_etp(request):
    """
    SIAE stats shown to their own members.
    They can only view data for their own SIAE.
    These stats are about ETP data from the ASP.
    """
    current_org = get_stats_siae_etp_current_org(request)
    context = {
        "page_title": "Données de ma structure (extranet ASP)",
        "department": current_org.department,
        "matomo_custom_url_suffix": format_region_and_department_for_matomo(current_org.department),
    }
    return render_stats(
        request=request,
        context=context,
        params={ASP_SIAE_FILTER_KEY: current_org.convention.asp_id},
    )


def render_stats_siae(request, page_title):
    """
    SIAE stats shown only to their own members.
    Employers can see stats for all their SIAEs at once, not just the one currently being worked on.
    These stats are built directly from C1 data.
    """
    current_org = get_stats_siae_current_org(request)
    context = {
        "page_title": page_title,
        "department": current_org.department,
        "matomo_custom_url_suffix": format_region_and_department_for_matomo(current_org.department),
    }
    return render_stats(
        request=request,
        context=context,
        params={
            C1_SIAE_FILTER_KEY: [
                str(membership.siae_id) for membership in request.user.active_or_in_grace_period_siae_memberships()
            ]
        },
    )


@login_required
def stats_siae_hiring(request):
    return render_stats_siae(request=request, page_title="Données de candidatures de mes structures")


@login_required
def stats_siae_auto_prescription(request):
    return render_stats_siae(request=request, page_title="Focus auto-prescription")


@login_required
def stats_siae_follow_siae_evaluation(request):
    return render_stats_siae(request=request, page_title="Suivi du contrôle a posteriori")


@login_required
def stats_cd(request):
    """
    CD ("Conseil Départemental") stats shown to relevant members.
    They can only view data for their own departement.
    """
    current_org = get_current_org_or_404(request)
    if not request.user.can_view_stats_cd(current_org=current_org):
        raise PermissionDenied
    department = request.user.get_stats_cd_department(current_org=current_org)
    params = get_params_for_departement(department)
    context = {
        "page_title": f"Données de mon département : {DEPARTMENTS[department]}",
        "department": department,
        "matomo_custom_url_suffix": format_region_and_department_for_matomo(department),
    }
    return render_stats(request=request, context=context, params=params)


def render_stats_pe(request, page_title):
    """
    PE ("Pôle emploi") stats shown to relevant members.
    They can view data for their whole departement, not only their agency.
    They cannot view data for other departments than their own.

    `*_main` views are linked directly from the C1 dashboard.
    `*_raw` views are not directly visible on the C1 dashboard but are linked from within their `*_main` counterpart.
    """
    current_org = get_current_org_or_404(request)
    if not request.user.can_view_stats_pe(current_org=current_org):
        raise PermissionDenied
    departments = request.user.get_stats_pe_departments(current_org=current_org)
    params = {
        DEPARTMENT_FILTER_KEY: [DEPARTMENTS[d] for d in departments],
    }
    context = {
        "page_title": page_title,
    }
    if current_org.is_dgpe:
        context |= {
            "matomo_custom_url_suffix": "dgpe",
        }
    elif current_org.is_drpe:
        context |= {
            "matomo_custom_url_suffix": f"{format_region_for_matomo(current_org.region)}/drpe",
            "region": current_org.region,
        }
    elif current_org.is_dtpe:
        context |= {
            "matomo_custom_url_suffix": f"{format_region_and_department_for_matomo(current_org.department)}/dtpe",
            "department": current_org.department,
        }
    else:
        context |= {
            "matomo_custom_url_suffix": f"{format_region_and_department_for_matomo(current_org.department)}/agence",
            "department": current_org.department,
        }
    return render_stats(request=request, context=context, params=params)


@login_required
def stats_pe_delay_main(request):
    return render_stats_pe(
        request=request,
        page_title="Délai d'entrée en IAE",
    )


@login_required
def stats_pe_delay_raw(request):
    return render_stats_pe(
        request=request,
        page_title="Données brutes de délai d'entrée en IAE",
    )


@login_required
def stats_pe_conversion_main(request):
    return render_stats_pe(
        request=request,
        page_title="Taux de transformation",
    )


@login_required
def stats_pe_conversion_raw(request):
    return render_stats_pe(
        request=request,
        page_title="Données brutes du taux de transformation",
    )


@login_required
def stats_pe_state_main(request):
    return render_stats_pe(
        request=request,
        page_title="Etat des candidatures orientées",
    )


@login_required
def stats_pe_state_raw(request):
    return render_stats_pe(
        request=request,
        page_title="Données brutes de l’état des candidatures orientées",
    )


@login_required
def stats_pe_tension(request):
    return render_stats_pe(
        request=request,
        page_title="Fiches de poste en tension",
    )


def render_stats_ddets(request, page_title, extra_context={}):
    department = get_stats_ddets_department(request)
    params = get_params_for_departement(department)
    context = {
        "page_title": f"{page_title} ({DEPARTMENTS[department]})",
        "department": department,
        "matomo_custom_url_suffix": format_region_and_department_for_matomo(department),
    }
    context.update(extra_context)
    return render_stats(request=request, context=context, params=params)


@login_required
def stats_ddets_auto_prescription(request):
    return render_stats_ddets(request=request, page_title="Focus auto-prescription")


@login_required
def stats_ddets_follow_siae_evaluation(request):
    return render_stats_ddets(request=request, page_title="Suivi du contrôle à posteriori")


@login_required
def stats_ddets_iae(request):
    return render_stats_ddets(request=request, page_title="Données IAE de mon département")


@login_required
def stats_ddets_siae_evaluation(request):
    extra_context = {
        "back_url": reverse("siae_evaluations_views:samples_selection"),
        "show_siae_evaluation_message": True,
    }
    return render_stats_ddets(
        request=request, page_title="Données du contrôle a posteriori", extra_context=extra_context
    )


@login_required
def stats_ddets_hiring(request):
    return render_stats_ddets(
        request=request,
        page_title="Données facilitation de l'embauche de mon département",
    )


def render_stats_dreets(request, page_title):
    region = get_stats_dreets_region(request)
    params = get_params_for_region(region)
    context = {
        "page_title": f"{page_title} ({region})",
        "matomo_custom_url_suffix": format_region_for_matomo(region),
        "region": region,
    }
    return render_stats(request=request, context=context, params=params)


@login_required
def stats_dreets_auto_prescription(request):
    return render_stats_dreets(request=request, page_title="Focus auto-prescription")


@login_required
def stats_dreets_follow_siae_evaluation(request):
    return render_stats_dreets(request=request, page_title="Suivi du contrôle à posteriori")


@login_required
def stats_dreets_iae(request):
    return render_stats_dreets(
        request=request,
        page_title="Données IAE de ma région",
    )


@login_required
def stats_dreets_hiring(request):
    return render_stats_dreets(
        request=request,
        page_title="Données facilitation de l'embauche de ma région",
    )


def render_stats_dgefp(request, page_title, extra_params=None, extra_context=None):
    if extra_context is None:
        extra_context = {}
    ensure_stats_dgefp_permission(request)
    context = {
        "page_title": page_title,
    }
    context.update(extra_context)
    return render_stats(request=request, context=context, params=extra_params)


@login_required
def stats_dgefp_auto_prescription(request):
    return render_stats_dgefp(
        request=request, page_title="Focus auto-prescription", extra_params=get_params_for_whole_country()
    )


@login_required
def stats_dgefp_follow_siae_evaluation(request):
    return render_stats_dgefp(
        request=request, page_title="Suivi du contrôle à posteriori", extra_params=get_params_for_whole_country()
    )


@login_required
def stats_dgefp_iae(request):
    return render_stats_dgefp(
        request=request, page_title="Données des régions", extra_params=get_params_for_whole_country()
    )


@login_required
def stats_dgefp_siae_evaluation(request):
    return render_stats_dgefp(
        request=request,
        page_title="Données (version bêta) du contrôle a posteriori",
        extra_context={"show_siae_evaluation_message": True},
        extra_params=get_params_for_whole_country(),
    )


@login_required
def stats_dgefp_af(request):
    return render_stats_dgefp(request=request, page_title="Annexes financières actives")


@login_required
def stats_dihal_state(request):
    current_org = get_current_institution_or_404(request)
    if not request.user.can_view_stats_dihal(current_org=current_org):
        raise PermissionDenied
    context = {
        "page_title": "Suivi des prescriptions des AHI",
    }
    return render_stats(request=request, context=context, params={})


@login_required
def stats_iae_network_hiring(request):
    current_org = get_current_institution_or_404(request)
    if not request.user.can_view_stats_iae_network(current_org=current_org):
        raise PermissionDenied
    context = {
        "page_title": "Données de candidatures des adhérents de mon réseau IAE",
    }
    return render_stats(
        request=request,
        context=context,
        params={IAE_NETWORK_FILTER_KEY: current_org.id},
    )
