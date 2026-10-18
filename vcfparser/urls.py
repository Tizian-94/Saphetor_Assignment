from django.urls import path
from vcfparser.views import VariantView

urlpatterns = [
    path('variants/', VariantView.as_view(), name='variant-list'),
]
