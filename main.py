from datetime import date

current_amount = 10000
current_id = 0
records = []

def spend_money(where_used, used_amount, current_amount, records, current_id):
    current_amount -= used_amount
    current_id += 1

    record = {
                "id": current_id,
                "date": str(date.today()),
                "where": where_used,
                "amount": used_amount
        }
    records.append(record)

    return current_amount, current_id


while True:
    where_used = input("사용처를 알려주세요: ")
    if where_used == "x":
                break
    used_amount = int(input("사용한 금액을 입력해주세요: "))

    current_amount, current_id = spend_money(
            where_used, used_amount, current_amount, records, current_id)

print("\n--- 저장된 장부 내역 ---")
print(records)
print(f"남은 잔액: {current_amount}원")

def list_transactions(records):
       for record in records:
        print(f"[{record['id']}] {record['date']} | {record['where']} | {record['amount']}원")

list_transactions(records)
print(f"\n남은 잔액: {current_amount}원")