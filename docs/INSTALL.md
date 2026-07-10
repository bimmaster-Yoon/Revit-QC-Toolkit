# 설치 가이드

## 1. 요구 환경

- Windows에서 실행되는 Autodesk Revit 2026
- Revit 2026에 연결된 pyRevit
- 저장소를 받을 Git 또는 GitHub Desktop
- Styled XLSX Report 사용 시 외부 CPython과 `openpyxl`

pyRevit 설치와 Revit 2026 연결은 이 Toolkit 설치 전에 완료되어 있어야 합니다.
Revit 리본에 pyRevit 탭이 보이지 않는다면 Toolkit 연결보다 pyRevit 설치 상태를
먼저 확인해 주세요.

## 2. 저장소 Clone

원하는 로컬 폴더에서 저장소를 Clone합니다.

```powershell
git clone <repository-url> Revit_Codex_Automation
cd Revit_Codex_Automation
```

Clone 후 다음 extension 폴더가 존재해야 합니다.

```text
Revit_Codex_Automation/
└─ YJH_RevitTools.extension/
   └─ Revit QC.tab/
      └─ QC Toolkit.panel/
```

## 3. pyRevit Extension 연결

pyRevit은 등록된 extension 검색 경로 아래의 `*.extension` 폴더를 읽습니다. pyRevit
Settings의 Custom Extension Directories에 **저장소 루트 폴더**를 추가해 주세요.

예시:

```text
C:\pyRevitExtensions\Revit_Codex_Automation
```

등록한 폴더 바로 아래에 `YJH_RevitTools.extension`이 있어야 합니다. 이미 별도의
공용 extension 검색 폴더를 운영한다면 `YJH_RevitTools.extension`을 그 폴더 아래에
배치하는 방식도 사용할 수 있습니다.

> pyRevit 버전에 따라 Settings 화면의 메뉴 명칭은 다를 수 있습니다. 핵심은
> `YJH_RevitTools.extension` 자체가 아니라 그 폴더를 포함하는 상위 경로를 extension
> 검색 경로로 등록하는 것입니다.

## 4. Styled XLSX용 Python 준비

CSV Export와 pyRevit Output만 사용할 경우 이 단계는 선택 사항입니다. Styled XLSX
Report를 사용하려면 외부 Python 환경에 저장소의 의존성을 설치합니다.

Python Launcher를 사용하는 경우:

```powershell
py -3 -m pip install -r requirements.txt
py -3 -c "import openpyxl; print(openpyxl.__version__)"
```

특정 Python 실행 파일을 사용하는 경우:

```powershell
"C:\Path\To\python.exe" -m pip install -r requirements.txt
"C:\Path\To\python.exe" -c "import openpyxl; print(openpyxl.__version__)"
```

Revit에서 `QC Settings`를 열고 다음 순서로 확인합니다.

1. `Set Python...`에서 위 패키지를 설치한 `python.exe`를 선택합니다.
2. `Test`를 실행합니다.
3. Python과 Excel Library가 Ready인지 확인합니다.
4. 오류 세부 정보가 필요하면 `Details`를 눌러 pyRevit Output을 확인합니다.

선택한 Python 경로는
`YJH_RevitTools.extension/config/qc_config_local.json`에 저장되며 Git에 포함되지
않습니다.

## 5. 새 PC 초기 설정

새 컴퓨터에서는 Clone만으로 개인 설정이 복원되지 않습니다. 다음 항목을 PC별로
설정해야 합니다.

1. Revit 2026과 pyRevit 설치 및 연결
2. 저장소 루트를 pyRevit extension 검색 경로에 등록
3. Styled XLSX를 사용할 Python과 `openpyxl` 설치
4. `QC Settings > Set Python...`에서 Python 선택 및 Test
5. 사용할 Rule Set 선택 후 `Use This` 적용
6. 첫 실행 시 Export 폴더 선택

`qc_config_local.json`, 마지막 Export 폴더, 마지막 보고서 경로, debug log는 로컬
환경 정보이므로 Git에서 제외됩니다.

## 6. Reload와 설치 확인

1. Revit을 실행하고 pyRevit 탭에서 Reload를 실행합니다.
2. 리본에 `Revit QC` 탭과 `QC Toolkit` 패널이 표시되는지 확인합니다.
3. 다음 버튼이 순서대로 보이는지 확인합니다.
   - DOC QC
   - QC Lite
   - Scan QC
   - QC Settings
   - Report
   - Help
4. `Help`를 실행해 별도 도움말 창이 열리는지 확인합니다.
5. 테스트 모델에서 `QC Lite`를 실행하고 결과가 pyRevit Output에 표시되는지
   확인합니다.

`Scan QC`는 Point Cloud 기반 Wall deviation MVP입니다. 실제 프로젝트 적용 전에는
테스트 모델에서 Source Plan View, Analysis Point Cloud Source, SCAN_QC_TARGET,
Selected Walls와 A3/A2 PDF Report 흐름을 먼저 검증해 주세요. CSV Export는 현재
Planned 상태로 비활성입니다.

버튼이 보이지 않으면 extension 검색 경로가 저장소 루트를 가리키는지,
`YJH_RevitTools.extension/Revit QC.tab/QC Toolkit.panel` 구조가 유지되어 있는지 확인한 뒤 다시
Reload합니다.
