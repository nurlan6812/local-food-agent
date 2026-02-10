#!/bin/bash
# Korean Food Agent 초기 설정 스크립트

set -e

echo "\ud83d\ude80 Korean Food Agent 설정을 시작합니다..."
echo ""

echo "\ud83d\udccc Python 버전 확인..."
python3 --version || { echo "\u274c Python 3가 설치되어 있지 않습니다."; exit 1; }
echo ""

echo "\ud83d\udccc Node.js 버전 확인..."
node --version || { echo "\u274c Node.js가 설치되어 있지 않습니다."; exit 1; }
npm --version || { echo "\u274c npm이 설치되어 있지 않습니다."; exit 1; }
echo ""

read -p "Python 가상환경을 생성하시겠습니까? (y/n): " create_venv
if [ "$create_venv" = "y" ]; then
    echo "\ud83d\udce6 Python 가상환경 생성 중..."
    python3 -m venv venv
    source venv/bin/activate
    echo "\u2705 가상환경 생성 완료 (venv/)"
    echo ""
fi

echo "\ud83d\udce6 Python 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt
echo "\u2705 Python 패키지 설치 완료"
echo ""

echo "\ud83c\udf10 Playwright 브라우저 설치 중..."
playwright install chromium
echo "\u2705 Playwright 브라우저 설치 완료"
echo ""

echo "\ud83d\udce6 프론트엔드 패키지 설치 중..."
cd frontend/app
npm install
cd ../..
echo "\u2705 프론트엔드 패키지 설치 완료"
echo ""

if [ ! -f .env ]; then
    echo "\ud83d\udcdd .env 파일 생성 중..."
    cp .env.example .env
    echo "\u2705 .env 파일 생성 완료"
    echo ""
    echo "\u26a0\ufe0f  중요: .env 파일을 열어서 API 키를 입력해주세요!"
    echo "   - GOOGLE_API_KEY (필수)"
    echo "   - SERPER_API_KEY (필수)"
    echo "   - KAKAO_API_KEY (필수)"
    echo "   - SUPABASE_URL (필수)"
    echo "   - SUPABASE_ANON_KEY (필수)"
    echo ""
else
    echo "\u2705 .env 파일이 이미 존재합니다."
    echo ""
fi

echo "\ud83d\udcca Supabase 데이터베이스 설정:"
echo "   Supabase 프로젝트의 SQL Editor에서 다음 파일을 실행하세요:"
echo "   \u2192 docs/supabase_schema.sql"
echo ""

echo "\u2705 설치가 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. .env 파일에 API 키 입력"
echo "2. Supabase에서 docs/supabase_schema.sql 실행"
echo "3. ./run_all.sh 로 서버 시작"
echo ""
echo "문제가 있으면 README.md를 참고하세요."
