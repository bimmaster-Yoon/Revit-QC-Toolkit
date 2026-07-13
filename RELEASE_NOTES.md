# RELEASE NOTES

## v2.10.1 — Help Link & DOC QC UI Hotfix

v2.10.0 배포 후 확인된 Help 시작 오류와 DOC QC Report Style 테두리 표시를 수정한 패치 릴리스입니다.

### 수정 사항

- Help 시작 시 `Process`를 top-level에서 import하지 않도록 변경했습니다.
- GitHub Repository/Releases 링크를 클릭할 때만 `System.Diagnostics` 타입을 lazy import합니다.
- 외부 URL 실행이 실패해도 Help Form이 유지되고 pyRevit traceback이 표시되지 않도록 방어했습니다.
- DOC QC의 Report Style ComboBox를 1px 연회색 Border Panel 안에 배치해 하단 테두리가 잘리지 않도록 수정했습니다.

### 유지 사항

- DOC QC 검사와 Report 생성 로직은 변경하지 않았습니다.
- Scan QC Sampling, Wall Deviation, Revision Cloud와 PDF Report 로직은 변경하지 않았습니다.
- 기존 v2.10.0 릴리스와 태그는 그대로 보존합니다.

## v2.10.0 — QC Toolkit Completion & UI Stabilization

Revit QC Toolkit의 도면 QC, Scan QC, 사용자 인터페이스와 공개 문서를 현재 기능 기준으로 정리한 안정화 릴리스입니다.

### 주요 변경

- Scan QC, DOC QC, QC Settings와 QC Lite Export의 Section Title, Orange Accent와 얇은 Border 위계를 통일했습니다.
- WinForms DPI 대응, Secondary Button Hover, Form cleanup과 종료 성능을 안정화했습니다.
- `SCAN_QC_TARGET` Yes/No Shared Parameter 자동 설치와 대상 Wall workflow를 정리했습니다.
- `Pick & Mark`, `Pick & Clear`, `Show Targets`를 추가했습니다.
- Top N Callouts를 Slider와 직접 숫자 입력으로 설정할 수 있으며 1~20 범위로 보정합니다.
- Scan QC 전용 A3/A2 PDF Report와 Revision Cloud ID Summary를 지원합니다.
- QC Lite Export, Compact Summary와 Dashboard 레이아웃을 개선했습니다.
- Help Navigation과 콘텐츠를 최신화하고 GitHub Repository/Release 링크를 추가했습니다.
- Ribbon 버튼명과 짧은 한글 Tooltip을 현재 기능에 맞게 통일했습니다.
- README와 공개 설치 문서를 사용자 중심으로 재정리했습니다.

### 현재 제한사항

- Point Cloud Sampling은 RCP/RCS 등록 상태, 좌표계, 점 밀도와 노이즈에 영향을 받습니다.
- Arc Wall, 짧은 Wall과 후보점이 부족한 Wall은 분석에서 Skip될 수 있습니다.
- 대규모 Active Plan Level 분석은 프로젝트 규모와 View Visibility 조건에 따라 시간이 증가할 수 있습니다.
- Scan QC CSV Export는 Planned 상태로 비활성입니다.
- Scan QC Image Export는 정식 출력 기능에 연결되지 않았습니다.
- 운영 프로젝트 적용 전 테스트 모델에서 Source Plan View, Point Cloud와 Report 결과를 확인하는 것을 권장합니다.

### 다음 단계

- QC Toolkit 유지보수와 실프로젝트 검증
- Active Plan Level 대규모 분석 안정화
- Interior Finish Toolkit 별도 개발

## v2.9.0 — QC UI Stabilization & Scan Target Workflow

이번 Pre-release는 DOC QC와 Scan QC의 실무 UI 안정화, `SCAN_QC_TARGET` 대상 지정 흐름, Help 및 Ribbon 안내 체계를 정리한 버전입니다.

현재 런타임 버전은 `YJH_RevitTools.extension/lib/toolkit_version.py`의 `2.9.0` 값을 단일 기준으로 사용합니다.

### DOC QC / QC Settings / Help UI

- DOC QC, Scan QC, QC Settings, Help의 WinForms 정렬과 100~125% DPI 표시 안정성을 개선했습니다.
- Footer 버튼 크기, 바깥 여백, GroupBox 정렬과 긴 경로 표시를 통일했습니다.
- DOC QC Report Folder 선택 후 경로가 즉시 갱신되도록 정리했습니다.
- UI 종료 시 Timer, event handler, Form lifecycle을 점검하고 불필요한 후처리와 강제 GC를 제거했습니다.
- Hover와 종료 과정에서 전체 Form Refresh를 피하고 필요한 컨트롤만 다시 그리도록 정리했습니다.
- Help를 카드형 Navigation 구조로 개편하고 현재 버튼명과 기능 설명을 반영했습니다.

### Ribbon 버튼 및 한글 Tooltip

Revit QC 탭의 버튼 순서와 명칭을 아래 기준으로 통일했습니다.

```text
DOC QC | QC Lite | Scan QC | QC Settings | Report | Help
```

- 각 pushbutton의 `bundle.yaml`에 짧은 한글 Ribbon Tooltip을 정의했습니다.
- 기존 `tooltip.md`, Help, README의 설명을 동일한 버튼명으로 정리했습니다.
- 이전 버튼명 표기를 제거하고 현재 버튼명으로 통일했습니다.

### SCAN_QC_TARGET Workflow

- 고정 GUID를 사용하는 `SCAN_QC_TARGET` Yes/No 인스턴스 Shared Parameter 정의를 추가했습니다.
- 최초 Scan QC 실행 시 Walls 카테고리 Instance Parameter 설치 여부를 확인할 수 있습니다.
- 동일 GUID가 이미 있으면 재생성하지 않고, 같은 이름의 다른 GUID는 자동 덮어쓰지 않습니다.
- `Pick & Mark`: Revit에서 선택한 Wall을 `Yes`로 지정합니다.
- `Pick & Clear`: 선택한 Wall 값을 `No`로 해제합니다.
- `Show Targets`: 현재 Source Plan View의 대상 Wall을 Revit 선택 상태로 표시합니다.
- 선택 취소 시 별도 Output이나 경고창 없이 Setup UI 상태를 유지합니다.

### Scan QC Setup

- Target Wall Filter는 여러 옵션 선택 시 AND 조건으로 적용됩니다.
- Interior / Exterior는 Wall Type Function, New Construction은 Phase Created 기준임을 명확히 표시합니다.
- Top N Callouts를 1~20 범위의 오렌지 Slider와 직접 숫자 입력으로 설정할 수 있습니다.
- Slider와 숫자 입력은 양방향으로 동기화되며 범위를 벗어난 값은 자동 보정됩니다.
- Default Tolerances의 OK / Review / Critical 셀 크기와 정렬을 통일했습니다.
- Scan QC 창의 마지막 위치와 크기를 기억하며, 모니터 구성이 변경되면 WorkingArea 안으로 보정합니다.

### Scan QC PDF Report

- A3 Landscape와 A2 Landscape 전용 Clean Report Sheet를 지원합니다.
- QC Plan View와 Summary Panel 영역을 분리하고 Viewport Scale을 자동 조정합니다.
- Revision Cloud ID와 Summary ID Mapping이 동일한 Top N 결과를 사용합니다.
- PDF 저장 경로 선택을 지원하며 취소 시 QC View / Sheet / PDF 생성을 진행하지 않습니다.

### 현재 제한사항

- Point Cloud Sampling은 Revit API, RCP/RCS 데이터 밀도와 좌표계 상태에 영향을 받습니다.
- Active Plan Level 전체 분석은 대규모 프로젝트와 View Visibility 조건에서 추가 검증이 필요합니다.
- Wall Deviation은 현재 Wall-face corrected distance와 P75/P90 기반 MVP 판정을 사용합니다.
- Scan QC CSV Export는 Planned 상태로 비활성입니다.
- Image Report는 아직 정식 Export 기능에 연결되지 않았습니다.
- Point Cloud 자체 색상과 원본 Source Plan View는 변경하지 않습니다.

### 향후 개발 예정

1. PDF / Image Report 품질 고도화
2. CSV 보조 출력
3. Active Plan Level 대규모 분석 안정화
4. 운영 프로젝트별 Point Cloud Sampling 성능 검증

## v2.8.1 — Scan QC Report Layout

- A3 / A2 Scan QC Report Sheet 옵션을 추가했습니다.
- 전용 Clean Report Sheet와 Summary Panel 레이아웃을 정리했습니다.
- Source Plan View, Point Cloud Source, Revision Cloud ID Mapping을 PDF에 반영했습니다.
- PDF 저장 경로 선택과 Viewport Scale 자동 조정 흐름을 추가했습니다.

## 배포 환경

- Revit 2026
- pyRevit
- Windows
- Styled XLSX Report 사용 시 외부 CPython + `openpyxl`

기존 Sheet QC / View QC / Parameter QC 검사 로직과 Point Cloud 자체 그래픽은 변경하지 않습니다.
