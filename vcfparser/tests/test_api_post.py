import pytest

from vcfparser.models import Variant

pytestmark = pytest.mark.usefixtures("vcf_file")

VALID_BODY = {
    "CHROM":"chr1",
    "POS":500,
    "ID":"rs999",
    "REF":"A",
    "ALT":"G",
}

def test_post_requires_authorization(api_client):
    # use api_client (no header) insted of auth_client to prove both paths

    r = api_client.post('/api/variants/', VALID_BODY, content_type='application/json')
    assert r.status_code == 403

def test_post_rejects_wrong_secret(api_client):
    # same as above to avoid bugs through where any header is accepted

    r = api_client.post(
        '/api/variants/', VALID_BODY,
        content_type='application/json',
        HTTP_AUTHORIZATION = 'not-the-secret',
    )
    assert r.status_code == 403
    
def test_post_creates_variant(auth_client, vcf_file):
    # check both db and file, a POST updating only DB would pass a DB only test but fail here

    r = auth_client.post('/api/variants/', VALID_BODY, content_type='application/json')
    assert r.status_code == 201
    # db state - row exists only once
    assert Variant.objects.filter(variant_id='rs999').count() == 1
    # file state - file on disc contains new line
    content = vcf_file.read_text()
    assert '\trs999\t' in content

def test_post_rejects_invalid_chrom(auth_client):
    body = {**VALID_BODY, "CHROM": "chrUn_gl000211"}
    r = auth_client.post('/api/variants/', body, content_type='application/json')
    assert r.status_code == 400

def test_post_rejects_invalid_id(auth_client):
    body = {**VALID_BODY, "ID":"."}
    r = auth_client.post('/api/variants/', body, content_type='application/json')
    assert r.status_code == 400

def test_post_rejects_negative_pos(auth_client):
    body = {**VALID_BODY, "POS": 0}
    r = auth_client.post('/api/variants/',body, content_type='application/json')
    assert r.status_code == 400

def test_post_rejects_missing_fields(auth_client):
    r = auth_client.post(
        '/api/variants/', {"CHROM": "chr1"}, content_type = 'application/json',
    )
    assert r.status_code == 400
    assert 'POS' in r.json() or 'ID' in r.json()