from django.db import models

#VcfHeader
#textfield - all ## lines & the #CHROM line
#file_mtime: Float field
#file_size: BigIntegerField
#loaded_at: Datetimefield(autonow=True)
#class method is_stale(os.stat(path)) + compare to stored values

#Variant

#id: Autofield(PK=True, autoincrement) - alt method to keep track of IDs and not assume duplicates
#chrom: CharField(max_length=64, db_index=True)
#pos: IntegerField(db_index=True)
#variant_id: CharField(max_length=64, db_index=True) - original vcf id field, can sometimes be . or blank
#ref: CharField(max_length=256)
#alt: CharField(max_length=256)
#raw_line: TextField -verbatim (full tab-separated line) / on PUT reconstruct via patching 5 fields into the raw line
#Meta.indexes (chrom, pos) - would be a text field probably?
#Meta.ordering = ['id'] - deterministic pagination to avoid duplicate or skip rows, set pagination row size also

