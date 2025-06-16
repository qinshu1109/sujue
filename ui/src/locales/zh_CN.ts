export default {
  // 应用标题和导航
  app_title: '女娲智能 Text-to-SQL 系统',
  
  // 查询输入组件
  query_input_title: '自然语言查询',
  query_input_placeholder: '请输入您想要查询的问题，例如：显示所有用户的姓名和邮箱',
  submit_query: '提交查询',
  clear: '清空',
  query_input_tip: '提示：使用 Ctrl+Enter 快速提交查询',
  
  // SQL展示组件
  generated_sql: '生成的SQL语句',
  sql_explanation: 'SQL语句解释',
  sql_explanation_example: '此查询从users表中选择所有包含指定关键词的用户记录',
  copy: '复制',
  copied: '已复制',
  copy_success: 'SQL语句已复制到剪贴板',
  copy_failed: '复制失败，请手动复制',
  
  // 结果表格组件
  query_results: '查询结果',
  no_data: '暂无数据',
  total_records: '共 {{count}} 条记录',
  table_pagination: '显示第 {{start}} 到 {{end}} 条记录，共 {{total}} 条',
  
  // 通用字段
  name: '姓名',
  email: '邮箱',
  id: 'ID',
  
  // 错误信息
  network_error: '网络错误，请检查连接',
  server_error: '服务器错误，请稍后重试',
  invalid_query: '查询格式无效，请重新输入',
  
  // 加载状态
  loading: '加载中...',
  processing: '处理中...',
  
  // 按钮文本
  retry: '重试',
  cancel: '取消',
  confirm: '确认',
  
  // 操作反馈
  query_success: '查询成功',
  query_failed: '查询失败，请重试',
  
  // 语言切换
  language_chinese: '中文',
  language_english: 'English',
  
  // API相关
  default_explanation: '该查询用于检索指定条件的数据'
};