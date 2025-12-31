# Renty Dynamic Pricing - SSL Certificate Setup Script
# Run this script to extract certificates from rentey.pfx

param(
    [string]$PfxPath = "..\rentey.pfx",
    [string]$OutputDir = "..\certs"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Renty SSL Certificate Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "Created directory: $OutputDir" -ForegroundColor Green
}

# Check if OpenSSL is available
$opensslPath = Get-Command openssl -ErrorAction SilentlyContinue

if (-not $opensslPath) {
    Write-Host "OpenSSL not found. Please install OpenSSL or use manual extraction." -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Use PowerShell to extract (requires .NET):" -ForegroundColor Yellow
    Write-Host ""
    
    # PowerShell alternative
    $code = @"
# Load the PFX
`$pfxPassword = Read-Host 'Enter PFX password' -AsSecureString
`$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
`$cert.Import('$PfxPath', `$pfxPassword, 'Exportable')

# Export certificate (public key)
`$certBytes = `$cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
[System.IO.File]::WriteAllBytes('$OutputDir\cert.pem', `$certBytes)

# For private key, use certutil
certutil -exportPFX -p '' -privatekey -f '$PfxPath' '$OutputDir\key.pem'
"@
    Write-Host $code -ForegroundColor Gray
    exit 1
}

# Check if PFX file exists
if (-not (Test-Path $PfxPath)) {
    Write-Host "PFX file not found: $PfxPath" -ForegroundColor Red
    Write-Host "Please place rentey.pfx in the project root directory." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Found PFX file: $PfxPath" -ForegroundColor Green
Write-Host ""

# Prompt for password
$password = Read-Host "Enter PFX password (leave empty if none)"

# Extract certificate
Write-Host "Extracting certificate..." -ForegroundColor Yellow
if ($password) {
    openssl pkcs12 -in $PfxPath -clcerts -nokeys -out "$OutputDir\cert.pem" -passin "pass:$password"
} else {
    openssl pkcs12 -in $PfxPath -clcerts -nokeys -out "$OutputDir\cert.pem" -passin "pass:"
}

# Extract private key
Write-Host "Extracting private key..." -ForegroundColor Yellow
if ($password) {
    openssl pkcs12 -in $PfxPath -nocerts -nodes -out "$OutputDir\key.pem" -passin "pass:$password"
} else {
    openssl pkcs12 -in $PfxPath -nocerts -nodes -out "$OutputDir\key.pem" -passin "pass:"
}

# Verify extraction
if ((Test-Path "$OutputDir\cert.pem") -and (Test-Path "$OutputDir\key.pem")) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  SSL Certificates Extracted Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Files created:" -ForegroundColor Cyan
    Write-Host "  - $OutputDir\cert.pem (Public certificate)" -ForegroundColor White
    Write-Host "  - $OutputDir\key.pem (Private key)" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Verify the certificates: openssl x509 -in $OutputDir\cert.pem -text -noout" -ForegroundColor White
    Write-Host "  2. Run: docker-compose up -d" -ForegroundColor White
} else {
    Write-Host "Certificate extraction failed!" -ForegroundColor Red
    exit 1
}

