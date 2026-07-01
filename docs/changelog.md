# Changelog

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
