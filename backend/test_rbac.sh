#!/bin/bash
# ============================================================
# PERSON 1 — Step 2 Verification: RBAC + Session Endpoints
#
# Usage:
#   1. Restart backend:  uvicorn app.main:app --reload --port 8000
#   2. bash test_rbac.sh
# ============================================================

BASE="http://localhost:8000/api/v1"
PASS=0; FAIL=0

green(){ echo -e "\033[32m$1\033[0m"; }
red(){ echo -e "\033[31m$1\033[0m"; }
blue(){ echo -e "\033[34m$1\033[0m"; }

check(){
  if [ "$3" == "$2" ]; then green "  PASS  $1  (got $3)"; PASS=$((PASS+1));
  else red "  FAIL  $1  (expected $2, got $3)"; FAIL=$((FAIL+1)); fi
}

login(){
  curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$1\",\"password\":\"password123\"}" \
    | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null
}

echo ""
blue "=== Logging in as all three roles ==="
ADMIN=$(login admin@acmeglobal.com)
FINANCE=$(login finance@acmeglobal.com)
VIEWER=$(login viewer@acmeglobal.com)

for pair in "ADMIN:$ADMIN" "FINANCE:$FINANCE" "VIEWER:$VIEWER"; do
  name="${pair%%:*}"; tok="${pair#*:}"
  if [ -n "$tok" ]; then green "  got $name token"; else red "  FAILED to get $name token"; exit 1; fi
done

A="Authorization: Bearer $ADMIN"
F="Authorization: Bearer $FINANCE"
V="Authorization: Bearer $VIEWER"

body='{"full_name":"RBAC Test User","email":"rbac.test@example.com","country":"NG","preferred_currency":"NGN"}'
post(){ curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/employees" -H "$1" -H 'Content-Type: application/json' -d "$2"; }

echo ""
blue "============================================"
blue " TEST 1: login now returns expires_in"
blue "============================================"
EXP=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"admin@acmeglobal.com","password":"password123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('expires_in',0))")
if [ "$EXP" -gt 0 ] 2>/dev/null; then green "  PASS  expires_in = $EXP seconds"; PASS=$((PASS+1));
else red "  FAIL  expires_in missing"; FAIL=$((FAIL+1)); fi

echo ""
blue "============================================"
blue " TEST 2: everyone can READ employees"
blue "============================================"
check "ADMIN   GET /employees"   "200" "$(curl -s -o /dev/null -w '%{http_code}' -H "$A" "$BASE/employees")"
check "FINANCE GET /employees"   "200" "$(curl -s -o /dev/null -w '%{http_code}' -H "$F" "$BASE/employees")"
check "VIEWER  GET /employees"   "200" "$(curl -s -o /dev/null -w '%{http_code}' -H "$V" "$BASE/employees")"

echo ""
blue "============================================"
blue " TEST 3: VIEWER cannot write  (the old hole)"
blue "============================================"
check "VIEWER  POST /employees blocked" "403" "$(post "$V" "$body")"
check "VIEWER  DELETE /employees/fake blocked" "403" \
  "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$BASE/employees/fake-id" -H "$V")"
check "VIEWER  POST /employees/invite blocked" "403" \
  "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/employees/invite" -H "$V" -H 'Content-Type: application/json' -d "$body")"

echo ""
blue "============================================"
blue " TEST 4: FINANCE can create, cannot delete"
blue "============================================"
CREATED=$(curl -s -X POST "$BASE/employees" -H "$F" -H 'Content-Type: application/json' -d "$body")
NEW_ID=$(echo "$CREATED" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('employee',{}).get('id',''))" 2>/dev/null)
CREATED_STATUS=$(echo "$CREATED" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
if [ -n "$NEW_ID" ]; then green "  PASS  FINANCE created employee ($CREATED_STATUS: $NEW_ID)"; PASS=$((PASS+1));
else red "  FAIL  FINANCE could not create: $CREATED"; FAIL=$((FAIL+1)); fi

# Guard: without an id the URL becomes /employees/ which 307-redirects to the
# list endpoint, producing confusing failures unrelated to the actual test.
if [ -z "$NEW_ID" ]; then
  red "  SKIP  delete checks - no employee id to work with"; FAIL=$((FAIL+2))
else
  check "FINANCE DELETE blocked (admin only)" "403" \
    "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$BASE/employees/$NEW_ID" -H "$F")"

  echo ""
  blue "============================================"
  blue " TEST 5: ADMIN can delete"
  blue "============================================"
  check "ADMIN   DELETE employee" "200" \
    "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$BASE/employees/$NEW_ID" -H "$A")"
fi

echo ""
blue "============================================"
blue " TEST 6: 403 message is human readable"
blue "============================================"
MSG=$(curl -s -X POST "$BASE/employees" -H "$V" -H 'Content-Type: application/json' -d "$body" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('detail',''))" 2>/dev/null)
echo "        \"$MSG\""
if echo "$MSG" | grep -qi "role"; then green "  PASS  message explains the role problem"; PASS=$((PASS+1));
else red "  FAIL  unhelpful message"; FAIL=$((FAIL+1)); fi

echo ""
blue "============================================"
blue " TEST 7: POST /auth/refresh"
blue "============================================"
REFRESHED=$(curl -s -X POST "$BASE/auth/refresh" -H "$V")
NEWTOK=$(echo "$REFRESHED" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
if [ -n "$NEWTOK" ] && [ "$NEWTOK" != "$VIEWER" ]; then
  green "  PASS  got a NEW token"; PASS=$((PASS+1));
else red "  FAIL  refresh did not return a new token: $REFRESHED"; FAIL=$((FAIL+1)); fi

check "old token revoked after refresh" "401" \
  "$(curl -s -o /dev/null -w '%{http_code}' -H "$V" "$BASE/auth/me")"
check "new token works" "200" \
  "$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $NEWTOK" "$BASE/auth/me")"

echo ""
blue "============================================"
blue " TEST 8: POST /auth/logout"
blue "============================================"
LO="Authorization: Bearer $NEWTOK"
check "logout succeeds" "200" "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/auth/logout" -H "$LO")"
check "token dead after logout" "401" "$(curl -s -o /dev/null -w '%{http_code}' -H "$LO" "$BASE/auth/me")"

echo ""
blue "============================================"
blue " TEST 9: POST /auth/change-password"
blue "============================================"
CP=$(login viewer@acmeglobal.com)
CPH="Authorization: Bearer $CP"
cp_call(){ curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/auth/change-password" \
  -H "$CPH" -H 'Content-Type: application/json' -d "$1"; }

check "wrong current password" "401" "$(cp_call '{"current_password":"nope","new_password":"newpass123"}')"
check "new password too short"  "422" "$(cp_call '{"current_password":"password123","new_password":"abc"}')"
check "same as current"         "422" "$(cp_call '{"current_password":"password123","new_password":"password123"}')"
check "valid change"            "200" "$(cp_call '{"current_password":"password123","new_password":"newpass123"}')"
check "token revoked after change" "401" "$(curl -s -o /dev/null -w '%{http_code}' -H "$CPH" "$BASE/auth/me")"

# log in with the NEW password, then restore the original so re-runs work
NEW_LOGIN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"viewer@acmeglobal.com","password":"newpass123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
if [ -n "$NEW_LOGIN" ]; then green "  PASS  can log in with the new password"; PASS=$((PASS+1));
else red "  FAIL  new password does not work"; FAIL=$((FAIL+1)); fi

curl -s -o /dev/null -X POST "$BASE/auth/change-password" \
  -H "Authorization: Bearer $NEW_LOGIN" -H 'Content-Type: application/json' \
  -d '{"current_password":"newpass123","new_password":"password123"}'
echo "        (restored viewer password to password123)"

echo ""
blue "============================================"
echo -e " Results:  \033[32m$PASS passed\033[0m / \033[31m$FAIL failed\033[0m"
blue "============================================"
echo ""
[ "$FAIL" -eq 0 ] && green "Step 2 verified." || red "Some checks failed - see above."
echo ""
