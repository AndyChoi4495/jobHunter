# jobHunter 계획

## 목표

혼자 쓰는 구직 자동화 도구를 만든다.

1. 채용 공고 수집 (LinkedIn, Indeed 등)
2. 새 공고 알림
3. 지원 현황 관리
4. 공고별 이력서·자기소개서 맞춤 작성

## 핵심 결정

| 항목 | 결정 |
|---|---|
| 사용자 | 본인 1인 (로그인 없음) |
| 언어 | Python |
| 공고 수집 | GitHub 공고 목록 저장소(SimplifyJobs, canada-internship) 우선. JSearch 집계 API는 선택적 보조 출처 |
| 저장소 겸 UI | Notion 데이터베이스 |
| 알림 | Discord 웹훅 |
| 실행 | GitHub Actions cron |
| MVP | 수집 + 알림 |
| 직무 | 소프트웨어 개발자 — 인턴(Co-op 포함), 신입(New Grad / Associate / Junior) 두 트랙 |
| 국가 | 지역별로 분리 운영. 캐나다는 활성, 미국은 설정만 두고 비활성 |
| 원격 여부 | 무관 (필터하지 않음) |
| 포트폴리오 | 공개 GitHub 저장소 + 읽기 전용 공개 공고 보드(GitHub Pages). 지원 현황은 Notion에만 두고 비공개 |

결정 이유는 `context-notes.md`에 정리한다.

## 구조

```
GitHub Actions (cron)
   └─ main.py
        1. config.yaml 로드
        2. enabled인 지역마다 반복
           a. 켜진 출처(sources/*)에서 트랙(인턴/신입)별 공고 수집
           b. filter.py → 지역(국가)·카테고리·제외어 필터
           c. 출처 간 중복 병합 (URL, 회사+제목 기준)
           d. notion_store.py → 지역의 Notion DB에서 기존 Job ID 조회, 새 공고만 추가
           e. notify가 true면 notify_discord.py → 지역의 Discord 웹훅으로 요약 전송
        3. publish가 true인 지역의 현재 활성 공고 → board.py → site/jobs.json
   └─ actions/deploy-pages → GitHub Pages에 site/ 배포
```

### 공개 공고 보드 (포트폴리오)

- **공개하는 것**은 코드 전체와, 수집해서 걸러낸 공고 목록이다. 공고마다 회사, 제목, 위치, 트랙, 게시일, 출처, 지원 링크를 보여준다.
- **공개하지 않는 것**은 지원 상태, 메모, 맞춤 이력서 같은 개인 정보다. 이런 정보는 Notion에만 있고, 보드는 Notion을 읽지 않는다. 보드 데이터를 수집 결과로만 만들기 때문에 실수로 개인 정보가 섞여 나갈 경로가 없다.
- **보드의 형태**는 빌드 도구 없는 정적 HTML과 JS 한 페이지다. 트랙, 도시, 출처 필터와 검색, 최근 7일 신규 표시를 넣는다.
- **배포**는 Actions가 실행될 때마다 `site/`를 Pages 아티팩트로 배포하는 방식이다. 저장소에 데이터를 커밋하지 않아 git 히스토리가 깨끗하게 유지된다.
- **원본 출처**를 보드와 README에 표기하고 링크한다. 소스 저장소 3곳 모두 라이선스가 명시되어 있지 않다.
- **외부인은 읽기만 할 수 있다.** 공개 저장소는 소유자만 푸시할 수 있고, 포크에서 온 PR은 Secrets에 접근하지 못한다. 저장소 설정에서 외부 PR의 Actions 실행에 승인을 요구하도록 한다.

### 포트폴리오 품질

- README에 문제 정의, 구조도, 보드 링크와 스크린샷, 실행 방법을 담는다.
- PR과 push마다 CI(테스트 + 린트)를 돌리고 배지를 단다.
- 타입 힌트와 출처별 파서 테스트(저장해 둔 샘플 데이터 사용)를 갖춘다.

### 지역(region) 분리

- 지역마다 **Notion DB와 Discord 웹훅을 따로** 둔다. 캐나다와 미국 공고가 섞이지 않는다.
- `enabled`(수집 여부)와 `notify`(알림 여부)를 지역별로 따로 켠다.
- 미국을 추가할 때는 미국용 Notion DB와 웹훅을 만들고 Secrets를 등록한 뒤 `enabled: true`, `notify: true`로 바꾸면 된다. 코드는 수정하지 않는다.

### config.yaml (초안)

```yaml
sources:
  simplify:
    enabled: true
    new_grad_repo: SimplifyJobs/New-Grad-Positions
    intern_repo: SimplifyJobs/Summer2027-Internships   # 시즌이 바뀌면 갱신
    categories: [Software, Software Engineering, AI/ML/Data]
  canada_internship:
    enabled: true            # 캐나다 지역에만 적용
  jsearch:
    enabled: false

tracks:
  intern:
    queries:                 # JSearch 전용
      - software developer intern
      - software engineer intern
      - software developer co-op
  new_grad:
    queries:
      - new grad software engineer
      - junior software developer
      - associate software engineer
      - entry level software developer

exclude_title_keywords: [senior, sr., staff, principal, lead, manager, director]

regions:
  canada:
    country: ca
    enabled: true
    notify: true
    publish: true            # 공개 보드에 포함
    notion_db_env: NOTION_DB_CANADA
    discord_webhook_env: DISCORD_WEBHOOK_CANADA
  usa:
    country: us
    enabled: false
    notify: false
    publish: false
    notion_db_env: NOTION_DB_USA
    discord_webhook_env: DISCORD_WEBHOOK_USA
```

- 비밀값은 config에 직접 쓰지 않는다. 환경변수 이름만 적는다.
- 검색어 목록은 초안이다. 실제 결과를 보고 조정한다.
- JSearch의 국가, 게시 기간, 고용 형태(INTERN), 경력 요건 파라미터 이름은 구현할 때 API 문서로 확인한다.

- 중복 제거는 Notion DB의 `Job ID` 속성을 기준으로 한다. 별도 상태 파일을 두지 않는다.
- `Job ID`는 정규화한 지원 URL로 만든다. 출처마다 ID 체계가 다르고 canada-internship은 쓸 만한 ID가 없기 때문이다. 같은 공고가 여러 출처에 있으면 URL이 같거나 회사+제목이 같을 때 하나로 합친다.

### 수집 출처

| 출처 | 형식 | 범위 | 트랙 구분 | 비고 |
|---|---|---|---|---|
| [SimplifyJobs/New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions) | `.github/scripts/listings.json` (JSON) | 전 세계 | 신입 | 구조화 데이터. `active`, `is_visible`, `category`, `locations`, `date_posted`(unix) 필드 |
| [SimplifyJobs/Summer2027-Internships](https://github.com/SimplifyJobs/Summer2027-Internships) | 동일 JSON | 전 세계 | 인턴 | `terms` 필드 추가. 저장소 이름에 연도가 들어 있어 매년 바뀜 |
| [Francklin9999/canada-internship](https://github.com/Francklin9999/canada-internship) `INTERNSHIPS.md` | 마크다운 표 | 캐나다만 | 인턴 | "Tech internships" 섹션만 사용. 링크 대부분 LinkedIn |
| 같은 저장소 `NEW_GRAD.md` | 마크다운 표 | 캐나다만 | 신입 | "Tech new-grad roles" 섹션만 사용 |
| JSearch API (선택) | REST JSON | 국가 지정 | 검색어로 구분 | 기본 비활성. 위 목록이 놓치는 공고 보완용 |

- 모두 `raw.githubusercontent.com`에서 받는다. API 키나 할당량이 필요 없다.
- Simplify 목록은 `category`가 Software, AI/ML/Data인 공고만 남기고, `locations`로 국가를 판별한다.
- canada-internship은 사람이 읽는 마크다운이라 형식이 바뀌면 파서가 깨질 수 있다. 파싱 결과가 0건이면 알림 대신 경고를 보낸다.
- Meta Muse는 자체 Notion 커넥터로 같은 DB를 읽는다. 공고 검색·요약·작성 보조용이며 코드 연동은 없다.
- 수집 출처는 `sources/` 아래 모듈로 분리한다. 나중에 출처를 추가하기 쉽게 하기 위해서다.

### 디렉터리 (초안)

```
jobHunter/
├─ config.yaml              # 검색 키워드, 지역, 제외어
├─ src/jobhunter/
│  ├─ main.py
│  ├─ config.py
│  ├─ models.py             # Job 데이터 클래스
│  ├─ filter.py
│  ├─ sources/
│  │  ├─ simplify.py        # SimplifyJobs listings.json
│  │  ├─ canada_internship.py  # Francklin9999 마크다운 표
│  │  └─ jsearch.py         # 선택
│  ├─ dedupe.py
│  ├─ notion_store.py
│  ├─ notify_discord.py
│  └─ board.py              # 공개 보드용 jobs.json 생성
├─ site/                    # 공개 보드 (index.html, app.js, style.css)
├─ tests/
│  └─ fixtures/             # 출처별 샘플 데이터
└─ .github/workflows/
   ├─ collect.yml           # cron: 수집 → Notion → Discord → Pages 배포
   └─ ci.yml                # PR·push: 테스트 + 린트
```

### Notion DB 속성 (초안)

| 속성 | 타입 | 비고 |
|---|---|---|
| 제목 | Title | 직무명 |
| 회사 | Text | |
| 위치 | Text | |
| 원격 | Checkbox | |
| 트랙 | Select | Intern / New Grad |
| 출처 | Select | Simplify / CanadaInternship / JSearch |
| 카테고리 | Select | Software / AI/ML/Data 등 (Simplify 기준) |
| 링크 | URL | 지원 링크 |
| Job ID | Text | 중복 제거 키 |
| 게시일 | Date | |
| 수집일 | Date | |
| 상태 | Select | 2단계부터 사용. 신규 → 관심 → 지원 → 서류 → 면접 → 결과 |

### 비밀값 (GitHub Secrets)

- `JSEARCH_API_KEY` (RapidAPI, JSearch를 켤 때만)
- `NOTION_TOKEN`
- `NOTION_DB_CANADA`, `DISCORD_WEBHOOK_CANADA`
- `NOTION_DB_USA`, `DISCORD_WEBHOOK_USA` (미국 활성화 시)
- `ANTHROPIC_API_KEY` (3단계부터)

로컬에서는 `.env`로 관리하고 git에 올리지 않는다.

## 단계

### 1단계 — MVP: 수집 + 알림
조건에 맞는 새 공고가 하루 1~2회 Notion에 쌓이고, Discord로 요약 알림이 온다.

### 2단계 — 지원 현황 관리
Notion `상태` 속성으로 지원 단계를 관리한다. 마감일과 후속 연락 리마인더를 Discord로 보낸다.

### 3단계 — 이력서·자기소개서 맞춤 작성
기본 이력서를 보관해 두고, 공고를 선택하면 Claude API로 맞춤본을 생성해 해당 Notion 페이지에 저장한다.

## 리스크

- **공개 보드의 데이터 재배포**: 소스 저장소에 라이선스가 없다. 출처를 표기하고 원문 링크로 연결하며, 원본 파일을 통째로 다시 배포하지 않고 걸러낸 일부만 보여준다. 출처 측에서 문제를 제기하면 해당 출처를 보드에서 빼는 플래그를 둔다.
- **GitHub 목록 의존성**: 커뮤니티가 관리하는 저장소라 갱신이 멈추거나 형식이 바뀔 수 있다. 특히 canada-internship은 규모가 작은 개인 저장소다. 출처별 수집 건수를 로그로 남겨 이상을 빨리 알아챈다.
- **인턴 저장소 시즌 교체**: Simplify 인턴 저장소는 `Summer2027`처럼 연도별로 새로 만들어진다. 시즌이 바뀌면 config의 저장소 이름을 갱신해야 한다.
- **JSearch 무료 할당량** (켤 경우): 월 요청 수가 제한되어 있다. 요청 수는 대략 `검색어 수 × 활성 지역 수 × 하루 실행 횟수 × 30`이다. 캐나다만 켜도 검색어 7개 × 하루 2회면 월 약 420회다. 한도를 확인한 뒤 검색어 수와 실행 주기를 맞추고, 미국을 켜면 두 배가 된다는 점을 고려한다.
- **공고 품질**: 집계 API가 원본 공고를 누락하거나 늦게 반영할 수 있다.
- **Notion API 속도 제한**: 초당 약 3회 요청으로 제한되므로 대량 추가 시 간격을 둔다.
- **GitHub Actions cron**: UTC 기준이고 실행이 몇 분 지연될 수 있다.
