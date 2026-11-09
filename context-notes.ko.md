# 컨텍스트 노트

[English](context-notes.md) | **한국어**

작업 중 내린 결정과 그 이유를 시간순으로 기록한다.

## 2026-11-09 — 초기 계획

- **수집은 직접 크롤링 대신 집계 API를 쓴다.** (이후 GitHub 공고 목록을 주 출처로 바꿨다. 아래 "수집 출처를 GitHub 공고 목록으로 변경" 참고.) LinkedIn은 약관상 스크래핑을 금지하고 차단도 강하다. Indeed는 공개 검색 API를 종료했고 크롤링 시 차단이 잦다. JSearch는 Google for Jobs 기반이라 두 사이트의 공고를 모두 포함한다.
- **사용자는 본인 1인이다.** 인증과 멀티테넌시가 필요 없어 범위가 크게 줄어든다.
- **UI는 별도 웹앱 대신 Notion DB로 한다.** 사용자 제안이다. 목록, 필터, 보드 뷰, 메모 기능을 Notion이 이미 제공하므로 백엔드 스크립트만 만들면 된다.
- **알림은 Discord 웹훅으로 보낸다.** 사용자가 선택했다. Notion 자체 알림은 외부에서 트리거하기 어렵다.
- **실행은 GitHub Actions cron에서 한다.** 서버 없이 무료로 돌릴 수 있고, 비밀값은 Secrets로 관리한다.
- **언어는 Python으로 한다.** 스크립트 중심이고 API·LLM 연동이 간단하다.
- **MVP 범위는 수집 + 알림이다.** 지원 현황 관리와 이력서 작성은 2·3단계로 미룬다.
- **중복 제거는 Notion DB의 `Job ID`로 한다.** 상태 파일을 따로 두지 않아 Actions 실행 간 상태를 공유할 필요가 없다.

- **Meta Muse(개인 AI 에이전트)는 코드로 직접 연동하지 않는다.** 사용자가 말한 "muse"는 Meta의 소비자용 에이전트 Muse다. 외부에서 메시지를 밀어넣는 API가 없어 알림 채널로는 쓸 수 없다. 대신 Muse에 Notion 커넥터가 있어서, 데이터를 Notion에 모아 두면 Muse가 별도 작업 없이 읽고 다룰 수 있다. 그래서 Notion을 단일 저장소로 두는 설계를 유지한다. 2026-11 기준 커넥터 지원 범위는 출처마다 다르니 실제 앱에서 확인해야 한다.

## 2026-11-09 — 검색 조건

- **직무는 인턴과 신입(New Grad / Associate / Junior) SWE 두 트랙으로 나눈다.** 검색어를 트랙별로 두고 Notion에 `트랙` 속성으로 구분한다. 캐나다는 인턴을 "Co-op"으로 부르는 경우가 많아 검색어에 포함했다.
- **국가는 지역(region) 단위로 분리한다.** 사용자가 미국을 따로 두고 싶어 했다. 지역마다 Notion DB와 Discord 웹훅을 분리해 섞이지 않게 하고, 미국 추가는 설정 변경만으로 가능하게 한다.
- **미국은 수집도 꺼 둔다(`enabled: false`).** 사용자는 "알림은 캐나다만"이라고 했다. 미국 공고를 알림 없이 미리 모을지는 명시하지 않았는데, JSearch 할당량을 아끼려고 기본값을 수집도 끄는 쪽으로 정했다. 원하면 `enabled: true`, `notify: false`로 바꿔 알림 없이 수집만 할 수 있다.
- **원격 여부는 필터하지 않는다.** 사용자가 무관하다고 했다.
- **시니어 이상 공고는 제목 키워드로 제외한다.** 집계 API의 경력 필터만으로는 부정확할 수 있어 이중으로 거른다.

## 2026-11-09 — 수집 출처를 GitHub 공고 목록으로 변경

사용자가 공고 목록 저장소 4개(파일 기준)를 공유했다. 직접 확인한 내용은 다음과 같다.

- **SimplifyJobs** (New-Grad-Positions, Summer2027-Internships)는 `.github/scripts/listings.json`에 구조화 데이터가 있다. 기본 브랜치는 `dev`이고 하루에도 여러 번 갱신된다. 확인 시점 기준 활성 공고는 신입 약 3,200건(캐나다 약 150건), 인턴 약 5,300건(캐나다 약 450건)이다. 비개발 직무(Hardware, Quant, Product 등)도 섞여 있어 `category`로 걸러야 한다. 국가 정보는 따로 없어서 `locations` 문자열("Toronto, ON, Canada", "Remote in Canada", "SF")로 판별한다.
- **Francklin9999/canada-internship**은 캐나다 전용이고 마크다운 표만 있다. 기본 브랜치는 `master`다. 행 형식은 `| 회사 | 제목(NEW 접두어 가능) | 위치 | 비고 | 게시일<br><sub>..</sub> | <a href=URL>Apply</a> | <!--id:0--> |`이다. id 주석은 모두 0이라 쓸 수 없어 URL을 키로 쓴다. 상단에 회사별 집계 표도 있어 "Tech" 섹션 안의 공고 표만 파싱해야 한다. 별 16개 정도의 작은 저장소라 언제 멈출지 모른다.

결정은 다음과 같다.

- **MVP 출처는 이 GitHub 목록들로 한다.** 무료이고 키와 할당량이 없으며, 약관 문제도 없다. 학생·신입 대상으로 이미 선별되어 있어 JSearch 검색 결과보다 품질이 좋을 가능성이 크다. 이 덕분에 MVP 준비에서 RapidAPI 가입이 빠진다.
- **JSearch는 지우지 않고 선택 출처로 남긴다(기본 비활성).** GitHub 목록이 놓치는 공고를 보완하거나 목록이 멈췄을 때 대체할 수 있다.
- **`Job ID`는 정규화한 URL로 한다.** 출처 간 ID 체계가 달라서다. 같은 공고가 Simplify와 canada-internship에 모두 있을 수 있으니 회사+제목으로도 병합한다.

## 2026-11-09 — 포트폴리오 공개 범위

- **공개 범위는 코드와 공개 공고 보드로 한다.** 사용자가 선택했다. 외부인은 읽기만 가능하다.
- **지원 현황은 공개하지 않는다.** 지원한 회사와 단계가 다른 채용 담당자에게 보이면 불리할 수 있다. 보드 데이터는 Notion이 아니라 수집 결과에서 만들어서, 개인 필드가 섞일 경로를 구조적으로 막는다.
- **보드는 GitHub Pages 정적 페이지로 한다.** 서버와 비용이 없고 Actions 실행과 같은 흐름에서 배포된다. 빌드 도구 없는 HTML과 JS라 유지보수가 가볍다. 나중에 웹 UI를 키울 일이 생기면 그때 프레임워크를 검토한다.
- **Pages는 아티팩트 배포 방식으로 한다.** 데이터를 커밋하는 방식은 하루 2회씩 봇 커밋이 쌓여 포트폴리오 저장소의 히스토리를 어지럽힌다.
- **소스 저장소 3곳 모두 라이선스가 명시되지 않았다**(GitHub API로 확인). 출처를 표기하고 걸러낸 일부만 링크와 함께 보여주며, 출처별로 보드에서 뺄 수 있게 한다.
- **저장소를 공개해도 비밀값은 안전하다.** 비밀값은 모두 GitHub Secrets와 로컬 `.env`에만 두고, config에는 환경변수 이름만 적는다.

## 2026-11-09 — git 설정

- **계획 문서(plan, checklist, context-notes, CLAUDE.md)는 공개한다.** 사용자가 결정했다. 설계 과정 자체가 포트폴리오가 된다.
- **커밋 이메일은 이 저장소에만 GitHub noreply 주소로 설정했다** (`87403433+AndyChoi4495@users.noreply.github.com`). 전역 설정의 개인 Gmail이 공개 히스토리에 남지 않게 하려는 것이다. 전역 git 설정은 건드리지 않았다.

## 2026-11-09 — 이중 언어 문서

- **GitHub에 올라가는 모든 문서는 영어와 한국어 버전을 모두 둔다.** 사용자가 요청했다.
- **한 파일에 두 언어를 섞지 않고 파일을 나눈다.** `X.md`는 영어, `X.ko.md`는 한국어이고 각 파일 위에 언어 전환 링크를 둔다. GitHub에서 흔한 방식이고 파일마다 읽기 편하다.
- **기본은 영어(`X.md`)로 한다.** 포트폴리오를 주로 볼 사람이 캐나다 채용 담당자이고, GitHub는 `README.md`를 기본으로 보여준다.
- **코드는** 식별자와 주석을 영어로 쓰고, 첫 줄 역할 주석만 한국어와 영어 두 줄로 쓴다(CLAUDE.md 6절).
- **`CLAUDE.md`는 Claude Code가 읽는 원본이라 영어로 유지한다.** `CLAUDE.ko.md`는 사람을 위한 번역본이다.

## 2026-11-09 — 에이전트 팀 설정

- **에이전트 팀은 이 프로젝트에서만 켰다.** `.claude/settings.json`에 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`을 넣었다. 팀은 세션이 시작될 때만 구성되므로 Claude Code를 다시 시작해야 한다.
- **분할 화면은 tmux로 한다.** 사용자는 Apple Terminal을 쓰는데, 팀 분할 화면을 기본 지원하지 않는다. 그래서 Homebrew로 tmux 3.8을 설치하고 사용자 설정에 `teammateMode: "tmux"`를 넣었다. `~/.tmux.conf`에서 마우스를 켜고, 활성 pane 테두리를 초록색으로 강조하고, 각 pane 위쪽 테두리에 번호와 제목을 표시하고, 상태바를 초록색으로 바꿔 활성 pane을 보여주게 했다.
- **계획 승인은 메시지로 받는다.** 문서에 따르면 plan mode로 띄운 팀원이 계획을 마치면, 리드가 검토하지 않아도 Claude Code가 자동으로 승인한다. 실제로 검토하려면 팀원이 리드에게 계획을 보내고 명시적인 승인을 기다려야 한다(CLAUDE.md 11절).
- **Sonnet 팀원 4명이 서로 겹치지 않는 파일을 맡는다**(plan.ko.md "에이전트 팀" 참고). 문서와 커밋은 리드가 맡아 충돌을 막고 영어·한국어 쌍을 맞춘다.

## 2026-11-09 — 스캐폴드

- **Python 최소 버전은 3.9다**(`requires-python >=3.9`). 로컬 인터프리터가 3.9.6이기 때문이다. 모듈은 `from __future__ import annotations`를 쓰고, 런타임에 평가되는 곳에서는 `X | Y`, `list[str]` 대신 `Optional`, `List`를 쓴다. CI는 3.11에서 돌리고 ruff는 py39 기준으로 검사한다.
- **`Job`에 Notion 표에 없는 `country` 필드(소문자 ISO 코드)를 넣었다.** Simplify 목록은 여러 나라 공고가 섞여 있어서, 필터가 공고마다 국가를 알아야 지역의 `country`와 맞출 수 있다.
- **`Track`, `Source`는 값이 config 키와 같은 `str` 열거형이다.** 표시 이름(Intern / New Grad, Simplify / CanadaInternship / JSearch)은 모델이 아니라 Notion과 게시판 코드에서 붙인다.
- **`posted`, `collected`는 datetime이 아니라 date다.** Notion Date와 게시판은 날짜만 필요하다.
- **`requests`는 처음부터 의존성에 넣었다.** 수집기, Notion, Discord 모두 HTTP 요청을 보낸다.
- **로컬 셋업에는 새 pip가 필요하다.** 시스템 pip 21.2.4는 pyproject 기반 editable 설치를 못 하므로 `.venv` 안에서 pip를 먼저 올린다.

## 2026-11-09 — 수집기, 필터, 중복 병합

- **기본 브랜치가 `main`이 아니다.** SimplifyJobs 저장소는 `dev`, canada-internship은 `master`다. 각 수집 모듈에 `BRANCH` 상수로 둔다.
- **Simplify는 위치 문자열마다 국가를 판별한다.** 캐나다를 먼저 본다("Canada", "CAN", 주 약어). 미국은 주 약어, SF/NYC/LA, 주 이름, "United States"로 판별한다. "CA" 단독은 캐나다가 아니라 캘리포니아다. 두 나라에 걸친 공고는 나라마다 `Job` 하나씩 만들고, 캐나다·미국 위치가 없는 공고는 버린다.
- **canada-internship은 Tech 섹션 안에서 `<a href=` 링크가 있는 표 행만 파싱한다.** HTML 엔티티를 풀고 "NEW " 접두어를 뗀다. 형식이 바뀌면 예외 대신 0건이 나오고, main.py가 0건 경고를 보낸다.
- **제외 키워드는 단어 경계로 매칭한다**(`re.escape`, 대소문자 무시). "senior"가 "seniority"에 걸리지 않고, "sr."은 글자 그대로 매칭된다.
- **중복은 `job_id`가 같거나 회사 + 제목 + 국가가 같으면 합친다.** 먼저 나온 쪽을 남기며, 카테고리가 있는 Simplify를 먼저 넘긴다. canada-internship 링크는 대부분 LinkedIn이라 출처 간 병합은 주로 회사 + 제목에 기댄다.
- **실제 데이터 첫 dry run(2026-11-09)**: Simplify 5361건, canada-internship 645건 → 필터와 병합 후 캐나다 공고 842건.

## 2026-11-09 — Notion, Discord, main, collect.yml

- **Notion API는 `requests`로 직접 호출하고 `Notion-Version: 2022-06-28`로 고정한다.** 새 버전(2025-09-03 이후)은 데이터베이스를 "data source"로 옮겼다. Notion은 옛 버전을 계속 지원한다고 밝혔고, 확인할 수 있었던 엔드포인트는 옛 `/databases/{id}/query`다. 지원이 끝나면 다시 본다.
- **Notion 요청 사이에 약 0.35초를 쉬고, 429가 오면 `Retry-After`를 보고 한 번 재시도한다.**
- **출처는 지역마다가 아니라 실행마다 한 번만 가져온다.** 가져오기에 실패하면 로그를 남기고 0건으로 취급해 Discord 경고를 보내며, `main()`은 1을 반환한다.
- **Pages 배포는 `main`이 0으로 끝날 때만 돈다.** 일부만 수집된 보드가 공개 보드를 덮어쓰지 않게 하기 위해서다.
- **`DRY_RUN=1`은 수집과 보드 생성만 하고 Notion, Discord 호출은 모두 건너뛴다.** 그래서 비밀값 없이 돌릴 수 있다. 로컬 `.env`는 자동으로 읽지 않으므로(의존성 추가 없음) 셸에서 export한다.
- **cron은 UTC 11:17, 23:17이다.** Actions 혼잡을 피하려고 정각을 피했다.
- **JSearch는 아직 구현하지 않았다.** config에서 켜면 로그만 남긴다.
- 코드는 다 썼고 모킹한 테스트로 검증했다. "로컬 실행 확인"과 Actions 항목은 실제 Notion, Discord로 돌려 볼 때까지 열어 둔다.

## 2026-11-09 — 첫 실제 실행 (스모크 테스트)

- **실제 Notion DB와 Discord 웹훅으로 공고 3건만 넣는 스모크 테스트가 통과했다**(읽기, 쓰기, 전송). `main.py`가 아니라 scratchpad 스크립트로 돌렸으므로 체크리스트의 "로컬 실행 확인"은 아직 열어 둔다.
- **제외 키워드에 `language specialist`, `ai trainer`를 추가했다.** Simplify가 프리랜서 "AI Trainer / Language Specialist" 공고를 AI/ML/Data로 분류하고 있었고, 테스트 3건 중 2건이 이런 공고였다. 2026-11-09 데이터 기준으로 정확히 3건이 빠지고(843 → 840), 모두 그런 공고다. 사용자는 이 공고가 필요 없다고 했다.

## 2026-11-09 — 최신 공고 우선

- **사용자가 보는 모든 곳은 게시일 최신순으로 정렬하고, 날짜가 없는 공고는 맨 뒤에 둔다.** 공고가 올라오자마자 지원하는 게 유리하기 때문이다. 보드는 이미 그렇게 하고 있었고, 이제 Discord 요약도 그렇게 한다. 그래서 "+N more"로 잘릴 때 가장 오래된 공고가 잘리고 최신 공고는 잘리지 않는다.
- **Notion 보기 정렬은 직접 설정한다.** 우리가 쓰는 API 버전으로는 보기 정렬을 바꿀 수 없으므로, Notion 화면에서 DB 보기를 `Posted` 내림차순으로 정렬한다.
- **`posted`는 아직 날짜라서 같은 날 올라온 공고끼리는 시간순으로 정렬되지 않는다.** Simplify의 `date_posted`에는 정확한 시각이 있지만 canada-internship은 날짜만 준다. 사용자가 날짜 단위 정렬이면 충분하다고 정해서 `posted`는 날짜로 둔다.

## 2026-11-09 — 첫 Actions 실행

- **첫 `collect` 실행은 `configure-pages`에서 실패했다.** Pages가 아직 켜져 있지 않았기 때문이다. `main`은 이미 성공해서 Notion과 Discord 작업은 끝났고, 보드만 배포되지 않았다. Pages → Source를 GitHub Actions로 바꾼 뒤 새로 실행하자 모든 단계가 통과했고, 보드가 https://andychoi4495.github.io/jobHunter/ 에 공고 839건으로 올라갔다.
- **다시 실행해도 안전하다.** Notion 중복 제거가 이미 있는 `Job ID`를 건너뛰고, 새 공고가 0건이면 Discord는 아무것도 보내지 않는다.
- **후속 작업:** GitHub가 `checkout@v4`, `setup-python@v5`, `configure-pages@v5`가 지원 종료된 Node.js 20용이라고 경고한다(지금은 Node 24로 강제 실행된다). 나중에 메이저 버전을 올린다.

## 2026-11-09 — 필터 품질: 직무 키워드

- **문제:** 공고의 약 10%가 개발 직무가 아니었다(비즈니스/BI, 마케팅, 평가자, IT 지원, 하드웨어/FPGA). canada-internship의 "Tech" 섹션 범위가 넓고, Simplify의 AI/ML/Data 카테고리에 단기 외주 일도 섞여 있다.
- **두 단계로 거른다.** 제목에 `include_title_keywords`의 직무 단어가 하나는 있어야 하고, `exclude_title_keywords`에 걸리면 그래도 뺀다(제외가 우선이다). 둘 다 단어 단위로 대소문자 없이 매칭하므로, 단어 형태(engineer / engineering, 프랑스어 형태)는 하나하나 적었다.
- **사용자가 정한 범위:** 소프트웨어 개발, Data/AI/Research, QA/Test는 남긴다. IT/Network/Systems, Hardware/FPGA/Embedded, 비즈니스/BI, 마케팅/영업, 은행, 평가자는 뺀다.
- **넓은 단어 하나가 진짜 개발 직무까지 지우는 경우에는 제외어를 구문으로 쓴다.** `business`가 "Application Developer Co-op – Enterprise Technology & Business Management"를 지워서 `business analyst`, `business intelligence` 같은 구문으로 바꿨다. `sales`가 "Data Analyst Intern – Global Sales"를 지워서 `sales strategy`, `sales representative`로 바꿨다.
- **`engineer`만으로는 다른 분야 엔지니어링이 들어온다.** 그래서 mechatronics, automotive, power system, firmware, certification 등을 제외한다. Compiler, kernel, Linux, Forward Deployed 엔지니어는 그대로 통과한다.
- **`bi`도 제외한다**(나중에 추가). 약어라서 `business intelligence`에 걸리지 않았다. 2026-11-09 데이터 기준으로 정확히 2건이 빠진다. "BI/Data Analyst Intern"과 프랑스어 "Développeur BI" 코업이다(650 → 648).
- **보안 직무는 뺀다**(예: "Security Analyst Intern"). 사용자의 선택에 따라 `security`는 직무 단어에 넣지 않는다. 보안 *엔지니어링* 제목은 `engineer`로 계속 통과한다.
- **알고 있는 대가:** `fpga` 때문에 "FPGA Software Tool Developer Co-op"도 빠진다. 단순하게 두려고 감수한다.
- **2026-11-09 데이터 결과:** 캐나다 공고 838건 → 650건. 이미 Notion에 들어간 페이지는 이걸로 지워지지 않는다. 보드는 실행마다 새로 만들어지므로 저절로 반영된다.

## 2026-11-09 — JSearch

- **LinkedIn, Indeed를 직접 쓰지 않고 JSearch를 쓰는 이유:** 둘 다 공개 공고 검색 API가 없고, 스크래핑은 약관 위반이며 Actions 러너에서 막히고 공개 포트폴리오 저장소에서 보기에도 좋지 않다.
- **구현 전에 테스트 호출을 했다(8회).** 예전 `/search` 엔드포인트는 없어졌고(404, 차감 안 됨), `/search-v2`가 `data.jobs`를 준다. `employment_types=INTERN`은 믿을 수 없어서(결과 1건, 그것도 FULLTIME 표시) 쓰지 않는다. 검색어 6개, 3일 기준으로 결과가 적었고(검색어당 1~10건), 대부분 재게시 사이트(BeBee, Jobrapido, Jooble, JobLeads, LinkedIn 1건, Indeed 1건)를 거쳤으며, 회사로 바로 가는 링크는 없었다. Simplify, canada-internship에 없던 실제 신입 공고는 약 6건이었다. 사용자는 그래도 2주 시험 운영을 골랐다. 비용이 작고, 신입 공고를 일찍 보는 게 중요하기 때문이다.
- **일정:** 무료 한도가 월 200회라서 JSearch는 평일 하루 한 번, 토론토 시간 12시대에 돈다(사용자의 선택). 검색어 7개를 모두 쓰고 `date_posted=3days`로 월요일에 주말 공고까지 받는다. 월 최대 161회다. cron은 서머타임이 없는 UTC라서 16:05와 17:05 UTC를 둘 다 걸어 두고, `should_run`이 토론토 정오 시간대에 걸린 쪽만 고른다. 나머지 정오 실행은 무료 출처만 한 번 더 수집한다.
- **공개 보드에는 절대 올리지 않는다**(사용자의 선택). 유료 제3자 데이터라 재게시가 허용되지 않을 수 있다. `board.py`가 직접 JSearch 공고를 빼므로 어떤 호출 쪽에서도 새어 나갈 수 없다.
- **실패는 경고만 한다.** 한도 초과 429나 API 변경이 생기면 Discord 경고만 보내고 실행은 실패로 치지 않는다. JSearch는 보드에 영향을 줄 수 없기 때문이다. `JSEARCH_API_KEY`가 없을 때도 같게 처리한다.
- **`DRY_RUN`에서는 절대 부르지 않는다.** 로컬 테스트로 한도를 쓰지 않기 위해서다.
- **JSearch 공고는 중복 병합 전에 맨 뒤에 둔다.** 같은 공고가 Simplify나 canada-internship에도 있으면 그쪽의 (더 낫고 직접 연결되는) 링크가 남는다.

## 열린 질문

- 3단계(이력서 맞춤 작성)를 Claude API로 자동화할지, Muse가 Notion 페이지를 읽고 작성하도록 수동으로 맡길지 정하지 않았다.
- 캐나다 안에서 특정 도시(토론토, 밴쿠버 등)로 좁힐지 정하지 않았다. 현재는 캐나다 전체다.
