import re

def apply_masking(text):
    if not text:
        return ""
        
    masked_text = text
    
    # 1. 치환 대상 회사명 (LG 관련)
    company_names = [
        r'LG유플러스',
        r'엘지유플러스',
        r'LG U\+',
        r'LG',
        r'엘지'
    ]
    
    for name in company_names:
        # 대소문자 무시 치환
        masked_text = re.sub(name, 'OOO', masked_text, flags=re.IGNORECASE)
        
    # 2. 고객 개인정보 마스킹 (정규표현식 기반)
    # 전화번호 형식 (010-1234-5678, 02-123-4567 등)
    phone_pattern = r'0\d{1,2}-\d{3,4}-\d{4}'
    masked_text = re.sub(phone_pattern, '[전화번호]', masked_text)
    
    # 이메일 형식
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    masked_text = re.sub(email_pattern, '[이메일]', masked_text)
    
    # 주민등록번호 형식
    jumin_pattern = r'\d{6}-\d{7}'
    masked_text = re.sub(jumin_pattern, '[주민번호]', masked_text)
    
    # (선택적) 이름 마스킹 - 매우 가변적이므로 완벽한 정규식은 어려울 수 있음
    # 필요하다면 추가 로직 (예: 성+이름 구조 등) 넣을 수 있음
    
    return masked_text

if __name__ == "__main__":
    # Test cases
    test_text = "안녕하세요. 엘지유플러스 고객센터입니다. 제 이름은 홍길동이고 연락처는 010-1234-5678 입니다. LG u+ 서비스 불만. LG폰."
    print("Original:", test_text)
    print("Masked:", apply_masking(test_text))
