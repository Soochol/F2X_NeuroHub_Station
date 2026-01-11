# F2X NeuroHub Station Service - Portable Mode

서비스 등록 없이 일반 프로그램처럼 실행하는 배치 파일입니다.

## 파일 설명

### 1. update_portable.bat
**완전 자동 업데이트 + 실행 스크립트**

- GitHub에서 최신 릴리스 자동 다운로드
- ZIP 압축 해제
- 설정 파일 자동 백업/복원
- 버전 비교 후 필요시에만 업데이트
- 실행까지 한 번에 처리

**사용법:**
```batch
update_portable.bat
```

**동작 과정:**
1. 현재 버전 확인 (`VERSION.txt`)
2. GitHub API로 최신 릴리스 버전 조회
3. 버전 비교
   - 최신이면: 바로 실행
   - 구버전이면: 업데이트 후 실행
4. 실행 중인 프로세스 자동 종료
5. 설정 파일 백업 (`config` 폴더)
6. 새 버전 다운로드 및 압축 해제
7. 파일 업데이트 (logs, data, config 보존)
8. StationService.exe 실행

### 2. run_portable.bat
**빠른 실행 스크립트**

이미 설치된 StationService를 바로 실행합니다.
설치되지 않았다면 자동으로 `update_portable.bat`을 호출합니다.

**사용법:**
```batch
run_portable.bat
```

또는 더블클릭으로 실행

## 설치 위치

기본 설치 경로: `C:\StationService_Portable`

변경하려면 배치 파일 상단의 `INSTALL_PATH` 변수를 수정하세요.

```batch
set "INSTALL_PATH=D:\MyFolder\StationService"
```

## 디렉토리 구조

```
C:\StationService_Portable\
├── StationService.exe          # 실행 파일
├── VERSION.txt                 # 현재 버전
├── config\                     # 설정 파일 (업데이트 시 보존)
│   └── station.yaml
├── logs\                       # 로그 파일 (업데이트 시 보존)
│   └── service.log
├── data\                       # 데이터베이스 (업데이트 시 보존)
│   └── station.db
└── sequences\                  # 테스트 시퀀스
    └── ...
```

## 보존되는 파일/폴더

업데이트 시 다음 항목들은 삭제되지 않고 보존됩니다:
- `config/` - 설정 파일
- `logs/` - 로그 파일
- `data/` - 데이터베이스
- `VERSION.txt` - 버전 정보

## Windows 서비스 vs Portable 모드

| 기능 | Windows 서비스 | Portable 모드 |
|------|---------------|--------------|
| 관리자 권한 | 필요 (설치 시) | 불필요 |
| 자동 시작 | 부팅 시 자동 | 수동 실행 |
| 백그라운드 실행 | 가능 | 콘솔 창 필요 |
| 트레이 아이콘 | 있음 | 있음 |
| 서비스 관리 | `services.msc` | 배치 파일 |
| 업데이트 방법 | `update.ps1` | `update_portable.bat` |
| 설치 도구 | NSSM | 불필요 |

## 사용 시나리오

### Portable 모드 권장
- 개발/테스트 환경
- 관리자 권한이 없는 환경
- 임시로 사용하는 경우
- 여러 버전을 동시에 테스트

### Windows 서비스 권장
- 프로덕션 환경
- 24/7 무인 운영
- 자동 시작 필요
- 관리자 권한 사용 가능

## 문제 해결

### 1. "PowerShell을 찾을 수 없습니다"
Windows 7 이상에서는 PowerShell이 기본 설치되어 있어야 합니다.
- 해결: PowerShell 설치 확인

### 2. "다운로드 실패"
GitHub API 접근이 차단되었을 수 있습니다.
- 해결: 방화벽/프록시 설정 확인
- 해결: 수동으로 ZIP 파일 다운로드 후 압축 해제

### 3. "StationService.exe를 찾을 수 없습니다"
압축 해제 중 문제가 발생했을 수 있습니다.
- 해결: `C:\StationService_Portable` 폴더 삭제 후 재실행

### 4. 포트 충돌 (8080 already in use)
다른 프로그램이 포트 8080을 사용 중입니다.
- 해결: `config\station.yaml`에서 포트 변경

```yaml
api:
  host: 0.0.0.0
  port: 8081  # 다른 포트로 변경
```

### 5. 업데이트 후 설정이 초기화됨
설정 백업/복원 과정에서 문제가 발생했습니다.
- 확인: `config\station.yaml` 파일 존재 여부
- 해결: 수동으로 설정 파일 복원

## 수동 설치 (배치 파일 없이)

1. GitHub 릴리스 페이지에서 ZIP 다운로드:
   https://github.com/Soochol/F2X_NeuroHub_Station/releases/latest

2. 원하는 위치에 압축 해제

3. `config\station.yaml` 설정

4. `StationService.exe` 실행

## 자동 업데이트 활성화

`run_portable.bat` 파일을 수정하여 실행 시마다 자동으로 업데이트 확인:

```batch
:: 이 줄의 주석을 제거
start /min "" "%UPDATE_SCRIPT%"
```

주의: 업데이트 다운로드 중 실행이 지연될 수 있습니다.

## 작업 스케줄러 등록 (선택사항)

Windows 부팅 시 자동 실행하려면 작업 스케줄러에 등록:

1. `taskschd.msc` 실행
2. "작업 만들기"
3. 트리거: "로그온할 때"
4. 동작: `C:\...\update_portable.bat` 실행
5. 확인

또는 PowerShell로 등록:

```powershell
$action = New-ScheduledTaskAction -Execute "C:\path\to\update_portable.bat"
$trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "StationService" -Action $action -Trigger $trigger -RunLevel Limited
```

## 버전 확인

현재 설치된 버전:
```batch
type C:\StationService_Portable\VERSION.txt
```

최신 버전 조회:
```powershell
Invoke-RestMethod -Uri "https://api.github.com/repos/Soochol/F2X_NeuroHub_Station/releases/latest" | Select-Object tag_name
```

## 로그 확인

실시간 로그:
```batch
powershell Get-Content C:\StationService_Portable\logs\service.log -Wait -Tail 50
```

최근 50줄:
```batch
powershell Get-Content C:\StationService_Portable\logs\service.log -Tail 50
```

## 제거

1. 실행 중인 프로세스 종료:
   ```batch
   taskkill /F /IM StationService.exe
   ```

2. 폴더 삭제:
   ```batch
   rmdir /s /q C:\StationService_Portable
   ```

## 지원

- GitHub Issues: https://github.com/Soochol/F2X_NeuroHub_Station/issues
- Wiki: https://github.com/Soochol/F2X_NeuroHub_Station/wiki
