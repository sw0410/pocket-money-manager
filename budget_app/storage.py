# budget_app/storage.py
import csv  # <-- 1. csv 모듈 추가
import json
import os
from dataclasses import asdict
from typing import Any, Dict, Generator, Iterable, List

from budget_app.models import Budget, Category, Transaction

# CSV 헤더 규격 (물리 저장 포맷이므로 Storage에 배치)
CSV_HEADERS = ["date", "type", "category", "amount", "memo", "tags"]


class Storage:
    """데이터 영속성 및 파일 입출력을 전담하는 저장소 클래스"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.tx_file = os.path.join(self.data_dir, "transactions.jsonl")
        self.cat_file = os.path.join(self.data_dir, "categories.jsonl")
        self.budget_file = os.path.join(self.data_dir, "budgets.jsonl")

    def _atomic_write_jsonl(self, filepath: str, items: Iterable[dict]) -> None:
        """임시 파일(.tmp)에 기록 후 교체하여 쓰기 도중 충돌 시 원본을 보존합니다."""
        tmp_file = f"{filepath}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        os.replace(tmp_file, filepath)

    # --- 거래 내역 ---

    def stream_transactions(self) -> Generator[Transaction, None, None]:
        """거래 내역 전체를 한 줄씩 제너레이터로 스트리밍 반환합니다."""
        if not os.path.exists(self.tx_file):
            return
        with open(self.tx_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                yield Transaction(**data)

    def append_transaction(self, tx: Transaction) -> None:
        """새 단일 거래를 파일 끝에 즉시 덧붙입니다 (상수 시간)."""
        with open(self.tx_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(tx), ensure_ascii=False) + "\n")

    def save_all_transactions(self, transactions: Iterable[Transaction]) -> None:
        """전체 거래 목록을 원자적으로 덮어씁니다 (수정/삭제 시 사용)."""
        self._atomic_write_jsonl(
            self.tx_file, (asdict(tx) for tx in transactions)
        )

    # --- 카테고리 ---

    def load_categories(self) -> List[Category]:
        """카테고리 전체 목록을 불러옵니다."""
        if not os.path.exists(self.cat_file):
            return []
        categories = []
        with open(self.cat_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                categories.append(Category(**json.loads(line)))
        return categories

    def save_categories(self, categories: Iterable[Category]) -> None:
        """카테고리 목록을 원자적으로 저장합니다."""
        self._atomic_write_jsonl(
            self.cat_file, (asdict(c) for c in categories)
        )

    # --- 예산 ---

    def load_budgets(self) -> List[Budget]:
        """월별 예산 전체 목록을 불러옵니다."""
        if not os.path.exists(self.budget_file):
            return []
        budgets = []
        with open(self.budget_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                budgets.append(Budget(**json.loads(line)))
        return budgets

    def save_budgets(self, budgets: Iterable[Budget]) -> None:
        """월별 예산 목록을 원자적으로 저장합니다."""
        self._atomic_write_jsonl(
            self.budget_file, (asdict(b) for b in budgets)
        )

    # --- CSV 입출력 (Storage 전담 책임으로 신설) ---

    def export_transactions_csv(self, filepath: str, transactions: Iterable[Transaction]) -> int:
        """거래 목록을 받아 물리 CSV 파일(utf-8-sig)로 기록합니다."""
        count = 0
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            for tx in transactions:
                writer.writerow([tx.date, tx.type, tx.category, tx.amount, tx.memo, ",".join(tx.tags)])
                count += 1
        return count

    def read_transactions_csv(self, filepath: str) -> Generator[Dict[str, str], None, None]:
        """물리 CSV 파일에서 한 줄씩 Dict 형태로 스트리밍 읽기를 수행합니다."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row