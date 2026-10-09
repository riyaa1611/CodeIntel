import { useState } from 'react'
import { apiClient } from '../api/client'

interface Props {
  repoId: number
}

export default function ExportPanel({ repoId }: Props) {
  // CSV state
  const [csvFrom, setCsvFrom] = useState('')
  const [csvTo, setCsvTo] = useState('')
  const [csvLoading, setCsvLoading] = useState(false)
  const [csvError, setCsvError] = useState<string | null>(null)

  // PDF state
  const [pdfMonth, setPdfMonth] = useState(() => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  })
  const [pdfLoading, setPdfLoading] = useState(false)
  const [pdfError, setPdfError] = useState<string | null>(null)

  const downloadCsv = async () => {
    setCsvLoading(true)
    setCsvError(null)
    try {
      const params = new URLSearchParams()
      if (csvFrom) params.set('from_date', csvFrom)
      if (csvTo) params.set('to_date', csvTo)

      const response = await apiClient.get(
        `/api/repos/${repoId}/export/csv?${params.toString()}`,
        { responseType: 'blob' }
      )

      const url = URL.createObjectURL(new Blob([response.data as BlobPart], { type: 'text/csv' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `reviews_${repoId}${csvFrom ? `_from_${csvFrom}` : ''}${csvTo ? `_to_${csvTo}` : ''}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      setCsvError('Failed to export CSV')
    } finally {
      setCsvLoading(false)
    }
  }

  const downloadPdf = async () => {
    setPdfLoading(true)
    setPdfError(null)
    try {
      const response = await apiClient.get(
        `/api/repos/${repoId}/export/pdf?month=${pdfMonth}`,
        { responseType: 'blob' }
      )

      const url = URL.createObjectURL(new Blob([response.data as BlobPart], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `digest_${pdfMonth}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err: any) {
      const status = err?.response?.status
      if (status === 501) {
        setPdfError('PDF generation requires the reportlab package on the server.')
      } else {
        setPdfError('Failed to generate PDF')
      }
    } finally {
      setPdfLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-1">
          Export Data
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Download PR review data as CSV or generate a PDF monthly digest.
        </p>
      </div>

      {/* CSV Export */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-200">CSV Export</h4>
        <div className="flex flex-wrap gap-3">
          <div className="flex-1 min-w-36">
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
              From date
            </label>
            <input
              type="date"
              value={csvFrom}
              onChange={(e) => setCsvFrom(e.target.value)}
              className="input text-sm"
            />
          </div>
          <div className="flex-1 min-w-36">
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
              To date
            </label>
            <input
              type="date"
              value={csvTo}
              onChange={(e) => setCsvTo(e.target.value)}
              className="input text-sm"
            />
          </div>
        </div>
        {csvError && <p className="text-sm text-red-600 dark:text-red-400">{csvError}</p>}
        <button
          onClick={downloadCsv}
          disabled={csvLoading}
          className={`btn-secondary text-sm ${csvLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {csvLoading ? 'Generating…' : '⬇ Download CSV'}
        </button>
      </div>

      {/* PDF Digest */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-200">PDF Monthly Digest</h4>
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            Month
          </label>
          <input
            type="month"
            value={pdfMonth}
            onChange={(e) => setPdfMonth(e.target.value)}
            className="input text-sm"
          />
        </div>
        {pdfError && <p className="text-sm text-red-600 dark:text-red-400">{pdfError}</p>}
        <button
          onClick={downloadPdf}
          disabled={pdfLoading}
          className={`btn-secondary text-sm ${pdfLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {pdfLoading ? 'Generating…' : '⬇ Download PDF'}
        </button>
      </div>
    </div>
  )
}
