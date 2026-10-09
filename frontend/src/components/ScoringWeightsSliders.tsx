import { useEffect, useState } from 'react'
import { getRepoConfig, updateRepoConfig } from '../api/client'
import type { ScoringWeights } from '../types'
import { useAuth } from '@/contexts/AuthContext'

interface Props {
  repoId: number
}

const DIMENSIONS: { key: keyof ScoringWeights; label: string; color: string }[] = [
  { key: 'requirement', label: 'Requirement Alignment', color: 'bg-green-500' },
  { key: 'security', label: 'Security', color: 'bg-red-500' },
  { key: 'quality', label: 'Code Quality', color: 'bg-amber-500' },
  { key: 'performance', label: 'Performance', color: 'bg-purple-500' },
]

const DEFAULT_WEIGHTS: ScoringWeights = {
  requirement: 30,
  security: 30,
  quality: 20,
  performance: 20,
}

export default function ScoringWeightsSliders({ repoId }: Props) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [weights, setWeights] = useState<ScoringWeights>(DEFAULT_WEIGHTS)
  const [scanThreshold, setScanThreshold] = useState<number | null>(null)
  const [thresholdEnabled, setThresholdEnabled] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    setLoading(true)
    getRepoConfig(repoId)
      .then((cfg) => {
        setWeights(cfg.weights)
        if (cfg.scan_threshold != null) {
          setScanThreshold(cfg.scan_threshold)
          setThresholdEnabled(true)
        } else {
          setScanThreshold(60)
          setThresholdEnabled(false)
        }
      })
      .catch(() => setError('Failed to load scoring config'))
      .finally(() => setLoading(false))
  }, [repoId])

  const total = weights.requirement + weights.security + weights.quality + weights.performance
  const isValid = total === 100

  const handleChange = (key: keyof ScoringWeights, value: number) => {
    setWeights((prev) => ({ ...prev, [key]: value }))
    setSuccess(false)
  }

  const handleSave = async () => {
    if (!isValid) return
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      const updated = await updateRepoConfig(
        repoId,
        weights,
        thresholdEnabled ? (scanThreshold ?? 60) : null
      )
      setWeights(updated.weights)
      if (updated.scan_threshold != null) {
        setScanThreshold(updated.scan_threshold)
        setThresholdEnabled(true)
      } else {
        setThresholdEnabled(false)
      }
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Failed to save scoring config')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-1">
          Scoring Weights
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Adjust how each dimension contributes to the overall PR score. Weights must sum to 100%.
          {!isAdmin && ' (Admin only — read-only view)'}
        </p>
      </div>

      <div className="space-y-4">
        {DIMENSIONS.map(({ key, label, color }) => (
          <div key={key}>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm text-gray-700 dark:text-gray-300">{label}</label>
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 w-10 text-right">
                {weights[key]}%
              </span>
            </div>
            <input
              type="range"
              min={5}
              max={80}
              value={weights[key]}
              disabled={!isAdmin}
              onChange={(e) => handleChange(key, Number(e.target.value))}
              className={`w-full h-2 rounded-lg appearance-none cursor-pointer accent-blue-600 ${
                !isAdmin ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            />
            <div className="mt-1 h-1 w-full rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className={`h-1 rounded-full transition-all ${color}`}
                style={{ width: `${weights[key]}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Total indicator */}
      <div className={`flex items-center justify-between rounded-lg px-4 py-2 text-sm font-medium ${
        isValid
          ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
          : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
      }`}>
        <span>Total</span>
        <span>{total}% {isValid ? '✓' : `(need ${100 - total > 0 ? '+' : ''}${100 - total} more)`}</span>
      </div>

      {/* Auto deep-scan threshold */}
      <div className="border-t border-gray-100 dark:border-gray-700 pt-5 space-y-3">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
          Auto Deep-Scan
        </h4>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-700 dark:text-gray-300">
            Trigger on low PR score
          </span>
          <button
            disabled={!isAdmin}
            onClick={() => isAdmin && setThresholdEnabled((v) => !v)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              thresholdEnabled ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
            } ${!isAdmin ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                thresholdEnabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        {thresholdEnabled && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm text-gray-600 dark:text-gray-400">
                Score threshold (send approval notification when PR scores below this)
              </label>
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 w-10 text-right">
                {scanThreshold ?? 60}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={scanThreshold ?? 60}
              disabled={!isAdmin}
              onChange={(e) => { setScanThreshold(Number(e.target.value)); setSuccess(false) }}
              className={`w-full h-2 rounded-lg appearance-none cursor-pointer accent-blue-600 ${
                !isAdmin ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            />
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      )}

      {isAdmin && (
        <button
          onClick={handleSave}
          disabled={!isValid || saving}
          className={`btn-primary w-full ${(!isValid || saving) ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {saving ? 'Saving…' : success ? '✓ Saved' : 'Save Settings'}
        </button>
      )}
    </div>
  )
}
