import { useEffect, useRef, useState } from 'react'
import ChatbotPage from './pages/ChatbotPage'
import HistoryPage from './pages/HistoryPage'
import HomePage from './pages/HomePage'

function App() {
  const [page, setPage] = useState('home')
  const [isExiting, setIsExiting] = useState(false)
  const [history, setHistory] = useState([])
  const timeoutRef = useRef(null)

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  function goTo(nextPage) {
    if (nextPage === page || isExiting) return

    setIsExiting(true)
    timeoutRef.current = setTimeout(() => {
      setPage(nextPage)
      setIsExiting(false)
    }, 180)
  }

  if (page === 'chat') {
    return (
      <div className={`page-fade ${isExiting ? 'page-fade-exit' : ''}`} key="chat">
        <ChatbotPage
          onBackHome={() => goTo('home')}
          onOpenHistory={() => goTo('history')}
          onNewQuestion={(entry) =>
            setHistory((prev) => [
              {
                id: `${Date.now()}-${Math.random()}`,
                text: entry.text,
                time: entry.time,
              },
              ...prev,
            ])
          }
        />
      </div>
    )
  }

  if (page === 'history') {
    return (
      <div className={`page-fade ${isExiting ? 'page-fade-exit' : ''}`} key="history">
        <HistoryPage
          history={history}
          onBackChat={() => goTo('chat')}
          onBackHome={() => goTo('home')}
        />
      </div>
    )
  }

  return (
    <div className={`page-fade ${isExiting ? 'page-fade-exit' : ''}`} key="home">
      <HomePage onStartChat={() => goTo('chat')} />
    </div>
  )
}

export default App
