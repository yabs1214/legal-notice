-- Supabase SQL Editor에서 실행할 테이블 생성 스크립트

-- 1. settings 테이블 (API 키, 관리자 비밀번호 등)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- 기본 관리자 비밀번호 삽입
INSERT INTO settings (key, value) VALUES ('admin_password', 'admin1234')
ON CONFLICT (key) DO NOTHING;

-- 2. templates 테이블 (학습 데이터)
CREATE TABLE IF NOT EXISTS templates (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    date TEXT,
    type TEXT,
    level TEXT,
    original_text TEXT,
    masked_text TEXT
);

-- RLS (Row Level Security) 비활성화 (간단한 설정을 위해)
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;

-- 모든 사용자에게 접근 허용 정책
CREATE POLICY "Allow all on settings" ON settings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on templates" ON templates FOR ALL USING (true) WITH CHECK (true);
