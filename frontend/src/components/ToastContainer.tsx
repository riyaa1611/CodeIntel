import { useToast } from '@/contexts/ToastContext'

const ICON: Record<string, string> = {
  success: '✓',
  error: '✕',
  warning: '!',
  info: 'i',
}

const BG: Record<string, string> = {
  success: 'bg-green-50 border-green-400 dark:bg-green-900/30 dark:border-green-600',
  error: 'bg-red-50 border-red-400 dark:bg-red-900/30 dark:border-red-600',
  warning: 'bg-yellow-50 border-yellow-400 dark:bg-yellow-900/30 dark:border-yellow-600',
  info: 'bg-blue-50 border-blue-400 dark:bg-blue-900/30 dark:border-blue-600',
}

const TITLE_COLOR: Record<string, string> = {
  success: 'text-green-800 dark:text-green-200',
  error: 'text-red-800 dark:text-red-200',
  warning: 'text-yellow-800 dark:text-yellow-200',
  info: 'text-blue-800 dark:text-blue-200',
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`flex items-start gap-3 rounded-lg border px-4 py-3 shadow-lg transition-all ${BG[toast.type]}`}
        >
          <span className="text-lg leading-none mt-0.5">{ICON[toast.type]}</span>
          <div className="flex-1 min-w-0">
            <p className={`font-semibold text-sm ${TITLE_COLOR[toast.type]}`}>{toast.title}</p>
            {toast.message && (
              <p className="text-xs text-gray-600 dark:text-gray-300 mt-0.5 truncate">{toast.message}</p>
            )}
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-lg leading-none ml-1"
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
