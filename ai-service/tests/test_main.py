import pytest
from httpx import AsyncClient
from main import app, redis_client
import json
import asyncio

# 確保每個測試案例開始前清空 Redis
@pytest.fixture(autouse=True)
def setup_and_teardown_redis_for_tests():
    if redis_client:
        redis_client.flushdb()
    yield # 測試運行
    if redis_client:
        redis_client.flushdb()

@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "InsightForge AI Service 運行中！"}

@pytest.mark.asyncio
async def test_analyze_endpoint_sentiment_success():
    test_task_id = "test-sentiment-123"
    test_payload = {
        "task_id": test_task_id,
        "data": json.dumps({"text": "這是一個非常正面的測試語句，我很喜歡！"}),
        "task_type": "sentiment_analysis",
        "model_version": "v1.0",
        "webhook_url": "http://mock-laravel/api/analysis/result",
        "webhook_secret": "your_secret_key_here" # 這裡仍然使用預設值，之後手動修改
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/analyze", json=test_payload)
    
    assert response.status_code == 200
    assert "分析任務已接收並處理中" in response.json()["message"]
    assert response.json()["task_id"] == test_task_id

    # 稍微等待，讓異步回調有機會執行 (在實際測試中，通常會模擬回調或用更可靠的方式等待)
    await asyncio.sleep(3) 

    # 驗證 Redis 中任務狀態是否正確
    task_data = redis_client.hgetall(f"task:{test_task_id}")
    assert task_data["status"] == "completed"
    assert "result" in task_data
    result = json.loads(task_data["result"])
    assert result["sentiment"] == "Positive"
    assert redis_client.ttl(f"task:{test_task_id}") > 0 # 檢查 TTL 是否設定

@pytest.mark.asyncio
async def test_analyze_endpoint_ner_success():
    test_task_id = "test-ner-456"
    test_payload = {
        "task_id": test_task_id,
        "data": json.dumps({"text": "蘋果公司在台灣設有研發中心，張三是其員工。"}),
        "task_type": "named_entity_recognition",
        "model_version": "v1.0",
        "webhook_url": "http://mock-laravel/api/analysis/result",
        "webhook_secret": "your_secret_key_here" # 這裡仍然使用預設值，之後手動修改
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/analyze", json=test_payload)
    
    assert response.status_code == 200
    assert response.json()["task_id"] == test_task_id

    await asyncio.sleep(3) 

    task_data = redis_client.hgetall(f"task:{test_task_id}")
    assert task_data["status"] == "completed"
    result = json.loads(task_data["result"])
    assert any(ent["text"] == "蘋果" for ent in result["entities"])
    assert any(ent["text"] == "台灣" for ent in result["entities"])
    assert any(ent["text"] == "張三" for ent in result["entities"])

@pytest.mark.asyncio
async def test_analyze_endpoint_invalid_data():
    test_task_id = "test-invalid-789"
    test_payload = {
        "task_id": test_task_id,
        "data": "非JSON格式的資料", # 錯誤的資料格式
        "task_type": "sentiment_analysis",
        "model_version": "v1.0",
        "webhook_url": "http://mock-laravel/api/analysis/result"
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/analyze", json=test_payload)
    
    assert response.status_code == 200 # FastAPI 會返回 200，但內部處理失敗，並發送失敗回調
    assert response.json()["task_id"] == test_task_id

    await asyncio.sleep(3) 

    task_data = redis_client.hgetall(f"task:{test_task_id}")
    assert task_data["status"] == "failed"
    assert "error" in task_data
    assert "輸入數據或任務類型錯誤" in task_data["error"]

@pytest.mark.asyncio
async def test_get_result_endpoint_found():
    test_task_id = "test-get-111"
    redis_client.hmset(f"task:{test_task_id}", {
        "status": "completed",
        "result": json.dumps({"sentiment": "Positive"}),
        "task_type": "sentiment_analysis"
    })
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/result/{test_task_id}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["result"]["sentiment"] == "Positive"

@pytest.mark.asyncio
async def test_get_result_endpoint_not_found():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/result/non-existent-task")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "任務不存在或已過期"

