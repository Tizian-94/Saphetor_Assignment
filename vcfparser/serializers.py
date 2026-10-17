from rest_framework import serializers

from vcfparser.models import Variant
from vcfparser.validators import ( ALLELE_VALIDATOR, CHROM_VALIDATOR, ID_VALIDATOR,)

class VariantSerializer(serializers.ModelSerializer):
    # Read only used for GET responses, format uses VCF uppercase field names mapped to lowercase attributes via source=
    CHROM = serializers.CharField(source="chrom", read_only=True)
    POS = serializers.IntegerField(source="pos", read_only=True)
    ID = serializers.CharField(source="variant_id", read_only=True)
    REF = serializers.CharField(source="ref",read_only=True)
    ALT = serializers.CharField(source="alt",read_only=True)

    class Meta:
        model = Variant
        fields = ["CHROM","POS","ID","REF","ALT"]

class VariantWriteSerializer(serializers.Serializer):
    # input serializer used for POST (create) and PUT (update) bodies, validates strictly.
    # 'source=' remaps uppercase to lowercase keys in 'validated_data' so that the layer can work with model-style names

    CHROM = serializers.CharField(
        max_length=64,
        source="chrom",
        validators=[CHROM_VALIDATOR],
    )
    POS = serializers.IntegerField(source="pos",min_value=1)
    ID = serializers.CharField(
        max_length=64,
        source="variant_id",
        validators =[ID_VALIDATOR],
    )
    REF = serializers.CharField(
        max_length=256,
        source="ref",
        validators = [ALLELE_VALIDATOR],
    )
    ALT = serializers.CharField(
        max_length = 256,
        source = "alt",
        validators = [ALLELE_VALIDATOR],
    )