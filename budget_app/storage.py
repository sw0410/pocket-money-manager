# budget_app/storage.py
import csv
import json
import os
from collections.abc import Iterable, Iterator
from dataclasses import asdict

from budget_app.models import Budget, Category, Transaction

CSV_HEADERS = ["date", "type", "category", "amount", "memo", "tags"]


class Storage:
    """JSONL 및 JSON 기반 파일 영속성을 담당하는 저장소 클래스"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.tx_file = os.path.join(self.data_dir, "transactions.jsonl")
        self.cat_file = os.path.join(self.data_dir, "categories.json")
        self.budget_file = os.path.join(self.data_dir, "budgets.json")

    # --- 내부 보조 메서드 (원자적 쓰기) ---

    def _atomic_write_jsonl(self, filepath: str, items: Iterable[dict]) -> None:
        """임시 파일을 생성하여 기록한 후 원본 파일로 원자적 치환(Atomic Replace)합니다."""
        temp_path = f"{filepath}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        os.replace(temp_path, filepath)

    # --- 카테고리 입출력 ---

    def load_categories(self) -> list[Category]:
        """categories.json 파일에서 카테고리 목록을 불러옵니다."""
        if not os.path.exists(self.cat_file):
            return []
        with open(self.cat_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Category(**item) for item in data]

    def save_categories(self, categories: list[Category]) -> None:
        """카테고리 목록을 categories.json 파일에 안전하게 저장합니다."""
        temp_path = f"{self.cat_file}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in categories], f, ensure_ascii=False, indent=2)
        os.replace(temp_path, self.cat_file)

    # --- 예산 입출력 ---

    def load_budgets(self) -> list[Budget]:
        """budgets.json 파일에서 예산 목록을 불러옵니다."""
        if not os.path.exists(self.budget_file):
            return []
        with open(self.budget_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Budget(**item) for item in data]

    def save_budgets(self, budgets: list[Budget]) -> None:
        """예산 목록을 budgets.json 파일에 안전하게 저장합니다."""
        temp_path = f"{self.budget_file}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump([asdict(b) for b in budgets], f, ensure_ascii=False, indent=2)
        os.replace(temp_path, self.budget_file)

    # --- 거래 내역 입출력 (JSONL) ---

    def stream_transactions(self) -> Iterator[Transaction]:
        """transactions.jsonl 파일에서 거래 내역을 한 줄씩 제너레이터로 반환합니다."""
        if not os.path.exists(self.tx_file):
            return
        with open(self.tx_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield Transaction(**json.loads(line))

    def append_transaction(self, tx: Transaction) -> None:
        """거래 내역 1건을 transactions.jsonl 파일 맨 끝에 즉시 추가합니다."""
        with open(self.tx_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(tx), ensure_ascii=False) + "\n")

    def save_all_transactions(self, transactions: list[Transaction]) -> None:
        """전체 거래 목록을 원자적 쓰기로 transactions.jsonl에 갱신합니다."""
        self._atomic_write_jsonl(self.tx_file, (asdict(tx) for tx in transactions))

    # --- CSV 내보내기 / 가져오기 ---

    def export_transactions_csv(self, filepath: str, transactions: list[Transaction]) -> int:
        """거래 내역 목록을 CSV 파일로 내보냅니다."""
        temp_path = f"{filepath}.tmp"
        count = 0
        with open(temp_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            for tx in transactions:
                writer.writerow({
                    "date": tx.date,
                    "type": tx.type,
                    "category": tx.category,
                    "amount": tx.amount,
                    "memo": tx.memo,
                    "tags": ",".join(tx.tags),
                })
                count += 1
        os.replace(temp_path, filepath)
        return count

    def read_transactions_csv(self, filepath: str) -> Iterator[dict[str, str]]:
        """CSV 파일을 한 줄씩 딕셔너리 형태로 스트리밍 읽기합니다."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row