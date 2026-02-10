# PWA 아이콘 생성 가이드

## 빠른 방법 (권장)

### 1. 온라인 생성기 사용
https://realfavicongenerator.net/
1. icon.svg 업로드
2. 모든 플랫폼용 아이콘 다운로드
3. `public/` 폴더에 복사

### 2. ImageMagick 사용 (로컬)
```bash
# SVG -> PNG 변환
convert public/icon.svg -resize 192x192 public/icon-192.png
convert public/icon.svg -resize 512x512 public/icon-512.png
```

## 현재 상태

✅ manifest.json 생성됨
✅ next-pwa 설정 완료
✅ icon.svg 생성됨
⏳ icon-192.png, icon-512.png 필요

## 테스트

```bash
npm run dev
```

브라우저:
1. http://localhost:3000 접속
2. 개발자 도구 > Application > Manifest 확인
3. 프로덕션 배포 후 "홈 화면에 추가" 가능
