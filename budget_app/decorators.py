# 명령줄 인터페이스 예외 처리 데코레이터
import sys
from functools import wraps
from typing import Callable, Any


def handle_cli_errors(func: Callable) -> Callable:
    """CLI 명령어 실행 중 발생하는 예외를 잡아 스택트레이스 대신 
    사용자 친화적인 원인과 힌트를 출력하고 적절한 종료 코드를 반환하는 데코레이터입니다.
    
    요구사항 명세:
    - 오류는 스택트레이스 대신 원인 + 해결 힌트로 출력한다.
    - 정상 종료는 0, 오류 종료는 0이 아닌 값(1)으로 종료한다.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            # 서비스 로직에서 의도적으로 발생시킨 예외(검증 실패 등)
            print(f"\n[오류] 잘못된 입력입니다.\n원인: {e}", file=sys.stderr)
            print("해결 힌트: --help 옵션을 사용하여 명령어의 올바른 형식을 확인하거나 입력값을 다시 확인해 주세요.", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError as e:
            # 파일 경로와 관련된 예외
            print(f"\n[오류] 파일을 찾을 수 없습니다.\n원인: {e}", file=sys.stderr)
            print("해결 힌트: 파일 경로가 올바른지, 폴더에 대한 읽기/쓰기 권한이 있는지 확인해 주세요.", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            # 사용자가 강제 종료(Ctrl+C)한 경우
            print("\n[알림] 사용자에 의해 프로그램이 중단되었습니다.")
            sys.exit(130)  # 리눅스 표준 Ctrl+C 종료 코드
        except Exception as e:
            # 그 밖의 예상하지 못한 치명적 예외
            print(f"\n[시스템 오류] 예기치 않은 문제가 발생했습니다.\n원인: {e}", file=sys.stderr)
            print("해결 힌트: 프로그램 로그를 확인하거나 개발자에게 문의해 주세요.", file=sys.stderr)
            sys.exit(1)
            
    return wrapper
