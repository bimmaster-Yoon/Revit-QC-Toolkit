# Revit QC Toolkit

Revit 2026 모델의 Sheet, View, Parameter 상태를 점검하고 결과를 pyRevit Output과
CSV/XLSX 보고서로 정리하는 pyRevit 기반 QC Toolkit입니다.

이 프로젝트는 **read-only 검사 도구**입니다. Revit 요소를 생성·수정·삭제하는
Transaction을 사용하지 않으며, 실행 중인 모델의 정보를 수집해 검토 항목을
보고하는 데 목적이 있습니다.

## 주요 기능

- Sheet Number, Sheet Name, 배치 View 유무 검사
- View 이름의 임시 키워드, Scale, View Template, Sheet 배치 상태 검사
- JSON Rule Set에 정의된 카테고리별 필수 Parameter와 입력값 검사
- 반복 Issue를 Review Group으로 묶은 pyRevit Output 요약
- 전체 상세 항목을 보존하는 Full CSV
- 그룹별 검토 항목을 정리하는 Summary CSV
- `QC Summary`, `Review Groups`, `Key Samples`, `Full Detail` 시트로 구성된 Styled XLSX
- Default, Interior, Company 및 사용자 정의 Rule Set 선택
- 마지막으로 생성한 보고서 열기

## 버튼 구성

| 버튼 | 역할 |
| --- | --- |
| **Run Full QC** | Sheet, View, Parameter 전체 QC를 실행합니다. |
| **Quick QC** | Parameter QC를 제외하고 Sheet와 View를 빠르게 검사합니다. |
| **QC Settings** | Styled XLSX용 Python 환경과 현재 JSON Rule Set을 관리합니다. |
| **Open Last Report** | 마지막으로 정상 생성되어 기록된 XLSX 또는 CSV를 엽니다. |
| **Help** | 버튼, Rule Set, Export Options 사용 방법을 pyRevit Output에 표시합니다. |

## 결과 확인과 Export

QC 결과는 실행 후 항상 pyRevit Output에 표시됩니다. 파일 저장이 필요하지 않으면
Export Options에서 `Full CSV`, `Summary CSV`, `Styled XLSX Report`를 모두 해제하고
검사만 실행할 수 있습니다.

- **Full CSV**: 개별 Issue 전체를 보존하는 상세 데이터
- **Summary CSV**: Category, Item Type, QC Item, Issue Message 기준의 그룹 요약
- **Styled XLSX Report**: 검토·공유·보고용으로 서식을 적용한 Excel 보고서

Styled XLSX는 외부 Python과 `openpyxl`을 사용합니다. Python 환경이 준비되지 않아도
Revit QC와 CSV Export는 사용할 수 있습니다.

## JSON Rule Set

검사 기준은 `YJH_RevitTools.extension/config`의 JSON Rule Set으로 관리합니다.
`QC Settings`에서 Rule Set을 선택하고 `Use This`를 누르면 다음 Full/Quick QC부터
해당 기준이 적용됩니다. 개인 Python 경로와 활성 Rule Set 정보는 Git에서 제외되는
`qc_config_local.json`에 저장됩니다.

자세한 구조와 관리 기준은 [설정 가이드](docs/CONFIG.md)를 확인해 주세요.

## 시작하기

1. [설치 가이드](docs/INSTALL.md)에 따라 저장소와 pyRevit extension을 연결합니다.
2. Revit에서 pyRevit Reload 후 `Revit QC > QC Toolkit` 패널을 확인합니다.
3. `QC Settings`에서 Python 환경과 Rule Set을 확인합니다.
4. [사용 가이드](docs/USAGE.md)에 따라 Full QC 또는 Quick QC를 실행합니다.

버전별 변경 내역은 [기존 Changelog](docs/changelog.md), 상세 동작 흐름은
[Workflow](docs/workflow.md)에서 확인할 수 있습니다.

## 프로젝트 성격

이 저장소는 Revit 기반 인테리어 실시설계 업무에서 반복되는 모델·도면 검토를
표준화하는 BIM/DX 포트폴리오 프로젝트입니다. 단순 결과 화면보다 다음 실무 역량을
보여주는 데 초점을 둡니다.

- 도면과 모델의 정합성 검토 기준 구조화
- Sheet/View/Parameter 검사 모듈 분리
- 회사·프로젝트별 JSON Rule Set 운영
- 원본 상세 데이터와 보고용 결과물의 분리
- pyRevit 기반 실무 도구 배포와 로컬 설정 관리

이 도구의 결과는 검토를 지원하는 자료이며, 프로젝트 기준 충족 여부에 대한 최종
판단과 모델 수정은 담당 실무자가 수행합니다.
