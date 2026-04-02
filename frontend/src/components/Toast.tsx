import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'

export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

interface ToastProps {
  toast: Toast
  onDismiss: (id: string) => void
}

function ToastItem({ toast, onDismiss }: ToastProps) {
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsExiting(true)
      setTimeout(() => onDismiss(toast.id), 200)
    }, toast.duration || 5000)

    return () => clearTimeout(timer)
  }, [toast, onDismiss])

  const config = {
    success: {
      icon: CheckCircle,
      iconColor: 'text-success',
      borderColor: 'border-success/30',
      bgGlow: 'shadow-success/20',
    },
    error: {
      icon: XCircle,
      iconColor: 'text-error',
      borderColor: 'border-error/30',
      bgGlow: 'shadow-error/20',
    },
    warning: {
      icon: AlertTriangle,
      iconColor: 'text-warning',
      borderColor: 'border-warning/30',
      bgGlow: 'shadow-warning/20',
    },
    info: {
      icon: Info,
      iconColor: 'text-info',
      borderColor: 'border-info/30',
      bgGlow: 'shadow-info/20',
    },
  }

  const { icon: Icon, iconColor, borderColor, bgGlow } = config[toast.type]

  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-xl border bg-[#192134] shadow-xl ${borderColor} ${bgGlow}
        ${isExiting ? 'toast-exit' : 'toast-enter'}`}
      role="alert"
    >
      <Icon className={`w-5 h-5 flex-shrink-0 ${iconColor}`} />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-white">{toast.title}</p>
        {toast.message && (
          <p className="text-sm mt-1 text-gray-400 truncate">{toast.message}</p>
        )}
      </div>
      <button
        onClick={() => {
          setIsExiting(true)
          setTimeout(() => onDismiss(toast.id), 200)
        }}
        className="text-gray-500 hover:text-white transition-colors p-1"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

interface ToastContainerProps {
  toasts: Toast[]
  onDismiss: (id: string) => void
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-3 max-w-sm w-full px-4 sm:px-0">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

// Hook for managing toasts
export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    setToasts((prev) => [...prev, { ...toast, id }])
    return id
  }

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  const success = (title: string, message?: string) =>
    addToast({ type: 'success', title, message })

  const error = (title: string, message?: string) =>
    addToast({ type: 'error', title, message, duration: 8000 })

  const warning = (title: string, message?: string) =>
    addToast({ type: 'warning', title, message })

  const info = (title: string, message?: string) =>
    addToast({ type: 'info', title, message })

  return {
    toasts,
    addToast,
    dismissToast,
    success,
    error,
    warning,
    info,
  }
}
