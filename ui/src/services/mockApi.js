// 模拟API服务，用于开发和测试
export const mockTextToSqlApi = {
  // 模拟生成SQL
  generateSql: async (query) => {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 根据查询内容返回不同的模拟结果
    if (query.toLowerCase().includes('用户') || query.toLowerCase().includes('user')) {
      return {
        sql: "SELECT id, name, email, created_at FROM users WHERE status = 'active' ORDER BY created_at DESC",
        explanation: "从用户表中查询所有活跃用户的ID、姓名、邮箱和创建时间，按创建时间倒序排列"
      };
    } else if (query.toLowerCase().includes('订单') || query.toLowerCase().includes('order')) {
      return {
        sql: "SELECT o.id, o.order_number, u.name as customer_name, o.total_amount, o.status FROM orders o JOIN users u ON o.user_id = u.id WHERE o.status != 'cancelled'",
        explanation: "查询所有非取消状态的订单信息，包括订单号、客户姓名、总金额和状态"
      };
    } else if (query.toLowerCase().includes('产品') || query.toLowerCase().includes('product')) {
      return {
        sql: "SELECT id, name, price, category, stock_quantity FROM products WHERE stock_quantity > 0 AND status = 'active'",
        explanation: "查询所有有库存且状态为活跃的产品信息"
      };
    } else {
      return {
        sql: "SELECT * FROM information_schema.tables WHERE table_schema = 'public'",
        explanation: "查询数据库中所有公共表的信息"
      };
    }
  },

  // 模拟执行查询
  executeQuery: async (sql) => {
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // 根据SQL内容返回不同的模拟数据
    if (sql.includes('users')) {
      return {
        columns: [
          { title: 'ID', dataIndex: 'id', key: 'id' },
          { title: '姓名', dataIndex: 'name', key: 'name' },
          { title: '邮箱', dataIndex: 'email', key: 'email' },
          { title: '创建时间', dataIndex: 'created_at', key: 'created_at' }
        ],
        data: [
          { key: 1, id: 1, name: '张三', email: 'zhangsan@example.com', created_at: '2024-01-15' },
          { key: 2, id: 2, name: '李四', email: 'lisi@example.com', created_at: '2024-01-16' },
          { key: 3, id: 3, name: '王五', email: 'wangwu@example.com', created_at: '2024-01-17' },
          { key: 4, id: 4, name: 'John Doe', email: 'john@example.com', created_at: '2024-01-18' },
          { key: 5, id: 5, name: 'Jane Smith', email: 'jane@example.com', created_at: '2024-01-19' }
        ],
        execution_time: '0.023s'
      };
    } else if (sql.includes('orders')) {
      return {
        columns: [
          { title: '订单ID', dataIndex: 'id', key: 'id' },
          { title: '订单号', dataIndex: 'order_number', key: 'order_number' },
          { title: '客户姓名', dataIndex: 'customer_name', key: 'customer_name' },
          { title: '总金额', dataIndex: 'total_amount', key: 'total_amount' },
          { title: '状态', dataIndex: 'status', key: 'status' }
        ],
        data: [
          { key: 1, id: 1001, order_number: 'ORD-20240101-001', customer_name: '张三', total_amount: 299.99, status: '已完成' },
          { key: 2, id: 1002, order_number: 'ORD-20240101-002', customer_name: '李四', total_amount: 156.50, status: '处理中' },
          { key: 3, id: 1003, order_number: 'ORD-20240101-003', customer_name: '王五', total_amount: 89.99, status: '已发货' }
        ],
        execution_time: '0.045s'
      };
    } else if (sql.includes('products')) {
      return {
        columns: [
          { title: '产品ID', dataIndex: 'id', key: 'id' },
          { title: '产品名称', dataIndex: 'name', key: 'name' },
          { title: '价格', dataIndex: 'price', key: 'price' },
          { title: '分类', dataIndex: 'category', key: 'category' },
          { title: '库存', dataIndex: 'stock_quantity', key: 'stock_quantity' }
        ],
        data: [
          { key: 1, id: 2001, name: 'iPhone 15', price: 6999.00, category: '电子产品', stock_quantity: 50 },
          { key: 2, id: 2002, name: 'MacBook Pro', price: 12999.00, category: '电子产品', stock_quantity: 25 },
          { key: 3, id: 2003, name: 'AirPods Pro', price: 1899.00, category: '电子产品', stock_quantity: 100 }
        ],
        execution_time: '0.031s'
      };
    } else {
      return {
        columns: [
          { title: '表名', dataIndex: 'table_name', key: 'table_name' },
          { title: '表类型', dataIndex: 'table_type', key: 'table_type' }
        ],
        data: [
          { key: 1, table_name: 'users', table_type: 'BASE TABLE' },
          { key: 2, table_name: 'orders', table_type: 'BASE TABLE' },
          { key: 3, table_name: 'products', table_type: 'BASE TABLE' }
        ],
        execution_time: '0.012s'
      };
    }
  }
};

// 完整的模拟查询流程
export const mockCompleteQuery = async (naturalLanguageQuery) => {
  try {
    // 1. 生成SQL
    const sqlResult = await mockTextToSqlApi.generateSql(naturalLanguageQuery);
    
    // 2. 执行SQL查询
    const queryResult = await mockTextToSqlApi.executeQuery(sqlResult.sql);
    
    return {
      sql: sqlResult.sql,
      explanation: sqlResult.explanation,
      columns: queryResult.columns,
      data: queryResult.data,
      executionTime: queryResult.execution_time
    };
  } catch (error) {
    console.error('Mock query failed:', error);
    throw error;
  }
};