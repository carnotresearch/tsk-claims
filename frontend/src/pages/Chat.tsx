import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Plus, ChevronDown, Bot, User, MoreVertical, Trash2 } from 'lucide-react'
import { getSessions, createSession, getMessages, sendMessage, deleteSession } from '../api/chat'
import type { ChatMessage, ChatSession } from '../types'
import Spinner from '../components/ui/Spinner'

function SqlBlock({ sql }: { sql: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800"
      >
        <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
        {open ? 'Hide SQL' : 'View SQL'}
      </button>
      {open && (
        <pre className="mt-1 p-3 bg-gray-900 text-green-400 text-xs rounded-lg overflow-x-auto leading-relaxed">
          {sql}
        </pre>
      )}
    </div>
  )
}

function ResultTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (rows.length === 0) return <p className="text-xs text-gray-400 mt-2">No results returned.</p>
  const cols = Object.keys(rows[0])
  return (
    <div className="mt-2 overflow-x-auto">
      <table className="text-xs border-collapse">
        <thead>
          <tr className="bg-gray-100">
            {cols.map(c => <th key={c} className="border border-gray-200 px-2 py-1 text-left font-semibold text-gray-600">{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 20).map((r, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {cols.map(c => <td key={c} className="border border-gray-200 px-2 py-1 text-gray-700">{String(r[c] ?? '—')}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 20 && <p className="text-xs text-gray-400 mt-1">Showing 20 of {rows.length} rows</p>}
    </div>
  )
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${isUser ? 'bg-indigo-600' : 'bg-slate-700'}`}>
        {isUser ? <User size={14} className="text-white" /> : <Bot size={14} className="text-white" />}
      </div>
      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div className={`px-4 py-2.5 rounded-2xl text-sm ${isUser ? 'bg-indigo-600 text-white rounded-tr-sm' : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'}`}>
          {msg.content}
        </div>
        {msg.sql_generated && <SqlBlock sql={msg.sql_generated} />}
        {msg.result_rows && msg.result_rows.length > 0 && <ResultTable rows={msg.result_rows} />}
      </div>
    </div>
  )
}

function SessionItem({
  session,
  active,
  onSelect,
  onDelete,
}: {
  session: ChatSession
  active: boolean
  onSelect: () => void
  onDelete: () => void
}) {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className={`group relative flex items-center rounded-lg transition-colors ${active ? 'bg-indigo-50' : 'hover:bg-gray-50'}`}>
      <button
        onClick={onSelect}
        className={`flex-1 text-left px-3 py-2 text-sm truncate ${active ? 'text-indigo-700 font-medium' : 'text-gray-600'}`}
      >
        {session.title ?? `Chat ${session.id}`}
      </button>

      {/* 3-dot menu */}
      <div className="relative shrink-0 pr-1">
        <button
          onClick={(e) => { e.stopPropagation(); setMenuOpen(v => !v) }}
          className={`p-1 rounded text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 ${menuOpen ? 'opacity-100' : ''}`}
        >
          <MoreVertical size={14} />
        </button>
        {menuOpen && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 top-6 z-20 bg-white border border-gray-200 rounded-lg shadow-lg py-1 w-32">
              <button
                onClick={() => { setMenuOpen(false); onDelete() }}
                className="flex items-center gap-2 w-full px-3 py-1.5 text-sm text-red-600 hover:bg-red-50"
              >
                <Trash2 size={13} /> Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default function Chat() {
  const qc = useQueryClient()
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null)
  const [input, setInput] = useState('')
  const [sendError, setSendError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const sessionsQ = useQuery({ queryKey: ['chat-sessions'], queryFn: getSessions })
  const messagesQ = useQuery({
    queryKey: ['chat-messages', activeSession?.id],
    queryFn: () => getMessages(activeSession!.id),
    enabled: !!activeSession,
  })

  const newSession = useMutation({
    mutationFn: () => createSession(),
    onSuccess: (s) => {
      qc.invalidateQueries({ queryKey: ['chat-sessions'] })
      setActiveSession(s)
    },
  })

  const deleteChat = useMutation({
    mutationFn: (id: number) => deleteSession(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ['chat-sessions'] })
      if (activeSession?.id === id) setActiveSession(null)
    },
  })

  const sendMsg = useMutation({
    mutationFn: (content: string) => sendMessage(activeSession!.id, content),
    onSuccess: () => {
      setSendError('')
      qc.invalidateQueries({ queryKey: ['chat-messages', activeSession?.id] })
    },
    onError: (e: unknown) => {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setSendError(detail ?? 'Failed to get a response. Please try again.')
    },
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messagesQ.data])

  const handleSend = () => {
    const text = input.trim()
    if (!text || !activeSession || sendMsg.isPending) return
    setInput('')
    setSendError('')
    sendMsg.mutate(text)
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Sessions sidebar */}
      <div className="w-56 shrink-0 flex flex-col gap-2">
        <button
          className="btn-primary justify-center text-sm py-2"
          onClick={() => newSession.mutate()}
        >
          <Plus size={15} /> New Chat
        </button>
        <div className="card p-2 flex-1 overflow-y-auto space-y-0.5">
          {sessionsQ.isLoading && <Spinner />}
          {sessionsQ.data?.map(s => (
            <SessionItem
              key={s.id}
              session={s}
              active={activeSession?.id === s.id}
              onSelect={() => setActiveSession(s)}
              onDelete={() => { if (confirm(`Delete "${s.title ?? `Chat ${s.id}`}"?`)) deleteChat.mutate(s.id) }}
            />
          ))}
          {sessionsQ.data?.length === 0 && (
            <p className="text-xs text-gray-400 px-2 py-4 text-center">No sessions yet</p>
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="card flex-1 flex flex-col p-0 overflow-hidden">
        {!activeSession ? (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400 gap-3">
            <Bot size={40} className="text-gray-300" />
            <p className="text-sm">Start a new chat or select a session</p>
            <button className="btn-primary text-sm" onClick={() => newSession.mutate()}>
              <Plus size={15} /> New Chat
            </button>
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messagesQ.isLoading ? <Spinner /> : (
                <>
                  {messagesQ.data?.length === 0 && (
                    <div className="text-center py-8">
                      <Bot size={32} className="text-gray-300 mx-auto mb-3" />
                      <p className="text-sm text-gray-500 font-medium">Ask anything about your claims data</p>
                      <p className="text-xs text-gray-400 mt-1">e.g. "What is the total billed amount?" or "Show claims with outstanding amount"</p>
                    </div>
                  )}
                  {messagesQ.data?.map(msg => (
                    <MessageBubble key={msg.id} msg={msg} />
                  ))}
                  {sendMsg.isPending && (
                    <div className="flex gap-3">
                      <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center">
                        <Bot size={14} className="text-white" />
                      </div>
                      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-2.5">
                        <div className="flex gap-1">
                          {[0, 1, 2].map(i => (
                            <div key={i} className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                  {sendError && (
                    <div className="flex gap-3">
                      <div className="w-7 h-7 rounded-full bg-red-500 flex items-center justify-center shrink-0">
                        <Bot size={14} className="text-white" />
                      </div>
                      <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2.5 rounded-2xl rounded-tl-sm max-w-[80%]">
                        {sendError}
                      </div>
                    </div>
                  )}
                  <div ref={bottomRef} />
                </>
              )}
            </div>

            {/* Input */}
            <div className="border-t border-gray-100 p-3">
              <div className="flex gap-2">
                <input
                  className="input flex-1 text-sm"
                  placeholder="Ask about your claims data…"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                  disabled={sendMsg.isPending}
                />
                <button
                  className="btn-primary px-3 disabled:opacity-50"
                  onClick={handleSend}
                  disabled={!input.trim() || sendMsg.isPending}
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
