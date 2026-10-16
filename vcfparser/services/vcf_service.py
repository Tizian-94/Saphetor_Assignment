#parse_vcf(path) - > (header_text, list[dict]) - read file, split headers from body, return the header blob and a list of dicts with the 5 fields + raw_line

#load_into_db(path) - calls parse_vcf, wipe and refill VcfHeader + Variant inside transaction, called by management command

#ensure_fresh(path)

#get_variants(queryset_or_page_params) - django rest framework
#filter_by_id(variant_id) - return queryset filtered by variant_id
#append_variant(data: dict) - validate then insert db row, append to file and update vcfHeader.file_mtime/size
#update_variants(variant_id, data: dict) -> int - patch the matching rows inside the db and rewrite the file atomically, return count of modified records
#delete_variants(variant_id) -> int - delete matching rows and rewrite the file atomically, return count of deleted records
#rewrite_vcf(path) - atomic write helper: read the header + variants from db, write to path.tmp, os.replace

