# 체크리스트

[English](checklist.md) | **한국어**

## 0. 준비
- [x] git 저장소 초기화 (noreply 이메일 설정)
- [x] GitHub **공개** 저장소 생성, 첫 푸시
- [ ] 저장소 설정: 외부 기여자 PR의 Actions 실행에 승인 필요, Pages 소스를 GitHub Actions로 설정
- [x] Python 프로젝트 셋업 (pyproject.toml, 테스트 도구)
- [x] `.gitignore`에 `.env` 추가
- [x] Notion 통합(Integration) 생성, 토큰 발급
- [x] 캐나다용 Notion DB 생성 (plan.ko.md 속성 표 기준), 통합에 DB 공유
- [x] Discord 캐나다 알림 채널에 웹훅 생성
- [x] 검색 조건 확정 (인턴·신입 SWE, 캐나다 우선, 원격 무관)

## 1. MVP — 수집 + 알림
- [x] `config.yaml` 스키마와 로더 (tracks, regions, enabled/notify 플래그)
- [x] `Job` 모델 정의
- [x] Simplify 수집기 (listings.json → `Job`, active·visible·카테고리·국가 판별) + 테스트
- [x] canada-internship 수집기 (Tech 섹션 마크다운 표 파싱) + 테스트
- [x] 필터 (제외 키워드 등) + 테스트
- [x] 출처 간 중복 병합 (URL 정규화, 회사+제목) + 테스트
- [x] 수집 0건 등 출처 이상 시 Discord 경고
- [x] Notion 기존 `Job ID` 조회
- [x] Notion 새 공고 추가
- [x] Discord 요약 메시지 전송 (새 공고 0건이면 생략)
- [x] `main.py`로 전체 흐름 연결, 로컬 실행 확인
- [x] GitHub Actions 워크플로 (cron + 수동 실행), Secrets 등록
- [x] Actions에서 실제 실행 확인
- [ ] 1~2주 운영 후 검색어·제외어 조정

## 1.5 포트폴리오 — 공개 보드
- [x] `board.py`: publish 지역의 활성 공고 → `site/jobs.json` (개인 필드 없음) + 테스트
- [x] `site/` 정적 페이지: 목록, 트랙·도시·출처 필터, 검색, 신규 표시, 출처 표기
- [x] `collect.yml`에 Pages 배포 단계 추가
- [x] `ci.yml`: 테스트 + 린트
- [x] README: 문제 정의, 구조도, 보드 링크, 스크린샷, 실행 방법, 출처 표기, CI 배지

## JSearch 보조 출처 (원할 때)
- [ ] RapidAPI에서 JSearch 구독, API 키 발급, 무료 할당량 확인
- [ ] JSearch 수집기 + 테스트, config에서 활성화

## 미국 확장 (원할 때)
- [ ] 미국용 Notion DB, Discord 웹훅 생성
- [ ] `NOTION_DB_USA`, `DISCORD_WEBHOOK_USA` Secrets 등록
- [ ] `config.yaml`에서 usa `enabled`, `notify`를 true로 변경
- [ ] Simplify 목록의 미국 위치 판별 확인 (`SF`, `NYC`, `San Jose, CA` 같은 약칭 처리)

## 2. 지원 현황 관리
- [ ] Notion `상태`·`마감일` 속성 활용 방식 확정
- [ ] 마감 임박·후속 연락 리마인더 Discord 알림

## 3. 이력서 맞춤 작성
- [ ] 기본 이력서 보관 위치 결정
- [ ] 생성 트리거 방식 결정 (Notion 체크박스 등)
- [ ] Claude API로 맞춤 이력서·자기소개서 생성 후 Notion 페이지에 저장
