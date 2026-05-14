#!/bin/bash
# test_connection.sh — validate Splunk API connectivity before running export

KEYCHAIN_SERVICE="splunk-dashboard-export"
SPLUNK_HOST="https://host.example.gov"
APP="search"

PASS_ICON="✅"
FAIL_ICON="❌"

echo "=== Splunk Connection Test ==="
echo ""

# --- Step 1: Pull credentials from Keychain ---
echo "[1/4] Checking Keychain credentials..."
SPLUNK_USER=$(security find-generic-password -s "$KEYCHAIN_SERVICE" -g 2>&1 \
  | grep '"acct"' | sed 's/.*"acct"<blob>="//;s/"//')
SPLUNK_PASS=$(security find-generic-password -s "$KEYCHAIN_SERVICE" -w 2>/dev/null)

if [[ -z "$SPLUNK_USER" || -z "$SPLUNK_PASS" ]]; then
  echo "$FAIL_ICON Credentials not found. Run ./setup_credentials.sh first."
  exit 1
fi
echo "$PASS_ICON Found credentials for user: $SPLUNK_USER"
echo ""

# --- Step 2: Basic host reachability ---
echo "[2/4] Testing host reachability ($SPLUNK_HOST)..."
HTTP_CODE=$(curl -sk --max-time 10 -o /dev/null -w "%{http_code}" "$SPLUNK_HOST")
if [[ "$HTTP_CODE" == "000" ]]; then
  echo "$FAIL_ICON Host unreachable (timeout or DNS failure). Check VPN."
  exit 1
fi
echo "$PASS_ICON Host reachable (HTTP $HTTP_CODE)"
echo ""

# --- Step 3: Auth check via /services/auth/login ---
echo "[3/4] Testing authentication..."
AUTH_RESPONSE=$(curl -sk --max-time 10 -u "$SPLUNK_USER:$SPLUNK_PASS" \
  "$SPLUNK_HOST/services/authentication/current-context?output_mode=json")
AUTH_USER=$(echo "$AUTH_RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d['entry'][0]['content'].get('username', ''))
except:
    print('')
" 2>/dev/null)

if [[ -z "$AUTH_USER" ]]; then
  echo "$FAIL_ICON Auth failed. Response:"
  echo "$AUTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$AUTH_RESPONSE"
  exit 1
fi
echo "$PASS_ICON Authenticated as: $AUTH_USER"
echo ""

# --- Step 4: Dashboard list API ---
echo "[4/4] Fetching dashboard list (app=$APP)..."
RESPONSE=$(curl -sk --max-time 15 -u "$SPLUNK_USER:$SPLUNK_PASS" \
  "$SPLUNK_HOST/servicesNS/-/$APP/data/ui/views?output_mode=json&count=0")

COUNT=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    dashboards = [e['name'] for e in data['entry'] if e['content'].get('isDashboard', False)]
    print(len(dashboards))
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)

if [[ "$COUNT" =~ ^[0-9]+$ ]]; then
  echo "$PASS_ICON Found $COUNT dashboards in app '$APP'"
  echo ""
  echo "=== All checks passed. Safe to run ./export_dashboards.sh ==="
else
  echo "$FAIL_ICON Could not parse dashboard list. Response:"
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  exit 1
fi
