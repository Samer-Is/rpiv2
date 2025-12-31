#!/bin/bash
# Extract SSL certificate from PFX file
# Usage: ./extract-certificate.sh certificate.pfx

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <pfx-file>"
    echo "Example: $0 rentey.pfx"
    exit 1
fi

PFX_FILE=$1
OUTPUT_DIR="/etc/nginx/ssl"

echo "Extracting certificate from: $PFX_FILE"
echo "Output directory: $OUTPUT_DIR"

# Create output directory
sudo mkdir -p $OUTPUT_DIR

# Extract certificate
echo "Enter the PFX password when prompted..."
sudo openssl pkcs12 -in "$PFX_FILE" -clcerts -nokeys -out "$OUTPUT_DIR/cert.pem"

# Extract private key
sudo openssl pkcs12 -in "$PFX_FILE" -nocerts -nodes -out "$OUTPUT_DIR/key.pem"

# Set permissions
sudo chmod 600 "$OUTPUT_DIR/key.pem"
sudo chmod 644 "$OUTPUT_DIR/cert.pem"
sudo chown root:root "$OUTPUT_DIR/key.pem" "$OUTPUT_DIR/cert.pem"

echo ""
echo "Certificate extracted successfully!"
echo "  Certificate: $OUTPUT_DIR/cert.pem"
echo "  Private Key: $OUTPUT_DIR/key.pem"
echo ""
echo "Now update your Nginx config and reload:"
echo "  sudo nginx -t && sudo systemctl reload nginx"

