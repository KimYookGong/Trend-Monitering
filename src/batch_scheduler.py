from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
import logging
import random
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# [Mock 데이터베이스 쿼리 함수]
# 실제 환경에서는 PostgreSQL이나 TimescaleDB에서 SQL로 지난 24시간 내 수집된 키워드와 이전 24시간의 키워드를 집계합니다.
# SELECT keyword, count(*) FROM keyword_logs WHERE created_at >= NOW() - INTERVAL '24 hours' GROUP BY keyword;
def fetch_keyword_counts_from_db(start_time: datetime, end_time: datetime) -> dict:
    # 데모를 위한 가상 키워드 빈도 생성
    base_keywords = {
        "Generative AI": 100, "LLM": 80, "RAG": 50, "Vector DB": 40, "Fine-Tuning": 30,
        "Agentic Workflow": 10, "Multimodal": 60, "Transformer": 70, "GPU Bottleneck": 5
    }
    
    # 시간에 따른 난수 변화 가미
    keywords_with_noise = {}
    for kw, count in base_keywords.items():
        # 급상승 테스트를 위해 특정 키워드에 가중치 폭발 발생
        noise = random.randint(-15, 15)
        if kw == "Agentic Workflow": # 오늘 갑자기 급상승하는 트렌드로 설정
            noise = random.randint(150, 200)
        elif kw == "GPU Bottleneck":
            noise = random.randint(30, 50)
            
        final_count = max(1, count + noise)
        keywords_with_noise[kw] = final_count
        
    return keywords_with_noise

# 급상승 키워드 연산 배치 로직
def compute_daily_rising_trends():
    logger.info("==========================================")
    logger.info("매일 자정 배치 스케줄러: 급상승 키워드 연산 시작")
    logger.info("==========================================")
    
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    
    # 1. 지난 24시간(오늘)의 키워드 빈도 추출
    today_counts = fetch_keyword_counts_from_db(yesterday, now)
    
    # 2. 그 전 24시간(어제)의 키워드 빈도 추출
    yesterday_counts = fetch_keyword_counts_from_db(two_days_ago, yesterday)
    
    rising_keywords = []
    
    # 3. 급상승률(%) 및 가중치 계산
    for keyword, today_cnt in today_counts.items():
        yesterday_cnt = yesterday_counts.get(keyword, 1) # Division by zero 방지
        
        # 언급량 증가폭 계산
        increase_ratio = (today_cnt - yesterday_cnt) / yesterday_cnt * 100
        
        rising_keywords.append({
            "keyword": keyword,
            "today_count": today_cnt,
            "yesterday_count": yesterday_cnt,
            "growth_rate": round(increase_ratio, 2)
        })
        
    # 4. 급상승률이 높은 순으로 정렬
    rising_keywords.sort(key=lambda x: x["growth_rate"], reverse=True)
    
    # 5. 분석 결과 데이터베이스 적재 (콘솔 및 가상 적재)
    logger.info(f"[배치 연산 완료] {now.strftime('%Y-%m-%d')} 기준 Top 5 급상승 트렌드:")
    for idx, item in enumerate(rising_keywords[:5], 1):
        logger.info(
            f"순위 {idx}: [{item['keyword']}] 언급량: {item['yesterday_count']} -> {item['today_count']} "
            f"({item['growth_rate']}% 증가)"
        )
        
    # 6. 주간/일간 트렌드 리포트 생성 및 파일 저장
    generate_markdown_report(now, rising_keywords[:5])

def generate_markdown_report(report_date: datetime, top_trends: list):
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    
    filename = f"{report_dir}/trend_report_{report_date.strftime('%Y%m%d')}.md"
    
    report_content = f"""# AI 트렌드 분석 일일 리포트 ({report_date.strftime('%Y-%m-%d')})

본 리포트는 지난 24시간 동안 수집된 AI 뉴스, 학술 논문, SNS 포스트의 키워드 빈도 급증을 기반으로 생성된 배치 분석 리포트입니다.

## 1. 오늘 가장 핫한 급상승 키워드 Top 5

| 순위 | 키워드 | 어제 언급량 | 오늘 언급량 | 급상승률 (Growth Rate) |
| :--- | :--- | :--- | :--- | :--- |
"""
    for idx, item in enumerate(top_trends, 1):
        report_content += f"| **{idx}** | `{item['keyword']}` | {item['yesterday_count']} | {item['today_count']} | **+{item['growth_rate']}%** |\n"
        
    report_content += f"""
## 2. 기술적 인사이트 요약
- **주요 감지 사항**: 오늘 가장 눈에 띄는 상승폭을 기록한 키워드는 `{top_trends[0]['keyword']}`(으)로, 전날 대비 **+{top_trends[0]['growth_rate']}%** 급성장했습니다.
- **분석 추천**: 해당 키워드를 중심으로 한 벡터 유사 검색 및 실시간 뉴스 스트리밍을 추적하여 신규 연구 주제 또는 비즈니스 기회 요소를 도출하십시오.

---
*본 리포트는 Anti-Gravity Trend Monitoring Batch Scheduler에 의해 매일 자정 자동 생성됩니다.*
"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    logger.info(f"트렌드 보고서 저장 완료: {os.path.abspath(filename)}")

# APScheduler를 통한 크론 작업 스케줄링 설정
def start_scheduler():
    scheduler = BlockingScheduler()
    
    # 1. 매일 자정 (00:00) 배치 스케줄러 등록
    scheduler.add_job(
        compute_daily_rising_trends, 
        'cron', 
        hour=0, 
        minute=0, 
        id='daily_rising_trends',
        misfire_grace_time=3600
    )
    
    # 2. 로컬 테스트를 위해 즉시 1회 가동 및 10초마다 반복하도록 설정하는 데모용 트리거 (선택적)
    logger.info("스케줄러 테스트용 즉시 실행 1회 동작 중...")
    compute_daily_rising_trends()
    
    logger.info("스케줄러 구동 중... (매일 자정에 연산 동작 예정)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("스케줄러가 중단되었습니다.")

if __name__ == "__main__":
    start_scheduler()
