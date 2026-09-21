import json
import os
from dataclasses import asdict, dataclass
from datetime import date
import csv

# ==========================================
# 1. 파일명 상수 및 데이터 구조
# ==========================================
FILENAME = "transactions.jsonl"
CATEGORY_FILE = "categories.txt"
BUDGET_FILE = "budget.txt"


@dataclass
class Transaction:
    id: int
    date: str
    transaction_type: str
    category: str
    amount: int


@dataclass
class Category:
    id: int
    name: str


# 전역 상태 관리 변수
transactions = []
categories = []
current_amount = 0
current_id = 0


# ==========================================
# 2. 모든 함수 정의 (def)
# ==========================================
# --- 거래 관련 함수 ---
def add_transaction(current_amount, current_id, tx):
    current_id = current_id + 1
    if tx.transaction_type == "수입":
        current_amount += tx.amount
    elif tx.transaction_type == "지출":
        current_amount -= tx.amount
    return current_id, current_amount


def stream_transaction(filename: str):
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            yield Transaction(
                id=data["id"],
                date=data["date"],
                transaction_type=data["transaction_type"],
                category=data["category"],
                amount=data["amount"],
            )


# --- 카테고리 관련 함수 ---
def save_categories():
    with open(CATEGORY_FILE, "w", encoding="utf-8") as f:
        for cat in categories:
            f.write(f"{cat.id},{cat.name}\n")


def load_categories():
    if not os.path.exists(CATEGORY_FILE):
        return
    with open(CATEGORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            cat = Category(int(parts[0]), parts[1])
            categories.append(cat)


def add_category(name):
    new_id = len(categories) + 1
    new_cat = Category(new_id, name)
    categories.append(new_cat)
    save_categories()
    print(f"카테고리 등록 완료: [{new_cat.id}] {new_cat.name}")


def list_categories():
    print("--- 카테고리 목록 ---")
    for cat in categories:
        print(f"{cat.id},{cat.name}")


def remove_categories(target_id):
    for cat in categories:
        if cat.id == target_id:
            categories.remove(cat)
            save_categories()
            print(f"카테고리 삭제 완료: [{cat.id}] {cat.name}")
            break


def get_category_by_id(cat_id):
    for cat in categories:
        if cat.id == cat_id:
            return cat
    return None


def select_category():
    while True:
        list_categories()
        try:
            chosen_id = int(input("선택할 카테고리 번호: "))
        except ValueError:
            print("숫자(번호)만 입력해주세요.\n")
            continue

        selected_cat = get_category_by_id(chosen_id)
        if selected_cat:
            return selected_cat
        else:
            print("존재하지 않는 카테고리 번호입니다. 다시 입력해주세요.\n")


# --- 예산 관련 함수 ---
def load_budget():
    if not os.path.exists(BUDGET_FILE):
        return 0
    with open(BUDGET_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if content:
            return int(content)
        return 0


def save_budget(amount):
    with open(BUDGET_FILE, "w", encoding="utf-8") as f:
        f.write(str(amount))

def delete_transaction_by_id(target_id):
    for tx in transactions:
        if tx.id == target_id:
            transactions.remove(tx)
            return True
    print("해당 id의 거래를 찾지 못했습니다.")
    return False

def update_transaction_by_id(target_id,new_amount):
    for tx in transactions:
        if tx.id == target_id:
            tx.amount = new_amount
            return True
    print("해당 id의 거래를 찾지 못했습니다.")
    return False

def save_transactions_safely(filename="transactions.jsonl"):
    tmp_filename = f"{filename}.tmp"
    with open(tmp_filename, "w", encoding="utf-8") as f:
        for tx in transactions:
            tx_dict = asdict(tx)
            tx_json = json.dumps(tx_dict, ensure_ascii=False)
            f.write(tx_json + "\n")
    os.replace(tmp_filename, filename)
    print("장부 파일 안전 저장 완료.")
    return True

def export_to_csv(filename="transactions.csv"):
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        # 1. 헤더 쓰기
        writer.writerow(["id", "date", "transaction_type", "category", "amount"])

        # 2. 파일이 열려있는 with 안에서 반복문 실행
        for tx in transactions:
            writer.writerow(
                [tx.id, tx.date, tx.transaction_type, tx.category, tx.amount]
            )

    # 3. 파일 쓰기가 온전히 끝난 후 1번만 출력
    print(f"{filename} 파일로 내보내기 완료.")

def import_from_csv(filename="transactions.csv"):
    if not os.path.exists(filename):
        print(f"{filename}이 존재하지 않습니다.")
        return
    else:
        with open(filename, "r", encoding="utf-8-sig")as f:
            reader = csv.DictReader(f)
            for row in reader:
                pass

        
# ==========================================
# 3. 프로그램 초기화 및 데이터 세팅
# ==========================================
# [1] 거래 내역 복원
if not os.path.exists(FILENAME):
    with open(FILENAME, "w", encoding="utf-8") as f:
        pass

for tx in stream_transaction(FILENAME):
    transactions.append(tx)
    current_id, current_amount = add_transaction(current_amount, current_id, tx)

print(f"시스템 준비 완료: 총 {len(transactions)}건의 거래 복원됨. 현재 잔액: {current_amount}원, 다음 거래번호: {current_id + 1}")

# # === 수정 및 파일 안전 저장 연동 테스트 ===
# if transactions:
#     first_tx = transactions[0]
#     print(f"수정 전 {first_tx.id}번 거래 금액: {first_tx.amount:,}원")

#     # 1. 메모리 데이터 수정
#     update_transaction_by_id(first_tx.id, 55555)

#     # 2. 변경된 리스트 전체를 파일에 안전하게 저장
#     save_transactions_safely(FILENAME)

#     print(f"수정 후 {first_tx.id}번 거래 금액: {first_tx.amount:,}원")
# # ==========================================


#  print("삭제 전 거래 건수:", len(transactions))
#  delete_transaction_by_id(1)  # 1번 거래 삭제 시도
#   print("삭제 후 거래 건수:", len(transactions))

# # === update_transaction_by_id 테스트 ===
# if transactions:
#     first_tx = transactions[0]
#     print(f"수정 전 {first_tx.id}번 거래 금액: {first_tx.amount:,}원")

#     update_transaction_by_id(first_tx.id, 77777)  # 77,777원으로 변경 시도

#     print(f"수정 후 {first_tx.id}번 거래 금액: {first_tx.amount:,}원")
# # =======================================

# [2] 카테고리 로드 및 기본값 세팅
load_categories()
if len(categories) == 0:
    add_category("식비")
    add_category("교통")
    add_category("급여")
    add_category("기타")

# [3] 예산 로드 및 초기 세팅
monthly_budget = load_budget()
if monthly_budget == 0:
    monthly_budget = int(input("이번달 목표 예산을 입력해주세요: "))
    save_budget(monthly_budget)
    print(f"목표 예산이 {monthly_budget:,}원으로 설정되었습니다.")


# ==========================================
# 4. 메인 거래 입력 루프
# ==========================================
while True:
    menu = input("메뉴를 선택하세요 (1.등록 / 2.수정 / 3.삭제 / 4.내보내기 / Enter=종료): ").strip()
    if menu == "":
        break

    # 1. 등록 분기 
    if menu == "1":
        transaction_type = input("거래 타입을 입력하세요 (수입/지출): ").strip()
        if transaction_type not in ["수입", "지출"]:
            print("수입 또는 지출만 입력해주세요.")
            continue

        chosen_cat = select_category()
        category = chosen_cat.name

        while True:
            amount = input("금액을 입력해주세요: ")
            try:
                amount = int(amount)
                if amount > 0:
                    break
                else:
                    print("0보다 큰 숫자만 입력해주세요.")
            except ValueError:
                print("숫자만 입력해주세요.")

        tx = Transaction(
            id=current_id + 1,
            date=str(date.today()),
            transaction_type=transaction_type,
            category=category,
            amount=amount,
        )

        current_id, current_amount = add_transaction(current_amount, current_id, tx)
        transactions.append(tx)

        # JSONL 파일 영구 저장
        tx_dict = asdict(tx)
        tx_json = json.dumps(tx_dict, ensure_ascii=False)
        with open(FILENAME, "a", encoding="utf-8") as f:
            f.write(tx_json + "\n")

        print(f"거래번호: {current_id}, 현재잔액: {current_amount}원 (등록 완료)")

    # 2. 수정 분기
    elif menu == "2":
        try:
            target_id = int(input("수정할 거래 번호(ID)를 입력하세요: "))
            new_amount = int(input("변경할 새 금액을 입력하세요: "))
            if update_transaction_by_id(target_id, new_amount):
                save_transactions_safely(FILENAME)
        except ValueError:
            print("숫자만 입력해주세요.")

    # 3. 삭제 분기
    elif menu == "3":
        try:
            target_id = int(input("삭제할 거래 번호(ID)를 입력하세요: "))
            if delete_transaction_by_id(target_id):
                save_transactions_safely(FILENAME)
        except ValueError:
            print("숫자(ID)만 입력해주세요.")

    # 4. 내보내기 분기 
    elif menu == "4":
        export_to_csv()
        continue
        
    # 1, 2, 3 외의 잘못된 입력 처리
    else:
        print("1, 2, 3, 4 중 하나를 입력하거나 엔터를 눌러 종료하세요.\n")

# ==========================================
# 5. 프로그램 종료 후 통계 집계
# ==========================================
category_total = {}
for tx in transactions:
    if tx.category not in category_total:
        category_total[tx.category] = 0
    category_total[tx.category] += tx.amount

for category, total in category_total.items():
    print(f"카테고리: {category} | 총 합계: {total:,}원")

total_income = 0
total_expense = 0
for tx in transactions:
    if tx.transaction_type == "수입":
        total_income += tx.amount
    elif tx.transaction_type == "지출":
        total_expense += tx.amount

print(f"총 수입: {total_income:,}원")
print(f"총 지출: {total_expense:,}원")
print(f"순 잔액(수입 - 지출): {total_income - total_expense:,}원")

import_from_csv()