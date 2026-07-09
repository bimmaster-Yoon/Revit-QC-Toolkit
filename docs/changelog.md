# Changelog

## v2.6 - Settings Preset Manager

- QC Settings, Export Options, Help, pyRevit Output와 Styled Excel Report에 공통 UI 팔레트 적용
- Primary button을 저채도 blue-gray `#536777`, secondary border를 `#C7D0D8`로 통일
- card fill `#F4F6F8`, border `#D6DDE3`, muted text `#5F6F7D` 적용
- warning은 `#FFF3E8` fill과 `#C85F1A` text로 제한
- report/XLSX 제목 및 header의 강한 navy와 orange accent line 완화
- QC Settings mockup과 Toolkit Button Layout portfolio asset을 동일 팔레트로 갱신
- QC Settings를 Excel Report, QC Rules, Rule Count 구조로 단순화
- 긴 Python 경로는 기본 화면에서 숨기고 실행 파일명과 상태만 표시
- Python, Excel Library, Excel Report 상태 카드를 사용자 중심 용어로 정리
- Set Python..., Test, Clear 및 Use This, Copy 버튼명으로 단순화
- Set Python...에서 Python 선택과 local 설정 저장을 한 단계로 통합
- Rule Count 카드 높이와 여백을 확보하고 숫자를 16pt bold로 표시
- 하단 작업을 Details, Open Log, Close 3개 소형 버튼으로 정리
- config/helper/debug/probe/openpyxl 상세 정보는 Details에서 pyRevit Output으로 표시
- 상태 카드와 Rule Count 카드에 고정 높이를 적용해 텍스트 하단 잘림 방지
- QC Settings 창을 resizable Form과 Font 기반 AutoScale로 정리
- QC Settings의 불필요한 AutoScroll을 제거해 기본 창의 세로 스크롤바 제거
- 고정 높이 합계를 기준으로 최종 ClientSize 1040 x 1040, MinimumSize 1020 x 1000 적용
- Excel Report 318px, QC Rules 286px, Rule Count 184px 고정 구조와 충분한 하단 여백 적용
- Main padding 28px, 섹션 간격 22px, 하단 action 60px + margin 24px 적용
- 모든 설정 버튼에 10pt, 중앙 정렬과 GDI text rendering을 적용해 Copy 텍스트 왜곡 방지
- 모든 설정 버튼 최소/실높이를 42px로 통일하고 parent row 하단 여백 확보
- Set Python 160px, Test/Clear 125px, Use This 125px 고정 폭 적용
- Copy 155px, Open Rule Folder 245px, Reload 155px 고정 크기 FlowLayout 적용
- Rule Set ComboBox에 10pt, ItemHeight 24px, 높이 42px와 54px row 적용
- 상태 카드 110px, Rule Count 카드 116px 최소 높이와 GDI 텍스트 렌더링 적용
- QC Rules 설명과 버튼 사이에 전용 spacer row를 추가해 겹침 방지
- 스크롤 콘텐츠와 하단 버튼 영역을 분리해 기본 크기에서 스크롤 최소화
- Details, Open Log, Close를 FlowLayoutPanel로 우측 정렬
- Export Options에서 저장 형식을 모두 해제한 view-only QC 실행 지원
- 저장 없는 실행은 folder 검증과 export 함수를 건너뛰고 pyRevit Output만 표시
- 파일이 생성되지 않으면 latest report와 last export folder 기록을 유지
- 기본 화면에서 default/local/helper/debug/probe 상세 경로 숨김
- Styled XLSX 용어를 Styled Excel Report로 정리
- config 폴더의 `qc_config_*.json` preset 자동 검색 및 local config 제외
- Default QC, Interior QC, Company Template preset 제공
- 선택 preset을 local `active_config`에 저장하고 Full/QC Lite에 적용
- preset metadata `preset_name`, `preset_description` 추가
- 선택 preset 복제 및 timestamp custom preset 생성 기능 추가
- Sheet/View/Parameter Rules와 Required Parameters 요약 카드 추가
- 잘못된 active preset은 Default QC로 fallback하고 warning metadata 제공
- XLSX Metadata에 preset 이름과 파일명을 함께 표시
- Help, README와 workflow에 Excel Report 및 QC Rules 흐름 반영
- Help를 7개 안내 섹션의 카드형 HTML 화면으로 재구성
- Help HTML 출력 실패 시 Markdown, Alert 순으로 안내하는 fallback 추가
- Help 설명을 한국어 중심으로 현지화하고 버튼명과 주요 UI 용어는 영어로 유지
- Help 카드의 고정 높이 없이 내용 기반 레이아웃과 compact table 적용
- Help 기본 글자를 16px로 확대하고 1180px 폭의 제품 도움말 레이아웃 적용
- Rule Set 작성 방법, 조정 가능 항목과 새 PC 설정 흐름을 Help에 추가
- 반복되던 Export, Rule Set, Model Safety 설명을 각 전용 섹션으로 통합
- Help 시작 시 Markdown 제목과 로딩 문구를 먼저 출력해 빈 output 방지
- 외부 CSS 주입을 제거하고 단순 inline HTML 및 전체 Markdown fallback 적용
- pyRevit output 렌더링 문제를 피해 Help를 독립 WinForms 창으로 전환
- 1200 x 900 resizable Help Form, 스크롤 콘텐츠와 150 x 42 Close 버튼 적용
- Help 본문 줄 수와 표 row 수를 기준으로 카드 높이를 계산해 마지막 행 clipping 방지
- 표 header 50px, 섹션별 데이터 row 최소 58~66px 및 긴 설명 row 78px 적용
- Help 카드 최소 높이를 섹션별 260~430px로 확대해 한글 배율 clipping 방지
- 표 밖 Help 본문을 줄별 Label로 분리하고 항목 간 12px 여백 적용
- 기본 흐름, Rule Set, 새 PC와 Model Safety 카드 높이를 줄간격에 맞춰 추가 확대
- Help 본문 항목 간격을 12px로 확대하고 Subtitle에 8px 전용 spacer 적용
- 표 첫 컬럼을 260px로 확대하고 Rule Set 카드 및 Footer 가독성 보정
- 기존 QC 검사, Export Options, CSV, Styled XLSX helper와 read-only 방식 유지

## v2.5.2 - QC Settings UI Polish

- JSON 기본 연결 프로그램 자동 실행 제거
- 760 x 520 이상 WinForms 기반 `Revit QC Settings` 설정창 추가
- Config 및 Styled XLSX Environment 상태를 읽기 전용 필드로 표시
- `Browse Python...`에서 `python.exe` 선택 지원
- 선택 경로를 Git 제외 `qc_config_local.json`에 저장하고 기존 local 키 유지
- 선택된 Python만 실행해 Python 및 openpyxl 버전을 엄격하게 진단
- Save 후 environment 상태 자동 갱신
- Test 결과를 설정창과 pyRevit Output에 함께 표시
- Open Config Folder, Open Debug Log, Clear Python Path 및 Close 기능 추가
- Codex runtime cache 경로 사용 시 비차단 장기 사용 warning 표시
- DPI 기준 스케일링, 1080 x 820 창과 4열 x 2행 Actions 배치로 문구 잘림 보정
- 긴 경로는 tooltip을 유지하고 TextBox가 경로 시작부터 표시되도록 개선
- 기존 QC 검사, Export Options, CSV 및 Styled XLSX 생성 흐름 유지

## v2.5.1 - Styled XLSX Report Polish

- Styled XLSX 데이터 구조와 외부 Python helper 흐름 유지
- QC Summary를 KPI 카드, Status/Severity, Metadata 영역의 보고서형 레이아웃으로 정리
- Review Groups, Key Samples, Full Detail 제목과 고정 열 너비 적용
- 기본 10pt, 표 데이터 9.5pt, Full Detail 데이터 9pt 폰트 적용
- 숫자 우측 정렬, Header 가운데 정렬, 본문 text wrap 및 vertical alignment 정리
- 모든 시트 gridline 숨김, zoom 90, A4 가로, 1페이지 너비 맞춤 적용
- 좌우 0.25, 상하 0.35 인쇄 여백 및 반복 제목 행 설정
- High/Medium/Low 및 Review Items에 완화된 Severity fill 적용
- 기존 QC 검사, Export Options, CSV Export 및 read-only 방식 유지

## v2.5 - Styled XLSX Report

- IronPython QC 데이터를 임시 JSON으로 전달하는 외부 Python helper 구조 적용
- `tools/make_styled_xlsx.py`에서 `openpyxl` 기반 Styled XLSX 생성
- config `external_python_path` 우선 사용 후 `py -3`, `python`, `python3` 탐색
- `qc_config_default.json`의 외부 Python 경로는 빈 값으로 유지
- Git 제외 `qc_config_local.json`을 자동 탐색해 사용자 PC 설정 override
- local config 최상위 `external_python_path`를 export 설정으로 정규화
- 후보 Python별 `openpyxl` import probe 후 helper 실행
- `reports/xlsx_helper_debug.log`에 후보별 command/stdout/stderr/exit code 기록
- temp JSON, helper, XLSX 경로와 파일 존재 여부 및 실패 원인 기록
- QC Settings에 default/local 경로, local 존재 여부와 적용된 Python 경로 표시
- QC Settings에 External Python/openpyxl/helper/debug log 진단 및 local 예시 추가
- debug 옵션이 꺼져 있으면 임시 JSON 자동 삭제
- QC Summary, Review Groups, Key Samples, Full Detail 시트 생성
- Summary에 프로젝트, config, 실행 모드, 검사 수량, 상태, 시간 및 저장 경로 기록
- 완화된 #34495A Header, #263645 Text, #E97826 포인트 적용
- SUIT/Malgun Gothic 폰트 적용
- High/Medium/Low Severity fill, zebra row, 얇은 border와 text wrap 적용
- Review Groups Count 강조 및 Recommendation 컬럼 추가
- 표 시트 autofilter, freeze pane 및 자동 열 너비 적용
- DOC QC와 QC Lite의 Styled XLSX 선택 옵션 연결
- 생성된 XLSX를 `latest_report_path.txt`의 최우선 결과로 기록
- 외부 Python/openpyxl 미설치 또는 helper 실패 시 XLSX만 skip하고 CSV/QC 계속 실행
- Full CSV와 Summary CSV 원본·호환 기능 유지

## v2.4 - Export Options

- DOC QC와 QC Lite 시작 시 공통 Export Options 대화상자 표시
- 체크박스로 Full CSV, Summary CSV, Styled XLSX Report 선택 가능
- QC Lite 기본값을 Full CSV OFF, Summary CSV ON, Styled XLSX ON으로 설정
- Windows 폴더 선택 UI와 실제 쓰기 가능 여부 검증 적용
- 사용자가 Cancel하거나 출력 형식을 선택하지 않으면 QC 실행 중단
- 선택 폴더에 timestamp 기반 Full/Summary CSV 저장
- 마지막 저장 폴더를 `reports/latest_export_folder.txt`에 runtime 기록
- 마지막 결과 경로를 XLSX, Summary CSV, Full CSV 우선순위로 기록
- Styled XLSX 호출 구조와 non-blocking placeholder 추가
- pyRevit Output에 저장 폴더, 선택 형식, 결과 경로와 warning 표시
- 기존 Sheet, View, Parameter 검사 로직과 read-only 방식 유지

## v2.3.1 - Toolkit Icons and Tooltips

- DOC QC에 문서와 체크마크 아이콘 적용
- QC Lite에 번개와 체크마크 아이콘 적용
- QC Settings에 슬라이더 아이콘 적용
- Report에 폴더와 문서 아이콘 적용
- Help에 문서와 물음표 아이콘 적용
- 5개 버튼 tooltip을 검사 범위와 사용 목적 중심으로 정리
- 투명 배경, 다크 네이비 선, 오렌지 포인트의 공통 스타일 적용
- 아이콘 생성 원본과 공통 스타일 자료를 extension `assets`에 보관
- 포트폴리오용 Toolkit 버튼 배치 SVG 추가
- QC 검사, CSV Export 및 read-only 기능 로직은 변경하지 않음

## v2.3 - QC Toolkit Buttons

- 기존 `QC Report.pushbutton`을 `01 DOC QC.pushbutton`으로 이전
- Sheet + View + Parameter 전체 검사 및 Full/Summary CSV 기능 유지
- Sheet + View만 검사하는 `02 QC Lite.pushbutton` 추가
- 공통 JSON 경로를 표시하고 여는 `04 QC Settings.pushbutton` 추가
- 마지막 Summary CSV를 여는 `05 Report.pushbutton` 추가
- 버튼 역할과 read-only 방식을 설명하는 `06 Help.pushbutton` 추가
- 공통 `lib`, `config`, `reports`를 extension 루트로 이동
- DOC QC와 QC Lite 실행 후 `reports/latest_report_path.txt` 갱신
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
