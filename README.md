# Revit QC Toolkit

Revit QC Toolkit은 Revit 2026 + pyRevit 환경에서 도면 문서 품질 검토와 Scan QC 검토 흐름을 지원하는 pyRevit Extension입니다.

기존 Sheet / View / Parameter QC 기능을 기반으로, Point Cloud와 Revit Wall 모델의 정합성을 검토하는 Scan QC 기능을 단계적으로 확장하고 있습니다.

## Project Overview

이 툴킷의 목적은 Revit 기반 인테리어 실시설계와 BIM 검토 과정에서 반복적으로 발생하는 도면 품질 점검, 뷰 정리, 파라미터 누락 확인, Scan-to-BIM 정합성 검토를 빠르게 수행하는 것입니다.

주요 사용자는 Revit으로 도면화, 모델 검토, 협업 대응, 현장 기준 검토를 수행하는 BIM / DX 실무자입니다.

## Installation / Setup

1. 이 저장소를 로컬 PC에 복사하거나 Git clone 합니다.
2. pyRevit에서 `YJH_RevitTools.extension` 폴더를 Extension 경로로 추가합니다.
3. pyRevit Reload를 실행합니다.
4. Revit 상단 Ribbon에서 `Revit QC` 탭을 확인합니다.
5. 필요하면 `QC Settings`에서 Rule Set, 출력 옵션, Scan QC 설정을 확인합니다.

권장 환경:

- Revit 2026
- pyRevit
- Windows 환경
- Styled Excel Report 사용 시 외부 CPython + `openpyxl`

## Button Layout

Revit QC 탭의 버튼 순서는 아래 기준으로 정리되어 있습니다.

| 순서 | 버튼명 | 용도 |
| --- | --- | --- |
| 1 | DOC QC | Sheet / View / Parameter 전체 도면 QC 실행 |
| 2 | QC Lite | 주요 항목 요약 검토 |
| 3 | Scan QC | Point Cloud 기반 Wall Deviation / Revision Cloud ID / PDF Report |
| 4 | QC Settings | Rule Set, 출력 옵션, Scan QC 설정 관리 |
| 5 | Report | 마지막 QC Report 열기 |
| 6 | Help | 사용 가이드 열기 |

pyRevit Reload 후 다음과 같이 표시되는 것을 기준으로 합니다.

```text
DOC QC | QC Lite | Scan QC | QC Settings | Report | Help
```

## Features

### DOC QC

Sheet QC, View QC, Parameter QC를 포함한 전체 도면 문서 QC를 실행합니다.

- Sheet 번호 / 이름 / 상태 검토
- View 배치 여부 및 관리 상태 검토
- 필수 Parameter 누락 여부 확인
- Review Group Summary / Review Item Samples 출력
- Full / Summary CSV, Styled Excel Report 출력 지원

### QC Lite

주요 항목만 빠르게 확인하는 요약 검토 모드입니다.

- 빠른 사전 점검용
- 주요 Review 항목 중심 출력
- 전체 DOC QC 전 단계의 경량 검토에 적합

### Scan QC

Point Cloud 기반으로 Revit Wall 모델의 위치 오차를 검토하는 기능입니다.

현재 Scan QC 흐름:

1. Source Plan View 선택
2. Analysis Point Cloud Source 선택
3. Analysis Scope 선택
   - Active Plan Level
   - Selected Walls
4. Target Wall Filter 적용
   - Interior Walls Only
   - New Construction Only
   - Exclude Exterior Walls
   - Only `SCAN_QC_TARGET = Yes`
5. Scan QC Standards 자동 확인 / 설치
6. QC Plan View / QC 3D View 생성
7. Wall Deviation Sampling 수행
8. Review / Critical 결과에 Revision Cloud ID 생성
9. Scan QC 전용 PDF Report Sheet 생성
10. PDF Report Export

Scan QC는 원본 Active View를 직접 수정하지 않고, `SCAN_QC_PLAN_*`, `SCAN_QC_3D_*`, `SCAN_QC_REPORT_*` 형태의 작업용 View / Sheet를 생성합니다.

### QC Settings

QC 기준과 출력 옵션을 관리합니다.

- Rule Set 선택
- CSV / Excel 출력 옵션 확인
- Styled Excel Report용 Python 경로 설정
- Scan QC 기본 설정 확인

### Report

마지막으로 생성된 QC Report를 엽니다.

### Help

Revit QC Toolkit 사용 가이드를 별도 Help 창으로 표시합니다.

## Scan QC Details

### Source Plan View

Scan QC의 기준이 되는 평면 View입니다. Active View가 평면이 아니어도 UI에서 Source Plan View를 선택할 수 있습니다.

### Analysis Point Cloud Source

Wall Deviation Sampling에 사용할 Point Cloud Instance입니다. 선택한 Point Cloud를 기준으로 Revit Wall과의 거리 검토를 수행합니다.

### Standards

Scan QC는 `config/scan_qc_defaults.json` 설정과 `resources/standards/ScanQC_Standards.rvt` 기준 파일을 사용합니다.

필요 기준:

- `VT_SCAN_QC_PLAN`
- `VT_SCAN_QC_3D`
- `SCAN_QC_3D_BASE`

기준 요소가 현재 프로젝트에 없고 Standards 파일에 있으면 Scan QC 실행 중 설치를 시도합니다.

### Wall Deviation Sampling

Selected Walls 모드에서는 선택한 Wall을 기준으로 Point Cloud 주변 점을 샘플링하고, Wall face 기준으로 보정된 deviation 값을 계산합니다.

결과는 OK / Review / Critical로 분류되며, 도면에는 상위 Review / Critical 항목만 Revision Cloud ID로 표시됩니다.

### Target Wall Filter

Target Wall Filter는 검토 대상 벽을 줄이기 위한 선택 옵션입니다.

- Interior / Exterior 기준은 도면상 위치가 아니라 Revit Wall Type Function 기준입니다.
- New Construction 기준은 Phase Created / Demolished 정보를 사용합니다.
- `SCAN_QC_TARGET = Yes`는 사용자 파라미터 기준입니다.
- 여러 필터를 동시에 선택하면 AND 조건으로 적용됩니다.

기본값은 전체 벽 검토를 위해 모두 OFF입니다.

### Revision Cloud ID

Review / Critical로 판정된 벽 위치에는 Revision Cloud가 생성되고, 중앙에 A, B, C 형식의 ID가 표시됩니다.

상세 정보는 PDF Report의 Summary Panel에서 ID Mapping 표로 정리됩니다.

### PDF Report

Scan QC PDF Report는 전용 Clean Report Sheet를 생성해 도면 영역과 Summary Panel을 분리합니다.

지원 항목:

- A3 / A2 Landscape Paper Size 선택
- PDF 저장 경로 선택
- QC Plan View 자동 생성
- Revision Cloud ID 기반 ID Mapping
- Result Count / Tolerance / Project Source 정보 표시

## Current Status

| 기능 | 상태 |
| --- | --- |
| Sheet QC | 사용 가능 |
| View QC | 사용 가능 |
| Parameter QC | 사용 가능 |
| DOC QC | 사용 가능 |
| QC Lite | 사용 가능 |
| Styled Excel Report | 사용 가능 |
| Scan QC Standards 설치 | 사용 가능 |
| Scan QC QC Plan / 3D View 생성 | 사용 가능 |
| Scan QC Wall Deviation Sampling | MVP 단계 |
| Scan QC PDF Report | MVP 단계 |
| Scan QC CSV Export | 향후 개발 |

## Current Limitations

- Point Cloud Sampling은 Revit API와 Point Cloud 데이터 상태에 영향을 받습니다.
- Active Plan Level 전체 분석은 프로젝트 규모와 View Visibility 상태에 따라 추가 안정화가 필요합니다.
- Scan QC 결과는 Wall face corrected distance와 P75 기반 분류를 사용합니다.
- Point Cloud 자체 색상 변경은 수행하지 않습니다.
- CSV 보조 출력은 아직 정식 구현 전입니다.
- PDF/Image Report는 현재 MVP 레이아웃이며, 포트폴리오용 리포트 품질을 목표로 계속 개선 중입니다.

## Folder Structure

```text
YJH_RevitTools.extension/
├─ Revit QC.tab/
│  └─ QC Toolkit.panel/
│     ├─ 01 DOC QC.pushbutton/
│     ├─ 02 QC Lite.pushbutton/
│     ├─ 03 Scan QC.pushbutton/
│     ├─ 04 QC Settings.pushbutton/
│     ├─ 05 Report.pushbutton/
│     └─ 06 Help.pushbutton/
├─ lib/
│  └─ scan_qc/
├─ config/
├─ resources/
│  └─ standards/
└─ reports/
```

## Roadmap

우선순위 높은 개발 예정 항목:

1. PDF/Image Report 고도화
2. CSV 보조 출력
3. Active Plan Level 전체 분석 안정화
4. Scan QC 결과 Sheet / 이미지 리포트 품질 개선
5. 재료 면적 산출 Toolkit 추가
