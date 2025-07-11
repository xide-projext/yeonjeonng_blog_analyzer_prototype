# Blog SEO Analyzer - 개발 TODO 목록

본 TODO 목록은 MDC 규칙과 프로젝트 요구사항에 따라 체계적으로 관리됩니다.

## 1. 프로젝트 초기화 및 환경 구축
- [x] 마이크로서비스 기반 디렉토리 구조 설계 및 생성
- [x] pyproject.toml, Dockerfile, docker-compose.yml, .gitignore 등 환경 파일 작성
- [x] PostgreSQL, Redis, Celery, Prometheus, Grafana 등 인프라 설정
- [x] 환경 변수 예시 파일(env.example) 작성
- [x] 데이터베이스 초기화 스크립트 작성

## 2. 공통 모듈 및 설정
- [x] 공통 설정(config.py) 및 데이터 모델(models.py) 정의

## 3. 크롤링 서비스
- [x] 플랫폼 자동 감지 및 적응형 크롤러 구현 (네이버, 티스토리, 워드프레스, 미디엄, 브런치)
- [x] Rate Limiting, User-Agent, 프록시 관리, robots.txt 준수
- [x] JavaScript 렌더링 지원 (Playwright)

## 4. SEO 분석 서비스
- [x] 키워드 밀도/배치/다양성 분석
- [x] 메타데이터 최적화(제목, 설명, Open Graph, Twitter Cards)
- [x] 헤딩 구조(H1~H6), 링크 분석, 이미지 최적화
- [x] 가독성 평가, 기술적 SEO(속도, 모바일, Core Web Vitals)

## 5. 자연어 처리(NLP) 서비스
- [ ] 한국어 형태소 분석 (KoNLPy, soynlp, Kiwi)
- [ ] 키워드 추출(TF-IDF, TextRank), 토픽 모델링(LDA, BERTopic)
- [ ] 감성 분석, 문서 유사도, 의미 네트워크 분석

## 6. 백엔드 API 서버
- [ ] FastAPI 기반 RESTful API 서버 구축
- [ ] OpenAPI/Swagger 문서 자동화
- [ ] 비동기 작업 큐(Celery) 연동
- [ ] 인증/인가(JWT, OAuth2, RBAC) 구현

## 7. 프론트엔드 대시보드
- [ ] React 18+ TypeScript 기반 대시보드 설계 및 개발
- [ ] Material-UI, Chart.js, D3.js, 워드클라우드, 네트워크 그래프 시각화
- [ ] 실시간 분석 상태(WebSocket), 반응형 디자인, PWA 지원

## 8. 테스트 및 품질 보증
- [ ] pytest, Jest 기반 단위/통합/E2E 테스트
- [ ] 코드 커버리지 80% 이상 달성
- [ ] SonarQube, Bandit 등 코드 품질/보안 검사

## 9. 문서화 및 오픈소스 정책
- [ ] README, CONTRIBUTING.md, API 문서, 개발자 가이드 작성
- [ ] MIT 라이선스, 코드 오브 컨덕트, 이슈/기여 템플릿

---

> **진행상황**: 체크박스(✓)로 관리하며, 세부 작업은 각 모듈별로 추가/수정될 수 있습니다. 