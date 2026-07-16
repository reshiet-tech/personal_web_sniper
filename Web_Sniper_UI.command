#!/bin/bash
# 실행 파일이 위치한 디렉토리로 이동
cd "$(dirname "$0")"

echo "======================================"
echo "🎯 Web Sniper 타겟 관리자 실행 중..."
echo "======================================"
echo "잠시 후 인터넷 창이 자동으로 열립니다."
echo "(이 까만 창을 끄면 관리자 웹페이지도 함께 종료됩니다)"
echo ""

# 가상환경 활성화 및 Streamlit 실행
source venv/bin/activate
streamlit run ui.py
