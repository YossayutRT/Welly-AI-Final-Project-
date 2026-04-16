import { useEffect, useMemo, useState } from 'react'

const initialForm = {
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
  age: '',
  sex: '',
  heightCm: '',
  weightKg: '',
  activityLevel: 'moderate',
  primaryGoal: 'balanced',
  conditions: [],
  dietaryNotes: '',
  consentProfile: false,
}

const activityOptions = [
  { value: 'low', label: 'เคลื่อนไหวน้อย' },
  { value: 'moderate', label: 'ปานกลาง' },
  { value: 'high', label: 'ออกกำลังกายบ่อย' },
]

const goalOptions = [
  { value: 'balanced', label: 'กินให้สมดุล' },
  { value: 'weight_loss', label: 'ลดน้ำหนัก' },
  { value: 'cholesterol_control', label: 'คุมคอเลสเตอรอล' },
  { value: 'blood_sugar_control', label: 'คุมน้ำตาล' },
  { value: 'low_sodium', label: 'ลดโซเดียม' },
  { value: 'high_protein', label: 'เพิ่มโปรตีน' },
]

const conditionOptions = [
  { value: 'high_cholesterol', label: 'คอเลสเตอรอลสูง' },
  { value: 'diabetes', label: 'เบาหวาน/น้ำตาลสูง' },
  { value: 'hypertension', label: 'ความดันสูง' },
]

function FieldError({ submitted, errors, name }) {
  if (!submitted || !errors[name]) return null
  return <p className="mt-1 text-xs text-rose-500">{errors[name]}</p>
}

function SignUpPage({ onBackHome, onStartChat }) {
  const [form, setForm] = useState(initialForm)
  const [submitted, setSubmitted] = useState(false)
  const [savedDraft, setSavedDraft] = useState(null)

  useEffect(() => {
    document.body.dataset.theme = 'light'
  }, [])

  const bmi = useMemo(() => {
    const height = Number(form.heightCm)
    const weight = Number(form.weightKg)
    if (!height || !weight) return null
    return weight / (height / 100) ** 2
  }, [form.heightCm, form.weightKg])

  const errors = useMemo(() => {
    const nextErrors = {}
    const age = Number(form.age)
    const height = Number(form.heightCm)
    const weight = Number(form.weightKg)

    if (!form.fullName.trim()) nextErrors.fullName = 'กรอกชื่อที่ใช้เรียกในระบบ'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) nextErrors.email = 'กรอกอีเมลให้ถูกต้อง'
    if (form.password.length < 8) nextErrors.password = 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร'
    if (form.password !== form.confirmPassword) nextErrors.confirmPassword = 'รหัสผ่านไม่ตรงกัน'
    if (!age || age < 1 || age > 120) nextErrors.age = 'กรอกอายุระหว่าง 1-120 ปี'
    if (!height || height < 80 || height > 250) nextErrors.heightCm = 'กรอกส่วนสูงระหว่าง 80-250 ซม.'
    if (!weight || weight < 20 || weight > 300) nextErrors.weightKg = 'กรอกน้ำหนักระหว่าง 20-300 กก.'
    if (!form.consentProfile) nextErrors.consentProfile = 'ต้องยินยอมก่อนสร้างโปรไฟล์'

    return nextErrors
  }, [form])

  function updateField(name, value) {
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }))
    setSavedDraft(null)
  }

  function toggleCondition(value) {
    setForm((prev) => {
      const exists = prev.conditions.includes(value)
      return {
        ...prev,
        conditions: exists
          ? prev.conditions.filter((item) => item !== value)
          : [...prev.conditions, value],
      }
    })
    setSavedDraft(null)
  }

  function fieldClass(name) {
    const invalid = submitted && errors[name]
    return `mt-2 w-full rounded-xl border bg-white/80 px-3 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none ${
      invalid
        ? 'border-rose-300 focus:ring-2 focus:ring-rose-100'
        : 'border-white/80 focus:ring-2 focus:ring-emerald-100'
    }`
  }

  function handleSubmit(event) {
    event.preventDefault()
    setSubmitted(true)

    if (Object.keys(errors).length > 0) {
      setSavedDraft(null)
      return
    }

    setSavedDraft({
      fullName: form.fullName.trim(),
      email: form.email.trim(),
      age: Number(form.age),
      sex: form.sex || null,
      heightCm: Number(form.heightCm),
      weightKg: Number(form.weightKg),
      activityLevel: form.activityLevel,
      primaryGoal: form.primaryGoal,
      conditions: form.conditions,
      dietaryNotes: form.dietaryNotes.trim(),
      bmi: bmi ? Number(bmi.toFixed(1)) : null,
    })
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-pink-50 via-white to-blue-50">
      <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-5 px-4 py-5 sm:px-6 sm:py-6">
        <header className="flex items-center justify-between gap-4">
          <button
            type="button"
            onClick={onBackHome}
            className="flex items-center gap-2 rounded-2xl border border-white/70 bg-white/60 px-3 py-2 text-sm font-semibold text-slate-800 shadow-[0_8px_20px_rgba(31,54,74,0.12)] backdrop-blur-xl"
          >
            <img src="/Welly.png" alt="Welly AI" className="h-8 w-8 rounded-xl object-contain" />
            Welly AI
          </button>

          <button
            type="button"
            onClick={onStartChat}
            className="rounded-2xl border border-white/70 bg-white/70 px-4 py-2 text-sm font-medium text-slate-700 shadow-[0_8px_20px_rgba(31,54,74,0.12)] backdrop-blur-xl"
          >
            ไปหน้าแชต
          </button>
        </header>

        <section className="grid flex-1 items-stretch gap-5 lg:grid-cols-[0.82fr_1.18fr]">
          <aside className="flex flex-col justify-between rounded-3xl border border-white/70 bg-white/55 p-5 text-slate-700 shadow-[0_20px_60px_rgba(31,54,74,0.12)] backdrop-blur-xl sm:p-7">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200/70 bg-emerald-100/70 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-800">
                Health Profile
              </div>
              <h1 className="mt-5 text-2xl font-semibold leading-tight text-slate-800 sm:text-3xl">
                สมัครใช้งานและตั้งค่าข้อมูลสุขภาพเริ่มต้น
              </h1>
              <p className="mt-4 text-sm leading-7 text-slate-500">
                โปรไฟล์นี้เตรียมข้อมูลพื้นฐานสำหรับการแนะนำอาหารเฉพาะบุคคล เช่น เป้าหมายสุขภาพ น้ำหนัก ส่วนสูง และข้อจำกัดด้านอาหาร
              </p>
            </div>

            <div className="mt-6 grid gap-3">
              {[
                'ใช้ข้อมูลเท่าที่จำเป็นต่อการแนะนำอาหาร',
                'แยกข้อมูลบัญชีออกจากข้อมูลสุขภาพ',
                'พร้อมเชื่อมต่อ database ในขั้นถัดไป',
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-start gap-3 rounded-2xl border border-white/70 bg-white/65 p-3"
                >
                  <span className="mt-1 h-2 w-2 rounded-full bg-emerald-400"></span>
                  <span className="text-sm text-slate-600">{item}</span>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-2xl border border-white/70 bg-white/65 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Profile snapshot</p>
              <dl className="mt-3 grid gap-3 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">เป้าหมาย</dt>
                  <dd className="font-semibold text-slate-800">
                    {goalOptions.find((goal) => goal.value === form.primaryGoal)?.label}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">กิจกรรม</dt>
                  <dd className="font-semibold text-slate-800">
                    {activityOptions.find((activity) => activity.value === form.activityLevel)?.label}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">BMI</dt>
                  <dd className="font-semibold text-slate-800">{bmi ? bmi.toFixed(1) : '-'}</dd>
                </div>
              </dl>
            </div>
          </aside>

          <form
            className="rounded-3xl border border-white/70 bg-white/65 p-5 shadow-[0_20px_60px_rgba(31,54,74,0.12)] backdrop-blur-xl sm:p-7"
            onSubmit={handleSubmit}
          >
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-emerald-500">
                  Create account
                </p>
                <h2 className="mt-2 text-xl font-semibold text-slate-800">ข้อมูลสมัครใช้งาน</h2>
              </div>
              <span className="rounded-full border border-white/80 bg-white/70 px-3 py-1 text-xs text-slate-500">
                ยังไม่บันทึกลง database
              </span>
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700">
                ชื่อที่ใช้เรียก
                <input
                  className={fieldClass('fullName')}
                  value={form.fullName}
                  onChange={(event) => updateField('fullName', event.target.value)}
                  placeholder="เช่น Mind"
                  autoComplete="name"
                />
                <FieldError submitted={submitted} errors={errors} name="fullName" />
              </label>

              <label className="block text-sm font-medium text-slate-700">
                อีเมล
                <input
                  className={fieldClass('email')}
                  type="email"
                  value={form.email}
                  onChange={(event) => updateField('email', event.target.value)}
                  placeholder="name@example.com"
                  autoComplete="email"
                />
                <FieldError submitted={submitted} errors={errors} name="email" />
              </label>

              <label className="block text-sm font-medium text-slate-700">
                รหัสผ่าน
                <input
                  className={fieldClass('password')}
                  type="password"
                  value={form.password}
                  onChange={(event) => updateField('password', event.target.value)}
                  placeholder="อย่างน้อย 8 ตัวอักษร"
                  autoComplete="new-password"
                />
                <FieldError submitted={submitted} errors={errors} name="password" />
              </label>

              <label className="block text-sm font-medium text-slate-700">
                ยืนยันรหัสผ่าน
                <input
                  className={fieldClass('confirmPassword')}
                  type="password"
                  value={form.confirmPassword}
                  onChange={(event) => updateField('confirmPassword', event.target.value)}
                  placeholder="กรอกรหัสผ่านอีกครั้ง"
                  autoComplete="new-password"
                />
                <FieldError submitted={submitted} errors={errors} name="confirmPassword" />
              </label>
            </div>

            <div className="mt-7 border-t border-white/70 pt-5">
              <h2 className="text-xl font-semibold text-slate-800">ข้อมูลร่างกายเบื้องต้น</h2>
              <div className="mt-4 grid gap-4 md:grid-cols-4">
                <label className="block text-sm font-medium text-slate-700">
                  อายุ
                  <input
                    className={fieldClass('age')}
                    type="number"
                    min="1"
                    max="120"
                    value={form.age}
                    onChange={(event) => updateField('age', event.target.value)}
                    placeholder="ปี"
                  />
                  <FieldError submitted={submitted} errors={errors} name="age" />
                </label>

                <label className="block text-sm font-medium text-slate-700">
                  เพศ
                  <select
                    className={fieldClass('sex')}
                    value={form.sex}
                    onChange={(event) => updateField('sex', event.target.value)}
                  >
                    <option value="">ไม่ระบุ</option>
                    <option value="female">หญิง</option>
                    <option value="male">ชาย</option>
                    <option value="other">อื่น ๆ</option>
                  </select>
                </label>

                <label className="block text-sm font-medium text-slate-700">
                  ส่วนสูง
                  <input
                    className={fieldClass('heightCm')}
                    type="number"
                    min="80"
                    max="250"
                    value={form.heightCm}
                    onChange={(event) => updateField('heightCm', event.target.value)}
                    placeholder="ซม."
                  />
                  <FieldError submitted={submitted} errors={errors} name="heightCm" />
                </label>

                <label className="block text-sm font-medium text-slate-700">
                  น้ำหนัก
                  <input
                    className={fieldClass('weightKg')}
                    type="number"
                    min="20"
                    max="300"
                    value={form.weightKg}
                    onChange={(event) => updateField('weightKg', event.target.value)}
                    placeholder="กก."
                  />
                  <FieldError submitted={submitted} errors={errors} name="weightKg" />
                </label>
              </div>
            </div>

            <div className="mt-7 grid gap-4 md:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700">
                ระดับกิจกรรม
                <select
                  className={fieldClass('activityLevel')}
                  value={form.activityLevel}
                  onChange={(event) => updateField('activityLevel', event.target.value)}
                >
                  {activityOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block text-sm font-medium text-slate-700">
                เป้าหมายหลัก
                <select
                  className={fieldClass('primaryGoal')}
                  value={form.primaryGoal}
                  onChange={(event) => updateField('primaryGoal', event.target.value)}
                >
                  {goalOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="mt-7 border-t border-white/70 pt-5">
              <h2 className="text-xl font-semibold text-slate-800">ภาวะสุขภาพและข้อจำกัดอาหาร</h2>
              <div className="mt-4 flex flex-wrap gap-2">
                {conditionOptions.map((condition) => (
                  <button
                    key={condition.value}
                    type="button"
                    onClick={() => toggleCondition(condition.value)}
                    className={`rounded-full border px-3 py-2 text-xs font-semibold transition ${
                      form.conditions.includes(condition.value)
                        ? 'border-emerald-200 bg-emerald-200/90 text-emerald-950'
                        : 'border-white/80 bg-white/70 text-slate-600 hover:border-emerald-200'
                    }`}
                  >
                    {condition.label}
                  </button>
                ))}
              </div>

              <label className="mt-4 block text-sm font-medium text-slate-700">
                แพ้อาหาร อาหารที่ไม่กิน หรือข้อจำกัดอื่น ๆ
                <textarea
                  className={`${fieldClass('dietaryNotes')} min-h-24 resize-none`}
                  value={form.dietaryNotes}
                  onChange={(event) => updateField('dietaryNotes', event.target.value)}
                  placeholder="เช่น แพ้ถั่ว ไม่กินหมู ไม่กินนม ต้องการอาหารฮาลาล"
                />
              </label>
            </div>

            <label className="mt-6 flex items-start gap-3 rounded-2xl border border-white/70 bg-white/65 p-4 text-sm text-slate-600">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-white/80 text-emerald-500"
                checked={form.consentProfile}
                onChange={(event) => updateField('consentProfile', event.target.checked)}
              />
              <span>
                ยินยอมให้ใช้ข้อมูลสุขภาพที่กรอกเพื่อสร้างโปรไฟล์แนะนำอาหารเฉพาะบุคคล
                <FieldError submitted={submitted} errors={errors} name="consentProfile" />
              </span>
            </label>

            {savedDraft ? (
              <div className="mt-5 rounded-2xl border border-emerald-200/80 bg-emerald-50/90 p-4 text-sm text-emerald-900">
                เตรียมข้อมูลโปรไฟล์ของ {savedDraft.fullName} เรียบร้อยแล้ว พร้อมเชื่อมต่อ API สำหรับบันทึกลง database ในขั้นถัดไป
              </div>
            ) : null}

            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={onBackHome}
                className="rounded-2xl border border-white/80 bg-white/70 px-5 py-3 text-sm font-medium text-slate-700"
              >
                กลับหน้าแรก
              </button>
              <button
                type="submit"
                className="rounded-2xl bg-emerald-200/90 px-5 py-3 text-sm font-semibold text-emerald-950 shadow-[0_12px_28px_rgba(52,211,153,0.35)] transition hover:-translate-y-0.5"
              >
                สมัครใช้งาน
              </button>
            </div>
          </form>
        </section>
      </main>
    </div>
  )
}

export default SignUpPage
