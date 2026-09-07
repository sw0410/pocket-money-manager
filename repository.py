# repository.py
from dataclasses import asdict
import json
import os
from models import Transaction

FILE_PATH = "transactions.jsonl"


def load_transactions():
    """파일에서 트랜잭션을 한 행씩 읽어 yield로 스트리밍합니다."""
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                record = Transaction(
                    id=data["id"],
                    date=data["date"],
                    transaction_type=data["transaction_type"],
                    category=data["category"],
                    amount=data["amount"],
                )
                yield record


def save_transaction(record: Transaction):
    """단일 트랜잭션 인스턴스를 JSONL 파일 끝에 추가합니다."""
    with open(FILE_PATH, "a", encoding="utf-8") as f:
        line = json.dumps(asdict(record), ensure_ascii=False)
        f.write(line + "\n")