# pocket-money-manager 인터랙티브 학습 시나리오

이 문서는 코드를 읽은 뒤 직접 실행하고 설명하는 연습을 위한 자료입니다. 각 시나리오는 **실행 → 관찰 → 코드 추적 → 말로 설명** 순서로 학습합니다.

> 실행 예시는 저장소 루트에서 실행합니다. 데이터가 섞이지 않도록 연습용 디렉터리를 사용합니다.
>
> ```bash
> python -m budget_app --data-dir ./practice-data category list
> ```

---

## 0. 학습 방법

각 시나리오마다 다음 질문에 답해보세요.

1. 사용자가 입력한 값은 어디에서 파싱되는가?
2. 어떤 함수가 핵심 작업을 수행하는가?
3. 어떤 검증이 실행되는가?
4. 어떤 파일이 읽히거나 변경되는가?
5. 성공 또는 실패 결과가 어떻게 사용자에게 전달되는가?
6. 이 기능의 시간·메모리 비용은 무엇인가?

코드를 설명할 때는 다음 문장 구조를 사용하면 좋습니다.

> `cli.py`가 입력을 받고, `services.py`가 규칙을 검증하고 계산한 뒤, `storage.py`가 JSONL 파일에 저장합니다. 결과는 다시 `cli.py`가 출력합니다.

---

## 1. 첫 실행과 모듈 탐색

### 실행

```bash
python -m budget_app --help
python -m budget_app --data-dir ./practice-data category list
```

### 관찰할 것

- `python -m budget_app`은 `budget_app/__main__.py`에서 시작합니다.
- `__main__.py`는 `cli.main()`을 호출합니다.
- 명령줄 옵션은 `cli.py`의 `create_parser()`가 정의합니다.
- 첫 실행 시 기본 카테고리가 없으면 `ensure_default_categories()`가 기본 카테고리를 생성합니다.

### 코드 추적 순서

```text
__main__.py
  → cli.main()
  → Storage(...)
  → BudgetService(...)
  → ensure_default_categories()
  → category list 처리
```

### 설명 연습

**질문:** 프로그램 실행의 시작점은 어디인가요?

**모범 답변:**

> `python -m budget_app` 명령은 `budget_app/__main__.py`를 실행합니다. 이 파일은 CLI의 `main()`을 호출합니다. `main()`은 인자를 파싱하고 `Storage`와 `BudgetService`를 만든 다음 사용자가 선택한 명령을 처리합니다.

---

## 2. 거래 추가(add)

### 실행

```bash
python -m budget_app --data-dir ./practice-data add
```

입력 예시:

```text
날짜: 2026-09-26
타입: expense
카테고리: 식비
금액: 12000
메모: 점심
태그: 외식,회사
```

### 데이터 흐름

```text
사용자 입력
  → handle_add_interactive()
  → BudgetService.add_transaction()
  → 날짜/타입/금액/카테고리 검증
  → Transaction 객체 생성
  → Storage.append_transaction()
  → transactions.jsonl에 한 줄 추가
  → 성공 메시지 출력
```

### 확인

```bash
cat practice-data/transactions.jsonl
python -m budget_app --data-dir ./practice-data list
```

### 설명 질문

- 거래 ID는 어떻게 만들어지나요?
- 태그는 어떤 형태로 저장되나요?
- CLI가 금액을 검증하는 것이 아니라 Service가 검증하는 이유는 무엇인가요?

### 모범 답변

> CLI는 입력을 수집하지만 업무 규칙을 직접 소유하지 않습니다. `add_transaction()`이 날짜 형식, 거래 타입, 양의 금액, 등록된 카테고리인지 검증합니다. 검증이 끝나면 `Transaction`을 만들고 `append_transaction()`으로 JSONL 마지막에 추가합니다. 추가는 기존 파일을 다시 쓰지 않으므로 일반적으로 빠릅니다.

---

## 3. 거래 조회(list)와 제너레이터

### 실행

```bash
python -m budget_app --data-dir ./practice-data list
python -m budget_app --data-dir ./practice-data list --limit 1
```

### 코드 추적

```text
cli.main()
  → service.list_transactions(limit)
  → storage.stream_transactions()
  → transactions.jsonl을 한 줄씩 읽음
  → sort_transactions()
  → print_transaction_table()
```

### 핵심 관찰

- `stream_transactions()`는 `yield`를 사용합니다.
- 파일의 모든 행을 즉시 목록으로 만들지 않고 순회 시 거래를 하나씩 생성합니다.
- 현재 `list_transactions()`는 정렬과 limit 적용을 위해 결과를 목록으로 만들기 때문에 최종적으로는 전체 거래가 메모리에 올라갑니다.

### 설명할 때 주의할 점

> 이 프로젝트는 파일 읽기 단계에서는 제너레이터로 스트리밍합니다. 하지만 최신순 정렬을 하려면 모든 결과를 비교해야 하므로 `list()`와 정렬이 필요합니다. 따라서 “list 기능 전체가 완전히 상수 메모리”라고 설명하면 안 되고, “파일 접근을 한 줄씩 처리할 수 있는 구조이며 검색/정렬 결과는 목록으로 모은다”고 설명해야 정확합니다.

---

## 4. 거래 검색(search)

### 실행

```bash
python -m budget_app --data-dir ./practice-data search --category 식비
python -m budget_app --data-dir ./practice-data search --type expense --q 점심
python -m budget_app --data-dir ./practice-data search --from 2026-09-01 --to 2026-09-30 --tag 외식
```

### 필터 흐름

```text
stream_transactions()
  → 시작 날짜 조건
  → 종료 날짜 조건
  → 카테고리 조건
  → 거래 타입 조건
  → 메모 키워드 조건
  → 태그 조건
  → 최신순 정렬
  → 테이블 출력
```

### 설명 질문

- 조건이 여러 개이면 AND인가요?
- 파일을 읽는 동안 결과를 어떻게 골라내나요?
- 10만 건일 때 무엇이 느려질 수 있나요?

### 모범 답변

> 각 조건을 통과하지 못하면 `continue`로 해당 거래를 제외하므로 여러 조건은 AND처럼 적용됩니다. 현재는 인덱스가 없는 JSONL 파일을 처음부터 끝까지 확인하므로 검색 비용은 거래 수에 비례하는 O(n)입니다. 대규모 데이터에서는 SQLite와 날짜·카테고리·타입 인덱스를 사용하는 것이 적합합니다.

---

## 5. 거래 수정(update)과 삭제(delete)

### 실행

```bash
python -m budget_app --data-dir ./practice-data update --id 1 --amount 13000 --memo "수정된 점심"
python -m budget_app --data-dir ./practice-data delete --id 1
```

### 수정/삭제 흐름

```text
전체 거래 읽기
  → ID가 일치하는 거래 찾기
  → 필드 수정 또는 대상 제외
  → 임시 JSONL 파일에 전체 데이터 쓰기
  → os.replace()로 원본 교체
```

### 왜 전체 파일을 다시 쓰나요?

JSONL은 행 단위 추가에는 적합하지만 특정 행의 길이를 안전하게 바꾸거나 중간 행을 삭제하는 기능은 제공하지 않습니다. 따라서 현재 구현은 전체 데이터를 읽고 수정된 결과를 새 파일에 쓴 뒤 원본과 교체합니다.

### 설명 질문

- 수정 중 프로그램이 중단되면 원본은 어떻게 되나요?
- update/delete의 시간복잡도는 무엇인가요?
- `append_transaction()`과 `save_all_transactions()`는 언제 각각 사용하나요?

### 모범 답변

> 추가는 파일 끝에 기록하므로 `append_transaction()`을 사용합니다. 수정과 삭제는 결과 전체를 다시 구성해야 하므로 `save_all_transactions()`를 사용합니다. 이 메서드는 `.tmp` 파일에 먼저 쓰고 `os.replace()`로 교체하므로 쓰기 도중 문제가 발생해도 기존 파일을 바로 덮어쓰지 않습니다. 다만 데이터 전체를 읽고 다시 쓰기 때문에 O(n)입니다.

---

## 6. 카테고리 관리와 참조 무결성

### 실행

```bash
python -m budget_app --data-dir ./practice-data category add "건강"
python -m budget_app --data-dir ./practice-data category list
python -m budget_app --data-dir ./practice-data category remove --id 5
```

거래에서 사용 중인 카테고리는 삭제해봅니다.

### 흐름

```text
category remove
  → 카테고리 ID 조회
  → transactions.jsonl 스트리밍
  → 거래의 category가 대상 이름과 같은지 확인
  → 사용 중이면 삭제 거부
  → 사용 중이 아니면 categories.jsonl 원자적 저장
```

### 설명

> 거래가 카테고리 이름을 참조하고 있으므로 사용 중인 카테고리를 삭제하면 과거 거래가 가리키는 값의 의미가 사라질 수 있습니다. 그래서 삭제 전에 거래 파일을 확인하고 참조 중이면 `ValueError`를 발생시켜 삭제를 막습니다. 이것이 파일 기반 프로그램에서 직접 구현한 참조 무결성 검사입니다.

---

## 7. 예산과 월별 요약(summary)

### 실행

```bash
python -m budget_app --data-dir ./practice-data budget set --month 2026-09 --amount 300000
python -m budget_app --data-dir ./practice-data summary --month 2026-09 --top 5
```

### 계산 순서

```text
월 형식 검증
  → 해당 월 거래 필터링
  → 수입 합계 계산
  → 지출 합계 계산
  → 카테고리별 지출 집계
  → 지출 금액 내림차순 정렬
  → 예산 조회
  → 사용률 = 총지출 / 예산 × 100
  → 총지출 > 예산이면 초과
```

### 설명 질문

- 수입과 지출은 어떻게 구분하나요?
- 예산이 없으면 사용률은 무엇인가요?
- `top_n`은 무엇을 제한하나요?

### 모범 답변

> 거래의 `type`이 `income`이면 수입, `expense`이면 지출로 집계합니다. 예산이 설정되지 않은 경우 사용률과 초과 여부를 계산할 기준이 없으므로 사용률은 `None`, 초과 여부는 `False`로 반환합니다. `top_n`은 카테고리별 지출 집계 결과 중 상위 몇 개를 보여줄지 결정합니다.

---

## 8. CSV 내보내기(export)

### 실행

```bash
python -m budget_app --data-dir ./practice-data export --month 2026-09 --out september.csv
head -n 3 september.csv
```

### CSV 스키마

```text
date,type,category,amount,memo,tags
```

- 파일 인코딩: `utf-8-sig`
- 헤더: `date`, `type`, `category`, `amount`, `memo`, `tags`
- 여러 태그: 쉼표로 연결

### 설명

> 내부 저장은 프로그램이 구조화된 거래를 다루기 편한 JSONL을 사용하고, export는 Excel 등 다른 도구와 호환하기 좋은 CSV를 사용합니다. 즉 JSONL은 내부 영속 저장 포맷이고 CSV는 교환 포맷입니다.

---

## 9. CSV 가져오기(import)와 부분 성공

### 실행

```bash
python -m budget_app --data-dir ./practice-data import --from september.csv
```

### 깨진 행 실습

다음처럼 금액이 숫자가 아닌 행을 포함한 CSV를 만들어보세요.

```csv
date,type,category,amount,memo,tags
2026-09-01,expense,식비,5000,정상 행,점심
2026-09-02,expense,식비,잘못된금액,깨진 행,
2026-09-03,expense,교통,3000,정상 행,버스
```

### 현재 동작

```text
행 1 → 성공 카운트 증가
행 2 → 예외 발생, 건너뜀 카운트 증가
행 3 → 성공 카운트 증가
최종 출력 → 성공 2건, 실패/건너뜀 1건
```

### 설명할 때 말할 내용

> 현재 구현은 각 행을 `try-except`로 독립 처리하므로 깨진 행 때문에 전체 import가 중단되지 않습니다. 유효한 행은 먼저 저장되고 실패한 행은 건너뛰며 성공/실패 건수를 사용자에게 보여줍니다. 사용자 신뢰를 더 높이려면 실패한 행 번호, 실패 이유, 원본 행을 별도 오류 리포트로 남기는 것이 다음 개선입니다.

### 설계 토론

- **부분 성공**: 정상 데이터는 반영하고 오류 행만 보고합니다.
- **전체 롤백**: 모든 행을 먼저 검증한 뒤 하나라도 실패하면 저장하지 않습니다.
- **권장 개선**: `ImportResult`에 성공 수와 실패 목록을 담고, 실패 목록에 행 번호·오류 메시지를 포함합니다.

---

## 10. 오류 처리와 종료 코드

### 실습

```bash
python -m budget_app --data-dir ./practice-data update --id 999999 --amount 1000
printf "종료 코드: %s\n" "$?"

python -m budget_app --data-dir ./practice-data import --from not-found.csv
printf "종료 코드: %s\n" "$?"
```

### 오류 흐름

```text
서비스에서 ValueError 또는 파일 오류 발생
  → @handle_cli_errors가 예외를 가로챔
  → 스택트레이스 대신 오류 원인 출력
  → 해결 힌트 출력
  → sys.exit(1)
```

### 설명

> `main()`에 `handle_cli_errors` 데코레이터를 적용해 CLI 전체의 공통 오류 처리를 한 곳으로 모았습니다. 입력 오류는 `ValueError`, 파일 누락은 `FileNotFoundError`, Ctrl+C는 `KeyboardInterrupt`로 구분해 메시지와 종료 코드를 다르게 처리합니다. 오류 시 `sys.exit(1)` 또는 Ctrl+C의 130을 사용하므로 셸에서도 실패를 확인할 수 있습니다.

---

## 11. 기능별 발표 연습 카드

### 카드 A: add

- 입력은 어디서 받나요? → `cli.py`
- 검증은 어디서 하나요? → `services.py`
- 저장은 어디서 하나요? → `storage.py`
- 저장 방식은? → JSONL append

### 카드 B: search

- 파일을 어떻게 읽나요? → `stream_transactions()` 제너레이터
- 조건은 어떻게 적용하나요? → 조건별 `continue`
- 정렬은 어디서 하나요? → Service의 공통 정렬 함수
- 대용량 병목은? → 인덱스 없는 전체 스캔

### 카드 C: update/delete

- 왜 전체 파일을 다시 쓰나요? → JSONL 중간 행 수정/삭제의 한계
- 안전성은 어떻게 확보하나요? → 임시 파일 작성 후 `os.replace()`
- 비용은? → 읽기와 쓰기 모두 O(n)

### 카드 D: summary

- 무엇을 계산하나요? → 수입, 지출, 잔액, 카테고리별 지출, 예산 사용률
- 월 필터는? → `date.startswith(month)`
- 예산 초과는? → 총지출이 예산보다 큰지 비교

### 카드 E: import

- 행별 처리가 가능한 이유는? → 각 행을 `try-except`로 감쌈
- 실패 행은? → 건너뛰고 실패 건수 집계
- 개선점은? → 행 번호와 오류 이유 리포트

---

## 12. 3분 발표 연습 대본

> 이 프로그램은 콘솔 CLI, 서비스, 저장소, 모델로 책임을 분리한 파일 기반 가계부입니다. 사용자가 명령을 입력하면 `cli.py`가 파싱하고, `services.py`가 날짜·금액·카테고리 같은 업무 규칙을 검증합니다. 그 다음 `storage.py`가 거래는 JSONL에 추가하고, 수정·삭제는 임시 파일에 전체 결과를 쓴 뒤 원본과 원자적으로 교체합니다.
>
> 거래 파일을 읽을 때는 제너레이터를 사용해 한 줄씩 처리할 수 있습니다. 다만 최신순 정렬이나 요약처럼 전체 데이터를 비교해야 하는 기능은 결과를 메모리에 모으므로 완전한 상수 메모리 처리는 아닙니다. 공통 오류 처리는 데코레이터로 분리해 스택트레이스 대신 사용자 메시지와 해결 힌트를 출력하고, 실패 시 0이 아닌 종료 코드를 반환합니다.
>
> 내부 저장 포맷으로 JSONL을 선택한 이유는 구현이 단순하고 거래 추가가 빠르며 사람이 직접 확인할 수 있기 때문입니다. 반면 10만 건 이상에서는 검색·수정·삭제·요약 시 전체 파일을 스캔하거나 다시 쓰는 것이 병목이 됩니다. 그때는 같은 서비스 인터페이스를 유지하면서 SQLite와 인덱스로 교체하는 것이 적절합니다. CSV import는 행별 부분 성공 방식이라 정상 행은 반영하고 오류 행은 건너뛰며 성공·실패 수를 보고합니다.

---

## 13. 최종 자기 점검

다음 질문에 문서를 보지 않고 답해보세요.

- [ ] `python -m budget_app` 실행 시 처음 호출되는 파일과 함수는?
- [ ] CLI와 Service의 책임 차이는?
- [ ] Storage가 직접 비즈니스 검증을 하지 않는 이유는?
- [ ] JSONL append와 원자적 전체 저장은 각각 언제 쓰이나요?
- [ ] 제너레이터가 메모리를 절약하는 원리는?
- [ ] list/search가 결과를 메모리에 모으는 이유는?
- [ ] 카테고리 삭제 전 거래를 확인하는 이유는?
- [ ] 예산 사용률 계산식은?
- [ ] CSV의 헤더와 인코딩은?
- [ ] 깨진 import 행을 현재 어떻게 처리하나요?
- [ ] 오류 시 종료 코드가 왜 0이 아니어야 하나요?
- [ ] 거래 10만 건에서 가장 먼저 SQLite를 고려할 이유는?

모든 질문에 자신의 말로 답할 수 있으면 체크리스트의 구조·설계·기술 의사결정 항목을 설명할 준비가 된 것입니다.
