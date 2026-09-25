#!/bin/bash
# ============================================================
# PERSON 1 — Step 3 Verification: Input Validation
#
#   1. Restart backend:  uvicorn app.main:app --reload --port 8000
#   2. bash test_validation.sh
# ============================================================

BASE="http://localhost:8000/api/v1"
PASS=0; FAIL=0

green(){ echo -e "\033[32m$1\033[0m"; }
red(){ echo -e "\033[31m$1\033[0m"; }
blue(){ echo -e "\033[34m$1\033[0m"; }

check(){ if [ "$3" == "$2" ]; then green "  PASS  $1  (got $3)"; PASS=$((PASS+1));
         else red "  FAIL  $1  (expected $2, got $3)"; FAIL=$((FAIL+1)); fi }

TOKEN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"admin@acmeglobal.com","password":"password123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
[ -z "$TOKEN" ] && { red "Could not log in. Is the backend running?"; exit 1; }
H="Authorization: Bearer $TOKEN"

post(){ curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/employees" -H "$H" -H 'Content-Type: application/json' -d "$1"; }
why(){ curl -s -X POST "$BASE/employees" -H "$H" -H 'Content-Type: application/json' -d "$1" \
  | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin).get('detail')
    if isinstance(d,list): print(' | '.join(f\"{'.'.join(str(i) for i in e.get('loc',[])[1:])}: {e.get('msg')}\" for e in d))
    else: print(d)
except Exception: print('(unparseable)')" 2>/dev/null; }

echo ""
blue "============================================"
blue " TEST 1: Garbage input is now rejected (422)"
blue "============================================"
check "invalid email"        "422" "$(post '{"full_name":"Test User","email":"not-an-email","country":"NG"}')"
check "country not ISO code" "422" "$(post '{"full_name":"Test User","email":"a@b.com","country":"Nigeria"}')"
check "unsupported currency" "422" "$(post '{"full_name":"Test User","email":"a@b.com","country":"NG","preferred_currency":"XYZ"}')"
check "salary is a string"   "422" "$(post '{"full_name":"Test User","email":"a@b.com","country":"NG","expected_salary":"banana"}')"
check "negative salary"      "422" "$(post '{"full_name":"Test User","email":"a@b.com","country":"NG","expected_salary":-5000}')"
check "name too short"       "422" "$(post '{"full_name":"A","email":"a@b.com","country":"NG"}')"
check "name over 100 chars"  "422" "$(post "{\"full_name\":\"$(printf 'X%.0s' {1..101})\",\"email\":\"a@b.com\",\"country\":\"NG\"}")"
check "missing email+country" "422" "$(post '{"full_name":"Test User"}')"
check "empty body"           "422" "$(post '{}')"

echo ""
blue "============================================"
blue " TEST 2: Errors say WHICH field and WHY"
blue "============================================"
for payload in \
  '{"full_name":"Test User","email":"not-an-email","country":"NG"}' \
  '{"full_name":"Test User","email":"a@b.com","country":"Nigeria"}' \
  '{"full_name":"Test User","email":"a@b.com","country":"NG","preferred_currency":"XYZ"}'
do
  MSG=$(why "$payload")
  echo "        $MSG"
  if [ -n "$MSG" ] && [ "$MSG" != "(unparseable)" ]; then PASS=$((PASS+1)); green "  PASS  message is specific";
  else FAIL=$((FAIL+1)); red "  FAIL  no useful message"; fi
done

echo ""
blue "============================================"
blue " TEST 3: Valid input is normalised + 201"
blue "============================================"
RES=$(curl -s -X POST "$BASE/employees" -H "$H" -H 'Content-Type: application/json' \
  -d '{"full_name":"  Step3 Tester  ","email":"  STEP3@Acme.COM ","country":"ng","preferred_currency":"ngn","department":"   ","expected_salary":450000}')
CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/employees" -H "$H" -H 'Content-Type: application/json' \
  -d '{"full_name":"Step3 Tester2","email":"step3b@acme.com","country":"ng"}')
check "create returns 201 Created" "201" "$CODE"
echo "        status field: $(echo "$RES" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))" 2>/dev/null)  (created or restored are both valid)"

echo "$RES" | python3 -c "
import sys,json
d=json.load(sys.stdin).get('employee',{})
checks=[('email lowercased',d.get('email')=='step3@acme.com',d.get('email')),
        ('name trimmed',d.get('full_name')=='Step3 Tester',d.get('full_name')),
        ('country upper',d.get('country')=='NG',d.get('country')),
        ('currency upper',d.get('preferred_currency')=='NGN',d.get('preferred_currency')),
        ('blank dept -> null',d.get('department') is None,d.get('department'))]
for label,ok,val in checks:
    print(('  PASS  ' if ok else '  FAIL  ')+label+'  -> '+repr(val))
" 
NORM_OK=$(echo "$RES" | python3 -c "
import sys,json;d=json.load(sys.stdin).get('employee',{})
print(sum([d.get('email')=='step3@acme.com',d.get('full_name')=='Step3 Tester',d.get('country')=='NG',d.get('preferred_currency')=='NGN',d.get('department') is None]))" 2>/dev/null)
PASS=$((PASS+${NORM_OK:-0})); FAIL=$((FAIL+$((5-${NORM_OK:-0}))))

NEW_ID=$(echo "$RES" | python3 -c "import sys,json;print(json.load(sys.stdin).get('employee',{}).get('id',''))" 2>/dev/null)
if [ -z "$NEW_ID" ]; then
  red "  ABORT  create did not return an employee id:"; echo "         $RES"
  red "         (later tests would hit /employees/ and 307-redirect)"; exit 1
fi

echo ""
blue "============================================"
blue " TEST 4: Duplicate email -> 409"
blue "============================================"
check "same email again" "409" "$(post '{"full_name":"Someone Else","email":"step3@acme.com","country":"NG"}')"

echo ""
blue "============================================"
blue " TEST 5: PUT is a partial update"
blue "============================================"
put(){ curl -s -o /dev/null -w '%{http_code}' -X PUT "$BASE/employees/$NEW_ID" -H "$H" -H 'Content-Type: application/json' -d "$1"; }
check "update only department" "200" "$(put '{"department":"Engineering"}')"
check "empty update body -> 400" "400" "$(put '{}')"
check "invalid email on update -> 422" "422" "$(put '{"email":"bad"}')"

KEPT=$(curl -s "$BASE/employees/$NEW_ID" -H "$H" \
  | python3 -c "import sys,json;d=json.load(sys.stdin)['employee'];print(d.get('full_name'),'|',d.get('department'))" 2>/dev/null)
echo "        after partial update: $KEPT"
if echo "$KEPT" | grep -q "Step3 Tester | Engineering"; then
  green "  PASS  omitted fields were preserved"; PASS=$((PASS+1))
else red "  FAIL  partial update clobbered other fields"; FAIL=$((FAIL+1)); fi

echo ""
blue "============================================"
blue " TEST 6: Cleanup"
blue "============================================"
check "delete test employee" "200" "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$BASE/employees/$NEW_ID" -H "$H")"
ID2=$(curl -s "$BASE/employees?search=step3b" -H "$H" | python3 -c "
import sys,json;i=json.load(sys.stdin).get('items',[]);print(i[0]['id'] if i else '')" 2>/dev/null)
[ -n "$ID2" ] && curl -s -o /dev/null -X DELETE "$BASE/employees/$ID2" -H "$H" && echo "        (removed second test row)"

echo ""
blue "============================================"
echo -e " Results:  \033[32m$PASS passed\033[0m / \033[31m$FAIL failed\033[0m"
blue "============================================"
echo ""
[ "$FAIL" -eq 0 ] && green "Step 3 verified." || red "Some checks failed - see above."
echo ""
