import { useEffect, useState } from 'react'
import { getScanSchedule, upsertScanSchedule } from '../api/client'
import type { ScanFrequency, ScanSchedule } from '../types'
import { useAuth } from '@/contexts/AuthContext'

interface Props {
  repoId: number
}

const FREQUENCIES: { value: ScanFrequency; label: string; description: string }[] = [
  { value: 'daily', label: 'Daily', description: 'Every 24 hours' },
  { value: 'weekly', label: 'Weekly', description: 'Every 7 days' },
  { value: 'monthly', label: 'Monthly', description: 'Every 30 days' },
]

function formatDatetime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export default function ScanScheduler({ repoId }: Props) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [schedule, setSchedule] = useState<ScanSchedule | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Form state
  const [frequency, setFrequency] = useState<ScanFrequency>('weekly')
  const [enabled, setEnabled] = useState(true)

  useEffect(() => {
    setLoading(true)
    getScanSchedule(repoId)
      .then((sched) => {
        setSchedule(sched)
        if (sched) {
          setFrequency(sched.frequency)
          setEnabled(sched.enabled)
        }
      })
      .catch(() => setError('Failed to load scan schedule'))
      .finally(() => setLoading(false))
  }, [repoId])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      const updated = await upsertScanSchedule(repoId, frequency, enabled)
      setSchedule(updated)
      setFrequency(updated.frequency)
      setEnabled(updated.enabled)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Failed to save schedule')
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
          Scheduled Deep Scans
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Automatically run a deep codebase scan on a fixed cadence.
          {!isAdmin && ' (Admin only — read-only view)'}
        </p>
      </div>

      {/* Current status */}
      {schedule && (
        <div className="rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-3 text-sm space-y-1">
          <div className="flex items-center gap-2">
            <span className={`inline-block w-2 h-2 rounded-full ${schedule.enabled ? 'bg-green-500' : 'bg-gray-400'}`} />
            <span className="text-gray-700 dark:text-gray-200 font-medium">
              {schedule.enabled ? 'Active' : 'Paused'} — {schedule.frequency}
            </span>
          </div>
          {schedule.last_run_at && (
            <p className="text-gray-500 dark:text-gray-400 text-xs">
              Last run: {formatDatetime(schedule.last_run_at)}
            </p>
          )}
          <p className="text-gray-500 dark:text-gray-400 text-xs">
            Next run: {formatDatetime(schedule.next_run_at)}
          </p>
        </div>
      )}

      {!schedule && (
        <div className="rounded-lg bg-gray-50 dark:bg-gray-800 border border-dashed border-gray-300 dark:border-gray-600 px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
          No schedule configured yet.
        </div>
      )}

      {/* Frequency selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Frequency
        </label>
        <div className="grid grid-cols-3 gap-2">
          {FREQUENCIES.map((f) => (
            <button
              key={f.value}
              disabled={!isAdmin}
              onClick={() => isAdmin && setFrequency(f.value)}
              className={`rounded-lg border px-3 py-2 text-left transition-colors ${
                frequency === f.value
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                  : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:border-gray-300'
              } ${!isAdmin ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div className="text-sm font-medium">{f.label}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">{f.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Enable toggle */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-700 dark:text-gray-300">Enable schedule</span>
        <button
          disabled={!isAdmin}
          onClick={() => isAdmin && setEnabled((v) => !v)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            enabled ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
          } ${!isAdmin ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      )}

      {isAdmin && (
        <button
          onClick={handleSave}
          disabled={saving}
          className={`btn-primary w-full ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {saving ? 'Saving…' : success ? '✓ Saved' : schedule ? 'Update Schedule' : 'Enable Schedule'}
        </button>
      )}
    </div>
  )
}
