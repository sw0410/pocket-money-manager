from datetime import date
from models import Transaction
from repository import load_transactions, save_transaction




def add_transaction(category, amount, current_amount, records, current_id, transaction_type):

    if transaction_type == "수입":
        current_amount += amount
    elif transaction_type == "지출":
         current_amount -= amount

    current_id += 1
    
    record = Transaction(
    id= current_id,
    date= str(date.today()),
    transaction_type= transaction_type,
    category= category,
    amount= amount
)
    records.append(record)

# 기존 with open(...) 대신 repository 호출
    save_transaction(record)
    return current_amount, current_id

def list_transactions(records):
    for record in records:
        print(f"[{record.id}] {record.date} | {record.transaction_type} |{record.category} | {record.amount}원")

def main():
    records = list(load_transactions())

    if records:
        current_id = records[-1].id
    else:
        current_id = 0

    current_amount = 0
    for r in records:
        if r.transaction_type == "수입":
            current_amount += r.amount
        elif r.transaction_type == "지출":
            current_amount -= r.amount 

    while True:
        transaction_type = input("수입 / 지출 :" )
        if transaction_type == "":
            break
        elif transaction_type not in ["수입", "지출"]:
            print("수입 / 지출만 입력해주세요.\n")
            continue

        category = input("분류: ")
        while True:
            try:
                amount = int(input("금액: "))
                if amount > 0:
                    break
                else:
                    print("금액은 0보다 커야 합니다.")
            except ValueError:
                print("숫자만 입력해 주세요.")

        current_amount, current_id = add_transaction(category, amount, current_amount, records, current_id, transaction_type )

    print("\n--- 저장된 장부 내역 ---")
    list_transactions(records)
    print(f"\n남은 잔액: {current_amount}원")

if __name__ == "__main__":
    main()