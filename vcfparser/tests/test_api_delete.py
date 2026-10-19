import pytest

from vcfparser.models import Variant

pytestmark = pytest.mark.usefixtures("vcf_file")

def test_delete_requires_authorization(api_client):
    r = api_client.delete('/api/variants/?id=rs2')
    assert r.status_code == 403

def test_delete_rejects_wrong_secret(api_client):
    r = api_client.delete(
        '/api/variants/?id=rs2',
        HTTP_AUTHORIZATION='not-the-secret',
    )
    assert r.status_code == 403

def test_delete_removes_row(auth_client, vcf_file):
    r = auth_client.delete('/api/variants/?id=rs2')
    assert r.status_code == 204
    assert not Variant.objects.filter(variant_id='rs2').exists()
    assert '\trs2\t' not in vcf_file.read_text()

def test_delete_returns_404_for_nonmatching_id(auth_client):
    r = auth_client.delete('/api/variants/?id=rs_nonexistent')
    assert r.status_code ==404

def test_delete_returns_400_without_id_param(auth_client):
    r = auth_client.delete('/api/variants/')
    assert r.status_code == 400

def test_delete_multiple_rows(auth_client):
    r = auth_client.delete('/api/variants/?id=rs1')
    assert r.status_code == 204
    assert not Variant.objects.filter(variant_id='rs1').exists()