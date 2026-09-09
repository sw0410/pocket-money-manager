from dataclasses import dataclass
from datetime import date


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


while True:
    transaction_type = input("거래 타입을 입력하세요: ").strip()
    if transaction_type == "":
        break
    if transaction_type not in ["수입","지출"]:
        print("수입 또는 지출만 입력해주세오")
        continue

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

    new_transaction = {"date": date.today(), "transaction_type": transaction_type , "amount": amount }
    transactions.append(new_transaction)

    # 통과 후 add_transaction
    current_id,current_amount = add_transaction(current_amount,current_id,transaction_type, amount)
    print(f"거래번호: {current_id}, 현재 잔액: {current_amount}")

for transaction in transactions:
    print(transaction['date'], transaction['transaction_type'],transaction['amount'])



