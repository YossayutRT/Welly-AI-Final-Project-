# CSI207 Project Review: Welly AI

## Executive Summary

Welly AI มีองค์ประกอบของ data science project ค่อนข้างครบสำหรับงานวิชา CSI207 คือมีทั้ง EDA, Data Preparation, Modelling, structured knowledge, และ Q&A / RAG prototype อยู่จริงใน repo เดียวกัน ซึ่งเป็นจุดแข็งมากในแง่ scope และ ambition ของงาน

อย่างไรก็ตาม ในมุมการส่งงานวิชา ปัญหาหลักตอนนี้ไม่ใช่เรื่อง “ทำไม่ครบ” แต่เป็นเรื่อง “เล่าเรื่องและพิสูจน์ความน่าเชื่อถือยังไม่แน่น” โดยเฉพาะ 3 เรื่อง:

1. modelling ยังมี label leakage ชัดเจน เพราะ target `risk_level` ถูกสร้างจากกฎบน feature ชุดเดียวกับที่ใช้ train model
2. โครงสร้าง notebook ยังซ้ำและรก ทำให้ยากต่อการบอกว่าไฟล์ไหนคือ final version
3. RAG prototype รันได้ แต่ retrieval quality ยังไม่เสถียรและยังไม่ถูกประเมินอย่างเป็นระบบ

ถ้ามองแบบอาจารย์ งานนี้อยู่ในระดับ “มีของและมีความพยายามจริง” แต่ถ้ายังไม่ cleanup อาจถูกถามหนักเรื่องความถูกต้องของ modelling และความเป็น final pipeline

## จุดแข็ง

- Scope โปรเจกต์ดีและสอดคล้องกับวิชา data science มาก เพราะเชื่อม food analytics, user health profiling, external knowledge, และ prototype QA เข้าด้วยกัน
- โครงสร้างโฟลเดอร์หลัก `data/`, `Notebooks/`, `outputs/`, `Src/` ถือว่าถูกทิศทางและอ่านง่ายในระดับหนึ่ง
- มี notebook หลักสำหรับ data preparation / modelling และ RAG แยกออกมาแล้ว คือ `Notebooks/04_data_preparation_and_modelling_final.ipynb` และ `Notebooks/07_rag_qa_system.ipynb`
- มีการแปลงความรู้จากเอกสารให้อยู่ในรูป structured tables ใน `data/knowledge/` ซึ่งช่วยให้โปรเจกต์ดูมี external knowledge จริง ไม่ได้พึ่ง raw CSV อย่างเดียว
- มี output artifacts จริง เช่น `outputs/food_dataset_with_risk.csv`, `outputs/model_results.csv`, `outputs/feature_importance.csv`, `outputs/full_knowledge_base.csv`
- มี user health knowledge สำหรับ chatbot / RAG แล้วใน `data/knowledge/user_health_knowledge.csv`
- Data preparation ขั้นพื้นฐานทำไว้ดีพอสมควร เช่น standardize columns, remove duplicates, convert numeric, impute missing, create derived features
- มี baseline comparison ระหว่าง Logistic Regression, Decision Tree, Random Forest ทำให้เห็นความตั้งใจด้าน modelling มากกว่าการใช้ model เดียว

## จุดอ่อน

- Repo ยังไม่มี “final story” ที่ชัดว่า notebook ไหนคือฉบับส่งจริง และ notebook ไหนเป็น draft
- มี notebook ซ้ำหลายไฟล์ เช่น `eda.ipynb`, `eda_2.ipynb`, `eda_2 copy.ipynb`, `eda_standard.ipynb`, `eda_standard2.ipynb`, `eda_standard_with_bmi_standards.ipynb`
- `Src/model.py` เป็นไฟล์ว่าง ทำให้โฟลเดอร์ `Src/` ยังไม่ช่วยเรื่อง reproducibility
- `outputs/model_results.csv` แสดงว่า Decision Tree และ Random Forest ได้ accuracy = `1.00000` ซึ่งในบริบทนี้เป็นสัญญาณอันตรายมากกว่าเป็นข้อดี
- target `risk_level` มาจากกฎของ `sodium`, `sat_fat`, `cholesterol`, `sugar` แล้ว feature ที่ใช้ train ก็มีตัวแปรเหล่านี้และ percent-derived features โดยตรง จึงแทบเป็นการให้ model เรียนกฎเดิมซ้ำ
- class distribution ของ `risk_label` ไม่สมดุลมาก (`High` มีเพียง 14 แถวจาก 2395 แถว) แต่ output ที่เก็บมีแค่ accuracy ยังไม่พอสำหรับอธิบายคุณภาพโมเดล
- RAG notebook โหลด knowledge เพียงบางไฟล์ แม้ใน `data/knowledge/` จะมีไฟล์อื่นที่น่าจะมีประโยชน์ เช่น `claim_rules_df.csv`, `dga_rules_df.csv`, `label_required_nutrients_df.csv`, `serving_size_reference_df.csv`
- full knowledge base มีความไม่สมดุลด้าน source สูงมาก: `user_health_knowledge` 5000 rows, `food_dataset_with_risk` 2395 rows, แต่ guideline tables รวมกันมีเพียงหลักสิบแถว จึงเสี่ยงทำให้ retrieval ดึง user records มากกว่าความรู้มาตรฐาน
- ยังไม่เห็นไฟล์อธิบายการ extract / structure ความรู้จาก PDF แบบชัดเจน ทำให้ตอบคำถามเรื่อง provenance ของ knowledge ได้ยาก
- ยังไม่มี README, requirements/environment, data dictionary, หรือ run instructions สำหรับอาจารย์

## สิ่งที่ควรแก้ทันที

1. จัดชุด notebook ให้เหลือเฉพาะ final version
   - ควรเก็บเพียง 3-4 ไฟล์หลัก และย้าย draft/duplicate ออกหรือใส่โฟลเดอร์ `Notebooks/archive/`

2. ปรับคำอธิบาย modelling ให้ตรงความจริง
   - ตอนนี้ไม่ควรอ้างว่าเป็น predictive model ที่เรียนรู้จาก ground truth
   - ควรอธิบายว่าเป็น `baseline model trained on heuristic risk labels` หรือ `rule-replication baseline`

3. เพิ่ม metric ที่เหมาะกับ class imbalance
   - อย่างน้อยควรมี macro F1, weighted F1, per-class precision/recall, balanced accuracy
   - ถ้าไม่เพิ่ม จุดนี้จะถูกถามแน่นอนว่าทำไม accuracy สูงแต่ class `High` มีน้อยมาก

4. ลดความเสี่ยงของ label leakage ใน narrative
   - ถ้าแก้ pipeline ไม่ทัน ให้พูดตรง ๆ ว่า model นี้มีไว้สาธิต baseline classification จาก heuristic labels ไม่ใช่ clinical prediction

5. จัด RAG ให้ตอบ guideline questions ได้ดีขึ้น
   - ควรแยก retrieval ตาม source type หรืออย่างน้อย filter source เมื่อ query เป็นคำถามเชิงมาตรฐาน เช่น sodium/day, BMI range

6. เพิ่ม README และไฟล์อธิบายวิธีรัน
   - ไม่มีไฟล์นี้จะทำให้ repo ดูยังไม่พร้อมส่ง แม้เนื้อหาข้างในจะทำมาเยอะ

7. ตัดไฟล์ที่สร้างความสับสนทันที
   - `eda_2 copy.ipynb` ควรเอาออกจากชุดส่ง
   - `eda.ipynb` ที่มี `%pip install` ควรไม่อยู่ใน final submission set

## สิ่งที่ควรทำเพิ่มถ้ามีเวลา

- สร้างไฟล์ `README.md` ที่อธิบาย project objective, datasets, pipeline, outputs, และวิธีรัน notebook ตามลำดับ
- เพิ่ม `requirements.txt` หรือ `environment.yml`
- เพิ่ม `data_dictionary.md` อธิบายความหมายและหน่วยของ feature สำคัญ
- export รูปสำคัญจาก EDA และ confusion matrix เป็นไฟล์ในโฟลเดอร์ `outputs/figures/`
- เพิ่ม notebook หรือ script สำหรับ “PDF knowledge extraction / structuring” เพื่อให้ provenance ของ external knowledge ชัด
- เพิ่ม evaluation ของ RAG อย่างง่าย เช่น 5-10 fixed questions พร้อม expected source / expected answer pattern
- เชื่อม user profile กับ food risk ให้ชัดขึ้น เช่น demo query ว่า user ที่ blood sugar สูงควรหลีกเลี่ยงอาหารประเภทไหน
- ถ้ามีเวลาพอ ควรแยก `Src/` ให้มี script ที่รันซ้ำได้จริงแทนการพึ่ง notebook ทั้งหมด

## รีวิวตาม requirement ของวิชา

### 1) Review Scope Project

โดยรวม scope ดีและน่าสนใจ เพราะไม่ได้มีแค่การทำนายหรือแค่ EDA แต่ครอบคลุม 3 มิติ:

- food nutrition analytics
- user health profiling
- knowledge-based QA / RAG

ในมุมอาจารย์ นี่เป็น scope ที่ “ดีเกินขั้นต่ำ” แต่ต้องระวังไม่ให้ scope กว้างเกินจนแต่ละส่วนดูไม่ลึกพอ การเล่าเรื่องควรชัดว่า:

- part A: วิเคราะห์และเตรียมข้อมูลอาหาร
- part B: สร้าง user health knowledge
- part C: สร้าง baseline food risk model
- part D: สร้าง QA / RAG prototype จาก combined knowledge

### 2) Exploratory Data Analysis (EDA)

EDA มีอยู่จริงและมีหลายเวอร์ชัน แต่ปัญหาคือกระจายหลาย notebook จนดูไม่เป็น final narrative

สิ่งที่โอเค:

- มีการดู distribution, correlation, top high-calorie foods, ingredient complexity
- มี notebook ที่พยายามเล่าภาพรวม project progress
- มีการเชื่อม EDA ไปสู่ data preparation และ modelling

สิ่งที่ยังขาด:

- ควรมี EDA final notebook เพียงไฟล์เดียวที่สรุป insight สำคัญจริง ๆ
- ควรมี summary slide-ready findings ชัดเจน 3-5 ข้อ
- ควรอธิบายว่าแต่ละ insight ถูกนำไปใช้ใน modelling หรือ recommendation อย่างไร

ข้อเสนอ:

- ใช้ `eda_standard_with_bmi_standards.ipynb` เป็น EDA/main progress notebook หลัก
- ตัดหรือ archive notebook EDA รุ่นเก่า

### 3) Data Preparation

ส่วนนี้ถือว่า “พอใช้ถึงค่อนข้างดี” สำหรับงานเรียน เพราะมี:

- column standardization
- duplicate removal
- numeric conversion
- median imputation
- derived percentage features
- user health structured knowledge

แต่ยังมี gap สำคัญ:

- ยังไม่ชัดเรื่อง unit harmonization ระหว่าง food datasets หลายชุด
- ยังไม่เห็น explicit data validation rules เช่น range checks, impossible values, schema checks
- ยังไม่มี data dictionary อธิบาย feature สำคัญ
- ยังไม่แยก clearly ระหว่าง “raw data”, “prepared data”, และ “modelling-ready data”

สรุปคือ data preparation ใช้งานได้ แต่ยังต้องทำให้ “อธิบายได้” มากขึ้น

### 4) Modelling

ส่วนนี้เป็นจุดที่ต้องระวังที่สุด

สิ่งที่ดี:

- ใช้ baseline models หลายตัว
- มี train/test split แบบ stratified
- มี pipeline, imputer, scaler สำหรับ logistic regression
- มี confusion matrix และ feature importance

ปัญหาเชิงวิธีวิทยา:

- target `risk_level` ถูกสร้างจาก feature nutrition ชุดเดียวกับที่ใช้ train model
- feature set มีทั้ง raw features และ features ที่คำนวณจาก raw features เดิม
- ผล accuracy = 1.0 ของ Decision Tree และ Random Forest จึงไม่ใช่หลักฐานว่า model เก่ง แต่เป็นหลักฐานว่าโจทย์นี้เกือบ deterministic
- class imbalance สูงมาก แต่ไม่มี metric ที่สะท้อนคุณภาพการทำนาย minority class จริง

ข้อสรุป:

- ถ้าจะส่งแบบปัจจุบัน ควรวาง modelling นี้เป็น `baseline heuristic-classification experiment`
- ไม่ควรอ้างว่าเป็น strong predictive modelling ในความหมายของ machine learning ที่ generalize ไปหา unknown health outcomes

## Notebook ที่ควรเก็บ / ควรตัด

| Notebook | ควรเก็บไหม | ความเห็น |
|---|---|---|
| `Notebooks/eda_standard_with_bmi_standards.ipynb` | เก็บ | ใช้เป็น EDA / project progress notebook หลักได้ |
| `Notebooks/04_data_preparation_and_modelling_final.ipynb` | เก็บ | เป็น notebook หลักของ preparation + modelling |
| `Notebooks/user_health_knowledge.ipynb` | เก็บ | ชัดเจนและมีประโยชน์ต่อ chatbot / RAG |
| `Notebooks/07_rag_qa_system.ipynb` | เก็บ | เหมาะเป็น prototype notebook สำหรับ QA / RAG |
| `Notebooks/eda_standard2.ipynb` | ตัดหรือ archive | เนื้อหาถูก supersede โดยเวอร์ชันที่มี BMI standards |
| `Notebooks/eda_standard.ipynb` | ตัดหรือ archive | ดูเป็น transitional notebook มากกว่า final |
| `Notebooks/eda_2.ipynb` | ตัดหรือ archive | เป็น early-phase notebook |
| `Notebooks/eda.ipynb` | ตัดจากชุดส่ง | มี `%pip install` และดูเป็น exploratory draft |
| `Notebooks/eda_2 copy.ipynb` | ตัดทันที | ชื่อไฟล์ทำให้ repo ดูไม่ final |

## มีส่วนไหนซ้ำหรือรกเกินไปไหม

มีชัดเจน และเป็นหนึ่งในจุดที่ควร cleanup ก่อนส่ง:

- notebook EDA หลายไฟล์ทำหน้าที่คล้ายกัน
- notebook รุ่นเก่ายังอยู่ปนกับรุ่น final
- ชื่อไฟล์ไม่ consistent ระหว่างแบบ numbered กับ non-numbered
- มี `.venv`, `.DS_Store` ใน repo ซึ่งไม่ควรเป็นส่วนของงานส่ง
- `Src/model.py` ว่าง ทำให้โครงสร้างดูเหมือนมี codebase แต่จริง ๆ ยังไม่ถูกใช้

## Q&A / RAG prototype ตอนนี้โอเคไหมสำหรับงานเรียน

คำตอบคือ “โอเคในฐานะ prototype” แต่ “ยังไม่โอเคในฐานะระบบตอบคำถามที่พิสูจน์แล้ว”

สิ่งที่โอเค:

- มี knowledge loading
- มี text conversion
- มี TF-IDF retriever
- มี demo queries
- มี full knowledge base output

สิ่งที่ยังไม่โอเค:

- ยังไม่มี evaluation framework
- retrieval ไม่ route ตามชนิดคำถาม
- guideline queries บางคำถามถูกดึงไปที่ user records แทน knowledge มาตรฐาน
- ยังไม่ใช้ knowledge files ทั้งหมดที่มีอยู่ใน `data/knowledge/`
- answer generator ยังเป็น retrieval dump มากกว่าการสรุปคำตอบเชิงเหตุผล

ดังนั้น ถ้าจะ present ควรเรียกว่า `Q&A / RAG prototype` หรือ `retrieval-based QA baseline`

## Outputs ที่มีอยู่พอหรือยัง

ตอนนี้ “พอสำหรับแสดงว่าทำงานจริง” แต่ “ยังไม่พอสำหรับ final submission ที่ดู polished”

มีแล้ว:

- `outputs/food_dataset_with_risk.csv`
- `outputs/model_results.csv`
- `outputs/feature_importance.csv`
- `outputs/full_knowledge_base.csv`
- `data/knowledge/user_health_knowledge.csv`
- `data/knowledge/user_health_knowledge.json`

ควรมีเพิ่ม:

- `README.md`
- `requirements.txt` หรือ `environment.yml`
- `data_dictionary.md`
- `project_summary.md` หรือ `final_report_outline.md`
- `outputs/figures/` สำหรับเก็บกราฟสำคัญ
- ถ้าเป็นไปได้ `Src/model.py` ที่รันซ้ำได้จริง หรือเอาไฟล์นี้ออกจาก narrative

## ไฟล์ไหนควรเพิ่มก่อนส่งงาน

- `README.md`
- `requirements.txt` หรือ `environment.yml`
- `data_dictionary.md`
- `HOW_TO_RUN.md` หรือรวมไว้ใน README
- `outputs/figures/` พร้อมรูปที่อ้างในรายงาน
- อาจเพิ่ม `Notebooks/00_project_overview.ipynb` หรือ markdown สรุปลำดับการอ่านไฟล์

## จุดที่อาจารย์อาจถามแล้วตอบยาก

1. ทำไม Decision Tree กับ Random Forest accuracy 100%?
   - ต้องตอบให้ได้ว่า target มาจาก heuristic rules และ model เรียน pattern ที่เกือบ deterministic

2. `risk_level` คือ ground truth จริงหรือแค่ label ที่สร้างเอง?
   - ถ้าตอบไม่ชัด งาน modelling จะดูอ่อนทันที

3. ความรู้จาก PDF ถูก extract มาอย่างไร?
   - ตอนนี้ยังไม่มี pipeline ที่โชว์ provenance แบบชัดเจนในชุดไฟล์หลัก

4. ทำไมรวมหลาย food datasets แล้วเชื่อว่า comparable?
   - ต้องตอบเรื่องหน่วย, schema mapping, และ cleaning strategy

5. ทำไม RAG ตอบคำถาม guideline บางข้อแล้วไปดึง user health rows?
   - เพราะ source imbalance และไม่มี source routing/filtering

6. ทำไม knowledge files บางตัวมีอยู่แต่ไม่ได้ถูกใช้ใน RAG?
   - เช่น `claim_rules_df.csv`, `dga_rules_df.csv`, `label_required_nutrients_df.csv`, `serving_size_reference_df.csv`

7. โปรเจกต์นี้ “recommendation” ตรงไหน?
   - ต้องอธิบายว่า recommendation ตอนนี้ยังอยู่ในระดับ prototype ผ่าน structured knowledge และ retrieval ไม่ใช่ end-to-end recommender system เต็มรูปแบบ

## Checklist สุดท้ายก่อนส่งงาน

- เลือก final notebook ให้เหลือชัดเจนไม่เกิน 4 ไฟล์
- ย้าย draft notebooks ออกจากโฟลเดอร์หลักหรือ archive
- ลบ `eda_2 copy.ipynb` ออกจากชุดส่ง
- เพิ่ม `README.md`
- เพิ่ม `requirements.txt` หรือ `environment.yml`
- เพิ่ม data dictionary
- แก้ narrative ของ modelling ให้ชัดว่าเป็น baseline บน heuristic labels
- เพิ่ม macro F1 / balanced accuracy / per-class metrics
- ใส่ข้อจำกัดของงานใน final notebook หรือ report
- อธิบาย PDF knowledge provenance ให้ชัด
- ปรับ RAG ให้ filter source ตามประเภทคำถามอย่างน้อยแบบ rule-based
- export รูปสำคัญจาก EDA และ evaluation
- ตรวจว่าทุก path รันได้จาก `Notebooks/`
- ตัดไฟล์รก เช่น `.DS_Store` และไม่รวม `.venv` ในงานส่ง

## สรุประดับความพร้อมส่ง

### ระดับตอนนี้

พร้อมส่งในระดับประมาณ **70%** หรือประมาณ **B- / B** ถ้าอาจารย์ให้คะแนนตาม “มีองค์ประกอบครบและทำงานจริง”

### ถ้าแก้จุดเร่งด่วนก่อนส่ง

ถ้าจัด repo ให้สะอาด, ปรับ narrative ของ modelling, เพิ่ม metrics ที่เหมาะสม, และทำ README ให้ครบ งานนี้สามารถขยับไปสู่ระดับประมาณ **80-85%** ได้ค่อนข้างชัด

### คำตัดสินสุดท้าย

โปรเจกต์นี้ **ไม่ใช่งานที่อ่อน** ตรงกันข้าม มันมี scope ดีและมีหลายส่วนที่น่าสนใจมาก แต่ตอนนี้ยังดูเป็น “โปรเจกต์ที่ทำมาเยอะ” มากกว่า “โปรเจกต์ที่ curate มาเพื่อส่ง” ดังนั้นสิ่งที่ต้องทำต่อไม่ใช่เพิ่มของใหม่เยอะ ๆ แต่คือการลดความซ้ำ, ทำ narrative ให้คม, และปิดจุดถามยากเรื่อง modelling กับ RAG ให้เรียบร้อย
