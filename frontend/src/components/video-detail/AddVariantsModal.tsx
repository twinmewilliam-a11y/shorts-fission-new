

interface AddVariantsModalProps {
  isOpen: boolean
  onClose: () => void
  additionalVariantCount: number
  onCountChange: (count: number) => void
  onAddVariants: (count: number) => void
}

export function AddVariantsModal({
  isOpen,
  onClose,
  additionalVariantCount,
  onCountChange,
  onAddVariants
}: AddVariantsModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-surface-raised rounded-lg p-6 max-w-sm w-full mx-4 border border-border-subtle">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-text-primary">新增变体</h3>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-text-muted"
          >
            ✕
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-text-secondary text-sm">新增变体数量：</label>
            <input
              type="number"
              min="1"
              max="50"
              value={additionalVariantCount}
              onChange={(e) => onCountChange(parseInt(e.target.value) || 1)}
              className="w-full mt-1 px-3 py-2 border border-border-subtle rounded-lg text-text-primary bg-surface-raised"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 bg-gray-600 text-text-primary py-2 rounded-lg hover:bg-gray-700"
            >
              取消
            </button>
            <button
              onClick={() => {
                onAddVariants(additionalVariantCount)
                onClose()
              }}
              className="flex-1 bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700"
            >
              确认
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}