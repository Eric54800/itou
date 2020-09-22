"""

This script is still needed until we complete the national opening, end of November 2020.

It does ressucitate GEIQ structures as well whereas `import_siae.py` doesn't.

"""
import json
import os

from django.core.management.base import BaseCommand

from itou.siaes.models import Siae
from itou.utils.address import departments


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

JSON_FILE = f"{CURRENT_DIR}/data/deleted_siae.json"


# Carefully pick your choice.
DEPARTMENTS_TO_OPEN = departments.DEPARTMENTS_TO_OPEN_ON_22_09_2020


class Command(BaseCommand):
    """
    Restore deleted SIAEs data into the database.

    Usage:
        django-admin import_deleted_siae --dry-run
        django-admin import_deleted_siae

    Why have some SIAEs been deleted from the database?

    # COVID-19 "Operation ETTI".

    26/03/2020: following COVID-19 pandemic, Thibaut asks us to open Itou for
    all SIAEs of kind ETTI outside test departements (62, 67, 93) to encourage
    hiring.

    This is called "operation ETTI". The aim is to manufacture the products
    needed for the war effort. To meet manpower requirements "HCIEE" and
    "La fédération des entreprises d'insertion" have built in a few days
    the ETTI coalition to respond to these needs. ITOU should make it possible
    to put customers directly in touch (Intermarché and other brands) with
    geolocalised ETTIs that are likely to offer manpower.

    In number, ETTIs represent 10% of all SIAEs in the database.

    To minimise load/performance risks and customer support flooding risk,
    we chose to delete non-ETTIs and non-93-62-67 SIAEs from the database
    instead of opening Itou for all SIAEs which was our initial idea.

    Deleted SIAEs have been saved in a fixture.

    Since the `pk` looks mandatory in Django's fixtures and `loaddata`
    overwrites all existing data while synchronizing database, we use
    this management command to restore the fixture with new `pk`s.

    # Open Itou gradually.

    13/04/2020: it was decided to gradually restore SIAE according to
    the deployment schedule.

    14/04/2020: open Île-de-France (75, 77, 78, 91, 92, 93, 94, 95)

    20/04/2020 and later: see DEPARTMENTS_TO_OPEN_ON_* above.
    """

    help = "Restore deleted SIAEs data into the database."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Only print data to import")

    def handle(self, dry_run=False, **options):

        total_new_siaes = 0

        with open(JSON_FILE, "r") as raw_json_data:

            json_data = json.load(raw_json_data)
            total_len = len(json_data)
            last_progress = 0

            for i, item in enumerate(json_data):

                progress = int((100 * i) / total_len)
                if progress > last_progress + 5:
                    self.stdout.write(f"Restoring SIAEs… {progress}%")
                    last_progress = progress

                siae = Siae(**item["fields"])

                if siae.department not in DEPARTMENTS_TO_OPEN:
                    continue

                if Siae.objects.filter(siret=siae.siret, kind=siae.kind).exists():
                    self.stdout.write(f"siae siret={siae.siret} kind={siae.kind} already exists (will be ignored)")
                    continue

                total_new_siaes += 1

                if not dry_run:
                    siae.save()

        self.stdout.write("-" * 80)

        if not dry_run:
            self.stdout.write(f"{total_new_siaes} siaes have been created.")
        else:
            self.stdout.write(f"{total_new_siaes} siaes would have been created.")

        self.stdout.write("-" * 80)
        self.stdout.write("Done.")
