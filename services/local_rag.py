import os
import faiss
import numpy as np
import pickle
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from core.config import log

# 設定本地向量資料庫儲存路徑
VECTOR_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "local_rag_index.faiss")
METADATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "local_rag_metadata.pkl")

class LocalRAGService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalRAGService, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.index = None
            cls._instance.metadata = []
        return cls._instance

    def _ensure_model(self):
        if self.model is None:
            log("🤖 正在加載本地 Embedding 模型 (BAAI/bge-m3)...")
            self.model = SentenceTransformer('BAAI/bge-m3')
            log("✅ 模型載入完成")

    def _initialize_index(self, dimension: int):
        if self.index is None:
            if os.path.exists(VECTOR_DB_PATH):
                log(f"📚 正在從本地載入向量索引: {VECTOR_DB_PATH}")
                self.index = faiss.read_index(VECTOR_DB_PATH)
                with open(METADATA_PATH, 'rb') as f:
                    self.metadata = pickle.load(f)
            else:
                log("🆕 建立新的 FAISS 向量索引")
                self.index = faiss.IndexFlatL2(dimension)
                self.metadata = []

    def save(self):
        if self.index:
            faiss.write_index(self.index, VECTOR_DB_PATH)
            with open(METADATA_PATH, 'wb') as f:
                pickle.dump(self.metadata, f)
            log(f"💾 向量索引已儲存至: {VECTOR_DB_PATH}")

    async def add_documents(self, documents: List[str], metadatas: List[Dict] = None):
        """將文本片段加入向量索引。"""
        self._ensure_model()
        
        embeddings = self.model.encode(documents, convert_to_numpy=True)
        dimension = embeddings.shape[1]
        
        self._initialize_index(dimension)
        
        self.index.add(embeddings)
        
        if metadatas is None:
            metadatas = [{"text": doc} for doc in documents]
        else:
            for i, doc in enumerate(documents):
                if "text" not in metadatas[i]:
                    metadatas[i]["text"] = doc
                    
        self.metadata.extend(metadatas)
        self.save()
        log(f"➕ 已加入 {len(documents)} 個片段至 RAG 索引")

    async def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """進行語意搜尋。"""
        self._ensure_model()
        
        query_vector = self.model.encode([query], convert_to_numpy=True)
        dimension = query_vector.shape[1]
        
        self._initialize_index(dimension)
        
        if self.index.ntotal == 0:
            return []
            
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                results.append({
                    "metadata": self.metadata[idx],
                    "score": float(distances[0][i])
                })
        return results

    def export_knowledge(self) -> Optional[bytes]:
        """將 RAG 索引與元數據封裝成位元組流以便同步 (Hive Sync)。"""
        if self.index is None:
            return None
        try:
            faiss_bytes = faiss.serialize_index(self.index)
            payload = {
                "faiss_index": faiss_bytes,
                "metadata": self.metadata
            }
            return pickle.dumps(payload)
        except Exception as e:
            log(f"❌ [Hive Sync] Export failed: {e}")
            return None

    def import_knowledge(self, data_bytes: bytes, merge: bool = True):
        """匯入或同步外部知識。"""
        try:
            payload = pickle.loads(data_bytes)
            # 反序列化
            new_index = faiss.deserialize_index(payload["faiss_index"])
            new_metadata = payload["metadata"]
            
            if merge and self.index:
                # 簡單合併邏輯：提取新索引的所有向量並加入現有索引
                log("🐝 [Hive Sync] Merging incoming knowledge...")
                # 重新構建向量 (IndexFlatL2 適用)
                vectors = np.zeros((new_index.ntotal, new_index.d), dtype='float32')
                for i in range(new_index.ntotal):
                    vectors[i] = new_index.reconstruct(i)
                
                self.index.add(vectors)
                self.metadata.extend(new_metadata)
                self.save()
            else:
                self.index = new_index
                self.metadata = new_metadata
                self.save()
            log(f"✅ [Hive Sync] Imported {len(new_metadata)} fragments.")
            return True
        except Exception as e:
            log(f"❌ [Hive Sync] Import failed: {e}")
            return False

local_rag = LocalRAGService()
