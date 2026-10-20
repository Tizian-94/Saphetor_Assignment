# Saphetor_Assignment
Saphetor technical assignment

This is a Django + Django REST Framework project that does API serving for a VCF file over HTTP, it exposes CHROM, POS, ID, REF and ALT with JSON/XML negotiation, pagination and ETag cacheing as requested by the assignment.
Additionally it also contains the optional assignment possibility of CRUD editing the records in the loaded VCF file.
The design principle holds the file as the primary source of truth, while it does use SQLite for better record manipulation with built in Django ORM it acts mostly as an indexed cache for faster reads.

## What is covered in the project:

- GET paginated variants with next and previous (PageNumberPagination, '?page=N')
- Accepts json and xml, the fallback is json else it returns 406 via DRF renderers
- Etag + If-None-Match returns 304 (ETagMixin, SHA-1 over URL + Accept + file stat)
- querystring filter '?id=' returns 404 if no match is found
- auth requiring POST that appends a variant on success returns 201, on failure 403
- Validation on POST with Regex validators
- PUT updates by id where '?id=' returns 200 on success, 400 if "?id=" is missing and 404 if no rows match. Preserves the QUAL, FILTER, INFO and sample columns
- DELETE by '?id=' returns 204 on success, 400 if the id "?id=" is missing and 404 if no rows match.
- 98 tests are created using Pytest (ran with the command "pytest -v") all successful ~1.5 sec

## quickstart guide

Requires python 3.11 or later

```bash
git clone https://github.com/Tizian-94/Saphetor_Assignment.git
cd Saphetor_Assignment

python -m venv env
# Windows: env\Scripts\activate
# macOS/Linux: source env/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env - set DJANGO_SECRET_KEY and API_SECRET provided

# vcf file name is set to use sample.vcf, you can change it in .env (settings.py uses also sample.vcf for VCF_FILE_PATH fallback if VCF_FILE_PATH is unset in .env)
cp /path/to/name.vcf data/sample.vcf

python manage.py migrate
python manage.py load_vcf data/sample.vcf --force
python manage.py runserver

# verify:
curl http://localhost:8000/api/variants/

# running the tests:
pytest -v
```
## API reference
the base path is /api/variants/

GET /api/variants/ is a public, paginated list of variants. The accepted query parameters are: "?page=N" to change page number (default = 1), "?page_size=N" to change items per page (max 100, default 20) and "?id=rs123" filter by VCF ID
The default header values are application/json which is also used as fallback for */*, XML is also supported but anything else returns a 406
An id (?id=) with no matches will return 404 and matching "If-None-Match" header leads to 304 with no body

Response example:
{
  "count": 202463,
  "next": "http://localhost:8000/api/variants/?page=2",
  "previous": null,
  "results": [
    {"CHROM": "chr1", "POS": 12783, "ID": "rs62635284", "REF": "G", "ALT": "A"}
  ]
}

POST /api/variants/ require Authorization: "API_SECRET", it returns 201 on success, 400 on validation failure or 403 with an invalid auth
body example:
{"CHROM": "chr1", "POS": 1000, "ID": "rs123", "REF": "A", "ALT": "G"}

PUT /api/variants/?id=rs123 also require auth, it updates all the rows matching id "?id=" and has the same body shape as POST.
It returns 200 on success, 400 if the "?id=" is missing or body is invalid, 404 if no rows match and 403 without a valid auth

DELETE /api/variants/?id=rs123 requires auth as well, it deletes all rows matching the "?id=".
It returns 204 on success, 400 if "?id=" is missing, 404 if no rows match and 403 without a valid auth

## Assumptions

- The project is designed assuming the uploaded file follows the standard VCF column order: CHROM, POS, ID, REF, ALT are the fields 1-5 tab separated which is also required by the VCF spec.
- The Header lines start with a "#" and the body starts at the firs line not starting with a "#", universal newlines are used.
- INFO, FORMAT and sample columns are preserved verbatim in 'raw_line' but arent parsed, additional columns after position 5 are tolerated.
- The file size is assumed manageable in memory (sqlite cache)

## Design Choices

### File vs DB:
I chose to go with the file being the true source and the SQLite database to hold an indexed mirror for a faster reading of records, on every request ensure_fresh() compares the file s metadata (size and time) against the values stored in VcfHeader. If size or mtime differ the cache is rebuilt from the file.
An alternative approach would be to use what is loaded into the DB as the source but since in the task it is written as the API manipulates data based on the contents of a VCF file so i didnt wish to stray from the course.

### Storage:
From what i researched and saw in the sample vcf file i understood that each Variant should store two separate representations of the same data:
1) an indexed list of fields for querying (chrom, pos, variant_id, ref and alt)
2) the full original line (raw_line)

This is done because PUT and DELETE shouldnt corrupt the trailing columns (QUAL, FILTER, INFO, FORMAT, sample data) so rebuilding raw_line from only 5 fields would cause data loss so raw_line is verbatim for rapresentation and the structured fields are for querying

### Why uppercase:
The api accepts and returns CHROM, POS, ID, REF and ALT because it matches the provided VCF spec and the example in the assignment. Internally the model uses lowercase fields with DRF: serializer.CharField(source='chrom')

### Permission design:
The default project security is BearerSecretPermission and any new endpoint added without explicit get_permissions() requires auth by default, only GET is set to AllowAny.
This ensures that data can be shown but not interacted with directly unless specified.

### Compare_digest:
The Authorization header is compared to settings.API_SECRET using secrets.compare_digest and not == which can sometimes leak information on character mismatch, compare_digest runs in constant time.
If the API_SECRET field is empty every request will be denied.

### Writes:
For POST i used a simple append, this choice was a design tradeoff because of speed, i should have maybe have used fh.flush(); and os.fsync(fh.fileno()) for better security but depending on file size this may have been unacceptably slow for a test assignment.
IMPORTANT NOTE: Due to using append, if the process dies mid write it may leave a truncated line

For PUT and DELETE the rewrite is done by using a temp file together with os.replace() Atomic on POSIX and Windows, slower but more accurate. Here the time processing longer is more acceptable because these operations are not usually done en masse

### Transactions (PUT & DELETE):
PUT and DELETE wrap DB changes and rewrite_vcf() in transaction.atomic() meaning that if the file write fails because of a full disk or missing permissions the DB will actually roll back, without this a failed rewrite would leave the DB and file out of sync.
POST is not wrapped, if the file append succeds but the DB insert fails the fingerprint isnt updated so the next ensure_fresh() rebuilds the DB from the file and the row appears. If the client saw an error for a POST that didnt apply correctly in case of a retry it would create a duplicate. (limitation)

### ETag:
The custom ETagMixin computes SHA-1 over the full request path and query string, the Accpt header and the file s mtime/size. If If-None-Match matches the current ETag the mixin will return 304 before permissions, before acces and before any file reads because the task's requirement explicitly states "avoid any other processing".
Each hash input has a different Etag outcome:
-if URL differs we get a different page/representation
-if the Accept differs we get a different body (JSON or XML)
-If mtime/size of file differs we get different data

### Line endings:
The VCF spec requires "\n" but Windows editors (like my own) produce "\r\n" which caused me a lot of pain to figure out so now the loader reads with universal newlines.

## Example use cases (in order)
after setting up the project and running the development server with python manage.py runserver, in another powershell terminal:

First, load the secret from `.env` into a PowerShell variable:

```powershell
$secret = ((Get-Content .env | Where-Object { $_ -match '^API_SECRET=' }) -replace '^API_SECRET=', '').Trim()
Write-Host "Secret loaded: $($secret.Length) chars"
```


1) Fetch Variants by ID (ensure id exists):

Replace `rs62635284` with any ID present in your loaded file:

```powershell
curl.exe -s "http://localhost:8000/api/variants/?id=rs62635284"
```

2) ETag + 304 try block:

```powershell
$r1 = Invoke-WebRequest -Uri "http://localhost:8000/api/variants/" -UseBasicParsing

$etag = $r1.Headers['ETag']

Write-Host "ETag: $etag"

try {
    $r2 = Invoke-WebRequest -Uri "http://localhost:8000/api/variants/" `
        -Headers @{ "If-None-Match" = $etag } -UseBasicParsing
    Write-Host "Status: $($r2.StatusCode)"
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)"
}
```

Expected: ETag printed, then `Status: 304`.

3) Content negotiation (returns XML)

```powershell
curl.exe -s -H "Accept: application/xml" "http://localhost:8000/api/variants/?id=rs62635284"
```

4) POST a new variant:

```powershell
curl.exe -s -w "`nStatus: %{http_code}`n" -X POST http://localhost:8000/api/variants/ `
    -H "Content-Type: application/json" `
    -H "Authorization: $secret" `
    -d '{\"CHROM\":\"chr1\",\"POS\":5000000,\"ID\":\"rs999999\",\"REF\":\"A\",\"ALT\":\"G\"}'

curl.exe -s "http://localhost:8000/api/variants/?id=rs999999"
```

Expected: `Status: 201`, then the created row.

5) PUT preserving trailing columns:

Expected: `Status: 200`, `REF` changed from `A` to `C` in both the API response and the file line (trailing `.` columns preserved).

```powershell
curl.exe -s "http://localhost:8000/api/variants/?id=rs999999"

curl.exe -s -w "`nStatus: %{http_code}`n" -X PUT "http://localhost:8000/api/variants/?id=rs999999" `
    -H "Content-Type: application/json" `
    -H "Authorization: $secret" `
    -d '{\"CHROM\":\"chr1\",\"POS\":5000000,\"ID\":\"rs999999\",\"REF\":\"C\",\"ALT\":\"G\"}'

curl.exe -s "http://localhost:8000/api/variants/?id=rs999999"

Select-String "rs999999" "data/sample.vcf"
```

6) DELETE:

```powershell
curl.exe -s -w "`nStatus: %{http_code}`n" -X DELETE "http://localhost:8000/api/variants/?id=rs999999" `
    -H "Authorization: $secret"

curl.exe -s -w "`nStatus: %{http_code}`n" "http://localhost:8000/api/variants/?id=rs999999"
```

Expected: `Status: 204`, then `Status: 404`.

7) Auth gate:

```powershell
curl.exe -s -w "`nStatus: %{http_code}`n" -X POST http://localhost:8000/api/variants/ `
    -H "Content-Type: application/json" `
    -H "Authorization: wrong-secret" `
    -d '{\"CHROM\":\"chr1\",\"POS\":1,\"ID\":\"rs1\",\"REF\":\"A\",\"ALT\":\"G\"}'
```

Expected: `{"detail":"Invalid or missing Authorization header"}`, then `Status: 403`.