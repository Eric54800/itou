import dataclasses
import datetime
from typing import Optional

from django.conf import settings
from django.db import models
from django.utils import timezone

from itou.users.models import User


class FranceConnectQuerySet(models.QuerySet):
    def cleanup(self):
        expired_datetime = timezone.now() - settings.FRANCE_CONNECT_STATE_EXPIRATION
        return self.filter(created_at__lte=expired_datetime).delete()


class FranceConnectState(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    # Length used in call to get_random_string()
    csrf = models.CharField(max_length=12, blank=False, null=False, unique=True)

    objects = models.Manager.from_queryset(FranceConnectQuerySet)()


@dataclasses.dataclass
class FranceConnectUserData:  # pylint: disable=too-many-instance-attributes
    username: str
    first_name: str
    last_name: str
    birthdate: datetime.date
    email: str
    phone: str
    address_line_1: str
    post_code: str
    city: str
    country: Optional[str] = None


def load_user_data(user_data: dict) -> dict:
    user_model_dict = {
        "username": user_data["sub"],
        "first_name": user_data.get("given_name", ""),
        "last_name": user_data.get("family_name", ""),
        "birthdate": datetime.date.fromisoformat(user_data["birthdate"]) if user_data.get("birthdate") else None,
        "email": user_data.get("email"),
        "phone": user_data.get("phone_number"),
        "address_line_1": "",
        "post_code": "",
        "city": "",
        "country": None,
    }

    if "address" in user_data:
        user_model_dict |= {
            "address_line_1": user_data["address"].get("street_address"),
            "post_code": user_data["address"].get("postal_code"),
            "city": user_data["address"].get("locality"),
            "country": user_data["address"].get("country"),
        }

    return user_model_dict


def set_fields_from_user_data(user: User, fc_user_data: FranceConnectUserData):
    # birth_country_id from user_data["birthcountry"]
    # birth_place_id from user_data["birthplace"]
    provider_json = {}
    now = timezone.now()
    provider_info = {"source": "france_connect", "created_at": now}
    for field in ["username", "first_name", "last_name", "birthdate", "email", "phone"]:
        setattr(user, field, getattr(fc_user_data, field))
        provider_json[field] = provider_info

    if fc_user_data.country == "France":
        for field in ["address_line_1", "post_code", "city"]:
            setattr(user, field, getattr(fc_user_data, field))
            provider_json[field] = provider_info

    user.provider_json = provider_json


def update_fields_from_user_data(user: User, fc_user_data: FranceConnectUserData, provider_json: dict):
    now = timezone.now()

    # Not very smart
    def is_fc_source(field):
        return provider_json.get(field) and provider_json[field]["source"] == "france_connect"

    def update_time(field):
        provider_json[field]["created_at"] = now

    for field in dataclasses.fields(fc_user_data):
        if field.name == "country":
            continue

        if is_fc_source(field.name):
            setattr(user, field.name, getattr(fc_user_data, field.name))
            update_time(field.name)


def create_or_update_user(fc_user_data: FranceConnectUserData):
    # We can't use a get_or_create here because we have to set provider_json for each field
    try:
        user = User.objects.get(username=fc_user_data.username)
        # Should we update the user fields on user authenticate?
        # In first approach, it safes to update FC fields
        update_fields_from_user_data(user, fc_user_data, user.provider_json)
        created = False
    except User.DoesNotExist:
        # Create a new user
        user = User()
        set_fields_from_user_data(user, fc_user_data)
        created = True
    user.save()

    return user, created
