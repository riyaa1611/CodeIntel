import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { ChevronDown, ChevronUp, ExternalLink, FileText, Clock } from 'lucide-react'
import { getRepoPreview } from '../api/client'
import type { RepositoryPreview } from '../types'

interface Props {
  repoId: number
}

function relativeTime(dateStr: string): string {
  if (!dateStr) return ''
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 2592000) return `${Math.floor(diff / 86400)}d ago`
  return new Date(dateStr).toLocaleDateString()
}

export default function RepositoryPreview({ repoId }: Props) {
  const [data, setData] = useState<RepositoryPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [collapsed, setCollapsed] = useState(true)

  // Lazy-load: only fetch when expanded for the first time
  useEffect(() => {
    if (!collapsed && !data && !loading) {
      setLoading(true)
      setError(null)
      getRepoPreview(repoId)
        .then(setData)
        .catch(() => setError('Failed to load repository preview'))
        .finally(() => setLoading(false))
    }
  }, [collapsed, data, loading, repoId])

  return (
    <div className="card">
      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed((v) => !v)}
        className="w-full flex items-center justify-between text-left"
      >
        <span className="flex items-center gap-2 text-base font-semibold text-gray-800">
          <FileText className="w-4 h-4 text-blue-500" />
          Repository Preview
          {data?.last_updated && (
            <span className="flex items-center gap-1 text-xs text-gray-400 font-normal">
              <Clock className="w-3 h-3" />
              Last pushed {relativeTime(data.last_updated)}
            </span>
          )}
        </span>
        {collapsed ? (
          <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
        ) : (
          <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0" />
        )}
      </button>

      {!collapsed && (
        <div className="mt-4 space-y-4">
          {loading && (
            <div className="space-y-3 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-5/6" />
              <div className="h-4 bg-gray-200 rounded w-2/3" />
            </div>
          )}

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
              {error}
            </p>
          )}

          {data && (
            <>
              {/* Live deployment URLs */}
              {data.live_urls.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                    Detected Live URLs
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {data.live_urls.map((url) => (
                      <a
                        key={url}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700 hover:bg-blue-100 transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
                        <span className="truncate max-w-xs">{url}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* README */}
              {data.readme_markdown ? (
                <div className="prose prose-sm max-w-none border border-gray-200 rounded-lg p-4 overflow-auto max-h-[600px]">
                  <ReactMarkdown
                    components={{
                      code({ node, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '')
                        const isBlock = !props.ref && match
                        return isBlock ? (
                          <SyntaxHighlighter
                            style={oneDark as any}
                            language={match[1]}
                            PreTag="div"
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        )
                      },
                    }}
                  >
                    {data.readme_markdown}
                  </ReactMarkdown>
                </div>
              ) : (
                <p className="text-sm text-gray-400 italic">No README found for this repository.</p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
