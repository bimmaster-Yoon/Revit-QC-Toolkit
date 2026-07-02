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
