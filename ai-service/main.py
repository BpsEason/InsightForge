import os
import json
import redis
import requests
import hmac
import hashlib
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加載環境變數
load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
LARAVEL_WEBHOOK_URL = os.getenv('LARAVEL_WEBHOOK_URL')
LARAVEL_WEBHOOK_SECRET = os.getenv('LARAVEL_WEBHOOK_SECRET')
TASK_PROCESSING_TIMEOUT = int(os.getenv('TASK_PROCESSING_TIMEOUT', 60)) # seconds

# Redis 客戶端
try:
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    redis_client.ping()
    logger.info(f"成功連接到 Redis: {REDIS_HOST}:{REDIS_PORT}")
except redis.exceptions.ConnectionError as e:
    logger.error(f"無法連接到 Redis: {e}")
    redis_client = None # 設置為 None，讓應用程式知道 Redis 不可用

app = FastAPI(
    title="InsightForge AI Service API",
    description="提供 AI 驅動的資料分析任務處理服務。",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- 模擬 AI 模型推論邏輯 ---
# 實際應用中，這裡會載入你的 ML 模型
class MockAIModel:
    def __init__(self, version: str):
        self.version = version
        logger.info(f"Mock AI Model {self.version} initialized.")

    async def predict(self, data_payload: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        await asyncio.sleep(2) # 模擬模型推論時間

        text_data = data_payload.get('text', '')
        if not text_data:
            raise ValueError("Input data 'text' is missing.")

        if task_type == 'sentiment_analysis':
            # 簡單的模擬情感分析
            if 'positive' in text_data.lower() or '好' in text_data:
                sentiment = "Positive"
            elif 'negative' in text_data.lower() or '壞' in text_data:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"
            return {"sentiment": sentiment, "score": 0.95, "model_info": f"Sentiment Model {self.version}"}
        elif task_type == 'named_entity_recognition':
            # 簡單的模擬實體識別
            entities = []
            if '蘋果' in text_data:
                entities.append({"entity": "蘋果", "type": "ORGANIZATION"})
            if '台灣' in text_data:
                entities.append({"entity": "台灣", "type": "LOCATION"})
            return {"entities": entities, "model_info": f"NER Model {self.version}"}
        else:
            raise ValueError(f"Unsupported task_type: {task_type}")

# 全局模型實例 (可根據實際需求調整為多版本管理)
# model_instances = {
#     "v1.0": MockAIModel("v1.0"),
#     "v1.1": MockAIModel("v1.1")
# }

# 為了簡化，這裡只使用一個 MockAIModel
mock_model = MockAIModel("v1.0")

# --- API 請求與響應模型 ---
class AnalyzeRequest(BaseModel):
    task_id: str = Field(..., description="來自 Laravel 的唯一任務 ID")
    data: str = Field(..., description="JSON 格式的輸入數據，例如 {\"text\": \"你的文本\"}")
    task_type: str = Field(..., description="分析任務類型，例如 'sentiment_analysis', 'named_entity_recognition'")
    model_version: str = Field("v1.0", description="指定使用的模型版本，例如 'v1.0'")
    webhook_url: str = Field(..., description="Laravel 用於接收結果回調的 URL")
    webhook_secret: str = Field(None, description="Webhook 回調的共享密鑰") # 可選，但推薦用於驗證

class AnalyzeResponse(BaseModel):
    message: str = Field(..., description="服務處理訊息")
    task_id: str = Field(..., description="處理中的任務 ID")

class WebhookCallbackPayload(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    model_version: Optional[str] = None

# --- 輔助函數：回調 Laravel ---
async def callback_to_laravel(payload: WebhookCallbackPayload):
    if not LARAVEL_WEBHOOK_URL:
        logger.error("LARAVEL_WEBHOOK_URL 未設置，無法回調 Laravel。")
        return

    json_payload = payload.model_dump_json()
    headers = {'Content-Type': 'application/json'}

    if LARAVEL_WEBHOOK_SECRET:
        signature = hmac.new(
            LARAVEL_WEBHOOK_SECRET.encode('utf-8'),
            json_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        headers['X-Webhook-Signature'] = signature
        logger.info(f"生成 Webhook 簽名: {signature}")

    try:
        # 使用 asyncio.to_thread 執行同步的 requests 呼叫，避免阻塞 ASGI
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(LARAVEL_WEBHOOK_URL, data=json_payload, headers=headers, timeout=10)
        )
        response.raise_for_status()
        logger.info(f"成功回調 Laravel for task {payload.task_id}. Response: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"回調 Laravel 失敗 for task {payload.task_id}: {e}")
    except Exception as e:
        logger.error(f"回調 Laravel 時發生未知錯誤 for task {payload.task_id}: {e}")

# --- API 端點 ---
@app.get("/", summary="服務健康檢查")
async def root():
    """
    檢查 AI 服務是否正常運行。
    """
    return {"message": "InsightForge AI Service 運行中！"}

@app.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK, summary="處理 AI 分析任務")
async def analyze_task(request: AnalyzeRequest):
    """
    接收來自 Laravel 的分析任務，執行 AI 模型推論，並將結果存入 Redis 和回調 Laravel。
    """
    task_id = request.task_id
    data_str = request.data
    task_type = request.task_type
    model_version = request.model_version

    if redis_client is None:
        logger.error("Redis 客戶端未初始化。")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI 服務內部錯誤: Redis 不可用"
        )

    # 將任務狀態存入 Redis
    redis_client.hmset(f"task:{task_id}", {
        "status": "processing",
        "task_type": task_type,
        "model_version": model_version,
        "data_payload": data_str # 存儲原始數據
    })
    redis_client.expire(f"task:{task_id}", TASK_PROCESSING_TIMEOUT) # 設置過期時間

    logger.info(f"接收到任務: {task_id}, 類型: {task_type}, 模型: {model_version}")

    result_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    callback_status: str = "failed"

    try:
        data_json = json.loads(data_str)
        
        # 獲取模型實例 (這裡簡化為單一 mock_model)
        # model = model_instances.get(model_version) # 如果有多版本
        # if not model:
        #     raise ValueError(f"不支持的模型版本: {model_version}")

        # 執行模型推論
        ai_result = await mock_model.predict(data_json, task_type)
        result_payload = ai_result
        callback_status = "completed"

        redis_client.hmset(f"task:{task_id}", {
            "status": callback_status,
            "result": json.dumps(result_payload)
        })
        logger.info(f"任務 {task_id} 處理成功。")

    except ValueError as e:
        error_message = f"輸入數據或任務類型錯誤: {e}"
        logger.error(f"任務 {task_id} 處理失敗: {error_message}")
        redis_client.hmset(f"task:{task_id}", {
            "status": callback_status,
            "error": error_message
        })
    except Exception as e:
        error_message = f"AI 模型處理錯誤: {e}"
        logger.error(f"任務 {task_id} 處理失敗: {error_message}", exc_info=True)
        redis_client.hmset(f"task:{task_id}", {
            "status": callback_status,
            "error": error_message
        })
    finally:
        # 異步回調 Laravel
        callback_data = WebhookCallbackPayload(
            task_id=task_id,
            status=callback_status,
            result=result_payload,
            error_message=error_message,
            model_version=model_version
        )
        asyncio.create_task(callback_to_laravel(callback_data))

    return AnalyzeResponse(
        message=f"分析任務已接收並處理中，結果將透過Webhook回調: {LARAVEL_WEBHOOK_URL}",
        task_id=task_id
    )

@app.get("/result/{task_id}", summary="查詢指定任務的分析結果")
async def get_task_result(task_id: str):
    """
    從 Redis 查詢指定任務的當前狀態和結果。
    """
    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI 服務內部錯誤: Redis 不可用"
        )

    task_data = redis_client.hgetall(f"task:{task_id}")
    if not task_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任務不存在或已過期")

    # 解析結果
    response_data = {k: v for k, v in task_data.items()}
    if 'data_payload' in response_data:
        response_data['data_payload'] = json.loads(response_data['data_payload'])
    if 'result' in response_data and response_data['result']:
        response_data['result'] = json.loads(response_data['result'])
    if 'error' in response_data and response_data['error']:
        response_data['error'] = response_data['error']

    return response_data
