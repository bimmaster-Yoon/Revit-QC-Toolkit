# RELEASE NOTES

## v2.8.1 Scan QC Report Layout

이번 릴리즈는 Scan QC MVP 이후 Report Sheet 레이아웃, Setup UI, 버튼명, Help 문구, 한글 문서를 정리한 배포 버전입니다.

## 주요 변경

### 버튼명 및 Revit QC 탭 정리

Revit QC 탭의 버튼명을 짧고 일관되게 정리했습니다.

```text
DOC QC | QC Lite | Scan QC | QC Settings | Report | Help
```

- `DOC QC`: Sheet / View / Parameter 전체 도면 QC
- `QC Lite`: 주요 항목 요약 검토
- `Scan QC`: Point Cloud 기반 Wall Deviation 검토
- `QC Settings`: Rule Set, 출력 옵션, Scan QC 설정 관리
- `Report`: 마지막 QC Report 열기
- `Help`: 사용 가이드 열기

### Scan QC Setup UI 개선

- 주요 옵션에 한글 중심 Tooltip을 추가했습니다.
- `Analysis Point Cloud Source` 명칭으로 Point Cloud 선택 용도를 명확히 했습니다.
- Target Wall Filter 설명을 보완했습니다.
- Target Wall Filter 기본값을 모두 OFF로 정리했습니다.
- 여러 Target Wall Filter를 동시에 선택하면 AND 조건으로 적용된다는 점을 명확히 했습니다.

### Target Wall Filter

Scan QC 대상 벽을 선택적으로 제한할 수 있습니다.

- Interior Walls Only
- New Construction Only
- Exclude Exterior Walls
- Only `SCAN_QC_TARGET = Yes`

Interior / Exterior 기준은 Revit Wall Type Function 기준이며, 도면상 위치 자동 판정 기능은 아닙니다.

### A3 / A2 Paper Size 옵션

Scan QC PDF Report에서 A3 Landscape와 A2 Landscape를 선택할 수 있습니다.

- A3 Landscape: 기본값
- A2 Landscape: 넓은 도면 영역이 필요한 경우 선택

### PDF 저장 경로 선택

Create PDF Report 실행 시 PDF 저장 경로를 사용자가 선택할 수 있습니다.

사용자가 저장 대화상자를 취소하면 Scan QC 실행을 계속하지 않고 Setup UI로 돌아가도록 정리했습니다.

### Scan QC 전용 PDF Report Sheet Layout

기존 회사 Titleblock에 의존하지 않는 Scan QC 전용 Clean Report Sheet 구조를 적용했습니다.

- 좌측 / 중앙: QC Plan View 영역
- 우측: Summary Panel 영역
- 도면과 Summary가 겹치지 않도록 레이아웃 분리
- Viewport Scale 자동 조정
- 긴 Viewport Title 노출 최소화

### Summary Panel 정리

우측 Summary Panel을 리포트형 구조로 정리했습니다.

- Header
- Project / Source
- Tolerance
- Result Count
- ID Mapping
- Method / Note

텍스트 위계, 줄간격, 구분선 위치, 표 컬럼 정렬을 정리해 PDF 캡처용 리포트로 사용할 수 있는 수준을 목표로 개선했습니다.

### Revision Cloud ID 기반 Report 구성

Scan QC 결과 중 상위 Review / Critical 항목만 Revision Cloud ID로 표시합니다.

- 도면에는 A, B, C 형식의 ID만 표시
- 상세 정보는 PDF Summary Panel의 ID Mapping 표에 정리
- 도면의 Revision Cloud ID와 Summary ID Mapping 개수가 일치하도록 정리

## 현재 제한사항

- Point Cloud Sampling은 Revit API와 Point Cloud 데이터 상태에 영향을 받습니다.
- Active Plan Level 전체 분석은 프로젝트 규모와 View Visibility 조건에 따라 추가 안정화가 필요합니다.
- PDF Report는 MVP 레이아웃이며, 이미지 리포트 / 시트 리포트 품질 고도화가 필요합니다.
- CSV 보조 출력은 아직 정식 구현 전입니다.
- Point Cloud 자체 색상 변경은 수행하지 않습니다.

## 다음 개발 예정

1. PDF/Image Report 고도화
2. CSV 보조 출력
3. Active Plan Level 전체 분석 안정화
4. 재료 면적 산출 Toolkit

## 배포 메모

- Revit 2026 + pyRevit 환경 기준입니다.
- 기존 Sheet QC / View QC / Parameter QC 동작은 유지합니다.
- Scan QC는 별도 `scan_qc` 모듈 중심으로 유지됩니다.
- Point Cloud API Probe와 개발용 도구는 릴리즈 UI와 배포 패키지에서 제외합니다.
