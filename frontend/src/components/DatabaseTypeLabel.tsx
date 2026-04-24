import { Tag } from 'antd'
import type { DatabaseType } from '../services/api'

const DB_TYPE_CONFIG: Record<DatabaseType, { label: string; color: string }> = {
  postgresql: { label: 'PostgreSQL', color: 'blue' },
  mysql: { label: 'MySQL', color: 'orange' },
}

export function DatabaseTypeLabel({ dbType }: { dbType: DatabaseType }) {
  const config = DB_TYPE_CONFIG[dbType] ?? { label: dbType, color: 'default' }
  return <Tag color={config.color}>{config.label}</Tag>
}
