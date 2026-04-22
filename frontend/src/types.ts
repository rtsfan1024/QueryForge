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
