# 사용자 입력 수용 및 화면 출력
import argparse
import sys
from datetime import date
from typing import Optional

from budget_app.decorators import handle_cli_errors
from budget_app.models import Transaction
from budget_app.services import BudgetService, parse_tags
from budget_app.storage import Storage


# create_parser(), handle_add_interactive(), print_transaction_table() 및 main()은
# 기존 구현을 유지하고, 아래 두 태그 파싱 위치만 parse_tags()를 사용합니다.
