---
category: RAG最佳实践
priority: optional
updated: 2026-05-30
---

# 多模态 RAG

## 概述

多模态 RAG 扩展了传统文本 RAG 的能力，支持图片、表格、代码等多种数据类型的检索与生成。本规范涵盖图片检索（CLIP embedding）、表格检索（结构化抽取）和代码检索（AST 感知分块）的最佳实践。

## 核心规则

### 🔴 必须遵守 (MUST)

1. **每种模态必须有专用的处理 pipeline**
   - 不要试图用文本 embedding 处理图片或表格
   - 每种模态的信息抽取策略独立设计

2. **多模态结果必须统一为可消费格式**
   - 图片：生成文字描述后存入向量库
   - 表格：转为结构化 Markdown 或 JSON
   - 代码：保留 AST 元数据

### 🟡 强烈建议 (SHOULD)

1. **图片检索策略**
   - 方案 A：CLIP embedding（图文双编码器）
   - 方案 B：图片描述生成（图→文→检索）
   - 方案 B 更加成熟，适合大多数场景

2. **表格检索策略**
   - 使用 Table Transformer 进行表格结构识别
   - 表格上下文保留：表头、表注、关联段落

3. **代码检索策略**
   - AST 感知分块，保持函数/类完整
   - 保留代码的调用关系和依赖信息

### 🟢 可选建议 (MAY)

1. **多模态融合**
   - 为不同模态分配权重，融合排序
   - 根据查询意图自动选择主导模态

2. **多模态生成**
   - 检索到的图片作为多模态 LLM 的输入
   - 检索到的代码直接运行验证

## 正确示例

```python
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class Modality(Enum):
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    CODE = "code"


@dataclass
class MultiModalDocument:
    modality: Modality
    content: str           # 文本内容或代码
    embedding: List[float] = None
    metadata: dict = None
    
    # 模态特有字段
    image_path: str = ""           # 图片路径
    image_caption: str = ""        # 图片描述
    table_structure: dict = None   # 表格结构化数据
    ast_info: dict = None          # 代码 AST 信息


class ImageRetriever:
    """图片检索器 — 使用图片描述 + 文本检索"""
    
    def __init__(self, vision_llm_client, vector_store):
        self.vision_llm = vision_llm_client
        self.vector_store = vector_store
    
    async def index_image(self, image_path: str) -> MultiModalDocument:
        """索引图片：先生成描述，再存入向量库"""
        caption = await self._generate_caption(image_path)
        
        doc = MultiModalDocument(
            modality=Modality.IMAGE,
            content=caption,
            image_path=image_path,
            image_caption=caption,
            metadata={"type": "image", "path": image_path},
        )
        
        # 使用描述文本生成 embedding
        doc.embedding = await self._embed_text(caption)
        await self.vector_store.insert(doc)
        return doc
    
    async def _generate_caption(self, image_path: str) -> str:
        """使用视觉模型生成图片描述"""
        prompt = "请用中文详细描述这张图片的内容，包括主要对象、场景、文字信息等。"
        
        # 调用多模态 LLM
        response = await self.vision_llm.generate(
            prompt=prompt,
            images=[image_path],
        )
        return response
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[MultiModalDocument]:
        """通过文本查询检索相关图片"""
        query_embedding = await self._embed_text(query)
        results = await self.vector_store.similarity_search(
            query_embedding, top_k, filter={"type": "image"}
        )
        return results


class TableRetriever:
    """表格检索器 — 结构化抽取 + 文本检索"""
    
    async def index_table(self, table_html: str, source: str) -> MultiModalDocument:
        """索引表格：转为结构化数据"""
        structure = await self._extract_table_structure(table_html)
        
        # 生成可检索的文本表示
        text_repr = self._table_to_text(structure)
        
        doc = MultiModalDocument(
            modality=Modality.TABLE,
            content=text_repr,
            table_structure=structure,
            metadata={"source": source, "type": "table"},
        )
        
        doc.embedding = await self._embed_text(text_repr)
        await self.vector_store.insert(doc)
        return doc
    
    def _table_to_text(self, structure: dict) -> str:
        """将表格转为文本表示"""
        headers = structure.get("headers", [])
        rows = structure.get("rows", [])
        
        text_parts = []
        text_parts.append("表格数据:")
        text_parts.append("列名: " + " | ".join(headers))
        for row in rows[:5]:  # 前 5 行作为摘要
            text_parts.append(" | ".join(str(cell) for cell in row))
        text_parts.append(f"共 {len(rows)} 行数据")
        
        return "\n".join(text_parts)
    
    @staticmethod
    async def _extract_table_structure(table_html: str) -> dict:
        """提取表格结构（可使用 Table Transformer 等模型）"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(table_html, "html.parser")
        headers = [th.get_text(strip=True) for th in soup.find_all("th")]
        rows = []
        for tr in soup.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                rows.append(cells)
        
        return {"headers": headers, "rows": rows}


class CodeRetriever:
    """代码检索器"""
    
    async def index_code(self, code: str, language: str, 
                          source: str) -> MultiModalDocument:
        """索引代码：AST 分析 + 分块"""
        import ast
        
        tree = ast.parse(code)
        
        # 提取函数和类定义
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "end_lineno": node.end_lineno,
                    "docstring": ast.get_docstring(node) or "",
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "methods": [
                        n.name for n in node.body 
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ],
                })
        
        # 生成可检索的摘要文本
        summary_parts = [
            f"文件: {source}",
            f"语言: {language}",
            f"函数: {', '.join(f['name'] for f in functions)}",
            f"类: {', '.join(c['name'] for c in classes)}",
        ]
        if functions:
            summary_parts.append("---")
            for f in functions:
                summary_parts.append(f"函数 {f['name']} (行 {f['lineno']}-{f['end_lineno']})")
                if f['docstring']:
                    summary_parts.append(f"  文档: {f['docstring'][:100]}")
        
        text_repr = "\n".join(summary_parts)
        
        doc = MultiModalDocument(
            modality=Modality.CODE,
            content=text_repr,
            ast_info={"functions": functions, "classes": classes},
            metadata={"source": source, "language": language, "type": "code"},
        )
        
        doc.embedding = await self._embed_text(text_repr)
        await self.vector_store.insert(doc)
        return doc
```

## 错误示例

```python
# 错误 1：直接用文本 embedding 检索图片
def bad_text_embedding_for_image():
    """图片文件名或路径作为文本存入向量库"""
    doc = {
        "content": "image_001.png",  # 只是文件名
        # 没有图片描述 → 语义检索完全失效
    }


# 错误 2：表格不分结构，当纯文本处理
def bad_table_as_plain_text():
    """HTML 表格当成纯文本"""
    html_table = "<table><tr><td>Name</td><td>Age</td></tr>..."
    chunks = text_splitter.split_text(html_table)  # 按字符拆分
    # 表格被拆散，无法还原语义


# 错误 3：代码当成普通文本分块
def bad_code_as_text():
    """代码按字符数切块 → 函数被切断"""
    code = """
def complex_algorithm(data):
    # ... 200 行代码
    return result
"""
    chunks = [
        "def complex_algorithm(data):\n    # ... 前 100 行",  # 不完整
        "# ... 后 100 行\n    return result"  # 缺少函数定义
    ]
    # 检索到任意一个 chunk 都无法理解完整函数
```

## 参考来源

- [CLIP: Learning Transferable Visual Models](https://arxiv.org/abs/2103.00020)
- [Table Transformer](https://huggingface.co/microsoft/table-transformer-detection)
- [AST 文档](https://docs.python.org/3/library/ast.html)
