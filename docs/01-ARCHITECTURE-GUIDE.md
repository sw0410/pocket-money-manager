# pocket-money-manager 아키텍처 학습 가이드

## 목차
1. [전체 시스템 개요](#1-전체-시스템-개요)
2. [데이터플로우 다이어그램](#2-데이터플로우-다이어그램)
3. [시퀀스 다이어그램](#3-시퀀스-다이어그램)
4. [모듈별 책임 분석](#4-모듈별-책임-분석)
5. [아키텍처 설계 원칙](#5-아키텍처-설계-원칙)
6. [고급 프로그래밍 기법](#6-고급-프로그래밍-기법)
7. [기술 의사결정](#7-기술-의사결정)
8. [확장성과 병목 분석](#8-확장성과-병목-분석)

---

## 1. 전체 시스템 개요

### 1.1 프로그램의 목적
**pocket-money-manager**는 Python 기반 콘솔 가계부 애플리케이션으로, 사용자가 거래(수입/지출)를 기록하고 관리할 수 있습니다.

### 1.2 핵심 기능
- **거래 관리**: 추가(add), 조회(list), 검색(search), 수정(update), 삭제(delete)
- **카테고리 관리**: 추가, 목록 조회, 삭제
- **예산 관리**: 월별 예산 설정, 사용률 분석
- **데이터 교환**: CSV 내보내기(export), 가져오기(import)
- **통계**: 월별 요약 및 지출 분석

### 1.3 전체 아키텍처 (4계층 모델)

```
┌─────────────────────────────────────────────────────┐
│                   사용자 (Terminal)                  │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│  Presentation Layer (cli.py)                        │
│  - 명령어 파싱                                      │
│  - 사용자 입력 수용                                 │
│  - 결과 화면 출력                                   │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│  Business Logic Layer (services.py)                 │
│  - 데이터 검증 (날짜, 금액, 카테고리)              │
│  - 비즈니스 규칙 (예: 카테고리 삭제 검증)         │
│  - 계산 및 통계 (합계, 평균, 순위)                │
│  - 데이터 변환 (정렬, 필터링, 집계)               │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│  Data Access Layer (storage.py)                     │
│  - JSONL 파일 읽기/쓰기                            │
│  - 원자적(Atomic) 쓰기로 안정성 확보              │
│  - 스트리밍 처리로 메모리 효율화                   │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│  Data Model Layer (models.py)                       │
│  - Transaction, Category, Budget 정의               │
│  - 타입 힌트로 데이터 무결성 보장                  │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│            File System (data/ 디렉토리)             │
│  - transactions.jsonl                               │
│  - categories.jsonl                                 │
│  - budgets.jsonl                                    │
└─────────────────────────────────────────────────────┘
```

---

## 2. 데이터플로우 다이어그램

### 2.1 일반적인 흐름

```
사용자 입력 (CLI 명령)
    │
    ├─ 파싱 (cli.py)
    │   ├─ 명령어 식별 (add, list, search, ...)
    │   └─ 인자 추출
    │
    ├─ 비즈니스 로직 (services.py)
    │   ├─ 입력값 검증 (날짜, 금액, 카테고리)
    │   ├─ 데이터 조회/계산 (스토리지에서 읽기)
    │   └─ 결과 생성
    │
    ├─ 데이터 접근 (storage.py)
    │   ├─ JSONL 파일 읽기
    │   ├─ 데이터 변환 (JSON → Python 객체)
    │   └─ 필요시 파일 쓰기
    │
    └─ 화면 출력 (cli.py)
        ├─ 테이블 포맷
        ├─ 메시지 출력
        └─ 종료 코드 반환
```

### 2.2 데이터 저장소 구조

```
data/ (데이터 디렉토리)
├── transactions.jsonl
│   └─ 형식: {"id": 1, "date": "2024-01-01", "type": "expense", ...}
│
├── categories.jsonl
│   └─ 형식: {"id": 1, "name": "식비"}
│
└── budgets.jsonl
    └─ 형식: {"month": "2024-01", "amount": 1000000}
```

### 2.3 주요 데이터 구조

```
Transaction (거래)
├─ id: int (고유 식별자)
├─ date: str (YYYY-MM-DD)
├─ type: str (income 또는 expense)
├─ category: str (카테고리명)
├─ amount: int (금액, 양의 정수)
├─ memo: str (선택 사항)
└─ tags: List[str] (태그 목록)

Category (카테고리)
├─ id: int
└─ name: str

Budget (예산)
├─ month: str (YYYY-MM)
└─ amount: int (예산 금액)
```

---

## 3. 시퀀스 다이어그램

### 3.1 거래 추가 (add) 흐름

```
사용자                CLI                Service              Storage            File
  │                   │                   │                   │                  │
  │──── add 명령 ───→│                   │                   │                  │
  │                   │─── 대화형 입력 ──→│                   │                  │
  │                   │                   │                   │                  │
  │                   │◄──── 거래 객체 ───│                   │                  │
  │                   │                   │                   │                  │
  │                   │──── 검증 ─────→│                   │                  │
  │                   │     (날짜, 금액)  │                   │                  │
  │                   │                   │                   │                  │
  │                   │───── append_transaction() ──→│                  │
  │                   │                   │           │── 추가 쓰기 ──→│
  │                   │                   │           │                  │
  │◄──── 성공 메시지 ──│◄──── 저장 완료 ──│◄──────────│                  │
```

**단계별 상세:**
1. 사용자가 `python -m budget_app add` 실행
2. `cli.py`의 `handle_add_interactive()`가 6단계 입력 수집
3. `services.py`의 `add_transaction()` 호출
4. 서비스에서 검증 (날짜 형식, 금액 > 0, 카테고리 존재)
5. 유효하면 다음 ID 생성
6. `storage.py`의 `append_transaction()`으로 파일 추가
7. 성공 메시지 출력

### 3.2 거래 검색 (search) 흐름

```
사용자              CLI              Service            Storage           File
  │                 │                 │                 │                 │
  │─ search ─────→ │                 │                 │                 │
  │   --category   │ (조건 파싱)      │                 │                 │
  │   --from ...   │                 │                 │                 │
  │                 │─ search_transactions() ─→│                 │
  │                 │                 │         │─ stream_transactions() ─→│
  │                 │                 │         │     (파일 읽기)         │
  │                 │                 │         │◄─ 한 줄씩 읽음 ─────────│
  │                 │                 │         │                         │
  │                 │◄─ 필터링 + 정렬 ──│◄────────│                 │
  │                 │                 │                 │                 │
  │◄─ 결과 테이블 ──│                 │                 │                 │
```

**단계별 상세:**
1. 사용자가 `search --category 식비 --from 2024-01-01` 입력
2. `cli.py`에서 조건 파싱
3. `services.py`의 `search_transactions()` 호출
4. `storage.py`의 `stream_transactions()`로 파일 스트리밍 시작
5. 각 거래를 조건과 비교
6. 일치하는 것만 수집
7. 최신순 정렬
8. 테이블로 출력

### 3.3 월별 요약 (summary) 흐름

```
사용자           CLI          Service         Storage       File
  │              │             │              │             │
  │─ summary ──→ │             │              │             │
  │ --month      │ (파싱)       │              │             │
  │ --top 5      │             │              │             │
  │              │─ get_summary() ──→│              │
  │              │             │      │─ stream_transactions() ──→│
  │              │             │      │                (읽기)    │
  │              │             │      │◄─ 모든 거래 ────────────│
  │              │             │      │                           │
  │              │◄─ 집계 ──────│◄─────│                           │
  │              │  (수입, 지출)│                     │             │
  │              │  (카테고리별)│                     │             │
  │              │  (예산률)   │                     │             │
  │              │             │                     │             │
  │◄─ 요약 표시 ──│             │                     │             │
```

**단계별 상세:**
1. `get_summary(month="2024-01", top_n=5)` 호출
2. 해당 월의 모든 거래 필터링
3. 수입 합계 계산 (income 타입 필터링)
4. 지출 합계 계산 (expense 타입 필터링)
5. 카테고리별 지출 집계
6. TOP 5 정렬
7. 예산과 비교하여 사용률 계산
8. 결과 출력

### 3.4 CSV 내보내기 (export) 흐름

```
사용자          CLI          Service        Storage      CSV File
  │             │             │             │             │
  │─ export ──→ │             │             │             │
  │ --out       │ (파경 검증)  │             │             │
  │ --month     │             │             │             │
  │             │─ export_csv() ──→│        │             │
  │             │             │     │─ search_transactions() ──→│
  │             │             │     │      (조건 필터링)      │
  │             │             │     │◄─ 결과 ─────────────────│
  │             │             │     │                         │
  │             │◄─ 저장 완료 ──│◄─────│─ CSV 쓰기 ──────────→│
  │             │             │             │                 │
  │◄─ 성공 메시지 ─│             │             │                 │
```

**단계별 상세:**
1. `export_csv(filepath="output.csv", month="2024-01")` 호출
2. 조건에 맞는 거래 검색
3. CSV 헤더 작성: date, type, category, amount, memo, tags
4. 각 거래를 CSV 행으로 변환
5. UTF-8-SIG 인코딩으로 저장 (한글 호환)
6. 저장된 행 수 리포트

### 3.5 CSV 가져오기 (import) 흐름

```
CSV File        Storage      Service       Models       File
  │             │             │             │            │
  │─ 읽기 ────→ │             │             │            │
  │             │ (DictReader)│             │            │
  │             │             │             │            │
  │             │─ 각 행 검증 ─→│             │            │
  │             │             │             │            │
  │             │─ add_transaction() ──→│    │            │
  │             │             │       (객체) │            │
  │             │             │             │            │
  │             │◄─ 성공/실패 ──│             │            │
  │             │ (누적 카운트)  │             │            │
  │             │             │             │            │
  │             │─────── 최종 저장 ──────────→│
```

**단계별 상세:**
1. CSV 파일 열기 (UTF-8-SIG)
2. DictReader로 행 읽기
3. 각 행마다:
   - 데이터 추출 및 타입 변환
   - `add_transaction()` 호출로 검증
   - 성공하면 success_count += 1
   - 실패하면 skip_count += 1 (예외 무시)
4. 최종 리포트: "성공 10건, 실패 2건"

---

## 4. 모듈별 책임 분석

### 4.1 cli.py (프레젠테이션 계층)

**책임:**
- 사용자 입력 수용
- 명령 분기 처리
- 결과 화면 출력
- 오류 메시지 전달

**핵심 함수:**
```python
create_parser()              # argparse 설정
handle_add_interactive()     # 대화형 입력
print_transaction_table()    # 테이블 출력
main()                       # CLI 진입점 및 명령 분기
```

**책임 경계:**
- ❌ 데이터 검증하지 않음 (services.py에서)
- ❌ 파일 I/O 하지 않음 (storage.py에서)
- ✅ 단지 입력 수용 → 서비스 호출 → 결과 출력

**예시:**
```python
# cli.py
def handle_add_interactive(service):
    # 1. 입력 수용
    date_val = input("날짜: ")
    # 2. 서비스 호출 (검증은 여기서)
    tx = service.add_transaction(date_str=date_val, ...)
    # 3. 결과 출력
    print(f"[성공] 거래 ID {tx.id}번이 등록됐습니다")
```

### 4.2 services.py (비즈니스 로직 계층)

**책임:**
- 입력값 검증 (날짜 형식, 금액 > 0, 카테고리 존재 여부)
- 비즈니스 규칙 적용 (예: 카테고리 삭제 시 참조 무결성 확인)
- 계산 및 통계 (합계, 평균, TOP N)
- 데이터 변환 (정렬, 필터링, 집계)

**핵심 함수:**
```python
# 검증 헬퍼
validate_date()
validate_month()
normalize_transaction_type()

# 비즈니스 로직
add_transaction()           # 거래 추가
update_transaction()        # 거래 수정
delete_transaction()        # 거래 삭제
search_transactions()       # 조건 검색
get_summary()              # 월별 요약

# 카테고리/예산
add_category()
remove_category()           # 참조 무결성 검증
set_budget()

# CSV
import_csv()               # 부분 성공 처리
export_csv()
```

**책임 경계:**
- ❌ 파일을 직접 읽지 않음 (storage 사용)
- ❌ CLI 메시지 출력하지 않음 (cli 에서)
- ✅ 모든 검증과 계산을 여기서 담당

**검증 예시:**
```python
def add_transaction(self, date_str, tx_type, category, amount, ...):
    # 1. 날짜 검증
    validate_date(date_str)
    
    # 2. 타입 검증
    tx_type = normalize_transaction_type(tx_type)
    
    # 3. 금액 검증
    if amount <= 0:
        raise ValueError("금액은 0보다 커야 합니다")
    
    # 4. 카테고리 존재 여부 검증
    valid_cats = {c.name for c in self.storage.load_categories()}
    if category not in valid_cats:
        raise ValueError(f"존재하지 않는 카테고리: {category}")
    
    # 5. 저장소에 위임
    next_id = max((tx.id for tx in self.storage.stream_transactions()), default=0) + 1
    new_tx = Transaction(id=next_id, date=date_str, type=tx_type, ...)
    self.storage.append_transaction(new_tx)
    return new_tx
```

### 4.3 storage.py (데이터 접근 계층)

**책임:**
- JSONL 파일 읽기/쓰기
- 원자적(Atomic) 쓰기로 안정성 보장
- 데이터 스트리밍 처리

**핵심 함수:**
```python
# 거래
stream_transactions()       # 제너레이터로 스트리밍 반환
append_transaction()        # 파일 끝에 추가
save_all_transactions()     # 전체 덮어쓰기

# 카테고리
load_categories()          # 전체 로드
save_categories()

# 예산
load_budgets()
save_budgets()

# 내부 헬퍼
_atomic_write_jsonl()       # 원자적 쓰기
```

**책임 경계:**
- ❌ 데이터 검증하지 않음 (이미 services에서 검증됨)
- ❌ 비즈니스 로직 없음 (단순 I/O)
- ✅ 오직 파일 읽기/쓰기만

**원자적 쓰기 예시:**
```python
def _atomic_write_jsonl(self, filepath, items):
    # 1. 임시 파일에 쓰기
    tmp_file = f"{filepath}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    # 2. 원본 파일을 임시 파일로 교체
    #    → 교체 중 오류 발생 시 원본은 안전함
    os.replace(tmp_file, filepath)
```

### 4.4 models.py (데이터 모델 계층)

**책임:**
- 데이터 구조 정의
- 타입 힌트로 무결성 보장

**데이터 클래스:**
```python
@dataclass
class Transaction:
    id: int
    type: str           # "income" 또는 "expense"
    date: str           # "YYYY-MM-DD"
    amount: int         # 양의 정수
    category: str
    memo: str = ""
    tags: List[str] = field(default_factory=list)

@dataclass
class Category:
    id: int
    name: str

@dataclass
class Budget:
    month: str          # "YYYY-MM"
    amount: int         # 양의 정수
```

**책임 경계:**
- ✅ 순수한 데이터 정의만
- ❌ 메서드 로직 없음
- ❌ 파일 I/O 없음

### 4.5 decorators.py (공통 기능 계층)

**책임:**
- CLI 오류 처리 (스택트레이스 대신 친화적 메시지)
- 종료 코드 관리 (정상: 0, 오류: 1)

**핵심 데코레이터:**
```python
@handle_cli_errors
def main():
    # ValueError → "[오류] 잘못된 입력입니다"
    # FileNotFoundError → "[오류] 파일을 찾을 수 없습니다"
    # KeyboardInterrupt → "[알림] 사용자에 의해 중단됐습니다"
    # Exception → "[시스템 오류] 예기치 않은 문제"
```

---

## 5. 아키텍처 설계 원칙

### 5.1 관심사의 분리 (Separation of Concerns)

각 모듈이 **하나의 책임**만 가집니다:

| 모듈 | 책임 | 의존 대상 |
|------|------|---------|
| cli.py | 입/출력 | services |
| services.py | 검증/계산 | storage, models |
| storage.py | I/O | models |
| models.py | 데이터 정의 | (독립) |

**왜 중요한가?**
- 변경 영향 최소화 (한 모듈 수정 시 다른 모듈 영향 없음)
- 테스트 용이 (각 모듈을 독립적으로 테스트)
- 코드 재사용성 증대

### 5.2 의존성 역전 (Dependency Inversion)

상위 계층이 하위 계층에 의존하도록 설계:

```
cli.py (상위)
  ↓ 의존
services.py (중간)
  ↓ 의존
storage.py (하위)
  ↓ 의존
models.py (최하위)
```

**장점:**
- 파일 저장소를 DB로 바꿔도 cli, services는 변경 안 함
- 테스트 시 mock Storage 사용 가능

### 5.3 단일 책임 원칙 (Single Responsibility Principle)

각 함수는 **하나의 이유로만** 변경됩니다:

```python
# ❌ 나쁜 예: 여러 책임
def add_and_save(date, amount, category):
    # 1. 검증
    if not validate_date(date):
        print("Invalid date")  # 책임 1: 검증
    # 2. 저장
    save_to_file(...)          # 책임 2: I/O
    # 3. 출력
    print("Added!")            # 책임 3: UI

# ✅ 좋은 예: 책임 분리
def add_transaction(date, amount, category):      # services
    validate_date(date)                            # 검증만
    ...
    storage.append_transaction(new_tx)             # 저장은 storage에
    return new_tx

# 출력은 cli에서
print(f"[성공] ID {tx.id} 추가됨")
```

### 5.4 파일 기반 데이터 안전성

**문제:** 거래 수정/삭제 시 어떻게 안전하게 파일을 변경?

**해결: 원자적 쓰기 (Atomic Write)**

```
전: transactions.jsonl (원본)

1. 메모리에 로드
2. 수정/삭제 처리
3. transactions.jsonl.tmp에 쓰기
4. tmp 파일을 원본으로 교체 (원자적)

후: transactions.jsonl (수정됨)
   transactions.jsonl.tmp (삭제됨)

→ 교체 중 오류 발생 시 원본은 안전함!
```

**코드:**
```python
def save_all_transactions(self, transactions):
    self._atomic_write_jsonl(self.tx_file, ...)

def _atomic_write_jsonl(self, filepath, items):
    tmp_file = f"{filepath}.tmp"
    # 1. 임시 파일에 쓰기
    with open(tmp_file, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    # 2. 원자적 교체
    os.replace(tmp_file, filepath)
```

---

## 6. 고급 프로그래밍 기법

### 6.1 제너레이터 (Generator) - 메모리 효율성

**문제:** 거래가 100만 건이면 메모리에 모두 올릴 수 없음

**해결:** 제너레이터로 한 줄씩만 메모리에 유지

```python
# ❌ 나쁜 예: 전체 로드 (메모리 낭비)
def load_all_transactions(filepath):
    transactions = []
    with open(filepath, "r") as f:
        for line in f:
            transactions.append(Transaction(**json.loads(line)))
    return transactions  # 메모리에 모두 올려짐

data = load_all_transactions("transactions.jsonl")  # 100만 건 × 200 bytes = 200MB

# ✅ 좋은 예: 제너레이터 (메모리 효율)
def stream_transactions(filepath):
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield Transaction(**json.loads(line))  # 한 줄씩만 반환

for tx in stream_transactions("transactions.jsonl"):
    process(tx)  # 필요할 때만 메모리 할당
```

**사용 예:**
```python
# search_transactions에서
def search_transactions(self, category=None, ...):
    results = []
    # 한 줄씩 읽으면서 조건 확인
    for tx in self.storage.stream_transactions():
        if category and tx.category != category:
            continue
        results.append(tx)
    return sort_transactions(results)
```

**메모리 비교:**
| 방식 | 데이터 크기 | 메모리 사용 | 속도 |
|------|-----------|----------|-----|
| 전체 로드 | 100만 건 | ~200MB | 빠름 |
| 스트리밍 | 100만 건 | ~1KB | 느림 |
| **스트리밍 (추천)** | 100만 건 | ~1KB | 충분함 |

### 6.2 데코레이터 (Decorator) - 관심사 분리

**문제:** 모든 CLI 함수에서 예외 처리 코드가 반복됨

```python
# ❌ 반복되는 코드
def main():
    try:
        # 비즈니스 로직
        add_transaction(...)
    except ValueError as e:
        print(f"[오류] {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"[오류] 파일을 찾을 수 없습니다")
        sys.exit(1)

def handle_add():
    try:
        # 비즈니스 로직
        ...
    except ValueError as e:
        # 동일한 처리
        ...
```

**해결:** 데코레이터로 공통화

```python
# ✅ 데코레이터로 통일
def handle_cli_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print(f"[오류] 잘못된 입력입니다\n원인: {e}", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"[오류] 파일을 찾을 수 없습니다\n원인: {e}", file=sys.stderr)
            sys.exit(1)
    return wrapper

@handle_cli_errors
def main():
    # 비즈니스 로직만 (예외 처리 없음)
    add_transaction(...)
```

**장점:**
- 코드 중복 제거
- 에러 메시지 일관성
- 종료 코드 통일

### 6.3 타입 힌트 (Type Hints) - 안정성 향상

**문제:** 데이터 타입이 명확하지 않으면 버그 증가

```python
# ❌ 타입 불명확
def add_transaction(date, tx_type, category, amount, memo, tags):
    # amount가 int인지 str인지?
    # tags가 List인지 str인지?
    pass

# 호출 시 실수 가능
add_transaction("2024-01-01", "expense", "식비", "5000", ...)  # "5000" 오류!

# ✅ 타입 힌트로 명확
def add_transaction(
    self,
    date_str: str,
    tx_type: str,
    category: str,
    amount: int,           # int만 가능
    memo: str = "",
    tags: Optional[List[str]] = None,
) -> Transaction:
    ...

# IDE 자동완성 및 타입 체커(mypy) 지원
# 호출 시: add_transaction(..., amount="5000")  # IDE 경고!
```

**타입 힌트 예시:**
```python
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class Transaction:
    id: int
    date: str
    type: str
    amount: int
    category: str
    memo: str = ""
    tags: List[str] = field(default_factory=list)

def search_transactions(
    self,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Transaction]:
    ...

def get_summary(self, month: str, top_n: int = 5) -> Dict[str, Any]:
    ...
```

**이점:**
| 항목 | 효과 |
|------|------|
| IDE 자동완성 | 개발 속도 증가 |
| 타입 체커 (mypy) | 실행 전 버그 발견 |
| 문서화 | 함수 의도 명확 |
| 협업 | 코드 이해 용이 |

---

## 7. 기술 의사결정

### 7.1 JSONL vs CSV vs SQLite

| 항목 | JSONL | CSV | SQLite |
|------|-------|-----|--------|
| **포맷** | 한 줄 = 하나의 JSON | 테이블형 | 관계형 DB |
| **Append** | 매우 빠름 | 느림 | 빠름 |
| **Search** | 느림 (전체 스캔) | 느림 | 빠름 (인덱스) |
| **확장성** | 100KB 수준 | 1MB 수준 | 1GB+ |
| **복잡도** | 낮음 | 낮음 | 높음 |
| **버전관리** | 쉬움 (텍스트) | 쉬움 | 어려움 (바이너리) |
| **호환성** | Python 전용 | 범용 (Excel) | 범용 |

**우리의 선택: JSONL**

```
왜?
1. 프로토타입 프로젝트이므로 단순함 우선
2. 거래 추가(append)가 빠름
3. 파일 기반이므로 Git 버전관리 용이
4. 디버깅 시 파일을 직접 볼 수 있음 (텍스트)

단점은?
- 검색이 느림 (100만 건 이상이면 문제)
- 관계형 데이터 표현 어려움
→ 확장 시 SQLite로 마이그레이션 가능!
```

### 7.2 append vs save_all 전략

**거래 추가 (add) 시:**
```python
# ✅ append 사용 (빠름)
def append_transaction(self, tx: Transaction):
    with open(self.tx_file, "a") as f:  # "a" = append
        f.write(json.dumps(asdict(tx), ensure_ascii=False) + "\n")
# 장점: O(1) 속도, 파일 끝에만 추가
```

**거래 수정/삭제 시:**
```python
# ✅ save_all 사용 (안전)
def save_all_transactions(self, transactions):
    self._atomic_write_jsonl(self.tx_file, ...)
# 이유: 파일 전체를 다시 써야 하므로
#      원자적 쓰기로 안전성 보장
```

### 7.3 CSV Import의 부분 성공 처리

**문제:** 1000행 CSV에 깨진 행 10개가 섞여있으면?

```csv
date,type,category,amount,memo,tags
2024-01-01,expense,식비,5000,점심,
2024-01-02,expense,교통,invalid,버스비,  ← 오류!
2024-01-03,expense,식비,3000,저녁,태그1
```

**선택:**
1. **전체 롤백**: 1000건 모두 안 들어옴 (❌ 사용자 불만)
2. **부분 성공**: 990건 성공, 10건 실패 (✅ 추천)
3. **수동 수정**: 사용자가 직접 고침 (❌ 번거움)

**우리의 구현: 부분 성공**

```python
def import_csv(self, filepath):
    success_count = 0
    skip_count = 0
    
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # 각 행을 독립적으로 처리
                date_str = row["date"].strip()
                amount = int(row["amount"].strip())  # ← 여기서 실패 가능
                
                # add_transaction은 자체 검증
                self.add_transaction(...)
                success_count += 1
            except Exception:
                # 실패한 행만 건너뜀
                skip_count += 1
    
    print(f"[완료] 성공 {success_count}건, 실패 {skip_count}건")
    return success_count, skip_count
```

**왜 이 방식?**
- ✅ 사용자가 일부 데이터라도 받을 수 있음
- ✅ 어떤 행이 실패했는지 알 수 있음
- ✅ 실패한 행만 수정해서 다시 import 가능
- ✅ 신뢰도 높음

---

## 8. 확장성과 병목 분석

### 8.1 현재 구조의 병목 지점

**시나리오: 거래가 10만 건일 때**

| 작업 | 시간복잡도 | 병목 | 해결책 |
|------|----------|------|--------|
| 거래 추가 | O(1) | ❌ 없음 | - |
| 거래 조회 (list) | O(n) | ✅ 전체 파일 스캔 | 인덱스, DB |
| 거래 검색 (search) | O(n) | ✅ 조건 필터링 | 인덱스, 쿼리 언어 |
| 거래 수정 | O(n) | ✅ 전체 파일 다시 쓰기 | ID 기반 접근 |
| 거래 삭제 | O(n) | ✅ 전체 파일 다시 쓰기 | ID 기반 접근 |
| 월별 요약 | O(n) | ✅ 전체 데이터 집계 | 인덱스, 캐시 |

### 8.2 마이그레이션 전략

**Phase 1: JSONL (현재) - 1만 건까지 OK**
```python
storage = FileStorage(data_dir="./data")
service = BudgetService(storage)
```

**Phase 2: SQLite - 100만 건까지 가능**
```python
# 같은 인터페이스 유지
storage = SQLiteStorage(db_path="./data.db")
service = BudgetService(storage)  # 코드 변경 없음!

# Storage는 바뀌지만 Service와 CLI는 그대로
```

**Phase 3: PostgreSQL - 무제한**
```python
storage = PostgresStorage(connection_string="...")
service = BudgetService(storage)
```

**핵심: 의존성 역전!**
- Service는 `Storage` 인터페이스만 알고 있음
- 구현체(FileStorage, SQLiteStorage, ...)는 교체 가능
- CLI는 변경 없음

### 8.3 성능 최적화 로드맵

**즉시 (비용 낮음):**
- [ ] 캐시 추가 (categories, budgets)
- [ ] 배치 수정 지원
- [ ] 날짜 범위로 파일 분할 (2024-01.jsonl, 2024-02.jsonl)

**단기 (1주일):**
- [ ] SQLite 마이그레이션
- [ ] 인덱스 추가 (date, category, type)
- [ ] 트랜잭션 지원

**중기 (1개월):**
- [ ] PostgreSQL 지원
- [ ] 병렬 처리
- [ ] 부분 검색 (elasticsearch 등)

### 8.4 데이터 크기별 전략

```
데이터 크기          추천 저장소        특징
─────────────────────────────────────────────
< 10MB (1만 건)    JSONL ✅           현재 상태
10MB ~ 100MB       SQLite             마이그레이션 필요
100MB ~ 1GB        PostgreSQL + Cache
> 1GB              분산 DB + 샤딩

거래는 1건 = 약 200 bytes
따라서:
- 5만 건 ≈ 10MB
- 50만 건 ≈ 100MB
- 500만 건 ≈ 1GB
```

---

## 정리

### 아키텍처의 핵심 원칙

1. **관심사 분리**: 각 모듈이 하나의 책임만
2. **의존성 역전**: 상위가 하위에만 의존
3. **안전성**: 원자적 쓰기, 검증 강화
4. **확장성**: 저장소 교체 가능
5. **효율성**: 제너레이터로 메모리 절약

### 체크리스트와의 연결

| 체크리스트 항목 | 관련 아키텍처 |
|----------------|-------------|
| 기능 동작 | 4계층 분리로 각 기능 담당 모듈 명확 |
| 아키텍처 | 모듈별 책임 분리, 의존성 역전 |
| 고급 기법 | 제너레이터, 데코레이터, 타입 힌트 |
| 기술 의사결정 | JSONL 선택, 부분 성공 처리 |
| 확장성 | 저장소 교체 전략, SQLite 마이그레이션 |

이 가이드를 통해 프로젝트의 **"왜"**를 이해하고, 체크리스트의 각 항목을 설명할 수 있습니다!
