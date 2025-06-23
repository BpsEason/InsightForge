import asyncio
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MockAIModel:
    """
    模擬 AI 模型，用於測試和骨架搭建。
    在實際應用中，這裡會載入你的 ML 模型並執行推論。
    """
    def __init__(self, version: str = "v1.0"):
        self.version = version
        logger.info(f"MockAIModel {self.version} initialized. (This is a placeholder)")

    async def predict(self, data_payload: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """
        模擬根據任務類型執行 AI 推論。
        
        Args:
            data_payload (Dict[str, Any]): 包含原始輸入數據的字典。
                                            預期包含 'text' 鍵。
            task_type (str): 任務類型，例如 'sentiment_analysis', 'named_entity_recognition'。

        Returns:
            Dict[str, Any]: 模擬的分析結果。

        Raises:
            ValueError: 如果輸入數據格式不正確或任務類型不支持。
        """
        await asyncio.sleep(1) # 模擬模型推論的延遲

        text_data = data_payload.get('text', '')
        if not text_data or not isinstance(text_data, str):
            logger.error("Input data 'text' is missing or not a string.")
            raise ValueError("Input data must contain a 'text' field (string).")

        result = {}
        if task_type == 'sentiment_analysis':
            # 簡單的基於關鍵字的模擬情感分析
            if 'positive' in text_data.lower() or '好' in text_data or '棒' in text_data:
                sentiment = "Positive"
            elif 'negative' in text_data.lower() or '壞' in text_data or '差' in text_data:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"
            result = {"sentiment": sentiment, "score": round(abs(hash(text_data)) % 100 / 100, 2), "model_info": f"Sentiment Model {self.version}"}
        elif task_type == 'named_entity_recognition':
            # 簡單的基於關鍵字的模擬實體識別
            entities = []
            if '蘋果' in text_data:
                entities.append({"text": "蘋果", "type": "ORGANIZATION"})
            if '台灣' in text_data:
                entities.append({"text": "台灣", "type": "LOCATION"})
            if '張三' in text_data:
                entities.append({"text": "張三", "type": "PERSON"})
            result = {"entities": entities, "model_info": f"NER Model {self.version}"}
        else:
            logger.error(f"Unsupported task_type: {task_type}")
            raise ValueError(f"Unsupported task_type: {task_type}")
        
        logger.info(f"MockAIModel {self.version} processed task_type='{task_type}' for text='{text_data[:30]}...'")
        return result

# 可以創建一個工廠函數來獲取不同版本的模型
def get_model(version: str) -> MockAIModel:
    """
    根據版本獲取 AI 模型實例。在實際應用中，這裡會載入相應的模型檔案。
    """
    return MockAIModel(version)

