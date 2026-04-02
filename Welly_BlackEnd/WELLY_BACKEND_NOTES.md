# Welly Backend Notes

ไฟล์นี้ใช้เป็นโน้ตอธิบายฝั่ง backend ของโปรเจกต์ Welly AI แบบละเอียด

อ้างอิงโค้ดหลักจาก:
- [main.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/main.py)
- [config.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/config.py)
- [schemas.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/schemas.py)
- [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py)
- [requirements.txt](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/requirements.txt)

## ภาพรวม

backend ของโปรเจกต์นี้เป็น FastAPI application ที่ทำหน้าที่เป็นตัวกลางระหว่าง frontend กับระบบ RAG

หน้าที่หลักของ backend คือ:

1. โหลด config และ secret ที่จำเป็น
2. โหลด dataset ที่เกี่ยวข้องกับโภชนาการ
3. โหลดหรือสร้าง FAISS index
4. โหลด embedding model
5. โหลด Groq LLM ถ้ามี API key
6. เปิด API ให้ frontend เรียก
7. รับคำถามแล้วส่งต่อเข้า logic ของ `WellyRAGService`
8. คืนคำตอบพร้อม source metadata กลับไป

## เทคโนโลยีที่ใช้

- `FastAPI` สำหรับสร้าง API
- `Pydantic` สำหรับ request/response schema
- `pandas` สำหรับอ่าน CSV
- `LangChain` สำหรับ document, prompt, vectorstore, embeddings
- `FAISS` สำหรับ vector search
- `sentence-transformers` / `HuggingFaceEmbeddings` สำหรับ embedding
- `ChatGroq` สำหรับ LLM generation
- `rapidfuzz` สำหรับ fuzzy matching ชื่ออาหาร

## โครงสร้างไฟล์

### `app/main.py`

หน้าที่:
- สร้าง FastAPI app
- ตั้งค่า CORS
- จัดการ startup ผ่าน lifespan
- expose API endpoints

### `app/config.py`

หน้าที่:
- โหลด environment variables
- สร้าง object `Settings`
- resolve path ของ model และ project data

### `app/schemas.py`

หน้าที่:
- กำหนดรูปแบบข้อมูล request/response ของ API

### `app/service.py`

หน้าที่:
- เป็นหัวใจหลักของ backend
- รวม logic ทั้งหมดของ RAG service

### `requirements.txt`

หน้าที่:
- ระบุ dependency ที่ backend ต้องใช้

## การทำงานระดับสูงของ Backend

flow หลักของ backend มีลำดับนี้:

1. `uvicorn app.main:app` เริ่มรัน server
2. `main.py` เรียก `get_settings()`
3. `main.py` สร้าง `rag_service = WellyRAGService(settings)`
4. ตอน startup จะเรียก `rag_service.initialize()`
5. service จะโหลด data, embeddings, vectorstores, และ LLM
6. เมื่อ frontend ยิง `/api/chat` ระบบจะเรียก `rag_service.ask()`
7. service จะตัดสินใจว่าใช้ direct handler, retrieval fallback, หรือ LLM generation
8. backend ส่ง JSON response กลับไปให้ frontend

## อธิบายทีละไฟล์

### 1. `app/main.py`

#### หน้าที่หลัก

ไฟล์นี้เป็น entry point ของ FastAPI app

สิ่งที่เกิดขึ้นในไฟล์นี้:
- import `get_settings`
- import schema
- import `WellyRAGService`
- สร้าง object กลางของ service
- สร้าง app และ route

#### lifespan

ใช้ `@asynccontextmanager` เพื่อทำ startup logic

ช่วง startup:
- เรียก `rag_service.initialize()`
- ถ้าเจอ exception จะเก็บไว้ใน `rag_service.startup_error`

ประโยชน์:
- ทำให้ backend โหลด model และ vector store แค่ครั้งเดียวตอนเปิดระบบ
- route หลังจากนั้นใช้งาน object เดิมได้เลย

#### endpoints ที่มี

`GET /health`
- ใช้เช็กสุขภาพระบบ
- คืนว่า backend พร้อมไหม
- คืนว่า LLM เปิดไหม
- คืนชื่อ model และ startup error ถ้ามี

`POST /api/chat`
- ใช้รับคำถามจาก frontend
- ถ้า service ยังไม่พร้อมจะคืน `503`
- ถ้าพร้อมจะเรียก `rag_service.ask()`

`GET /api/suggestions`
- ใช้แนะนำชื่ออาหารที่พิมพ์ใกล้เคียง
- รับ query string ชื่อ `query`

### 2. `app/config.py`

ไฟล์นี้เป็นศูนย์รวม config ของ backend

#### สิ่งที่ไฟล์นี้ทำ

- อ่านค่าจาก environment variables
- โหลด `.env` อัตโนมัติ
- สร้าง `Settings` dataclass
- resolve path ของ model cache

#### ฟังก์ชันสำคัญ

`_env_bool()`
- ใช้แปลง env string ให้เป็น boolean

`_env_list()`
- ใช้แปลง env ที่เป็น comma-separated string ให้เป็น list

`_resolve_snapshot_path(model_name)`
- พยายามหา model snapshot จาก Hugging Face cache
- ช่วยให้ backend รันแบบ offline ได้

`_resolve_model_path(model_name)`
- ถ้ามี `WELLY_MODEL_PATH` จะใช้ path นั้นก่อน
- ถ้าไม่มีและ `model_name` เป็น path อยู่แล้วก็ใช้ path นั้น
- ถ้าไม่ใช่จะลอง resolve จาก cache

#### `Settings`

เก็บ config หลักทั้งหมด เช่น:
- `project_root`
- `notebooks_dir`
- `data_dir`
- `outputs_dir`
- `knowledge_dir`
- `model_name`
- `model_path`
- `llm_model`
- `groq_api_key`
- `embeddings_local_only`
- `default_top_k`
- `allowed_origins`

#### จุดสำคัญ

backend จะโหลด `.env` จากได้ 2 ที่:
- root project
- `Welly_BlackEnd/.env`

นี่ทำให้ deployment และ local dev ยืดหยุ่นขึ้น

### 3. `app/schemas.py`

ไฟล์นี้นิยามรูปแบบข้อมูลที่ API รับและส่ง

#### `SourceItem`

ใช้เก็บ metadata ของแหล่งข้อมูล เช่น:
- `table`
- `row_index`
- `retrieved_from`
- `method`
- `source`
- `title`
- `food_item`
- `doc_type`

#### `ChatRequest`

request body ของ `/api/chat`

field:
- `message`
- `k`

#### `ChatResponse`

response ของ `/api/chat`

field:
- `question`
- `intent`
- `answer`
- `sources`
- `llm_enabled`
- `used_context_fallback`

#### `HealthResponse`

response ของ `/health`

field:
- `status`
- `ready`
- `llm_enabled`
- `model_name`
- `model_path`
- `llm_model`
- `startup_error`
- `loaded_tables`

### 4. `app/service.py`

ไฟล์นี้เป็น core ของระบบทั้งหมด

class หลักคือ `WellyRAGService`

## โครงของ `WellyRAGService`

### `__init__`

ทำหน้าที่:
- รับ `settings`
- เตรียม lock
- ตั้งค่าตัวแปรสถานะ เช่น `ready`, `startup_error`
- สร้างที่เก็บ object ต่าง ๆ เช่น vectorstore และ llm
- สร้าง prompt กลางชื่อ `rag_prompt`

prompt นี้กำหนดกติกาหลัก:
- ตอบเป็นภาษาไทย
- ใช้เฉพาะ context ที่ให้มา
- ถ้าข้อมูลไม่พอให้ตอบ fallback
- ถ้านอกขอบเขตให้ปฏิเสธ

### `llm_enabled`

เป็น property ที่ใช้เช็กว่า `self.llm` ถูกสร้างสำเร็จหรือยัง

### `initialize()`

เป็น startup method ที่สำคัญที่สุด

สิ่งที่ method นี้ทำ:

1. โหลดตารางทั้งหมดด้วย `_load_tables()`
2. โหลด embedding model ด้วย `_load_embeddings()`
3. โหลดหรือสร้าง knowledge vector store
4. โหลดหรือสร้าง recipe vector store
5. โหลดหรือสร้าง calories vector store
6. โหลด LLM ด้วย `_build_llm()`
7. ตั้ง `ready = True`

จุดสำคัญ:
- method นี้ใช้ lock ป้องกันการ initialize ซ้ำหลายรอบ

### `health()`

คืนสถานะของระบบในรูป dict

ใช้สำหรับ route `/health`

### `ask(question, k=None)`

เป็น method สำคัญที่สุดของ backend

flow ของ method นี้:

1. ตรวจว่าระบบพร้อมหรือยัง
2. strip คำถาม
3. ถ้าคำถามนอกขอบเขต ให้ตอบปฏิเสธทันที
4. ลอง direct handlers ก่อน
5. ถ้าไม่เข้า direct handler ให้ detect intent
6. collect context จาก vector stores
7. ถ้า context ไม่พอ ให้ fallback
8. ถ้าไม่มี LLM ให้ render context fallback
9. ถ้ามี LLM ให้สร้าง prompt แล้วเรียก `self.llm.invoke()`
10. clean คำตอบแล้วคืนกลับ

ดังนั้น `ask()` คือ orchestrator ของทั้งระบบ

### `suggest_food_names(user_text)`

ใช้ fuzzy search หา food names ที่ใกล้เคียงจาก `food_dataset_with_risk.csv`

เหมาะกับ:
- autocomplete
- spell correction

## ส่วน Loading Data และ Index

### `_load_tables()`

หน้าที่:
- โหลด CSV หลักทั้งหมด

ชุดข้อมูลที่โหลด:
- knowledge tables
- `user_health_knowledge.csv`
- `food_dataset_with_risk.csv`

ถ้าไฟล์ขาด:
- raise `FileNotFoundError`

### `_load_embeddings()`

หน้าที่:
- สร้าง `HuggingFaceEmbeddings`
- ใช้ `intfloat/multilingual-e5-small` ตาม config

จุดสำคัญ:
- ถ้า `embeddings_local_only` เป็นจริง จะใช้ `local_files_only`
- รองรับการโหลดจาก local snapshot path

### `_load_knowledge_vectorstore()`

หน้าที่:
- โหลดหรือสร้าง FAISS knowledge index

ถ้ามีไฟล์ index แล้ว:
- ใช้ `FAISS.load_local()`

ถ้ายังไม่มี:
- แปลง row ของทุก table เป็น `Document`
- split เป็น chunk
- สร้าง FAISS ใหม่
- save ลงดิสก์

### `_load_recipe_vectorstore()`

หน้าที่:
- โหลดหรือสร้าง index สำหรับ recipe corpus

ข้อมูลมาจาก:
- `13k-recipes.csv`

### `_load_calories_vectorstore()`

หน้าที่:
- โหลดหรือสร้าง index สำหรับ calorie corpus

ข้อมูลมาจาก:
- `calories.csv`

### `_build_llm()`

หน้าที่:
- ถ้ามี `groq_api_key` จะสร้าง `ChatGroq`
- ถ้าไม่มี จะคืน `None`

ผลคือ backend รองรับ 2 โหมด:
- `LLM mode`
- `retrieval fallback mode`

## ส่วน Data Transformation

### `_row_to_text(table_name, row)`

หน้าที่:
- แปลงข้อมูลแต่ละ row จาก CSV ให้เป็นข้อความ

เหตุผล:
- vector embedding ทำงานกับ text ได้ดีที่สุด
- ตารางแต่ละชนิดจึงต้องถูกแปลงให้เป็นประโยคสั้น ๆ ที่มี semantic meaning

ตัวอย่าง:
- `standard_df.csv` กลายเป็นข้อความแนว nutrition standard
- `food_dataset_with_risk.csv` กลายเป็นข้อความแนว food nutrition + risk
- `user_health_knowledge.csv` กลายเป็นข้อความแนว profile สุขภาพ

นี่คือจุดสำคัญมากของคุณภาพ retrieval

## ส่วน Retrieval

### `_collect_context(question, intent, k)`

หน้าที่:
- เลือกว่าจะค้นจาก store ไหนบ้าง
- รวมผลลัพธ์จากหลาย store
- boost score ตาม intent และชนิด table
- dedupe hits
- sort ตาม score

logic สำคัญ:
- ทุกคำถามมี knowledge store เป็นฐาน
- ถ้า intent เป็น `recipe` จะเพิ่ม recipe store
- ถ้า intent เป็น `calorie` จะเพิ่ม calories store
- ถ้าเป็น `guideline` จะ boost table กลุ่ม guideline

### `_search_scored(vectorstore, query, k)`

หน้าที่:
- เรียก similarity search แบบมี score
- ถ้าล้มเหลวจะ fallback ไป similarity search ปกติ

### `_dedupe_hits(items)`

หน้าที่:
- เอา hit ที่ซ้ำกันออก
- ลดปัญหา context ซ้ำใน prompt

## ส่วน Intent / Guardrails / Cleanup

### `_detect_intent(question)`

intent ที่รองรับ:
- `calorie`
- `recipe`
- `guideline`
- `general`

วิธีทำ:
- ใช้ keyword-based routing

### `_is_out_of_scope(question)`

หน้าที่:
- กรองคำถามเรื่องอาหารสัตว์ เช่น dog food / cat food

### `_default_fallback(question)`

หน้าที่:
- สร้างข้อความ fallback เมื่อข้อมูลไม่พอ

### `_clean_chat_answer(text, intent, question)`

หน้าที่:
- ทำความสะอาดคำตอบจาก LLM
- เอา apology ที่ฟุ่มเฟือยออก
- จัดการกรณี LLM ส่ง JSON แทน text

### `_render_context_fallback(question, collected, llm_error=None)`

หน้าที่:
- ใช้แสดงผลแบบ retrieval-only เมื่อ LLM ใช้ไม่ได้
- ดึง snippet จาก context มาแสดงแทน

## ส่วน Direct Handlers

backend นี้ไม่ใช่ pure RAG 100% เพราะมี direct handler บางตัว

### `_answer_high_cholesterol_examples()`

หน้าที่:
- ถ้าผู้ใช้ถามตัวอย่างอาหารคอเลสเตอรอลสูง
- จะตอบจาก table โดยตรง

ข้อดี:
- ตรงและ deterministic

### `_answer_sugar_limit()`

หน้าที่:
- ตอบคำถามเรื่องน้ำตาลจาก table ที่เกี่ยวข้อง

จุดสำคัญ:
- ถ้าถาม “ต่อวัน” ตอนนี้ระบบตอบแบบ conservative ว่า dataset พบเกณฑ์ต่อมื้อ แต่ยังไม่พบต่อวันโดยตรง

### `_answer_sodium_limit()`

หน้าที่:
- ตอบคำถามเรื่องโซเดียมจาก `dga_rules_df.csv`

## สรุป Request Lifecycle ของ `/api/chat`

ลำดับจริงเวลา frontend ยิงคำถาม:

1. frontend ส่ง `message` ไปที่ `/api/chat`
2. FastAPI route รับ `ChatRequest`
3. route เรียก `rag_service.ask(message, k)`
4. service ตรวจ out-of-scope
5. service ตรวจ direct handlers
6. service detect intent
7. service collect context จาก FAISS
8. ถ้าคะแนนไม่พอ -> fallback
9. ถ้ามี LLM -> สร้าง prompt และ invoke Groq
10. ส่ง `ChatResponse` กลับ frontend

## ความสัมพันธ์กับ Notebook

backend นี้ไม่ได้เริ่มจากศูนย์ แต่ย้ายแนวคิดมาจาก [Welly_AI_RAG.ipynb](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Notebooks/Welly_AI_RAG.ipynb)

สิ่งที่ย้ายมาหลัก ๆ:
- `row_to_text`
- intent detection
- retrieval logic
- direct handlers
- prompt
- recipe / calorie vector stores

ดังนั้น backend คือเวอร์ชันที่แปลง notebook logic ให้กลายเป็น API service

## Environment Variables ที่สำคัญ

ตัวอย่างค่า:

```env
GROQ_API_KEY=your_real_key
WELLY_LLM_MODEL=llama-3.1-8b-instant
WELLY_MODEL_NAME=intfloat/multilingual-e5-small
WELLY_EMBEDDINGS_LOCAL_ONLY=true
WELLY_TOP_K=4
WELLY_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

ตัวแปรสำคัญ:

- `GROQ_API_KEY`
  ใช้เปิด LLM generation

- `WELLY_LLM_MODEL`
  กำหนด model ของ Groq

- `WELLY_MODEL_NAME`
  กำหนด embedding model

- `WELLY_MODEL_PATH`
  บังคับใช้ local path ของ embedding model ถ้าต้องการ

- `WELLY_EMBEDDINGS_LOCAL_ONLY`
  ใช้กรณีอยากรันแบบ offline

- `WELLY_TOP_K`
  จำนวนเอกสารที่ดึงมาเป็น context

- `WELLY_ALLOWED_ORIGINS`
  ใช้ตั้งค่า CORS

## คำสั่งรัน Backend

```bash
cd Welly_BlackEnd
python -m pip install -r requirements.txt
แ
```

## จุดเด่นของ Backend

- แยก layer ชัดเจนระหว่าง route, config, schema, service
- รองรับ LLM mode และ fallback mode
- รองรับหลาย vector stores
- reuse logic จาก notebook ได้ดี
- มี health endpoint ทำให้ frontend เช็กสถานะได้ง่าย

## จุดที่ควรจำเวลาอธิบาย

- backend นี้เป็น FastAPI wrapper รอบระบบ RAG
- หัวใจจริงอยู่ที่ `WellyRAGService`
- มี hybrid behavior เพราะมี direct handlers ก่อน retrieval เต็มรูป
- ถ้าไม่มี `GROQ_API_KEY` ระบบยังทำงานได้ แต่จะตอบแบบ fallback มากขึ้น

## ถ้าจะพรีเซนต์สั้น ๆ

พูดได้ว่า:

`backend ของ Welly AI พัฒนาด้วย FastAPI โดยแยก route, schema, config และ service ออกจากกันอย่างชัดเจน ตัว service จะโหลดข้อมูลโภชนาการและดัชนี FAISS ไว้ตั้งแต่ตอน startup จากนั้นเมื่อมีคำถามเข้ามา ระบบจะทำ intent detection, retrieval จาก vector store, สร้าง prompt และส่งเข้า Groq LLM เพื่อสร้างคำตอบ พร้อมคืน source metadata กลับไปให้ frontend แสดงผล`
