# 사용 가이드

## 기본 실행 순서

1. Revit 2026에서 검토할 모델을 엽니다.
2. 필요하면 `QC Settings`에서 Rule Set과 Excel 환경을 확인합니다.
3. `DOC QC` 또는 `QC Lite`를 선택합니다.
4. Export Options에서 저장 폴더와 형식을 선택합니다.
5. `Run QC`를 눌러 검사를 실행합니다.
6. pyRevit Output에서 요약, Issue Group, 저장 결과와 warning을 확인합니다.

`DOC QC`와 `QC Lite`는 read-only 방식이며 Revit 모델을 수정하지 않습니다.
`Scan QC`는 별도 개발 중인 기능으로, 선택한 옵션에 따라 QC 작업용 View와
Revision Cloud/ID TextNote 같은 검토용 요소를 생성할 수 있습니다.

## DOC QC

Sheet, View, Parameter를 모두 검사할 때 사용합니다.

- Sheet Number와 Sheet Name
- Sheet에 배치된 View 유무
- 대상 View의 이름, Scale, Template, Sheet 배치 상태
- Rule Set에 정의된 카테고리별 필수 Parameter와 입력 여부
- pyRevit Output 요약 및 선택한 CSV/XLSX Export

납품 전 점검, 전체 모델 검토, Parameter 입력 상태 확인에 적합합니다.

## QC Lite

Sheet와 View 중심으로 빠르게 상태를 확인합니다. Parameter QC는 실행하지 않습니다.

- 초기 도면 상태 확인
- 반복 실행이 필요한 중간 검토
- Sheet/View 구성의 빠른 점검

QC Lite의 기본 Export 선택은 `Summary CSV`와 `Styled XLSX Report`이며,
`Full CSV`는 기본 해제 상태입니다.

## QC Settings

`QC Settings`에서는 두 가지를 관리합니다.

### Excel Report

- `Set Python...`: Styled XLSX에 사용할 외부 `python.exe` 선택
- `Test`: Python 실행과 `openpyxl` 사용 가능 여부 확인
- `Details`: 전체 Python 경로, helper, debug log와 probe 결과를 pyRevit Output에 표시

### QC Rules

- 목록에서 Default, Interior, Company 또는 사용자 정의 Rule Set 선택
- `Use This`를 눌러 다음 QC 실행에 적용
- `Copy`로 기존 Rule Set을 사용자 정의 파일로 복사
- `Reload`로 config 폴더의 Rule Set 목록 새로고침
- Rule Count에서 Sheet/View/Parameter 기준 수 확인

목록에서 선택하는 것만으로는 활성 Rule Set이 변경되지 않습니다. 반드시 `Use This`를
눌러야 다음 DOC QC/QC Lite에 적용됩니다.

## Report

마지막 QC 실행에서 정상 생성되어 기록된 보고서를 기본 프로그램으로 엽니다.
기록 우선순위는 다음과 같습니다.

1. Styled XLSX Report
2. Summary CSV
3. Full CSV

파일 저장 형식을 모두 해제한 실행은 기존 마지막 보고서 경로를 변경하지 않습니다.
기록된 파일이 이동되거나 삭제되면 pyRevit Output에 안내가 표시됩니다.

## Help

Toolkit의 버튼 구성, Rule Set, Export Options, Styled XLSX 환경과 모델 안전 기준을
별도 WinForms 도움말 창에서 확인합니다.

## Scan QC

`Scan QC`는 Point Cloud 기반 Wall deviation 검토를 목표로 개발 중인 기능입니다.
기존 Sheet QC, View QC, Parameter QC와 분리된 `scan_qc` 모듈에서 동작합니다.

현재 지원하는 흐름은 다음과 같습니다.

1. Source Plan View를 선택합니다.
2. Point Cloud Instance를 선택합니다.
3. Analysis Scope를 선택합니다.
   - Active Plan Level
   - Selected Walls
4. Tolerance 값을 확인하거나 이번 실행용으로 입력합니다.
5. 필요한 출력 옵션을 선택합니다. 현재 PDF/CSV 출력은 계획 단계라 UI에서 비활성화되어 있습니다.
6. `Run`을 눌러 standards check, working view creation, deviation/preview flow를 실행합니다.

현재 2D 표현 방식:

- 생성된 `SCAN_QC_PLAN_*` 뷰에 Revision Cloud를 배치합니다.
- 각 Revision Cloud 중앙에 `A`, `B`, `C` 같은 알파벳 ID를 표시합니다.
- 상세 정보는 pyRevit Output의 ID mapping과 Wall deviation table에서 확인합니다.
- 향후 PDF/image report 또는 시트 하단/우측 표로 정리하는 흐름을 계획하고 있습니다.

Selected Walls MVP에서는 선택한 Wall 주변의 Point Cloud points를 샘플링하고,
PointCloudInstance transform 후보를 비교한 뒤 WallType.Width/2를 보정한 wall-face
deviation 기준으로 OK/Review/Critical을 판단합니다.

현재 제한:

- Active Plan Level 전체 Wall deviation은 아직 fallback/preview 성격입니다.
- Scan QC PDF, CSV export는 아직 구현되지 않았고 UI에서도 선택할 수 없습니다.
- Point Cloud 자체 색상은 변경하지 않습니다.
- 3D preview marker는 현재 비활성화되어 있습니다.

## Export Options

DOC QC 또는 QC Lite를 누르면 검사 전에 Export Options가 열립니다.

1. 파일을 저장할 폴더를 선택합니다.
2. 필요한 형식을 체크합니다.
3. `Run QC`를 누릅니다.

| 옵션 | 용도 |
| --- | --- |
| Full CSV | 개별 Issue 전체를 보존하는 상세 데이터 |
| Summary CSV | 반복 Issue를 그룹화한 검토 목록 |
| Styled XLSX Report | 요약·그룹·샘플·상세 시트를 포함한 보고용 Excel 파일 |

DOC QC에서는 세 형식이 기본 선택됩니다. QC Lite에서는 Full CSV만 기본 해제됩니다.
선택한 파일은 timestamp가 포함된 이름으로 지정 폴더에 저장됩니다.

## 파일을 저장하지 않고 결과만 확인하기

Export Options에서 세 가지 형식을 모두 해제한 뒤 `Run QC`를 누릅니다. 저장 폴더는
비활성화되고 파일은 생성되지 않지만, QC 결과는 pyRevit Output에 정상 표시됩니다.

이 방식은 다음 상황에 적합합니다.

- 모델 상태만 빠르게 확인할 때
- 중간 작업 중 불필요한 결과 파일 생성을 피할 때
- CSV/XLSX 환경과 무관하게 QC 로직만 실행할 때

## CSV와 XLSX 저장 방식

- CSV는 pyRevit 실행 환경에서 직접 저장됩니다.
- Styled XLSX는 QC 데이터를 임시 JSON으로 전달하고 외부 Python helper가 생성합니다.
- XLSX 생성에 실패해도 QC 결과와 선택한 CSV Export는 계속 처리됩니다.
- XLSX 실행 정보는 extension의 `reports/xlsx_helper_debug.log`에 기록됩니다.
- 임시 파일, debug log, 마지막 폴더와 보고서 경로는 Git에 포함되지 않습니다.
