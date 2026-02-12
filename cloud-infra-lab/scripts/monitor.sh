#!/bin/bash
# =============================================================================
# Cloud Infrastructure Lab - Health Monitor Script
# Periodically checks server health and logs results
# Usage: ./monitor.sh [URL] [INTERVAL_SECONDS] [LOG_FILE]
# =============================================================================

set -euo pipefail

# Configuration (override via command-line arguments)
TARGET_URL="${1:-http://localhost/health}"
CHECK_INTERVAL="${2:-30}"
LOG_FILE="${3:-/var/log/cloud-lab-monitor.log}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "  Cloud Infrastructure Lab - Monitor"
echo "=========================================="
echo "  Target:   $TARGET_URL"
echo "  Interval: ${CHECK_INTERVAL}s"
echo "  Log:      $LOG_FILE"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop monitoring."
echo ""

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Counters
total_checks=0
successful_checks=0
failed_checks=0

# Cleanup on exit
cleanup() {
    echo ""
    echo "=========================================="
    echo "  Monitoring Summary"
    echo "=========================================="
    echo "  Total checks:  $total_checks"
    echo "  Successful:    $successful_checks"
    echo "  Failed:        $failed_checks"
    if [[ $total_checks -gt 0 ]]; then
        success_rate=$(echo "scale=1; $successful_checks * 100 / $total_checks" | bc)
        echo "  Success rate:  ${success_rate}%"
    fi
    echo "=========================================="
    exit 0
}

trap cleanup SIGINT SIGTERM

# Main monitoring loop
while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    total_checks=$((total_checks + 1))

    # Make the health check request
    http_code=$(curl -s -o /tmp/health_response.json -w "%{http_code}" \
        --connect-timeout 5 --max-time 10 "$TARGET_URL" 2>/dev/null || echo "000")

    response_time=$(curl -s -o /dev/null -w "%{time_total}" \
        --connect-timeout 5 --max-time 10 "$TARGET_URL" 2>/dev/null || echo "0")

    if [[ "$http_code" == "200" ]]; then
        successful_checks=$((successful_checks + 1))
        status="UP"
        color="$GREEN"

        # Extract details from health response
        uptime=$(cat /tmp/health_response.json 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('uptime', {}).get('human', 'N/A'))
except: print('N/A')" 2>/dev/null || echo "N/A")

        memory=$(cat /tmp/health_response.json 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('memory', {}).get('system', {}).get('usedPercent', 'N/A'))
except: print('N/A')" 2>/dev/null || echo "N/A")

        log_entry="[$timestamp] STATUS=$status HTTP=$http_code RESPONSE=${response_time}s UPTIME=$uptime MEMORY=$memory"
    else
        failed_checks=$((failed_checks + 1))
        status="DOWN"
        color="$RED"
        log_entry="[$timestamp] STATUS=$status HTTP=$http_code RESPONSE=${response_time}s ERROR=Connection failed or non-200 response"
    fi

    # Print to console
    echo -e "${color}[$timestamp]${NC} Status: ${color}${status}${NC} | HTTP: $http_code | Response: ${response_time}s | Checks: $total_checks (${successful_checks} OK, ${failed_checks} FAIL)"

    # Write to log file
    echo "$log_entry" >> "$LOG_FILE"

    # Alert on failure (could be extended to send notifications)
    if [[ "$status" == "DOWN" ]]; then
        echo -e "${RED}  *** ALERT: Server is not responding! ***${NC}"
    fi

    # Wait for next check
    sleep "$CHECK_INTERVAL"
done
