# 발동 범위와 타임아웃 재검증 — 2026-10-13

**결론: 릴리즈/전역 설치 승격 기각.** 자동 발동 안내를 좁히고 실측 프로세스의120초 강제 종료를 보완했지만, 새 pilot에서는 총토큰 절감이 확인되지 않았다. 사전 중단 규칙에 따라 추가12episode, GitHub 릴리즈와 전역 설치를 실행하지 않았다. 공개 안정판/전역은2.6.0 그대로다.

## 실제 변경

측정 후보 **2.7.0(미태그) /75b74384145180cf2f0d7a70512e0980f10aba09 /policy v2.4**. 기본 Python-only, model0, 기존15% 문자 기준, matcher·순위·source guard·모델 좌표·출력 cap·return-context off는 유지했다.

SKILL description과 agents/openai.yaml을 분산 오류 로그에 맞췄다. 코드/심볼 탐색·한 위치·이미 충분한 근거는 스킬 본문을 읽기 전에 제외하도록 안내한다. 이미 주어진 안내를 다시 읽지 않도록 했다. 암묵 선택은 유지했으며, metadata는 호스트/메인 모델의 판단 지침이다. 프로그램 차원의 강제 차단기나 미래 총토큰 예측기가 아니다. 측정 가능한 계약은 실제 스킬 읽기/라우터 호출 여부다. 코드 CLI 기능은 명시적 advanced 사용으로 남겼다.

scripts/bench_process.py는 연구용이며 설치 payload에 포함하지 않는다. stdout/stderr를 실행 중 즉시 파일에 저장한다. 모든 군에 처음부터 idle240초/absolute360초, 종료 유예20초를 똑같이 적용한다. stderr 경고가 stdout 무응답 타이머를 계속 연장하지 않는다. SIGINT 후 제한된 유예와 강제 종료를 구분한다. 종료 후 완전한 usage가 없으면 총토큰은 null, 부분 누적값은 하한이며 재시도·승격을 차단한다. 완전한 청구값이 있는 실패만 최대1회 재시도, 전체 재시도2회 상한이다. 합산은 실패·재전달을 포함하고 cached/reasoning 부분집합은 더하지 않는다.

Left 검수에서 timeout 이후 capture overflow가 completeness를 잘못 유지하는 결함을 찾았다. **723eeb8**에서 독립 truncated 플래그와 입력 쓰기 thread를 추가했다. 이번 live는 시작 때75b7438 helper를 로드했고 모든 캡처가2MB보다 작고 deadline도 발생하지 않아 이 결함의 영향을 받지 않았다. 수정본은 별도9개 로컬 dummy-process 테스트와 전체 suite에서 검사했다. 새 안전 코드를 과거 모델 실측 코드로 표시하지 않는다.

## 타임아웃 원인 구분

지난 SciPy 실패는 reader/Luna 실행 이전의 메인 Codex 대기였다. 모델 서버 지연의 원인은 밝혀지지 않았고, 수십ms의 state DB 경고만으로 원인을 만들지 않았다. router의ROUTER_TIMEOUT을 바꾸지 않았다. 외부 실측 장치의120초 일괄 SIGKILL을 충분한 동일 관측 창과 스트리밍/종료 계약으로 대체했다. 새8회에서 timeout0/usage 미상0. 이것이 앞으로 서버 지연이 없어짐을 보장하지는 않는다.

이전13CLI의 **325,108known tokens+usage 미상1회**는 그대로 별도 보존했다. 새 성공 회차로 그 실패를 없애거나 토큰0으로 바꾸지 않았다. 과거까지 포함한 정확한 총비용은 여전히 미확정이다.

## 고정 실험과 비용

기존4과제×2군×2회+신규2과제×2군×1회, 총20episode를 먼저 고정했다. 원문/정답/질문/모델 설정과 hash를 잠갔고 첫 단계4과제8회에 이득이 없으면 중단하도록 했다. 새 pandas frame447,104bytes와 pytest 실제 CI log60,432bytes는 입력·정답을 먼저 고정했지만 pilot 실패로 실모델 평가하지 않았다. 이를 성공한 잠금 평가로 세지 않는다.

모델gpt-6.1-sol/medium, Codex0.162.1, built-in OpenAI/ChatGPT 로그인·구독. 네트워크/추가 모델/다른 스킬은 금지. 양쪽에 **같은 자연어 질문과 공통 지침**, native discovery 차이만 제공했다. $token-router를 넣거나 첫 reader를 강제하지 않았다. 일반 검색도 배치rg/context/번호 범위 읽기가 가능하다. 모델 source command 최대3, 성공/실패를 모두 센다. 문맥의 충분성을 희생하며 출력 최소화를 강제하지 않았다. provider 내부 HTTP retry 횟수는 독립적으로 관측되지 않는다; 완전한 CLI usage를 비용으로 사용하며 물리적 HTTP 청구 전체의 별도 원장을 주장하지 않는다.

첫 attrs plain은21,029토큰을 반환한 뒤 harness 후처리의 attempts key 충돌로 parent가 실패했다. 원시 결과를 보존하고 해당 답/usage/wall을 그대로 재사용했다. 모델을 다시 호출하지 않았고 같은 청구를 두 번 합치지 않았다. run-01의 completed terminal 표시는 이 후처리 오류를 반영하지 못한 잘못된 라벨이며 harness-repair.json에 정정 기록했다. run-02는 순수 기록 조립을 고친 실제 continuation이다. 모델/자료/질문/제품은 바꾸지 않았다.

예산22CLI/700,000known tokens/1,800초/재시도2. 실제 **8CLI,189,233토큰, timeout0, usage 미상0, 모델 재시도0**. 후처리 실패의 최초 청구도 포함했다. 연구자 수정 대기를 제품 완료 시간에 더하지 않았다. admission 시계는 재사용 이전 wall을 제외했지만 episode 합계에는14.16초를 포함했으며, 실제 총량은 한도보다 충분히 작다. absolute deadline에는 추가20초 종료 유예가 가능하다. 토큰 제한은 usage 기반 admission/stop이며 서버 hard cap이 아니다.

| pilot 합계 | 일반 검색 | 후보 설치 환경 |
|---|---:|---:|
| 사실 정답 |25/25|25/25|
| 정답+실제 노출 인용 범위 |25/25|25/25|
| 최종 성공 과제 |4/4|4/4|
| 모든 시도 input+output |83,774|105,459|
| 전체 wall |61.68초|63.09초|
| episode 토큰 중앙값 |21,346.5|26,406|
| 원문 command |6|7|
| 별도 SKILL 읽기 / router |0/0|0/0|

후보 **총토큰+25.9%, 시간+2.3%**. 인용 검사는 답 정확성+범위 전체의 실제 노출+일부 gold 겹침이며 의미적 충분성의 자동 확률 판단이 아니다. 모든 답 ID/원문 좌표/허용 파일을 실제 tool output으로 검사했다.

가장 큰 차이는 attrs: 일반 검색1회, 후보2회. 후보의 첫 검색은 조건/예외 일부를 포함하지 못해 범위를 추가로 읽었다. 양쪽 모두 스킬/reader를 호출하지 않았다. 따라서 비용 증가를 reader 실행비로 귀속하지 않는다. native metadata 존재와 모델의 검색 선택 변동을 분리한 인과 실험도 아니다. 이번 네 과제에서 별도 스킬 본문 읽기와 reader 호출이 관측되지 않았지만, 이 사실이 본문 주입 여부·미래의 강제 차단·제품 전체 비용 절감을 입증하지는 않는다. 실제 reader 호출이0이므로 이번 결과를 새로운 추출 기능의 성능으로 홍보하지 않는다.

## 검증과 배포 결정

172 tests: Python3.10.20/3.14.5 macOS PASS, Windows 전용1skip. 기존 manifest10/10, skill validator PASS. archive-only 설치/업데이트/복원/제거/no-cloud smoke에서 새 numbered literal/context0/선택 traceback도 확인했다. 신규9개 helper tests는 무응답 vs활동/absolute, stdout 조각·stderr 배수, 완료·부분·중복 usage, known 실패+재시도 합산, 새 미완료 turn, timeout 후 overflow, 큰 stdin 쓰기를 포함한다. 합성 청구값은 실제 모델 효용 표본으로 세지 않는다.

후보 Linux/Windows 원격 CI는 실행하지 않았다. 절감 기준 미충족이므로 PR/릴리즈/전역 스킬/AGENTS/인증은 변경하지 않았다. 과거 baseline과 새 결과를 섞지 않았다. 선택 제한과 실측 안전 코드만 개발 브랜치에 남긴다. 정식 사용자는 tag v2.6.0을 유지한다.

## 재현 자료와 롤백

로컬 `benchmarks/activation-gate-2.7.0-20261013`: manifest/product-lock/prompts; run-01 original raw; run-02/attempt-*의 즉시 기록 이벤트·usage·답·commands; harness-repair; 새 summary/그림. 재사용된 최초 결과는 provenance만 있으며 독립 episode로 이중 합산하지 않는다. 원문/prompt/instructions/package/capture hash가 기록돼 있다. 공개 검토본은 문서·요약·질문·hash만 포함하며 개인 경로/실행 환경 원시는 로컬에 보존한다.

오프라인: `python3 -m unittest discover -s tests`; `python3 scripts/run_router_tests.py tests/router-tests.json`; 깨끗한 commit에서 build_release와 smoke_archive. Live harness는 새 출력 폴더/사전 예산을 고정하고 실행해야 하며 기존 원시 자료를 지우지 않는다. 최초 run.py의 후처리 결함 대신 run-v2.py를 참고하되 과거 재사용 분기는 새 실험에 적용하지 않는다.

제품 후보75b7438을 취소하려면 feature commit을 revert하고 해당 smoke를 함께 원복한다. 연구 helper723eeb8은 운영 payload와 별개다. 정식 설치 롤백은 검증된 v2.6.0 archive/backup으로 수행한다. 기존 source safety를 제거하지 않는다.
