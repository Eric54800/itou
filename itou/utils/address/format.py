import unicodedata

from itou.asp.models import LANE_TYPE_ALIASES, LaneExtension, LaneType
from itou.prescribers.models import PrescriberOrganization
from itou.siaes.models import Siae
from itou.users.models import User
from itou.utils.apis.geocoding import detailed_geocoding_data, get_geocoding_data


def strip_accents(s):
    nfkd_form = unicodedata.normalize("NFKD", s)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def format_address(obj, update_coords=False):
    """
    Formats the address contained in obj into a valid address "structure" for ASP ER exports.

    Heavily relies on geo.api.gouv.fr API to do parts of the job for us:
    - extracting lane number and extension
    - giving a geocoding score / threshold in order to improve an existing DB address
    - validation of a real-world address

    Employee records ("Fiches salarié") contains 2 addresses of this kind.

    See validation of ASP address for expected/valid fields

    Returns a (result,error) tuple:
    - OK => (smth, None),
    - KO => (None, error_message)
    """

    if type(obj) not in [Siae, PrescriberOrganization, User]:
        return None, "This object has no address"

    # Do we have enough data to make an extraction?
    if not obj.post_code or not obj.address_line_1:
        return None, "Incomplete address data"

    print(f"FMT: {obj.address_line_1}, {obj.post_code}")

    # first we use geo API to get a 'lane' and a number
    address = get_geocoding_data(obj.address_line_1, post_code=obj.post_code, fmt=detailed_geocoding_data)

    if not address:
        return None, "Geocoding error, unable to get result"

    result = {}

    # Get street extension (bis, ter ...)
    # It's part of the resulting streetnumber geo API field
    number_plus_ext = address.get("number")
    if number_plus_ext:
        number, *extension = number_plus_ext.split()

        if number:
            result["number"] = number

        if extension:
            extension = extension[0]
            if ext := LaneExtension.has_similar_name_or_value(extension):
                result["std_extension"] = ext
                # return None, f"Unknown lane extension: {extension}"
            else:
                result["non_std_extension"] = extension

    lane = None
    if not address.get("lane") and not address.get("address"):
        print(address)
        return None, "Unable to get address lane"
    else:
        lane = address.get("lane") or address.get("address")
        lane = strip_accents(lane)
        result["lane"] = lane

    # Lane type processing
    lane_type = lane.split(maxsplit=1)[0]

    if lt := LaneType.has_similar_name(lane_type, fmt=strip_accents):
        result["lane_type"] = lt
    elif lt := LaneType.name_for_similar_value(lane_type):
        result["lane_type"] = lt
    elif lt := LANE_TYPE_ALIASES.get(lane_type):
        result["lane_type"] = lt.name
    else:
        return None, f"Can't find lane type: {lane_type}"

    # INSEE code:
    # must double check with ASP ref file
    result["insee_code"] = address.get("insee_code")
    # TODO check with ASP data

    if update_coords and address.get("coords", None) and address.get("score", -1) > obj.get("geocoding_score", 0):
        # User, Siae and PrescribersOrganisation all have score and coords
        obj.coords = address["coords"]
        obj.geocoding_score = address["score"]
        obj.save()

    return result, None
