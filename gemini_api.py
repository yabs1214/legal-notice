import google.generativeai as genai
import textwrap

def configure_gemini(api_key):
    genai.configure(api_key=api_key)

def check_api_key_validity(api_key):
    try:
        configure_gemini(api_key)
        # 간단한 요청으로 키 검증
        model = genai.GenerativeModel('gemini-2.5-flash')
        model.generate_content("test")
        return True, "API 키가 성공적으로 인증되었습니다."
    except Exception as e:
        return False, f"API 키 인증 실패: {str(e)}"

def generate_mail(api_key, templates, current_type, current_level, user_context):
    """
    제미나이 API를 호출하여 내용증명을 생성합니다.
    templates: 기존 학습용 내용증명 리스트 [{'original_text': '', 'masked_text': ''}, ...]
    user_context: 사용자가 입력한 구체적 상황
    """
    configure_gemini(api_key)
    # 내용증명 생성에는 성능이 좋은 pro 모델을 권장 (또는 flash 사용)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 1. 학습 데이터 (Few-shot prompting 구성)
    training_context = ""
    if templates:
        training_context += "아래는 기존에 작성된 내용증명 샘플들입니다. 이 샘플들의 구조와 어투, 문체, 법적 용어 사용 등을 학습하여, 이와 유사한 전문적인 톤을 유지해주세요.\n\n"
        for i, t in enumerate(templates):
            training_context += f"[샘플 {i+1}]\n{t['masked_text']}\n\n"
    else:
        training_context += "기존 내용증명 샘플이 없습니다. 일반적인 전문적이고 단호한 법적 통지문(내용증명)의 문체를 사용하세요.\n\n"
        
    # 2. 프롬프트 작성
    prompt = textwrap.dedent(f"""
    당신은 기업의 법무팀 담당자로, 문제행동 소비자(블랙컨슈머)에게 발송할 내용증명 통고서를 작성하는 업무를 맡았습니다.
    
    {training_context}
    
    새로운 상황에 맞춰 내용증명을 작성해야 합니다.
    문제행동 유형: {current_type}
    대응 수준: {current_level}
    
    [사건 내용 및 요구사항 요약]
    {user_context}
    
    [작성 지침]
    1. 수신인, 발신인 정보는 절대 제외하고 "제목"과 "본문"만 작성하세요. 
    2. 본문은 위 샘플들처럼 논리적이고, 단호하며, 1차/2차/3차 대응 수준에 맞는 법적 경고 수위를 포함하세요.
    3. 구구절절한 서술은 피하고, 사실관계 확인 및 요구사항, 향후 조치(법적 조치 예고 등)를 명확히 기재하세요.
    4. 회사명과 고객 이름이 필요한 곳은 OOO 등의 마스킹 기호를 그대로 사용하세요.
    5. 출력 형식을 반드시 아래와 같이 맞춰주세요:
    
    [제목]
    제목 내용
    
    [본문]
    본문 내용
    """)

    try:
        response = model.generate_content(prompt)
        # response가 반환되면 텍스트 추출
        text_output = response.text
        return True, text_output
    except Exception as e:
        return False, f"오류 발생: {str(e)}"

