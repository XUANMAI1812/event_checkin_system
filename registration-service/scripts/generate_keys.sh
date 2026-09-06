#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEY_DIR="$SCRIPT_DIR/../keys"
mkdir -p "$KEY_DIR"
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$KEY_DIR/private_key.pem"
openssl rsa -in "$KEY_DIR/private_key.pem" -pubout -out "$KEY_DIR/public_key.pem"
echo "Da sinh $KEY_DIR/private_key.pem va $KEY_DIR/public_key.pem"
