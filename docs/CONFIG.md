# 설정 가이드

## 설정 파일 구성

공용 Rule Set은 `YJH_RevitTools.extension/config`에 저장됩니다.

| 파일 | 역할 |
| --- | --- |
| `qc_config_default.json` | 기본 검사 기준과 전체 설정의 기준값 |
| `qc_config_interior.json` | 인테리어 도면 검토용 Rule Set |
| `qc_config_company_template.json` | 회사 기준 작성을 위한 템플릿 |
| `qc_config_custom_*.json` | QC Settings에서 복사해 만드는 로컬 사용자 정의 Rule Set |
| `qc_config_local.json` | 현재 PC의 활성 Rule Set과 외부 Python 경로 |

`qc_config_local.json`과 `qc_config_custom_*.json`은 기본적으로 Git에서 제외됩니다.
회사 공통 Rule Set으로 배포할 파일은 별도 이름으로 정리한 뒤 의도적으로 버전 관리하는
방식을 권장합니다.

## JSON Rule Set 구조

```json
{
  "version": "v2.10.1",
  "preset_name": "Example QC",
  "preset_description": "Example project QC preset.",
  "sheet_qc": {
    "require_sheet_number": true,
    "require_sheet_name": true,
    "require_placed_view": true
  },
  "view_qc": {
    "supported_view_types": ["FloorPlan", "CeilingPlan"],
    "template_required_view_types": ["FloorPlan"],
    "sheet_required_view_types": ["FloorPlan", "CeilingPlan"],
    "temporary_keywords": ["Copy", "Temp", "Working", "TEST"]
  },
  "parameter_qc": {
    "rules": [
      {
        "built_in_category": "OST_Rooms",
        "category_name": "Rooms",
        "parameter_name": "RoomType"
      }
    ]
  },
  "display": {
    "group_sample_max_length": 25,
    "group_sample_limit": 3,
    "key_issue_limit": 8,
    "key_item_max_length": 35
  },
  "export": {
    "file_prefix": "Revit_QC_Example"
  }
}
```

### 주요 영역

- `sheet_qc`: Sheet Number, Name, 배치 View 검사 사용 여부
- `view_qc`: 검사할 View Type과 Template/Sheet 배치가 필요한 View Type, 임시 이름 키워드
- `parameter_qc.rules`: Revit Built-in Category별 필수 Parameter
- `display`: pyRevit Output에 표시할 샘플 길이와 개수
- `export.file_prefix`: CSV/XLSX 파일명 접두사

JSON의 Revit category와 View Type 값은 코드에서 인식하는 정확한 이름을 사용해야
합니다. 새 기준을 추가할 때는 기존 Rule Set을 복사하고 테스트 모델에서 결과를 먼저
검증해 주세요.

## QC Settings에서 Rule Set 선택

1. `QC Settings`를 엽니다.
2. `QC Rules` 목록에서 Rule Set을 선택합니다.
3. 설명과 Rule Count를 확인합니다.
4. `Use This`를 누릅니다.
5. DOC QC 또는 QC Lite를 실행합니다.

`Use This`는 선택한 파일명을 `qc_config_local.json`의 `active_config`에 기록합니다.
QC 실행 시 Default 설정을 기준으로 활성 Rule Set을 병합하고, 마지막으로 로컬 Python
경로를 적용합니다. 활성 파일이 없거나 잘못된 경우 Default QC로 fallback하고
pyRevit Output에 warning을 표시합니다.

## Rule Count 의미

Rule Count는 선택한 Rule Set의 규모를 빠르게 확인하기 위한 지표입니다.

- **Sheet Rules**: `sheet_qc`에서 활성화된 항목 수
- **View Rules**: `view_qc`에서 값이 설정된 항목 수
- **Parameter Rules**: `parameter_qc.rules`에 등록된 검사 행 수
- **Required Parameters**: Parameter Rules에서 중복을 제거한 Parameter 이름 수

Rule Count가 많다고 QC 품질이 자동으로 높아지는 것은 아닙니다. 프로젝트 납품 기준과
실제 모델 작성 규칙에 맞는지 검토하는 용도로 사용해야 합니다.

## 개인 로컬 설정과 Git

다음 정보는 PC와 사용자마다 달라질 수 있으므로 Git에 포함하지 않습니다.

- `qc_config_local.json`의 외부 Python 절대 경로
- 현재 활성 Rule Set 파일명
- 최근 Export 폴더와 마지막 보고서 경로
- XLSX helper debug log와 임시 JSON
- 실행으로 생성된 CSV, XLSX, PDF

공용 `qc_config_default.json`에는 개인 Python 절대 경로를 기록하지 마세요. 새 PC에서는
`QC Settings > Set Python...`을 사용해 로컬 설정을 다시 생성합니다.
