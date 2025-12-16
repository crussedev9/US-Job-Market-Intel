# Example daily run script for US Job Market Intel (PowerShell)
# Usage: .\scripts\run_daily_example.ps1

$ErrorActionPreference = "Stop"

# Configuration
$ProjectDir = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $ProjectDir "venv"
$LogDir = Join-Path $ProjectDir "logs"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "pipeline_$Timestamp.log"

# Ensure log directory exists
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Activate virtual environment
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
& $ActivateScript

# Log start
$StartMessage = @"
========================================
Pipeline started at $(Get-Date)
========================================
"@
$StartMessage | Tee-Object -FilePath $LogFile -Append

# Run full pipeline
Set-Location $ProjectDir
jobintel full-run --log-level INFO 2>&1 | Tee-Object -FilePath $LogFile -Append

# Log completion
$EndMessage = @"
========================================
Pipeline completed at $(Get-Date)
========================================
"@
$EndMessage | Tee-Object -FilePath $LogFile -Append

# Optional: Upload to cloud storage (uncomment if needed)
# azcopy copy "data\staged\latest\*" "https://youraccount.blob.core.windows.net/jobintel/latest/" --recursive

# Optional: Send notification (uncomment if needed)
# Invoke-WebRequest -Uri "https://your-webhook-url" -Method POST -Body "Pipeline completed successfully"

exit 0
