#!/bin/bash
# ============================================================
# PERSON 1 — Step 4 Verification: Unified Error Responses
#
#   1. Restart backend:  uvicorn app.main:app --reload --port 8000
#   2. bash test_errors.sh
# ============================================================

BASE="http://localhost:8000/api/v1"
PASS=0; FAIL=0

green(){ echo -e "\033[32m$1\033[0m"; }
red(){ echo -e "\033[31m$1\033[0m"; }
blue(){ echo -e "\033[34m$1\033[0m"; }
ok(){ green "  PASS  $1"; PASS=$((PASS+1)); }
no(){ red   "  FAIL  $1"; FAIL=$((FAIL+1)); }

TOKEN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"admin@acmeglobal.com","password":"password123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
[ -z "$TOKEN" ] && { red "Cannot log in - is the backend running?"; exit 1; }
H="Authorization: Bearer $TOKEN"

VIEWER=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"viewer@acmeglobal.com","password":"password123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

# envelope <label> <expected_status> <expected_code> <curl args...>
envelope(){
  local label="$1" want_status="$2" want_code="$3"; shift 3
  local body status
  body=$(curl -s "$@")
  status=$(curl -s -o /dev/null -w '%{http_code}' "$@")
  local parsed
  parsed=$(echo "$body" | python3 -c "
import sys,json
try: d=json.load(sys.stdin)
except Exception: print('NOTJSON||'); sys.exit()
e=d.get('error') or {}
print('%s|%s|%s' % (e.get('code',''), 'Y' if isinstance(d.get('detail'),str) else 'N', 'Y' if e.get('request_id') else 'N'))
" 2>/dev/null)
  local code="${parsed%%|*}"; local rest="${parsed#*|}"
  local legacy="${rest%%|*}"; local rid="${rest##*|}"

  echo "        $status  code=$code  detail=str:$legacy  request_id:$rid"
  [ "$status" == "$want_status" ] && ok "$label status $want_status" || no "$label status (got $status want $want_status)"
  [ "$code" == "$want_code" ] && ok "$label code=$want_code" || no "$label code (got '$code' want '$want_code')"
  [ "$legacy" == "Y" ] && ok "$label keeps legacy .detail string" || no "$label lost .detail"
  [ "$rid" == "Y" ] && ok "$label has request_id" || no "$label missing request_id"
}

echo ""
blue "============================================"
blue " TEST 1: every error uses the same envelope"
blue "============================================"
echo "  -- 404 unknown route"
envelope "404" 404 NOT_FOUND "$BASE/this-route-does-not-exist"
echo "  -- 401 no token"
envelope "401" 401 UNAUTHENTICATED "$BASE/employees"
echo "  -- 403 wrong role"
envelope "403" 403 FORBIDDEN -X POST "$BASE/employees" -H "Authorization: Bearer $VIEWER" \
  -H 'Content-Type: application/json' -d '{"full_name":"A B","email":"x@y.com","country":"NG"}'
echo "  -- 404 missing employee"
envelope "404 employee" 404 NOT_FOUND "$BASE/employees/does-not-exist" -H "$H"
echo "  -- 405 wrong method"
envelope "405" 405 METHOD_NOT_ALLOWED -X PATCH "$BASE/auth/login"
echo "  -- 422 validation"
envelope "422" 422 VALIDATION_ERROR -X POST "$BASE/employees" -H "$H" \
  -H 'Content-Type: application/json' -d '{"full_name":"A B","email":"bad","country":"NG"}'

echo ""
blue "============================================"
blue " TEST 2: validation errors carry .fields"
blue "============================================"
OUT=$(curl -s -X POST "$BASE/employees" -H "$H" -H 'Content-Type: application/json' \
  -d '{"email":"bad-email","country":"Nigeria","preferred_currency":"XYZ","expected_salary":-1}')
echo "$OUT" | python3 -c "
import sys,json
d=json.load(sys.stdin); f=d.get('error',{}).get('fields')
if not f: print('  NO FIELDS'); sys.exit(1)
for x in f: print('        %-20s %s' % (x['field'], x['message']))
print('COUNT=%d' % len(f))
" > /tmp/_f.txt 2>/dev/null
cat /tmp/_f.txt | grep -v COUNT
N=$(grep -o 'COUNT=[0-9]*' /tmp/_f.txt | cut -d= -f2)
[ "${N:-0}" -ge 4 ] && ok "got $N per-field errors" || no "expected >=4 field errors, got ${N:-0}"
echo "$OUT" | grep -q '"loc"' && no "raw pydantic 'loc' still leaking" || ok "no raw pydantic 'loc' - flattened to .field"
echo "$OUT" | grep -q 'Value error,' && no "'Value error,' prefix not stripped" || ok "'Value error,' prefix stripped"

echo ""
blue "============================================"
blue " TEST 3: X-Request-ID header matches body"
blue "============================================"
HDR=$(curl -s -D - -o /tmp/_b.txt "$BASE/employees" | grep -i '^x-request-id' | tr -d '\r' | awk '{print $2}')
BID=$(python3 -c "import json;print(json.load(open('/tmp/_b.txt'))['error'].get('request_id',''))" 2>/dev/null)
echo "        header=$HDR   body=$BID"
[ -n "$HDR" ] && [ "$HDR" == "$BID" ] && ok "header and body ids match" || no "ids differ or missing"

echo ""
blue "============================================"
blue " TEST 4: 401 keeps its WWW-Authenticate header"
blue "============================================"
curl -s -D - -o /dev/null "$BASE/employees" -H 'Authorization: Bearer garbage' \
  | grep -qi 'www-authenticate' && ok "WWW-Authenticate preserved" || no "WWW-Authenticate was dropped"

echo ""
blue "============================================"
blue " TEST 5: success responses are NOT wrapped"
blue "============================================"
curl -s "$BASE/employees" -H "$H" | grep -q '"items"' && ok "200 body unchanged (no error envelope)" || no "success response was altered"
curl -s "$BASE/auth/me" -H "$H" | grep -q '"email"' && ok "/auth/me unchanged" || no "/auth/me altered"

echo ""
blue "============================================"
blue " TEST 6: nothing internal leaks"
blue "============================================"
ALL=$(curl -s "$BASE/employees/does-not-exist" -H "$H"; curl -s "$BASE/nope"; \
      curl -s -X POST "$BASE/employees" -H "$H" -H 'Content-Type: application/json' -d '{"email":"x"}')
LEAK=""
for w in Traceback sqlalchemy SELECT "site-packages" ".py\"" password; do
  echo "$ALL" | grep -qi "$w" && LEAK="$LEAK $w"
done
[ -z "$LEAK" ] && ok "no tracebacks / SQL / file paths in error bodies" || no "leaked:$LEAK"

echo ""
blue "============================================"
echo -e " Results:  \033[32m$PASS passed\033[0m / \033[31m$FAIL failed\033[0m"
blue "============================================"
echo ""
[ "$FAIL" -eq 0 ] && green "Step 4 verified." || red "Some checks failed - see above."
echo ""
