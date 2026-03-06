import streamlit as st
import database as db
from masking import apply_masking
from gemini_api import check_api_key_validity, generate_mail
import datetime

# --- Constants & Config ---
st.set_page_config(page_title="내용증명 자동 작성 프로그램", page_icon="📝", layout="wide")

TYPES = ["성희롱", "성희롱 + 욕설", "성희롱 + 전화공세", "성희롱 + 욕설 + 전화공세", "욕설", "욕설 + 전화공세", "전화공세", "기타"]
LEVELS = ["1차", "2차", "3차", "기타"]

# --- Session State ---
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# --- CSS ---
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
    }
    h1 {
        color: #1f2937;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    h2 {
        color: #374151;
        font-weight: 600;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e5e7eb;
    }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
    }
    .stTextArea textarea {
        border-radius: 6px;
    }
    .masked-text-box {
        background-color: #f3f4f6;
        padding: 1rem;
        border-radius: 6px;
        border: 1px solid #e5e7eb;
        font-family: monospace;
        white-space: pre-wrap;
    }
    .result-box {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 8px;
        border: 1px solid #d1d5db;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-top: 1rem;
        white-space: pre-wrap;
        white-space: pre-wrap;
        line-height: 1.6;
    }
    
    /* data_editor (glide-data-grid) 내부 특정 컬럼 스타일 강제 적용 시도 
       주의: Streamlit의 glide-data-grid는 canvas 위에 그려지기 때문에 
       일반적인 CSS text-align 제어가 완벽히 100% 동작하지 않을 수 있습니다. 
       다만, st.data_editor 속성만으로는 정렬 지원이 안 되므로 최선의 우회 방법을 추가합니다.
    */
    div[data-testid="stDataFrame"] div[class*="glideDataEditor"] {
        text-align: center;
    }
    
    /* Streamlit data editor 컬럼 헤더 버튼 메뉴 한글화 CSS 해킹 */
    div[data-testid="stDataFrame"] span:contains("Autosize") {
        visibility: hidden;
        position: relative;
    }
    div[data-testid="stDataFrame"] span:contains("Autosize")::after {
        content: "자동 크기 조절";
        visibility: visible;
        position: absolute;
        left: 0;
    }
    div[data-testid="stDataFrame"] span:contains("Pin column") {
        visibility: hidden;
        position: relative;
    }
    div[data-testid="stDataFrame"] span:contains("Pin column")::after {
        content: "컬럼 고정";
        visibility: visible;
        position: absolute;
        left: 0;
    }
    div[data-testid="stDataFrame"] span:contains("Hide column") {
        visibility: hidden;
        position: relative;
    }
    div[data-testid="stDataFrame"] span:contains("Hide column")::after {
        content: "컬럼 숨기기";
        visibility: visible;
        position: absolute;
        left: 0;
    }
</style>
<script>
    // CSS :contains 선택자가 없기 때문에 자바스크립트로 한글 변환 처리를 보완
    function translateGridMenus() {
        const spans = document.querySelectorAll('span');
        spans.forEach(span => {
            if(span.textContent === 'Autosize') span.textContent = '자동 크기 맞춤';
            if(span.textContent === 'Pin column') span.textContent = '열 고정';
            if(span.textContent === 'Hide column') span.textContent = '열 숨기기';
            // 메뉴가 나타날 때 생성되는 span 태그들의 텍스트를 감지하여 변경
        });
    }
    // MutationObserver를 사용하여 메뉴가 DOM에 추가될 때마다 번역 스크립트 실행
    const observer = new MutationObserver((mutations) => {
        translateGridMenus();
    });
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# --- App Logic ---

def login_sidebar():
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔒 관리자 메뉴")
    if not st.session_state.admin_logged_in:
        with st.sidebar.form("login_form"):
            password = st.text_input("비밀번호", type="password")
            submit_button = st.form_submit_button("로그인")
            
            if submit_button:
                if password == db.get_setting("admin_password"):
                    st.session_state.admin_logged_in = True
                    st.success("로그인 성공")
                    st.rerun()
                else:
                    st.error("비밀번호가 틀렸습니다.")
    else:
        st.sidebar.success("관리자 로그인 상태입니다.")
        if st.sidebar.button("로그아웃"):
            st.session_state.admin_logged_in = False
            st.rerun()

def admin_page():
    st.title("⚙️ 관리자 설정 및 데이터 관리")
    
    tab1, tab2 = st.tabs(["API 및 설정", "학습 데이터 관리"])
    
    with tab1:
        st.subheader("제미나이 API 키 등록 (공용 키)")
        current_api_key = db.get_setting("gemini_api_key")
        view_key = ""
        if current_api_key:
            view_key = current_api_key[:4] + "*" * (len(current_api_key)-8) + current_api_key[-4:] if len(current_api_key) > 8 else "***..."
            st.info(f"현재 데이터베이스에 등록된 공용 API 키: {view_key}")
            if st.button("공용 API 키 삭제"):
                db.set_setting("gemini_api_key", "")
                st.success("데이터베이스에서 공용 API 키가 삭제되었습니다.")
                st.rerun()
                
        new_api_key = st.text_input("새로운 API 키 입력", type="password", help="여기에 등록된 키는 사용자가 자신의 키를 입력하지 않았을 때 예비용으로 사용될 수 있습니다.")
        save_to_db = st.checkbox("API 키를 데이터베이스에 영구 저장 (공용 키로 모든 사용자에게 허용)", value=True)
        
        if st.button("API 키 유효성 테스트 및 적용"):
            if new_api_key:
                is_valid, msg = check_api_key_validity(new_api_key)
                if is_valid:
                    if save_to_db:
                        db.set_setting("gemini_api_key", new_api_key)
                        st.success(f"성공: {msg} (데이터베이스에 공용 키로 저장됨)")
                    else:
                        st.session_state.admin_temp_api_key = new_api_key
                        st.success(f"성공: {msg} (데이터베이스에 저장하지 않고 권리자의 현재 세션에서만 적용됨)")
                else:
                    st.error(f"실패: {msg}")
            else:
                st.warning("API 키를 입력해주세요.")
                
        st.markdown("---")
        st.subheader("관리자 비밀번호 변경")
        current_pw_input = st.text_input("현재 비밀번호", type="password", key="cur_pw")
        new_pw_input1 = st.text_input("새 비밀번호", type="password", key="new_pw1")
        new_pw_input2 = st.text_input("새 비밀번호 확인", type="password", key="new_pw2")
        
        if st.button("비밀번호 변경"):
            if not current_pw_input or not new_pw_input1 or not new_pw_input2:
                st.warning("모든 비밀번호 필드를 입력해주세요.")
            elif current_pw_input != db.get_setting("admin_password"):
                st.error("현재 비밀번호가 일치하지 않습니다.")
            elif new_pw_input1 != new_pw_input2:
                st.error("새 비밀번호가 서로 일치하지 않습니다.")
            else:
                db.set_setting("admin_password", new_pw_input1)
                st.success("비밀번호가 성공적으로 변경되었습니다.")
                
    with tab2:
        st.subheader("내용증명 학습하기 (새 데이터 추가)")
        col1, col2 = st.columns(2)
        with col1:
            sel_level = st.selectbox("대응 수준", LEVELS)
        with col2:
            sel_type = st.selectbox("문제행동 유형", TYPES)
            
        original_text = st.text_area("학습할 내용증명 원본 (수신/발신인 텍스트는 빼주세요)", height=200)
        
        if st.button("내용 마스킹 처리 및 학습"):
            if original_text.strip():
                # 1. 마스킹 처리
                masked = apply_masking(original_text)
                st.markdown("**(미리보기) 마스킹 된 데이터 (이 데이터로 제미나이가 학습합니다)**")
                st.markdown(f'<div class="masked-text-box">{masked}</div>', unsafe_allow_html=True)
                
                # 2. DB 저장
                date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.add_template(date_str, sel_type, sel_level, original_text, masked)
                st.success("✅ 학습용 내용증명이 성공적으로 저장되었습니다.")
            else:
                st.warning("학습할 내용을 텍스트 영역에 입력해주세요.")
                
        st.markdown("---")
        st.subheader("기 학습 내역 관리")
        templates = db.get_all_templates()
        if not templates:
            st.info("저장된 학습 데이터가 없습니다.")
        else:
            # 1부터 N까지 순차적인 번호 부여
            for idx, t in enumerate(templates, start=1):
                with st.expander(f"[{idx}] {t['date']} | {t['level']} | {t['type']}"):
                    edit_col1, edit_col2 = st.columns(2)
                    
                    type_idx = TYPES.index(t['type']) if t['type'] in TYPES else 0
                    level_idx = LEVELS.index(t['level']) if t['level'] in LEVELS else 0
                    
                    with edit_col1:
                        edit_level = st.selectbox("대응 수준", LEVELS, index=level_idx, key=f"edit_lvl_{t['id']}")
                    with edit_col2:
                        edit_type = st.selectbox("문제행동 유형", TYPES, index=type_idx, key=f"edit_typ_{t['id']}")
                        
                    edit_text = st.text_area("마스킹 텍스트 수정 (수정 후 아래 버튼을 누르면 저장됩니다)", value=t['masked_text'], height=150, key=f"edit_txt_{t['id']}")
                    
                    action_col1, action_col2 = st.columns(2)
                    with action_col1:
                        if st.button("수정 내용 저장", key=f"update_{t['id']}"):
                            db.update_template(t['id'], edit_type, edit_level, t['original_text'], edit_text)
                            st.success("데이터가 성공적으로 수정되었습니다.")
                            st.rerun()
                    with action_col2:
                        if st.button("삭제", key=f"del_{t['id']}"):
                            db.delete_template(t['id'])
                            st.rerun()

def generator_page():
    st.title("📝 내용증명 자동 작성 프로그램")
    st.markdown("입력하신 상황과 기존 학습된 문체를 바탕으로 제미나이(Gemini)가 내용증명 초안을 작성합니다.")
    
    # 1. 사용자 개별 API 키 입력 지원
    saved_user_key = st.session_state.get('user_api_key', '')
    user_input_key = st.text_input("본인의 제미나이 API 키 (필수)", value=saved_user_key, type="password", help="발급받은 제미나이 API 키를 입력하세요. 미입력 시 시스템 공용 키가 있다면 그것을 사용합니다.")
    save_user_key = st.checkbox("내 브라우저 세션에 API 키 단기 저장 (일회성 테스트라면 체크 해제)", value=bool(saved_user_key))
    
    if save_user_key and user_input_key:
        st.session_state.user_api_key = user_input_key
    elif not save_user_key and 'user_api_key' in st.session_state:
        del st.session_state['user_api_key']
        
    st.markdown("---")
    
    # 2. 최종 API 키 결정 (사용자 입력 > 관리자 임시 키 > DB 공용 키)
    admin_temp_key = st.session_state.get('admin_temp_api_key', '')
    db_global_key = db.get_setting("gemini_api_key")
    
    api_key = user_input_key or admin_temp_key or db_global_key

    col1, col2 = st.columns(2)
    with col1:
        req_level = st.selectbox("대응 수준 선택", ["전체"] + LEVELS, index=0)
    with col2:
        req_type = st.selectbox("문제행동 유형 선택", ["전체"] + TYPES, index=0)
        
    user_context = st.text_area("사건 내용 및 추가 요구사항 (최대한 구체적으로 기재)", height=150, 
                              placeholder="예: 고객이 2월 25일에 매장에 방문하여 직원에게 폭언을 함. CCTV 확보 완료.")
                              
    st.markdown("**문제행동 내역 정리 (선택 입력 / 빈칸인 경우 무시됨)**")
    
    # 키 변경으로 구 세션 잠재("\ub0a0\uc9dc","상\ub2f4\uc0ac"...) 식 초기값 추제 및 완전 비워졌하기
    if 'incident_table_v2' not in st.session_state:
        st.session_state.incident_table_v2 = [{"col1": "", "col2": "", "col3": "", "col4": ""}]
    
    # 순번 조건부 부여: col2/col3/col4 중 하나라도 입력 시에만 표시
    for i, row in enumerate(st.session_state.incident_table_v2):
        has_content = any(str(row.get(k, "")).strip() for k in ["col2", "col3", "col4"])
        row["col1"] = str(i + 1) if has_content else ""

    edited_data = st.data_editor(
        st.session_state.incident_table_v2,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=False,
        column_config={
            "col1": st.column_config.TextColumn("순번", width=60, disabled=True),
            "col2": st.column_config.TextColumn("날짜", width=120),
            "col3": st.column_config.TextColumn("상담사", width=104),
            "col4": st.column_config.TextColumn("대화내용", width=650),
        },
        key="incident_table_widget"
    )
    
    # 전체 삭제 시 최소 1행 유지 (빈 행)
    needs_rerun = False
    if len(edited_data) == 0:
        edited_data = [{"col1": "", "col2": "", "col3": "", "col4": ""}]
        needs_rerun = True
    else:
        for i, row in enumerate(edited_data):
            has_content = any(str(row.get(k, "")).strip() for k in ["col2", "col3", "col4"])
            row["col1"] = str(i + 1) if has_content else ""

    if edited_data != st.session_state.incident_table_v2 or needs_rerun:
        st.session_state.incident_table_v2 = edited_data
        st.rerun()
                              
    if st.button("내용증명 생성하기", type="primary"):
        if not api_key:
            st.error("💡 제미나이 API 키를 상단에 입력해야 합니다.")
            return
            
        final_context = user_context.strip()
        
        has_table_data = False
        table_md = "\n\n[문제행동 내역 표]\n| 순번 | 날짜 | 상담사 | 대화내용 |\n|---|---|---|---|\n"
        for row in edited_data:
            if any(str(row.get(k, "")).strip() for k in ["col2", "col3", "col4"] if row.get(k) is not None):
                no = str(row.get("col1", "")).strip()
                date = str(row.get("col2", "")).strip()
                counselor = str(row.get("col3", "")).strip()
                content = str(row.get("col4", "")).strip()
                table_md += f"| {no} | {date} | {counselor} | {content} |\n"
                has_table_data = True
        if has_table_data:
            final_context += table_md

        with st.spinner("제미나이가 기존 데이터 구조를 분석하여 내용증명을 작성하고 있습니다..."):
            # 조건에 맞는 학습 데이터 불러오기
            matching_templates = db.get_templates_by_criteria(
                type_=req_type if req_type != "전체" else None,
                level=req_level if req_level != "전체" else None
            )
            
            if not matching_templates:
                st.warning("⚠️ 선택하신 '문제행동 유형'과 '대응 수준'에 맞는 학습된 내용증명 데이터가 없습니다. AI가 일반적인 법적 양식에 맞춰 초안을 작성합니다.")
            
            # 여기서 사용자 입력도 마스킹 처리 (안전을 위해)
            safe_context = apply_masking(final_context)
            
            success, result_text = generate_mail(api_key, matching_templates, req_type, req_level, safe_context)
            
            if success:
                st.success("생성 완료!")
                st.markdown('<div class="result-box">' + result_text + '</div>', unsafe_allow_html=True)
                st.info("복사하여 사용 시 수신/발신인 부분만 추가로 기입하시면 됩니다.")
            else:
                st.error(f"생성 실패: {result_text}")


def main():
    st.sidebar.title("메뉴")
    menu = st.sidebar.radio("", ["✨ 내용증명 생성기", "⚙️ 설정 및 학습 데이터"])
    
    login_sidebar()
    
    if menu == "✨ 내용증명 생성기":
        generator_page()
    elif menu == "⚙️ 설정 및 학습 데이터":
        if st.session_state.admin_logged_in:
            admin_page()
        else:
            st.warning("관리자 메뉴에 접근하려면 좌측 하단에서 로그인해주세요.")
            
if __name__ == "__main__":
    main()
