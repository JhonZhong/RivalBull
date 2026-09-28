import { test, expect, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'

// Browser-only fixtures: no real research or paid model request is made.
const experts = JSON.parse(readFileSync(new URL('../public/assets/experts.json', import.meta.url), 'utf8'))
const trace = { span_id: 'test-span', seq: 1, agent_id: 'L3-001', stage: 'intake', model: 'mimo-v2.6-pro', prompt: '测试提示', response: '测试输出', purpose: '拆解需求', prompt_tokens: 10, completion_tokens: 10, total_tokens: 20, latency_ms: 100, ts: '2026-09-28' }
const evidence = { evidence_id: 'e-test', source_url: 'https://example.com/source', source_type: 'official', title: '测试来源', excerpt: '保留真实出处', captured_at: '2026-09-28', credibility: .9, collected_by: 'L1-025' }
const claim = { claim_id: 'c-test', text: '浏览器测试结论', field: 'overview', evidence_ids: ['e-test'], confidence: 'high', cross_validated: true, author: 'L3-001' }
const report = { id: 'r-test', title: '浏览器测试报告', subtitle: '只用于界面验证', created_at: '2026-09-28', experts: ['L3-001', 'L1-025'], model_selection: 'mimo-v2.6-pro', toc: [{ id: 'summary', title: '摘要', level: 1 }], sections: [{ id: 'summary', title: '摘要', level: 1, paragraphs: ['保留原始研究内容。'], claims: [claim], data_grid: { columns: ['名称', '值', '指标', '来源', '链接'], rows: [{ name: '原始竞品', value: 42, metric: '测试指标', source: '官网', source_url: 'https://example.com/source' }] } }], charts: [], evidence: [evidence], claims: [claim], glossary: [{ term: '交叉验证', definition: '测试定义', source: 'Verda 四铁律' }], trace: [trace] }

async function fixtures(page: Page) {
  await page.route('**/api/**', async (route) => {
    const path = new URL(route.request().url()).pathname
    let body: unknown = []
    if (path === '/api/experts') body = experts
    else if (path === '/api/models') body = {
      options: [
        { id: 'auto', label: '自动分工', available: true },
        { id: 'mimo-v2.6-pro', label: 'MiMo-V2.6-Pro', available: true },
        { id: 'mimo-v2.6-flash', label: 'MiMo-V2.6-Flash', available: true },
        { id: 'mimo-v2.6-pro-ultraspeed', label: 'MiMo-V2.6-Pro-UltraSpeed', available: false },
      ], tiers: { core: 'mimo-v2.6-pro', aux: 'mimo-v2.6-flash', fast: 'mimo-v2.6-flash' },
    }
    else if (path === '/api/tasks') body = { taskId: 't-test', needClarify: true, clarifyQuestions: [{ id: 'focus', type: 'single', question: '想重点研究什么？', options: ['产品', '定价'] }] }
    else if (path.endsWith('/clarify')) body = { ok: true }
    else if (path.endsWith('/stream')) {
      const events = [
        ['message', { id: 'team-test', kind: 'team', members: ['L3-001', 'L1-025'] }],
        ['thought', { id: 'thought-test', expert: 'L3-001', kind: 'plan', text: '钟钟牛正在拆解调研需求', ts: Date.now() }],
        ['trace', trace],
      ]
      return route.fulfill({ contentType: 'text/event-stream', body: events.map(([type, data]) => `event: ${type}\ndata: ${JSON.stringify(data)}\n\n`).join('') })
    }
    else if (path === '/api/reports/r-test') body = report
    else if (path.endsWith('/trace')) body = { spans: [trace] }
    else if (path === '/api/reports') body = [{ ...report, evidence_count: 1, claim_count: 1, high_conf_count: 1 }]
    else if (path === '/api/dashboard') body = { reports: 1, evidence_total: 1, claim_total: 1, high_conf_total: 1, avg_evidence_per_report: 1, fact_accuracy: 100, platform_distribution: {}, brand_distribution: {} }
    else if (path === '/api/evidences') body = { items: [], facets: { total: 0, by_type: {}, by_brand: {} } }
    else if (path === '/api/experts/workload') body = [{ id: 'L3-001', name: '钟钟牛', title: '董事长', layer: 'L3', avatar: '/assets/avatars/L3-001.svg', missions: 1, claims_authored: 1, evidence_collected: 0 }]
    await route.fulfill({ json: body })
  })
}

test.beforeEach(async ({ page }) => { await fixtures(page) })

test('48 identities match all runtime catalogs and every portrait loads', async ({ page }) => {
  for (const path of ['../../branding/experts.json', '../../backend/app/data/experts.json', '../../api/app/data/experts.json']) {
    expect(JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'))).toEqual(experts)
  }
  expect(experts).toHaveLength(48)
  expect(new Set(experts.map((e: { name: string }) => e.name)).size).toBe(48)
  expect(experts.every((e: { name: string }) => /^.{2}牛$/.test(e.name))).toBeTruthy()
  await page.goto('/experts')
  await expect(page.locator('.cow-card')).toHaveCount(48)
  await page.locator('.cow-card').last().scrollIntoViewIfNeeded()
  await expect.poll(() => page.locator('.cow-card img').evaluateAll((imgs) => imgs.every((i) => (i as HTMLImageElement).naturalWidth > 0))).toBe(true)
  await page.getByPlaceholder('搜索专家、技能或知识标签').fill('饭团牛')
  await expect(page.locator('.cow-card')).toHaveCount(1)
  await page.locator('.cow-card').click()
  await expect(page.getByRole('heading', { name: '饭团牛' })).toBeVisible()
})

test('manual model reaches task creation, clarification and cow stream', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByLabel('调研模型')).toBeEnabled()
  await expect(page.getByRole('option', { name: /UltraSpeed/ })).toHaveJSProperty('disabled', true)
  await page.getByLabel('调研模型').selectOption('mimo-v2.6-pro')
  await page.getByLabel('今天，想探索什么？').fill('测试竞品需求')
  const request = page.waitForRequest((r) => new URL(r.url()).pathname === '/api/tasks' && r.method() === 'POST')
  await page.getByRole('button', { name: '牛牛，出发！' }).click()
  expect((await request).postDataJSON()).toEqual({ query: '测试竞品需求', mode: 'deep', model: 'mimo-v2.6-pro' })
  await expect(page).toHaveURL(/clarify\/t-test/)
  await page.getByRole('button', { name: '启动调研', exact: true }).click()
  await expect(page).toHaveURL(/workspace\/t-test/)
  await expect(page.getByText('钟钟牛正在拆解调研需求')).toBeVisible()
  await expect(page.locator('img[alt="钟钟牛"]').first()).toHaveAttribute('src', /L3-001.svg/)
})

test('failed creation stays on home with the query and an honest error', async ({ page }) => {
  await page.route('**/api/tasks', (r) => r.fulfill({ status: 503, json: { detail: 'unavailable' } }))
  await page.goto('/')
  await page.getByLabel('今天，想探索什么？').fill('保存这个问题')
  await page.getByRole('button', { name: '牛牛，出发！' }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  await expect(page.getByLabel('今天，想探索什么？')).toHaveValue('保存这个问题')
  await expect(page).toHaveURL('http://127.0.0.1:3410/')
})

test('all report views retain evidence and map stable expert IDs to cows', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (e) => errors.push(e.message))
  for (const route of ['/library', '/knowledge', '/dashboard', '/report/r-test', '/graph/r-test', '/trace/r-test']) {
    await page.goto(route)
    await expect(page.locator('body')).not.toHaveText('')
    await expect(page.locator('body')).not.toContainText(/青野|沈砚|林清越|GLM-5/)
    await expect(page).toHaveTitle(/RivalBull/)
    if (route === '/dashboard') {
      await expect(page.getByText('钟钟牛', { exact: true })).toBeAttached()
      await expect(page.locator('img[alt="钟钟牛"]')).toHaveAttribute('src', /L3-001.svg/)
    }
  }
  await expect(page.getByText('钟钟牛', { exact: true })).toBeVisible()
  await expect(page.getByText('mimo-v2.6-pro', { exact: true })).toBeVisible()
  await page.goto('/report/r-test')
  await expect(page.getByText('保留原始研究内容。', { exact: true })).toBeVisible()
  await expect(page.locator('a[href="https://example.com/source"]').first()).toBeAttached()
  await expect(page.getByText('RivalBull 四铁律')).toBeAttached()
  expect(errors).toEqual([])
})

test('offline expert fallback and empty research library use the same cow identity', async ({ page }) => {
  await page.route('**/api/experts', (r) => r.fulfill({ status: 503, body: '' }))
  await page.route('**/api/reports', (r) => r.fulfill({ json: [] }))
  await page.goto('/experts')
  await expect(page.locator('.cow-card')).toHaveCount(48)
  await page.getByRole('button', { name: /钟钟牛/ }).click()
  await expect(page.getByRole('heading', { name: '钟钟牛' })).toBeVisible()
  await expect(page.getByText('董事长 / 调研统筹')).toBeVisible()
  await page.goto('/library')
  await expect(page.getByText('还没有调研记录')).toBeVisible()
  await expect(page.locator('img[alt="牛牛等待开启第一次调研"]')).toHaveJSProperty('complete', true)
})

test('existing local knowledge and annotations survive the rebrand', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('verda.knowledge.v1', JSON.stringify([{ id: 'kb-old', reportId: 'r-test', reportTitle: '旧报告', kind: 'note', title: '旧收藏', content: '以前收藏的洞察', tags: [], createdAt: 1 }]))
    localStorage.setItem('verda.annotations.v1', JSON.stringify({ 'r-test': { edits: {}, highlights: [{ id: 'old-note', sectionId: 'summary', text: '保留原始研究内容', color: 'sun', comment: '以前写下的批注', createdAt: 1 }] } }))
  })
  await page.goto('/knowledge')
  await expect(page.getByText('以前收藏的洞察')).toBeVisible()
  await page.goto('/report/r-test')
  await expect(page.getByText('以前写下的批注')).toBeAttached()
})

test('CSV preserves research data and print keeps the RivalBull report', async ({ page }, info) => {
  await page.goto('/report/r-test')
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: '导出 CSV' }).click()
  const file = await (await download).path()
  expect(readFileSync(file!, 'utf8')).toContain('"原始竞品","42","测试指标","官网","https://example.com/source"')
  await page.emulateMedia({ media: 'print' })
  await expect(page.getByText('RivalBull · 牛牛调研报告')).toBeVisible()
  await expect(page.locator('.report-actions')).toBeHidden()
  await expect(page.getByText('RivalBull 四铁律')).toBeVisible()
  await expect(page.locator('a[href="https://example.com/source"]').last()).toBeVisible()
  const pdf = await page.pdf({ path: info.outputPath('report.pdf'), printBackground: true })
  expect(pdf.byteLength).toBeGreaterThan(1000)
})

test('home and pasture remain usable at desktop and mobile widths', async ({ page }, info) => {
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 })
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /把问题交给牛牛/ })).toBeVisible()
    await expect(page.getByLabel('调研模型')).toBeEnabled()
    await page.screenshot({ path: info.outputPath(`home-${width}.png`), fullPage: true })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.goto('/experts')
    await expect(page.locator('.cow-card')).toHaveCount(48)
    await page.screenshot({ path: info.outputPath(`experts-${width}.png`), fullPage: true })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  }
})
