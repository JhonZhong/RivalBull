import { useState, type CSSProperties } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowUpRight, ArrowRight, Car, ShieldCheck, Layers, TrendingUp, Zap, Gem, Crown, LoaderCircle } from 'lucide-react'
import { fadeUp, stagger } from '../lib/motion'
import { useUIStore } from '../store/uiStore'
import { useExpertStore } from '../store/expertStore'
import { createTask } from '../lib/api'
import { ModelPicker } from '../components/ModelPicker'
import { BullMark } from '../components/BullMark'

const MODES = [
  { key: 'quick', icon: Zap, label: '快速速览', desc: '5 章 · 抓住核心问题' },
  { key: 'deep', icon: Gem, label: '深度调研', desc: '9 章 · 多维分析与交叉验证' },
  { key: 'expert', icon: Crown, label: '专家研判', desc: '12+ 章 · 深入战略与风险' },
]
const EXAMPLES = [
  { icon: Car, title: '谁在领跑新能源？', tag: '竞争格局', q: '分析特斯拉、比亚迪、理想在新能源车市场的产品力与定价竞争格局' },
  { icon: ShieldCheck, title: '找到竞品的长短板', tag: 'SWOT 分析', q: '为飞书、钉钉、企业微信做一份结构化 SWOT 竞争分析' },
  { icon: Layers, title: '好产品，差在哪里？', tag: '功能对标', q: '横向对比 Notion、飞书文档、Obsidian 的核心功能与定价' },
  { icon: TrendingUp, title: '下一片增长的草地', tag: '市场趋势', q: '梳理 2026 年 AI 笔记 / 知识管理赛道的关键趋势与代表玩家' },
]

export default function HomePage() {
  const navigate = useNavigate()
  const [text, setText] = useState('')
  const [mode, setMode] = useState('deep')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const model = useUIStore((s) => s.model)
  const experts = useExpertStore((s) => s.experts)

  async function submit(queryText: string) {
    const query = queryText.trim()
    if (!query || submitting) return
    setSubmitting(true)
    setError('')
    try {
      const resp = await createTask(query, mode, model)
      if (resp.needClarify) navigate(`/clarify/${resp.taskId}`, { state: { query, clarify: resp.clarifyQuestions } })
      else navigate(`/workspace/${resp.taskId}`, { state: { query } })
    } catch {
      setError('调研暂时没能出发。请确认后端与模型服务可用，再试一次；你的问题已保留。')
    } finally { setSubmitting(false) }
  }

  return <div className="pasture-home">
    <div className="pasture-topline">
      <span className="inline-flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-primary" /> RIVALBULL · 情报牧场</span>
      <span className="hidden sm:inline">让好问题，长出好答案。</span>
    </div>
    <section className="pasture-hero" aria-labelledby="welcome">
      <motion.div variants={fadeUp} initial="initial" animate="animate" className="pasture-hero-copy">
        <div className="pasture-eyebrow"><BullMark size={20} /> 48 位牛牛，各有所长</div>
        <h1 id="welcome">把问题交给牛牛，<br /><span>把洞察带回牧场。</span></h1>
        <p>钟钟牛带队，从真实信息中寻找线索。<br className="hidden lg:block" /> 竞品、市场与策略，一起研究个明白。</p>
      </motion.div>
      <img className="pasture-scene" src="/assets/brand/pasture.svg" alt="拿着放大镜和笔记本的牛牛，在牧场里寻找线索" />
    </section>

    <motion.section variants={fadeUp} initial="initial" animate="animate" className="research-desk" aria-label="发起调研">
      <div className="flex items-center justify-between gap-3">
        <label htmlFor="research-query" className="text-sm font-semibold text-ink">今天，想探索什么？</label>
        <span className="hidden text-[11px] text-ink-3 sm:inline">Ctrl / ⌘ + Enter 出发</span>
      </div>
      <textarea id="research-query" rows={3} value={text} onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && !e.nativeEvent.isComposing) { e.preventDefault(); void submit(text) } }}
        placeholder="例如：Notion、飞书文档和 Obsidian，谁更适合小团队？比较它们的功能与定价。"
        className="mt-4 w-full resize-y bg-transparent text-[15px] leading-7 text-ink outline-none placeholder:text-ink-3" />
      <div className="flex flex-wrap items-center gap-2 pb-5">
        {MODES.map((m) => <button key={m.key} type="button" onClick={() => setMode(m.key)} disabled={submitting}
          aria-pressed={mode === m.key} title={m.desc}
          className={`inline-flex h-8 items-center gap-1.5 rounded-full px-3 text-xs transition-colors ${mode === m.key ? 'bg-primary-tint font-semibold text-primary-deep ring-1 ring-primary/25' : 'text-ink-2 hover:bg-bg'}`}>
          <m.icon size={14} /> {m.label}
        </button>)}
        <span className="ml-auto text-[11px] text-ink-3">{MODES.find((m) => m.key === mode)?.desc}</span>
      </div>
      <div className="desk-footer">
        <ModelPicker disabled={submitting} />
        <button onClick={() => void submit(text)} disabled={!text.trim() || submitting} className="research-submit">
          {submitting ? <LoaderCircle size={18} className="animate-spin" /> : <BullMark size={22} />}
          {submitting ? '正在准备调研…' : '牛牛，出发！'} {!submitting && <ArrowUpRight size={18} />}
        </button>
      </div>
      {error && <p role="alert" className="mt-4 rounded-xl bg-risk/10 p-3 text-aux text-risk">{error}</p>}
    </motion.section>

    <section className="mt-8" aria-label="调研灵感">
      <div className="mb-3 flex items-center justify-between"><h2 className="text-xs font-semibold tracking-wide text-ink-2">从一个好问题开始</h2><span className="text-[11px] text-ink-3">挑一份调研灵感</span></div>
      <motion.div variants={stagger} initial="initial" animate="animate" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {EXAMPLES.map((ex, i) => <motion.button key={ex.title} variants={fadeUp} onClick={() => setText(ex.q)}
          className="inspiration-card" style={{ '--card-accent': ['#E8EFDB', '#F8E8C6', '#E2ECEE', '#F0E1D6'][i] } as CSSProperties}>
          <div className="flex items-center justify-between"><span className="inspiration-icon"><ex.icon size={18} /></span><ArrowUpRight size={15} className="text-ink-3" /></div>
          <span className="mt-3 text-sm font-semibold text-ink">{ex.title}</span><span className="mt-1 text-[11px] text-ink-2">{ex.tag}</span>
        </motion.button>)}
      </motion.div>
    </section>

    <button onClick={() => navigate('/experts')} className="team-invitation">
      <span className="flex -space-x-2">{experts.slice(0, 5).map((e) => <img key={e.id} src={e.avatar} alt={e.name} className="h-10 w-10 rounded-full border-[3px] border-bg" />)}</span>
      <span className="text-left"><span className="block text-xs font-semibold text-ink">认识你的牛牛团队</span><span className="text-[11px] text-ink-2">决策 · 策略 · 执行，各有拿手绝活</span></span>
      <ArrowRight size={17} className="ml-auto text-primary" />
    </button>
    <p className="pasture-footnote">小小牧场，认真研究。每一份结论，都让证据说话。</p>
  </div>
}
