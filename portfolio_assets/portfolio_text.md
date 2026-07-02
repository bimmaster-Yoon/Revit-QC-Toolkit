# InDesign Copy Deck

아래 문구는 A4 가로형 마지막 페이지의 텍스트 프레임별 최종안입니다.

## Page Title

REVIT QC REPORT AUTOMATION

## Subtitle

Codex-assisted pyRevit Workflow for Read-only Drawing QC

## Main Description

Revit 2026과 pyRevit을 기반으로 Sheet, View, Parameter 정보를 자동 점검하는 QC Report 도구를 구축했습니다. Codex를 활용해 검토 기준과 출력 구조를 반복적으로 정리했으며, 모델을 수정하지 않는 read-only 방식으로 도면 및 파라미터 정합성을 확인하도록 구성했습니다. 반복 검토 항목은 Review Group으로 분류하고, 상세 데이터와 요약 데이터를 Full CSV와 Summary CSV로 각각 출력해 후속 검토와 이력 관리에 활용할 수 있도록 했습니다.

## Workflow Caption

검토 기준 정의부터 pyRevit 스크립트 작성, Revit read-only 검사, QC Report 생성, CSV Export까지의 업무 흐름을 하나의 프로세스로 연결했습니다.

## QC Summary Caption

105개 Sheet, 302개 View, 860개 Parameter Element를 점검하고 365개 Review Item을 14개 Issue Group으로 정리했습니다. 화면에는 핵심 수치와 대표 그룹만 표시해 검토 우선순위를 빠르게 파악할 수 있도록 했습니다.

## CSV Export Caption

Full CSV에는 요소별 전체 검토 데이터를 유지하고, Summary CSV에는 반복 항목을 Category, Item Type, QC Item 기준으로 그룹화해 저장했습니다. 화면의 간결성과 실무 데이터의 추적성을 분리해 모두 확보했습니다.

## Git Version Control Caption

정상 실행이 확인된 단계별 상태를 Git commit과 tag로 저장해 v1.8의 기본 QC부터 v1.9의 그룹 요약, v2.1의 Compact Report까지 변경 이력을 관리했습니다. 이후 기능 확장 과정에서도 검증된 버전으로 즉시 롤백할 수 있는 작업 체계를 구성했습니다.

## Interview Explanation

이 작업은 개발 자체를 보여주기 위한 프로젝트라기보다, Revit 실무에서 반복되는 도면·View·Parameter 검토를 더 빠르고 일관되게 수행하기 위한 BIM/DX 개선 사례입니다. 먼저 실무에서 확인이 필요한 Sheet, View, Shared Parameter 기준을 정의하고, Codex를 활용해 pyRevit 스크립트의 구조와 예외 처리를 반복 검토했습니다. 검사는 Transaction을 사용하지 않는 read-only 방식이므로 모델을 변경하지 않으며, 반복 결과는 Review Group으로 묶어 화면에는 핵심만 보여줍니다. 동시에 Full CSV에는 요소별 상세값을 보존해 실제 수정 대상 확인과 협업 전달에 사용할 수 있도록 했습니다. Git으로 정상 작동 버전을 단계별 저장해 기능 개선과 롤백이 가능한 구조까지 함께 구축했습니다.
