import asyncio
import logging
import feedparser
from datetime import datetime
from kiwipiepy import Kiwi
import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 형태소 분석기 초기화
kiwi = Kiwi()

# 데이터베이스 및 벡터 DB 설정 (로컬 Mocking 또는 실제 연결)
# 여기서는 데모를 위해 Qdrant 인메모리 DB를 사용합니다.
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
try:
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    # 컬렉션이 없으면 생성
    collection_name = "ai_trends"
    if not qdrant_client.has_collection(collection_name):
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE) # 384차원 (MiniLM)
        )
except Exception as e:
    logger.warning(f"Qdrant 실시간 연결 실패 (인메모리 클라이언트로 대체): {e}")
    qdrant_client = QdrantClient(":memory:")
    qdrant_client.create_collection(
        collection_name="ai_trends",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

# 한국어 텍스트 명사 추출기 (형태소 분석)
def extract_nouns(text: str) -> list:
    if not text:
        return []
    # 형태소 분석 실행 (명사만 추출: NNG-일반명사, NNP-고유명사)
    tokens = kiwi.tokenize(text)
    nouns = [t.form for t in tokens if t.tag in ("NNG", "NNP") and len(t.form) > 1]
    return list(set(nouns))

# 임베딩 생성 함수 (MiniLM API 또는 Local SentenceTransformer 모사)
# 여기서는 OpenAI 임베딩 또는 로컬 경량 임베딩 서버로 비동기 호출을 처리하는 방식을 씁니다.
async def get_embedding(text: str) -> list:
    # 프로덕션에서는 OpenAI text-embedding-3-small(1536차원) 등을 활용합니다.
    # 본 예제에서는 비동기 HTTP 요청을 통해 가상의 Embedding API를 호출하거나 로컬 모델을 구동하는 구조를 보입니다.
    # 데모를 위해 384차원의 난수 벡터를 생성하여 반환합니다 (실 사용 시 OpenAI/HuggingFace API 대체 가능).
    import random
    random.seed(hash(text))
    mock_vector = [random.uniform(-0.1, 0.1) for _ in range(384)]
    
    # 만약 허깅페이스 임베딩 서버 API가 있다면 아래와 같이 호출 가능:
    # async with httpx.AsyncClient() as client:
    #     response = await client.post("http://localhost:8000/embed", json={"text": text})
    #     return response.json()["embedding"]
    
    return mock_vector

# 단일 뉴스/논문 아이템 파이프라인 처리
async def process_item(item: dict):
    title = item.get("title", "")
    summary = item.get("summary", "")
    link = item.get("link", "")
    published_str = item.get("published", "")
    
    full_text = f"{title}. {summary}"
    logger.info(f"수집된 데이터 처리 중: {title[:30]}...")

    # 1. 형태소 분석을 통한 핵심 키워드 추출
    keywords = extract_nouns(full_text)
    
    # 2. 임베딩 생성 (벡터화)
    embedding = await get_embedding(full_text)
    
    # 3. Vector DB 적재
    point_id = hash(link) & 0xffffffffffffffff  # 링크 기반 64비트 정수 ID 생성
    try:
        qdrant_client.upsert(
            collection_name="ai_trends",
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "keywords": keywords,
                        "published_at": published_str,
                        "processed_at": datetime.utcnow().isoformat()
                    }
                )
            ]
        )
        logger.info(f"Vector DB 적재 성공 - ID: {point_id}")
    except Exception as e:
        logger.error(f"Vector DB 적재 에러: {e}")
        
    # 4. 실시간 Pub/Sub 시스템 연동 (Redis용 이벤트 전송)
    # 아래는 Redis가 설치되어 있다고 가정하고 실시간 이벤트를 전송하는 목업
    # r.publish('ai_trends_channel', json.dumps({"title": title, "keywords": keywords}))

# RSS 피드 모니터링 데몬
async def monitor_rss(feed_url: str, interval: int = 60):
    logger.info(f"RSS 모니터링 데몬 시작: {feed_url}")
    seen_links = set()
    
    while True:
        try:
            # 비동기로 RSS 피드 파싱
            feed = feedparser.parse(feed_url)
            new_entries = []
            
            for entry in feed.entries:
                if entry.link not in seen_links:
                    seen_links.add(entry.link)
                    new_entries.append({
                        "title": entry.title,
                        "summary": getattr(entry, "summary", ""),
                        "link": entry.link,
                        "published": getattr(entry, "published", datetime.utcnow().isoformat())
                    })
            
            # 신규 데이터가 있으면 동시성있게 비동기 파이프라인 처리
            if new_entries:
                logger.info(f"새로운 피드 아이템 {len(new_entries)}개 감지!")
                tasks = [process_item(item) for item in new_entries]
                await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f"RSS 피드 모니터링 중 에러 발생: {e}")
            
        await asyncio.sleep(interval)

if __name__ == "__main__":
    # arXiv AI RSS 피드 주소 예시
    ARXIV_AI_FEED = "http://export.arxiv.org/rss/cs.AI"
    asyncio.run(monitor_rss(ARXIV_AI_FEED, interval=10))
