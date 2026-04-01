import { useEffect } from 'react'

const menuItems = [
  { label: 'New Chat', icon: 'chat' },
  { label: 'History', icon: 'history' },
]

const menuIcons = {
  chat: (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-3.5 w-3.5">
      <path
        d="M5 5h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H9l-4 3v-3H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z"
        fill="currentColor"
      />
    </svg>
  ),
  history: (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-3.5 w-3.5">
      <path
        d="M12 7v5l4 2"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M4.5 12a7.5 7.5 0 1 0 2.2-5.3"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <path
        d="M4.5 5.5v3.2h3.2"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  ),
}

function HistoryPage({ history, onBackChat, onBackHome }) {
  useEffect(() => {
    document.body.dataset.theme = 'light'
  }, [])

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-pink-50 via-white to-blue-50">
      <div className="relative min-h-screen overflow-hidden">
        <div className="pointer-events-none absolute -top-32 -left-32 h-[420px] w-[420px] rounded-full bg-emerald-200/50 blur-3xl"></div>
        <div className="pointer-events-none absolute top-10 -right-24 h-[480px] w-[480px] rounded-full bg-teal-200/60 blur-3xl"></div>
        <div className="pointer-events-none absolute -bottom-40 right-10 h-[520px] w-[520px] rounded-full bg-emerald-100/70 blur-3xl"></div>

        <div className="relative z-10 mx-auto flex min-h-screen w-full flex-col gap-4 px-3 py-4 sm:flex-row sm:gap-6 sm:px-6 sm:py-6">
          <aside className="flex w-full flex-row items-center gap-2 rounded-2xl border border-white/60 bg-white/50 p-2 backdrop-blur-xl shadow-[0_20px_60px_rgba(31,54,74,0.12)] transition hover:-translate-y-0.5 hover:shadow-[0_26px_70px_rgba(31,54,74,0.16)] sm:w-56 sm:flex-col sm:items-stretch sm:gap-4 sm:rounded-3xl sm:p-4">
            <div className="flex items-center gap-2 px-2">
              <img
                src="/Welly.png"
                alt="Welly AI"
                className="h-8 w-8 rounded-xl object-contain"
              />
              <span className="text-sm font-semibold text-slate-800">Welly AI</span>
            </div>

            <nav className="mt-0 flex flex-1 flex-row gap-2 overflow-x-auto sm:mt-2 sm:flex-col sm:gap-2 sm:overflow-visible">
              {menuItems.map((menu) => (
                <button
                  key={menu.label}
                  type="button"
                  onClick={() => (menu.label === 'New Chat' ? onBackChat() : null)}
                  className={`flex items-center gap-2 rounded-xl border px-2 py-2 text-xs text-slate-700 transition hover:-translate-y-0.5 hover:shadow-[0_12px_26px_rgba(58,85,112,0.18)] sm:gap-3 sm:px-3 sm:py-2 sm:text-sm ${
                    menu.label === 'History'
                      ? 'border-white/80 bg-white/70'
                      : 'border-transparent bg-white/60 hover:border-white/80'
                  }`}
                >
                  <span className="grid h-6 w-6 place-items-center rounded-lg border border-white/80 text-slate-600">
                    {menuIcons[menu.icon]}
                  </span>
                  <span className="min-w-[64px] truncate text-left sm:min-w-0 sm:truncate-0">{menu.label}</span>
                </button>
              ))}
            </nav>

            <div className="hidden gap-2 px-1 sm:grid sm:mt-auto">
              {onBackHome ? (
                <button
                  type="button"
                  onClick={onBackHome}
                  className="rounded-2xl border border-white/70 bg-white/60 px-4 py-2 text-sm font-medium text-slate-700 backdrop-blur-xl"
                >
                  Home
                </button>
              ) : null}
              <button
                type="button"
                className="rounded-2xl border border-emerald-200/80 bg-emerald-200/80 px-4 py-2 text-sm font-semibold text-emerald-950 shadow-[0_10px_24px_rgba(52,211,153,0.35)]"
              >
                Connect
              </button>
            </div>
          </aside>

          <main className="relative flex flex-1 flex-col gap-4 rounded-3xl border border-white/60 bg-white/40 p-4 backdrop-blur-xl shadow-[0_20px_70px_rgba(31,54,74,0.12)] transition hover:shadow-[0_26px_80px_rgba(31,54,74,0.16)] sm:gap-6 sm:p-6">
            <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Welly AI Nutrition</p>
                <h1 className="mt-2 text-xl font-semibold text-slate-800 sm:text-2xl">
                  ประวัติการถามล่าสุด
                </h1>
                <p className="mt-2 text-sm text-slate-500 sm:text-base">
                  เก็บเฉพาะคำถามที่คุณถามในรอบนี้ รีเฟรชแล้วจะหายทั้งหมด
                </p>
              </div>
              <button
                className="w-full rounded-2xl border border-white/70 bg-white/60 px-4 py-2 text-sm font-medium text-slate-700 backdrop-blur-xl shadow-[0_8px_20px_rgba(31,54,74,0.12)] transition hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(31,54,74,0.18)] sm:w-auto"
                type="button"
                onClick={onBackChat}
              >
                Back to Chat
              </button>
            </header>

            <section className="flex-1 rounded-3xl border border-white/60 bg-white/50 p-4 text-slate-600 sm:p-6">
              {history.length === 0 ? (
                <div className="grid h-full place-content-center gap-3 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-white/70 bg-emerald-100/80">
                    <img
                      src="/Welly.png"
                      alt="Welly AI"
                      className="h-7 w-7 object-contain"
                    />
                  </div>
                  <h2 className="text-base font-semibold text-slate-800 sm:text-lg">ยังไม่มีประวัติการถาม</h2>
                  <p className="text-sm text-slate-500">เริ่มถามคำถามในแชต แล้วกลับมาดูที่นี่ได้เลย</p>
                </div>
              ) : (
                <div className="flex h-full flex-col gap-3 overflow-y-auto">
                  {history.map((entry) => (
                    <article
                      key={entry.id}
                      className="rounded-2xl border border-white/70 bg-white/70 p-4 text-sm text-slate-700"
                    >
                      <p className="font-medium text-slate-800">{entry.text}</p>
                      <span className="mt-2 block text-xs text-slate-400">{entry.time}</span>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </main>
        </div>
      </div>
    </div>
  )
}

export default HistoryPage
