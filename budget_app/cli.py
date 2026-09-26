# 사용자 입력 수용 및 화면 출력
import argparse
import sys
from datetime import date
from typing import Optional

from budget_app.decorators import handle_cli_errors
from budget_app.models import Transaction
from budget_app.services import BudgetService, parse_tags
from budget_app.storage import Storage


def create_parser() -> argparse.ArgumentParser:
    """argparse 서브커맨드 및 옵션 파서를 정의합니다."""
    parser = argparse.ArgumentParser(
        prog="python -m budget_app",
        description="가계부 콘솔 CLI 애플리케이션",
    )
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="데이터 저장 디렉터리 경로 (기본값: ./data)",
    )

    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")
    subparsers.add_parser("add", help="대화형으로 새 거래 내역을 등록합니다.")

    list_p = subparsers.add_parser("list", help="최신순으로 거래 목록을 조회합니다.")
    list_p.add_argument("--limit", type=int, default=20, help="출력할 최대 건수 (기본값: 20)")

    update_p = subparsers.add_parser("update", help="특정 거래 내역을 수정합니다.")
    update_p.add_argument("--id", type=int, required=True, help="수정할 거래 ID")
    update_p.add_argument("--date", help="수정할 날짜 (YYYY-MM-DD)")
    update_p.add_argument("--type", help="수정할 거래 타입 (income / expense)")
    update_p.add_argument("--category", help="수정할 카테고리")
    update_p.add_argument("--amount", type=int, help="수정할 금액")
    update_p.add_argument("--memo", help="수정할 메모")
    update_p.add_argument("--tags", help="수정할 태그 (쉼표 구분)")

    delete_p = subparsers.add_parser("delete", help="특정 거래 내역을 삭제합니다.")
    delete_p.add_argument("--id", type=int, required=True, help="삭제할 거래 ID")

    search_p = subparsers.add_parser("search", help="조건에 맞는 거래를 검색합니다.")
    search_p.add_argument("--from", dest="from_date", help="시작 날짜 (YYYY-MM-DD)")
    search_p.add_argument("--to", dest="to_date", help="종료 날짜 (YYYY-MM-DD)")
    search_p.add_argument("--category", help="카테고리")
    search_p.add_argument("--type", help="거래 타입 (income / expense)")
    search_p.add_argument("--q", help="메모 검색 키워드")
    search_p.add_argument("--tag", help="검색할 태그")

    sum_p = subparsers.add_parser("summary", help="해당 월의 가계부 및 예산 요약을 출력합니다.")
    sum_p.add_argument("--month", required=True, help="조회할 대상 월 (YYYY-MM)")
    sum_p.add_argument("--top", type=int, default=5, help="지출 상위 카테고리 개수 (기본값: 5)")

    budget_p = subparsers.add_parser("budget", help="예산 관리 명령")
    b_subs = budget_p.add_subparsers(dest="budget_action", help="예산 하위 명령")
    b_set = b_subs.add_parser("set", help="월별 목표 예산 설정")
    b_set.add_argument("--month", required=True, help="대상 월 (YYYY-MM)")
    b_set.add_argument("--amount", type=int, required=True, help="예산 금액 (양수 정수)")

    cat_p = subparsers.add_parser("category", help="카테고리 관리 명령")
    c_subs = cat_p.add_subparsers(dest="cat_action", help="카테고리 하위 명령")
    c_subs.add_parser("list", help="카테고리 목록 조회")
    c_add = c_subs.add_parser("add", help="카테고리 추가")
    c_add.add_argument("name", help="추가할 카테고리명")
    c_remove = c_subs.add_parser("remove", help="카테고리 삭제")
    c_remove.add_argument("--id", type=int, required=True, help="삭제할 카테고리 ID")

    exp_p = subparsers.add_parser("export", help="조건에 맞는 거래를 CSV로 내보냅니다.")
    exp_p.add_argument("--out", required=True, help="저장할 CSV 파일 경로")
    exp_p.add_argument("--month", help="내보낼 대상 월 (YYYY-MM)")
    exp_p.add_argument("--from", dest="from_date", help="시작 날짜 (YYYY-MM-DD)")
    exp_p.add_argument("--to", dest="to_date", help="종료 날짜 (YYYY-MM-DD)")

    imp_p = subparsers.add_parser("import", help="CSV 파일에서 거래를 일괄 등록합니다.")
    imp_p.add_argument("--from", dest="from_file", required=True, help="가져올 CSV 파일 경로")
    return parser


def handle_add_interactive(service: BudgetService) -> None:
    """대화형으로 순차 입력받아 거래를 추가합니다."""
    print("=== 새 거래 내역 등록 (대화형) ===")
    today_str = date.today().strftime("%Y-%m-%d")
    date_val = input(f"1. 날짜 (YYYY-MM-DD, 기본값: {today_str}): ").strip() or today_str

    while True:
        type_val = input("2. 타입 (income / expense): ").strip().lower()
        if type_val in ["income", "expense"]:
            break
        print("   [오류] 거래 타입은 'income' 또는 'expense'여야 합니다.")

    categories = service.list_categories()
    cat_names = [c.name for c in categories]
    print(f"   등록 가능 카테고리: {', '.join(cat_names)}")
    while True:
        cat_val = input("3. 카테고리: ").strip()
        if cat_val in cat_names:
            break
        print(f"   [오류] '{cat_val}'은(는) 없는 카테고리입니다. 위 목록 중에서 입력해 주세요.")

    while True:
        amt_raw = input("4. 금액 (양의 정수): ").strip()
        try:
            amt_val = int(amt_raw)
            if amt_val > 0:
                break
            print("   [오류] 금액은 0보다 커야 합니다.")
        except ValueError:
            print("   [오류] 숫자로 입력해 주세요.")

    memo_val = input("5. 메모 (선택, 미입력 시 엔터): ").strip()
    tag_list = parse_tags(input("6. 태그 (선택, 쉼표 구분 e.g. 외식,점심): ").strip())
    tx = service.add_transaction(date_str=date_val, tx_type=type_val, category=cat_val, amount=amt_val, memo=memo_val, tags=tag_list)
    print(f"\n[성공] 거래가 등록되었습니다. (발급된 ID: {tx.id})")


def print_transaction_table(transactions: list[Transaction], title: str) -> None:
    """거래 내역 목록을 콘솔 테이블 형태로 정렬 출력합니다."""
    if not transactions:
        print(f"\n{title}: 내역이 없습니다.")
        return
    print(f"\n--- {title} ({len(transactions)}건) ---")
    print(f"{'ID':<5} | {'날짜':<10} | {'타입':<7} | {'카테고리':<10} | {'금액':>10} | {'메모':<15} | {'태그'}")
    print("-" * 80)
    for tx in transactions:
        type_str = "수입" if tx.type == "income" else "지출"
        tags_str = ", ".join(tx.tags) if tx.tags else ""
        print(f"{tx.id:<5} | {tx.date:<10} | {type_str:<7} | {tx.category:<10} | {tx.amount:>10,}원 | {tx.memo:<15} | {tags_str}")


@handle_cli_errors
def main() -> None:
    """CLI 진입점 메인 함수"""
    parser = create_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    storage = Storage(data_dir=args.data_dir)
    service = BudgetService(storage)
    service.ensure_default_categories()

    if args.command == "add":
        handle_add_interactive(service)
    elif args.command == "list":
        print_transaction_table(service.list_transactions(limit=args.limit), f"최근 거래 내역 (최대 {args.limit}건)")
    elif args.command == "update":
        tags_list = parse_tags(args.tags) if args.tags is not None else None
        updated = service.update_transaction(tx_id=args.id, date=args.date, type=args.type, category=args.category, amount=args.amount, memo=args.memo, tags=tags_list)
        print(f"[성공] ID {updated.id}번 거래가 정상 수정되었습니다.")
    elif args.command == "delete":
        if service.delete_transaction(args.id):
            print(f"[성공] ID {args.id}번 거래가 삭제되었습니다.")
        else:
            raise ValueError(f"ID {args.id}에 해당하는 거래 내역이 없습니다.")
    elif args.command == "search":
        results = service.search_transactions(from_date=args.from_date, to_date=args.to_date, category=args.category, tx_type=args.type, q=args.q, tag=args.tag)
        print_transaction_table(results, "검색 결과")
    elif args.command == "summary":
        res = service.get_summary(month=args.month, top_n=args.top)
        print(f"\n=== {res['month']} 가계부 요약 리포트 ===")
        if not res["has_data"]:
            print("데이터 없음 (해당 월의 거래 기록이 없습니다.)")
            return
        print(f"총 수입: {res['total_income']:,}원")
        print(f"총 지출: {res['total_expense']:,}원")
        print(f"순 잔액(수입 - 지출): {res['balance']:,}원")
        if res["budget"] is not None:
            print("\n[예산 분석]")
            print(f"- 설정 예산: {res['budget']:,}원")
            print(f"- 예산 사용률: {res['usage_rate']}%")
            print("⚠️ [경고] 설정된 예산을 초과하여 지출했습니다!" if res["is_over_budget"] else "✅ 예산 범위 내에서 안정적으로 지출하고 있습니다.")
        if res["top_categories"]:
            print(f"\n[지출 상위 TOP {len(res['top_categories'])} 카테고리]")
            for rank, (cat, total) in enumerate(res["top_categories"], start=1):
                print(f"  {rank}. {cat}: {total:,}원")
    elif args.command == "budget":
        if args.budget_action == "set":
            b = service.set_budget(month=args.month, amount=args.amount)
            print(f"[성공] {b.month} 예산이 {b.amount:,}원으로 설정되었습니다.")
        else:
            print("사용법: python -m budget_app budget set --month YYYY-MM --amount <금액>")
    elif args.command == "category":
        if args.cat_action == "list":
            print("\n--- 등록된 카테고리 목록 ---")
            for c in service.list_categories():
                print(f"ID: {c.id:<3} | 이름: {c.name}")
        elif args.cat_action == "add":
            new_cat = service.add_category(args.name)
            print(f"[성공] 카테고리 '{new_cat.name}'(ID: {new_cat.id})이(가) 등록되었습니다.")
        elif args.cat_action == "remove":
            service.remove_category(args.id)
            print(f"[성공] ID {args.id}번 카테고리가 삭제되었습니다.")
        else:
            print("사용법: python -m budget_app category [list|add|remove] ...")
    elif args.command == "export":
        count = service.export_csv(filepath=args.out, month=args.month, from_date=args.from_date, to_date=args.to_date)
        print(f"[성공] 총 {count}건의 거래 내역을 '{args.out}'(으)로 내보냈습니다.")
    elif args.command == "import":
        ok, skipped = service.import_csv(args.from_file)
        print(f"[완료] CSV 가져오기 결과: 성공 {ok}건, 실패/건너뜀 {skipped}건")
