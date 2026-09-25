#!/bin/bash
# ============================================================
# PERSON 1 — Auth Verification Script
# Proves JWT protection is working on every endpoint.
#
# Usage:
#   1. Start backend:  uvicorn app.main:app --reload --port 8000
#   2. In a new terminal:  bash test_auth.sh
# ============================================================

BASE="http://localhost:8000/api/v1"
PASS=0
FAIL=0

green() { echo -e "\033[32m$1\033[0m"; }
red()   { echo -e "\033[31m$1\033[0m"; }
blue()  { echo -e "\033[34m$1\033[0m"; }

check() {
  local label="$1" expected="$2" actual="$3"
  if [ "$actual" == "$expected" ]; then
    green "  PASS  $label  (got $actual)"; PASS=$((PASS+1))
  else
    red   "  FAIL  $label  (expected $expected, got $actual)"; FAIL=$((FAIL+1))
  fi
}

code() { curl -s -o /dev/null -w "%{http_code}" "$@"; }

echo ""
blue "============================================"
blue " TEST 1: No token  ->  must be 401"
blue "============================================"

for ep in "/employees" "/dashboard/summary" "/payroll/batches" "/cards" "/forecast/payroll-runway" "/webhooks/events" "/auth/me"; do
  c=$(code "$BASE$ep")
  if [ "$c" == "401" ]; then
    green "  PASS  GET $ep -> 401 (got $c)"; PASS=$((PASS+1))
  elif [ "$c" == "403" ]; then
    red   "  FAIL  GET $ep returned 403 - should be 401 for a MISSING token"; FAIL=$((FAIL+1))
  else
    red   "  FAIL  GET $ep NOT PROTECTED (got $c)"; FAIL=$((FAIL+1))
  fi
done

echo ""
blue "============================================"
blue " TEST 2: Garbage token  ->  must be 401"
blue "============================================"

check "GET /employees with fake token" "401" \
  "$(code -H 'Authorization: Bearer not-a-real-token' "$BASE/employees")"
check "GET /auth/me with fake token" "401" \
  "$(code -H 'Authorization: Bearer abc.def.ghi' "$BASE/auth/me")"

echo ""
blue "============================================"
blue " TEST 3: Bad credentials  ->  must be 401"
blue "============================================"

check "POST /auth/login wrong password" "401" \
  "$(code -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
     -d '{"email":"admin@acmeglobal.com","password":"WRONG"}')"

echo ""
blue "============================================"
blue " TEST 4: Real login  ->  must be 200 + token"
blue "============================================"

LOGIN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"admin@acmeglobal.com","password":"password123"}')

TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
  green "  PASS  Login returned a token"; PASS=$((PASS+1))
  echo "        ${TOKEN:0:45}..."
else
  red "  FAIL  Login did not return a token"; FAIL=$((FAIL+1))
  echo "        Response: $LOGIN"
  echo ""
  red "  Seed the database first:  python -m app.seed"
  exit 1
fi

echo ""
blue "============================================"
blue " TEST 5: Valid token  ->  must be 200"
blue "============================================"

AUTH="Authorization: Bearer $TOKEN"
for ep in "/auth/me" "/employees" "/dashboard/summary" "/payroll/batches" "/cards" "/forecast/payroll-runway" "/webhooks/events"; do
  check "GET $ep with valid token" "200" "$(code -H "$AUTH" "$BASE$ep")"
done

echo ""
blue "============================================"
blue " TEST 6: Public endpoints stay public"
blue "============================================"

check "GET /health (no auth needed)" "200" "$(code http://localhost:8000/health)"
check "GET / (no auth needed)"       "200" "$(code http://localhost:8000/)"

echo ""
blue "============================================"
echo -e " Results:  \033[32m$PASS passed\033[0m / \033[31m$FAIL failed\033[0m"
blue "============================================"
echo ""

[ "$FAIL" -eq 0 ] && green "All auth checks passed. Task 1 verified." || red "Some checks failed - see above."
echo ""
