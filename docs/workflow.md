# Workflow

## v2.2 Module Flow

1. `script.py` — config 로드 및 실행 순서 제어
2. `collectors.py` — Sheet, 배치 View ID, View, Parameter 대상 수집
3. `checks_sheet.py` — Sheet Number, Name, 배치 View 검사
4. `checks_view.py` — View Name, 임시 키워드, Scale, Template, Sheet 배치 검사
5. `checks_parameter.py` — Shared Parameter 존재 및 입력값 검사
6. `grouping.py` — Review Group, Summary, 대표 Sample 생성
7. `exporters.py` — Full CSV 및 Summary CSV 저장
8. `report_ui.py` — Compact Summary와 Review 표 출력

검사 기준은 `config/qc_config_default.json`에서 관리합니다. 각 모듈은 모델 요소를
읽기만 하며 Transaction을 생성하지 않습니다.

## Report Flow

1. Codex Prompt
2. pyRevit Script
3. Revit Model Read-only Check
4. Sheet QC
5. View QC
6. Parameter QC
7. Detailed Issue Collection
8. Issue Grouping
9. Full-detail CSV Data Preservation
10. Compact Summary
11. Portfolio Display Truncation (25 characters)
12. Review Group Summary (3 samples per group)
13. Review Item Samples (maximum 8)
14. Full CSV Export
15. Summary CSV Export
16. Git Version Control
17. Rollback Workflow

Full CSV에는 모든 상세 Issue를 저장하고, Summary CSV에는 Category, Item Type,
QC Item, Issue Message 기준으로 그룹화한 Count와 Sample Items를 저장합니다.
pyRevit Output에만 Sample Items의 25자 축약 및 그룹당 3개 제한을 적용합니다.
Compact Summary는 검사 수량, Review Item, Issue Group, QC Status와 Export 구성을 표시합니다.
