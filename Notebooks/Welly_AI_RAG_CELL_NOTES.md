# Welly AI RAG Code Cell Notes

ไฟล์นี้เป็นโน้ตอธิบาย [Welly_AI_RAG.ipynb](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Notebooks/Welly_AI_RAG.ipynb) โดยเน้นเฉพาะ `code cells`

เป้าหมายของโน้ตนี้คือ:
- อธิบายว่าแต่ละ code cell ทำอะไร
- บอกว่า cell นั้นอยู่ตรงไหนของ RAG pipeline
- แนะนำว่าถ้าจะพรีเซนต์ cell นั้นควรพูดยังไง

## ภาพรวมของ RAG ใน Notebook นี้

flow หลักของ notebook นี้คือ:

1. เตรียม environment และ token
2. โหลดไฟล์ข้อมูลจากโปรเจกต์
3. แปลงแต่ละ row ให้เป็น document text
4. split text เป็น chunks
5. สร้าง embedding
6. สร้างหรือโหลด FAISS vector store
7. รับคำถาม
8. หา context ที่เกี่ยวข้อง
9. สร้าง prompt
10. ส่งเข้า LLM
11. คืนคำตอบพร้อม source

แต่ notebook นี้ยังมี `helper logic` บางส่วนใน `ask_welly_rag()` จึงเป็น `RAG-driven with direct handlers` ไม่ใช่ pure RAG ล้วน

## ลำดับที่แนะนำเวลาพรีเซนต์

ถ้าจะเล่าให้กรรมการหรืออาจารย์เข้าใจง่าย ให้เรียงตามนี้:

1. Cell 10, 12: เราโหลดข้อมูลจากไหน
2. Cell 16, 17: เราแปลงข้อมูลเป็น documents ยังไง
3. Cell 19: เรา split ข้อความยังไง
4. Cell 21: เราใช้ embedding model อะไร และเก็บลง FAISS ยังไง
5. Cell 23: เราทดสอบ retrieval ยังไง
6. Cell 27: เราเตรียม LLM และ prompt ยังไง
7. Cell 29: query วิ่งผ่านระบบยังไง
8. Cell 34, 35: เราแยก recipe และ calories เป็นอีก 2 store ยังไง
9. Cell 30, 36-39, 41: เราทดสอบผลลัพธ์ยังไง

## Mapping กับ RAG แบบมาตรฐาน

- Data loading: Cell 10, 12
- Document creation: Cell 16, 17
- Chunking: Cell 19
- Embedding: Cell 21
- Vector database: Cell 21, 35
- Retrieval: Cell 23, 25, 29
- Prompting: Cell 27, 29
- Generation: Cell 27, 29
- Evaluation / demo: Cell 30, 36, 37, 38, 39, 41

## Code Cell Notes

### Cell 1
หน้าที่:
- ติดตั้ง package ที่จำเป็นด้วย `!pip`

เกี่ยวกับ RAG ตรงไหน:
- เป็นขั้นเตรียม environment

จุดสำคัญ:
- ใช้ install library หลักของ LangChain, FAISS, sentence-transformers, และ Groq

พรีเซนต์ยังไง:
- พูดว่า cell นี้ใช้เตรียมเครื่องมือทั้งหมดที่ระบบ RAG ต้องใช้ก่อน เช่น embedding, vector search, และ LLM integration

### Cell 2
หน้าที่:
- ติดตั้ง package แบบ `%pip`

เกี่ยวกับ RAG ตรงไหน:
- เป็นขั้นเตรียม environment เหมือน cell 1

จุดสำคัญ:
- ใน Jupyter มักใช้ `%pip` ได้เสถียรกว่า

พรีเซนต์ยังไง:
- พูดสั้น ๆ ว่า notebook นี้มี cell สำหรับติดตั้ง dependency ให้พร้อมก่อนเริ่ม pipeline

### Cell 3
หน้าที่:
- แสดง Python executable ที่ notebook ใช้อยู่

เกี่ยวกับ RAG ตรงไหน:
- ไม่ใช่ logic RAG โดยตรง
- เป็น debugging support

จุดสำคัญ:
- ใช้เช็กว่า notebook ใช้ environment ไหน

พรีเซนต์ยังไง:
- ถ้าไม่จำเป็นไม่ต้องเล่าลึก
- พูดได้ว่าใช้ตรวจ environment เพื่อให้แน่ใจว่า package ที่ติดตั้งถูกใช้งานจริง

### Cell 4
หน้าที่:
- ทดสอบ import library สำคัญ

เกี่ยวกับ RAG ตรงไหน:
- เป็น smoke test ก่อนเริ่ม pipeline

จุดสำคัญ:
- ถ้า cell นี้รันผ่าน แปลว่า dependency หลักพร้อมแล้ว

พรีเซนต์ยังไง:
- พูดว่าเราเช็กก่อนว่า library สำหรับ retrieval, embeddings, และ LLM พร้อมใช้งาน

### Cell 6
หน้าที่:
- import library ทั้งหมดที่ notebook ใช้

กลุ่ม library สำคัญ:
- `pandas`
- `Document`
- `HuggingFaceEmbeddings`
- `FAISS`
- `RecursiveCharacterTextSplitter`
- `ChatGroq`
- `PromptTemplate`

เกี่ยวกับ RAG ตรงไหน:
- ครอบคลุมทั้ง ingestion, retrieval, และ generation

พรีเซนต์ยังไง:
- พูดว่า cell นี้เป็นการรวมเครื่องมือหลักของระบบ เช่น data processing, embedding, vector database, และ LLM

### Cell 8
หน้าที่:
- โหลด `LC_TOKEN` และ `GROQ_TOKEN`
- ถ้าไม่มี `GROQ_TOKEN` ให้ user กรอกเอง
- map ไปเป็น `GROQ_API_KEY`

เกี่ยวกับ RAG ตรงไหน:
- เป็นส่วนเตรียม LLM access

จุดสำคัญ:
- ถ้าไม่มี Groq token ระบบยัง retrieval ได้ แต่ยัง generate คำตอบเต็มรูปไม่ได้

พรีเซนต์ยังไง:
- พูดว่าเราแยกส่วน secret ออกมา เพื่อให้ notebook ดึง token จาก environment ได้ และพร้อมเชื่อมกับ Groq LLM

### Cell 10
หน้าที่:
- กำหนด path ของข้อมูล
- ระบุ candidate files ที่ระบบต้องใช้
- ตรวจว่าแต่ละไฟล์มีอยู่จริงไหม

ไฟล์หลัก:
- `standard_df.csv`
- `dga_standard_df.csv`
- `dga_rules_df.csv`
- `bmi_standard_df.csv`
- `bmi_rules_df.csv`
- `claim_rules_df.csv`
- `label_required_nutrients_df.csv`
- `serving_size_reference_df.csv`
- `user_health_knowledge.csv`
- `food_dataset_with_risk.csv`

เกี่ยวกับ RAG ตรงไหน:
- เป็น `data source discovery`

พรีเซนต์ยังไง:
- พูดว่าเริ่มจากการระบุ knowledge sources ของระบบก่อน ว่าจะใช้ dataset ไหนเป็นฐานความรู้

### Cell 12
หน้าที่:
- โหลดทุกไฟล์จาก `candidate_files` เข้า `loaded_tables`

ผลลัพธ์สำคัญ:
- ได้ dictionary `loaded_tables`

เกี่ยวกับ RAG ตรงไหน:
- เป็น `data loading`

พรีเซนต์ยังไง:
- พูดว่า cell นี้เป็นขั้น ingestion แรก โดยอ่าน raw CSV ทั้งหมดเข้ามาเป็น DataFrame ก่อน

### Cell 14
หน้าที่:
- preview ข้อมูลตัวอย่างของทุกตาราง

เกี่ยวกับ RAG ตรงไหน:
- เป็น data inspection

จุดสำคัญ:
- ช่วยดู schema และรูปแบบข้อมูลก่อน map เป็น text

พรีเซนต์ยังไง:
- พูดว่าเรา preview data เพื่อทำความเข้าใจ column สำคัญก่อนออกแบบ document text

### Cell 16
หน้าที่:
- นิยาม `row_to_text(table_name, row)`
- แปลง row ของแต่ละตารางให้เป็นข้อความ

เกี่ยวกับ RAG ตรงไหน:
- เป็น `document transformation`

จุดสำคัญ:
- เป็น cell สำคัญมาก เพราะกำหนดว่า embedding จะ “เข้าใจ” row ยังไง
- แต่ละ table ใช้ format ข้อความต่างกัน เพื่อรักษาความหมายของข้อมูล

ตัวอย่าง:
- ตารางเกณฑ์ BMI จะถูกแปลงเป็นข้อความแนว standard/rule
- ตารางอาหารจะถูกแปลงเป็นข้อความแนว nutrition + risk

พรีเซนต์ยังไง:
- พูดว่า vector database ค้นข้อมูลจาก text ไม่ใช่ DataFrame โดยตรง เราเลยต้องออกแบบการแปลง row ให้เป็นประโยคที่สื่อความหมายชัด

### Cell 17
หน้าที่:
- วนทุก table และทุก row
- เรียก `row_to_text()`
- สร้าง `Document` object พร้อม metadata

ผลลัพธ์สำคัญ:
- ได้ list ชื่อ `documents`

metadata ที่เก็บ:
- `table`
- `row_index`

เกี่ยวกับ RAG ตรงไหน:
- เป็นขั้นสร้าง `document corpus`

พรีเซนต์ยังไง:
- พูดว่าแต่ละแถวถูกแปลงเป็น document พร้อม metadata เพื่อให้ภายหลังเรารู้ได้ว่าคำตอบมาจากตารางไหนและแถวไหน

### Cell 19
หน้าที่:
- สร้าง `RecursiveCharacterTextSplitter`
- split `documents` เป็น `split_docs`

parameter:
- `chunk_size=500`
- `chunk_overlap=50`

เกี่ยวกับ RAG ตรงไหน:
- เป็น `chunking`

จุดสำคัญ:
- แม้ข้อมูลแต่ละ row จะไม่ยาวมาก แต่การ split ช่วยให้ retrieval ยืดหยุ่นขึ้น

พรีเซนต์ยังไง:
- พูดว่าเราแบ่ง document เป็น chunks เพื่อให้ vector search หาส่วนที่เกี่ยวข้องที่สุดได้ง่ายขึ้น

### Cell 21
หน้าที่:
- เลือก embedding model
- ตรวจ device
- สร้าง `HuggingFaceEmbeddings`
- โหลดหรือสร้าง FAISS knowledge index

ค่าที่สำคัญ:
- model: `intfloat/multilingual-e5-small`
- vector store: `FAISS`

เกี่ยวกับ RAG ตรงไหน:
- เป็น `embedding + vector database`

จุดสำคัญ:
- ถ้ามี index อยู่แล้วจะโหลด reuse
- ถ้ายังไม่มีจะ build ใหม่จาก `split_docs`

พรีเซนต์ยังไง:
- พูดว่า cell นี้เป็นหัวใจของ retrieval เพราะเรานำ documents ไปแปลงเป็น vector embeddings และเก็บลง FAISS เพื่อให้ค้นแบบ semantic search ได้

### Cell 23
หน้าที่:
- ทดลอง query หลายแบบกับ `vectorstore.similarity_search()`

เกี่ยวกับ RAG ตรงไหน:
- เป็น `retrieval diagnostics`

จุดสำคัญ:
- ใช้ดูว่า top-k ที่ดึงมากลับมาตรงโจทย์ไหม
- เช็กได้ว่าตารางที่ถูกดึงมาเหมาะกับคำถามหรือเปล่า

พรีเซนต์ยังไง:
- พูดว่าเราทดสอบ retrieval แยกก่อนเข้า LLM เพื่อให้มั่นใจว่า context ที่จะส่งให้ model มีคุณภาพ

### Cell 25
หน้าที่:
- สร้าง `retriever = vectorstore.as_retriever(search_kwargs={"k": 4})`

เกี่ยวกับ RAG ตรงไหน:
- เป็น `retriever setup`

จุดสำคัญ:
- กำหนดจำนวนเอกสารที่ดึงเป็น 4

พรีเซนต์ยังไง:
- พูดว่าเรา wrap vector store ให้กลายเป็น retriever เพื่อใช้ในขั้นถามตอบต่อไป

### Cell 27
หน้าที่:
- สร้าง `ChatGroq`
- สร้าง `rag_prompt`

เกี่ยวกับ RAG ตรงไหน:
- เป็น `prompt + generation setup`

จุดสำคัญ:
- prompt บังคับให้ใช้เฉพาะ context
- มี fallback message และ out-of-scope message แบบ fix
- model ที่ใช้คือ `llama-3.1-8b-instant`

พรีเซนต์ยังไง:
- พูดว่าเรากำหนด prompt ให้ LLM ตอบโดยอ้างอิงเฉพาะข้อมูลที่ retrieve มา เพื่อลด hallucination และคุมรูปแบบคำตอบให้เหมาะกับงาน

### Cell 29
หน้าที่:
- เป็น cell สำคัญที่สุดของ notebook
- รวม utility functions และ `ask_welly_rag()`

ฟังก์ชันหลักใน cell นี้:
- `_search_scored()`
- `_detect_intent()`
- `_is_out_of_scope()`
- `_default_fallback()`
- `_clean_chat_answer()`
- `_to_float()`
- `_answer_high_cholesterol_examples()`
- `_answer_daily_sugar_limit()`
- `ask_welly_rag()`

เกี่ยวกับ RAG ตรงไหน:
- เป็น `query orchestration layer`

flow ของ `ask_welly_rag()`:

1. รับคำถาม
2. เช็ก out-of-scope
3. เช็ก direct handler เฉพาะทาง
4. detect intent
5. เลือก vector store ที่จะค้น
6. retrieve hits
7. รวม context
8. ถ้าคะแนนต่ำให้ fallback
9. ถ้าคะแนนพอให้สร้าง prompt
10. ส่งเข้า LLM
11. clean คำตอบแล้วคืนกลับ

จุดสำคัญ:
- cell นี้ทำให้ notebook กลายเป็น “ระบบถามตอบจริง”
- แต่ก็เป็นจุดที่ทำให้ระบบเป็น hybrid เพราะมี direct handler แทรกอยู่

พรีเซนต์ยังไง:
- พูดว่า cell นี้เป็นสมองหลักของระบบ เพราะจัดลำดับทุกอย่างตั้งแต่ intent detection, retrieval, context assembly, ไปจนถึง LLM response

### Cell 30
หน้าที่:
- ทดสอบ `ask_welly_rag()` กับชุดคำถาม demo

เกี่ยวกับ RAG ตรงไหน:
- เป็น `system demo`

จุดสำคัญ:
- ครอบคลุมหลาย intent
- ใช้ดู answer และ source พร้อมกัน

พรีเซนต์ยังไง:
- พูดว่า cell นี้ใช้ทดสอบภาพรวมของระบบว่าหลังจากประกอบทุกส่วนแล้ว ระบบตอบได้จริงในหลายกรณี

### Cell 32
หน้าที่:
- นิยาม `suggest_food_names()`
- ใช้ `rapidfuzz` และ `get_close_matches`

เกี่ยวกับ RAG ตรงไหน:
- เป็น utility ก่อน retrieval

จุดสำคัญ:
- ช่วยกรณีพิมพ์ชื่ออาหารผิด
- เหมาะสำหรับ autocomplete หรือ suggestion ใน UI

พรีเซนต์ยังไง:
- พูดว่าเราเพิ่ม fuzzy matching เพื่อช่วยให้ระบบเข้าใจชื่ออาหารที่ผู้ใช้อาจพิมพ์ไม่ตรงเป๊ะ

### Cell 34
หน้าที่:
- โหลด `13k-recipes.csv` และ `calories.csv`
- แปลง row เป็น recipe documents และ calorie documents
- split recipe docs เพิ่ม

เกี่ยวกับ RAG ตรงไหน:
- เป็น `ingestion` ของ corpus เพิ่มเติม

จุดสำคัญ:
- ทำให้ระบบไม่ตอบได้แค่ knowledge/guideline
- แต่ตอบเรื่อง recipe และ calories ได้ด้วย

พรีเซนต์ยังไง:
- พูดว่าเราขยายระบบจาก knowledge store หลักไปยัง recipe และ calories store เพื่อรองรับคำถามหลายประเภทมากขึ้น

### Cell 35
หน้าที่:
- สร้างหรือโหลด FAISS index สำหรับ recipes และ calories
- มี helper `build_faiss_in_batches()`
- สร้าง `recipes_vectorstore` และ `calories_vectorstore`

เกี่ยวกับ RAG ตรงไหน:
- เป็น `multi-vector-store setup`

จุดสำคัญ:
- build แบบ batch เพื่อประหยัดทรัพยากร
- ทำให้ query บางประเภทวิ่งไปยัง corpus ที่เหมาะกว่า

พรีเซนต์ยังไง:
- พูดว่าเราแยกฐานข้อมูลเวกเตอร์ตาม domain ของข้อมูล เพื่อให้ retrieval ของแต่ละคำถามแม่นขึ้น เช่นสูตรอาหารกับข้อมูลโภชนาการไม่ควรใช้กองเดียวกันเสมอไป

### Cell 36
หน้าที่:
- ทดสอบคำถาม out-of-scope

เกี่ยวกับ RAG ตรงไหน:
- เป็น guardrail test

พรีเซนต์ยังไง:
- พูดว่าเราเช็กว่าเมื่อถามนอกขอบเขต ระบบต้องปฏิเสธอย่างเหมาะสม ไม่ควรตอบมั่ว

### Cell 37
หน้าที่:
- ทดสอบคำถาม guideline เรื่อง BMI

เกี่ยวกับ RAG ตรงไหน:
- เป็น test ของ guideline path

พรีเซนต์ยังไง:
- พูดว่า cell นี้ใช้เช็กว่าคำถามเชิงมาตรฐานสุขภาพสามารถดึงข้อมูลจากชุด knowledge ที่ถูกต้องได้

### Cell 38
หน้าที่:
- ทดสอบคำถาม recipe/recommendation ที่เกี่ยวกับ cheese

เกี่ยวกับ RAG ตรงไหน:
- เป็น test ของ recipe retrieval path

พรีเซนต์ยังไง:
- พูดว่าเราใช้คำถามนี้เพื่อดูว่าระบบ route ไป recipe store และ knowledge store ได้เหมาะสมหรือไม่

### Cell 39
หน้าที่:
- ทดสอบคำถามที่อยู่นอก knowledge domain โดยตรง เช่นออกกำลังกาย

เกี่ยวกับ RAG ตรงไหน:
- เป็น fallback test

พรีเซนต์ยังไง:
- พูดว่าเราเช็กว่าถ้าคำถามเกินขอบเขตของ dataset ระบบควรบอกว่าข้อมูลไม่พอ แทนที่จะ hallucinate

### Cell 41
หน้าที่:
- quick test คำถามเรื่อง cholesterol และ sugar

เกี่ยวกับ RAG ตรงไหน:
- เป็น regression check

จุดสำคัญ:
- ใช้เช็ก direct handler และ answer path หลักอีกครั้งหลัง build ทุกอย่างเสร็จ

พรีเซนต์ยังไง:
- พูดว่า cell นี้ใช้ยืนยันว่าคำถามสำคัญที่เราเจอบ่อยยังตอบได้หลังจากประกอบทุกส่วนของระบบเสร็จแล้ว

## สรุปวิธีเล่า Notebook นี้แบบสั้น

ถ้าจะพูดรวดเดียวให้เข้าใจง่าย:

`ระบบนี้เริ่มจากการโหลดข้อมูลโภชนาการหลายตาราง จากนั้นแปลงแต่ละแถวให้เป็นข้อความและสร้าง embeddings เก็บลง FAISS vector store เมื่อผู้ใช้ถาม ระบบจะวิเคราะห์ intent แล้วค้น context ที่เกี่ยวข้องจาก knowledge store, recipe store หรือ calorie store ก่อน จากนั้นนำ context ไปสร้าง prompt และส่งเข้า LLM เพื่อสร้างคำตอบที่อ้างอิงข้อมูลใน dataset พร้อมแสดงแหล่งที่มา`

## สรุปวิธีเล่า Notebook นี้แบบเป็นช่วง

ช่วงที่ 1:
- เราโหลดข้อมูลและเตรียม corpus จากหลายตาราง

ช่วงที่ 2:
- เราแปลงข้อมูลเป็น documents, split เป็น chunks, แล้วสร้าง embeddings

ช่วงที่ 3:
- เราเก็บ embeddings ลง FAISS เพื่อใช้ semantic retrieval

ช่วงที่ 4:
- เราเตรียม LLM และ prompt สำหรับตอบแบบ grounded

ช่วงที่ 5:
- เราสร้างฟังก์ชัน `ask_welly_rag()` เพื่อรวม intent detection, retrieval, และ generation เข้าด้วยกัน

ช่วงที่ 6:
- เราทดสอบทั้งกรณีปกติ, สูตรอาหาร, guideline, fallback, และ out-of-scope

## ถ้าต้องเลือกแค่ไม่กี่ cell ไปพรีเซนต์

แนะนำให้เน้น:
- Cell 10
- Cell 12
- Cell 16
- Cell 17
- Cell 19
- Cell 21
- Cell 23
- Cell 27
- Cell 29
- Cell 34
- Cell 35

เพราะชุดนี้ครอบคลุม pipeline RAG ครบที่สุด
