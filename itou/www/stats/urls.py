from django.urls import path

from itou.www.stats import views


app_name = "stats"

urlpatterns = [
    # Public stats.
    path("", views.stats_public, name="stats_public"),
    path("pilotage/<int:dashboard_id>", views.stats_pilotage, name="stats_pilotage"),
    # Employer stats.
    path("siae/etp", views.stats_siae_etp, name="stats_siae_etp"),
    path("siae/hiring", views.stats_siae_hiring, name="stats_siae_hiring"),
    path("siae/auto_prescription", views.stats_siae_auto_prescription, name="stats_siae_auto_prescription"),
    path(
        "siae/follow_siae_evaluation",
        views.stats_siae_follow_siae_evaluation,
        name="stats_siae_follow_siae_evaluation",
    ),
    # Prescriber stats.
    path("cd", views.stats_cd, name="stats_cd"),
    path("pe/delay/main", views.stats_pe_delay_main, name="stats_pe_delay_main"),
    path("pe/delay/raw", views.stats_pe_delay_raw, name="stats_pe_delay_raw"),
    path("pe/conversion/main", views.stats_pe_conversion_main, name="stats_pe_conversion_main"),
    path("pe/conversion/raw", views.stats_pe_conversion_raw, name="stats_pe_conversion_raw"),
    path("pe/state/main", views.stats_pe_state_main, name="stats_pe_state_main"),
    path("pe/state/raw", views.stats_pe_state_raw, name="stats_pe_state_raw"),
    path("pe/tension", views.stats_pe_tension, name="stats_pe_tension"),
    # Institution stats - DDETS - department level.
    path("ddets/auto_prescription", views.stats_ddets_auto_prescription, name="stats_ddets_auto_prescription"),
    path(
        "ddets/follow_siae_evaluation",
        views.stats_ddets_follow_siae_evaluation,
        name="stats_ddets_follow_siae_evaluation",
    ),
    path("ddets/iae", views.stats_ddets_iae, name="stats_ddets_iae"),
    path("ddets/siae_evaluation", views.stats_ddets_siae_evaluation, name="stats_ddets_siae_evaluation"),
    path("ddets/hiring", views.stats_ddets_hiring, name="stats_ddets_hiring"),
    # Institution stats - DREETS - region level.
    path("dreets/auto_prescription", views.stats_dreets_auto_prescription, name="stats_dreets_auto_prescription"),
    path(
        "dreets/follow_siae_evaluation",
        views.stats_dreets_follow_siae_evaluation,
        name="stats_dreets_follow_siae_evaluation",
    ),
    path("dreets/iae", views.stats_dreets_iae, name="stats_dreets_iae"),
    path("dreets/hiring", views.stats_dreets_hiring, name="stats_dreets_hiring"),
    # Institution stats - DGEFP - nation level.
    path("dgefp/auto_prescription", views.stats_dgefp_auto_prescription, name="stats_dgefp_auto_prescription"),
    path(
        "dgefp/follow_siae_evaluation",
        views.stats_dgefp_follow_siae_evaluation,
        name="stats_dgefp_follow_siae_evaluation",
    ),
    path("dgefp/iae", views.stats_dgefp_iae, name="stats_dgefp_iae"),
    path("dgefp/siae_evaluation", views.stats_dgefp_siae_evaluation, name="stats_dgefp_siae_evaluation"),
    path("dgefp/af", views.stats_dgefp_af, name="stats_dgefp_af"),
    # Institution stats - DIHAL - nation level.
    path("dihal/state", views.stats_dihal_state, name="stats_dihal_state"),
    # Institution stats - IAE Network - nation level.
    path("iae_network/hiring", views.stats_iae_network_hiring, name="stats_iae_network_hiring"),
]
