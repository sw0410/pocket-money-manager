import json
from dataclasses import dataclass, asdict

# 1. 형태 언어 규격
@dataclass
class Transaction:
    id: int
    date: str
    transaction_type: str
    category: str
    amount: int

# 2. 이미 존재하는 온전한 표본 1개 (Dummy Instance)
sample_tx = Transaction(
    id=1,
    date="2026-09-14",
    transaction_type="지출",
    category="음식",
    amount=30000
)

# 3. 직렬화 변환 (4-1의 핵심 동작)
tx_dict = asdict(sample_tx)
tx_json = json.dumps(tx_dict, ensure_ascii=False)

# 4. 출력하여 눈으로 확인
print("딕셔너리 형태:", tx_dict)
print("JSON 문자열 형태:", tx_json)
print("문자열 타입 확인:", type(tx_json))