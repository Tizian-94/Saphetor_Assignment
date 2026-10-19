import pytest

from vcfparser.models import Variant

pytestmark = pytest.mark.usefixtures("vcf_file")

# content negation

def test_get_returns_json_by_default(api_client):
    r = api_client.get('/api/variants/')
    assert r.status_code == 200
    assert r['Content-Type'].startswith('application/json')
    body = r.json()
    assert body['count'] == 6
    assert len(body['results']) == 6

def test_get_returns_xml_when_accept_xml(api_client):
    r = api_client.get('/api/variants/', HTTP_ACCEPT='application/xml')
    assert r.status_code == 200
    assert r['Content-Type'].startswith('application/xml')
    assert b'<CHROM>chr1</CHROM>' in r.content

def test_get_returns_406_on_unacceptable_accept(api_client):
    r = api_client.get('/api/variants/', HTTP_ACCEPT='text/csv')
    assert r.status_code == 406

def test_get_falls_back_to_json_on_wildcard_accept(api_client):
    r = api_client.get('/api/variants/', HTTP_ACCEPT='*/*')
    assert r.status_code == 200
    assert r['Content-Type'].startswith('application/json')


# pagination

def test_get_pagination_shape(api_client):
    r = api_client.get('/api/variants/?page_size=2')
    body = r.json()
    assert body['count'] == 6
    assert len(body['results']) == 2
    assert body['next'] is not None
    assert body['previous'] is None

def test_get_pagination_previous_on_page_2(api_client):
    r = api_client.get('/api/variants/?page=2&page_size=2')
    body = r.json()
    assert body['previous'] is not None
    assert body['next'] is not None

# filter by ID

def test_get_filter_by_id_found(api_client):
    r = api_client.get('/api/variants/?id=rs2')
    assert r.status_code == 200
    body = r.json()
    assert body['count'] == 1
    assert body['results'][0]['ID'] == 'rs2'

def test_get_filter_by_id_multi_match(api_client):
    # if id appears twice must return both (rs1)
    r = api_client.get('/api/variants/?id=rs1')
    body = r.json()
    assert body['count'] == 2

def test_get_filter_by_id_not_found(api_client):
    r = api_client.get('/api/variants/?id=rs_nonexistent')
    assert r.status_code == 404

# ETAG

def test_get_response_includes_etag(api_client):
    r = api_client.get('/api/variants/')
    assert 'ETag' in r.headers
    assert r['ETag'].startswith('"')

def test_get_etag_if_none_match_returns_304(api_client):
    r1 = api_client.get('/api/variants/')
    etag = r1['ETag']
    r2 = api_client.get('/api/variants/', HTTP_IF_NONE_MATCH=etag)
    assert r2.status_code == 304

def test_get_etag_differs_for_different_accept(api_client):
    r_json = api_client.get('/api/variants/', HTTP_ACCEPT='application/json')
    r_xml = api_client.get('/api/variants/', HTTP_ACCEPT='application/xml')
    assert r_json['ETag'] != r_xml['ETag']

def test_get_etag_changes_when_file_changes(api_client, vcf_file):
    r1 = api_client.get('/api/variants/')
    etag1 = r1['ETag']

    with open(vcf_file, 'a') as f:
        f.write('chr1\t9999\trs_new\tA\tG\t.\t.\t.\n')

    r2 = api_client.get('/api/variants/', HTTP_IF_NONE_MATCH=etag1)
    #different mtime / size = new ETag. Must be 200 not 304
    assert r2.status_code == 200
    assert r2['ETag'] != etag1