# Anti-Gravity AI 트렌드 실시간 모니터링 및 변화 감지형 UX 인프라

본 프로젝트는 실시간 데이터 수집 파이프라인, 크론 배치 스케줄러, 이상 징후 알림 트리거 및 SSE 기반의 실시간 순위 변동 감지 React UI 대시보드로 구성된 종합 트렌드 분석 시스템입니다.

---

## 1. 아키텍처 개요 및 데이터 흐름

```mermaid
graph TD
    RSS[arXiv, Tech News RSS] -->|실시간 파싱| Ingestion[pipeline.py]
    Ingestion -->|형태소 분석 kiwipiepy| NLP[명사 추출 & 임베딩]
    NLP -->|벡터 저장| Qdrant[(Qdrant Vector DB)]
    NLP -->|시계열 빈도 누적| TSDB[(PostgreSQL)]
    
    TSDB -->|매시간 모니터링| Anomaly[anomaly_detector.py]
    Anomaly -->|200% 폭증 감지 시| Alert[슬랙 웹훅 / 이메일 알림]
    
    TSDB -->|매일 자정 00:00| Batch[batch_scheduler.py]
    Batch -->|일일 리포트 생성| Report[Reports 마크다운 자동 생성]
    
    Backend[server.py - FastAPI] -->|Redis PubSub 대체| SSE[/api/trends/stream]
    SSE -->|실시간 스트림| FE[Dashboard.jsx - React / Framer Motion]
```

---

## 2. 프로젝트 디렉토리 및 파일 구성

```text
g:/내 드라이브/2. Antigravity/Trend Monitering/
│
├── README.md                           <- 본 문서 (시스템 구동 및 아키텍처 가이드)
│
└── src/
    ├── pipeline.py                    <- [1. 실시간 처리] RSS 파이프라인, 형태소 분석, 벡터 임베딩 및 적재
    ├── batch_scheduler.py             <- [2. 주기적 업데이트] 매일 자정 크론 기반 급상승 키워드 배치 분석 스크립트
    ├── anomaly_detector.py            <- [3. 알림/리포트] 200% 이상 징후 감지 및 슬랙/SMTP 이메일 경보 시스템
    ├── Dashboard.jsx                  <- [4. 변화 감지 UX] Framer Motion & Tailwind CSS 실시간 랭킹 애니메이션 React 컴포넌트
    └── server.py                      <- [통합 SSE 백엔드] 실시간 데이터 스트리밍(SSE) 및 REST API FastAPI 서버
```

---

## 3. 핵심 기능 설명 및 파일별 기술 스택

### 3.1 `pipeline.py` (실시간 수집 및 벡터 임베딩)
- **핵심 기술**: `kiwipiepy` (형태소 분석), `qdrant-client` (벡터 데이터베이스), `feedparser` (RSS 파싱)
- **작동**: 비동기 루프를 돌며 arXiv 등의 RSS 피드에서 최신 논문을 수집하고, 한국어 명사를 추출한 뒤 가상의 384차원 조밀 벡터(MiniLM 임베딩 모델 포맷)로 실시간 인코딩하여 벡터 데이터베이스에 고속 적재합니다.

### 3.2 `batch_scheduler.py` (매일 자정 배치 연산)
- **핵심 기술**: `APScheduler`
- **작동**: 시스템 내 백그라운드 크론탭 데몬이 작동하여 매일 자정(`00:00`)에 지난 24시간과 지지난 24시간의 키워드 빈도 데이터를 역산하고, 성장 가중치(Growth Rate)를 비교하여 1~5위 급상승 키워드 리포트 마크다운 파일(예: `reports/trend_report_20260602.md`)을 로컬 및 원격 저장소에 자동 저장합니다.

### 3.3 `anomaly_detector.py` (이상 징후 급증 경보)
- **핵심 기술**: `httpx` (비동기 HTTP 클라이언트), `smtplib` (SMTP 이메일 전송)
- **작동**: 매시간 단위로 쿼리한 실시간 피드 내에서 전 시간 대비 **200% 이상**의 기하급수적인 키워드 출현 빈도 증가가 발견되면, 이벤트 리스너를 발동하여 사전에 설정된 슬랙 채널(Slack Webhook) 및 이메일(MIME 구조)로 비동기식 경보 메시지를 일괄 자동 배포합니다.

### 3.4 `Dashboard.jsx` (실시간 변화 감지 UI)
- **핵심 기술**: `React`, `Framer Motion`, `Recharts`, `Tailwind CSS`, `lucide-react`
- **작동**:
  - `EventSource` API를 사용하여 백엔드의 SSE 엔드포인트 `/api/trends/stream`과 지속 연동을 수립합니다.
  - 데이터가 유입될 때마다 화면 리로드 없이 실시간 시계열 그래프가 부드러운 스플라인 차트로 업데이트됩니다.
  - **Framer Motion의 `layout` 애니메이션**을 통해 트렌드 랭킹 순위가 실시간 수치에 의해 실시간으로 스왑(Swap)될 때 카드가 튀거나 깜빡이지 않고 물리엔진처럼 미끄러지듯이 위아래로 재배열되어 극도로 매끄러운 '변화 감지 UX'를 사용자에게 제공합니다.

### 3.5 `server.py` (FastAPI SSE 엔드포인트 웹서버)
- **핵심 기술**: `FastAPI`, `uvicorn`
- **작동**: 백엔드와 프론트엔드의 중개 서버 역할을 담당합니다. 브라우저와 SSE 영속 채널을 맺어주며, 4초 간격으로 실시간으로 변하는 가상의 실시간 트렌드 시그널 데이터를 프론트엔드에 실시간 직렬화하여 밀어줍니다.

---

## 4. 로컬 구동 및 검증 방법

### 4.1 백엔드 구동 (FastAPI & Python 데몬)
1. 관련 의존성 패키지를 설치합니다:
   ```bash
   pip install fastapi uvicorn feedparser kiwipiepy qdrant-client apscheduler httpx
   ```
2. 통합 SSE API 서버를 작동합니다:
   ```bash
   python src/server.py
   ```
3. 실시간 RSS 임베딩 파이프라인 및 이상 징후 감지, 배치 스케줄러 스크립트를 독립 데몬으로 가동해 테스트할 수 있습니다:
   ```bash
   python src/pipeline.py
   python src/anomaly_detector.py
   python src/batch_scheduler.py
   ```

### 4.2 프론트엔드 연동 (React 컴포넌트)
1. 개발 중인 React 앱 디렉토리에 `Dashboard.jsx`를 마운트합니다.
2. `framer-motion`, `recharts`, `lucide-react` 라이브러리를 추가합니다:
   ```bash
   npm install framer-motion recharts lucide-react
   ```
3. 컴포넌트를 호출하면 로컬 백엔드 서버(Port 8000)로부터 실시간 데이터 스트림을 전송받아 화면이 실시간으로 변화하는 장관을 경험하실 수 있습니다. (백엔드가 오프라인 상태일 때는 컴포넌트 내에 탑재된 가상 시뮬레이터 엔진이 4초마다 자동 가동되어 화면 동작성을 즉시 검증할 수 있도록 설계되어 있습니다.)
