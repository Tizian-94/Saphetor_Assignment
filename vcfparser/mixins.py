import hashlib
import os

from django.conf import settings
from django.http import HttpResponseNotModified

class ETagMixin:
    def dispatch(self,request, *args, **kwargs):
        if request.method in ('GET','HEAD'):
            etag = self._compute_etag(request)

            if self._if_none_match_matches(request,etag):
                response = HttpResponseNotModified()
                response['ETag'] = f'"{etag}"'
                return response

            response = super().dispatch(request, *args, **kwargs)
            response['Etag'] = f'"{etag}"'
            return response

        return super().dispatch(request, *args, **kwargs)

    def _compute_etag(self, request):
        parts = [
            request.get_full_path(),
            request.headers.get('Accept',''),
        ]
        try:
            stat = os.stat(settings.VCF_FILE_PATH)
            parts.append(str(stat.st_mtime))
            parts.append(str(stat.st_size))
        except OSError:
            parts.append('missing')

        return hashlib.sha1('|'.join(parts).encode('utf-8')).hexdigest()

    def _if_none_match_matches(self, request, etag):
        header = request.headers.get('If-None-Match', '').strip()
        if not header:
            return False
        if header == '*':
            return True
        candidates = header.replace('W/', '').replace('"','').split(',')
        return etag in [c.strip() for c in candidates]