import os
from django.db import models

#VcfHeader
class VcfHeader(models.Model):
    # store VCF headers verbatim & a fingerprint of the source file to detect if  file changes and if cache is stale
    
    #textfield - all ## lines & the #CHROM line
    content = models.TextField()

    #file_mtime: Float field
    file_mtime = models.FloatField()

    #file_size: BigIntegerField
    file_size = models.BigIntegerField()
    
    #loaded_at: Datetimefield(autonow=True)
    loaded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"VcfHeader (loaded {self.loaded_at:%Y-%m-%d %H:%M:%S})"
    
    #class method is_stale(os.stat(path)) + compare to stored values
    @classmethod
    def is_stale(cls, path):
        #True if db cache =/= current file on disk
        stat = os.stat(path)
        stored = cls.objects.first()
        if stored is None:
            return True
        return (stored.file_mtime,stored.file_size) != (stat.st_mtime, stat.st_size)

#Variant
class Variant(models.Model):
    #1 row per variant line, django automatic autoincrement "id" for PK

    #id: Autofield(PK=True, autoincrement) - alt method to keep track of IDs and not assume duplicates
    
    #chrom: CharField(max_length=64, db_index=True)
    chrom = models.CharField(max_length=64,db_index=True)

    #pos: IntegerField(db_index=True)
    pos = models.IntegerField(db_index=True)

    #variant_id: CharField(max_length=64, db_index=True) - original vcf id field, can sometimes be . or blank
    variant_id = models.CharField(max_length=64, db_index=True)

    #ref: CharField(max_length=256)
    ref = models.CharField(max_length=256)

    #alt: CharField(max_length=256)
    alt = models.CharField(max_length=256)

    #raw_line: TextField -verbatim (full tab-separated line) / on PUT reconstruct via patching 5 fields into the raw line
    raw_line = models.TextField()

    class Meta:
        #Meta.ordering = ['id'] - deterministic pagination to avoid duplicate or skip rows, set pagination row size also
        ordering = ['id']

        #Meta.indexes (chrom, pos)
        indexes = [models.Index(fields=['chrom','pos'])]

    def __str__(self):
        return f"{self.chrom}:{self.pos} {self.variant_id}"
