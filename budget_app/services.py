# 업무 규칙 및 계산 (검증, 통계 연산, 참조 무결성 확인)
import csv
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional, Tuple

from budget_app.models import Budget, Category, Transaction
from budget_app.storage import Storage


CSV_HEADERS = ["date", "type", "category", "amount", "memo", "tags"]


def validate_date(date_str: str) -> None:
    """날짜가 YYYY-MM-DD 형식인지 검증합니다."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("날짜 형식은 YYYY-MM-DD 이어야 합니다.")


def validate_month(month: str) -> None:
    """월이 YYYY-MM 형식인지 검증합니다."""
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise ValueError("월 형식은 YYYY-MM 이어야 합니다.")


def normalize_transaction_type(tx_type: str) -> str:
    """거래 타입을 정규화하고 검증합니다."""
    normalized = tx_type.strip().lower()
    if normalized not in {"income", "expense"}:
        raise ValueError("거래 타입은 'income' 또는 'expense' 이어야 합니다.")
    return normalized


def parse_tags(tags_raw: str) -> List[str]:
    """쉼표로 구분된 태그 문자열을 목록으로 변환합니다."""
    if not tags_raw:
        return []
    return [tag.strip() for tag in tags_raw.split(",") if tag.strip()]


def clean_tag_list(tags: Optional[List[str]]) -> List[str]:
    """태그 목록의 공백을 제거하고 빈 태그를 제외합니다."""
    return [tag.strip() for tag in (tags or []) if tag.strip()]


def sort_transactions(transactions: List[Transaction]) -> List[Transaction]:
    """거래를 날짜와 ID 기준으로 최신순 정렬합니다."""
    return sorted(transactions, key=lambda tx: (tx.date, tx.id), reverse=True)


class BudgetService:
    """가계부 핵심 비즈니스 로직을 처리하는 서비스 클래스"""

    def __init__(self, storage: Storage):
        self.storage = storage

    # --- 초기화 및 카테고리 관리 ---

    def ensure_default_categories(self) -> None:
        """카테고리가 비어 있는 경우 기본 카테고리 4종을 자동 등록합니다."""
        cats = self.storage.load_categories()
        if not cats:
            defaults = ["식비", "교통", "급여", "기타"]
            new_cats = [Category(id=i + 1, name=name) for i, name in enumerate(defaults)]
            self.storage.save_categories(new_cats)

    def list_categories(self) -> List[Category]:
        """등록된 전체 카테고리 목록을 반환합니다."""
        return self.storage.load_categories()

    def add_category(self, name: str) -> Category:
        """새 카테고리를 등록합니다."""
        name = name.strip()
        if not name:
            raise ValueError("카테고리 이름은 비어 있을 수 없습니다.")

        cats = self.storage.load_categories()
        if any(c.name == name for c in cats):
            raise ValueError(f"이미 존재하는 카테고리입니다: {name}")

        next_id = max((c.id for c in cats), default=0) + 1
        new_cat = Category(id=next_id, name=name)
        cats.append(new_cat)
        self.storage.save_categories(cats)
        return new_cat

    def remove_category(self, cat_id: int) -> None:
        """카테고리를 삭제합니다. 거래 내역에 사용 중인 경우 삭제를 차단합니다."""
        cats = self.storage.load_categories()
        target = next((c for c in cats if c.id == cat_id), None)
        if not target:
            raise ValueError(f"ID {cat_id}에 해당하는 카테고리가 존재하지 않습니다.")

        for tx in self.storage.stream_transactions():
            if tx.category == target.name:
                raise ValueError(
                    f"'{target.name}' 카테고리를 사용한 거래 내역이 존재하여 삭제할 수 없습니다."
                )

        updated_cats = [c for c in cats if c.id != cat_id]
        self.storage.save_categories(updated_cats)

    # --- 거래 내역 관리 ---

    def add_transaction(
        self,
        date_str: str,
        tx_type: str,
        category: str,
        amount: int,
        memo: str = "",
        tags: Optional[List[str]] = None,
    ) -> Transaction:
        """단일 거래를 유효성 검증 후 등록합니다."""
        validate_date(date_str)
        tx_type = normalize_transaction_type(tx_type)

        if amount <= 0:
            raise ValueError("금액은 0보다 큰 정수여야 합니다.")

        valid_cats = {c.name for c in self.storage.load_categories()}
        if category not in valid_cats:
            raise ValueError(
                f"등록되지 않은 카테고리입니다: '{category}'. 등록된 목록: {list(valid_cats)}"
            )

        next_id = max((tx.id for tx in self.storage.stream_transactions()), default=0) + 1
        new_tx = Transaction(
            id=next_id,
            date=date_str,
            type=tx_type,
            category=category,
            amount=amount,
            memo=memo.strip(),
            tags=clean_tag_list(tags),
        )
        self.storage.append_transaction(new_tx)
        return new_tx

    def list_transactions(self, limit: Optional[int] = None) -> List[Transaction]:
        """거래 내역을 최신순(날짜 내림차순, ID 내림차순)으로 반환합니다."""
        txs = sort_transactions(list(self.storage.stream_transactions()))
        if limit is not None and limit > 0:
            return txs[:limit]
        return txs

    def delete_transaction(self, tx_id: int) -> bool:
        """지정한 ID의 거래를 삭제합니다."""
        all_txs = list(self.storage.stream_transactions())
        filtered = [tx for tx in all_txs if tx.id != tx_id]
        if len(filtered) == len(all_txs):
            return False
        self.storage.save_all_transactions(filtered)
        return True

    def update_transaction(self, tx_id: int, **fields: Any) -> Transaction:
        """지정한 ID의 거래 필드를 수정합니다."""
        all_txs = list(self.storage.stream_transactions())
        target_idx = next((i for i, tx in enumerate(all_txs) if tx.id == tx_id), None)
        if target_idx is None:
            raise ValueError(f"ID {tx_id}에 해당하는 거래를 찾을 수 없습니다.")

        tx = all_txs[target_idx]
        if "date" in fields and fields["date"]:
            validate_date(fields["date"])
            tx.date = fields["date"]
        if "type" in fields and fields["type"]:
            tx.type = normalize_transaction_type(fields["type"])
        if "category" in fields and fields["category"]:
            valid_cats = {c.name for c in self.storage.load_categories()}
            if fields["category"] not in valid_cats:
                raise ValueError(f"등록되지 않은 카테고리: {fields['category']}")
            tx.category = fields["category"]
        if "amount" in fields and fields["amount"] is not None:
            amt = int(fields["amount"])
            if amt <= 0:
                raise ValueError("금액은 0보다 커야 합니다.")
            tx.amount = amt
        if "memo" in fields and fields["memo"] is not None:
            tx.memo = fields["memo"].strip()
        if "tags" in fields and fields["tags"] is not None:
            tx.tags = clean_tag_list(fields["tags"])

        self.storage.save_all_transactions(all_txs)
        return tx

    def search_transactions(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        category: Optional[str] = None,
        tx_type: Optional[str] = None,
        q: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Transaction]:
        """지정한 조건에 맞는 거래를 최신순으로 검색합니다."""
        results = []
        for tx in self.storage.stream_transactions():
            if from_date and tx.date < from_date:
                continue
            if to_date and tx.date > to_date:
                continue
            if category and tx.category != category:
                continue
            if tx_type and tx.type != normalize_transaction_type(tx_type):
                continue
            if q and q.lower() not in tx.memo.lower():
                continue
            if tag and tag not in tx.tags:
                continue
            results.append(tx)
        return sort_transactions(results)

    # --- 예산 및 요약 ---

    def set_budget(self, month: str, amount: int) -> Budget:
        """특정 월(YYYY-MM)의 예산을 설정합니다."""
        validate_month(month)
        if amount <= 0:
            raise ValueError("예산 금액은 0보다 커야 합니다.")

        budgets = self.storage.load_budgets()
        for budget in budgets:
            if budget.month == month:
                budget.amount = amount
                break
        else:
            budgets.append(Budget(month=month, amount=amount))

        self.storage.save_budgets(budgets)
        return Budget(month=month, amount=amount)

    def get_summary(self, month: str, top_n: int = 5) -> Dict[str, Any]:
        """특정 월의 수입, 지출, 카테고리별 지출 TOP N, 예산 대비 분석 요약을 반환합니다."""
        validate_month(month)
        month_txs = [tx for tx in self.storage.stream_transactions() if tx.date.startswith(month)]

        total_income = sum(tx.amount for tx in month_txs if tx.type == "income")
        total_expense = sum(tx.amount for tx in month_txs if tx.type == "expense")
        expense_by_cat: Dict[str, int] = {}
        for tx in month_txs:
            if tx.type == "expense":
                expense_by_cat[tx.category] = expense_by_cat.get(tx.category, 0) + tx.amount

        budgets = self.storage.load_budgets()
        target_budget = next((b for b in budgets if b.month == month), None)
        usage_rate = None
        is_over = False
        if target_budget and target_budget.amount > 0:
            usage_rate = round((total_expense / target_budget.amount) * 100, 1)
            is_over = total_expense > target_budget.amount

        return {
            "month": month,
            "has_data": bool(month_txs),
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": sorted(expense_by_cat.items(), key=lambda item: item[1], reverse=True)[:top_n],
            "budget": target_budget.amount if target_budget else None,
            "usage_rate": usage_rate,
            "is_over_budget": is_over,
        }

    # --- CSV 내보내기 / 가져오기 ---

    def export_csv(
        self,
        filepath: str,
        month: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> int:
        """조건에 맞는 거래를 CSV 파일(utf-8-sig)로 내보냅니다."""
        if not month and not (from_date and to_date):
            raise ValueError("내보내기 조건으로 --month 또는 (--from 및 --to)가 필수입니다.")

        results = self.search_transactions(from_date=from_date, to_date=to_date)
        if month:
            results = [tx for tx in results if tx.date.startswith(month)]

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            for tx in results:
                writer.writerow([tx.date, tx.type, tx.category, tx.amount, tx.memo, ",".join(tx.tags)])
        return len(results)

    def import_csv(self, filepath: str) -> Tuple[int, int]:
        """CSV 파일에서 거래를 읽어 유효한 행만 추가 등록합니다. (성공 수, 실패 수 반환)"""
        success_count = 0
        skip_count = 0
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date_str = row["date"].strip()
                    tx_type = row["type"].strip()
                    category = row["category"].strip()
                    amount = int(row["amount"].strip())
                    memo = row.get("memo", "").strip()
                    tags = parse_tags(row.get("tags", "").strip())

                    cats = {c.name for c in self.storage.load_categories()}
                    if category not in cats:
                        self.add_category(category)
                    self.add_transaction(
                        date_str=date_str,
                        tx_type=tx_type,
                        category=category,
                        amount=amount,
                        memo=memo,
                        tags=tags,
                    )
                    success_count += 1
                except Exception:
                    skip_count += 1
        return success_count, skip_count
