#\!/bin/bash
# 厚東川監視システム スモークテスト
# 主要機能の簡易動作確認

echo "=== Kotogawa Monitor Smoke Test ==="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# テスト結果カウンタ
PASS=0
FAIL=0
WARN=0

# 1. 最新データファイルの確認
echo "1. Checking latest data file..."
LATEST=$(find data/history -name "*.json" -type f 2>/dev/null | sort | tail -1)
if [ -n "$LATEST" ]; then
    echo -e "${GREEN}✓${NC} Latest file: $LATEST"
    ((PASS++))
    
    # ファイルの更新時刻確認
    if [ -f "$LATEST" ]; then
        FILE_MOD=$(stat -c %Y "$LATEST" 2>/dev/null || stat -f %m "$LATEST" 2>/dev/null)
        NOW=$(date +%s)
        if [ -n "$FILE_MOD" ]; then
            FILE_AGE=$((NOW - FILE_MOD))
            if [ $FILE_AGE -lt 3600 ]; then  # 1時間以内
                echo -e "${GREEN}✓${NC} File is recent (${FILE_AGE}s old)"
                ((PASS++))
            elif [ $FILE_AGE -lt 7200 ]; then  # 2時間以内
                echo -e "${YELLOW}⚠${NC} File is somewhat old (${FILE_AGE}s old)"
                ((WARN++))
            else
                echo -e "${RED}✗${NC} File is too old (${FILE_AGE}s old)"
                ((FAIL++))
            fi
        fi
    fi
else
    echo -e "${RED}✗${NC} No data files found"
    ((FAIL++))
fi
echo ""

# 2. JSON形式の検証
echo "2. Validating JSON format..."
if [ -n "$LATEST" ] && [ -f "$LATEST" ]; then
    python3 -m json.tool "$LATEST" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Valid JSON format"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} Invalid JSON format"
        ((FAIL++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Skipped (no file to check)"
    ((WARN++))
fi
echo ""

# 3. 必須フィールドの確認
echo "3. Checking required fields..."
if [ -n "$LATEST" ] && [ -f "$LATEST" ]; then
    python3 -c "
import json
import sys
try:
    with open('$LATEST') as f:
        data = json.load(f)
        required = ['timestamp', 'data_time', 'dam', 'river', 'rainfall']
        missing = [field for field in required if field not in data]
        if missing:
            print(f'Missing fields: {missing}')
            sys.exit(1)
        print('All required fields present')
        sys.exit(0)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All required fields present"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} Missing required fields"
        ((FAIL++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Skipped (no file to check)"
    ((WARN++))
fi
echo ""

# 4. データ収集スクリプトの確認
echo "4. Checking data collection script..."
if [ -f "scripts/collect_data.py" ]; then
    echo -e "${GREEN}✓${NC} collect_data.py exists"
    ((PASS++))
    
    # DEBUGログの確認
    DEBUG_COUNT=$(grep -c "print.*DEBUG" scripts/collect_data.py 2>/dev/null || echo "0")
    if [ "$DEBUG_COUNT" -eq "0" ]; then
        echo -e "${GREEN}✓${NC} No DEBUG logs found"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} Found $DEBUG_COUNT DEBUG log statements"
        ((FAIL++))
    fi
else
    echo -e "${RED}✗${NC} collect_data.py not found"
    ((FAIL++))
fi
echo ""

# 5. 過去24時間のデータ確認
echo "5. Checking data collection status (last 24h)..."
FILES_24H=$(find data/history -name "*.json" -type f -mtime -1 2>/dev/null | wc -l)
if [ "$FILES_24H" -gt "50" ]; then
    echo -e "${GREEN}✓${NC} Good coverage: $FILES_24H files in last 24h"
    ((PASS++))
elif [ "$FILES_24H" -gt "20" ]; then
    echo -e "${YELLOW}⚠${NC} Partial coverage: $FILES_24H files in last 24h"
    ((WARN++))
else
    echo -e "${RED}✗${NC} Poor coverage: $FILES_24H files in last 24h"
    ((FAIL++))
fi
echo ""

# 6. Python環境確認
echo "6. Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}✓${NC} Python3 available: $PYTHON_VERSION"
    ((PASS++))
else
    echo -e "${RED}✗${NC} Python3 not found"
    ((FAIL++))
fi

# 必要なパッケージ確認
python3 -c "import requests, bs4" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Core packages installed"
    ((PASS++))
else
    echo -e "${RED}✗${NC} Required packages missing"
    ((FAIL++))
fi
echo ""

# 結果サマリー
echo "======================================="
echo "SUMMARY:"
echo -e "${GREEN}Passed:${NC} $PASS"
echo -e "${YELLOW}Warnings:${NC} $WARN"
echo -e "${RED}Failed:${NC} $FAIL"

if [ $FAIL -eq 0 ]; then
    if [ $WARN -eq 0 ]; then
        echo -e "\n${GREEN}✓ All tests passed\!${NC}"
        exit 0
    else
        echo -e "\n${YELLOW}⚠ Tests passed with warnings${NC}"
        exit 0
    fi
else
    echo -e "\n${RED}✗ Some tests failed${NC}"
    exit 1
fi
