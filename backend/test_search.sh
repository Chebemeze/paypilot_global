#!/bin/bash
# ============================================================
# PERSON 1 — Step 5 Verification: Search, Filtering, Sorting
#
#   1. Restart backend:  uvicorn app.main:app --reload --port 8000
#   2. bash test_search.sh
#
# Creates its own fixture employees (prefix zzstep5), tests against them,
# then deletes them. Safe to run repeatedly.
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

# ── fixtures ──────────────────────────────────────────────────────────────────
echo ""
blue "=== Creating fixture employees ==="
mk(){ curl -s -o /dev/null -X POST "$BASE/employees" -H "$H" -H 'Content-Type: application/json' -d "$1"; }
mk '{"full_name":"Zzstep5 Ada","email":"zzstep5.ada@t.com","country":"NG","department":"Zzstep5Eng","role":"Backend Engineer","preferred_currency":"NGN","expected_salary":500000}'
mk '{"full_name":"Zzstep5 Bob","email":"zzstep5.bob@t.com","country":"US","department":"Zzstep5Eng","role":"Frontend Engineer","preferred_currency":"USD","expected_salary":4000}'
mk '{"full_name":"Zzstep5 Chidi","email":"zzstep5.chidi@t.com","country":"NG","department":"Zzstep5Fin","role":"Analyst","preferred_currency":"NGN","expected_salary":300000}'
mk '{"full_name":"Zzstep5 Eve 50% Bonus","email":"zzstep5.eve@t.com","country":"NG","department":"Zzstep5Sales","role":"Rep","preferred_currency":"NGN","expected_salary":200000}'
mk '{"full_name":"Zzstep5 Frank_Test","email":"zzstep5.frank@t.com","country":"US","department":"Zzstep5Sales","role":"Rep","preferred_currency":"USD","expected_salary":3500}'
green "  5 fixtures created"

# count <querystring>  -> number of matching rows
count(){ curl -s "$BASE/employees?search=zzstep5&$1" -H "$H" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('total','ERR'))" 2>/dev/null; }
# names <querystring>
names(){ curl -s "$BASE/employees?$1" -H "$H" \
  | python3 -c "import sys,json;print(','.join(i['full_name'] for i in json.load(sys.stdin).get('items',[])))" 2>/dev/null; }
code(){ curl -s -o /dev/null -w '%{http_code}' "$BASE/employees?$1" -H "$H"; }
msg(){ curl -s "$BASE/employees?$1" -H "$H" | python3 -c "
import sys,json;print(json.load(sys.stdin).get('error',{}).get('message',''))" 2>/dev/null; }

want(){ # want <label> <expected> <actual>
  if [ "$3" == "$2" ]; then ok "$1  ($3)"; else no "$1  (expected $2, got $3)"; fi }

echo ""
blue "============================================"
blue " TEST 1: new filters"
blue "============================================"
want "baseline: 5 fixtures"        5 "$(count '')"
want "country=NG"                  3 "$(count 'country=NG')"
want "country=US"                  2 "$(count 'country=US')"
want "currency=NGN"                3 "$(count 'currency=NGN')"
want "currency=USD"                2 "$(count 'currency=USD')"
want "department=Zzstep5Eng"       2 "$(count 'department=Zzstep5Eng')"
want "department=Zzstep5Sales"     2 "$(count 'department=Zzstep5Sales')"
want "combined NG + NGN"           3 "$(count 'country=NG&currency=NGN')"
want "combined US + Zzstep5Eng"    1 "$(count 'country=US&department=Zzstep5Eng')"
want "is_active=true"              5 "$(count 'is_active=true')"

echo ""
blue "============================================"
blue " TEST 2: search now spans 4 columns"
blue "============================================"
# NOTE: count() prefixes search=zzstep5 to scope results to our fixtures, but
# FastAPI keeps the LAST duplicate query param - so passing another search=
# REPLACES the scoping and queries the whole table. For search tests we must
# scope with a different filter instead. department=Zzstep5* is fixture-only.
scount(){ curl -s "$BASE/employees?$1" -H "$H" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('total','ERR'))" 2>/dev/null; }

want "by name fragment"            1 "$(scount 'search=zzstep5.ada')"
want "by email"                    1 "$(scount 'search=zzstep5.chidi@')"
want "by department"               2 "$(scount 'search=Zzstep5Eng')"
want "by job title (engineer)"     2 "$(scount 'search=engineer&department=Zzstep5Eng')"
want "case-insensitive (ENGINEER)" 2 "$(scount 'search=ENGINEER&department=Zzstep5Eng')"
want "search+filter narrows (Rep)" 2 "$(scount 'search=Rep&department=Zzstep5Sales')"

echo ""
blue "============================================"
blue " TEST 3: LIKE wildcard escaping  (the bug)"
blue "============================================"
# %25 = urlencoded '%'
# These deliberately search the WHOLE table. If escaping were broken, '%' would
# match every employee you have, so the count would be far above 1.
TOTAL_ALL=$(curl -s "$BASE/employees?limit=1" -H "$H" | python3 -c "
import sys,json;print(json.load(sys.stdin).get('total',0))" 2>/dev/null)
echo "        (total employees in database: $TOTAL_ALL)"
want "search '50%' matches ONLY Eve, not all $TOTAL_ALL" 1 "$(scount 'search=50%25')"
want "search 'Frank_Test' literal underscore"            1 "$(scount 'search=Frank_Test')"
want "search '%' alone does NOT match all $TOTAL_ALL"    1 "$(scount 'search=%25')"

echo ""
blue "============================================"
blue " TEST 4: sorting"
blue "============================================"
A=$(names 'search=zzstep5&sort_by=full_name&sort_order=asc')
D=$(names 'search=zzstep5&sort_by=full_name&sort_order=desc')
echo "        asc : $A"
echo "        desc: $D"
[ "$A" != "$D" ] && ok "asc and desc differ" || no "sort_order ignored"
FIRST=$(echo "$A" | cut -d, -f1)
[ "$FIRST" == "Zzstep5 Ada" ] && ok "asc starts with Ada" || no "asc wrong first row: $FIRST"
S=$(names 'search=zzstep5&sort_by=expected_salary&sort_order=desc' | cut -d, -f1)
[ "$S" == "Zzstep5 Ada" ] && ok "salary desc puts highest first" || no "salary sort wrong: $S"

echo ""
blue "============================================"
blue " TEST 5: invalid filters -> 422 WITH options"
blue "============================================"
for pair in "status=BOGUS" "country=Nigeria" "currency=XYZ" "sort_by=password" "sort_order=sideways"; do
  C=$(code "$pair"); M=$(msg "$pair")
  echo "        $pair -> $C"
  echo "          $M"
  [ "$C" == "422" ] && ok "$pair rejected" || no "$pair got $C (want 422)"
  [ -n "$M" ] && ok "$pair explains valid options" || no "$pair gave no message"
done

echo ""
blue "============================================"
blue " TEST 6: sort_by is an allowlist (no injection)"
blue "============================================"
want "sort_by=hashed_password blocked" 422 "$(code 'sort_by=hashed_password')"
want "sort_by=employer_id blocked"     422 "$(code 'sort_by=employer_id')"
want "sort_by=1;DROP TABLE blocked"    422 "$(code 'sort_by=1%3BDROP%20TABLE%20users')"

echo ""
blue "============================================"
blue " TEST 7: pagination metadata"
blue "============================================"
for p in 1 2 3; do
  echo -n "        page $p: "
  curl -s "$BASE/employees?search=zzstep5&limit=2&page=$p&sort_by=full_name&sort_order=asc" -H "$H" \
    | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('total=%s pages=%s has_prev=%-5s has_next=%-5s prev=%-4s next=%-4s %s' % (
  d['total'],d['total_pages'],d['has_prev'],d['has_next'],d['prev_page'],d['next_page'],
  [i['full_name'].replace('Zzstep5 ','') for i in d['items']]))" 2>/dev/null
done
P1=$(curl -s "$BASE/employees?search=zzstep5&limit=2&page=1" -H "$H" | python3 -c "
import sys,json;d=json.load(sys.stdin);print('%s|%s|%s' % (d['has_prev'],d['has_next'],d['next_page']))" 2>/dev/null)
want "page 1 flags" "False|True|2" "$P1"
P3=$(curl -s "$BASE/employees?search=zzstep5&limit=2&page=3" -H "$H" | python3 -c "
import sys,json;d=json.load(sys.stdin);print('%s|%s|%s' % (d['has_prev'],d['has_next'],d['next_page']))" 2>/dev/null)
want "last page flags" "True|False|None" "$P3"

echo ""
blue "============================================"
blue " TEST 8: stable order across pages"
blue "============================================"
ALL=""
for p in 1 2 3; do
  ALL="$ALL$(names "search=zzstep5&limit=2&page=$p&sort_by=country&sort_order=asc"),"
done
UNIQ=$(echo "$ALL" | tr ',' '\n' | grep -c "Zzstep5")
DUPES=$(echo "$ALL" | tr ',' '\n' | grep "Zzstep5" | sort | uniq -d | wc -l)
echo "        rows across 3 pages: $UNIQ   duplicates: $DUPES"
[ "$UNIQ" == "5" ] && ok "all 5 rows appear exactly once" || no "got $UNIQ rows across pages (want 5)"
[ "$DUPES" == "0" ] && ok "no row appears on two pages" || no "$DUPES rows duplicated across pages"

echo ""
blue "============================================"
blue " Cleanup"
blue "============================================"
IDS=$(curl -s "$BASE/employees?search=zzstep5&limit=100" -H "$H" \
  | python3 -c "import sys,json;[print(i['id']) for i in json.load(sys.stdin).get('items',[])]" 2>/dev/null)
N=0
for id in $IDS; do curl -s -o /dev/null -X DELETE "$BASE/employees/$id" -H "$H"; N=$((N+1)); done
green "  removed $N fixture employees"

echo ""
blue "============================================"
echo -e " Results:  \033[32m$PASS passed\033[0m / \033[31m$FAIL failed\033[0m"
blue "============================================"
echo ""
[ "$FAIL" -eq 0 ] && green "Step 5 verified." || red "Some checks failed - see above."
echo ""
