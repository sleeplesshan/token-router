# Token Router 총토큰 효용 검수와 제한적 보완

**결론: 조건부 사용 안내와 명시적 문맥 폭을 구현·검증했다. 후보는 선택적으로 유지한다. 범용 절감 또는 정식 배포 승격은 아직 채택하지 않는다.** 완료한 비교에서는 개선을 관측했지만, 손해 과제와 사용량 미상 실패를 포함한 전체 운영 비용의 개선은 확인되지 않았다.

## 검수와 원인

독립 Right/Left 검수를 사용했다. Right의 자동 호출 완전 비활성화 제안은 사용자의 기존 자동 조건부 적용 요청과 충돌해 채택하지 않았다. Left가 확인한 실제 문제는 넓은 반환 범위, 일반 검색에도 붙는 안내·모델 왕복, 필요한 문맥을 다시 읽는 비용이었다. 새 자동 분류기나 모델은 만들지 않았다. 자동 선택은 좁힌 스킬 description/지침을 읽는 메인 모델의 선택이며, 질문 복잡성 점수에 따른 코드 분기가 아니다.

기존 clean-final 로그 절감의 대조군은 `handler`로 빌드 옵션까지 검색했다. 이번에도 plain이 이 넓은 검색어를 스스로 선택했다. 일반 검색에 같은 배치 literal/주변 문맥 권한을 줬으나, 이 관측은 최적의 rg와 reader 알고리즘의 분리 비교가 아니다. 유리한 전체 파일 baseline으로 바꾸지 않았다.

## 변경과 식별

- 회귀 검사: `0669e13`의 `tests/test_search_context.py`.
- 구현: `14d742f`의 `scripts/router.py::parse_args`, `literal_search_packet`. `--search-context 0..12`는 `--search-term`과만 사용한다. None은 기존 코드12/로그4, 0은 일반 이웃 없음. 모든 실제 일치와 선택된 bounded traceback은 유지한다. 앞선 ERROR만 width0으로 읽으면 뒤의 선택되지 않은 traceback을 자동 포함하지 않는다.
- `SKILL.md` 발견 설명은 한 위치·이미 가진 근거를 제외하고 분산 literal의 배치 조회에 집중한다. 일반적인 `--query`를 일상적 절감 경로로 권하지 않는다. README/contract를 맞췄다.
- default v2.4, v2.5 opt-in, return-context off, Python-only/model0, matcher/순위/15% 기준/원문·좌표/source guard/최종 cap은 유지했다. 암묵 호출은 비활성화하지 않았다.

현재 비교 기준은 **2.7.0-dev / 80950e8**, 수정 후보는 **2.7.0-dev / 14d742f**, 두 군 policy v2.4다. 출시판/전역 설치 **2.6.0 / f68dc09**와 구분한다. 이번의 수정 전 군은 출시판 자체가 아니다. 기존 manifest의 v2.6.0 헤더는 원래 질문 자료의 역사적 메타데이터로 보존했으며, 실제 실행 버전은 product/execution lock이 지정한다.

## 같은 과제 실측

CPython 코드·로그, SciPy 로그, attrs 코드의 이전 회귀 4과제, 25개 사실 질문. 번역/반복을 독립 표본으로 세지 않았다. gpt-6.1-sol / medium, Codex0.162.1, 각 군1회. 분산3과제는 명시적 스킬 요청, subprocess 한 위치 과제는 세 군에 같은 질문과 암묵 선택을 사용했다. 첫 도구는 자유 선택, 원문 command 최대3(실패 포함), 안내 읽기는 별도지만 토큰·시간에는 포함한다. compound command는 도구 호출 단위이고 실제 파일 open 횟수로 해석하지 않는다.

| 완료 회차 지표 | 일반 검색 | 수정 전 개발판 | 수정 후보 |
|---|---:|---:|---:|
| 사실 정답 | 25/25 | 25/25 | 25/25 |
| 정답 + 실제 읽은 인용 범위 | 24/25 | 24/25 | 25/25 |
| 엄격 성공 과제 | 3/4 | 3/4 | 4/4 |
| input + output 총토큰 | 127,478 | 117,287 | 80,343 |
| 전체 wall 합계 | 87.27초 | 113.39초 | 77.23초 |
| episode 토큰 중앙값 | 25,677.5 | 28,443 | 20,680 |
| episode 시간 중앙값 | 22.74초 | 26.95초 | 19.69초 |
| 원문 조회 command / 후속 command | 9 / 5 | 9 / 5 | 6 / 2 |
| 실제 router 호출 | 0 | 0 | 1 |
| 별도 SKILL 읽기 command | 0 | 3 | 0 |

완료 회차 합계의 후보 변화: 일반 검색 대비 **총토큰 -37.0%, 시간 -11.5%**. 같은 과제의 토큰 차이 중앙값 -6,186, 시간 차이 중앙값 -1.87초다. 엄격 점수는 답의 정확성 + 인용 범위 전체의 실제 노출 + 일부 gold 겹침 검사이며, 의미적 충분성의 자동 증명은 아니다. CPython 대조군 두 군은 정답 pthread_kill을 맞혔지만 읽지 않은 중간 줄까지 인용했다. 보조 점수로 원래 strict 실패를 지우지 않았다.

| 과제 | 후보 토큰 변화 | 후보 완료 시간 변화 | 해석 |
|---|---:|---:|---|
| CPython 분산 로그 | -66.9% | -39.4% | 실제 reader1회, 후보6/6. 배치 조회로 추가 읽기를 줄임 |
| SciPy 분산 로그 | -3.5% | -0.7% | router0; 검색 선택 차이. 별도 실패는 아래 참조 |
| attrs 복잡한 코드 | **+6.4%** | **+16.7%** | router0; 일반 검색 대비 절감 실패 |
| subprocess 한 위치 | -42.9% | -21.1% | 모든 군 router0/별도 안내 읽기0. 검색1회 vs2회 차이; reader 효과로 세지 않음 |

한 위치 대조를 제외한 분산3과제 완료 합계는 일반 검색100,654 → 후보65,024토큰(-35.4%), 70.37 → 63.90초다. actual reader를 쓴 과제는 CPython 하나뿐이다. 작은 표본과 모델의 검색어/도구 선택 변동, 서비스·캐시 차이로 인해 범용 무열화 또는 인과효과를 주장하지 않는다.

## 실패와 전체 비용

첫 SciPy 후보 시도는 source command0, 120.016초 timeout, answer/usage 미상으로 종료했다. 최초 실험은 정해진 stop 규칙대로 중단했다. 이 회차를 삭제하거나 토큰0으로 대체하지 않았다. 자료·질문·제품·model은 바꾸지 않고 별도 continuation의 CLI 제한을240초로 늘려 나머지6회차를 완료했다. 제품의 자동 복구 엔진을 추가한 것이 아니다.

전체 **13CLI**, 알려진 **325,108토큰 + 미상1회**. 모든 시도의 정확한 총토큰은 null/미확정이다. 완료12회는 고정한 동일 질문·제품·모델을 비교하며 재개 회차의 timeout만 변경했다. 이 비교만으로 미상 실패를 포함한 전체 효용을 입증하지는 못한다. 후보 전체 시도 wall은 **197.25초**, 일반 검색87.27초보다 길다. 후보 답변 완료는4/5시도이며, 재개 후 최종 과제 성공은4/4다. 정상 종료와 문제 해결을 구분했다.

초기 예산12CLI/400k/900초는7CLI,182,603known tokens+unknown1에서 중단했다. 별도 재개 예산6CLI/200k/720초는6CLI,142,505tokens로 완료했다. 이 토큰 제한은 반환 usage에 따른 admission/stop이며 서버 hard cap이 아니다. 연구자 준비 대기 시간을 제품 wall에 더하지 않았다.

## 비용 귀속과 ablation

후보의 CPython 실제 옵션은 width4로 **기존 로그 기본 폭과 동일**하다. 따라서 -66.9%를 새 폭 조절 코드의 성과로 귀속하지 않는다. 실제 안내/reader 선택/검색어/왕복의 결합 효과다. 후보의 별도 SKILL cat0도 안내 비용0이라는 뜻이 아니다. input usage가 inline 안내 비용을 포함한다. Codex0.162.1은 명시적 skill mention을 turn에서 로드·주입한다([고정 버전 원문](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/core/src/session/turn.rs#L1082)). JSONL에 실제 주입 본문은 노출되지 않아 회차별 직접 확인은 아니다. debug의 초기 metadata 재구성은 turn 주입 전이며 exec와 config 처리도 달라 exact 입력 증거로 세지 않았다.

cached input/reasoning output은 usage 총량의 부분집합이므로 재가산하지 않는다. 선택 모델0. 완료회차 CLI CPU 합계는 일반5.863초/전개발판5.287초/후보5.066초이며 router-only CPU가 아니다. wall-CLI CPU 대기 대체치는81.405/108.103/72.164초로 remote 직접 계측이 아니다. 원문 로컬 시간은 offline-ablation의 subprocess startup+scan+render 중앙값으로 별도 기록했다; 전체 시간 개선에 합치지 않았다.

고정 literal의 오프라인 폭 ablation: CPython default4 반환8,787자 → width2 6,853자, gold anchor overlap6/6. 반면 subprocess default12도4/6, width2는3/6이고 attrs width2는2/7이다. SciPy의 넓은 고정 literal은 두 폭 모두 cap 보류다. 이는 범위 진단이고 실행 정책 성능/정답률이 아니다. 일괄 최소 폭을 채택하지 않았다. 실행 기본 query는 전후4/4 stdout·exit 동일.

## 검증, 재현과 롤백

Python3.10.20/3.14.5: 전체163 tests, Windows 전용1skip, PASS. 기존 manifest10/10, skill validator PASS. Left의 관련16 tests 독립 실행 PASS. 새0/1/12, default 동일, 모든 hit/Unicode/EOF, 잘못된 CLI, 선택/인접 traceback, cap/변경 시 빈 원문 검사를 추가했다. 기존 파일 변경·모델 좌표·긴 줄·모델0·CLI 우선순위 검사는 전체 suite에 포함한다. 새 Linux/Windows 원격 CI와 새 독립 잠금 자료는 이번에 측정하지 않았다.

공개 검토본은 이 문서·그림·요약·hash/고정 질문이다. 인증/개인 경로가 있는 CLI 원시는 로컬 `benchmarks/dual-brain-token-value-20261013`에 별도 보존한다. product-lock은 실제 package/module/source hash, prompts와 execution-lock은 질문/instructions/model/예산 hash, 두 phase는 실제 이벤트/답/commands/usage를 포함한다. 기존 자료는 덮어쓰지 않았다.

로컬 재현 명령: `python3 -m unittest discover -s tests`; `python3 scripts/run_router_tests.py tests/router-tests.json`; benchmark 폴더에서 `python3 ablation.py`(새 출력 이름 필요), `python3 report.py`, plotting 환경에서 `python plot.py`. `run.py`/`resume.py`는 신규 출력 폴더와 사전 예산을 고정한 뒤에만 다시 실행하며 비용이 발생한다. 옛 결과 폴더를 지우고 재실행하지 않는다.

롤백: `14d742f`의 기능/안내 commit만 revert하면 context helper가 원복된다. 테스트 commit0669e13도 함께 취소해야 전체 tests가 원복 API와 맞는다. 공통 safety를 제거하지 않는다. 안정판은 tag v2.6.0이다. 전역 스킬/AGENTS/public main/release는 변경하지 않았다.
