import os
from django.db import transaction

from vcfparser.models import VcfHeader, Variant

def parse_vcf(path):
    #read VCF file and return header_text, rows where header text startswith '#' concat verbatim (including #CHROM) && rows is a list of dicts with 5 extracted fields + raw_line

    #parse_vcf(path) - > (header_text, list[dict]) - read file, split headers from body, return the header blob and a list of dicts with the 5 fields + raw_line
    with open(path, 'r', newline='') as fh:
        lines = fh.readlines()

    header_lines = []
    rows = []
    in_header = True

    for line in lines:
        if in_header and line.startswith('#'):
            header_lines.append(line)
            continue
        in_header = False

        stripped = line.rstrip('\n').rstrip('\r')
        if not stripped:
            continue

        fields = stripped.split('\t')
        if len(fields) < 5:
            # malformed row - skip
            # @tODO - LOG
            continue

        rows.append({
            'chrom': fields[0],
            'pos': fields[1],
            'variant_id':fields[2],
            'ref':fields[3],
            'alt':fields[4],
            'raw_line':stripped,
        })

    return ''.join(header_lines), rows


#load_into_db(path) - calls parse_vcf, wipe and refill VcfHeader + Variant inside transaction, called by management command
@transaction.atomic
def load_into_db(path):
    #wipe cache and rebuild from file. Called by loader command

    header_text, rows = parse_vcf(path)
    stat = os.stat(path)

    Variant.objects.all().delete()
    VcfHeader.objects.all().delete()

    VcfHeader.objects.create(
        content=header_text,
        file_mtime=stat.st_mtime,
        file_size=stat.st_size,
    )

    #bulk-create bypass per row save() for speed
    Variant.objects.bulk_create([Variant(**r) for r in rows])

#ensure_fresh(path)
def ensure_fresh(path):
    # only re parse if file has changed
    if VcfHeader.is_stale(path):
        load_into_db(path)

def rewrite_vcf(path):
    # rebuild VCF from DB and atomically replace file on disk. original is never left half written. App writes to <path>/tmp and swaps it with os.replace.

    header = VcfHeader.objects.first()
    if header is None:
        raise RuntimeError("No VcfHeader in DB - run load_into_db first")

    tmp_path = path + '.tmp'
    try:
        with open(tmp_path, 'w', newline='') as fh:
            fh.write(header.content)
            if not header.content.endswith('\n'):
                fh.write('\n')
            for variant in Variant.objects.order_by('id').iterator():
                fh.write(variant.raw_line + '\n')
        os.replace(tmp_path, path) # outside the with block to avoid windows permissions
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    #refresh fingerprint so that is_stale() doesn't trip
    stat = os.stat(path)
    header.file_mtime = stat.st_mtime
    header.file_size = stat.st_size
    header.save(update_fields=['file_mtime', 'file_size'])

    #get_variants(queryset_or_page_params) - django rest framework
    #filter_by_id(variant_id) - return queryset filtered by variant_id
    #append_variant(data: dict) - validate then insert db row, append to file and update vcfHeader.file_mtime/size
    # def append_variant(data):
    #update_variants(variant_id, data: dict) -> int - patch the matching rows inside the db and rewrite the file atomically, return count of modified records
    # def update_variants(variant_id, data):
    #delete_variants(variant_id) -> int - delete matching rows and rewrite the file atomically, return count of deleted records
    # def delete_variants(variant_id):
    #rewrite_vcf(path) - atomic write helper: read the header + variants from db, write to path.tmp, os.replace

