import datetime

from dateutil.relativedelta import relativedelta

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from itou.approvals import models


@admin.register(models.Approval)
class ApprovalAdmin(admin.ModelAdmin):
    actions = ("send_number_by_email",)
    list_display = (
        "id",
        "number",
        "user",
        "start_at",
        "end_at",
        "number_sent_by_email",
    )
    list_filter = ("number_sent_by_email",)
    list_display_links = ("id", "number")
    raw_id_fields = ("user", "job_application", "created_by")
    readonly_fields = ("created_at", "created_by")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def add_view(self, request, form_url="", extra_context=None):
        """
        Prepopulate the form with calculated data.
        """
        g = request.GET.copy()
        g.update({"number": self.model.get_next_number()})
        start_at = g.get("start_at")
        if start_at:
            start_at = datetime.datetime.strptime(start_at, "%d/%m/%Y").date()
            end_at = start_at + relativedelta(years=2)
            g.update({"start_at": start_at, "end_at": end_at})
        request.GET = g
        return super().add_view(request, form_url, extra_context=extra_context)

    def send_number_by_email(self, request, queryset):
        for approval in queryset:
            approval.send_number_by_email()
            approval.number_sent_by_email = True
            approval.save()

    send_number_by_email.short_description = _("Envoyer le numéro par email")
