# 0.1.80 후속 개선

기준은 clean `wp-20261020-luna-0178-results@8fedde74154ab4216edeaf369171e81530eb4a4a`다.
기존 60건 실험과 0.1.79 증거는 재실행·수정하지 않는다.
새 증거는 `.work/luna-followup-20261020/`에 둔다.

## 변경과 검증 범위

- `harness-setup`: 기존 cohort 허용 목록에 배포된 capture 스크립트 3개를 반영했다.
  기존 설치 검증의 엄격한 누락/추가 파일 검사는 유지한다.
- `workflow-obligations`: 최종 출력 목록을 줄일 때 생략 개수를 갱신한다.
  `task_candidate_omitted`는 미조사 후보 수를 유지하고,
  `task_candidate_display_omitted`는 최종 출력에서 빠진 후보 수를 뜻한다.
  발견 완료와 표시 완료는 다르다.
- `verification-results`: 같은 cwd의 Git 관측을 준비 단계와 preflight 단계
  각각에서 공유한다. 두 단계 사이 재측정과 각 실제 실행 직전 확인은 유지한다.
  준비 중 소스가 바뀌면 새 plan을 쓰지 않는 부정 대조도 포함한다.
- `native-verification` / `agent-workflow`: 기존 `run_check.py`에 읽기 전용
  `--lookup <capture.json>`을 추가했다. 일반 직접 작업도 마지막 편집 후
  Git identity를 비교할 수 있다. CURRENT/STALE/UNKNOWN은 소스 상태이지
  행동 판정이 아니며, 실패한 명령을 성공으로 바꾸지 않는다.
  Skill과 결과 조회 지침에서 이 경로를 연결했다.

`red.json`은 수정 전 설치 실패, 축약 후 개수 누락, 공유 준비의 중복 관측,
직접 capture 조회 경로 부재를 재현한다. `green-first.json`에서 네 재현이
통과했다. `harness-regression.json`은 설치/전환을 포함한 관련 146개 검사 통과다.
`runtime-regression.json`은 관련 120개 중 119개 통과와 시간 초과 프로세스
종료 검사 1개 오류를 보존한다. 샌드박스의 `taskkill` 접근 거부가 원인이며,
남은 Python 프로세스가 없음을 확인하고 해당 검사만 호스트 권한으로 재실행한
`timeout-host-regression.json`에서 통과했다. 원래 실패를 PASS로 바꾸지 않았다.
`distribution-regression.json`은 패키지/가이드/생성 리소스 관련 41개 통과다.
`resource-check.log`, `distribution-check.log`도 통과했다.
동결 패키지와 native host 소비 결과는 별도로 기록한다.

`output-budget-comparison.json`의 동일 긴 입력에서 UI 전체 5개·표시 3개일 때
생략 값이 1→2로 바로잡혔다. 조사된 후보 5개가 전부 출력에서 빠진 경우도
미조사 0개·표시 생략 5개로 구분한다. 출력은 4,972→5,007자로 예산 안에 있다.

## 준비 비용 측정

`measure-prepare.py` / `prepare-measurements.json`은 같은 임시 Git 저장소에서
12개 Feature의 공유 체크를 각각 5회 준비했다. 실제 product 명령은 0회다.
시간은 로컬 준비 함수이며 모델 추론과 호스트 시작을 포함하지 않는다.
p95는 작은 표본의 nearest-rank 최댓값이다.

| 항목 | 변경 전 | 변경 후 |
| --- | ---: | ---: |
| Git snapshot 횟수 | 24 | 2 |
| 전체 Git 호출 | 207 | 97 |
| 중앙값 ms | 6,342.0 | 4,135.6 |
| p95 ms | 6,411.7 | 4,199.5 |

영속 캐시나 검증 조건 생략은 도입하지 않았다. 남은 Git 호출에는 경로와
원본·조건 검증이 포함되므로 모든 호출을 제거하려는 최적화는 하지 않았다.

## 직접 작업 실제 소비

`consume-direct.py`, `direct-consumption.json`, `direct-consumer/`에 다음 흐름을 보존한다.

1. 일반 unittest를 기존 capture로 실행하고 실제 성공 및 CURRENT를 확인.
2. 마지막 편집에서 문법 오류를 넣고 기존 capture 조회가 STALE임을 확인.
3. 실제 재검사를 실행해 실패를 관측. 소스가 CURRENT여도 실패 exit를 유지.
4. 수정 후 새 capture로 실제 성공을 확인하고 마지막 조회가 CURRENT임을 확인.

제품 검사는 3회, 조회에 의한 재실행과 파일 변경은 각각 0회다.
기존 실행 결과를 덮어쓰지 않았고 별도 task/계약/검증 계획을 요구하지 않았다.

## 한계와 운영 경계

직접 lookup은 Git 관측만 비교한다. ignored 입력, 의존성, runtime/server identity,
행동 정확성은 별도 검증 대상이다. 해당 조건이 중요하면 기존 bound plan을 사용한다.
에이전트가 최종 lookup을 실제 수행하는지에 대한 모델 행동 평가는 별도다.
설치·발견, shell 훅 실행, native host 자동 전달과 유료 모델 성공을 구분한다.
기존 설치본·전역 설정·readiness Goal·main·원격은 이 변경의 대상이 아니다.
