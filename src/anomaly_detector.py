import httpx
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
from datetime import datetime, timedelta

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 설정 변수 (실 사용시 환경 변수 또는 .env 파일에서 관리 권장)
SLACK_WEBHOOK_URL = ""  # 실제 Slack Webhook URL을 입력하십시오. (예: https://hooks.slack.com/services/...)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"
ALERT_RECIPIENT = "target_user@domain.com"

# 1. 비동기 슬랙 웹훅 알림 발송 함수
async def send_slack_alert(keyword: str, current_count: int, previous_count: int, rate: float):
    # 실제 연동 시 발송하려면 웹훅 URL이 유효해야 합니다.
    # 여기서는 예외 처리와 로깅을 갖춘 견고한 HTTP 비동기 발송 로직을 작성합니다.
    payload = {
        "text": f"🚨 *[AI 트렌드 경보] 이상 징후 감지!*",
        "attachments": [
            {
                "color": "#FF0000",
                "fields": [
                    {"title": "급상승 키워드", "value": f"`{keyword}`", "short": True},
                    {"title": "상승률", "value": f"*{rate:.1f}% 폭증* 📈", "short": True},
                    {"title": "직전 1시간 언급량", "value": f"{previous_count}회", "short": True},
                    {"title": "현재 1시간 언급량", "value": f"{current_count}회", "short": True}
                ],
                "footer": "Anti-Gravity Real-time Anomaly Detection System",
                "ts": int(datetime.utcnow().timestamp())
            }
        ]
    }
    
    logger.info(f"슬랙 웹훅 전송 시도 - 키워드: {keyword} ({rate:.1f}% 증가)")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(SLACK_WEBHOOK_URL, json=payload, timeout=5.0)
            if response.status_code == 200:
                logger.info("슬랙 경보 발송 완료!")
            else:
                logger.warning(f"슬랙 API 응답 오류 (테스트용 가상 웹훅 상태): {response.status_code}")
    except Exception as e:
        logger.error(f"슬랙 경보 발송 에러 (비네트워크 환경 모니터링 경고): {e}")

# 2. 비동기 이메일 알림 발송 함수
async def send_email_alert(keyword: str, current_count: int, previous_count: int, rate: float):
    # 블로킹되는 SMTP 전송을 별도의 스레드 풀에서 비동기로 실행하도록 처리
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_email_sync, keyword, current_count, previous_count, rate)

def _send_email_sync(keyword: str, current_count: int, previous_count: int, rate: float):
    logger.info(f"이메일 전송 시도 - 수신자: {ALERT_RECIPIENT}")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Anti-Gravity AI 트렌드] 🚨 '{keyword}' 키워드 {rate:.1f}% 급상승 이상 징후 경보"
    msg["From"] = SMTP_USERNAME
    msg["To"] = ALERT_RECIPIENT

    # HTML 메일 내용 구성
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
          <h2 style="color: #d9534f; border-bottom: 2px solid #d9534f; padding-bottom: 10px;">🚨 AI 트렌드 급상승 경보</h2>
          <p>안녕하세요, Anti-Gravity 분석 시스템에서 실시간으로 감지된 <b>이상 징후 키워드</b>를 안내해 드립니다.</p>
          <div style="background-color: #f9f9f9; padding: 15px; border-left: 5px solid #d9534f; margin: 20px 0;">
            <p style="margin: 5px 0;"><b>감지 키워드:</b> <span style="background-color: #ffeb3b; padding: 2px 5px; font-weight: bold;">{keyword}</span></p>
            <p style="margin: 5px 0;"><b>상승폭:</b> <span style="color: red; font-weight: bold;">+{rate:.1f}%</span></p>
            <p style="margin: 5px 0;"><b>수치 추이:</b> {previous_count}회 언급 &rarr; <b>{current_count}회 언급</b> (최근 1시간 기준)</p>
          </div>
          <p>해당 키워드의 소셜 및 미디어 급증 원인에 대해 모니터링 대시보드를 즉시 확인해보실 것을 권장합니다.</p>
          <p style="font-size: 12px; color: #777; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            본 메일은 시스템에 의해 자동 발송되는 메일입니다.
          </p>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html"))

    try:
        # SMTP 연결 (테스트 중에는 SMTP 실 계정 정보가 없으므로 pass/로그 처리로 견고하게 구성)
        if SMTP_USERNAME == "your_email@gmail.com":
            logger.info("[SMTP 가상 모드] 메일 계정이 기본값이므로 실제 이메일을 발송하지 않고 터미널에 로그를 남깁니다.")
            logger.info(f"== [이메일 본문 요약] '{keyword}'가 {rate:.1f}% 급상승! ==")
            return
            
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, ALERT_RECIPIENT, msg.as_string())
        logger.info("이메일 경보 발송 성공!")
    except Exception as e:
        logger.error(f"이메일 경보 발송 실패 (SMTP 구성 오류): {e}")

# 3. 이상 징후 실시간 감지 프로세스
async def check_anomaly_signals(realtime_db_feed: list):
    """
    실시간 데이터 파이프라인에서 전달받은 시간대별 빈도 분석 데이터를 기반으로
    전 시간 대비 200%(3배 이상) 급증한 키워드가 있는지 검사합니다.
    """
    logger.info("실시간 이상 징후 감지 스캔 시작...")
    
    for record in realtime_db_feed:
        keyword = record.get("keyword")
        prev_hour_count = record.get("prev_hour_count", 0)
        curr_hour_count = record.get("curr_hour_count", 0)
        
        if prev_hour_count == 0:
            continue  # 비교 대상이 없는 신규 유입 키워드는 스킵
            
        # 상승률 계산: ((현재 - 이전) / 이전) * 100
        increase_rate = ((curr_hour_count - prev_hour_count) / prev_hour_count) * 100
        
        # 200% 이상 증가 시 감지 (예: 10회 -> 30회 이상으로 폭증한 경우)
        if increase_rate >= 200.0:
            logger.warning(f"⚠️ 이상 징후 감지! 키워드: {keyword} (+{increase_rate:.1f}%)")
            
            # 슬랙 및 이메일 전송 태스크 비동기 백그라운드 구동
            asyncio.create_task(send_slack_alert(keyword, curr_hour_count, prev_hour_count, increase_rate))
            asyncio.create_task(send_email_alert(keyword, curr_hour_count, prev_hour_count, increase_rate))

# 데모 실행을 위한 메인 진입부
async def main():
    # 시뮬레이션용 데이터 피드
    # RAG 키워드가 10번 언급되다가 갑자기 32번 언급되는 상황 연출 (220% 증가)
    # fine-tuning 키워드는 15번에서 18번으로 정상 범위 유지 (20% 증가)
    mock_realtime_db_feed = [
        {"keyword": "RAG (Retrieval-Augmented Generation)", "prev_hour_count": 10, "curr_hour_count": 32},
        {"keyword": "Fine-Tuning", "prev_hour_count": 15, "curr_hour_count": 18},
        {"keyword": "DeepSeek", "prev_hour_count": 2, "curr_hour_count": 9} # 350% 증가
    ]
    
    await check_anomaly_signals(mock_realtime_db_feed)
    # 백그라운드 태스크가 끝나도록 잠시 대기
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
