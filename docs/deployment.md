# Korean Food Agent 배포 가이드

다른 서버에서 프로젝트를 실행하는 방법입니다.

## 📋 사전 요구사항

### 1. 시스템 요구사항
- Python 3.9 이상
- Node.js 18 이상
- npm 또는 yarn
- Git

### 2. API 키 준비
다음 API 키를 미리 발급받으세요:

| API | 발급 URL | 필수 여부 | 비용 |
|-----|----------|-----------|------|
| Google AI (Gemini) | https://aistudio.google.com/app/apikey | 필수 | 무료 (일 할당량) |
| Serper.dev | https://serper.dev/ | 필수 | 무료 2,500회/월 |
| 카카오 REST API | https://developers.kakao.com/ | 필수 | 무료 |
| Supabase | https://supabase.com/ | 필수 | 무료 (500MB DB) |
| OpenAI | https://platform.openai.com/ | 선택 | 종량제 |
| SerpAPI | https://serpapi.com/ | 선택 | Serper 대체용 |

### 3. Supabase 프로젝트 생성
1. https://supabase.com/ 접속
2. 새 프로젝트 생성
3. Project URL과 Anon Key 복사 (나중에 `.env`에 입력)

---

## 🚀 설치 방법

### 방법 1: 자동 설치 (권장)

```bash
# 1. 저장소 클론
git clone <repository-url>
cd food_agent

# 2. 설치 스크립트 실행
chmod +x setup.sh
./setup.sh

# 3. .env 파일 편집 (API 키 입력)
nano .env

# 4. Supabase 테이블 생성
# Supabase Dashboard > SQL Editor에서 docs/supabase_schema.sql 실행

# 5. 서버 시작
./run_all.sh
```

### 방법 2: 수동 설치

```bash
# 1. 저장소 클론
git clone <repository-url>
cd food_agent

# 2. Python 가상환경 생성 (선택사항)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Python 패키지 설치
pip install -r requirements.txt

# 4. Playwright 브라우저 설치
playwright install chromium

# 5. 프론트엔드 패키지 설치
cd frontend/app
npm install
cd ../..

# 6. 환경 변수 설정
cp .env.example .env
nano .env  # API 키 입력

# 7. Supabase 테이블 생성
# Supabase Dashboard > SQL Editor에서 docs/supabase_schema.sql 실행
```

---

## ⚙️ 환경 변수 설정

`.env` 파일을 열고 다음 값들을 입력하세요:

```env
# 필수
GOOGLE_API_KEY=your-google-api-key
SERPER_API_KEY=your-serper-api-key
KAKAO_API_KEY=your-kakao-api-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key

# 선택 (기본값 사용 가능)
MODEL_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp
```

---

## 🗄️ Supabase 설정

### 1. 테이블 생성
Supabase Dashboard → SQL Editor에서 `docs/supabase_schema.sql` 실행

### 2. Storage Bucket 생성 (이미지 저장용)
1. Supabase Dashboard → Storage
2. "Create a new bucket" 클릭
3. 이름: `images` (중요: 정확히 이 이름이어야 함)
4. Public bucket: ✅ 체크
5. Create bucket

### 3. Storage RLS 설정
1. Storage → `images` → Policies
2. "New Policy" → "For full customization"
3. Policy name: `Public Access`
4. Allowed operation: All
5. Policy definition: `true`
6. Save

또는 **"Allow public access"** 옵션 선택

---

## ▶️ 실행

### 개발 모드 (로컬)
```bash
# 백엔드 + 프론트엔드 동시 실행
./run_all.sh

# 접속
# - 프론트엔드: http://localhost:3000
# - 백엔드 API: http://localhost:8000
```

### 개별 실행
```bash
# 백엔드만
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 프론트엔드만
cd frontend/app && npm run dev
```

### 프로덕션 모드
```bash
# 백엔드
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# 프론트엔드 빌드 & 실행
cd frontend/app
npm run build
npm start
```

---

## 🐳 Docker 배포 (추가 예정)

```bash
# Docker Compose로 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

---

## 🔧 문제 해결

### Playwright 브라우저 오류
```bash
playwright install chromium
playwright install-deps  # Linux 의존성 설치
```

### Supabase 연결 오류
- `.env`의 `SUPABASE_URL`과 `SUPABASE_ANON_KEY` 확인
- Supabase Dashboard에서 프로젝트가 활성화되어 있는지 확인

### 카카오맵 크롤링 오류
- Playwright headless 모드 이슈일 수 있음
- `src/services/kakao.py`에서 `headless=False`로 변경해서 테스트

### API 키 오류
```bash
# 환경변수 로드 확인
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"
```

---

## 📊 모니터링

### 로그 확인
```bash
# 백엔드 로그
tail -f api.log

# 프론트엔드 로그 (npm)
cd frontend/app && npm run dev
```

### API 상태 확인
```bash
curl http://localhost:8000/
# 응답: {"message": "Korean Food Agent API", "version": "1.0.0"}
```

---

## 🔐 보안 설정 (프로덕션)

### 1. 환경 변수 보호
```bash
# .env 파일 권한 제한
chmod 600 .env
```

### 2. CORS 설정
`api/main.py`의 CORS 설정 수정:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Supabase RLS 강화
필요시 `docs/supabase_schema.sql`의 RLS 정책 수정

---

## 📦 업데이트

```bash
# 코드 업데이트
git pull origin main

# 의존성 업데이트
pip install -r requirements.txt --upgrade
cd frontend/app && npm install

# Playwright 브라우저 업데이트
playwright install chromium

# 재시작
./run_all.sh
```

---

## 📚 추가 문서

- [README.md](../README.md) - 프로젝트 개요
- [research_note.md](./research_note.md) - 상세 기술 문서
- [supabase_schema.sql](./supabase_schema.sql) - DB 스키마

---

## ❓ 문제가 있나요?

1. [GitHub Issues](https://github.com/your-repo/issues) 검색
2. 새 이슈 생성
3. 상세한 오류 로그와 환경 정보 포함
