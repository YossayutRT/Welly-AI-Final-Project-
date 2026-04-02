# Welly AI Presentation File-by-File

ไฟล์นี้ทำไว้สำหรับพรีเซนต์แบบเปิดโค้ดไปพร้อมกัน

รูปแบบการพูดของแต่ละช่วงคือ:
`อธิบายตรงนี้:` ใช้พูดว่าบล็อกนี้ทำอะไร
`ชี้จุดนี้:` ใช้บอกว่าควรเล็งเมาส์หรือเลื่อนไปตรงไหน

## ลำดับที่แนะนำ

1. เริ่มที่ RAG เพื่ออธิบายแกนของระบบ
2. ต่อที่ frontend เพื่ออธิบายว่าผู้ใช้คุยกับระบบยังไง
3. ปิดด้วย backend เพื่ออธิบายว่า API และ RAG service เชื่อมกันยังไง

## ส่วนที่ 1: RAG

### ไฟล์: [Welly_AI_RAG.ipynb](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Notebooks/Welly_AI_RAG.ipynb)

อธิบายตรงนี้: ไฟล์นี้เป็นต้นทางของระบบ RAG ทั้งชุด ตั้งแต่โหลดข้อมูล แปลงข้อมูลเป็นเอกสาร สร้าง embedding เก็บลง FAISS และใช้ context ที่ค้นมาไปตอบผ่าน LLM
ชี้จุดนี้: เปิด notebook แล้วบอกก่อนว่าเราจะพาดูเฉพาะ code cells หลัก ไม่จำเป็นต้องเล่าทุก cell

อธิบายตรงนี้: ช่วงแรกของ notebook เป็นการเตรียม dependency และ token เพื่อให้ notebook ใช้งาน LangChain, FAISS, embedding model และ Groq ได้
ชี้จุดนี้: `Cell 1`, `Cell 2`, `Cell 6`, `Cell 8`

อธิบายตรงนี้: จุดเริ่มต้นของ RAG จริงคือการระบุว่าเราจะใช้ไฟล์ไหนเป็น knowledge source เช่น guideline, BMI, DGA, ข้อมูลสุขภาพผู้ใช้ และข้อมูลอาหารที่มี risk
ชี้จุดนี้: `Cell 10` ที่กำหนด `candidate_files`

อธิบายตรงนี้: หลังจากรู้แหล่งข้อมูลแล้ว เราโหลด CSV ทั้งหมดเข้ามาเป็น DataFrame ก่อน เพื่อเตรียมแปลงเป็นเอกสารสำหรับ retrieval
ชี้จุดนี้: `Cell 12` ที่สร้าง `loaded_tables`

อธิบายตรงนี้: ก่อนแปลงเป็น text เราดูโครงสร้างข้อมูลก่อนว่าแต่ละตารางมี column อะไรบ้าง เพื่อให้ format ตอนแปลง row ไม่เสียความหมาย
ชี้จุดนี้: `Cell 14` ที่ preview ตารางตัวอย่าง

อธิบายตรงนี้: cell นี้สำคัญมาก เพราะเป็นฟังก์ชันที่แปลง row ของแต่ละตารางให้กลายเป็นข้อความที่ embedding model อ่านเข้าใจได้
ชี้จุดนี้: `Cell 16` ที่นิยาม `row_to_text(table_name, row)`

อธิบายตรงนี้: หลังจากมีฟังก์ชันแปลง row แล้ว เราจะวนทุกตารางและทุกแถว สร้าง `Document` พร้อม metadata เช่น table และ row index
ชี้จุดนี้: `Cell 17` ที่สร้าง `documents`

อธิบายตรงนี้: เมื่อได้ documents แล้ว เรา split ข้อความเป็น chunks เพื่อให้ semantic search ดึงส่วนที่เกี่ยวข้องที่สุดได้ดีขึ้น
ชี้จุดนี้: `Cell 19` ที่ใช้ text splitter

อธิบายตรงนี้: จากนั้นเราใช้ embedding model แบบ multilingual เพื่อเปลี่ยน text chunks เป็น vector และเก็บลง FAISS vector database
ชี้จุดนี้: `Cell 21` ที่โหลด `HuggingFaceEmbeddings` และสร้าง `FAISS`

อธิบายตรงนี้: ตรงนี้คือการเช็ก retrieval ก่อนเข้า LLM ว่าถ้าถามคำถามหนึ่ง ระบบจะดึง chunks ที่ตรงกับคำถามจริงหรือไม่
ชี้จุดนี้: `Cell 23` และ `Cell 25`

อธิบายตรงนี้: ช่วงนี้เป็นการตั้ง prompt และเชื่อม LLM โดยกำหนดให้โมเดลตอบจาก context ที่ retrieve มา ไม่ใช่ตอบลอยจากความรู้ทั่วไป
ชี้จุดนี้: `Cell 27` ที่ตั้ง prompt และ LLM

อธิบายตรงนี้: ฟังก์ชันหลักของ notebook คือจุดที่รับคำถาม ตรวจ intent เลือก store ดึง context มารวม แล้วค่อยส่งให้ LLM สร้างคำตอบ
ชี้จุดนี้: `Cell 29` ที่เป็น `ask_welly_rag()`

อธิบายตรงนี้: notebook นี้ไม่ได้มีแค่ knowledge store หลัก แต่ยังแยก recipe store และ calories store ออกมา เพื่อให้ retrieval ตรงกับประเภทคำถามมากขึ้น
ชี้จุดนี้: `Cell 34` และ `Cell 35`

อธิบายตรงนี้: ตอนท้ายเราจะมีชุดทดสอบ query หลายแบบ เพื่อดูว่าระบบตอบคำถามด้าน guideline, recipe และ calories ได้ตามที่ออกแบบไว้หรือไม่
ชี้จุดนี้: `Cell 30`, `Cell 36`, `Cell 37`, `Cell 38`, `Cell 39`, `Cell 41`

อธิบายตรงนี้: ถ้าอาจารย์ถามว่างานนี้เป็น RAG ยังไง ให้สรุปว่า flow คือ load data -> document transform -> chunking -> embedding -> FAISS -> retrieve -> prompt -> LLM
ชี้จุดนี้: ชี้กลับไปที่ `Cell 10`, `Cell 16`, `Cell 19`, `Cell 21`, `Cell 23`, `Cell 27`, `Cell 29`

## ส่วนที่ 2: Frontend

### ไฟล์: [index.html](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/index.html#L1)

อธิบายตรงนี้: ไฟล์นี้เป็น entry point ของหน้าเว็บ กำหนด title, font, โหลด Tailwind CDN และวาง `root` สำหรับ React
ชี้จุดนี้: [index.html](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/index.html#L7), [index.html](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/index.html#L12), [index.html](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/index.html#L20)

### ไฟล์: [main.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/main.jsx#L1)

อธิบายตรงนี้: ไฟล์นี้เอา React app ไป mount ลง `root` และทำให้ `App` เป็นศูนย์กลางของทั้ง frontend
ชี้จุดนี้: [main.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/main.jsx#L6)

### ไฟล์: [App.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/App.jsx#L1)

อธิบายตรงนี้: ไฟล์นี้เป็นตัวคุม navigation ภายในแอป และเก็บ history ของคำถามใน session ปัจจุบัน
ชี้จุดนี้: [App.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/App.jsx#L7), [App.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/App.jsx#L9)

อธิบายตรงนี้: ฟังก์ชัน `goTo` ใช้เปลี่ยนหน้าระหว่าง home, chat และ history พร้อม animation ก่อนสลับหน้า
ชี้จุดนี้: [App.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/App.jsx#L20)

อธิบายตรงนี้: ถ้าอยู่หน้า chat เราจะ render `ChatbotPage` และทุกครั้งที่ผู้ใช้ถามใหม่ จะ push ข้อความนั้นเข้า history
ชี้จุดนี้: [App.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/App.jsx#L30), [App.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/App.jsx#L36)

อธิบายตรงนี้: ถ้าอยู่หน้า history ก็จะส่งรายการคำถามไปให้ `HistoryPage` แสดงผล ส่วน default คือหน้า `HomePage`
ชี้จุดนี้: [App.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/App.jsx#L51), [App.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/App.jsx#L63)

### ไฟล์: [HomePage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HomePage.jsx#L1)

อธิบายตรงนี้: หน้า Home เป็น landing page ของระบบ ใช้สื่อสารว่า Welly AI คือผู้ช่วยด้านโภชนาการและชวนผู้ใช้เริ่มแชต
ชี้จุดนี้: [HomePage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HomePage.jsx#L36), [HomePage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HomePage.jsx#L43)

อธิบายตรงนี้: ปุ่มหลักของหน้า Home คือจุดที่พาผู้ใช้เข้าสู่หน้า chat เพื่อเริ่มถามคำถามจริง
ชี้จุดนี้: [HomePage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HomePage.jsx#L47)

อธิบายตรงนี้: card ด้านขวาเป็น preview UX ของระบบ แสดงตัวอย่างเมนูและ mood ของผลิตภัณฑ์ก่อนเข้าใช้งานจริง
ชี้จุดนี้: [HomePage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HomePage.jsx#L80)

### ไฟล์: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L1)

อธิบายตรงนี้: ไฟล์นี้เป็นหัวใจของ frontend เพราะเป็นหน้าที่รับคำถามจากผู้ใช้ เรียก backend และแสดงคำตอบกลับมา
ชี้จุดนี้: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L54)

อธิบายตรงนี้: บรรทัดแรกของ logic กำหนด `API_BASE_URL` เพื่อให้ frontend รู้ว่าจะยิง request ไปที่ FastAPI backend ตัวไหน
ชี้จุดนี้: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L3)

อธิบายตรงนี้: ตรงนี้คือ quick prompts ซึ่งช่วยให้ผู้ใช้กดคำถามตัวอย่างได้เลยโดยไม่ต้องพิมพ์เอง
ชี้จุดนี้: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L47)

อธิบายตรงนี้: state หลักของหน้า chat มีทั้ง input, loading, backend status และรายการ messages ที่แสดงในหน้าจอ
ชี้จุดนี้: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L56), [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L58), [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L63)

อธิบายตรงนี้: useEffect ชุดนี้ใช้เรียก `/health` ตอนหน้า chat เปิด เพื่อเช็กว่า backend พร้อมไหม และ LLM เปิดใช้งานอยู่หรือไม่
ชี้จุดนี้: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L78)

อธิบายตรงนี้: ฟังก์ชัน `requestAnswer` เป็นจุดที่ frontend ส่งข้อความผู้ใช้ไปยัง `/api/chat` ของ backend
ชี้จุดนี้: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L131)

อธิบายตรงนี้: ฟังก์ชัน `pushPrompt` คือ flow หลักของฝั่งหน้าเว็บ โดยจะสร้าง user message ก่อน เรียก backend แล้วจึง append assistant message ที่ได้กลับมา
ชี้จุดนี้: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L158)

อธิบายตรงนี้: ส่วนนี้คือ badge สถานะระบบ ถ้า backend พร้อมและมี key ก็จะแสดง `LLM Ready` ถ้ายังไม่มี LLM จะขึ้น `Retrieval Mode`
ชี้จุดนี้: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L301)

อธิบายตรงนี้: ตรงนี้คือ rendering ของ message แต่ละก้อน รวมถึง source chips และป้ายบอกว่าเป็น retrieval fallback หรือไม่
ชี้จุดนี้: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L329), [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L348), [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L361)

อธิบายตรงนี้: ฟอร์มล่างสุดเป็นจุดรับข้อความจากผู้ใช้ และเมื่อกด send ก็จะเรียก `handleSubmit` เพื่อส่งคำถามเข้าสู่ flow ทั้งหมด
ชี้จุดนี้: [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L379), [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L387)

### ไฟล์: [HistoryPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HistoryPage.jsx#L1)

อธิบายตรงนี้: หน้า History ใช้แสดงรายการคำถามที่ผู้ใช้ถามใน session ปัจจุบัน เพื่อให้ย้อนกลับมาดูได้
ชี้จุดนี้: [HistoryPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HistoryPage.jsx#L107)

อธิบายตรงนี้: ข้อความตรง header บอกข้อจำกัดของ prototype ชัดเจนว่า history ตอนนี้เก็บแค่ฝั่ง client และรีเฟรชแล้วข้อมูลจะหาย
ชี้จุดนี้: [HistoryPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HistoryPage.jsx#L114)

อธิบายตรงนี้: ถ้ายังไม่มีคำถาม ระบบจะแสดง empty state เพื่อบอกผู้ใช้ให้กลับไปเริ่มถามในหน้า chat ก่อน
ชี้จุดนี้: [HistoryPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HistoryPage.jsx#L127)

อธิบายตรงนี้: ถ้ามีประวัติแล้ว ก็จะ map ข้อมูลแต่ละรายการออกมาเป็น list ของคำถามพร้อมเวลา
ชี้จุดนี้: [HistoryPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HistoryPage.jsx#L141)

## ส่วนที่ 3: Backend

### ไฟล์: [main.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/main.py#L1)

อธิบายตรงนี้: ไฟล์นี้เป็น entry point ของ FastAPI ใช้สร้าง app, ตั้ง CORS, initialize RAG service และเปิด endpoints ที่ frontend ใช้งาน
ชี้จุดนี้: [main.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/main.py#L15), [main.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/main.py#L30)

อธิบายตรงนี้: ตอน backend เริ่มทำงาน จะเข้าสู่ `lifespan` และเรียก `rag_service.initialize()` เพื่อโหลด data, embeddings, vector stores และ LLM ไว้ล่วงหน้า
ชี้จุดนี้: [main.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/main.py#L19)

อธิบายตรงนี้: ตรงนี้คือการเปิด CORS เพื่อให้ frontend ที่รันบนพอร์ต 5173 เรียก backend ตัวนี้ได้
ชี้จุดนี้: [main.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/main.py#L36)

อธิบายตรงนี้: endpoint `/health` ใช้ตรวจว่า backend พร้อมหรือไม่ และ LLM เปิดอยู่หรือไม่
ชี้จุดนี้: [main.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/main.py#L45)

อธิบายตรงนี้: endpoint `/api/chat` รับข้อความจาก frontend แล้วส่งต่อไปยัง `rag_service.ask()` เพื่อให้ RAG pipeline ประมวลผล
ชี้จุดนี้: [main.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/main.py#L50)

อธิบายตรงนี้: endpoint `/api/suggestions` เป็น API เสริมที่ใช้คืนชื่ออาหารที่คล้ายกับข้อความที่ผู้ใช้พิมพ์
ชี้จุดนี้: [main.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/main.py#L60)

### ไฟล์: [config.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/config.py#L1)

อธิบายตรงนี้: ไฟล์นี้รวมการตั้งค่าของ backend ทั้ง path, model name, API key, top-k และ allowed origins
ชี้จุดนี้: [config.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/config.py#L71)

อธิบายตรงนี้: helper พวก `_env_bool` กับ `_env_list` ใช้แปลงค่าจาก `.env` ให้ backend ใช้งานต่อได้สะดวก
ชี้จุดนี้: [config.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/config.py#L15), [config.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/config.py#L22)

อธิบายตรงนี้: ส่วนนี้แก้ปัญหาสำคัญเรื่อง embedding model โดยพยายามหา model จาก local path หรือ Hugging Face cache ก่อน เพื่อให้รันแบบ offline ได้
ชี้จุดนี้: [config.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/config.py#L30), [config.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/config.py#L58)

อธิบายตรงนี้: `get_settings()` เป็นจุดที่ backend โหลด `.env` จากทั้ง root project และโฟลเดอร์ backend จากนั้นประกอบเป็น `Settings` object ตัวเดียวให้ทั้งระบบใช้
ชี้จุดนี้: [config.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/config.py#L100)

### ไฟล์: [schemas.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/schemas.py#L1)

อธิบายตรงนี้: ไฟล์นี้กำหนด schema ของ API เพื่อให้ frontend กับ backend คุยกันด้วยรูปแบบข้อมูลที่แน่นอน
ชี้จุดนี้: [schemas.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/schemas.py#L17), [schemas.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/schemas.py#L22)

อธิบายตรงนี้: `SourceItem` ใช้แทน source ที่ได้จาก retrieval เพื่อให้ frontend เอาไปโชว์เป็น chips ต่อท้ายคำตอบได้
ชี้จุดนี้: [schemas.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/schemas.py#L6)

อธิบายตรงนี้: `ChatRequest` กำหนดว่าคำถามต้องมี `message` และเลือกค่า `k` ได้ ส่วน `ChatResponse` จะคืนทั้ง answer, intent, sources และสถานะว่าใช้ LLM หรือ fallback
ชี้จุดนี้: [schemas.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/schemas.py#L17), [schemas.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/schemas.py#L22)

อธิบายตรงนี้: `HealthResponse` ใช้ส่งสถานะ startup ของระบบกลับไปให้หน้าเว็บเช็กตอนเปิดหน้า chat
ชี้จุดนี้: [schemas.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/schemas.py#L31)

### ไฟล์: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L1)

อธิบายตรงนี้: ไฟล์นี้เป็นหัวใจของ backend เพราะรวม logic ของ RAG ทั้งหมดไว้ใน `WellyRAGService`
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L30)

อธิบายตรงนี้: constructor ของ class จะเตรียมตัวแปรกลางทั้งหมด เช่น loaded tables, embeddings, vector stores, LLM และ prompt หลักของระบบ
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L31), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L44)

อธิบายตรงนี้: `initialize()` คือขั้น startup ของ service โดยโหลดทุกอย่างไว้ให้พร้อมก่อนรับ request จริง
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L76)

อธิบายตรงนี้: `health()` รวบรวมสถานะพร้อมใช้งานของระบบ เช่น ready, llm_enabled, model name และตารางที่โหลดสำเร็จ
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L99)

อธิบายตรงนี้: `ask()` คือ flow หลักของ backend เริ่มจากรับคำถาม ตรวจ out-of-scope, ตรวจ direct handlers, detect intent, collect context, แล้วค่อยตัดสินใจว่าจะตอบด้วย fallback หรือ LLM
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L111)

อธิบายตรงนี้: ช่วงแรกของ `ask()` มีตัวกันคำถามนอกขอบเขต เช่นอาหารสัตว์ เพื่อไม่ให้ระบบตอบเกิน domain
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L118), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L577)

อธิบายตรงนี้: ก่อนเข้า RAG เต็ม ระบบจะลอง direct handlers บางตัวก่อน เช่นคำถามเรื่องโซเดียม น้ำตาล หรือคอเลสเตอรอล เพื่อดึงคำตอบจากตารางโดยตรง
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L131), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L660), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L699), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L749)

อธิบายตรงนี้: ถ้าไม่เข้า direct handler ระบบจะ detect intent ก่อนว่าเป็น general, guideline, recipe หรือ calorie แล้วค่อยเลือก vector store ที่เหมาะ
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L142), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L563)

อธิบายตรงนี้: `collect_context()` เป็นจุดที่รวมผล retrieval จากหลาย store, boost score ตาม intent และ dedupe hits ก่อนส่ง context ต่อไป
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L488)

อธิบายตรงนี้: ถ้า context ไม่มี หรือคะแนนต่ำเกิน threshold ระบบจะตอบ fallback เพื่อหลีกเลี่ยงการ hallucinate
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L148), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L593)

อธิบายตรงนี้: ถ้ายังไม่มี LLM key ระบบก็ยังตอบได้ด้วย retrieval fallback โดยสรุปข้อมูลจาก context ที่ค้นเจอแทน
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L158), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L618)

อธิบายตรงนี้: ถ้า LLM พร้อม ระบบจะเอา question กับ context ไป format เป็น prompt แล้วเรียก Groq เพื่อสร้างคำตอบสุดท้าย
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L168), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L384)

อธิบายตรงนี้: `_load_tables()` คือขั้นดึง knowledge CSV เข้ามาใช้จริงใน backend เวอร์ชัน API
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L212)

อธิบายตรงนี้: `_load_embeddings()` จะเลือกว่าจะโหลด embedding model จาก local cache หรือ path ที่กำหนดไว้ และรองรับการรันแบบ offline
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L233)

อธิบายตรงนี้: `_load_knowledge_vectorstore()` แปลงตารางทั้งหมดเป็น `Document`, split เป็น chunks แล้วสร้างหรือโหลด FAISS knowledge index
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L259)

อธิบายตรงนี้: `_load_recipe_vectorstore()` และ `_load_calories_vectorstore()` คือส่วนที่แยก corpus เฉพาะทางออกจาก knowledge หลัก
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L291), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L339)

อธิบายตรงนี้: `_row_to_text()` คือสะพานจาก DataFrame ไปสู่ vector search เพราะเป็นตัวกำหนดว่าข้อมูลแต่ละแถวจะถูกเล่าเป็นข้อความแบบไหน
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L396)

อธิบายตรงนี้: ถ้าอาจารย์ถามว่าทำไม backend นี้ยังถือว่าเป็น RAG ให้ตอบว่าใจกลางของมันยังเป็น retrieve context ก่อน แล้วค่อย generate answer ผ่าน prompt กับ LLM
ชี้จุดนี้: [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L142), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L168), [service.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/service.py#L488)

## ปิดพรีเซนต์

อธิบายตรงนี้: ถ้าจะสรุปปิด ให้พูดว่าโปรเจกต์นี้มีครบทั้ง RAG notebook สำหรับพัฒนา logic, FastAPI backend สำหรับเสิร์ฟ API และ React frontend สำหรับใช้งานจริงในรูปแบบ chatbot
ชี้จุดนี้: ชี้สลับที่ [Welly_AI_RAG.ipynb](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Notebooks/Welly_AI_RAG.ipynb), [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx#L131), [main.py](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_BlackEnd/app/main.py#L50)
