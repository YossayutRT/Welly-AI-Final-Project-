from __future__ import annotations

import ast
import json
import logging
import os
import re
import threading
from difflib import get_close_matches
from pathlib import Path
from typing import Any

import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rapidfuzz import process

from .config import Settings

logger = logging.getLogger(__name__)

if os.getenv("WELLY_EMBEDDINGS_LOCAL_ONLY", "true").strip().lower() in {"1", "true", "yes", "on"}:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


class WellyRAGService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        self.ready = False
        self.startup_error: str | None = None

        self.loaded_tables: dict[str, pd.DataFrame] = {}
        self.embeddings: HuggingFaceEmbeddings | None = None
        self.knowledge_vectorstore: FAISS | None = None
        self.recipes_vectorstore: FAISS | None = None
        self.calories_vectorstore: FAISS | None = None
        self.recipe_table: pd.DataFrame | None = None
        self.llm: ChatGroq | None = None

        self.rag_prompt = PromptTemplate.from_template(
            """
You are Welly AI nutrition assistant for human nutrition.
Answer in Thai with a natural, polite chat tone.
Use ONLY the provided context and never use outside knowledge.

Strict grounding rules:
- Treat the context as the only source of truth.
- Do not add food names, calorie values, nutrition facts, medical claims, cooking advice, or diet rules that are not present in the context.
- If the exact answer is not present in the context, say the information is insufficient instead of guessing.
- For recommendations, every recommended food must appear in the context.

When context is sufficient:
- Answer directly and clearly in normal chat style.
- Keep it concise and practical.
- Mention that the answer is based on the provided dataset/context only.

When context is insufficient:
- Reply exactly:
"ตอนนี้ผมยังไม่มีข้อมูลที่เพียงพอเกี่ยวกับ '{question}' จาก dataset/context ที่ระบบโหลดไว้\nผมจึงไม่เดาหรือเพิ่มข้อมูลจากภายนอกครับ"

When out of scope (pet/animal food):
- Reply exactly:
"หัวข้อนี้อยู่นอกขอบเขตของผู้ช่วยโภชนาการสำหรับมนุษย์ครับ\nผมช่วยตอบเรื่องโภชนาการ อาหาร และสุขภาพของคนได้"

Question:
{question}

Context:
{context}

Answer:
""".strip()
        )

    @property
    def llm_enabled(self) -> bool:
        return self.llm is not None

    def initialize(self) -> None:
        if self.ready:
            return

        with self._lock:
            if self.ready:
                return

            if self.settings.embeddings_local_only:
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

            self.loaded_tables = self._load_tables()
            self.embeddings = self._load_embeddings()
            self.knowledge_vectorstore = self._load_knowledge_vectorstore()
            self.recipes_vectorstore = self._load_recipe_vectorstore()
            self.calories_vectorstore = self._load_calories_vectorstore()
            self.llm = self._build_llm()

            self.ready = True
            self.startup_error = None
            logger.info("Welly RAG service initialized")

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok" if self.ready else "degraded",
            "ready": self.ready,
            "llm_enabled": self.llm_enabled,
            "model_name": self.settings.model_name,
            "model_path": str(self.settings.model_path) if self.settings.model_path else None,
            "llm_model": self.settings.llm_model,
            "startup_error": self.startup_error,
            "loaded_tables": sorted(self.loaded_tables.keys()),
        }

    def ask(self, question: str, k: int | None = None) -> dict[str, Any]:
        if not self.ready:
            raise RuntimeError("RAG service is not ready")

        top_k = k or self.settings.default_top_k
        question = question.strip()

        if self._is_out_of_scope(question):
            return {
                "question": question,
                "intent": "out_of_scope",
                "answer": (
                    "หัวข้อนี้อยู่นอกขอบเขตของผู้ช่วยโภชนาการสำหรับมนุษย์ครับ\n"
                    "ผมช่วยตอบเรื่องโภชนาการ อาหาร และสุขภาพของคนได้"
                ),
                "sources": [],
                "llm_enabled": self.llm_enabled,
                "used_context_fallback": False,
            }

        for direct_handler in (
            self._answer_calorie_lookup,
            self._answer_recipe_recommendation,
            self._answer_food_recommendation,
            self._answer_high_cholesterol_examples,
            self._answer_sodium_limit,
            self._answer_sugar_limit,
        ):
            response = direct_handler(question)
            if response is not None:
                response["llm_enabled"] = self.llm_enabled
                response["used_context_fallback"] = False
                return response

        intent = self._detect_intent(question)
        if intent in {"calorie", "recommendation"}:
            return {
                "question": question,
                "intent": intent,
                "answer": self._default_fallback(question),
                "sources": [],
                "llm_enabled": self.llm_enabled,
                "used_context_fallback": False,
            }

        collected = self._collect_context(question, intent=intent, k=top_k)
        context = "\n\n".join(item[0] for item in collected)
        top_score = collected[0][2] if collected else 0.0
        sources = [item[1] for item in collected]

        if (not collected) or (not context.strip()) or (top_score < 0.25):
            return {
                "question": question,
                "intent": intent,
                "answer": self._default_fallback(question),
                "sources": sources[:2],
                "llm_enabled": self.llm_enabled,
                "used_context_fallback": False,
            }

        if not self.llm_enabled:
            return {
                "question": question,
                "intent": intent,
                "answer": self._render_context_fallback(question, collected),
                "sources": sources,
                "llm_enabled": False,
                "used_context_fallback": True,
            }

        try:
            prompt_text = self.rag_prompt.format(question=question, context=context)
            llm_response = self.llm.invoke(prompt_text)
            raw_answer = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
            final_answer = self._clean_chat_answer(raw_answer, intent=intent, question=question)
            return {
                "question": question,
                "intent": intent,
                "answer": final_answer,
                "sources": sources,
                "llm_enabled": True,
                "used_context_fallback": False,
            }
        except Exception as exc:
            logger.exception("LLM invocation failed")
            return {
                "question": question,
                "intent": intent,
                "answer": self._render_context_fallback(question, collected, llm_error=str(exc)),
                "sources": sources,
                "llm_enabled": True,
                "used_context_fallback": True,
            }

    def suggest_food_names(self, user_text: str) -> list[str]:
        food_df = self.loaded_tables.get("food_dataset_with_risk.csv")
        if food_df is None or "food_name" not in food_df.columns:
            return []

        food_names = food_df["food_name"].dropna().astype(str).unique().tolist()
        query = user_text.strip()

        fuzzy_matches = process.extract(query, food_names, limit=5)
        close_matches = get_close_matches(query, food_names, n=5, cutoff=0.4)

        result: list[str] = []
        for item in fuzzy_matches:
            result.append(item[0])
        for item in close_matches:
            if item not in result:
                result.append(item)

        return result[:5]

    def _load_tables(self) -> dict[str, pd.DataFrame]:
        candidate_files = [
            self.settings.knowledge_dir / "standard_df.csv",
            self.settings.knowledge_dir / "dga_standard_df.csv",
            self.settings.knowledge_dir / "dga_rules_df.csv",
            self.settings.knowledge_dir / "bmi_standard_df.csv",
            self.settings.knowledge_dir / "bmi_rules_df.csv",
            self.settings.knowledge_dir / "claim_rules_df.csv",
            self.settings.knowledge_dir / "label_required_nutrients_df.csv",
            self.settings.knowledge_dir / "serving_size_reference_df.csv",
            self.settings.knowledge_dir / "user_health_knowledge.csv",
            self.settings.outputs_dir / "food_dataset_with_risk.csv",
            self.settings.data_dir / "calories.csv",
        ]

        loaded: dict[str, pd.DataFrame] = {}
        for path in candidate_files:
            if not path.exists():
                raise FileNotFoundError(f"Missing required knowledge file: {path}")
            loaded[path.name] = pd.read_csv(path)
        return loaded

    def _load_embeddings(self) -> HuggingFaceEmbeddings:
        try:
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"

        embedding_source = str(self.settings.model_path) if self.settings.model_path else self.settings.model_name
        model_kwargs: dict[str, Any] = {"device": device}
        if self.settings.embeddings_local_only:
            model_kwargs["local_files_only"] = True

        try:
            return HuggingFaceEmbeddings(
                model_name=embedding_source,
                model_kwargs=model_kwargs,
                encode_kwargs={"normalize_embeddings": True, "batch_size": 64},
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to load embedding model. If this machine has no network access, "
                "make sure the Hugging Face model is cached locally, set WELLY_MODEL_PATH, "
                "or disable local-only mode."
            ) from exc

    def _load_knowledge_vectorstore(self) -> FAISS:
        assert self.embeddings is not None

        split_docs = self._build_knowledge_documents()
        cached = self._load_faiss_without_pickle(self.settings.knowledge_index_dir, split_docs)
        if cached is not None:
            return cached

        logger.warning("FAISS knowledge cache is missing or stale; rebuilding from source tables")
        return FAISS.from_documents(split_docs, self.embeddings)

    def _build_knowledge_documents(self) -> list[Document]:
        documents = []
        for table_name, df in self.loaded_tables.items():
            if table_name == "calories.csv":
                continue
            for idx, row in df.iterrows():
                text = self._row_to_text(table_name, row)
                documents.append(
                    Document(
                        page_content=text,
                        metadata={"table": table_name, "row_index": int(idx)},
                    )
                )

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        return splitter.split_documents(documents)

    def _load_recipe_vectorstore(self) -> FAISS:
        assert self.embeddings is not None

        split_docs = self._build_recipe_documents()
        cached = self._load_faiss_without_pickle(self.settings.recipes_index_dir, split_docs)
        if cached is not None:
            return cached

        logger.warning("FAISS recipe cache is missing or stale; rebuilding from source CSV")
        return FAISS.from_documents(split_docs, self.embeddings)

    def _build_recipe_documents(self) -> list[Document]:
        recipes_path = self.settings.data_dir / "13k-recipes.csv"
        recipes_df = pd.read_csv(
            recipes_path,
            usecols=["Title", "Cleaned_Ingredients", "Instructions"],
            nrows=3000,
        ).fillna("")

        recipe_docs: list[Document] = []
        for idx, row in recipes_df.iterrows():
            title = str(row.get("Title", "")).strip()
            ingredients = str(row.get("Cleaned_Ingredients", "")).strip()
            instructions = str(row.get("Instructions", "")).strip()[:350]
            recipe_docs.append(
                Document(
                    page_content=(
                        f"Recipe. Title: {title}. "
                        f"Ingredients: {ingredients}. "
                        f"How to cook (summary): {instructions}."
                    ),
                    metadata={
                        "source": "13k-recipes.csv",
                        "doc_type": "recipe",
                        "row_index": int(idx),
                        "title": title,
                    },
                )
            )

        splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
        return splitter.split_documents(recipe_docs)

    def _load_calories_vectorstore(self) -> FAISS:
        assert self.embeddings is not None

        calorie_docs = self._build_calorie_documents()
        cached = self._load_faiss_without_pickle(self.settings.calories_index_dir, calorie_docs)
        if cached is not None:
            return cached

        logger.warning("FAISS calorie cache is missing or stale; rebuilding from source CSV")
        return FAISS.from_documents(calorie_docs, self.embeddings)

    def _build_calorie_documents(self) -> list[Document]:
        calories_path = self.settings.data_dir / "calories.csv"
        calories_df = pd.read_csv(
            calories_path,
            usecols=["FoodCategory", "FoodItem", "Cals_per100grams"],
        ).fillna("")

        calorie_docs: list[Document] = []
        for idx, row in calories_df.iterrows():
            item = str(row.get("FoodItem", "")).strip()
            category = str(row.get("FoodCategory", "")).strip()
            cals = str(row.get("Cals_per100grams", "")).strip()
            calorie_docs.append(
                Document(
                    page_content=(
                        f"Calories reference. Food item: {item}. "
                        f"Category: {category}. "
                        f"Energy per 100 grams: {cals}."
                    ),
                    metadata={
                        "source": "calories.csv",
                        "doc_type": "calorie",
                        "row_index": int(idx),
                        "food_item": item,
                    },
                )
            )

        return calorie_docs

    def _load_faiss_without_pickle(self, index_dir: Path, documents: list[Document]) -> FAISS | None:
        assert self.embeddings is not None

        index_faiss = index_dir / "index.faiss"
        if not index_faiss.exists():
            return None

        try:
            import faiss

            index = faiss.read_index(str(index_faiss))
        except Exception:
            logger.exception("Failed to read FAISS index from %s", index_faiss)
            return None

        if index.ntotal != len(documents):
            logger.warning(
                "Ignoring stale FAISS index at %s: index has %s vectors but source documents produce %s records",
                index_faiss,
                index.ntotal,
                len(documents),
            )
            return None

        docstore_ids = [str(idx) for idx in range(len(documents))]
        docstore = InMemoryDocstore(dict(zip(docstore_ids, documents, strict=True)))
        index_to_docstore_id = {idx: docstore_id for idx, docstore_id in enumerate(docstore_ids)}
        return FAISS(self.embeddings, index, docstore, index_to_docstore_id)

    def _build_llm(self) -> ChatGroq | None:
        if not self.settings.groq_api_key:
            logger.warning("GROQ_API_KEY is not configured; backend will use retrieval-only fallback")
            return None

        os.environ["GROQ_API_KEY"] = self.settings.groq_api_key
        return ChatGroq(
            model=self.settings.llm_model,
            temperature=0.0,
            max_tokens=512,
        )

    def _row_to_text(self, table_name: str, row: pd.Series) -> str:
        table = table_name.lower()

        if table == "standard_df.csv":
            return (
                f"Nutrition standard. Source {row.get('source_doc', '')}. "
                f"Category {row.get('category', '')}. Metric {row.get('metric', '')}. "
                f"Recommended value {row.get('recommended_value', '')} {row.get('unit', '')}. "
                f"Note {row.get('note', '')}."
            )

        if table == "dga_standard_df.csv":
            return (
                f"DGA standard. Source {row.get('source_doc', '')}. Category {row.get('category', '')}. "
                f"Metric {row.get('metric', '')}. Min value {row.get('min_value', '')}. "
                f"Max value {row.get('max_value', '')} {row.get('unit', '')}. "
                f"Target group {row.get('target_group', '')}."
            )

        if table == "dga_rules_df.csv":
            return (
                f"DGA rule. Source {row.get('source_doc', '')}. Rule name {row.get('rule_name', '')}. "
                f"Condition {row.get('condition', '')}. Unit {row.get('unit', '')}."
            )

        if table == "bmi_standard_df.csv":
            return (
                f"BMI standard. Source {row.get('source_doc', '')}. Category {row.get('category', '')}. "
                f"Metric {row.get('metric', '')}. Label {row.get('label', '')}. "
                f"Min value {row.get('min_value', '')}. Max value {row.get('max_value', '')}. "
                f"Unit {row.get('unit', '')}. Target group {row.get('target_group', '')}. "
                f"Note {row.get('note', '')}."
            )

        if table == "bmi_rules_df.csv":
            return (
                f"BMI rule. Source {row.get('source_doc', '')}. Rule name {row.get('rule_name', '')}. "
                f"Condition {row.get('condition', '')}. Unit {row.get('unit', '')}. "
                f"Note {row.get('note', '')}."
            )

        if table == "claim_rules_df.csv":
            return (
                f"Claim rule. Source {row.get('source_doc', '')}. Rule name {row.get('rule_name', '')}. "
                f"Condition type {row.get('condition_type', '')}. Nutrient {row.get('nutrient', '')}. "
                f"Value {row.get('value', '')} {row.get('unit', '')}."
            )

        if table == "label_required_nutrients_df.csv":
            return (
                f"Label required nutrient. Source {row.get('source_doc', '')}. Section {row.get('section', '')}. "
                f"Nutrient {row.get('nutrient', '')}. Unit {row.get('unit', '')}."
            )

        if table == "serving_size_reference_df.csv":
            return (
                f"Serving size reference. Source {row.get('source_doc', '')}. Category {row.get('category', '')}. "
                f"Item {row.get('item', '')}. Reference serving {row.get('reference_serving', '')} {row.get('unit', '')}."
            )

        if table == "user_health_knowledge.csv":
            return (
                f"User health knowledge. Patient ID {row.get('Patient_ID', row.get('patient_id', ''))}. "
                f"Age {row.get('Age', '')}. Gender {row.get('Gender', '')}. "
                f"Height {row.get('Height_cm', '')} cm. Weight {row.get('Weight_kg', '')} kg. "
                f"BMI {row.get('BMI', '')}. BMI category {row.get('BMI_Category', '')}. "
                f"Blood pressure systolic {row.get('Blood_Pressure_Systolic', '')}. "
                f"Blood pressure diastolic {row.get('Blood_Pressure_Diastolic', '')}. "
                f"Blood sugar {row.get('Blood_Sugar_Level', '')}. "
                f"Cholesterol {row.get('Cholesterol_Level', '')}. "
                f"Recommended calories {row.get('Recommended_Calories', '')}. "
                f"Recommended protein {row.get('Recommended_Protein', '')}. "
                f"Recommended carbs {row.get('Recommended_Carbs', '')}. "
                f"Recommended fats {row.get('Recommended_Fats', '')}. "
                f"Recommended meal plan {row.get('Recommended_Meal_Plan', '')}. "
                f"Health summary {row.get('Health_Profile_Summary', '')}."
            )

        if table == "food_dataset_with_risk.csv":
            return (
                f"Food risk record. Food name {row.get('food_name', '')}. "
                f"Calories {row.get('calories', '')}. Fat {row.get('fat', '')}. "
                f"Saturated fat {row.get('sat_fat', '')}. Carbs {row.get('carbs', '')}. "
                f"Sugar {row.get('sugar', '')}. Protein {row.get('protein', '')}. "
                f"Fiber {row.get('fiber', '')}. Cholesterol {row.get('cholesterol', '')}. "
                f"Sodium {row.get('sodium', '')}. Risk level {row.get('risk_level', '')}. "
                f"Chatbot summary {row.get('chatbot_summary', '')}."
            )

        joined = ". ".join(f"{col}: {row.get(col, '')}" for col in row.index)
        return f"{table_name} record. {joined}"

    def _collect_context(self, question: str, intent: str, k: int) -> list[tuple[str, dict[str, Any], float]]:
        assert self.knowledge_vectorstore is not None

        store_plan: list[tuple[str, FAISS]] = [("knowledge", self.knowledge_vectorstore)]
        if intent == "calorie" and self.calories_vectorstore is not None:
            store_plan.insert(0, ("calorie", self.calories_vectorstore))
        elif intent == "recipe" and self.recipes_vectorstore is not None:
            store_plan.insert(0, ("recipe", self.recipes_vectorstore))

        preferred_tables = {
            "dga_rules_df.csv",
            "dga_standard_df.csv",
            "bmi_standard_df.csv",
            "standard_df.csv",
            "serving_size_reference_df.csv",
        }

        collected: list[tuple[str, dict[str, Any], float]] = []
        for source_name, vectorstore in store_plan:
            hits = self._search_scored(vectorstore, question, k=k)
            for doc, score in hits:
                metadata = dict(doc.metadata or {})
                metadata["retrieved_from"] = source_name

                boosted_score = float(score)
                if intent == "guideline" and metadata.get("table") in preferred_tables:
                    boosted_score += 0.10
                if intent == source_name:
                    boosted_score += 0.05

                collected.append((doc.page_content, metadata, boosted_score))

        deduped = self._dedupe_hits(collected)
        deduped.sort(key=lambda item: item[2], reverse=True)
        return deduped[:6]

    def _search_scored(self, vectorstore: FAISS, query: str, k: int = 4) -> list[tuple[Document, float]]:
        try:
            return vectorstore.similarity_search_with_relevance_scores(query, k=k)
        except AssertionError as exc:
            logger.warning("Vector search skipped due to index mismatch: %s", exc)
            return []
        except Exception as exc:
            logger.warning("Vector search fallback used: %s", exc)
            try:
                docs = vectorstore.similarity_search(query, k=k)
                return [(doc, 0.0) for doc in docs]
            except Exception:
                return []

    def _dedupe_hits(
        self,
        items: list[tuple[str, dict[str, Any], float]],
    ) -> list[tuple[str, dict[str, Any], float]]:
        seen: set[tuple[Any, ...]] = set()
        deduped: list[tuple[str, dict[str, Any], float]] = []

        for content, metadata, score in items:
            key = (
                metadata.get("retrieved_from"),
                metadata.get("table"),
                metadata.get("source"),
                metadata.get("doc_type"),
                metadata.get("row_index"),
                metadata.get("title"),
                metadata.get("food_item"),
                content,
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append((content, metadata, score))

        return deduped

    def _detect_intent(self, question: str) -> str:
        q = question.lower()
        calorie_keywords = ["แคล", "แคลอ", "kcal", "calorie", "calories", "พลังงาน"]
        recipe_keywords = ["วิธีทำ", "ทำยังไง", "ขั้นตอน", "สูตร", "เมนู", "recipe", "cook", "ingredients"]
        guideline_keywords = ["ควร", "ไม่เกิน", "ปกติ", "มาตรฐาน", "ต่อวัน", "ต่อมื้อ", "bmi", "โซเดียม", "น้ำตาล"]

        if any(keyword in q for keyword in calorie_keywords):
            return "calorie"
        if any(keyword in q for keyword in recipe_keywords):
            return "recipe"
        if self._looks_like_food_recommendation(q):
            return "recommendation"
        if any(keyword in q for keyword in guideline_keywords):
            return "guideline"
        return "general"

    def _is_out_of_scope(self, question: str) -> bool:
        q = question.lower()
        out_scope_keywords = [
            "อาหารหมา",
            "อาหารแมว",
            "อาหารสุนัข",
            "อาหารสัตว์",
            "หมากิน",
            "แมวกิน",
            "dog food",
            "cat food",
            "pet food",
            "animal feed",
        ]
        return any(keyword in q for keyword in out_scope_keywords)

    def _default_fallback(self, question: str) -> str:
        return (
            f"ตอนนี้ผมยังไม่มีข้อมูลที่เพียงพอเกี่ยวกับ '{question}' จาก dataset/context ที่ระบบโหลดไว้\n"
            "ผมจึงไม่เดาหรือเพิ่มข้อมูลจากภายนอกครับ"
        )

    def _clean_chat_answer(self, text: str, intent: str, question: str) -> str:
        answer = (text or "").strip()
        if not answer:
            return self._default_fallback(question)

        if intent == "out_of_scope" or "ตอนนี้ผมยังไม่มีข้อมูลที่เพียงพอ" in answer or "อยู่นอกขอบเขต" in answer:
            return answer

        if answer.startswith("{") and answer.endswith("}"):
            try:
                payload = json.loads(answer)
                if isinstance(payload, dict) and payload.get("answer"):
                    answer = str(payload["answer"]).strip()
            except Exception:
                pass

        answer = re.sub(r"^(ขออภัยด้วยครับ|ขอโทษครับ|ขออภัยครับ)\s*", "", answer).strip()
        return answer or self._default_fallback(question)

    def _render_context_fallback(
        self,
        question: str,
        collected: list[tuple[str, dict[str, Any], float]],
        llm_error: str | None = None,
    ) -> str:
        if not collected:
            return self._default_fallback(question)

        lines = [
            "ตอนนี้ระบบยังสรุปคำตอบด้วย LLM ไม่ได้ แต่ผมพบข้อมูลที่เกี่ยวข้องจาก context ที่ retrieve ได้ดังนี้ครับ:",
        ]
        for content, _, _score in collected[:3]:
            lines.append(f"- {self._compact_text(content)}")

        if llm_error:
            lines.append("หมายเหตุ: การเรียก LLM ล้มเหลวชั่วคราว จึงแสดงเฉพาะข้อมูลที่ค้นเจอ")
        else:
            lines.append("หากต้องการคำตอบสรุปอัตโนมัติ ให้ตั้งค่า GROQ_API_KEY สำหรับ backend เพิ่มเติม")

        return "\n".join(lines)

    def _compact_text(self, text: str, limit: int = 180) -> str:
        clean = re.sub(r"\s+", " ", text).strip()
        if len(clean) <= limit:
            return clean
        return clean[: limit - 3].rstrip() + "..."

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        text = re.sub(r"[^0-9.\-]", "", text)
        if not text:
            return None
        try:
            return float(text)
        except Exception:
            return None

    def _looks_like_food_recommendation(self, question: str) -> bool:
        q = question.lower()
        if self._looks_like_recipe_request(q):
            return False
        example_only = any(keyword in q for keyword in ["มีอะไรบ้าง", "อะไรบ้าง", "ตัวอย่าง", "example", "examples"])
        recommendation_terms = [
            "แนะนำ",
            "ควรกิน",
            "กินอะไร",
            "เลือกกิน",
            "อาหารสำหรับ",
            "อาหารเช้า",
            "อาหารเย็น",
            "อาหารกลางวัน",
            "เมนูสุขภาพ",
            "ลดน้ำหนัก",
            "คุมน้ำหนัก",
            "เบาหวาน",
            "คุมเบาหวาน",
            "น้ำตาลในเลือด",
            "ความดัน",
            "โซเดียมต่ำ",
            "คอเลสเตอรอลสูง",
            "ไขมันในเลือด",
            "โปรตีนสูง",
            "healthy",
            "recommend",
            "weight loss",
            "diabetes",
            "hypertension",
            "high protein",
        ]
        if example_only and not any(keyword in q for keyword in ["แนะนำ", "ควรกิน", "กินอะไร", "สำหรับ", "recommend"]):
            return False
        return any(keyword in q for keyword in recommendation_terms)

    def _looks_like_recipe_request(self, question: str) -> bool:
        q = question.lower()
        recipe_terms = [
            "เมนู",
            "สูตร",
            "วัตถุดิบ",
            "ส่วนผสม",
            "วิธีทำ",
            "ทำยังไง",
            "ทำอย่างไร",
            "ขั้นตอน",
            "แผนอาหาร",
            "7 วัน",
            "เจ็ดวัน",
            "recipe",
            "recipes",
            "ingredient",
            "ingredients",
            "cook",
            "meal plan",
        ]
        meal_terms = ["อาหารเช้า", "อาหารกลางวัน", "อาหารเย็น", "breakfast", "lunch", "dinner"]
        ask_terms = ["แนะนำ", "ช่วย", "หา", "จัด", "recommend", "suggest"]
        return any(term in q for term in recipe_terms) or (
            any(term in q for term in meal_terms) and any(term in q for term in ask_terms)
        )

    def _answer_recipe_recommendation(self, question: str) -> dict[str, Any] | None:
        q = question.lower()
        if not self._looks_like_recipe_request(q):
            return None

        profile = self._recipe_profile(q)
        rows = self._select_recipe_rows(profile)
        if rows.empty:
            return None

        lines = [
            "คำตอบนี้ใช้เฉพาะข้อมูลจาก 13k-recipes.csv ที่ระบบโหลดไว้เท่านั้นครับ",
            profile["intro"],
        ]
        if profile["nutrition_note"]:
            lines.append(profile["nutrition_note"])

        if profile["is_plan"]:
            lines.append("ตัวอย่างแผนเมนูจากสูตรอาหารใน dataset:")
            for day, (_, row) in enumerate(rows.iterrows(), start=1):
                lines.extend(self._format_recipe_row(row, prefix=f"วันที่ {day}"))
        else:
            lines.append("เมนูที่พบจาก dataset:")
            for _, row in rows.iterrows():
                lines.extend(self._format_recipe_row(row))

        return {
            "question": question,
            "intent": profile["intent"],
            "answer": "\n".join(lines),
            "sources": [
                {
                    "table": "13k-recipes.csv",
                    "row_index": int(row["row_index"]),
                    "retrieved_from": "recipe_table",
                    "method": profile["method"],
                    "title": str(row["Title"]),
                }
                for _, row in rows.iterrows()
            ],
        }

    def _recipe_profile(self, q: str) -> dict[str, Any]:
        is_plan = any(term in q for term in ["7 วัน", "เจ็ดวัน", "แผนอาหาร", "meal plan", "7-day", "7 day"])
        needs_steps = any(term in q for term in ["วิธีทำ", "ทำยังไง", "ทำอย่างไร", "ขั้นตอน", "cook"])
        health_terms = ["ลดน้ำหนัก", "โปรตีนสูง", "สุขภาพ", "เบาหวาน", "น้ำตาล", "คอเลสเตอรอล", "โซเดียม", "ความดัน"]

        terms: list[str] = []
        mode = "recipe_general"
        intro = "ผมคัดเมนูจากชื่อสูตรและรายการวัตถุดิบใน 13k-recipes.csv ครับ"

        if any(term in q for term in ["โปรตีนสูง", "high protein", "เพิ่มกล้าม", "muscle"]):
            mode = "recipe_high_protein"
            terms.extend(["chicken", "turkey", "fish", "salmon", "tuna", "egg", "bean", "lentil", "tofu", "shrimp", "yogurt"])
            intro = "ผมคัดเมนูที่ชื่อสูตรหรือวัตถุดิบมีแหล่งโปรตีนจาก 13k-recipes.csv ครับ"
        elif any(term in q for term in ["ลดน้ำหนัก", "คุมน้ำหนัก", "weight loss", "diet"]):
            mode = "recipe_weight_loss"
            terms.extend(["salad", "soup", "chicken", "fish", "vegetable", "bean", "lentil", "bowl"])
            intro = "ผมคัดเมนูที่ชื่อสูตรหรือวัตถุดิบเข้ากับกลุ่ม salad, soup, chicken, fish, vegetable, bean จาก dataset ครับ"
        elif any(term in q for term in ["อาหารเช้า", "breakfast"]):
            mode = "recipe_breakfast"
            terms.extend(["breakfast", "egg", "oat", "yogurt", "toast", "smoothie", "granola", "fruit"])
            intro = "ผมคัดเมนูอาหารเช้าจากชื่อสูตรและวัตถุดิบใน 13k-recipes.csv ครับ"
        elif any(term in q for term in ["อาหารกลางวัน", "lunch"]):
            mode = "recipe_lunch"
            terms.extend(["lunch", "salad", "sandwich", "bowl", "soup", "rice", "chicken"])
            intro = "ผมคัดเมนูอาหารกลางวันจากชื่อสูตรและวัตถุดิบใน 13k-recipes.csv ครับ"
        elif any(term in q for term in ["อาหารเย็น", "dinner"]):
            mode = "recipe_dinner"
            terms.extend(["dinner", "chicken", "salmon", "fish", "soup", "salad", "bowl", "stew", "roast"])
            intro = "ผมคัดเมนูอาหารเย็นจากชื่อสูตรและวัตถุดิบใน 13k-recipes.csv ครับ"
        elif any(term in q for term in ["สุขภาพ", "healthy"]):
            mode = "recipe_healthy"
            terms.extend(["salad", "soup", "vegetable", "chicken", "fish", "bean", "lentil", "yogurt", "oat"])
            intro = "ผมคัดเมนูที่ชื่อสูตรหรือวัตถุดิบเข้ากับกลุ่มอาหารสุขภาพจาก dataset ครับ"

        english_terms = [term for term in re.findall(r"[a-z][a-z0-9-]+", q) if len(term) > 2]
        terms.extend(english_terms)

        deduped_terms: list[str] = []
        for term in terms:
            if term not in deduped_terms:
                deduped_terms.append(term)
        if not deduped_terms:
            deduped_terms = ["chicken", "salad", "soup", "vegetable", "fish", "rice", "egg"]

        nutrition_note = ""
        if any(term in q for term in health_terms):
            nutrition_note = (
                "หมายเหตุ: 13k-recipes.csv มีชื่อเมนู วัตถุดิบ และวิธีทำ "
                "แต่ไม่มีค่าแคลอรี/โปรตีน/โซเดียมต่อจาน ผมจึงไม่ยืนยันตัวเลขโภชนาการจากสูตรเหล่านี้ครับ"
            )

        return {
            "intent": mode,
            "method": "recipe_title_ingredient_filter",
            "terms": deduped_terms,
            "is_plan": is_plan,
            "needs_steps": needs_steps,
            "limit": 7 if is_plan else 4,
            "intro": intro,
            "nutrition_note": nutrition_note,
            "prefer_easy": any(term in q for term in ["ง่าย", "เร็ว", "quick", "easy", "simple"]),
        }

    def _select_recipe_rows(self, profile: dict[str, Any]) -> pd.DataFrame:
        df = self._get_recipe_table()
        if df.empty:
            return df

        work = df.copy()
        work["recipe_text"] = (
            work["Title"].fillna("").astype(str) + " " + work["Cleaned_Ingredients"].fillna("").astype(str)
        ).str.lower()
        work["ingredient_count"] = work["Cleaned_Ingredients"].apply(lambda value: len(self._parse_recipe_ingredients(value)))
        work = work[work["ingredient_count"].between(3, 16)]

        terms = profile["terms"]
        if terms:
            pattern = "|".join(self._term_regex(term) for term in terms)
            matched = work[work["recipe_text"].str.contains(pattern, regex=True, na=False)].copy()
            if not matched.empty:
                work = matched

        if work.empty:
            return work

        work = self._remove_poor_recipe_candidates(work, health_focused=bool(profile["nutrition_note"]))
        if work.empty:
            return work

        work["recipe_score"] = work.apply(lambda row: self._recipe_score(row, profile), axis=1)
        work = work.sort_values(["recipe_score", "Title"], ascending=[False, True])
        return self._diverse_recipe_rows(work, limit=profile["limit"])

    def _get_recipe_table(self) -> pd.DataFrame:
        if self.recipe_table is not None:
            return self.recipe_table

        recipes_path = self.settings.data_dir / "13k-recipes.csv"
        try:
            self.recipe_table = (
                pd.read_csv(
                    recipes_path,
                    usecols=["Title", "Cleaned_Ingredients", "Instructions"],
                )
                .fillna("")
                .reset_index(names="row_index")
            )
        except Exception:
            logger.exception("Failed to load recipe table from %s", recipes_path)
            self.recipe_table = pd.DataFrame()

        return self.recipe_table

    def _remove_poor_recipe_candidates(self, df: pd.DataFrame, health_focused: bool) -> pd.DataFrame:
        poor_terms = ["cocktail", "margarita", "beer", "wine", "vodka", "martini"]
        if health_focused:
            poor_terms.extend(["cake", "cookie", "brownie", "ice cream", "pie", "cupcake", "donut", "frosting"])

        pattern = "|".join(re.escape(term) for term in poor_terms)
        return df[~df["recipe_text"].str.contains(pattern, regex=True, na=False)].copy()

    def _recipe_score(self, row: pd.Series, profile: dict[str, Any]) -> float:
        title = str(row.get("Title", "")).lower()
        text = str(row.get("recipe_text", ""))
        ingredient_count = int(row.get("ingredient_count", 0))

        score = 0.0
        for term in profile["terms"]:
            pattern = self._term_regex(term)
            if re.search(pattern, title):
                score += 6.0
            if re.search(pattern, text):
                score += 2.0

        if profile["prefer_easy"]:
            if ingredient_count <= 8:
                score += 5.0
            if any(term in title for term in ["easy", "quick", "simple"]):
                score += 5.0

        if 5 <= ingredient_count <= 11:
            score += 2.0

        return score

    def _diverse_recipe_rows(self, df: pd.DataFrame, limit: int) -> pd.DataFrame:
        selected_indexes: list[Any] = []
        used_groups: set[str] = set()

        for idx, row in df.iterrows():
            group = self._recipe_group(str(row.get("recipe_text", "")))
            if group in used_groups:
                continue
            selected_indexes.append(idx)
            used_groups.add(group)
            if len(selected_indexes) >= limit:
                return df.loc[selected_indexes]

        for idx, _row in df.iterrows():
            if idx in selected_indexes:
                continue
            selected_indexes.append(idx)
            if len(selected_indexes) >= limit:
                break

        return df.loc[selected_indexes]

    def _recipe_group(self, text: str) -> str:
        groups = {
            "chicken": ["chicken"],
            "fish": ["fish", "salmon", "tuna", "cod", "shrimp"],
            "egg": ["egg"],
            "bean": ["bean", "lentil", "chickpea"],
            "tofu": ["tofu"],
            "salad": ["salad"],
            "soup": ["soup"],
            "rice": ["rice"],
            "pasta": ["pasta", "noodle"],
            "vegetable": ["vegetable", "broccoli", "spinach", "carrot"],
            "yogurt": ["yogurt"],
            "oat": ["oat"],
        }
        for group, terms in groups.items():
            if any(re.search(self._term_regex(term), text) for term in terms):
                return group
        title_word = text.split(maxsplit=1)[0] if text else "other"
        return title_word

    def _format_recipe_row(self, row: pd.Series, prefix: str | None = None) -> list[str]:
        title = str(row.get("Title", "")).strip()
        ingredients = self._parse_recipe_ingredients(row.get("Cleaned_Ingredients", ""))
        ingredient_text = ", ".join(ingredients[:7]) if ingredients else "ไม่มีรายการวัตถุดิบในแถวนี้"
        heading = f"- {prefix}: {title}" if prefix else f"- {title}"
        lines = [heading, f"  วัตถุดิบจาก dataset: {ingredient_text}"]

        instruction = self._compact_recipe_instruction(str(row.get("Instructions", "")))
        if instruction:
            lines.append(f"  วิธีทำย่อจาก dataset: {instruction}")

        return lines

    def _parse_recipe_ingredients(self, value: Any) -> list[str]:
        text = str(value or "").strip()
        if not text:
            return []

        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                return [self._compact_text(str(item), limit=80) for item in parsed if str(item).strip()]
        except Exception:
            pass

        return [self._compact_text(item.strip(), limit=80) for item in text.split(",") if item.strip()]

    def _compact_recipe_instruction(self, text: str, limit: int = 170) -> str:
        clean = re.sub(r"\s+", " ", text).strip()
        if not clean:
            return ""

        first_sentence = re.split(r"(?<=[.!?])\s+", clean, maxsplit=1)[0]
        return self._compact_text(first_sentence, limit=limit)

    def _answer_food_recommendation(self, question: str) -> dict[str, Any] | None:
        q = question.lower()
        if not self._looks_like_food_recommendation(q):
            return None

        profile = self._recommendation_profile(q)
        rows = self._select_recommended_foods(profile)
        if rows.empty:
            return None

        lines = [
            "คำตอบนี้ใช้เฉพาะข้อมูลจาก food_dataset_with_risk.csv ที่ระบบโหลดไว้เท่านั้นครับ",
            profile["intro"],
            f"เกณฑ์ที่ใช้คัด: {profile['criteria']}",
        ]
        for _, row in rows.iterrows():
            lines.append(f"- {self._format_food_row(row)}")

        if profile.get("closing"):
            lines.append(profile["closing"])

        return {
            "question": question,
            "intent": profile["intent"],
            "answer": "\n".join(lines),
            "sources": [
                {
                    "table": "food_dataset_with_risk.csv",
                    "row_index": int(row["row_index"]),
                    "retrieved_from": "tabular_filter",
                    "method": profile["method"],
                    "food_item": str(row["food_name"]),
                }
                for _, row in rows.iterrows()
            ],
        }

    def _recommendation_profile(self, q: str) -> dict[str, Any]:
        if any(keyword in q for keyword in ["คอเลสเตอรอล", "cholesterol", "ไขมันในเลือด"]):
            return {
                "intent": "recommend_cholesterol_control",
                "method": "nutrition_filter_cholesterol",
                "intro": "สำหรับคำถามคอเลสเตอรอล ผมคัดเฉพาะรายการอาหารที่มีค่าโภชนาการอยู่ใน dataset ครับ",
                "criteria": "risk ต่ำ, คอเลสเตอรอลไม่เกินค่ากรองของระบบ, ไขมันอิ่มตัวต่ำ, น้ำตาลไม่สูง และตัดรายการที่ชื่อใน dataset เป็นวัตถุดิบ/ของทอด/ของหวาน",
                "filters": {
                    "calories_max": 450,
                    "cholesterol_max": 20,
                    "sat_fat_max": 2.5,
                    "sugar_max": 10,
                    "sodium_max": 1.0,
                    "preferred_terms": [
                        "oat",
                        "yogurt",
                        "salad",
                        "soup",
                        "chicken breast",
                        "fish",
                        "tuna",
                        "salmon",
                        "brown rice cooked",
                        "wild rice cooked",
                        "beans",
                        "lentil",
                        "vegetable",
                        "fruit",
                        "egg",
                    ],
                },
                "score_mode": "cholesterol",
                "closing": "ผมไม่เพิ่มรายการอาหารหรือคำแนะนำที่ไม่มีอยู่ใน dataset ครับ",
            }

        if any(keyword in q for keyword in ["เบาหวาน", "น้ำตาลในเลือด", "diabetes", "diabetic"]):
            return {
                "intent": "recommend_blood_sugar_control",
                "method": "nutrition_filter_diabetes",
                "intro": "สำหรับคำถามเบาหวาน/น้ำตาล ผมคัดเฉพาะรายการที่มีค่าน้ำตาลและสารอาหารอยู่ใน dataset ครับ",
                "criteria": "risk ต่ำ, น้ำตาลไม่เกินค่ากรองของระบบ, ไขมันอิ่มตัวไม่สูง, แคลอรีไม่สูงเกิน และตัดรายการที่ชื่อใน dataset เป็นของหวาน/เครื่องดื่มหวาน",
                "filters": {
                    "calories_max": 450,
                    "sugar_max": 5,
                    "sat_fat_max": 3,
                    "sodium_max": 1.0,
                    "preferred_terms": [
                        "oat",
                        "greek yogurt",
                        "salad",
                        "soup",
                        "chicken breast",
                        "fish",
                        "tuna",
                        "salmon",
                        "brown rice cooked",
                        "wild rice cooked",
                        "beans",
                        "lentil",
                        "vegetable",
                        "egg",
                    ],
                },
                "score_mode": "diabetes",
                "closing": "ผมไม่สรุปข้อมูลทางการแพทย์หรือปริมาณคาร์บที่ไม่มีอยู่ใน dataset ครับ",
            }

        if any(keyword in q for keyword in ["ความดัน", "โซเดียมต่ำ", "hypertension", "low sodium"]):
            return {
                "intent": "recommend_low_sodium",
                "method": "nutrition_filter_low_sodium",
                "intro": "สำหรับคำถามความดัน/โซเดียม ผมคัดเฉพาะรายการที่มีค่าโซเดียมอยู่ใน dataset ครับ",
                "criteria": "risk ต่ำ, โซเดียมไม่เกินค่ากรองของระบบ, ไขมันอิ่มตัวต่ำ, น้ำตาลไม่สูง และตัดรายการที่ชื่อใน dataset เป็นซอส/อาหารแปรรูปบางกลุ่ม",
                "filters": {
                    "calories_max": 450,
                    "sugar_max": 10,
                    "sat_fat_max": 3,
                    "sodium_max": 0.3,
                    "preferred_terms": [
                        "oat",
                        "yogurt",
                        "salad",
                        "chicken breast",
                        "fish",
                        "tuna",
                        "salmon",
                        "brown rice cooked",
                        "wild rice cooked",
                        "beans",
                        "lentil",
                        "vegetable",
                        "fruit",
                        "egg",
                    ],
                },
                "score_mode": "sodium",
                "closing": "ผมไม่เพิ่มคำแนะนำเรื่องอาหารหรือเครื่องปรุงที่ไม่มีอยู่ใน dataset ครับ",
            }

        if any(keyword in q for keyword in ["ลดน้ำหนัก", "คุมน้ำหนัก", "weight loss", "diet"]):
            return {
                "intent": "recommend_weight_loss",
                "method": "nutrition_filter_weight_loss",
                "intro": "สำหรับคำถามลดน้ำหนัก ผมคัดเฉพาะรายการที่มีค่าแคลอรีและสารอาหารอยู่ใน dataset ครับ",
                "criteria": "risk ต่ำ, แคลอรีไม่เกินค่ากรองของระบบ, น้ำตาลไม่สูง, ไขมันอิ่มตัวต่ำ และมีโปรตีนหรือไฟเบอร์ตามค่าที่บันทึกไว้",
                "filters": {
                    "calories_min": 30,
                    "calories_max": 350,
                    "sugar_max": 8,
                    "sat_fat_max": 3,
                    "sodium_max": 1.0,
                    "protein_or_fiber_min": 3,
                    "preferred_terms": [
                        "oat",
                        "yogurt",
                        "salad",
                        "soup",
                        "chicken breast",
                        "fish",
                        "tuna",
                        "salmon",
                        "brown rice cooked",
                        "wild rice cooked",
                        "beans",
                        "lentil",
                        "vegetable",
                        "fruit",
                        "egg",
                    ],
                },
                "score_mode": "weight_loss",
                "closing": "ผมไม่คำนวณเป้าหมายพลังงานรายวันหรือเพิ่มแผนอาหารที่ไม่มีอยู่ใน dataset ครับ",
            }

        if any(keyword in q for keyword in ["โปรตีนสูง", "high protein", "เพิ่มกล้าม", "muscle"]):
            return {
                "intent": "recommend_high_protein",
                "method": "nutrition_filter_high_protein",
                "intro": "สำหรับคำถามโปรตีนสูง ผมคัดเฉพาะรายการที่มีค่าโปรตีนอยู่ใน dataset ครับ",
                "criteria": "โปรตีนไม่ต่ำกว่าค่ากรองของระบบ, แคลอรีไม่เกินค่ากรองของระบบ, น้ำตาลไม่สูง และไขมันอิ่มตัวไม่สูง",
                "filters": {
                    "calories_max": 550,
                    "protein_min": 12,
                    "sugar_max": 8,
                    "sat_fat_max": 5,
                    "sodium_max": 1.2,
                    "preferred_terms": [
                        "chicken breast",
                        "fish",
                        "tuna",
                        "salmon",
                        "egg",
                        "greek yogurt",
                        "yogurt",
                        "beans",
                        "lentil",
                        "turkey",
                    ],
                },
                "score_mode": "high_protein",
                "closing": "ผมไม่เพิ่มคำแนะนำการจับคู่อาหารที่ไม่มีอยู่ใน dataset ครับ",
            }

        if any(keyword in q for keyword in ["อาหารเช้า", "breakfast"]):
            return {
                "intent": "recommend_breakfast",
                "method": "nutrition_filter_breakfast",
                "intro": "สำหรับคำถามอาหารเช้า ผมคัดเฉพาะรายการที่มีอยู่ใน dataset และชื่อเข้ากับกลุ่มอาหารเช้าที่ระบบรู้จักครับ",
                "criteria": "risk ต่ำ, แคลอรีไม่เกินค่ากรองของระบบ, น้ำตาลไม่สูง และชื่ออาหารตรงกับกลุ่มคำใน dataset เช่น oat, yogurt, cereal, egg, fruit",
                "filters": {
                    "calories_min": 30,
                    "calories_max": 350,
                    "sugar_max": 8,
                    "sat_fat_max": 3,
                    "sodium_max": 1.0,
                    "preferred_terms": ["oat", "yogurt", "cereal", "egg", "fruit", "rice soup", "banana"],
                },
                "score_mode": "breakfast",
                "closing": "ผมไม่เพิ่มเมนูอาหารเช้าที่ไม่มีอยู่ใน dataset ครับ",
            }

        return {
            "intent": "recommend_general",
            "method": "nutrition_filter_general",
            "intro": "ผมคัดเฉพาะรายการอาหารที่มีอยู่ใน dataset และมีค่าสารอาหารให้ตรวจได้ครับ",
            "criteria": "risk ต่ำ, แคลอรีไม่เกินค่ากรองของระบบ, น้ำตาลและไขมันอิ่มตัวไม่สูง และมีโปรตีนหรือไฟเบอร์ตามค่าที่บันทึกไว้",
            "filters": {
                "calories_min": 30,
                "calories_max": 450,
                "sugar_max": 10,
                "sat_fat_max": 4,
                "sodium_max": 1.0,
                "protein_or_fiber_min": 2,
                "preferred_terms": [
                    "oat",
                    "yogurt",
                    "salad",
                    "soup",
                    "chicken breast",
                    "fish",
                    "tuna",
                    "salmon",
                    "brown rice cooked",
                    "wild rice cooked",
                    "beans",
                    "lentil",
                    "vegetable",
                    "fruit",
                    "egg",
                ],
            },
            "score_mode": "general",
            "closing": "ผมไม่เพิ่มรายการอาหารหรือข้อมูลโภชนาการที่ไม่มีอยู่ใน dataset ครับ",
        }

    def _select_recommended_foods(self, profile: dict[str, Any], limit: int = 4) -> pd.DataFrame:
        df = self.loaded_tables.get("food_dataset_with_risk.csv")
        if df is None or df.empty:
            return pd.DataFrame()

        numeric_columns = ["calories", "fat", "sat_fat", "carbs", "sugar", "protein", "fiber", "cholesterol", "sodium"]
        work = df.reset_index(names="row_index").copy()
        for column in numeric_columns:
            work[column] = pd.to_numeric(work[column], errors="coerce").fillna(0)

        work["food_name_text"] = work["food_name"].fillna("").astype(str).str.lower()
        work = work[work["calories"] > profile["filters"].get("calories_min", 0)]
        work = work[work["calories"] <= profile["filters"].get("calories_max", 500)]
        work = work[work["protein"] <= 80]
        work = work[work["fiber"] <= 20]
        work = work[work["risk_level"].astype(str).str.lower().eq("low")]

        for column, filter_name in (
            ("cholesterol", "cholesterol_max"),
            ("sat_fat", "sat_fat_max"),
            ("sugar", "sugar_max"),
            ("sodium", "sodium_max"),
        ):
            max_value = profile["filters"].get(filter_name)
            if max_value is not None:
                work = work[work[column] <= max_value]

        protein_min = profile["filters"].get("protein_min")
        if protein_min is not None:
            work = work[work["protein"] >= protein_min]

        protein_or_fiber_min = profile["filters"].get("protein_or_fiber_min")
        if protein_or_fiber_min is not None:
            work = work[(work["protein"] >= protein_or_fiber_min) | (work["fiber"] >= protein_or_fiber_min)]

        preferred_terms = profile["filters"].get("preferred_terms")
        if preferred_terms:
            pattern = "|".join(self._term_regex(term) for term in preferred_terms)
            preferred = work[work["food_name_text"].str.contains(pattern, regex=True, na=False)]
            if not preferred.empty:
                work = preferred

        if work.empty:
            return work

        work = self._remove_poor_recommendation_candidates(work)
        if work.empty:
            return work

        work["recommendation_score"] = work.apply(
            lambda row: self._recommendation_score(row, profile["score_mode"]),
            axis=1,
        )
        work = work.sort_values(["recommendation_score", "protein", "fiber"], ascending=False)
        return self._diverse_food_rows(work, limit=limit)

    def _remove_poor_recommendation_candidates(self, df: pd.DataFrame) -> pd.DataFrame:
        poor_terms = [
            "raw",
            "flour",
            "oil",
            "fat",
            "brain",
            "liver",
            "giblet",
            "offal",
            "butter",
            "bacon",
            "ham",
            "sausage",
            "cheese",
            "candy",
            "chocolate",
            "cookie",
            "cake",
            "syrup",
            "pudding",
            "marshmallow",
            "frozen yogurt",
            "dried",
            "seasoning",
            "spice",
            "extract",
            "extender",
            "protein cookie",
            "protein bar",
            "noodles",
            "pasta",
            "macaroni",
            "fried",
            "crispy",
            "mcdonalds",
            "kentucky",
            "drink",
            "soda",
            "sauce",
            "dressing",
            "alcohol",
            "wine",
            "beer",
        ]
        pattern = "|".join(re.escape(term) for term in poor_terms)
        return df[~df["food_name_text"].str.contains(pattern, regex=True, na=False)].copy()

    def _diverse_food_rows(self, df: pd.DataFrame, limit: int) -> pd.DataFrame:
        selected_indexes: list[Any] = []
        used_groups: set[str] = set()

        for idx, row in df.iterrows():
            group = self._food_group(str(row.get("food_name_text", "")))
            if group in used_groups:
                continue
            selected_indexes.append(idx)
            used_groups.add(group)
            if len(selected_indexes) >= limit:
                return df.loc[selected_indexes]

        for idx, _row in df.iterrows():
            if idx in selected_indexes:
                continue
            selected_indexes.append(idx)
            if len(selected_indexes) >= limit:
                break

        return df.loc[selected_indexes]

    def _food_group(self, name: str) -> str:
        group_terms = {
            "beans": ["beans", "lentil", "pea"],
            "fish": ["fish", "tuna", "salmon", "cod", "sardine"],
            "yogurt": ["yogurt"],
            "oat": ["oat", "cereal"],
            "rice": ["rice"],
            "salad": ["salad"],
            "soup": ["soup"],
            "egg": ["egg"],
            "fruit": ["fruit", "banana", "apple", "berry"],
            "chicken": ["chicken"],
            "turkey": ["turkey"],
            "vegetable": ["vegetable", "spinach", "broccoli", "carrot"],
        }
        for group, terms in group_terms.items():
            if any(re.search(self._term_regex(term), name) for term in terms):
                return group
        first_word = name.split(maxsplit=1)[0] if name else "other"
        return first_word

    def _recommendation_score(self, row: pd.Series, mode: str) -> float:
        meal_bonus = self._meal_name_bonus(str(row.get("food_name_text", "")))
        base = (
            meal_bonus
            + float(row.get("protein", 0)) * 1.2
            + float(row.get("fiber", 0)) * 1.6
            - float(row.get("sugar", 0)) * 1.4
            - float(row.get("sat_fat", 0)) * 2.2
            - float(row.get("sodium", 0)) * 3.0
            - float(row.get("calories", 0)) / 160
            - float(row.get("cholesterol", 0)) / 60
        )

        if mode == "cholesterol":
            return base + float(row.get("fiber", 0)) * 2.0 - float(row.get("cholesterol", 0)) / 12 - float(row.get("sat_fat", 0)) * 3
        if mode == "diabetes":
            return base + float(row.get("fiber", 0)) * 3.0 + float(row.get("protein", 0)) - float(row.get("sugar", 0)) * 3
        if mode == "sodium":
            return base - float(row.get("sodium", 0)) * 8
        if mode == "weight_loss":
            return base + float(row.get("protein", 0)) * 1.8 + float(row.get("fiber", 0)) * 2.5 - float(row.get("calories", 0)) / 90
        if mode == "high_protein":
            return base + float(row.get("protein", 0)) * 3 - float(row.get("calories", 0)) / 140
        if mode == "breakfast":
            return base + self._breakfast_name_bonus(str(row.get("food_name_text", "")))
        return base

    def _meal_name_bonus(self, name: str) -> float:
        preferred_terms = [
            "oat",
            "yogurt",
            "salad",
            "soup",
            "chicken breast",
            "fish",
            "tuna",
            "salmon",
            "rice cooked",
            "brown rice cooked",
            "wild rice cooked",
            "beans",
            "lentil",
            "vegetable",
            "fruit",
            "egg",
        ]
        return sum(4.0 for term in preferred_terms if re.search(self._term_regex(term), name))

    def _breakfast_name_bonus(self, name: str) -> float:
        breakfast_terms = ["oat", "yogurt", "cereal", "egg", "fruit", "banana", "rice soup"]
        return sum(8.0 for term in breakfast_terms if re.search(self._term_regex(term), name))

    def _term_regex(self, term: str) -> str:
        escaped = re.escape(term.lower())
        return rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"

    def _format_food_row(self, row: pd.Series) -> str:
        name = str(row.get("food_name", "")).strip()
        calories = float(row.get("calories", 0))
        protein = float(row.get("protein", 0))
        fiber = float(row.get("fiber", 0))
        sugar = float(row.get("sugar", 0))
        sat_fat = float(row.get("sat_fat", 0))
        cholesterol = float(row.get("cholesterol", 0))
        sodium_mg = float(row.get("sodium", 0)) * 1000

        return (
            f"{name}: {calories:.0f} kcal, โปรตีน {protein:.1f} g, ไฟเบอร์ {fiber:.1f} g, "
            f"น้ำตาล {sugar:.1f} g, ไขมันอิ่มตัว {sat_fat:.1f} g, "
            f"คอเลสเตอรอล {cholesterol:.1f} mg, โซเดียมประมาณ {sodium_mg:.0f} mg"
        )

    def _answer_calorie_lookup(self, question: str) -> dict[str, Any] | None:
        q = question.lower()
        calorie_keywords = ["แคล", "แคลอ", "kcal", "calorie", "calories", "พลังงาน"]
        if not any(keyword in q for keyword in calorie_keywords):
            return None

        lookup = self._calorie_lookup_terms(q)
        if lookup is None:
            return None

        requested_name, search_terms = lookup
        matches = self._find_calorie_matches(search_terms)
        if not matches:
            return None

        exact = requested_name in {match["food_item"].lower() for match in matches}
        heading = (
            f"ข้อมูลแคลอรีของ {requested_name} จากฐานข้อมูลที่ระบบโหลดไว้เท่านั้น:"
            if exact
            else (
                f"ยังไม่พบรายการ '{requested_name}' ตรง ๆ ในฐานข้อมูลที่ระบบโหลดไว้ "
                "ผมจึงไม่ประเมินเอง และแสดงเฉพาะรายการใกล้เคียงที่มีในฐานข้อมูลดังนี้:"
            )
        )
        lines = [heading]
        for match in matches[:4]:
            lines.append(f"- {match['food_item']}: {match['calories_text']}")

        return {
            "question": question,
            "intent": "calorie_lookup",
            "answer": "\n".join(lines),
            "sources": [
                {
                    "table": match["table"],
                    "row_index": match["row_index"],
                    "retrieved_from": "tabular_lookup",
                    "method": "calorie_name_lookup",
                    "food_item": match["food_item"],
                }
                for match in matches[:4]
            ],
        }

    def _calorie_lookup_terms(self, q: str) -> tuple[str, list[str]] | None:
        food_df = self.loaded_tables.get("food_dataset_with_risk.csv")
        if food_df is None or "food_name" not in food_df.columns:
            return None

        food_names = food_df["food_name"].dropna().astype(str).unique().tolist()
        cleaned = re.sub(r"(กี่|เท่าไหร่|เท่าไร|มี|แคลอรี่|แคลอรี|แคล|kcal|calories|calorie|พลังงาน|ครับ|ค่ะ|ไหม|มั้ย)", " ", q)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return None

        fuzzy_matches = process.extract(cleaned, food_names, limit=3)
        terms = [item[0] for item in fuzzy_matches if item[1] >= 70]
        if not terms:
            return None
        return cleaned, terms

    def _find_calorie_matches(self, search_terms: list[str]) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []

        food_df = self.loaded_tables.get("food_dataset_with_risk.csv")
        if food_df is not None and "food_name" in food_df.columns:
            work = food_df.reset_index(names="row_index").copy()
            work["food_name_text"] = work["food_name"].fillna("").astype(str).str.lower()
            work["calories"] = pd.to_numeric(work["calories"], errors="coerce").fillna(0)
            work = work[work["calories"] > 0]
            for term in search_terms:
                term_words = [word for word in term.lower().split() if word]
                if not term_words:
                    continue
                mask = pd.Series(True, index=work.index)
                for word in term_words:
                    mask &= work["food_name_text"].str.contains(re.escape(word), regex=True, na=False)
                for _, row in work[mask].head(2).iterrows():
                    matches.append(
                        {
                            "table": "food_dataset_with_risk.csv",
                            "row_index": int(row["row_index"]),
                            "food_item": str(row["food_name"]),
                            "calories_text": f"{float(row['calories']):.0f} kcal ตาม serving/record ใน dataset",
                        }
                    )

        calories_df = self.loaded_tables.get("calories.csv")
        if calories_df is not None and "FoodItem" in calories_df.columns:
            work = calories_df.reset_index(names="row_index").copy()
            work["food_item_text"] = work["FoodItem"].fillna("").astype(str).str.lower()
            for term in search_terms:
                term_words = [word for word in term.lower().split() if word]
                if not term_words:
                    continue
                mask = pd.Series(True, index=work.index)
                for word in term_words:
                    mask &= work["food_item_text"].str.contains(re.escape(word), regex=True, na=False)
                for _, row in work[mask].head(2).iterrows():
                    matches.append(
                        {
                            "table": "calories.csv",
                            "row_index": int(row["row_index"]),
                            "food_item": str(row["FoodItem"]),
                            "calories_text": f"{row.get('Cals_per100grams', '')} ต่อ 100 g",
                        }
                    )

        deduped: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for match in matches:
            key = (match["table"], match["food_item"].lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(match)
        return deduped[:6]

    def _answer_high_cholesterol_examples(self, question: str) -> dict[str, Any] | None:
        q = question.lower()
        cholesterol_keywords = ["คอเลสเตอรอล", "cholesterol"]
        example_keywords = ["ตัวอย่าง", "มีอะไรบ้าง", "อะไรบ้าง", "example", "examples"]
        if not any(keyword in q for keyword in cholesterol_keywords):
            return None
        if not any(keyword in q for keyword in example_keywords):
            return None

        df = self.loaded_tables.get("food_dataset_with_risk.csv")
        if df is None or df.empty or "food_name" not in df.columns or "cholesterol" not in df.columns:
            return None

        work = df[["food_name", "cholesterol"]].copy()
        work["cholesterol_num"] = work["cholesterol"].apply(self._to_float)
        work = work.dropna(subset=["food_name", "cholesterol_num"])
        work = work[work["cholesterol_num"] > 0].sort_values("cholesterol_num", ascending=False)

        top = work.head(5)
        if top.empty:
            return None

        lines = ["ตัวอย่างอาหารที่มีคอเลสเตอรอลสูงจาก food_dataset_with_risk.csv เท่านั้น:"]
        for _, row in top.iterrows():
            lines.append(f"- {str(row['food_name']).strip()}: {row['cholesterol_num']:.1f}")

        return {
            "question": question,
            "intent": "cholesterol_examples",
            "answer": "\n".join(lines),
            "sources": [
                {
                    "table": "food_dataset_with_risk.csv",
                    "retrieved_from": "knowledge",
                    "method": "tabular_top_cholesterol",
                }
            ],
        }

    def _answer_sugar_limit(self, question: str) -> dict[str, Any] | None:
        q = question.lower()
        if "น้ำตาล" not in q and "sugar" not in q:
            return None

        rules_df = self.loaded_tables.get("dga_rules_df.csv")
        standards_df = self.loaded_tables.get("dga_standard_df.csv")
        if rules_df is None or standards_df is None:
            return None

        rule_match = rules_df[
            rules_df["rule_name"].astype(str).str.contains("sugar", case=False, na=False)
            | rules_df["condition"].astype(str).str.contains("sugar", case=False, na=False)
        ]
        standard_match = standards_df[
            standards_df["metric"].astype(str).str.contains("sugar", case=False, na=False)
            | standards_df["category"].astype(str).str.contains("sugar", case=False, na=False)
        ]

        if rule_match.empty and standard_match.empty:
            return None

        sources = [
            {"table": "dga_rules_df.csv", "retrieved_from": "knowledge", "method": "tabular_sugar_lookup"},
            {"table": "dga_standard_df.csv", "retrieved_from": "knowledge", "method": "tabular_sugar_lookup"},
        ]

        if "ต่อวัน" in q or "per day" in q or "daily" in q:
            return {
                "question": question,
                "intent": "guideline",
                "answer": (
                    "จาก dga_rules_df.csv ที่ระบบโหลดไว้ ผมพบเกณฑ์น้ำตาลเติมเพิ่มต่อมื้อไม่เกิน 10 กรัมต่อมื้อครับ "
                    "แต่ยังไม่พบเกณฑ์น้ำตาลต่อวันโดยตรงในฐานข้อมูลชุดนี้ จึงไม่เดาเพิ่มจากภายนอก"
                ),
                "sources": sources,
            }

        rule_row = rule_match.iloc[0].to_dict()
        unit = str(rule_row.get("unit", "")).strip()
        condition = str(rule_row.get("condition", "")).strip()
        value = condition.split("<=")[-1].strip() if "<=" in condition else condition

        return {
            "question": question,
            "intent": "guideline",
            "answer": f"จาก dga_rules_df.csv ที่ระบบโหลดไว้ น้ำตาลเติมเพิ่มต่อมื้อควรไม่เกิน {value} {unit} ครับ",
            "sources": sources,
        }

    def _answer_sodium_limit(self, question: str) -> dict[str, Any] | None:
        q = question.lower()
        if "โซเดียม" not in q and "sodium" not in q:
            return None

        df = self.loaded_tables.get("dga_rules_df.csv")
        if df is None or df.empty:
            return None

        match = df[
            df["rule_name"].astype(str).str.contains("sodium", case=False, na=False)
            | df["condition"].astype(str).str.contains("sodium", case=False, na=False)
        ]
        if match.empty:
            return None

        row = match.iloc[0].to_dict()
        condition = str(row.get("condition", "")).strip()
        unit = str(row.get("unit", "")).strip()
        value = condition.split("<")[-1].strip() if "<" in condition else condition

        return {
            "question": question,
            "intent": "guideline",
            "answer": f"จาก dga_rules_df.csv ที่ระบบโหลดไว้ โซเดียมต่อวันควรต่ำกว่า {value} {unit} ครับ",
            "sources": [
                {
                    "table": "dga_rules_df.csv",
                    "retrieved_from": "knowledge",
                    "method": "tabular_sodium_lookup",
                }
            ],
        }
