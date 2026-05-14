#!/bin/bash
# setup_credentials.sh — store Splunk credentials in macOS Keychain
# Run once. Never run again unless you need to update the password.

KEYCHAIN_SERVICE="splunk-dashboard-export"

read -rp "Splunk username: " SPLUNK_USER
read -rsp "Splunk password: " SPLUNK_PASS
echo

# Store username as an account attribute, password as the secret
security add-generic-password \
  -s "$KEYCHAIN_SERVICE" \
  -a "$SPLUNK_USER" \
  -w "$SPLUNK_PASS" \
  -U  # -U = update if already exists

echo "Credentials stored in Keychain under service: $KEYCHAIN_SERVICE"
echo "Username: $SPLUNK_USER"
