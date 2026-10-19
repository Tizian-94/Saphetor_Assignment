import pytest

from vcfparser.models import Variant

pytestmark = pytest.mark.usefixtures("vcf_file")

VALID_BODY = {
    "CHROM":"chr1", "POS":500, "ID":"rs2",
    "REF":"G", "ALT":"A",
}

def test_put_requires_authorization(api_client):
    r = api_client.put('/api/variants/?id=rs2', VALID_BODY, content_type='application/json')
    assert r.status_code == 403

def test_put_rejects_wrong_secret(api_client):
    r = api_client.put(
        '/api/variants/?id=rs2', VALID_BODY,
        content_type='application/json',
        HTTP_AUTHORIZATION='not-the-secret',
    )
    assert r.status_code == 403

def test_put_updates_matching_row(auth_client, vcf_file):
    r = auth_client.put(
        '/api/variants/?id=rs2', VALID_BODY, content_type='application/json',
    )
    assert r.status_code == 200
    v = Variant.objects.get(variant_id='rs2')
    assert v.pos == 500
    assert v.ref == 'G'
    assert '\trs2\tG\tA\t' in vcf_file.read_text()

def test_put_returns_404_for_nonmatching_id(auth_client):
    r = auth_client.put(
        '/api/variants/?id=rs_nonexistent', VALID_BODY,
        content_type='application/json',
    )
    assert r.status_code == 404

def test_put_returns_400_without_id_param(auth_client):
    r = auth_client.put('/api/variants/', VALID_BODY, content_type='application/json')
    assert r.status_code == 400

def test_put_rejects_invalid_chrom(auth_client):
    body = {**VALID_BODY, "CHROM":"chrUn_gl100211"}
    r = auth_client.put(
        '/api/variants/?id=rs2', body, content_type='application/json',
    )
    assert r.status_code == 400

def test_put_updates_multiple_rows(auth_client):
    body = {**VALID_BODY, "ID": "rs1"}
    r = auth_client.put(
        '/api/variants/?id=rs1', body, content_type='application/json',
    )
    assert r.status_code == 200
    assert Variant.objects.filter(variant_id='rs1', pos=500).count() == 2