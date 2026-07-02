# Changelog

## v2.3.1 - Toolkit Icons and Tooltips

- Run Full QC에 문서와 체크마크 아이콘 적용
- Quick QC에 번개와 체크마크 아이콘 적용
- QC Settings에 슬라이더 아이콘 적용
- Open Last Report에 폴더와 문서 아이콘 적용
- Help에 문서와 물음표 아이콘 적용
- 5개 버튼 tooltip을 검사 범위와 사용 목적 중심으로 정리
- 투명 배경, 다크 네이비 선, 오렌지 포인트의 공통 스타일 적용
- 아이콘 생성 원본과 공통 스타일 자료를 extension `assets`에 보관
- 포트폴리오용 Toolkit 버튼 배치 SVG 추가
- QC 검사, CSV Export 및 read-only 기능 로직은 변경하지 않음

## v2.3 - QC Toolkit Buttons

- 기존 `QC Report.pushbutton`을 `Run Full QC.pushbutton`으로 이전
- Sheet + View + Parameter 전체 검사 및 Full/Summary CSV 기능 유지
- Sheet + View만 검사하는 `Quick QC.pushbutton` 추가
- 공통 JSON 경로를 표시하고 여는 `QC Settings.pushbutton` 추가
- 마지막 Summary CSV를 여는 `Open Last Report.pushbutton` 추가
- 버튼 역할과 read-only 방식을 설명하는 `Help.pushbutton` 추가
- 공통 `lib`, `config`, `reports`를 extension 루트로 이동
- Full QC와 Quick QC 실행 후 `reports/latest_report_path.txt` 갱신
- 5개 버튼에 기존 icon.png를 임시 공통 아이콘으로 적용
- 각 버튼별 tooltip.md 추가
- Transaction을 사용하지 않는 read-only 방식 유지

## v2.2 - Maintainable Plugin Structure

- `script.py`를 수집, 검사, 그룹화, Export, UI 모듈을 호출하는 실행 진입점으로 단순화
- Revit 요소 수집 로직을 `lib/collectors.py`로 분리
- Sheet, View, Parameter QC를 각각 독립 검사 모듈로 분리
- 반복 Issue 그룹화 및 Summary 계산을 `lib/grouping.py`로 분리
- Full CSV 및 Summary CSV 저장을 `lib/exporters.py`로 분리
- pyRevit Compact Report 출력을 `lib/report_ui.py`로 분리
- 검사 Category, View Type, 임시 키워드, Parameter 규칙을 JSON config로 이동
- v2.1 Compact Summary, Review Group Summary, Review Item Samples 결과 유지
- Transaction을 사용하지 않는 read-only 검사 방식 유지

## v2.1 - Compact Portfolio Report

- pyRevit Output 상단에 7개 핵심 항목으로 구성된 Compact Summary 적용
- Checked Sheets, Checked Views, Checked Parameter Elements 표시
- Total Review Items, Issue Groups, QC Status 및 CSV Export 구성 표시
- Review Group Summary의 Sample Items를 최대 3개로 제한
- 화면 Sample Item을 항목당 최대 25자로 축약
- Review Item Samples를 최대 8개로 제한
- Full CSV 및 Summary CSV에는 축약하지 않은 전체 값 유지
- 기존 Sheet QC, View QC, Parameter QC 및 읽기 전용 검사 방식 유지

## v2.0 - Portfolio Ready Report

- QC Summary를 Checked Sheets, Checked Views, Checked Parameter Elements,
  Total Review Items, Issue Groups, High / Medium / Low 중심으로 간소화
- Issue Groups 수치를 별도 강조 영역으로 표시
- Issue Group Summary를 Review Group Summary로 변경
- Key Issue Samples를 Review Item Samples로 변경하고 최대 10개로 제한
- 임시 키워드 View, 배치 View가 없는 Sheet, Parameter 대표 누락 그룹 순으로 우선 표시
- 화면 Sample Item과 긴 요소 이름을 항목당 최대 35자로 축약
- Full CSV 및 Summary CSV에는 축약하지 않은 전체 데이터 유지
- 기존 Sheet QC, View QC, Parameter QC 및 읽기 전용 검사 방식 유지

## v1.9 - Filtered Portfolio Report

- pyRevit Output을 QC Summary, Issue Group Summary, Key Issue Samples 구조로 정리
- Category, Item Type, QC Item, Issue Message 기준 반복 Issue 그룹화
- Sample Items를 그룹당 최대 5개로 제한
- 임시 키워드가 포함된 View를 Key Issue Samples에 우선 표시
- Sheet에 배치되지 않은 도면용 View를 Count와 Sample Items로 요약
- 반복 Parameter 누락을 Category와 Parameter 단위로 요약
- 모든 상세 Issue를 포함하는 Full CSV와 그룹 결과용 Summary CSV 분리
- CSV 저장 실패 시 QC 검사가 중단되지 않도록 예외 처리

## v1.8 - Sheet + View + Parameter QC

- Sheet QC 구현
- View QC 구현
- Parameter QC 구현
- CSV Export 구현
- pyRevit button icon 적용
- Revit 2026 + pyRevit 환경에서 정상 실행 확인
- 현재 버전을 Git baseline으로 저장
