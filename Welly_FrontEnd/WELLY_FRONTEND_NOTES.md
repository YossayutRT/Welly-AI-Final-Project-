# Welly Frontend Notes

ไฟล์นี้ใช้เป็นโน้ตอธิบายฝั่ง frontend ของโปรเจกต์ Welly AI แบบละเอียด

อ้างอิงโค้ดหลักจาก:
- [main.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/main.jsx)
- [App.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/App.jsx)
- [HomePage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HomePage.jsx)
- [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx)
- [HistoryPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HistoryPage.jsx)

## ภาพรวม

frontend ของโปรเจกต์นี้เป็นเว็บแอป React ที่ใช้ Vite เป็น build tool

หน้าที่หลักของ frontend คือ:

1. แสดงหน้า landing page ของ Welly AI
2. เปิดหน้า chat สำหรับถามคำถามเกี่ยวกับโภชนาการ
3. ส่งคำถามไปที่ backend FastAPI
4. รับคำตอบกลับมาแล้วแสดงในรูปแบบ chat
5. แสดงสถานะว่า backend พร้อมไหม และตอนนี้ใช้ LLM หรือ fallback mode
6. เก็บประวัติคำถามแบบชั่วคราวใน state ฝั่ง client

## เทคโนโลยีที่ใช้

- `React` สำหรับสร้าง UI
- `Vite` สำหรับ dev server และ production build
- `ESLint` สำหรับ lint
- `Tailwind CSS via CDN` ผ่าน [index.html](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/index.html)
- CSS เพิ่มเติมใน [index.css](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/index.css)

## Flow การทำงานของ Frontend

ลำดับการทำงานหลักเป็นแบบนี้:

1. Browser โหลด [index.html](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/index.html)
2. `index.html` เรียก `/src/main.jsx`
3. [main.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/main.jsx) render `<App />`
4. [App.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/App.jsx) เป็นตัวควบคุม page state
5. ถ้าอยู่หน้า home จะแสดง [HomePage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HomePage.jsx)
6. ถ้าอยู่หน้า chat จะแสดง [ChatbotPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/ChatbotPage.jsx)
7. ถ้าอยู่หน้า history จะแสดง [HistoryPage.jsx](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/pages/HistoryPage.jsx)

## อธิบายทีละไฟล์

### 1. `index.html`

หน้าที่:
- เป็น HTML shell หลักของแอป
- โหลด Google Font
- โหลด Tailwind ผ่าน CDN
- มี `<div id="root"></div>` สำหรับให้ React mount app

จุดสำคัญ:
- แอปนี้ยังไม่ได้ติดตั้ง Tailwind แบบ compile-time ผ่าน PostCSS
- แต่ใช้ Tailwind classes ได้เพราะโหลดจาก CDN ตรง ๆ

### 2. `src/main.jsx`

หน้าที่:
- เป็น entry point ของ React app
- import [index.css](/Users/madba/Pictures/GitTast/Welly-AI-Final-Project-%202/Welly_FrontEnd/src/index.css)
- ใช้ `createRoot()` เพื่อ render `<App />`

flow:
- `document.getElementById('root')`
- `createRoot(...).render(...)`
- `<StrictMode><App /></StrictMode>`

### 3. `src/App.jsx`

หน้าที่:
- เป็น page controller หลักของแอป
- คุม navigation แบบง่ายด้วย state โดยไม่ใช้ React Router

state หลัก:
- `page` เก็บว่าตอนนี้อยู่หน้า `home`, `chat`, หรือ `history`
- `isExiting` ใช้ทำ animation ตอนเปลี่ยนหน้า
- `history` เก็บประวัติคำถามใน session ปัจจุบัน

ฟังก์ชันสำคัญ:
- `goTo(nextPage)` ใช้เปลี่ยนหน้าแบบมี fade animation

logic สำคัญ:
- ถ้า `page === 'chat'` จะ render `ChatbotPage`
- ถ้า `page === 'history'` จะ render `HistoryPage`
- ถ้าไม่ใช่สองอย่างนี้ จะ render `HomePage`

จุดสำคัญ:
- ประวัติคำถามถูกเก็บใน memory เท่านั้น
- ถ้า refresh หน้า เว็บจะเสียประวัติทั้งหมด

### 4. `src/pages/HomePage.jsx`

หน้าที่:
- เป็นหน้า landing page ของระบบ
- เน้นแนะนำว่า Welly AI คืออะไร
- มีปุ่มสำหรับเริ่มแชต

องค์ประกอบหลัก:
- header แสดง logo กับปุ่ม `Sign in`
- hero section แสดงข้อความโปรโมต
- CTA button `เริ่มแชตกับ Welly AI`
- preview card แสดงตัวอย่างเมนูสุขภาพ

logic:
- ใช้ `useEffect()` เพื่อตั้ง `document.body.dataset.theme = 'light'`
- เมื่อกดปุ่มเริ่มแชต จะเรียก `onStartChat` ที่ส่งมาจาก `App`

บทบาท:
- เป็นหน้าต้อนรับก่อนเข้าสู่ chatbot จริง

### 5. `src/pages/ChatbotPage.jsx`

หน้าที่:
- เป็นหน้าสำคัญที่สุดของ frontend
- จัดการ input ของผู้ใช้
- เชื่อมกับ backend
- แสดงผลลัพธ์จาก RAG/LLM

#### ตัวแปรสำคัญ

`API_BASE_URL`
- ใช้ค่าจาก `import.meta.env.VITE_API_BASE_URL`
- ถ้าไม่มีจะ fallback ไปที่ `http://127.0.0.1:8000`

`quickPrompts`
- ปุ่มลัดสำหรับส่งคำถามที่ใช้บ่อย
- เช่น breakfast, 7-day plan, calories, high protein

#### state หลัก

- `input` เก็บข้อความในช่องพิมพ์
- `isLoading` บอกว่าระบบกำลังรอคำตอบอยู่ไหม
- `backendStatus` เก็บสถานะ backend เช่น ready / llm enabled / status text
- `messages` เก็บบทสนทนาทั้งหมดของหน้า chat

#### การเช็กสถานะ backend

เมื่อ component mount:
- frontend จะยิง `GET /health`
- ถ้า `payload.ready = true` และ `payload.llm_enabled = true` จะแสดง `LLM Ready`
- ถ้า backend พร้อมแต่ไม่มี LLM จะแสดง `Retrieval Mode`
- ถ้าต่อ backend ไม่ได้ จะแสดง `Backend Offline`

นี่คือที่มาของ badge สถานะมุมขวาบนของหน้าแชต

#### การส่งคำถามไป backend

ฟังก์ชัน `requestAnswer(message)`:
- ยิง `POST /api/chat`
- body เป็น JSON:
  - `message`
  - `k: 4`

ฟังก์ชัน `pushPrompt(promptText)`:
- สร้าง user message
- append ลง `messages`
- เรียก `requestAnswer()`
- ถ้าสำเร็จจะสร้าง assistant message จาก `payload.answer`
- เก็บ `payload.sources`
- เก็บ `payload.used_context_fallback`

#### การแสดงผลคำตอบ

สำหรับแต่ละ assistant message:
- แสดงข้อความตอบ
- ถ้ามี `sources` จะแสดง source chips
- ถ้า `used_context_fallback = true` สามารถใช้บอกได้ว่าคำตอบนี้ไม่ได้ผ่าน LLM เต็มรูป

#### การเก็บ history

เมื่อส่งคำถาม:
- `ChatbotPage` จะเรียก `onNewQuestion()`
- `App.jsx` จะรับไปเก็บใน state `history`

หมายความว่า:
- history ที่หน้า frontend เห็นตอนนี้เป็นแค่ “รายการคำถาม”
- ยังไม่ได้ดึงจาก database จริง

### 6. `src/pages/HistoryPage.jsx`

หน้าที่:
- แสดงประวัติคำถามที่เก็บอยู่ใน state

พฤติกรรม:
- ถ้าไม่มี history จะขึ้น empty state
- ถ้ามี history จะ list เป็น card
- มีปุ่มกลับไปหน้า chat และหน้า home

จุดสำคัญ:
- มีข้อความเตือนในหน้าเองว่า “รีเฟรชแล้วจะหายทั้งหมด”
- เป็น history แบบชั่วคราว ไม่ใช่ persistent history

### 7. `src/index.css`

หน้าที่:
- เป็น CSS กลางของแอป
- กำหนด font family, theme variables, animations

เนื้อหาหลัก:
- import font เพิ่ม
- กำหนด `:root`
- กำหนดตัวแปร theme สำหรับ light/dark
- page fade animation
- orb floating animation

บทบาท:
- ถึงตัว layout ส่วนใหญ่ใช้ Tailwind utility classes
- แต่ไฟล์นี้เป็นตัวกำหนด global look-and-feel และ motion ของแอป

### 8. `package.json`

หน้าที่:
- ระบุ dependency และ script ของ frontend

script หลัก:
- `npm run dev`
- `npm run build`
- `npm run lint`
- `npm run preview`

จุดสำคัญ:
- dependency runtime มีแค่ `react` และ `react-dom`
- ส่วน Vite และ ESLint อยู่ใน devDependencies

## การเชื่อมกับ Backend

frontend คุยกับ backend ผ่าน 2 endpoint หลัก:

### `GET /health`

ใช้สำหรับ:
- เช็กว่า backend พร้อมหรือยัง
- ดูว่า LLM เปิดอยู่ไหม

frontend ใช้ endpoint นี้เพื่อ:
- แสดง `LLM Ready`
- หรือ `Retrieval Mode`
- หรือ `Backend Offline`

### `POST /api/chat`

ใช้สำหรับ:
- ส่งคำถามของผู้ใช้ไปให้ backend ประมวลผล

payload ที่ส่ง:
```json
{
  "message": "ช่วยหาเมนูอาหารเย็นที่ทำง่ายและมีโปรตีนสูง",
  "k": 4
}
```

payload ที่คาดว่าจะได้กลับ:
- `question`
- `intent`
- `answer`
- `sources`
- `llm_enabled`
- `used_context_fallback`

## การไหลของข้อมูลในหน้า Chat

flow แบบง่าย:

1. ผู้ใช้พิมพ์คำถาม
2. กดส่ง
3. `pushPrompt()` สร้าง user message
4. frontend เรียก `requestAnswer()`
5. backend ตอบกลับ JSON
6. frontend เอา `answer` ไปใส่ใน assistant message
7. frontend แสดง source และสถานะ LLM/fallback

## จุดเด่นของ Frontend

- โครงสร้างง่าย อ่านง่าย
- ไม่ซับซ้อนเกินไปสำหรับโปรเจกต์นักศึกษา
- เชื่อม backend จริงแล้ว
- มี quick prompts
- มี badge สถานะ backend
- UI มี visual direction ชัดพอสมควร

## จุดที่ควรจำเวลาอธิบาย

- navigation ใช้ state ไม่ได้ใช้ router
- history ยังเป็น client-side state
- authentication ยังเป็น UI placeholder
- backend status ถูกเช็กจาก `/health`
- ตัวตอบจริงอยู่ฝั่ง backend ไม่ได้ generate ใน frontend

## ถ้าจะพรีเซนต์สั้น ๆ

พูดได้ว่า:

`frontend ของ Welly AI ถูกสร้างด้วย React และ Vite โดยแบ่งออกเป็น 3 หน้าหลักคือ Home, Chat, และ History หน้า Chat จะเชื่อมกับ FastAPI backend ผ่าน endpoint /health และ /api/chat เพื่อเช็กสถานะระบบและส่งคำถามไปยัง RAG + LLM backend จากนั้นจะแสดงคำตอบพร้อมแหล่งอ้างอิงกลับมาในรูปแบบ chatbot`

## คำสั่งรัน Frontend

```bash
cd Welly_FrontEnd
npm install
npm run dev
```

ถ้าต้องการกำหนด backend URL เอง:

สร้างไฟล์ `.env` ใน `Welly_FrontEnd`

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```
