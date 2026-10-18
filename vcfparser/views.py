#direct reference import for mock tests
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from vcfparser.models import Variant
from vcfparser.pagination import StandardResultsSetPagination
from vcfparser.permissions import BearerSecretPermission
from vcfparser.serializers import VariantSerializer, VariantWriteSerializer
from vcfparser.services import vcf_service

class VariantView(APIView):

    def get_permissions(self):
        # writes require the shared secret since GET is public, intentionally strict project default security
        if self.request.method == "GET":
            return [AllowAny()] #GET is public, post, put & delete require Authorization or 403
        return [BearerSecretPermission()]

    def get(self, request):
        vcf_service.ensure_fresh(str(settings.VCF_FILE_PATH))

        queryset = Variant.objects.all()

        variant_id = request.query_params.get('id')
        # if client sends ?id= for GET treat as filter by empty id (match nothing or return 404)
        if variant_id is not None:
            queryset = queryset.filter(variant_id=variant_id)
            if not queryset.exists():
                return Response(
                    {'detail':f"No variant with id '{variant_id}'"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = VariantSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        vcf_service.ensure_fresh(str(settings.VCF_FILE_PATH))

        serializer = VariantWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vcf_service.append_variant(serializer.validated_data, settings.VCF_FILE_PATH)
        return Response(status=status.HTTP_201_CREATED)

    def put(self, request):
        vcf_service.ensure_fresh(str(settings.VCF_FILE_PATH))

        variant_id = request.query_params.get('id')
        # if client sends ?id= for put/delete treat as unknown record to modify and return 400
        if not variant_id:
            return Response(
                {'detail': "'id' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VariantWriteSerializer(data=request.data)
        #validation happens before the service is called
        serializer.is_valid(raise_exception=True)

        modified = vcf_service.update_variants(
            variant_id, serializer.validated_data, settings.VCF_FILE_PATH
        )
        if modified == 0:
            return Response(
                {'detail': f"No variant with id '{variant_id}'."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_200_OK)

    def delete(self, request):
        vcf_service.ensure_fresh(str(settings.VCF_FILE_PATH))

        variant_id = request.query_params.get('id')
        # if client sends ?id= for mutation treat as malformed and return 400
        if not variant_id:
            return Response(
                {'detail':"'id' query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deleted = vcf_service.delete_variants(variant_id, settings.VCF_FILE_PATH)
        if deleted == 0:
            return Response(
                {'detail':f"No variant with id '{variant_id}'"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
