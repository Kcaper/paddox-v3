import { useEffect, useState } from 'react'
import client from '../api/client'

export default function Quiz() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [answering, setAnswering] = useState({})

  const load = () => {
    client.get('/api/quiz/current/').then((r) => setData(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const submitAnswer = async (questionId, option) => {
    setAnswering((prev) => ({ ...prev, [questionId]: true }))
    try {
      await client.post(`/api/quiz/answer/${questionId}/`, { option })
      setData((prev) => ({
        ...prev,
        questions: prev.questions.map((q) =>
          q.id === questionId ? { ...q, my_answer: option } : q
        ),
      }))
    } catch {
      // already answered or too late — reload to get fresh state
      load()
    } finally {
      setAnswering((prev) => ({ ...prev, [questionId]: false }))
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-6 h-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const questions = data?.questions || []
  const qualiQuestions = questions.filter((q) => q.batch === 'quali')
  const raceQuestions = questions.filter((q) => q.batch === 'race')

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Race Quiz</h2>
        <p className="text-gray-500 text-sm mt-1">
          {data?.race || 'No active race'} · 1 point per correct answer
        </p>
      </div>

      {questions.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-sm">No questions live yet.</p>
          <p className="text-xs mt-2 text-gray-600">5 questions drop before qualifying, 5 more on race day.</p>
        </div>
      ) : (
        <div className="space-y-8">
          {qualiQuestions.length > 0 && (
            <Section title="Pre-Qualifying" questions={qualiQuestions} answering={answering} onAnswer={submitAnswer} />
          )}
          {raceQuestions.length > 0 && (
            <Section title="Race Day" questions={raceQuestions} answering={answering} onAnswer={submitAnswer} />
          )}
        </div>
      )}
    </div>
  )
}

function Section({ title, questions, answering, onAnswer }) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">{title}</h3>
      <div className="space-y-4">
        {questions.map((q) => (
          <QuestionCard key={q.id} question={q} loading={answering[q.id]} onAnswer={onAnswer} />
        ))}
      </div>
    </div>
  )
}

function QuestionCard({ question: q, loading, onAnswer }) {
  const options = ['A', 'B', 'C', 'D']
  const optionLabels = { A: q.option_a, B: q.option_b, C: q.option_c, D: q.option_d }
  const answered = !!q.my_answer
  const confirmed = q.answers_confirmed

  const optionClass = (opt) => {
    const base = 'w-full text-left px-4 py-3 rounded-lg border text-sm transition-colors flex items-center gap-3'
    if (q.is_voided) return `${base} border-white/10 bg-white/4 text-gray-500`
    if (confirmed) {
      if (opt === q.correct_option) return `${base} border-green-500/40 bg-green-500/10 text-green-300`
      if (opt === q.my_answer && opt !== q.correct_option) return `${base} border-red-500/30 bg-red-500/5 text-red-400`
      return `${base} border-white/5 bg-white/2 text-gray-600`
    }
    if (opt === q.my_answer) return `${base} border-red-500/40 bg-red-500/10 text-white`
    if (answered) return `${base} border-white/5 bg-white/2 text-gray-600`
    return `${base} border-white/10 bg-white/4 text-gray-300 hover:border-white/20 hover:text-white`
  }

  return (
    <div className={`rounded-xl border p-5 ${q.is_voided ? 'border-white/5 opacity-50' : 'border-white/8'}`}>
      <p className="text-sm font-medium text-white mb-4 leading-relaxed">{q.question_text}</p>
      {q.is_voided ? (
        <p className="text-xs text-yellow-500">Voided — everyone scores</p>
      ) : (
        <div className="space-y-2">
          {options.map((opt) => (
            <button
              key={opt}
              disabled={answered || loading}
              onClick={() => onAnswer(q.id, opt)}
              className={optionClass(opt)}
            >
              <span className="text-xs font-mono font-bold w-5 shrink-0 text-gray-500">{opt}</span>
              <span>{optionLabels[opt]}</span>
              {confirmed && opt === q.correct_option && <span className="ml-auto text-xs text-green-400">✓</span>}
              {confirmed && opt === q.my_answer && opt !== q.correct_option && <span className="ml-auto text-xs text-red-400">✗</span>}
            </button>
          ))}
        </div>
      )}
      {!confirmed && answered && !q.is_voided && (
        <p className="text-xs text-gray-500 mt-3">Answer locked in — results confirmed after the race</p>
      )}
    </div>
  )
}
