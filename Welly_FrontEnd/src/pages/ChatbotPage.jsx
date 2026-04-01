import { useEffect, useMemo, useRef, useState } from 'react'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

const sidebarMenus = [
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

const quickPrompts = [
  { label: 'Breakfast', prompt: 'ช่วยแนะนำเมนูอาหารเช้าที่ดีต่อสุขภาพ' },
  { label: '7-Day Plan', prompt: 'ช่วยจัดแผนอาหารสำหรับลดน้ำหนัก 7 วัน' },
  { label: 'Calories', prompt: 'ช่วยสรุปแคลอรีและสารอาหารของมื้อกลางวัน' },
  { label: 'High Protein', prompt: 'ช่วยหาเมนูอาหารเย็นที่ทำง่ายและมีโปรตีนสูง' },
]

function ChatbotPage({ onBackHome, onOpenHistory, onNewQuestion }) {
  const nextIdRef = useRef(2)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [backendStatus, setBackendStatus] = useState({
    ready: false,
    llmEnabled: false,
    statusText: 'กำลังตรวจสอบ backend',
  })
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      text: 'สวัสดีครับ ผมคือ Welly AI พร้อมช่วยตอบคำถามด้านโภชนาการ เมนูอาหาร และสุขภาพของคุณ',
      time: '09:00',
      sources: [],
      usedContextFallback: false,
    },
  ])

  useEffect(() => {
    document.body.dataset.theme = 'light'
  }, [])

  useEffect(() => {
    let ignore = false

    async function checkBackend() {
      try {
        const response = await fetch(`${API_BASE_URL}/health`)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const payload = await response.json()
        if (ignore) return

        setBackendStatus({
          ready: Boolean(payload.ready),
          llmEnabled: Boolean(payload.llm_enabled),
          statusText: payload.ready
            ? payload.llm_enabled
              ? 'Backend พร้อมและ LLM ใช้งานได้'
              : 'Backend พร้อมในโหมด retrieval fallback'
            : payload.startup_error || 'Backend ยังไม่พร้อม',
        })
      } catch {
        if (ignore) return
        setBackendStatus({
          ready: false,
          llmEnabled: false,
          statusText: 'เชื่อมต่อ backend ไม่ได้',
        })
      }
    }

    checkBackend()

    return () => {
      ignore = true
    }
  }, [])

  const isInputEmpty = useMemo(() => input.trim().length === 0 || isLoading, [input, isLoading])

  function nowTime() {
    return new Date().toLocaleTimeString('th-TH', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  }

  function formatSourceLabel(source) {
    return source.title || source.food_item || source.table || source.source || source.retrieved_from || 'source'
  }

  async function requestAnswer(message) {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        k: 4,
      }),
    })

    let payload = null
    try {
      payload = await response.json()
    } catch {
      payload = null
    }

    if (!response.ok) {
      const detail = payload?.detail || `HTTP ${response.status}`
      throw new Error(detail)
    }

    return payload
  }

  async function pushPrompt(promptText) {
    const value = promptText.trim()
    if (!value || isLoading) return

    const userId = nextIdRef.current
    nextIdRef.current += 1
    const botId = nextIdRef.current
    nextIdRef.current += 1

    const userMessage = {
      id: userId,
      role: 'user',
      text: value,
      time: nowTime(),
      sources: [],
      usedContextFallback: false,
    }

    if (onNewQuestion) {
      onNewQuestion({ text: value, time: userMessage.time })
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const payload = await requestAnswer(value)
      const assistantMessage = {
        id: botId,
        role: 'assistant',
        text: payload.answer,
        time: nowTime(),
        sources: payload.sources || [],
        usedContextFallback: Boolean(payload.used_context_fallback),
      }

      setMessages((prev) => [...prev, assistantMessage])
      setBackendStatus((prev) => ({
        ...prev,
        ready: true,
        llmEnabled: Boolean(payload.llm_enabled),
        statusText: payload.llm_enabled
          ? 'Backend พร้อมและ LLM ใช้งานได้'
          : 'Backend พร้อมในโหมด retrieval fallback',
      }))
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: botId,
          role: 'assistant',
          text: `เชื่อมต่อ backend ไม่สำเร็จ: ${error.message}`,
          time: nowTime(),
          sources: [],
          usedContextFallback: false,
          isError: true,
        },
      ])
      setBackendStatus({
        ready: false,
        llmEnabled: false,
        statusText: 'เชื่อมต่อ backend ไม่ได้',
      })
    } finally {
      setIsLoading(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    pushPrompt(input)
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-pink-50 via-white to-blue-50">
      <div className="relative h-screen overflow-hidden">
        <div className="pointer-events-none absolute -top-32 -left-32 h-[420px] w-[420px] rounded-full bg-emerald-200/50 blur-3xl"></div>
        <div className="pointer-events-none absolute top-10 -right-24 h-[480px] w-[480px] rounded-full bg-teal-200/60 blur-3xl"></div>
        <div className="pointer-events-none absolute -bottom-40 right-10 h-[520px] w-[520px] rounded-full bg-emerald-100/70 blur-3xl"></div>

        <div className="relative z-10 mx-auto flex h-full w-full flex-col gap-3 px-3 py-3 sm:flex-row sm:gap-6 sm:px-6 sm:py-6">
          <aside className="flex w-full flex-row items-center gap-2 rounded-2xl border border-white/60 bg-white/60 p-2 backdrop-blur-xl shadow-[0_16px_40px_rgba(31,54,74,0.12)] transition hover:-translate-y-0.5 hover:shadow-[0_26px_70px_rgba(31,54,74,0.16)] sm:w-56 sm:flex-col sm:items-stretch sm:gap-4 sm:rounded-3xl sm:p-4">
            <div className="flex items-center gap-2 px-2">
              <img
                src="/Welly.png"
                alt="Welly AI"
                className="h-8 w-8 rounded-xl object-contain"
              />
              <span className="text-sm font-semibold text-slate-800">Welly AI</span>
            </div>

            <nav className="mt-0 flex flex-1 flex-row gap-2 overflow-x-auto sm:mt-2 sm:flex-col sm:gap-2 sm:overflow-visible">
              {sidebarMenus.map((menu) => (
                <button
                  key={menu.label}
                  type="button"
                  onClick={() => (menu.label === 'History' ? onOpenHistory?.() : null)}
                  className={`flex items-center gap-2 rounded-xl border px-2 py-1.5 text-xs text-slate-700 transition hover:-translate-y-0.5 hover:shadow-[0_12px_26px_rgba(58,85,112,0.18)] sm:gap-3 sm:px-3 sm:py-2 sm:text-sm ${
                    menu.label === 'New Chat'
                      ? 'border-white/80 bg-white/70'
                      : 'border-transparent bg-white/60 hover:border-white/80'
                  }`}
                >
                  <span className="grid h-6 w-6 place-items-center rounded-lg border border-white/80 text-slate-600">
                    {menuIcons[menu.icon]}
                  </span>
                  <span className="min-w-[64px] truncate text-left sm:min-w-0">{menu.label}</span>
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

          <main className="relative flex min-h-0 flex-1 flex-col gap-4 overflow-hidden rounded-3xl border border-white/60 bg-white/40 p-4 backdrop-blur-xl shadow-[0_20px_70px_rgba(31,54,74,0.12)] transition hover:shadow-[0_26px_80px_rgba(31,54,74,0.16)] sm:gap-6 sm:p-6">
            <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-[10px] uppercase tracking-[0.28em] text-slate-500 sm:text-xs sm:tracking-[0.3em]">Welly AI Nutrition</p>
                <h1 className="mt-2 text-lg font-semibold text-slate-800 sm:text-2xl">
                  แนะนำอาหารอัจฉริยะ เพื่อสุขภาพที่ดีทุกวัน
                </h1>
                <p className="mt-2 text-sm text-slate-500 sm:text-base">
                  ผู้ช่วยด้านโภชนาการที่ดึงข้อมูลจากฐานความรู้ก่อนตอบ และสรุปคำแนะนำให้เหมาะกับคำถามของคุณ
                </p>
              </div>

              <div className="flex w-full flex-col gap-2 sm:w-auto sm:items-end">
                <span
                  className={`rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] ${
                    backendStatus.ready
                      ? 'border border-emerald-200/70 bg-emerald-200/60 text-emerald-900'
                      : 'border border-amber-200/80 bg-amber-100/80 text-amber-900'
                  }`}
                >
                  {backendStatus.ready ? (backendStatus.llmEnabled ? 'LLM Ready' : 'Retrieval Mode') : 'Backend Offline'}
                </span>
                <span className="text-xs text-slate-500">{backendStatus.statusText}</span>
              </div>
            </header>

            <div className="flex flex-wrap gap-2">
              {quickPrompts.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  disabled={isLoading}
                  onClick={() => pushPrompt(item.prompt)}
                  className="rounded-full border border-white/80 bg-white/70 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:-translate-y-0.5 hover:border-emerald-200/80 hover:bg-white disabled:opacity-50"
                >
                  {item.label}
                </button>
              ))}
            </div>

            <section className="flex min-h-0 flex-1 flex-col rounded-3xl border border-white/60 bg-white/50 p-4 text-slate-600 sm:p-6">
              <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto overscroll-contain scroll-smooth pr-2">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`max-w-[78%] ${message.role === 'user' ? 'ml-auto text-right' : 'mr-auto text-left'}`}
                  >
                    <div
                      className={`rounded-2xl border px-4 py-3 text-sm whitespace-pre-wrap ${
                        message.role === 'user'
                          ? 'border-emerald-200/70 bg-emerald-200/80 text-emerald-950'
                          : message.isError
                            ? 'border-amber-200/80 bg-amber-50 text-amber-900'
                            : 'border-white/70 bg-white/70 text-slate-700'
                      }`}
                    >
                      {message.text}
                    </div>

                    {message.role === 'assistant' && message.sources?.length ? (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {message.sources.slice(0, 4).map((source, index) => (
                          <span
                            key={`${message.id}-${index}`}
                            className="rounded-full border border-white/80 bg-white/70 px-2 py-1 text-[10px] font-medium text-slate-500"
                          >
                            {formatSourceLabel(source)}
                          </span>
                        ))}
                      </div>
                    ) : null}

                    {message.role === 'assistant' && message.usedContextFallback ? (
                      <div className="mt-1 text-[10px] text-slate-400">ตอบแบบ retrieval fallback</div>
                    ) : null}

                    <div className="mt-1 text-xs text-slate-400">{message.time}</div>
                  </div>
                ))}

                {isLoading ? (
                  <div className="mr-auto max-w-[78%]">
                    <div className="rounded-2xl border border-white/70 bg-white/70 px-4 py-3 text-sm text-slate-500">
                      Welly AI กำลังประมวลผลคำตอบ...
                    </div>
                  </div>
                ) : null}
              </div>
            </section>

            <div className="mx-auto flex w-full max-w-2xl flex-col gap-3">
              <form
                className="flex w-full flex-wrap items-center gap-2 rounded-2xl border border-white/70 bg-white/70 px-3 py-2 backdrop-blur-xl sm:gap-3"
                onSubmit={handleSubmit}
              >
                <label className="sr-only" htmlFor="prompt-input">
                  Message
                </label>
                <input
                  id="prompt-input"
                  className="min-w-[160px] flex-1 bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="พิมพ์คำถามเรื่องโภชนาการหรือเมนูที่ต้องการ"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isInputEmpty}
                  className="rounded-xl bg-emerald-200/90 px-4 py-2 text-xs font-semibold text-emerald-950 transition hover:-translate-y-0.5 hover:shadow-[0_12px_24px_rgba(52,211,153,0.3)] disabled:opacity-50"
                >
                  {isLoading ? 'Sending...' : 'Send'}
                </button>
              </form>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}

export default ChatbotPage
