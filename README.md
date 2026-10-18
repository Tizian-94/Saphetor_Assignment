# Saphetor_Assignment
Saphetor technical assignment


If the app appears to write successfully but the file is unchanged, run python manage.py shell → from django.conf import settings; print(settings.VCF_FILE_PATH). Verify the app's path matches the file you're inspecting.

data/*.vcf is gitignored. Copy your own VCF to data/sample.vcf, then run python manage.py load_vcf data/sample.vcf.