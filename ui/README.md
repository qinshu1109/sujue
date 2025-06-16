# 女娲智能Text-to-SQL系统 - 前端UI

这是text2sql-mvp0项目的React前端界面，提供自然语言到SQL查询的用户交互界面。

## 功能特性

- 🌍 **国际化支持**: 支持中文和英文界面切换
- 📱 **响应式设计**: 适配桌面和移动设备
- 🎨 **现代UI**: 基于Ant Design 5的现代化界面
- ⚡ **实时查询**: 支持自然语言实时转换为SQL
- 📋 **结果展示**: 清晰的SQL展示和查询结果表格
- 📄 **SQL解释**: 提供生成SQL的详细解释

## 技术栈

- **React 18**: 前端框架
- **Ant Design 5**: UI组件库
- **react-i18next**: 国际化解决方案
- **Axios**: HTTP客户端
- **TypeScript**: 类型安全的JavaScript

## 项目结构

```
ui/
├── public/                 # 静态资源
│   ├── index.html         # HTML模板
│   └── manifest.json      # PWA配置
├── src/
│   ├── components/        # React组件
│   │   ├── QueryInput.jsx # 查询输入组件
│   │   ├── SQLDisplay.jsx # SQL展示组件
│   │   └── ResultTable.jsx# 结果表格组件
│   ├── locales/          # 国际化语言包
│   │   ├── zh_CN.ts      # 中文语言包
│   │   └── en_US.ts      # 英文语言包
│   ├── services/         # API服务
│   │   ├── api.js        # 真实API服务
│   │   └── mockApi.js    # 模拟API服务
│   ├── App.jsx           # 主应用组件
│   ├── App.css           # 应用样式
│   ├── i18n.ts           # 国际化配置
│   ├── index.js          # 应用入口
│   └── index.css         # 全局样式
├── package.json          # 项目配置和依赖
├── .env                  # 环境变量
└── README.md             # 项目说明
```

## 快速开始

### 安装依赖

```bash
cd ui
npm install
```

### 开发模式

```bash
npm start
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
npm run build
```

### 运行测试

```bash
npm test
```

## 配置说明

### 环境变量

在 `.env` 文件中配置以下变量：

- `REACT_APP_API_BASE_URL`: 后端API地址（默认: http://localhost:8000）
- `REACT_APP_NAME`: 应用名称
- `REACT_APP_VERSION`: 应用版本

### 国际化

项目支持中英文切换：

- 中文语言包: `src/locales/zh_CN.ts`
- 英文语言包: `src/locales/en_US.ts`

## API集成

### 模拟API (开发阶段)

当前使用 `mockApi.js` 提供模拟数据，支持：
- 用户查询示例
- 订单查询示例  
- 产品查询示例
- 数据库表结构查询

### 真实API集成

`api.js` 文件提供与FastAPI后端的完整集成：

```javascript
// 生成SQL
const result = await textToSqlApi.generateSql('显示所有用户');

// 执行查询
const data = await textToSqlApi.executeQuery(result.sql);
```

## 组件说明

### QueryInput 查询输入组件

- 支持多行文本输入
- 字符计数和限制
- 快捷键支持（Ctrl+Enter提交）
- 加载状态处理

### SQLDisplay SQL展示组件

- 语法高亮的SQL代码展示
- 一键复制功能
- SQL语句解释说明
- 响应式布局

### ResultTable 结果表格组件

- 可配置列定义
- 分页、排序、筛选
- 响应式表格
- 空状态处理

## 开发指南

### 添加新语言

1. 在 `src/locales/` 下创建新的语言文件
2. 在 `src/i18n.ts` 中注册新语言
3. 更新语言切换逻辑

### 自定义主题

修改 `src/App.css` 和组件样式文件来自定义界面主题。

### 添加新功能

1. 在 `src/components/` 下创建新组件
2. 在相应语言包中添加翻译文本
3. 在 `App.jsx` 中集成新组件

## 部署

### 开发环境

```bash
npm start
```

### 生产环境

```bash
npm run build
npm install -g serve
serve -s build -p 3000
```

### Docker部署

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 贡献指南

1. 遵循代码风格和ESLint规则
2. 为新功能添加适当的测试
3. 更新文档和类型定义
4. 确保国际化文本完整

## 许可证

本项目采用MIT许可证。