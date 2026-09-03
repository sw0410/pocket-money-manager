# main.py

# 1. 상태 준비
balance = 10000
records = []

print(f"현재 잔액: {balance}원\n")

# 2. 사용자 입력
item = input("어디에 썼나요?: ")
amount = int(input("얼마를 썼나요?: "))

# 3. 핵심 연산 & 기록
balance -= amount
records.append({"item": item, "amount": amount})

# 4. 결과 확인
print("\n=== 지출 완료 ===")
print(f"남은 잔액: {balance}원")
print("내역 장부:", records)