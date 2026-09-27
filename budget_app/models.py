from dataclasses import dataclass, field

@dataclass
class Transaction:
    """단일 거래 내역 데이터 모델"""
    id: int
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)  # List 대신 내장 list 사용

@dataclass
class Category:
    """카테고리 데이터 모델"""
    id: int
    name: str

@dataclass
class Budget:
    """월별 목표 예산 데이터 모델"""
    month: str
    amount: int