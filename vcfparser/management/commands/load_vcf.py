from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from vcfparser.models import Variant
from vcfparser.services.vcf_service import ensure_fresh, load_into_db

class Command(BaseCommand):
    help = ( "Load a VCF file into the DB cache. If the file is unchanged since the last load, command is no-op unless --force is passed")

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            type=str,
            help="Path to the vcf file"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Reparse the file even if previous fingerprint matches"
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        force = options["force"]
        
        # validate the file exists before touching db
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        #call load_into_db
        if force:
            load_into_db(str(path))
            action = "reloaded (forced)"
        else:
            ensure_fresh(str(path))
            action = "ensured fresh"

        #print output
        count = Variant.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"VCF {action}: {path} -> {count} variants in DB")
        )



