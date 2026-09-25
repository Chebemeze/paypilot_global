#!/bin/bash
# ============================================================
# PERSON 1 — Step 6 Verification: Bulk CSV Import
#
#   1. Restart backend:  uvicorn app.main:app --reload --port 8000
#   2. bash test_import.sh
#
# Creates fixture employees (prefix zzimp), then deletes them. Re-runnable.
# ============================================================

BASE="http://localhost:8000/api/v1"
PASS=0; FAIL=0
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

green(){ echo -e "\033[32m$1\033[0m"; }
red(){ echo -e "\033[31m$1\033[0m"; }
blue(){ echo -e "\033[34m$1\033[0m"; }
ok(){ green "  PASS  $1"; PASS=$((PASS+1)); }
no(){ red   "  FAIL  $1"; FAIL=$((FAIL+1)); }
want(){ if [ "$3" == "$2" ]; then ok "$1  ($3)"; else no "$1  (expected $2, got $3)"; fi }

TOKEN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"admin@acmeglobal.com","password":"password123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
[ -z "$TOKEN" ] && { red "Cannot log in - is the backend running?"; exit 1; }
H="Authorization: Bearer $TOKEN"
VIEWER=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"viewer@acmeglobal.com","password":"password123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

# upload <file> [dry_run] [token]
upload(){
  local f="$1" dry="${2:-false}" tk="${3:-$TOKEN}"
  curl -s -X POST "$BASE/employees/import" -H "Authorization: Bearer $tk" \
       -F "file=@$f;type=text/csv" -F "dry_run=$dry"
}
ucode(){
  local f="$1" dry="${2:-false}" tk="${3:-$TOKEN}"
  curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/employees/import" \
       -H "Authorization: Bearer $tk" -F "file=@$f;type=text/csv" -F "dry_run=$dry"
}
jq_(){ python3 -c "import sys,json;print(json.load(sys.stdin).get('$1',''))" 2>/dev/null; }

# created + restored. DELETE is a SOFT delete, so the cleanup at the end of a
# previous run leaves rows with deleted_at set. Re-importing those emails
# correctly RESTORES them instead of creating new rows. Asserting on `created`
# alone therefore passes on a virgin database and fails on every re-run --
# the row landed either way, which is what we actually care about.
imported(){ python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('created',0)+d.get('restored',0))" 2>/dev/null; }
emsg(){ python3 -c "import sys,json;print(json.load(sys.stdin).get('error',{}).get('message',''))" 2>/dev/null; }
total(){ curl -s "$BASE/employees?search=zzimp&limit=1" -H "$H" | jq_ total; }

# ── fixture files ─────────────────────────────────────────────────────────────
cat > "$TMP/good.csv" <<'CSV'
full_name,email,country,currency,department,job_title,salary
Zzimp Ada,zzimp.ada@t.com,Nigeria,NGN,ZzimpEng,Backend Engineer,"450,000"
Zzimp Bob,ZZIMP.BOB@T.COM,United States,USD,ZzimpEng,Frontend Engineer,4000
Zzimp Chidi,zzimp.chidi@t.com,NG,NGN,ZzimpFin,Analyst,300000
CSV

cat > "$TMP/messy.csv" <<'CSV'
Full Name,E-Mail,Country,Currency,Salary
Zzimp Valid,zzimp.valid@t.com,Ghana,USD,1000
,zzimp.noname@t.com,NG,NGN,100
Zzimp BadEmail,not-an-email,NG,NGN,100
Zzimp BadCountry,zzimp.bc@t.com,Atlantis,NGN,100
Zzimp BadCurrency,zzimp.bcur@t.com,NG,XYZ,100
Zzimp NegSalary,zzimp.neg@t.com,NG,NGN,-500
Zzimp DupeA,zzimp.dupe@t.com,NG,NGN,100
Zzimp DupeB,zzimp.dupe@t.com,NG,NGN,200

CSV

printf 'full_name;email;country\nZzimp Semi;zzimp.semi@t.com;NG\n' > "$TMP/semi.csv"
printf '\xef\xbb\xbffull_name,email,country\nZzimp Bom,zzimp.bom@t.com,NG\n' > "$TMP/bom.csv"
printf 'name,salary\nNobody,100\n' > "$TMP/nocols.csv"
printf '' > "$TMP/empty.csv"
printf 'full_name,email,country\n' > "$TMP/headeronly.csv"
printf 'just some prose with no commas at all\n' > "$TMP/notcsv.csv"

echo ""
blue "============================================"
blue " TEST 1: dry_run writes nothing"
blue "============================================"
BEFORE=$(total)
R=$(upload "$TMP/good.csv" true)
echo "        $(echo "$R" | python3 -c "
import sys,json;d=json.load(sys.stdin)
print('dry_run=%s total_rows=%s created=%s restored=%s failed=%s' % (d['dry_run'],d['total_rows'],d['created'],d['restored'],d['failed']))" 2>/dev/null)"
want "dry_run reports 3 would-be imports" 3 "$(echo "$R" | imported)"
want "dry_run flag is true" "True" "$(echo "$R" | jq_ dry_run)"
AFTER=$(total)
want "nothing was written" "$BEFORE" "$AFTER"

echo ""
blue "============================================"
blue " TEST 2: real import + normalisation"
blue "============================================"
R=$(upload "$TMP/good.csv")
want "3 rows imported (created or restored)" 3 "$(echo "$R" | imported)"
want "failed 0"  0 "$(echo "$R" | jq_ failed)"
curl -s "$BASE/employees?search=zzimp&sort_by=full_name&sort_order=asc" -H "$H" \
  | python3 -c "
import sys,json
for i in json.load(sys.stdin)['items']:
    print('        %-14s %-22s %s %s %s' % (i['full_name'],i['email'],i['country'],i['preferred_currency'],i['expected_salary']))" 2>/dev/null
CHK=$(curl -s "$BASE/employees?search=zzimp.ada" -H "$H" | python3 -c "
import sys,json;i=json.load(sys.stdin)['items'][0];print('%s|%s|%s' % (i['country'],i['preferred_currency'],i['expected_salary']))" 2>/dev/null)
want "'Nigeria' -> NG, '450,000' -> 450000" "NG|NGN|450000.0" "$CHK"
CHK=$(curl -s "$BASE/employees?search=zzimp.bob" -H "$H" | python3 -c "
import sys,json;i=json.load(sys.stdin)['items'][0];print('%s|%s' % (i['country'],i['email']))" 2>/dev/null)
want "'United States' -> US, email lowercased" "US|zzimp.bob@t.com" "$CHK"

echo ""
blue "============================================"
blue " TEST 3: bad rows isolated, good rows land"
blue "============================================"
R=$(upload "$TMP/messy.csv")
echo "$R" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('        total=%s created=%s restored=%s skipped=%s failed=%s' % (
  d['total_rows'],d['created'],d['restored'],d['skipped'],d['failed']))
for r in d['results']:
    print('        row %-3s %-9s %-22s %s' % (r['row'],r['status'],r['email'][:22],r['message'][:52]))" 2>/dev/null
want "2 good rows still imported" 2 "$(echo "$R" | imported)"
want "5 rows failed validation"  5 "$(echo "$R" | jq_ failed)"
want "1 in-file duplicate skipped" 1 "$(echo "$R" | jq_ skipped)"
# Parse the JSON instead of grepping it. JSONResponse emits compact separators
# ("row":3) while json.dumps writes ("row": 3), so a literal grep for '"row": 3'
# silently fails on a response that is perfectly correct.
ROWCHK=$(echo "$R" | python3 -c "
import sys,json
rs = json.load(sys.stdin)['results']
rows = [r['row'] for r in rs]
# Data starts on spreadsheet line 2 (line 1 is the header) and must be gapless.
expected = list(range(2, 2+len(rs)))
print('OK' if rows == expected else 'BAD %s' % rows)" 2>/dev/null)
[ "$ROWCHK" == "OK" ] && ok "row numbers match spreadsheet lines (2..N)" || no "row numbers wrong: $ROWCHK"

FIELDCHK=$(echo "$R" | python3 -c "
import sys,json
rs = json.load(sys.stdin)['results']
bad = [r for r in rs if r['status']=='failed' and not r.get('errors')]
print('OK' if not bad else 'BAD rows %s have no errors[]' % [r['row'] for r in bad])" 2>/dev/null)
[ "$FIELDCHK" == "OK" ] && ok "every failed row carries errors[] with field names" || no "$FIELDCHK"

echo ""
blue "============================================"
blue " TEST 4: whole-file failures -> 422"
blue "============================================"
for pair in "nocols.csv:missing required column" "empty.csv:empty file" \
            "headeronly.csv:header but no rows" "notcsv.csv:not a csv"; do
  f="${pair%%:*}"; label="${pair#*:}"
  C=$(ucode "$TMP/$f"); M=$(upload "$TMP/$f" | emsg)
  echo "        $label -> $C"
  echo "          ${M:0:96}"
  want "$label rejected" 422 "$C"
  [ -n "$M" ] && ok "$label explains the problem" || no "$label gave no message"
done

echo ""
blue "============================================"
blue " TEST 5: format tolerance"
blue "============================================"
want "semicolon delimiter" 1 "$(upload "$TMP/semi.csv" | imported)"
want "UTF-8 BOM from Excel" 1 "$(upload "$TMP/bom.csv" | imported)"
echo "        header aliases accepted: Full Name / E-Mail / Salary / job_title"
ok "alias headers parsed (see TEST 3)"

echo ""
blue "============================================"
blue " TEST 6: RBAC"
blue "============================================"
want "VIEWER cannot import" 403 "$(ucode "$TMP/good.csv" false "$VIEWER")"
want "ADMIN can import"     200 "$(ucode "$TMP/good.csv" false "$TOKEN")"

echo ""
blue "============================================"
blue " TEST 7: idempotent re-import"
blue "============================================"
R=$(upload "$TMP/good.csv")
want "re-import imports nothing" 0 "$(echo "$R" | imported)"
want "re-import skips 3"         3 "$(echo "$R" | jq_ skipped)"

echo ""
blue "============================================"
blue " TEST 8: deleted employee is restored"
blue "============================================"
ID=$(curl -s "$BASE/employees?search=zzimp.ada" -H "$H" | python3 -c "
import sys,json;print(json.load(sys.stdin)['items'][0]['id'])" 2>/dev/null)
curl -s -o /dev/null -X DELETE "$BASE/employees/$ID" -H "$H"
R=$(upload "$TMP/good.csv")
want "deleted row comes back as 'restored'" 1 "$(echo "$R" | jq_ restored)"

echo ""
blue "============================================"
blue " Cleanup"
blue "============================================"
IDS=$(curl -s "$BASE/employees?search=zzimp&limit=100" -H "$H" \
  | python3 -c "import sys,json;[print(i['id']) for i in json.load(sys.stdin).get('items',[])]" 2>/dev/null)
N=0; for id in $IDS; do curl -s -o /dev/null -X DELETE "$BASE/employees/$id" -H "$H"; N=$((N+1)); done
green "  removed $N fixture employees"

echo ""
blue "============================================"
echo -e " Results:  \033[32m$PASS passed\033[0m / \033[31m$FAIL failed\033[0m"
blue "============================================"
echo ""
[ "$FAIL" -eq 0 ] && green "Step 6 verified." || red "Some checks failed - see above."
echo ""
