import pytest
from django.test import Client

from vcfparser.services import vcf_service

FIXTURE_VCF = (
    "##fileformat=VCFv4.2\n"
    "##contig=<ID=chr1,length=249250621>\n"
    "##contig=<ID=chr2,length=243199373>\n"
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    "chr1\t100\trs1\tA\tG\t99\tPASS\tDP=10\n"
    "chr1\t200\trs2\tC\tT\t99\tPASS\tDP=10\n"
    "chr1\t300\trs3\tG\tA\t99\tPASS\tDP=10\n"
    "chr2\t100\trs4\tT\tC\t99\tPASS\tDP=10\n"
    "chr2\t200\t.\tA\tG\t99\tPASS\tDP=10\n"
    "chr2\t400\trs1\tA\tC\t50\tPASS\tDP=5\n"
)

@pytest.fixture
def vcf_file(tmp_path, settings, db):
    # create fresh vcf in per test tmp dir and loads into DB, each test is in separate file and DB state to avoid cross contamination
    path = tmp_path / "sample.vcf"
    path.write_bytes(FIXTURE_VCF.encode('utf-8'))
    settings.VCF_FILE_PATH = path
    vcf_service.load_into_db(str(path))
    return path

@pytest.fixture
def test_rewrite_normalizes_crlf_input(tmp_path, settings, db):
    # avoid \\n on windows edited files
    from vcfparser.services import vcf_service
    p = tmp_path / "windows.vcf"
    p.write_bytes(b"##fileformat=VCFv4.2\r\n#CHROM\tPOS\tID\tREF\tALT\r\nchr1\t100\trs1\tA\tG\r\n")
    settings.VCF_FILE_PATH = p
    vcf_service.load_into_db(str(p))
    vcf_service.rewrite_vcf(str(p))

    content = p.read_bytes()
    assert b'\r' not in content
    assert content.endswith(b'\n')

@pytest.fixture
def api_client():
    # anon drf client (for GET test)
    return Client()

@pytest.fixture
def auth_client(settings):
    # client with secret attached to request (for POST PUT DELETE)
    c = Client()
    c.defaults['HTTP_AUTHORIZATION'] = settings.API_SECRET
    return c