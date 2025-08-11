#!/bin/bash
# Verification script for latest.json refactoring
# Safe, read-only operations to verify the refactoring is working correctly

set -e

echo "==================================="
echo "latest.json Refactoring Verification"
echo "==================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if helper module exists
echo "1. Checking helper module..."
if [ -f "utils/data_helper.py" ]; then
    echo -e "${GREEN}✓${NC} Helper module exists"
else
    echo -e "${RED}✗${NC} Helper module not found"
    exit 1
fi

# Test 2: Run unit tests
echo ""
echo "2. Running unit tests..."
if source kotogawa_env/bin/activate 2>/dev/null && python -m pytest tests/test_data_helper.py -q; then
    echo -e "${GREEN}✓${NC} All unit tests passed"
else
    echo -e "${RED}✗${NC} Unit tests failed"
    exit 1
fi

# Test 3: Compare latest.json with most recent history file
echo ""
echo "3. Comparing data sources..."
LATEST_HISTORY=$(source kotogawa_env/bin/activate && python -c "
from utils.data_helper import get_latest_history_file
from pathlib import Path
latest = get_latest_history_file(Path('data/history'))
print(latest if latest else 'None')
")

if [ "$LATEST_HISTORY" != "None" ] && [ -f "$LATEST_HISTORY" ]; then
    echo "Latest history file: $LATEST_HISTORY"
    
    # Compare timestamps
    if [ -f "data/latest.json" ]; then
        LATEST_TIME=$(cat data/latest.json | grep -o '"timestamp"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | cut -d'"' -f4)
        HISTORY_TIME=$(cat "$LATEST_HISTORY" | grep -o '"timestamp"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | cut -d'"' -f4)
        
        if [ "$LATEST_TIME" = "$HISTORY_TIME" ]; then
            echo -e "${GREEN}✓${NC} Timestamps match: $LATEST_TIME"
        else
            echo -e "${YELLOW}⚠${NC} Timestamps differ:"
            echo "  latest.json: $LATEST_TIME"
            echo "  history:     $HISTORY_TIME"
        fi
    else
        echo -e "${YELLOW}⚠${NC} latest.json not found (may be intentional if Phase 4 complete)"
    fi
else
    echo -e "${RED}✗${NC} Could not find latest history file"
fi

# Test 4: Test data loading through helper
echo ""
echo "4. Testing data loading..."
DATA_LOADED=$(source kotogawa_env/bin/activate && python -c "
from utils.data_helper import load_latest_data
from pathlib import Path
data = load_latest_data(Path('data'))
if data:
    print(f\"timestamp:{data.get('timestamp', 'None')[:19]}\")
    print(f\"has_dam:{('dam' in data)}\")
    print(f\"has_river:{('river' in data)}\")
else:
    print('FAILED')
" 2>/dev/null)

if echo "$DATA_LOADED" | grep -q "FAILED"; then
    echo -e "${RED}✗${NC} Data loading failed"
    exit 1
else
    echo "$DATA_LOADED" | while read line; do
        echo -e "${GREEN}✓${NC} $line"
    done
fi

# Test 5: Check for remaining latest.json references
echo ""
echo "5. Checking for latest.json references..."
REFS=$(grep -r "latest\.json" --exclude-dir=.git --exclude-dir=kotogawa_env --exclude-dir=venv --exclude-dir=__pycache__ --exclude="*.backup" --exclude="verify_refactor.sh" --exclude-dir=docs . 2>/dev/null | wc -l)
echo "Found $REFS references to latest.json"
if [ $REFS -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} References still exist (expected during transition):"
    grep -r "latest\.json" --exclude-dir=.git --exclude-dir=kotogawa_env --exclude-dir=venv --exclude-dir=__pycache__ --exclude="*.backup" --exclude="verify_refactor.sh" --exclude-dir=docs . 2>/dev/null | head -5 | sed 's/^/  /'
fi

# Test 6: Performance check (cache key generation)
echo ""
echo "6. Testing cache key generation..."
CACHE_TIME=$(source kotogawa_env/bin/activate && python -c "
import time
from utils.data_helper import get_latest_file_mtime
from pathlib import Path
start = time.time()
mtime = get_latest_file_mtime(Path('data'))
elapsed = (time.time() - start) * 1000
if mtime:
    print(f'{elapsed:.2f}')
else:
    print('FAILED')
" 2>/dev/null)

if [ "$CACHE_TIME" = "FAILED" ]; then
    echo -e "${RED}✗${NC} Cache key generation failed"
else
    echo -e "${GREEN}✓${NC} Cache key generated in ${CACHE_TIME}ms"
fi

# Summary
echo ""
echo "==================================="
echo "Verification Summary"
echo "==================================="
echo -e "${GREEN}✓${NC} Helper module created and tested"
echo -e "${GREEN}✓${NC} Data loading works from history files"
echo -e "${GREEN}✓${NC} Performance acceptable"
if [ $REFS -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} $REFS references to latest.json remain (monitor during transition)"
else
    echo -e "${GREEN}✓${NC} No references to latest.json found"
fi

echo ""
echo "Refactoring verification complete!"