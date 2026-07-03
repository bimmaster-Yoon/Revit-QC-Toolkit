# Revit QC Report Automation

Codex-assisted pyRevit tool for Revit 2026 drawing QC.

## 주요 기능

- Sheet QC
- View QC
- Parameter QC
- pyRevit Output Report
- CSV Export
- Read-only model checking
- Git-based version control

## v2.5.2 - QC Settings UI

QC Settings에서 JSON을 직접 열거나 수정하지 않고 `Browse Python...`으로
`python.exe`를 선택해 저장할 수 있습니다. 개인 경로는 Git에서 제외되는
`config/qc_config_local.json`에만 기록하며, 기존 local 설정은 유지합니다.
`Test XLSX Environment`에서 Python 실행, openpyxl 버전, helper와 debug log 상태를
확인할 수 있습니다. Codex runtime cache 경로는 동작을 막지 않고 장기 사용 경고만
표시합니다.

## v2.5.1 - Styled XLSX Report Polish

Styled XLSX는 보고서형 `QC Summary`, 그룹 검토용 `Review Groups`, 대표 항목용
`Key Samples`, 전체 데이터 검토용 `Full Detail` 시트로 구성됩니다. Summary에는
KPI 카드와 상태·Severity 영역을 배치하고, 표 시트에는 고정 열 너비, 정렬,
freeze pane, autofilter와 A4 가로 인쇄 설정을 적용합니다. QC 데이터와 CSV Export
구조는 변경하지 않습니다.

## v2.5 - Styled XLSX Report

Styled XLSX Report는 `QC Summary`, `Review Groups`, `Key Samples`, `Full Detail`
4개 시트로 구성된 보고·공유용 결과물입니다. 다크 네이비 Header, 오렌지 포인트,
Severity 강조, zebra row, filter, freeze pane과 자동 열 너비를 적용합니다.
CSV는 전체 원본 데이터와 호환성을 위한 교환용 형식으로 계속 유지합니다.
IronPython은 QC 데이터를 임시 JSON으로 저장하고 외부 Python helper를 호출합니다.
공통 `qc_config_default.json`은 `external_python_path`를 빈 값으로 유지합니다.
사용자 PC 경로는 Git에서 제외되는 `config/qc_config_local.json`에 저장하며,
local override가 없거나 비어 있으면 `py -3`, `python`, `python3` 순으로 확인합니다.
설치 명령은 `py -3 -m pip install openpyxl`입니다. 외부 Python을 찾지 못해도
XLSX만 skip하고 CSV와 QC는 정상 완료됩니다.

Styled XLSX 실행 기록은 `reports/xlsx_helper_debug.log`에 저장됩니다. QC Settings에서
감지된 Python, openpyxl 버전, helper 경로와 마지막 debug log 위치를 확인할 수 있습니다.

`config/qc_config_local.json`을 만들고 JSON 이스케이프를 적용합니다.

```json
{
  "external_python_path": "C:\\Python312\\python.exe"
}
```

설정 병합 순서는 `qc_config_default.json → qc_config_local.json override`입니다.

## v2.4 - Export Options

Run Full QC와 Quick QC 실행 시 저장 폴더와 출력 형식을 먼저 선택합니다.
Full CSV, Summary CSV, Styled XLSX Report를 체크박스로 선택할 수 있으며,
Quick QC 기본값은 Full CSV OFF, Summary CSV ON, Styled XLSX ON입니다.
선택한 폴더는 다음 실행을 위해 runtime 기록으로만 보관하고 Git에서는 제외합니다.
CSV Export와 read-only QC 검사 기능은 그대로 유지합니다.

## v2.3.1 - Toolkit Icons and Tooltips

5개 Toolkit 버튼에 기능별 미니멀 아이콘과 간결한 tooltip을 적용했습니다.
아이콘은 투명 배경의 64 x 64 PNG이며, 다크 네이비 선과 오렌지 포인트로
포트폴리오 시각 체계를 통일했습니다. QC 검사와 Export 기능 로직은 변경하지 않았습니다.

## v2.3 - QC Toolkit Buttons

기존 단일 QC Report 버튼을 `Run Full QC`, `Quick QC`, `QC Settings`,
`Open Last Report`, `Help`의 5개 버튼으로 분리했습니다. 공통 `lib`와 `config`는
extension 루트에서 공유하며, Full QC와 Quick QC가 생성한 마지막 Summary CSV 경로는
`reports/latest_report_path.txt`에 저장됩니다.

## v2.2 - Maintainable Plugin Structure

단일 `script.py`에 있던 수집, Sheet/View/Parameter 검사, 그룹화, CSV Export,
pyRevit Output 로직을 `lib/` 모듈로 분리했습니다. 검사 기준과 화면 Sample 설정은
`config/qc_config_default.json`에서 관리하며, `script.py`는 실행 순서를 연결하는
read-only 진입점 역할만 담당합니다.

## v2.1 - Compact Portfolio Report

포트폴리오 캡처용 Compact Summary에 검사 수량, Review Item 수,
Issue Group 수, QC Status와 CSV Export 구성을 한 화면에 표시합니다.
화면의 그룹 Sample은 최대 3개, 항목당 25자로 제한하며 CSV 원본은 유지합니다.

## v2.0 - Portfolio Ready Report

포트폴리오 캡처용 pyRevit Output은 Total Review Items와 Issue Groups를 중심으로
간결하게 표시합니다. 화면의 Sample Items와 긴 요소 이름만 축약하며,
Full CSV와 Summary CSV에는 전체 데이터를 유지합니다.

## v1.9 - Filtered Portfolio Report

pyRevit Output은 반복 Issue를 그룹화하여 핵심 요약과 대표 Sample만 표시합니다.
전체 상세 Issue는 Full CSV에 유지하고, 그룹 결과는 별도의 Summary CSV로 저장합니다.

이 도구는 Revit 모델을 직접 수정하지 않는 읽기 전용 검토 도구입니다.
