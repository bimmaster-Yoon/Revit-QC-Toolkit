# Workflow

## v2.10.0 Settings and Preset Flow

1. QC Settings의 Excel Report에서 Python과 Excel Library 상태 확인
2. Set Python...으로 Python 선택 및 저장 후 Test로 Excel Report 환경 확인
3. QC Rules에서 Default, Interior, Company 또는 custom Rule Set 선택
4. Apply Rule로 `qc_config_local.json`의 `active_config` 갱신
5. Rule Count에서 현재 기준 확인
6. DOC QC 또는 QC Lite 실행
7. 선택한 Rule Set 기준으로 read-only QC 수행
8. Export Options에서 CSV / Styled Excel Report 출력

`QC Settings → Select Rule Set → Apply Rule → Run QC → Export`

loader는 `qc_config_default.json`을 기반으로 active preset을 병합하고 local Python
경로를 마지막에 적용합니다. active preset 파일이 없거나 잘못된 경우 Default QC로
fallback하며, 검사 로직과 모델 read-only 방식은 유지됩니다.

기본 화면은 Python 실행 파일명과 상태만 표시합니다. 전체 Python 경로, config,
helper, debug log, probe error와 openpyxl 정보는 `Details`를 눌러 pyRevit Output에서
확인합니다.

## v2.5.2 QC Settings UI

1. QC Settings 버튼 실행
2. Config 및 현재 Styled XLSX Environment 상태 확인
3. `Browse Python...`으로 안정적인 local `python.exe` 선택
4. `Save Python Path`로 Git 제외 `qc_config_local.json`에 저장
5. `Test XLSX Environment`에서 Python 실행 및 openpyxl 버전 확인
6. Export Options에서 Styled XLSX 선택
7. External Python Helper가 보고용 XLSX 생성

`Settings UI → Browse Python → Save Local Config → Test Environment → Styled XLSX Export`

기본 `qc_config_default.json`은 수정하지 않습니다. 설정창은 기존 local JSON의 다른
키를 유지하면서 `external_python_path`만 갱신합니다. JSON 파일 자체를 자동으로
열지 않으며 Config 폴더와 debug log는 별도 버튼으로 확인합니다.

## v2.5.1 XLSX Report Layout

1. 기존 QC 데이터와 Temporary JSON 구조 유지
2. QC Summary에 KPI, Status/Severity, Metadata 영역 배치
3. Review Groups와 Key Samples를 보고서형 검토 표로 구성
4. Full Detail을 9pt 데이터 검토 표로 구성
5. 모든 시트에 gridline 숨김, freeze pane, autofilter와 text wrap 적용
6. A4 가로, fit-to-width 1페이지와 축소 여백을 적용해 보고·출력용 XLSX 생성

레이아웃 마감은 XLSX 표현에만 적용되며 Sheet/View/Parameter QC, Export Options,
Full CSV와 Summary CSV 데이터 흐름은 변경하지 않습니다.

## v2.5 Styled XLSX Export

1. Export Options에서 Styled XLSX Report 선택
2. `qc_config_default.json`을 로드하고 선택적 `qc_config_local.json`을 병합
3. local `external_python_path`, `py -3`, `python`, `python3` 순서로 Python 탐색
4. 후보 Python에서 `openpyxl` import 확인
5. pyRevit QC Data를 `reports/temp`의 Temporary JSON으로 직렬화
6. External Python Helper `tools/make_styled_xlsx.py` 실행
7. QC Summary / Review Groups / Key Samples / Full Detail 시트 생성
8. 선택 폴더에 `Revit_QC_Report_YYYYMMDD_HHMMSS.xlsx` 저장
9. debug 옵션이 꺼져 있으면 Temporary JSON 삭제
10. 생성 성공 시 XLSX 경로를 마지막 리포트로 우선 기록
11. helper 실패 시 warning 출력 후 CSV와 QC 계속 실행

각 실행의 Python probe, helper command, stdout/stderr, exit code, 임시 JSON과 XLSX
존재 여부는 `reports/xlsx_helper_debug.log`에서 확인합니다. 실패 warning에는 이 debug
log 경로가 포함됩니다.

`pyRevit QC Data → Temporary JSON → External Python Helper → Styled XLSX Report`

CSV는 원본 상세 데이터와 외부 호환을 위한 교환용 형식이며, Styled XLSX는
검토 결과를 읽기 쉽게 전달하는 보고·공유용 형식입니다.
외부 Python에 openpyxl이 없으면 `py -3 -m pip install openpyxl`로 설치합니다.
개인 Python 경로는 `config/qc_config_local.json`에만 기록하며 이 파일은 Git에서 제외합니다.

## v2.4 Export Options

1. DOC QC 또는 QC Lite 실행
2. 마지막 저장 폴더 안내 확인
3. Export 폴더 선택 및 쓰기 권한 검증
4. Full CSV / Summary CSV / Styled XLSX Report 선택
5. Revit Model Read-only QC 실행
6. 선택 형식만 timestamp 파일명으로 Export
7. pyRevit Output에 생성 경로 및 warning 표시
8. 마지막 저장 폴더와 우선순위 결과 경로를 runtime 파일로 기록

QC Lite 기본 선택은 Summary CSV와 Styled XLSX Report이며 Full CSV는 해제 상태입니다.
결과 경로 우선순위는 Styled XLSX, Summary CSV, Full CSV 순서입니다.
`latest_export_folder.txt`와 `latest_report_path.txt`는 로컬 경로를 포함할 수 있어
Git에서 제외합니다.

## v2.3 Toolkit Buttons

| Button | Role | Export |
| --- | --- | --- |
| DOC QC | Sheet + View + Parameter QC, Compact Summary, Review Group Summary | Full CSV + Summary CSV |
| QC Lite | Sheet + View + Parameter QC, 공식 Compact Summary | Summary CSV + Styled XLSX + Compact HTML/PDF |
| QC Settings | 공통 JSON 설정 경로 표시 및 기본 편집기로 열기 | 없음 |
| Report | 마지막 Summary CSV 또는 HTML Report 열기 | 없음 |
| Help | 버튼별 사용법과 read-only 방식 안내 | 없음 |

각 버튼은 자신의 `__file__`에서 extension 루트를 계산하고 공통 `lib` 및 `config`를
참조합니다. DOC QC와 QC Lite는 생성된 Summary CSV 경로를
`reports/latest_report_path.txt`에 저장하며, 이 runtime 파일은 Git에서 제외합니다.

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

1. pyRevit Script
2. Revit Model Read-only Check
3. Sheet QC
4. View QC
5. Parameter QC
6. Detailed Issue Collection
7. Issue Grouping
8. Full-detail CSV Data Preservation
9. Compact Summary
10. Display Truncation (25 characters)
11. Review Group Summary (3 samples per group)
12. Review Item Samples (maximum 8)
13. Full CSV Export
14. Summary CSV Export

Full CSV에는 모든 상세 Issue를 저장하고, Summary CSV에는 Category, Item Type,
QC Item, Issue Message 기준으로 그룹화한 Count와 Sample Items를 저장합니다.
pyRevit Output에만 Sample Items의 25자 축약 및 그룹당 3개 제한을 적용합니다.
Compact Summary는 검사 수량, Review Item, Issue Group, QC Status와 Export 구성을 표시합니다.
