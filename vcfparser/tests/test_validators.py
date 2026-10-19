import pytest
from django.core.exceptions import ValidationError
from vcfparser.validators import CHROM_VALIDATOR, ID_VALIDATOR, ALLELE_VALIDATOR

# chrom
@pytest.mark.parametrize("chrom", ["chr1","chr9","chr10","chr22","chrX", "chrY", "chrM"])
def test_chrom_validator_accepts(chrom):
    CHROM_VALIDATOR(chrom)

@pytest.mark.parametrize("chrom", ["chr0","chr23","CHR1","chrUn_gl000211", "1", ""])
def test_chrom_validator_rejects(chrom):
    with pytest.raises(ValidationError):
        CHROM_VALIDATOR(chrom)

# id
@pytest.mark.parametrize("id", ["rs123","rs1","rs2","rs3","rs4", "rs5", "rs6"])
def test_id_validator_accepts(id):
    ID_VALIDATOR(id)

@pytest.mark.parametrize("id", ["rs","RS111","rsABC",".", "2", ""])
def test_id_validator_rejects(id):
    with pytest.raises(ValidationError):
        ID_VALIDATOR(id)

# Allele
@pytest.mark.parametrize("ref", ["A","C","G","T","."])
def test_ref_validator_accepts(ref):
    ALLELE_VALIDATOR(ref)

@pytest.mark.parametrize("ref", ["AC","N","a",""])
def test_ref_validator_rejects(ref):
    with pytest.raises(ValidationError):
        ALLELE_VALIDATOR(ref)

@pytest.mark.parametrize("alt", ["A","C","G","T","."])
def test_alt_validator_accepts(alt):
    ALLELE_VALIDATOR(alt)

@pytest.mark.parametrize("alt", ["AC","N","a",""])
def test_alt_validator_rejects(alt):
    with pytest.raises(ValidationError):
        ALLELE_VALIDATOR(alt)