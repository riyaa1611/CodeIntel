import { useEffect, useRef, useState } from 'react'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  LineChart,
  Line,
  Tooltip,
  XAxis,
} from 'recharts'
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  FileCode,
  Info,
  PlayCircle,
  XCircle,
} from 'lucide-react'
import {
  triggerDeepScan,
  getLatestDeepScan,
  getDeepScanHistory,
} from '../api/client'
import type { DeepScanResult, DeepScanHistoryItem } from '../types'

interface Props {
  repoId: number
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 75 ? 'bg-green-100 text-green-700' :
    score >= 50 ? 'bg-yellow-100 text-yellow-700' :
    'bg-red-100 text-red-700'
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-semibold ${color}`}>
      {score.toFixed(0)}
    </span>
  )
}

interface AccordionProps {
  title: string
  score: number
  content: string
}

function AccordionSection({ title, score, content }: AccordionProps) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      >
        <span className="flex items-center gap-2 font-medium text-sm text-gray-700">
          {title}
          <ScoreBadge score={score} />
        </span>
        {open ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
      </button>
      {open && (
        <div className="px-4 py-3 text-sm text-gray-600 leading-relaxed border-t border-gray-200">
          {content || 'No detailed feedback available.'}
        </div>
      )}
    </div>
  )
}

function ScanResults({ result }: { result: DeepScanResult }) {
  const radarData = [
    { subject: 'Architecture', value: result.architecture_score },
    { subject: 'Security', value: result.security_score },
    { subject: 'Duplication', value: result.duplication_score },
    { subject: 'Docs', value: result.documentation_score },
    { subject: 'Test Coverage', value: result.test_coverage_score },
    { subject: 'Overall', value: result.overall_score },
  ]

  return (
    <div className="space-y-6 mt-4">
      {/* Header: overall score + meta */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Overall Score</span>
          <ScoreBadge score={result.overall_score} />
        </div>
        <div className="flex items-center gap-1.5 text-xs text-gray-400">
          <FileCode className="w-3.5 h-3.5" />
          {result.files_analyzed} files analyzed
        </div>
        <div className="flex items-center gap-1.5 text-xs text-gray-400">
          <Clock className="w-3.5 h-3.5" />
          {new Date(result.created_at).toLocaleString()}
        </div>
      </div>

      {/* 6-axis radar chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
            <Radar
              name="Score"
              dataKey="value"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.25}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Critical findings */}
      {result.critical_findings.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-red-700 flex items-center gap-1.5 mb-2">
            <XCircle className="w-4 h-4" /> Critical Findings
          </h4>
          <ul className="space-y-1.5">
            {result.critical_findings.map((f, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700 p-2 bg-red-50 rounded-lg border border-red-100">
                <XCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0 mt-0.5" />
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-yellow-700 flex items-center gap-1.5 mb-2">
            <AlertTriangle className="w-4 h-4" /> Warnings
          </h4>
          <ul className="space-y-1.5">
            {result.warnings.map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700 p-2 bg-yellow-50 rounded-lg border border-yellow-100">
                <AlertTriangle className="w-3.5 h-3.5 text-yellow-500 flex-shrink-0 mt-0.5" />
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Positive observations */}
      {result.positive_observations.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-green-700 flex items-center gap-1.5 mb-2">
            <CheckCircle2 className="w-4 h-4" /> Positive Observations
          </h4>
          <ul className="space-y-1.5">
            {result.positive_observations.map((p, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700 p-2 bg-green-50 rounded-lg border border-green-100">
                <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0 mt-0.5" />
                {p}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended actions */}
      {result.recommended_actions.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-blue-700 flex items-center gap-1.5 mb-2">
            <Info className="w-4 h-4" /> Recommended Actions
          </h4>
          <ol className="space-y-1.5 list-none">
            {result.recommended_actions.map((a, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mt-0.5">
                  {i + 1}
                </span>
                {a}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Per-dimension accordion */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Detailed Feedback</h4>
        <div className="space-y-2">
          <AccordionSection title="Architecture" score={result.architecture_score} content={result.architecture_feedback} />
          <AccordionSection title="Security" score={result.security_score} content={result.security_feedback} />
          <AccordionSection title="Code Duplication" score={result.duplication_score} content={result.duplication_feedback} />
          <AccordionSection title="Documentation" score={result.documentation_score} content={result.documentation_feedback} />
          <AccordionSection title="Test Coverage" score={result.test_coverage_score} content={result.test_coverage_feedback} />
        </div>
      </div>
    </div>
  )
}

function HistorySparkline({ history }: { history: DeepScanHistoryItem[] }) {
  if (history.length < 2) return null
  const chartData = [...history].reverse().map((h, i) => ({
    i,
    score: Math.round(h.overall_score),
    date: new Date(h.created_at).toLocaleDateString(),
  }))

  return (
    <div className="mt-4">
      <p className="text-xs text-gray-500 mb-1">Scan history ({history.length} scans)</p>
      <ResponsiveContainer width="100%" height={60}>
        <LineChart data={chartData}>
          <XAxis dataKey="i" hide />
          <Tooltip
            formatter={(v: number) => [`${v}`, 'Score']}
            labelFormatter={(_, payload) => payload?.[0]?.payload?.date ?? ''}
            contentStyle={{ fontSize: 12 }}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function DeepScanPanel({ repoId }: Props) {
  const [result, setResult] = useState<DeepScanResult | null>(null)
  const [history, setHistory] = useState<DeepScanHistoryItem[]>([])
  const [scanning, setScanning] = useState(false)
  const [loadingLatest, setLoadingLatest] = useState(true)
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const buttonClickTimeRef = useRef<number>(0)

  // Load existing latest scan on mount
  useEffect(() => {
    Promise.all([
      getLatestDeepScan(repoId).catch(() => null),
      getDeepScanHistory(repoId).catch(() => []),
    ]).then(([latest, hist]) => {
      if (latest) setResult(latest)
      setHistory(hist)
      setLoadingLatest(false)
    })
  }, [repoId])

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
    }
  }

  useEffect(() => () => stopPolling(), [])

  const handleRunScan = async () => {
    setScanning(true)
    buttonClickTimeRef.current = Date.now()
    try {
      await triggerDeepScan(repoId)
    } catch {
      setScanning(false)
      return
    }

    // Poll every 5s for a result newer than the click time
    pollTimerRef.current = setInterval(async () => {
      try {
        const latest = await getLatestDeepScan(repoId)
        const resultTime = new Date(latest.created_at).getTime()
        // Accept result if created within 2 seconds before the click (clock skew tolerance)
        if (resultTime >= buttonClickTimeRef.current - 2000) {
          setResult(latest)
          setScanning(false)
          stopPolling()
          // Refresh history
          getDeepScanHistory(repoId)
            .then(setHistory)
            .catch(() => {})
        }
      } catch {
        // Result not ready yet, keep polling
      }
    }, 5000)
  }

  return (
    <div>
      {/* Action bar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-base font-semibold text-gray-800">Deep Scan</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            AI-powered full codebase analysis — architecture, security, duplication, docs, and tests.
          </p>
        </div>
        <button
          onClick={handleRunScan}
          disabled={scanning}
          className="btn-primary flex items-center gap-2"
        >
          <PlayCircle className="w-4 h-4" />
          {scanning ? 'Scanning…' : 'Run Deep Scan'}
        </button>
      </div>

      {/* Scanning state */}
      {scanning && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-blue-800">Analyzing repository…</p>
            <p className="text-xs text-blue-600 mt-0.5">This may take 30–60 seconds while the AI reviews your codebase.</p>
          </div>
        </div>
      )}

      {/* No results yet */}
      {!loadingLatest && !result && !scanning && (
        <div className="mt-6 text-center py-10 text-gray-400">
          <FileCode className="w-10 h-10 mx-auto mb-2 opacity-40" />
          <p className="text-sm">No scans yet. Click "Run Deep Scan" to analyze this repository.</p>
        </div>
      )}

      {/* Results */}
      {result && !scanning && <ScanResults result={result} />}

      {/* History sparkline */}
      {history.length >= 2 && !scanning && (
        <div className="card mt-4">
          <HistorySparkline history={history} />
        </div>
      )}
    </div>
  )
}
