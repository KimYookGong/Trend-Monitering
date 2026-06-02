from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import json
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Anti-Gravity Real-time Trend API")

# 프론트엔드 연동을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 초기 키워드 풀 설정 (SSE 스트리밍을 통해 점진적으로 가중치를 부여)
KEYWORDS_POOL = [
    "Generative AI", "RAG Systems", "Agentic Workflows", 
    "Vector Database", "Multimodal Models", "DeepSeek", "LLM Ops"
]

async def trend_event_generator(request: Request):
    """
    SSE 스트림 이벤트 생성기
    클라이언트에 4초마다 갱신된 트렌드 랭킹과 시계열 차트 데이터를 푸시합니다.
    """
    # 초기 빈도수 딕셔너리 생성
    trends_counts = {kw: random.randint(50, 150) for kw in KEYWORDS_POOL}
    
    while True:
        # 클라이언트 연결 끊김 감지 시 세션 해제
        if await request.is_disconnected():
            logger.info("SSE client disconnected.")
            break
            
        # 1. 랜덤하게 키워드들의 언급 수치를 보정 (실시간 변동 시뮬레이션)
        for kw in trends_counts:
            # 200% 폭증 상황 연출을 위한 가중치 트리거 확률
            if random.random() < 0.15:
                trends_counts[kw] += random.randint(30, 80) # 폭증
            else:
                trends_counts[kw] += random.randint(-15, 15)
                
            trends_counts[kw] = max(10, trends_counts[kw]) # 최소 10 유지
            
        # 2. 언급량 기준으로 랭킹 재정렬
        sorted_trends = sorted(
            [{"keyword": kw, "count": count} for kw, count in trends_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )
        
        # 3. 실시간 시계열 차트에 바인딩할 데이터 포인트 생성
        current_time = asyncio.get_event_loop().time()
        time_str = json.dumps(current_time) # 가상의 타임스탬프 또는 포맷팅
        from datetime import datetime
        formatted_time = datetime.now().strftime("%H:%M:%S")
        
        chart_point = {
            "time": formatted_time,
            "count": sum(trends_counts.values()) // len(trends_counts) # 평균 활성도
        }
        
        # 4. 클라이언트 전송용 SSE 데이터 직렬화
        sse_payload = {
            "trends": sorted_trends[:5], # Top 5 키워드만 전달
            "chartPoint": chart_point
        }
        
        # SSE 규격(data: [JSON]\n\n)에 맞춰 yield
        yield f"data: {json.dumps(sse_payload)}\n\n"
        
        # 4초 대기
        await asyncio.sleep(4)

@app.get("/api/trends/stream")
async def get_trends_stream(request: Request):
    """
    실시간 트렌드 업데이트 SSE 엔드포인트
    """
    logger.info("New SSE Connection Initiated!")
    return StreamingResponse(
        trend_event_generator(request),
        media_type="text/event-stream"
    )

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Anti-Gravity Trend Server"}

if __name__ == "__main__":
    import uvicorn
    # 로컬 호스트의 8000 포트에서 구동
    uvicorn.run(app, host="0.0.0.0", port=8000)
