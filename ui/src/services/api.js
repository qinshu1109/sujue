import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('Response Error:', error.response?.status, error.message);
    
    // 统一错误处理
    if (error.response?.status === 401) {
      // 处理未授权错误
      console.error('Unauthorized access');
    } else if (error.response?.status >= 500) {
      // 处理服务器错误
      console.error('Server error');
    }
    
    return Promise.reject(error);
  }
);

// API接口定义
export const textToSqlApi = {
  // 提交自然语言查询，生成SQL
  generateSql: async (query) => {
    try {
      const response = await api.post('/api/text2sql', {
        query: query,
        context: {
          language: 'zh',
          user_preferences: {}
        },
        session_id: `session_${Date.now()}`
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to generate SQL');
    }
  },

  // 执行SQL查询并返回结果
  executeQuery: async (sql) => {
    try {
      const response = await api.post('/api/v1/execute', {
        sql: sql,
        limit: 100
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to execute query');
    }
  },

  // 获取数据库表结构
  getSchema: async () => {
    try {
      const response = await api.get('/api/v1/schema');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get schema');
    }
  },

  // 验证SQL语句
  validateSql: async (sql) => {
    try {
      const response = await api.post('/api/sql/validate', {
        sql: sql
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to validate SQL');
    }
  },

  // 获取查询历史
  getHistory: async (limit = 20) => {
    try {
      const response = await api.get(`/api/v1/history?limit=${limit}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get history');
    }
  }
};

// 完整的查询流程：从自然语言到结果
export const completeQuery = async (naturalLanguageQuery) => {
  try {
    // 1. 生成SQL（FastAPI返回完整结果）
    const result = await textToSqlApi.generateSql(naturalLanguageQuery);
    
    return {
      sql: result.sql,
      explanation: result.explanation || 'Default query explanation',
      columns: result.result ? Object.keys(result.result[0] || {}).map(key => ({
        title: key,
        dataIndex: key,
        key: key
      })) : [],
      data: result.result || [],
      executionTime: result.execution_time_ms,
      confidence: result.confidence,
      tokens_used: result.tokens_used
    };
  } catch (error) {
    console.error('Complete query failed:', error);
    throw error;
  }
};

export default api;