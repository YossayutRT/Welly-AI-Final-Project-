import { useEffect } from 'react'

function HomePage({ onStartChat, onOpenSignup }) {
  useEffect(() => {
    document.body.dataset.theme = 'light'
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-white to-blue-50">
      <div className="relative min-h-screen overflow-hidden">
        <div className="pointer-events-none absolute -top-32 -left-32 h-[420px] w-[420px] rounded-full bg-emerald-200/50 blur-3xl"></div>
        <div className="pointer-events-none absolute top-10 -right-24 h-[480px] w-[480px] rounded-full bg-teal-200/60 blur-3xl"></div>
        <div className="pointer-events-none absolute -bottom-40 right-10 h-[520px] w-[520px] rounded-full bg-emerald-100/70 blur-3xl"></div>

        <main className="relative z-10 mx-auto flex min-h-screen w-full flex-col gap-8 px-4 py-5 sm:gap-10 sm:px-6 sm:py-6">
          <header className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-slate-800">
              <img
                src="/Welly.png"
                alt="Welly AI"
                className="h-8 w-8 rounded-xl object-contain"
              />
              <span className="text-sm font-semibold">Welly AI</span>
            </div>
            <button
              type="button"
              onClick={onOpenSignup}
              className="rounded-2xl border border-white/70 bg-white/60 px-4 py-2 text-sm font-medium text-slate-700 backdrop-blur-xl shadow-[0_8px_20px_rgba(31,54,74,0.12)]"
            >
              สมัครใช้งาน
            </button>
          </header>

          <section className="relative grid flex-1 items-center gap-8 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="pointer-events-none absolute left-1/2 top-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/70 bg-[radial-gradient(circle_at_30%_30%,_rgba(255,255,255,0.95),_rgba(190,220,255,0.7)_45%,_rgba(255,190,222,0.45)_70%,_rgba(255,255,255,0.2)_100%)] shadow-[0_30px_80px_rgba(55,92,121,0.28)] sm:h-56 sm:w-56 lg:h-64 lg:w-64 orb-float"></div>
            <div className="pointer-events-none absolute left-1/2 top-1/2 h-56 w-56 -translate-x-1/2 -translate-y-1/2 rounded-full border border-dashed border-white/70 sm:h-64 sm:w-64 lg:h-72 lg:w-72 orb-float-delayed"></div>
            <div>
              <p className="text-[11px] uppercase tracking-[0.28em] text-emerald-500">AI Nutrition Assistant</p>
              <h1 className="mt-4 text-2xl font-semibold text-slate-800 sm:text-3xl md:text-4xl">
                แนะนำอาหารอัจฉริยะ
                <br />
                เพื่อสุขภาพที่ดีทุกวัน
              </h1>
              <p className="mt-4 max-w-xl text-sm text-slate-500 md:text-base">
                Welly AI ช่วยแนะนำเมนูตามเป้าหมายสุขภาพ เช่น ลดน้ำหนัก เพิ่มกล้ามเนื้อ คุมเบาหวาน และโภชนาการที่เหมาะกับไลฟ์สไตล์ของคุณ
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={onStartChat}
                  className="rounded-2xl bg-emerald-200/90 px-5 py-3 text-sm font-semibold text-emerald-950 shadow-[0_12px_28px_rgba(52,211,153,0.35)]"
                >
                  เริ่มแชตกับ Welly AI
                </button>
                <button
                  type="button"
                  onClick={onOpenSignup}
                  className="rounded-2xl border border-white/70 bg-white/70 px-5 py-3 text-sm font-medium text-slate-700"
                >
                  สร้างโปรไฟล์สุขภาพ
                </button>
              </div>

              <div className="mt-8 grid gap-3 md:grid-cols-3">
                {[
                  { value: '3,000+', label: 'เมนูอาหารสุขภาพ' },
                  { value: '24/7', label: 'พร้อมให้คำแนะนำ' },
                  { value: 'Personalized', label: 'แผนอาหารเฉพาะบุคคล' },
                ].map((item) => (
                  <article
                    key={item.value}
                    className="rounded-2xl border border-white/70 bg-white/60 p-4 text-slate-700"
                  >
                    <strong className="text-base text-slate-800">{item.value}</strong>
                    <span className="mt-2 block text-xs text-slate-500">{item.label}</span>
                  </article>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/70 bg-white/60 p-5 shadow-[0_20px_60px_rgba(31,54,74,0.12)] backdrop-blur-xl sm:p-6">
              <div className="flex items-center justify-between">
                <span className="rounded-full border border-emerald-200/70 bg-emerald-200/50 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-800">
                  Live AI Preview
                </span>
                <span className="text-xs text-slate-500">Healthy mode active</span>
              </div>

              <div className="mt-4 rounded-2xl border border-white/70 bg-white/70 p-4">
                <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-500">Suggestion of the day</p>
                <h3 className="mt-2 text-base font-semibold text-slate-800">
                  ข้าวไรซ์เบอร์รี่ + อกไก่ย่าง + ผักย่าง
                </h3>
                <p className="mt-2 text-xs leading-6 text-slate-500">
                  พลังงานประมาณ 420 kcal, โปรตีนสูง, ไขมันดี และมีไฟเบอร์ช่วยให้อิ่มนาน
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {['High Protein', 'Low Sugar', 'Balanced Meal'].map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-emerald-200/70 bg-emerald-100/70 px-3 py-1 text-[10px] font-semibold text-emerald-800"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-3">
                {[
                  { label: 'Breakfast', value: 'Greek Yogurt Bowl' },
                  { label: 'Lunch', value: 'Salmon Quinoa Salad' },
                  { label: 'Dinner', value: 'Tofu Veggie Stir-fry' },
                ].map((item) => (
                  <article key={item.label} className="rounded-2xl border border-white/70 bg-white/70 p-3">
                    <p className="text-[10px] uppercase tracking-[0.2em] text-slate-400">{item.label}</p>
                    <strong className="mt-2 block text-xs text-slate-700">{item.value}</strong>
                  </article>
                ))}
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}

export default HomePage
