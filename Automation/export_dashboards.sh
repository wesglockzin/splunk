#!/bin/bash
# export_dashboards.sh — bulk export all Splunk dashboards to JSON
# Credentials pulled from macOS Keychain (run setup_credentials.sh first)

set -euo pipefail

KEYCHAIN_SERVICE="splunk-dashboard-export"
SPLUNK_HOST="https://host.example.gov"
APP="search"
OUTPUT_DIR="./dashboards"

# --- Pull credentials from Keychain ---
SPLUNK_USER=$(security find-generic-password -s "$KEYCHAIN_SERVICE" -g 2>&1 \
  | grep '"acct"' | sed 's/.*"acct"<blob>="//;s/"//')
SPLUNK_PASS=$(security find-generic-password -s "$KEYCHAIN_SERVICE" -w)

if [[ -z "$SPLUNK_USER" || -z "$SPLUNK_PASS" ]]; then
  echo "ERROR: Credentials not found in Keychain. Run setup_credentials.sh first."
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Connecting to $SPLUNK_HOST as $SPLUNK_USER ..."

# --- Get list of all dashboard names ---
RESPONSE=$(curl -sk --max-time 15 -u "$SPLUNK_USER:$SPLUNK_PASS" \
  "$SPLUNK_HOST/servicesNS/-/$APP/data/ui/views?output_mode=json&count=0") || {
  echo "ERROR: curl failed — port may be blocked or host unreachable."
  echo "Try: curl -sk https://host.example.gov/[redacted-path] -u your-username:<pass>"
  exit 1
}

# Check for auth failure
if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'entry' in d else 1)" 2>/dev/null; then
  :
else
  echo "ERROR: Failed to retrieve dashboard list. Check credentials or host reachability."
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  exit 1
fi

DASHBOARDS=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for e in data['entry']:
    if e['content'].get('isDashboard', False):
        print(e['name'])
")

TOTAL=$(echo "$DASHBOARDS" | wc -l | tr -d ' ')
echo "Found $TOTAL dashboards. Exporting..."

COUNT=0
FAILED=()

while IFS= read -r DASH; do
  [[ -z "$DASH" ]] && continue
  OUTFILE="$OUTPUT_DIR/${DASH}.json"

  HTTP_CODE=$(curl -sk -u "$SPLUNK_USER:$SPLUNK_PASS" \
    "$SPLUNK_HOST/servicesNS/-/$APP/data/ui/views/$DASH?output_mode=json" \
    -o "$OUTFILE" -w "%{http_code}")

  if [[ "$HTTP_CODE" == "200" ]]; then
    COUNT=$((COUNT + 1))
    echo "  [$COUNT/$TOTAL] $DASH"
  else
    FAILED+=("$DASH (HTTP $HTTP_CODE)")
    echo "  [FAILED] $DASH — HTTP $HTTP_CODE"
    rm -f "$OUTFILE"
  fi
done <<< "$DASHBOARDS"

echo ""
echo "Done. $COUNT/$TOTAL dashboards exported to $OUTPUT_DIR/"

if [[ ${#FAILED[@]} -gt 0 ]]; then
  echo ""
  echo "Failed exports:"
  for F in "${FAILED[@]}"; do
    echo "  - $F"
  done
fi
