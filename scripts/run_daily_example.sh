#!/bin/bash
# Example daily run script for US Job Market Intel
# Usage: ./scripts/run_daily_example.sh

set -e  # Exit on error

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/pipeline_$(date +%Y%m%d_%H%M%S).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Log start
echo "========================================" | tee -a "$LOG_FILE"
echo "Pipeline started at $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Run full pipeline
cd "$PROJECT_DIR"
jobintel full-run --log-level INFO 2>&1 | tee -a "$LOG_FILE"

# Log completion
echo "========================================" | tee -a "$LOG_FILE"
echo "Pipeline completed at $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Optional: Upload to cloud storage (uncomment if needed)
# aws s3 sync data/staged/latest/ s3://your-bucket/jobintel/latest/
# az storage blob upload-batch -d jobintel -s data/staged/latest/

# Optional: Send notification (uncomment if needed)
# curl -X POST "https://your-webhook-url" -d "Pipeline completed successfully"

exit 0
