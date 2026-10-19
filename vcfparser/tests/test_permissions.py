import pytest

from django.test import RequestFactory, override_settings
from vcfparser.permissions import BearerSecretPermission

@pytest.fixture
def perm():
    return BearerSecretPermission()

@pytest.fixture
def rf():
    return RequestFactory()

def test_denies_missing_header(perm, rf, settings):
    r = rf.post('/x')
    assert perm.has_permission(r, None) is False

def test_denies_wrong_secret(perm, rf, settings):
    r = rf.post('/x', HTTP_AUTHORIZATION='wrong')
    assert perm.has_permission(r, None) is False

def test_allows_correct_secret(perm, rf, settings):
    r = rf.post('/x', HTTP_AUTHORIZATION=settings.API_SECRET)
    assert perm.has_permission(r, None) is True

@override_settings(API_SECRET='')
def test_denies_when_secret_unset(perm,rf):
    r = rf.post('/x')
    assert perm.has_permission(r,None) is False

def test_denies_non_ascii_header(perm, rf, settings):
    r = rf.post('/x', HTTP_AUTHORIZATION='é')
    assert perm.has_permission(r,None) is False