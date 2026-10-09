import { useState } from 'react'
import { updateSlackWebhook } from '../api/client'

interface Props {
  repoId: number
  currentWebhook: string | null
  onUpdated: (url: string) => void
}

export default function SlackSetup({ repoId, currentWebhook, onUpdated }: Props) {
  const [url, setUrl] = useState(currentWebhook || '')
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      await updateSlackWebhook(repoId, url)
      setSuccess(true)
      onUpdated(url)
    } catch {
      setError('Failed to update Slack webhook. Please check the URL.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600">
        Get notified in Slack whenever a PR review completes. Paste your{' '}
        <a
          href="https://api.slack.com/messaging/webhooks"
          target="_blank"
          rel="noreferrer"
          className="text-blue-600 hover:underline"
        >
          Slack Incoming Webhook URL
        </a>{' '}
        below.
      </p>

      <div className="flex gap-3">
        <input
          type="url"
          placeholder="https://hooks.slack.com/services/..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="input flex-1"
        />
        <button
          onClick={handleSave}
          disabled={saving || !url}
          className="btn-primary whitespace-nowrap"
        >
          {saving ? 'Saving…' : 'Save Webhook'}
        </button>
      </div>

      {success && (
        <p className="text-sm text-green-600">Slack webhook updated successfully.</p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {currentWebhook && (
        <p className="text-xs text-gray-400">
          Current: {currentWebhook.slice(0, 40)}…
        </p>
      )}
    </div>
  )
}
