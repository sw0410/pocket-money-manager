# budget_app/models.py
from dataclasses import dataclass, field
from typing import List


@dataclass
class Transaction:
    """단일 거래 내역 데이터 모델
    
    필드 규격:
    - id: 고유 식별자 (양의 정수)
    - type: 거래 유형 ('income' 또는 'expense')
    - date: 거래 일자 (YYYY-MM-DD)
    - amount: 거래 금액 (양의 정수)
    - category: 카테고리명
    - memo: 선택 메모 (기본값: 빈 문자열)
    - tags: 태그 목록 (기본값: 빈 리스트)
    """
    id: int
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class Category:
    """카테고리 데이터 모델
    
    필드 규격:
    - id: 고유 식별자 (양의 정수)
    - name: 카테고리명
    """
    id: int
    name: str


@dataclass
class Budget:
    """월별 목표 예산 데이터 모델
    
    필드 규격:
    - month: 대상 연월 (YYYY-MM)
    - amount: 설정 예산 금액 (양의 정수)
    """
    month: str
    amount: int