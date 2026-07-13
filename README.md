# Revit QC Toolkit

**현재 버전: v2.10.1**

Revit QC Toolkit은 Revit 2026과 pyRevit 환경에서 도면 정보 품질과 Point Cloud 기반 모델 정합성을 검토하는 QC Extension입니다. DOC QC와 QC Lite는 모델을 변경하지 않는 검사 흐름이며, Scan QC는 선택한 옵션에 따라 별도의 QC View, Revision Cloud와 Report Sheet를 생성합니다.

## 지원 환경

- Autodesk Revit 2026
- Revit 2026에 연결된 pyRevit
- Windows
- Styled XLSX Report: 외부 CPython과 `openpyxl`
- Compact Summary PDF: 외부 CPython과 `reportlab`

외부 Python 환경이 준비되지 않아도 기본 QC 검사와 지원되는 CSV/HTML 출력은 사용할 수 있습니다. 실제 pyRevit 버전별 메뉴 명칭과 IronPython 엔진 구성은 설치 환경에 따라 다를 수 있습니다.

## 설치

1. [최신 Release](https://github.com/BIMboy-Yoon/Revit-QC-Toolkit/releases)에서 `Revit_QC_Toolkit_v2.10.1.zip`을 받습니다.
2. ZIP을 해제해 `Revit_QC_Toolkit.extension` 폴더를 pyRevit Extension 검색 경로 아래에 배치합니다.
3. pyRevit Reload를 실행합니다. 버튼이 나타나지 않으면 Revit을 다시 시작합니다.
4. Revit의 `Revit QC` 탭에서 `QC Toolkit` 패널을 확인합니다.
5. Styled XLSX/PDF 출력이 필요하면 `QC Settings`에서 외부 Python 경로와 Library 상태를 확인합니다.

소스 저장소를 직접 연결하는 경우에는 `YJH_RevitTools.extension`을 포함하는 상위 폴더를 pyRevit Custom Extension Directory로 등록합니다. 자세한 내용은 [설치 가이드](docs/INSTALL.md)를 참고하세요.

## 버튼 구성

| 순서 | 버튼 | 역할 |
| --- | --- | --- |
| 1 | DOC QC | Sheet·View·Parameter 전체 검사와 상세 보고서 생성 |
| 2 | QC Lite | 핵심 QC 검사, Compact Summary와 Dashboard 표시 |
| 3 | Scan QC | Point Cloud와 Wall 오차 분석 및 QC Report 생성 |
| 4 | QC Settings | Rule Set과 Excel/PDF 보고서 실행 환경 관리 |
| 5 | Report | 가장 최근에 생성된 QC 보고서 열기 |
| 6 | Help | 기능별 사용 방법, 안전 범위와 문제 해결 안내 |

```text
DOC QC | QC Lite | Scan QC | QC Settings | Report | Help
```

## DOC QC

현재 프로젝트의 도면 패키지를 선택한 Rule Set으로 검사합니다.

- Sheet QC: Sheet Number, Sheet Name, Titleblock과 View 배치 상태
- View QC: View Name, Scale, View Template과 Sheet 배치 상태
- Parameter QC: Rule Set에 정의된 필수 Parameter와 빈 값
- Naming QC와 View Placement QC는 기존 Sheet/View 검사에 포함
- Review Scope, QC Categories, Rule Set, Report Folder와 Report Style 설정
- pyRevit Output Summary
- Full CSV, Summary CSV, Styled XLSX Report
- Review Group Summary, Representative Item Samples와 Full Detail

DOC QC 검사는 read-only이며 Revit 요소를 생성·수정·삭제하지 않습니다.

## QC Lite

DOC QC와 동일한 결과 모델을 사용해 주요 상태를 빠르게 확인합니다.

- Export Options에서 저장 폴더와 출력 형식 선택
- Styled XLSX Report
- Summary CSV
- Compact Summary HTML
- Full CSV
- Compact Summary PDF
- QC Lite Dashboard의 Summary Cards, Issue Stats와 Top Issues
- Dashboard에서 DOC QC, 최근 Report와 상세 pyRevit Output 접근

Compact Summary HTML/PDF, CSV와 XLSX Summary는 동일한 QC result data를 기준으로 생성됩니다.

## Scan QC

선택한 Point Cloud Instance와 Revit Wall을 비교해 작업용 QC View와 검토 결과를 생성합니다.

### 설정 흐름

1. `Analysis Scope` 선택
2. `Source Plan View` 선택
3. `Target Wall Filter` 설정
4. `Analysis Point Cloud Source` 선택
5. Tolerance와 Top N Callouts 설정
6. QC Plan/3D View와 PDF Report 옵션 확인

### Target Wall Filter

- Interior Walls Only: Wall Type Function 기준
- New Construction Only: Phase Created 기준
- Exclude Exterior Walls: Wall Type Function이 Exterior인 Wall 제외
- Only `SCAN_QC_TARGET = Yes`: Shared Parameter 대상 Wall만 검사
- 여러 필터를 선택하면 AND 조건으로 적용

`SCAN_QC_TARGET`은 고정 GUID를 사용하는 Walls 인스턴스 Yes/No Shared Parameter입니다. 프로젝트에 없으면 설치 여부를 확인하며, 기존 같은 GUID를 재생성하거나 같은 이름의 다른 GUID를 덮어쓰지 않습니다.

- `Pick & Mark`: 선택 Wall을 대상에 포함
- `Pick & Clear`: 선택 Wall의 대상 값 해제
- `Show Targets`: 현재 Source Plan View의 대상 Wall 표시

### Wall Deviation과 결과

- Wall Bounding Box 주변 Point Cloud 점을 제한적으로 Sampling
- Point Cloud Transform 적용
- Wall LocationCurve와 Wall Type Width를 사용한 wall-face corrected distance
- UI Tolerance에 따른 OK / Review / Critical 분류
- P75/P90 중심의 보수적인 상태 판정과 노이즈 필터
- Review/Critical 상위 Top N 항목만 Revision Cloud ID로 표시
- Top N 범위 1~20, Slider와 직접 숫자 입력 양방향 동기화

### 생성 요소와 Report

- `SCAN_QC_PLAN_YYMMDD_HHMMSS`
- `SCAN_QC_3D_YYMMDD_HHMMSS`
- Revision Cloud와 중앙 A/B/C… ID
- Scan QC 전용 Report Sheet
- A3/A2 Landscape PDF Report

Scan QC는 원본 Source Plan View와 Point Cloud 그래픽을 수정하지 않습니다.

## QC Settings

- Styled Excel Report용 외부 Python 경로 지정
- Python / Excel Library / Excel Report 상태 확인
- Test / Clear
- Rule Set 선택과 Apply Rule
- Copy / Open Rule Folder / Reload
- Details / Open Log

외부 Python 경로와 활성 Rule Set 같은 사용자별 값은 Git에서 제외되는 로컬 설정에 저장됩니다.

## Report와 Help

- `Report`: 가장 최근에 정상 생성된 QC 보고서를 엽니다. 보고서가 없으면 안전하게 안내합니다.
- `Help`: 현재 버튼과 기능, 모델 안전 범위, 문제 해결 방법 및 GitHub 링크를 표시합니다.

## 모델 안전성

- DOC QC와 QC Lite는 read-only 검사입니다.
- Scan QC는 사용자가 선택한 옵션에 따라 작업용 View, Revision Cloud, TextNote, Report Sheet를 생성할 수 있습니다.
- Scan QC Standards 설치와 결과 요소 생성 시에만 필요한 Revit Transaction을 사용합니다.
- 원본 Source Plan View와 Point Cloud 그래픽은 수정하지 않습니다.
- 생성된 결과를 운영 프로젝트에 적용하기 전에 테스트 모델에서 먼저 검증하는 것을 권장합니다.

## 현재 제한사항

- Point Cloud 결과는 RCP/RCS 등록 상태, 좌표계, 점 밀도와 노이즈에 영향을 받습니다.
- Arc Wall, 지나치게 짧은 Wall, 신뢰할 수 있는 후보점이 부족한 Wall은 Skip될 수 있습니다.
- 대규모 Active Plan Level 분석은 View Visibility와 프로젝트 규모에 따라 시간이 증가할 수 있습니다.
- Scan QC CSV Export는 현재 Planned 상태로 비활성입니다.
- Scan QC Image Export는 정식 출력 기능에 연결되지 않았습니다.
- PDF Report는 Revit의 Sheet/View 배치 및 PDF Export 환경에 영향을 받을 수 있습니다.

## Release와 GitHub

- Repository: [github.com/BIMboy-Yoon/Revit-QC-Toolkit](https://github.com/BIMboy-Yoon/Revit-QC-Toolkit)
- Releases: [github.com/BIMboy-Yoon/Revit-QC-Toolkit/releases](https://github.com/BIMboy-Yoon/Revit-QC-Toolkit/releases)
- 변경 내역: [RELEASE_NOTES.md](RELEASE_NOTES.md)

## Folder Structure

소스 저장소:

```text
YJH_RevitTools.extension/
├─ Revit QC.tab/
│  ├─ QC Toolkit.panel/
│  │  ├─ 01 DOC QC.pushbutton/
│  │  ├─ 02 QC Lite.pushbutton/
│  │  ├─ 03 Scan QC.pushbutton/
│  │  ├─ 04 QC Settings.pushbutton/
│  │  ├─ 05 Report.pushbutton/
│  │  └─ 06 Help.pushbutton/
│  └─ Interior Finish.panel/      # 별도 개발 범위
├─ lib/
│  └─ scan_qc/
├─ config/
├─ resources/
│  ├─ parameters/
│  └─ standards/
└─ reports/                       # 로컬 실행 산출물
```

v2.10.1 배포 ZIP은 `Revit_QC_Toolkit.extension/`을 최상위로 사용하며 QC Toolkit만 포함합니다. Interior Finish, dev/probe 도구, 테스트 자산과 로컬 출력은 제외됩니다.

## Roadmap

- QC Toolkit 실프로젝트 검증과 유지보수
- Active Plan Level 대규모 분석 안정화
- Scan QC 보조 CSV/Image 출력 검토
- Interior Finish Toolkit 별도 개발
