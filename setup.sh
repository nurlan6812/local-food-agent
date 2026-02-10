#!/bin/bash
# Korean Food Agent 초기 설정 스크립트

set -e

echo "🚀 Korean Food Agent 설정을 시작합니다..."
echo ""

# Python 버전 확인
echo "📌 Python 버전 확인..."
python3 --version || { echo "❌ Python 3가 설치되어 있지 않습니다."; exit 1; }
echo ""

# Node.js 버전 확인
echo "📌 Node.js 버전 확인..."
node --version || { echo "❌ Node.js가 설치되어 있지 않습니다."; exit 1; }
npm --version || { echo "❌ npm이 설치되어 있지 않습니다."; exit 1; }
echo ""

# 1. Python 가상환경 생성 (선택사항)
read -p "Python 가상환경을 생성하시겠습니까? (y/n): " create_venv
if [ "$create_venv" = "y" ]; then
    echo "📦 Python 가상환경 생성 중..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 가상환경 생성 완료 (venv/)"
    echo ""
fi

# 2. Python 의존성 설치
echo "📦 Python 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Python 패키지 설치 완료"
echo ""

# 3. Playwright 브라우저 설치
echo "🌐 Playwright 브라우저 설치 중..."
playwright install chromium
echo "✅ Playwright 브라우저 설치 완료"
echo ""

# 4. 프론트엔드 의존성 설치
echo "📦 프론트엔드 패키지 설치 중..."
cd frontend/app
npm install
cd ../..
echo "✅ 프론트엔드 패키지 설치 완료"
echo ""

# 5. .env 파일 생성
if [ ! -f .env ]; then
    echo "📝 .env 파일 생성 중..."
    cp .env.example .env
    echo "✅ .env 파일 생성 완료"
    echo ""
    echo "⚠️  중요: .env 파일을 열어서 API 키를 입력해주세요!"
    echo "   - GOOGLE_API_KEY (필수)"
    echo "   - SERPER_API_KEY (필수)"
    echo "   - KAKAO_API_KEY (필수)"
    echo "   - SUPABASE_URL (필수)"
    echo "   - SUPABASE_ANON_KEY (필수)"
    echo ""
else
    echo "✅ .env 파일이 이미 존재합니다."
    echo ""
fi

# 6. Supabase 테이블 안내
echo "📊 Supabase 데이터베이스 설정:"
echo "   Supabase 프로젝트의 SQL Editor에서 다음 파일을 실행하세요:"
echo "   → docs/supabase_schema.sql"
echo ""

# 완료
echo "✅ 설치가 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. .env 파일에 API 키 입력"
echo "2. Supabase에서 docs/supabase_schema.sql 실행"
echo "3. ./run_all.sh 로 서버 시작"
echo ""
echo "문제가 있으면 README.md를 참고하세요."
