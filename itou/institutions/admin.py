from django.contrib import admin
from django.contrib.gis import forms as gis_forms
from django.contrib.gis.db import models as gis_models

from itou.common_apps.organizations.admin import MembersInline, OrganizationAdmin
from itou.institutions import models
from itou.institutions.admin_forms import InstitutionAdminForm


class InstitutionMembersInline(MembersInline):
    model = models.InstitutionMembership


@admin.register(models.Institution)
class InstitutionAdmin(OrganizationAdmin):

    form = InstitutionAdminForm
    fieldsets = (
        (
            "Structure",
            {
                "fields": (
                    "pk",
                    "kind",
                    "name",
                )
            },
        ),
        (
            "Adresse",
            {
                "fields": (
                    "address_line_1",
                    "address_line_2",
                    "post_code",
                    "city",
                    "department",
                    "extra_field_refresh_geocoding",
                    "coords",
                    "geocoding_score",
                )
            },
        ),
        (
            "Info",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    inlines = (InstitutionMembersInline,)
    list_display = ("pk", "name", "kind", "post_code", "city", "department", "member_count")
    list_display_links = ("pk", "name")
    list_filter = (
        "kind",
        "department",
    )
    readonly_fields = (
        "pk",
        "created_at",
        "updated_at",
        "geocoding_score",
    )
    search_fields = (
        "pk",
        "name",
        "department",
        "post_code",
        "city",
    )
    formfield_overrides = {
        # https://docs.djangoproject.com/en/2.2/ref/contrib/gis/forms-api/#widget-classes
        gis_models.PointField: {"widget": gis_forms.OSMWidget(attrs={"map_width": 800, "map_height": 500})}
    }

    def get_queryset(self, request):
        # OrganizationAdmin adds some useful annotations.
        return super().get_queryset(request)

    def save_model(self, request, obj, form, change):
        if not change:
            if not obj.geocoding_score and obj.geocoding_address:
                # Set geocoding.
                obj.set_coords(obj.geocoding_address, post_code=obj.post_code)

        if change and form.cleaned_data.get("extra_field_refresh_geocoding") and obj.geocoding_address:
            # Refresh geocoding.
            obj.set_coords(obj.geocoding_address, post_code=obj.post_code)

        super().save_model(request, obj, form, change)
