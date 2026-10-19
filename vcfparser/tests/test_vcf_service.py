import pytest

from vcfparser.models import VcfHeader, Variant
from vcfparser.services import vcf_service

# parse vcf

def test_parse_vcf_splits_header_and_body(vcf_file):
    header, rows = vcf_service.parse_vcf(str(vcf_file))
    assert header.startswith('##fileformat=VCFv4.2')
    assert header.endswith('\n')
    assert len(rows) == 6

def test_parse_vcf_skips_malformed_rows(tmp_path):
    p = tmp_path / "bad.vcf"
    p.write_text(
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\n"
        "chr1\t100\trs1\tA\tG\n"
        "too-few-columns\n" # 1 column, must skip
        "chr1\t200\trs2\tC\tT\n"
    )
    _, rows = vcf_service.parse_vcf(str(p))
    assert len(rows) == 2
    assert {r['variant_id'] for r in rows} == {'rs1','rs2'}

# load into db

def test_load_creates_header_and_rows(vcf_file):
    # verify if fixture loaded
    assert VcfHeader.objects.count() == 1
    assert Variant.objects.count() == 6

def test_load_wipes_previous_state(vcf_file):
    # add mistake row then reload to clear it
    Variant.objects.create(
        chrom='chrZ', pos=1, variant_id='rs_mistake',
        ref='A', alt='T',raw_line='chrZ\t1\trs_mistake\tA\tT\t.\t.\t.',
    )
    assert Variant.objects.count() == 7
    vcf_service.load_into_db(str(vcf_file))
    assert Variant.objects.count() == 6
    assert not Variant.objects.filter(variant_id='rs_mistake').exists()

# ensure fresh

def test_ensure_fresh_skips_when_unchanged(vcf_file):
    before = VcfHeader.objects.first().loaded_at
    vcf_service.ensure_fresh(str(vcf_file))
    after = VcfHeader.objects.first().loaded_at
    assert before == after # no reload happends

def test_ensure_fresh_reloads_when_file_changes(vcf_file):
    with open(vcf_file, 'a') as f:
        f.write('chr1\t9999\trs_new\tA\tG\t.\t.\t.\n')
    vcf_service.ensure_fresh(str(vcf_file))
    assert Variant.objects.count() == 7

# append variant

def test_append_variant_writes_file_and_db(vcf_file):
    # verify if last line matches exact tab joined string including 3 "."

    data = {
        'chrom': 'chr1', 'pos': 1234, 'variant_id': 'rs777',
        'ref': 'A', 'alt': 'T',
    }
    vcf_service.append_variant(data, str(vcf_file))
    # db
    assert Variant.objects.filter(variant_id='rs777').count() == 1
    # file (last line)
    last = vcf_file.read_text().splitlines()[-1]
    assert last == 'chr1\t1234\trs777\tA\tT\t.\t.\t.'

#update variants

def test_update_variants_single_row(vcf_file):
    data = {
        'chrom':'chr1','pos': 999, 'variant_id': 'rs2',
        'ref': 'G', 'alt': 'A',
    }
    n = vcf_service.update_variants('rs2',data, str(vcf_file))
    assert n == 1
    v = Variant.objects.get(variant_id='rs2')
    assert v.pos == 999
    assert v.ref == 'G'

def test_update_variants_multiple_rows(vcf_file):
    # rs1 appears twice
    data = {
        'chrom':'chr9', 'pos': 5000, 'variant_id': 'rs1',
        'ref': 'T', 'alt':'C',
    }
    n = vcf_service.update_variants('rs1', data, str(vcf_file))
    assert n == 2
    assert Variant.objects.filter(variant_id='rs1').count() == 2
    assert Variant.objects.filter(chrom='chr9').count() == 2

def test_update_variants_preserves_trailing_columns(vcf_file):
    # verify parts [0:5] = [...] and if rejoin preserves QUAL, FILTER, INFO

    # original row = chr1:200, REF=C, ALT=T, QUAL=99, FILTER=PASS, INFO=DP=10
    data = {
        'chrom':'chr1','pos': 300, 'variant_id': 'rs2',
        'ref': 'G', 'alt': 'A',
    }
    vcf_service.update_variants('rs2', data, str(vcf_file))
    # rewrite raw line from disk
    content = vcf_file.read_text()
    # find line with pos= 100 and ref=C
    lines = [l for l in content.splitlines() if l.startswith('chr1\t300\trs2\t')]
    assert len(lines) == 1
    parts = lines[0].split('\t')
    # changed
    assert parts[2] == 'rs2'
    assert parts[3] == 'G'
    assert parts[4] == 'A'
    # the same
    assert parts[5] == '99'
    assert parts[6] == 'PASS'
    assert parts[7] == 'DP=10'

def test_update_variants_multi_row_preserves_each_row_trailing(vcf_file):
    # since rs1 appears twice with different trailing columns. verify both are preserved independent
    data = {
        'chrom':'chr9', 'pos':5000, 'variant_id':'rs1',
        'ref':'T', 'alt':'C'
    }
    vcf_service.update_variants('rs1', data, str(vcf_file))

    content = vcf_file.read_text()
    lines = [l for l in content.splitlines() if l.startswith('chr9\t5000\trs1\t')]
    assert len(lines) == 2
    #  1 - QUAL 99, 2 - QUAL 50
    quals = sorted(line.split('\t')[5] for line in lines)
    assert quals == ['50', '99']

def test_update_variants_no_match_returns_zero(vcf_file):
    # prove modified == 0 in views.py results in 404

    n = vcf_service.update_variants(
        'rs_nonexistent',
        {'chrom': 'chr1', 'pos':1, 'variant_id': 'rs_nonexistent', 'ref':'A','alt':'T'},
        str(vcf_file),
    )
    assert n == 0

# delete variants

def test_delete_variants_single(vcf_file):
    n = vcf_service.delete_variants('rs2', str(vcf_file))
    assert n == 1
    assert not Variant.objects.filter(variant_id = 'rs2').exists()
    assert 'rs2' not in vcf_file.read_text()

def test_delete_variants_multiple(vcf_file):
    n = vcf_service.delete_variants('rs1', str(vcf_file))
    assert n == 2
    assert not Variant.objects.filter(variant_id = 'rs1').exists()

def test_delete_variants_no_match_returns_zero(vcf_file):
    n = vcf_service.delete_variants('rs_missing', str(vcf_file))
    assert n == 0

# rewrite vcf

def test_rewrite_is_byte_identical_when_unchanged(vcf_file):
    # check if diff shows changes
    original = vcf_file.read_bytes()
    vcf_service.rewrite_vcf(str(vcf_file))
    after = vcf_file.read_bytes()
    assert original == after