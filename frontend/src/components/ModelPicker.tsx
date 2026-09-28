import { useEffect, useState } from 'react'
import { Cpu } from 'lucide-react'
import { fetchModels, type ModelCatalog } from '../lib/api'
import { useUIStore } from '../store/uiStore'

export function ModelPicker({ disabled = false }: { disabled?: boolean }) {
  const { model, setModel } = useUIStore()
  const [catalog, setCatalog] = useState<ModelCatalog | null>(null)
  const [error, setError] = useState(false)
  useEffect(() => {
    let active = true
    fetchModels().then((data) => {
      if (!active) return
      setCatalog(data)
      if (!data.options.some((m) => m.id === model && m.available)) setModel('auto')
    }).catch(() => { if (active) setError(true) })
    return () => { active = false }
  }, [model, setModel])
  return <div className="model-picker">
    <label className="flex items-center gap-2 text-aux font-semibold text-primary-deep">
      <Cpu size={16} />
      <span className="sr-only">调研模型</span>
      <select aria-label="调研模型" value={model} onChange={(e) => setModel(e.target.value)}
        disabled={disabled || !catalog} className="min-w-0 max-w-full cursor-pointer bg-transparent py-2 pr-3 outline-none disabled:cursor-wait">
        {!catalog && <option value="auto">{error ? '自动分工（列表暂不可用）' : '正在读取模型…'}</option>}
        {catalog?.options.map((m) => <option key={m.id} value={m.id} disabled={!m.available}>
          {m.label}{!m.available ? ' · 未启用' : ''}
        </option>)}
      </select>
    </label>
    <p className="text-[11px] leading-relaxed text-ink-2">
      {catalog ? model === 'auto'
        ? `核心 ${catalog.tiers.core} · 辅助 ${catalog.tiers.aux}`
        : '本次调研全程使用所选模型' : error ? '请确认后端已启动；重试时仍会验证模型配置。' : '读取当前服务配置'}
    </p>
  </div>
}
