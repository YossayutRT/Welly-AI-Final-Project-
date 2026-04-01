from __future__ import annotations

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
        self.llm: ChatGroq | None = None

        self.rag_prompt = PromptTemplate.from_template(
            """
You are Welly AI nutrition assistant for human nutrition.
Answer in Thai with a natural, polite chat tone.
Use ONLY the provided context and never use outside knowledge.

When context is sufficient:
- Answer directly and clearly in normal chat style.
- Keep it concise and practical.

When context is insufficient:
- Reply exactly:
"ตอนนี้ผมยังไม่มีข้อมูลที่เพียงพอเกี่ยวกับ '{question}'\nหากคุณต้องการ ผมช่วยแนะนำคำถามด้านโภชนาการหรือสูตรอาหารที่ใกล้เคียงให้ได้ครับ"

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

        index_dir = self.settings.knowledge_index_dir
        index_faiss = index_dir / "index.faiss"
        index_pkl = index_dir / "index.pkl"
        if index_faiss.exists() and index_pkl.exists():
            return FAISS.load_local(
                str(index_dir),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )

        documents = []
        for table_name, df in self.loaded_tables.items():
            for idx, row in df.iterrows():
                text = self._row_to_text(table_name, row)
                documents.append(
                    Document(
                        page_content=text,
                        metadata={"table": table_name, "row_index": int(idx)},
                    )
                )

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        split_docs = splitter.split_documents(documents)

        vectorstore = FAISS.from_documents(split_docs, self.embeddings)
        index_dir.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(index_dir))
        return vectorstore

    def _load_recipe_vectorstore(self) -> FAISS:
        assert self.embeddings is not None

        index_dir = self.settings.recipes_index_dir
        index_faiss = index_dir / "index.faiss"
        index_pkl = index_dir / "index.pkl"
        if index_faiss.exists() and index_pkl.exists():
            return FAISS.load_local(
                str(index_dir),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )

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
        split_docs = splitter.split_documents(recipe_docs)
        vectorstore = FAISS.from_documents(split_docs, self.embeddings)
        index_dir.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(index_dir))
        return vectorstore

    def _load_calories_vectorstore(self) -> FAISS:
        assert self.embeddings is not None

        index_dir = self.settings.calories_index_dir
        index_faiss = index_dir / "index.faiss"
        index_pkl = index_dir / "index.pkl"
        if index_faiss.exists() and index_pkl.exists():
            return FAISS.load_local(
                str(index_dir),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )

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

        vectorstore = FAISS.from_documents(calorie_docs, self.embeddings)
        index_dir.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(index_dir))
        return vectorstore

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
            f"ตอนนี้ผมยังไม่มีข้อมูลที่เพียงพอเกี่ยวกับ '{question}'\n"
            "หากคุณต้องการ ผมช่วยแนะนำคำถามด้านโภชนาการหรือสูตรอาหารที่ใกล้เคียงให้ได้ครับ"
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
            "ตอนนี้ระบบยังสรุปคำตอบด้วย LLM ไม่ได้ แต่ผมพบข้อมูลที่เกี่ยวข้องดังนี้ครับ:",
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

    def _answer_high_cholesterol_examples(self, question: str) -> dict[str, Any] | None:
        q = question.lower()
        cholesterol_keywords = ["คอเลสเตอรอล", "cholesterol"]
        example_keywords = ["ตัวอย่าง", "มีอะไรบ้าง", "อะไรบ้าง", "high", "สูง"]
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

        lines = ["ตัวอย่างอาหารที่มีคอเลสเตอรอลสูง (จาก dataset):"]
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
                    "จากชุดความรู้ที่มีตอนนี้ ผมพบเกณฑ์น้ำตาลเติมเพิ่มต่อมื้อไม่เกิน 10 กรัมต่อมื้อครับ "
                    "แต่ยังไม่พบเกณฑ์น้ำตาลต่อวันโดยตรงในฐานข้อมูลชุดนี้"
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
            "answer": f"น้ำตาลเติมเพิ่มต่อมื้อควรไม่เกิน {value} {unit} ครับ",
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
            "answer": f"โซเดียมต่อวันควรต่ำกว่า {value} {unit} ครับ",
            "sources": [
                {
                    "table": "dga_rules_df.csv",
                    "retrieved_from": "knowledge",
                    "method": "tabular_sodium_lookup",
                }
            ],
        }
