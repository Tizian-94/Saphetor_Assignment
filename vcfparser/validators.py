from django.core.validators import RegexValidator

# vcf spec allows more contig names (chrUn_*, chr*_gl*,etc) but int he assignment the post and put are restricted to  chr1-22,chrX, chrY, chrM.
# loader accepts full contig set from file
CHROM_VALIDATOR = RegexValidator(
    regex=r"^chr([1-9]1[0-9]2[0-2]|X|Y|M)$",
    message="CHROM must be either chr1-chr22, chrX, chrY or chrM",
)

ID_VALIDATOR = RegexValidator(
    regex=r"^rs\d+$",
    message="ID must match 'rs<int>' eg: rs123"
)

# assignment restricts ref / alt to single characters (A, C, G, T or '.'), VCFs might contain other indels like REF=CAG or ALT=C
# the loader will accept them but post / put is intentionally set up to be strict
ALLELE_VALIDATOR = RegexValidator(
    regex=r"^[ACGT.]$",
    message="REF/ALT must be a single character (A,C,G,T,'.')",
)
