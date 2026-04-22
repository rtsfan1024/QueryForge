export type DatabaseSummary = {
  name: string
  status: string
  lastConnectedAt: string | null
}

export type SchemaTable = {
  id: string
  dbName: string
  objectName: string
  objectType: 'table' | 'view'
  columnsJson: Array<{ name: string; type: string }>
  rawMetadataJson?: Record<string, unknown> | null
  refreshedAt: string
}

export type QueryResult = {
  columns: Array<{ name: string; type: string }>
  rows: Array<Record<string, unknown>>
  rowCount: number
  appliedLimit: number
  durationMs: number
  error?: { code: string; message: string } | null
}

export type NaturalQueryResponse = {
  generatedSql: string
  result: QueryResult | null
  validationError?: string | null
  executionError?: string | null
}

export type ApiError = {
  detail?: string | { msg?: string; message?: string }
}

const BASE_URL = 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!response.ok) {
    const text = await response.text()
    try {
      const json = JSON.parse(text) as ApiError | Array<{ detail?: string }>
      if (Array.isArray(json)) {
        throw new Error(json.map((item) => item.detail).filter(Boolean).join('; ') || text)
      }
      if (typeof json.detail === 'string') {
        throw new Error(json.detail)
      }
      if (json.detail && typeof json.detail === 'object') {
        throw new Error(json.detail.message ?? json.detail.msg ?? text)
      }
    } catch {
      throw new Error(text)
    }
  }
  return response.json() as Promise<T>
}

export function listDatabases(): Promise<{ items: DatabaseSummary[] }> {
  return request('/api/v1/dbs')
}

export function addDatabase(name: string, url: string, password?: string): Promise<DatabaseSummary> {
  return request(`/api/v1/dbs/${encodeURIComponent(name)}`, {
    method: 'POST',
    body: JSON.stringify({ url, password }),
  })
}

export function getDatabase(name: string): Promise<{ name: string; tables: SchemaTable[]; views: SchemaTable[] }> {
  return request(`/api/v1/dbs/${encodeURIComponent(name)}`)
}

export function runQuery(name: string, sql: string): Promise<QueryResult> {
  return request(`/api/v1/dbs/${encodeURIComponent(name)}/query`, {
    method: 'POST',
    body: JSON.stringify({ sql }),
  })
}

export function generateSql(name: string, prompt: string): Promise<NaturalQueryResponse> {
  return request(`/api/v1/dbs/${encodeURIComponent(name)}/query/natural`, {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  })
}
