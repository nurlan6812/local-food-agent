# Korean Food Agent 🍜

LangGraph + Gemini 기반 한국 음식 AI 에이전트

음식 이미지를 분석하고, 식당 정보를 검색하며, 레시피와 영양정보를 제공하는 멀티모달 AI 에이전트입니다.

## ✨ 주요 기능

| 기능 | 설명 | 도구 |
|------|------|------|
| 🔍 **음식 이미지 인식** | Google Lens로 음식/식당 파악 | `search_food_by_image` |
| 🏪 **식당 검색** | 카카오맵 API + Playwright 크롤링으로 식당 정보 및 메뉴 조회 | `search_restaurant_info` |
| 📝 **후기 분석** | 카카오맵 후기 크롤링 및 AI 요약 | `get_restaurant_reviews` |
| 🍳 **레시피 검색** | 만개의레시피 등에서 크롤링 | `search_recipe_online` |
| 📊 **영양정보** | 칼로리, 단백질 등 영양성분 검색 | `get_nutrition_info` |
| 💾 **이미지 수집** | 새 음식 이미지 Supabase DB 저장 | `save_food_image`, `update_food_image` |

## 🛠️ 기술 스택

### Backend
| 레이어 | 기술 | 설명 |
|--------|------|------|
| **LLM** | Gemini 3.0 Flash | 멀티모달 언어 모델 |
| **에이전트** | LangGraph | ReAct 패턴 구현 |
| **메모리** | MemorySaver | 대화 히스토리 자동 관리 |
| **API** | FastAPI | 스트리밍 지원 백엔드 |
| **DB** | Supabase | PostgreSQL + Storage |
| **크롤링** | Playwright | 동적 웹 크롤링 |

### Frontend
- **Framework**: Next.js 16 (React 19)
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui, Radix UI
- **Map**: 카카오맵 JavaScript SDK

### External APIs
- **Google Lens**: Serper.dev (이미지 검색)
- **Kakao Local API**: 식당 검색
- **Web Search**: Serper.dev (텍스트 검색)

## 📁 프로젝트 구조

```
food_agent/
├── api/
│   └── main.py                 # FastAPI 백엔드 (SSE 스트리밍)
├── src/
│   ├── agent.py                # LangGraph ReAct 에이전트
│   ├── config.py               # 설정 관리
│   ├── db/
│   │   └── client.py           # Supabase 클라이언트
│   ├── services/
│   │   ├── serper.py           # Google Lens + 텍스트 검색
│   │   └── kakao.py            # 카카오맵 API + Playwright
│   └── tools/                  # LangChain 도구들
│       ├── image.py            # search_food_by_image
│       ├── restaurant.py       # search_restaurant_info, get_restaurant_reviews
│       ├── recipe.py           # search_recipe_online
│       ├── nutrition.py        # get_nutrition_info
│       ├── save_image.py       # save_food_image
│       └── update_image.py     # update_food_image
├── frontend/app/               # Next.js 프론트엔드
│   ├── app/
│   │   ├── page.tsx           # 메인 채팅 페이지
│   │   ├── layout.tsx         # 루트 레이아웃
│   │   └── globals.css        # 글로벌 스타일
│   ├── components/            # React 컴포넌트
│   │   ├── chat-input.tsx
│   │   ├── chat-message.tsx
│   │   ├── map-embed.tsx
│   │   ├── image-gallery.tsx
│   │   ├── restaurant-card.tsx
│   │   ├── theme-toggle.tsx
│   │   └── ui/                # shadcn/ui 컴포넌트
│   ├── hooks/
│   │   └── use-toast.ts       # Toast 알림 훅
│   └── lib/
│       ├── api.ts             # 백엔드 API 클라이언트
│       ├── types.ts           # TypeScript 타입
│       └── utils.ts           # 유틸리티 함수
├── docs/
│   ├── deployment.md          # 배포 가이드
│   ├── research_note.md       # 상세 기술 문서
│   └── supabase_schema.sql    # DB 스키마
├── scripts/
│   └── benchmark_latency.py   # 성능 측정
├── requirements.txt           # Python 의존성 (18개)
├── setup.sh                   # 자동 설치 스크립트
├── run_all.sh                 # 서버 실행 스크립트
├── .env.example               # 환경 변수 템플릿 (10개)
├── README.md                  # 이 파일
├── QUICK_START.md             # 5분 빠른 시작
├── VERIFICATION.md            # 코드 검증 결과
└── STRUCTURE.md               # 전체 폴더 구조
```

> **참고**: 전체 폴더 구조는 [STRUCTURE.md](STRUCTURE.md)를 참고하세요.

## 🚀 빠른 시작 (5분)

### 사전 준비

**필수 API 키 발급:**
- [Google AI (Gemini)](https://aistudio.google.com/app/apikey) - 무료
- [Serper.dev](https://serper.dev/) - 무료 2,500회/월
- [카카오 Developers](https://developers.kakao.com/) - 무료
- [Supabase](https://supabase.com/) - 무료 500MB

### 1. 설치

```bash
# 저장소 클론
git clone https://github.com/nurlan6812/food-agent.git
cd food_agent

# 자동 설치 실행
./setup.sh
```

### 2. 환경 변수 설정

```bash
nano .env
```

**필수 5개만 입력:**
```env
GOOGLE_API_KEY=실제-구글-API-키
SERPER_API_KEY=실제-Serper-API-키
KAKAO_API_KEY=실제-카카오-API-키
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=실제-Supabase-Anon-Key
```

### 3. Supabase 설정

**① 테이블 생성**
1. Supabase Dashboard → SQL Editor
2. `docs/supabase_schema.sql` 내용 복사
3. 실행 (Run)

**② Storage 버킷 생성**
1. Supabase Dashboard → Storage
2. Create bucket → 이름: `images`, Public 체크
3. Policies → Allow public access

### 4. 실행

```bash
./run_all.sh
```

**접속:**
- 🎨 프론트엔드: http://localhost:3000
- 🔧 백엔드 API: http://localhost:8000

끝! 🎉

---

## 📖 사용 예시

### 웹 인터페이스
1. http://localhost:3000 접속
2. 음식 이미지 업로드 또는 텍스트로 질문
3. 실시간 스트리밍 응답 확인

### Python API

```python
from src.agent import KoreanFoodAgent

agent = KoreanFoodAgent()

# 텍스트 질문
response = agent.chat("강남역 맛집 추천해줘")

# 이미지 질문
response = agent.chat("/path/to/food.jpg 이 음식 뭐야?")

# 스트리밍
for chunk in agent.stream("김치찌개 레시피 알려줘"):
    print(chunk)
```

### REST API

```bash
# 동기 채팅
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "불고기 레시피"}'

# 스트리밍 채팅 (SSE)
curl -N http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "불고기 레시피"}'
```

## 🔧 개발

### 수동 설치

```bash
# Python 패키지
pip install -r requirements.txt
playwright install chromium

# 프론트엔드
cd frontend/app
npm install
```

### 개별 실행

```bash
# 백엔드만
python -m uvicorn api.main:app --reload --port 8000

# 프론트엔드만
cd frontend/app && npm run dev
```

### 코드 구조

- **에이전트**: `src/agent.py` - LangGraph ReAct 에이전트
- **도구들**: `src/tools/` - 7개 LangChain 도구
- **서비스**: `src/services/` - 외부 API 클라이언트
- **백엔드**: `api/main.py` - FastAPI SSE 스트리밍
- **프론트엔드**: `frontend/app/` - Next.js 채팅 UI

## 🌐 배포

상세한 배포 가이드는 [docs/deployment.md](docs/deployment.md)를 참고하세요.

### 프로덕션 실행

```bash
# 백엔드
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# 프론트엔드
cd frontend/app
npm run build
npm start
```

## 📊 성능

- **Gemini 2.0 Flash 응답 속도**: 5-10초 (API 지연 포함)
- **스트리밍 지연**: 실시간 토큰 출력
- **도구 호출**: 병렬 처리 지원
- **이미지 검색**: Google Lens 기반

## 🧪 테스트

```bash
# Gemini 레이턴시 측정
python scripts/benchmark_latency.py
```

## 🔐 보안

- Supabase RLS 정책 적용
- Storage 공개 버킷 사용 (이미지)
- API 키는 `.env`에서 관리 (Git 제외)
- CORS 설정 필요 (프로덕션)

## 🤝 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

MIT License

## 📚 추가 문서

- [상세 기술 문서](docs/research_note.md)
- [배포 가이드](docs/deployment.md)
- [Supabase 스키마](docs/supabase_schema.sql)

## 💡 참고

- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Gemini API**: https://ai.google.dev/
- **Serper.dev**: https://serper.dev/
- **Supabase**: https://supabase.com/
