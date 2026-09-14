from dataclasses import dataclass
from dataclasses import asdict
from datetime import date
import json
import os

FILENAME = "transactions.jsonl"
@dataclass
class transaction : 
    id: int 
    date: str
    transaction_type: str
    category: str
    amount: int

transactions =[]

# 2. 거래 연산 함수 (Transformation)
def add_transaction(current_amount, current_id, transaction_type, amount):
    # [1] id를 1 증가시키는 코드 작성
    current_id = current_id +1
    # [2] 거래타입(수입/지출)에 따라 current_amount를 더하거나 빼는 if/elif 작성
    if transaction_type == "수입":
        current_amount += amount
    elif transaction_type == "지출":
        current_amount -= amount
    # [3] 변경된 current_amount와 current_id를 반환하는 return 작성
    return current_id, current_amount

# 초기 바닥 상태 (Ground)
current_amount = 0
current_id = 0


if not os.path.exists(FILENAME):
    with open(FILENAME, "w", encoding="utf-8") as f:
        pass

with open(FILENAME, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()  # 1. 꼬리표에 정제된 결과를 다시 담는다
        if not line:         # 2. 문지기: 비어있다면 즉시 다음 줄로 넘긴다
            continue

        data = json.loads(line)

        tx = transaction(id= data["id"], date= data["date"], transaction_type= data["transaction_type"], category= data["category"], amount= data["amount"])
        transactions.append(tx)

        current_id, current_amount = add_transaction(current_amount, current_id, tx.transaction_type, tx.amount)

print(f"시스템 준비 완료: 총 {len(transactions)}건의 거래 복원됨. 현재 잔액: {current_amount}원, 다음 거래번호: {current_id + 1}")


while True:
    transaction_type = input("거래 타입을 입력하세요: ").strip()
    if transaction_type == "":
        break
    if transaction_type not in ["수입","지출"]:
        print("수입 또는 지출만 입력해주세오")
        continue

    while True:
        category = input("카테고리를 입력해 주세요: ").strip()
        if category != "":
            break
        print("문자를 입력해주세요: ")
    
    while True:
        amount = input("금액을 입력해주세요: ")
        try:
            amount = int(amount)
            if amount > 0:
                break
            else:
                print("0보다 큰 숫자만 입력해주세요.")
                
        except ValueError:
            print("숫자만 입력해주세요. ")

    # 통과 후 add_transaction
    current_id,current_amount = add_transaction(current_amount,current_id,transaction_type, amount)
    print(f"거래번호: {current_id}, 현재 잔액: {current_amount}")

    tx = transaction(id= current_id, date= str(date.today()), transaction_type= transaction_type, category= category, amount= current_amount)
    transactions.append(tx)

    for tx in transactions:
        print(tx.id, tx.date, tx.transaction_type, tx.category, tx.amount)

    tx_dict = asdict(tx)

    tx_json = json.dumps(tx_dict, ensure_ascii=False)

    with open("transactions.jsonl", "a", encoding="utf-8") as f:
        f.write(tx_json + "\n")

    print(f"거래번호: {current_id}, 현재잔액: {current_amount} (파일 저장 완료)")

