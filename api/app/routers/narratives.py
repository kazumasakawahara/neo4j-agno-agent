"""Narratives router — Gemini-based text extraction, validation, registration, and safety check."""

import logging
import os
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.agents.gemini_agent import extract_from_text, check_safety_compliance
from app.agents.validator import validate_schema
from app.lib.db_operations import register_to_database
from app.lib.dedup import find_semantic_duplicates
from app.lib.file_readers import read_file
from app.schemas.narrative import (
    ExtractionRequest,
    ExtractedGraph,
    RegistrationResult,
    SafetyCheckResult,
    SemanticDuplicateWarning,
    ValidationResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/narratives", tags=["narratives"])

# サポートするファイル拡張子
_SUPPORTED_EXTENSIONS = {".docx", ".xlsx", ".pdf", ".txt", ".csv"}

# Semantic dedup config: label → (vector index name, text property)
_SEMANTIC_CHECK_CONFIG: dict[str, dict[str, str]] = {
    "NgAction": {"index": "ng_action_embedding", "prop": "action"},
    "CarePreference": {"index": "care_preference_embedding", "prop": "instruction"},
}


@router.post("/extract")
async def extract(request: ExtractionRequest):
    """ナラティブテキストから構造化データを抽出する。"""
    try:
        result = await extract_from_text(request.text, request.client_name)
        if result is None:
            raise HTTPException(
                status_code=422,
                detail="テキストからのデータ抽出に失敗しました。入力内容を確認してください。",
            )
        return ExtractedGraph(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("extract failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/validate", response_model=ValidationResult)
async def validate(graph: ExtractedGraph):
    """抽出済みグラフデータのスキーマバリデーションを行う。"""
    try:
        return validate_schema(graph.model_dump())
    except Exception as exc:
        logger.error("validate failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/register", response_model=RegistrationResult)
async def register(graph: ExtractedGraph):
    """抽出済みグラフデータを Neo4j に登録する。"""
    try:
        result = register_to_database(graph.model_dump())
        if result.get("status") == "error":
            raise HTTPException(
                status_code=422,
                detail=result.get("error", "データベース登録に失敗しました。"),
            )

        # Semantic dedup check — best effort, warnings only, never blocks registration
        semantic_dups: list[SemanticDuplicateWarning] = []
        for node in graph.nodes:
            config = _SEMANTIC_CHECK_CONFIG.get(node.label)
            if not config:
                continue
            text = node.properties.get(config["prop"], "")
            if not text:
                continue
            try:
                candidates = await find_semantic_duplicates(
                    text,
                    label=node.label,
                    index_name=config["index"],
                )
                for candidate in candidates:
                    semantic_dups.append(
                        SemanticDuplicateWarning(
                            new_text=text,
                            existing_text=candidate.get("text", ""),
                            similarity_score=candidate.get("score", 0.0),
                            label=node.label,
                            node_id=candidate.get("nodeId", ""),
                        )
                    )
            except Exception as dedup_exc:  # noqa: BLE001
                logger.warning(
                    "semantic dedup check failed for label=%s: %s",
                    node.label,
                    dedup_exc,
                )

        reg = RegistrationResult(**result)
        reg.semanticDuplicates = semantic_dups
        return reg
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("register failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """ファイルをアップロードしてテキストを抽出する。"""
    try:
        # ファイル拡張子チェック
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in _SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"未対応のファイル形式です: {ext}（対応: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}）",
            )

        content = await file.read()
        text = read_file(BytesIO(content), file.filename)
        if not text or not text.strip():
            raise HTTPException(
                status_code=422,
                detail="ファイルからテキストを抽出できませんでした。",
            )
        return {"filename": file.filename, "text": text}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("upload_file failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/safety-check", response_model=SafetyCheckResult)
async def safety_check(request: ExtractionRequest):
    """テキスト内容の安全性チェック（NgAction との照合）を行う。"""
    try:
        ng_actions = []
        if request.client_name:
            from app.lib.db_operations import run_query
            records = run_query(
                "MATCH (c:Client {name: $name})-[:MUST_AVOID]->(ng:NgAction) RETURN ng",
                {"name": request.client_name},
            )
            ng_actions = [dict(r["ng"]) for r in records]
        result = await check_safety_compliance(request.text, ng_actions)
        if result is None:
            raise HTTPException(
                status_code=422,
                detail="安全性チェックに失敗しました。",
            )
        return SafetyCheckResult(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("safety_check failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
