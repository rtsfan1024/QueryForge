import { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Col, Empty, Form, Input, Layout, Row, Select, Space, Table, Typography, message } from 'antd'
import Editor from '@monaco-editor/react'
import { addDatabase, generateSql, getDatabase, listDatabases, runQuery, type DatabaseSummary, type NaturalQueryResponse, type QueryResult, type SchemaTable } from './services/api'

const { Header, Content } = Layout

export function App() {
  const editorRef = useRef<{ setValue: (value: string) => void } | null>(null)
  const [databases, setDatabases] = useState<DatabaseSummary[]>([])
  const [selectedDb, setSelectedDb] = useState<string>('')
  const [tables, setTables] = useState<SchemaTable[]>([])
  const [sql, setSql] = useState('SELECT * FROM users')
  const [prompt, setPrompt] = useState('查询用户表的所有信息')
  const [generatedSql, setGeneratedSql] = useState('')
  const [naturalResponse, setNaturalResponse] = useState<NaturalQueryResponse | null>(null)
  const [result, setResult] = useState<QueryResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [dbForm] = Form.useForm<{ name: string; url: string; password?: string }>()

  useEffect(() => {
    void refreshDatabases()
  }, [])

  useEffect(() => {
    if (!selectedDb && databases.length > 0) {
      setSelectedDb(databases[0].name)
    }
  }, [databases, selectedDb])

  useEffect(() => {
    if (selectedDb) {
      void refreshSchema(selectedDb)
    }
  }, [selectedDb])

  useEffect(() => {
    if (editorRef.current && generatedSql) {
      editorRef.current.setValue(generatedSql)
    }
  }, [generatedSql])

  const columns = useMemo(() => result?.columns.map((column) => ({ title: column.name, dataIndex: column.name, key: column.name })) ?? [], [result])

  async function refreshDatabases() {
    const data = await listDatabases()
    setDatabases(data.items)
  }

  async function refreshSchema(name: string) {
    const data = await getDatabase(name)
    setTables([...data.tables, ...data.views])
  }

  async function onAddDatabase() {
    const values = await dbForm.validateFields()
    setLoading(true)
    try {
      await addDatabase(values.name, values.url, values.password)
      message.success('数据库已添加')
      await refreshDatabases()
      setSelectedDb(values.name)
      await refreshSchema(values.name)
      dbForm.resetFields()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '添加数据库失败')
    } finally {
      setLoading(false)
    }
  }

  async function onRunQuery() {
    if (!selectedDb) {
      message.warning('请先选择数据库')
      return
    }
    setLoading(true)
    try {
      const data = await runQuery(selectedDb, sql)
      setResult(data)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '执行 SQL 失败')
    } finally {
      setLoading(false)
    }
  }

  async function onGenerateSql() {
    if (!selectedDb) {
      message.warning('请先选择数据库')
      return
    }
    setLoading(true)
    try {
      const data = await generateSql(selectedDb, prompt)
      setNaturalResponse(data)
      if (data.generatedSql) {
        setGeneratedSql(data.generatedSql)
        setSql(data.generatedSql)
        editorRef.current?.setValue(data.generatedSql)
      }
      if (data.result) {
        setResult(data.result)
      }
      if (data.validationError) {
        message.warning(`校验失败：${data.validationError}`)
      } else if (data.executionError) {
        message.warning(`执行失败：${data.executionError}`)
      } else {
        message.success('SQL 已生成并同步到编辑器')
      }
    } catch (error) {
      message.error(error instanceof Error ? error.message : '生成 SQL 失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f7fb' }}>
      <Header style={{ background: '#fff', borderBottom: '1px solid #e8e8e8' }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          DB Query Explorer
        </Typography.Title>
      </Header>
      <Content style={{ padding: 24 }}>
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Card title="数据库连接管理">
            <Form form={dbForm} layout="inline">
              <Form.Item name="name" label="连接名" rules={[{ required: true, message: '请输入连接名' }]}>
                <Input placeholder="demo" />
              </Form.Item>
              <Form.Item name="url" label="数据库 URL" rules={[{ required: true, message: '请输入数据库 URL' }]}>
                <Input placeholder="postgres://postgres@localhost:5432/postgres" style={{ width: 320 }} />
              </Form.Item>
              <Form.Item name="password" label="密码">
                <Input.Password placeholder="postgres" />
              </Form.Item>
              <Form.Item>
                <Button type="primary" loading={loading} onClick={() => void onAddDatabase()}>
                  添加数据库
                </Button>
              </Form.Item>
              <Form.Item label="当前数据库">
                <Select
                  style={{ width: 220 }}
                  value={selectedDb}
                  onChange={(value) => setSelectedDb(value)}
                  options={databases.map((item) => ({ label: item.name, value: item.name }))}
                />
              </Form.Item>
            </Form>
          </Card>

          <Row gutter={16}>
            <Col span={10}>
              <Card title="Schema（模式）浏览">
                {tables.length > 0 ? (
                  <Table
                    rowKey={(record) => record.id}
                    columns={[
                      { title: '对象名', dataIndex: 'objectName', key: 'objectName' },
                      { title: '类型', dataIndex: 'objectType', key: 'objectType' },
                    ]}
                    dataSource={tables}
                    pagination={false}
                  />
                ) : (
                  <Empty description="暂无元数据，添加数据库后展示表与视图" />
                )}
              </Card>
            </Col>
            <Col span={14}>
              <Card title="SQL 编辑器">
                <Editor
                  height="240px"
                  defaultLanguage="sql"
                  value={sql}
                  onMount={(editor) => {
                    editorRef.current = editor
                  }}
                  onChange={(value) => setSql(value ?? '')}
                  options={{ minimap: { enabled: false } }}
                />
                <Space style={{ marginTop: 12 }}>
                  <Button type="primary" loading={loading} onClick={() => void onRunQuery()}>
                    执行 SQL
                  </Button>
                  <Button onClick={() => void onGenerateSql()}>生成 SQL</Button>
                </Space>
              </Card>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={10}>
              <Card title="自然语言输入">
                <Input.TextArea rows={6} value={prompt} onChange={(event) => setPrompt(event.target.value)} />
                <Button type="primary" loading={loading} style={{ marginTop: 12 }} onClick={() => void onGenerateSql()}>
                  生成 SQL
                </Button>
                {naturalResponse?.generatedSql ? (
                  <Typography.Paragraph style={{ marginTop: 12 }}>
                    已生成 SQL：{naturalResponse.generatedSql}
                  </Typography.Paragraph>
                ) : null}
                {naturalResponse?.validationError ? (
                  <Typography.Paragraph style={{ marginTop: 12, color: '#cf1322' }}>
                    校验失败：{naturalResponse.validationError}
                  </Typography.Paragraph>
                ) : null}
                {naturalResponse?.executionError ? (
                  <Typography.Paragraph style={{ marginTop: 12, color: '#cf1322' }}>
                    执行失败：{naturalResponse.executionError}
                  </Typography.Paragraph>
                ) : null}
              </Card>
            </Col>
            <Col span={14}>
              <Card title="查询结果">
                {result ? (
                  <>
                    <Typography.Paragraph>
                      行数 {result.rowCount}，应用限制 {result.appliedLimit}，耗时 {result.durationMs}ms
                    </Typography.Paragraph>
                    <Table rowKey={(record) => String((record as { id?: string | number }).id ?? Math.random())} columns={columns} dataSource={result.rows} pagination={false} />
                  </>
                ) : (
                  <Empty description="暂无查询结果" />
                )}
              </Card>
            </Col>
          </Row>
        </Space>
      </Content>
    </Layout>
  )
}
