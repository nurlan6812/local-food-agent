-- Korean Food Agent Supabase Schema
-- Supabase SQL Editor에서 이 파일을 실행하세요

-- ===================================
-- 1. food_images 테이블 생성
-- ===================================

CREATE TABLE IF NOT EXISTS food_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 이미지 정보
    image_url TEXT NOT NULL,

    -- 음식 정보
    food_name TEXT NOT NULL,
    food_verified BOOLEAN DEFAULT false,
    food_source_type TEXT DEFAULT 'unknown',  -- "restaurant", "home_cooked", "delivery", "unknown"

    -- 식당 정보 (선택사항)
    restaurant_name TEXT,
    restaurant_verified BOOLEAN DEFAULT false,

    -- 위치 정보 (선택사항)
    location TEXT,

    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================
-- 2. 인덱스 생성 (검색 성능 향상)
-- ===================================

-- 음식 이름으로 검색
CREATE INDEX IF NOT EXISTS idx_food_images_food_name
ON food_images(food_name);

-- 식당 이름으로 검색
CREATE INDEX IF NOT EXISTS idx_food_images_restaurant_name
ON food_images(restaurant_name)
WHERE restaurant_name IS NOT NULL;

-- 검증된 데이터만 조회
CREATE INDEX IF NOT EXISTS idx_food_images_verified
ON food_images(food_verified, restaurant_verified);

-- 생성일 기준 정렬
CREATE INDEX IF NOT EXISTS idx_food_images_created_at
ON food_images(created_at DESC);

-- 출처 타입으로 필터링
CREATE INDEX IF NOT EXISTS idx_food_images_source_type
ON food_images(food_source_type);

-- ===================================
-- 3. RLS (Row Level Security) 설정
-- ===================================

-- RLS 활성화
ALTER TABLE food_images ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기 가능
CREATE POLICY "food_images_select_policy"
ON food_images FOR SELECT
USING (true);

-- 모든 사용자가 삽입 가능
CREATE POLICY "food_images_insert_policy"
ON food_images FOR INSERT
WITH CHECK (true);

-- 모든 사용자가 업데이트 가능
CREATE POLICY "food_images_update_policy"
ON food_images FOR UPDATE
USING (true);

-- ===================================
-- 4. Storage Bucket 생성 (이미지 저장용)
-- ===================================

-- 중요: 버킷 이름은 'images'여야 합니다 (코드에서 사용)
-- Supabase Storage에서 수동으로 생성:
-- 1. Storage > Create bucket
-- 2. Name: images
-- 3. Public bucket: ✅ 체크
-- 4. Create

-- 또는 SQL로 생성 (Supabase CLI 필요):
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('images', 'images', true)
-- ON CONFLICT (id) DO NOTHING;

-- Storage Bucket의 RLS 설정:
-- Storage > images > Policies
-- "Allow public access" 선택 또는 커스텀 정책:
-- - Policy name: Public Access
-- - Allowed operation: All
-- - Policy definition: true

-- ===================================
-- 5. 함수: updated_at 자동 업데이트
-- ===================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
DROP TRIGGER IF EXISTS update_food_images_updated_at ON food_images;

CREATE TRIGGER update_food_images_updated_at
    BEFORE UPDATE ON food_images
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===================================
-- 완료!
-- ===================================

-- 테이블 확인
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'food_images'
ORDER BY ordinal_position;
