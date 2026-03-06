import os
import streamlit as st
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Supabase 클라이언트를 생성하여 반환합니다."""
    # Streamlit Cloud에서는 st.secrets 사용, 로컬에서는 환경변수 사용
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
    
    if not url or not key:
        st.error("⚠️ Supabase URL과 Key가 설정되지 않았습니다. Settings → Secrets에서 설정해주세요.")
        st.stop()
    
    return create_client(url, key)

def init_db():
    """DB 초기화 - 기본 관리자 비밀번호가 없으면 생성합니다."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("settings").select("value").eq("key", "admin_password").execute()
        if not result.data:
            supabase.table("settings").insert({"key": "admin_password", "value": "admin1234"}).execute()
    except Exception:
        pass  # 테이블이 아직 없으면 무시 (첫 실행 시)

def get_setting(key):
    try:
        supabase = get_supabase_client()
        result = supabase.table("settings").select("value").eq("key", key).execute()
        if result.data:
            return result.data[0]["value"]
        return None
    except Exception:
        return None

def set_setting(key, value):
    try:
        supabase = get_supabase_client()
        # upsert: 있으면 업데이트, 없으면 삽입
        supabase.table("settings").upsert({"key": key, "value": value}).execute()
    except Exception as e:
        st.error(f"설정 저장 실패: {e}")

def add_template(date, type_, level, original_text, masked_text):
    try:
        supabase = get_supabase_client()
        supabase.table("templates").insert({
            "date": date,
            "type": type_,
            "level": level,
            "original_text": original_text,
            "masked_text": masked_text
        }).execute()
    except Exception as e:
        st.error(f"데이터 추가 실패: {e}")

def get_all_templates():
    try:
        supabase = get_supabase_client()
        result = supabase.table("templates").select("*").order("id", desc=True).execute()
        templates = []
        for row in result.data:
            templates.append({
                'id': row['id'],
                'date': row['date'],
                'type': row['type'],
                'level': row['level'],
                'original_text': row['original_text'],
                'masked_text': row['masked_text']
            })
        return templates
    except Exception:
        return []

def get_templates_by_criteria(type_=None, level=None):
    try:
        supabase = get_supabase_client()
        query = supabase.table("templates").select("original_text, masked_text")
        
        if type_ and type_ != "전체":
            query = query.eq("type", type_)
        if level and level != "전체":
            query = query.eq("level", level)
        
        result = query.execute()
        return [{'original_text': r['original_text'], 'masked_text': r['masked_text']} for r in result.data]
    except Exception:
        return []

def update_template(template_id, type_, level, original_text, masked_text):
    try:
        supabase = get_supabase_client()
        supabase.table("templates").update({
            "type": type_,
            "level": level,
            "original_text": original_text,
            "masked_text": masked_text
        }).eq("id", template_id).execute()
    except Exception as e:
        st.error(f"데이터 수정 실패: {e}")

def delete_template(template_id):
    try:
        supabase = get_supabase_client()
        supabase.table("templates").delete().eq("id", template_id).execute()
    except Exception as e:
        st.error(f"데이터 삭제 실패: {e}")

# Initialize DB on import
init_db()
