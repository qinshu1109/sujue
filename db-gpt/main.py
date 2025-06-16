"""
DB-GPT Text2SQL 主服务
女娲造物：融合天地，化育万象
"""

import os
import json
import asyncio
import yaml
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from anthropic import AsyncAnthropic
import chromadb
from tenacity import retry, stop_after_attempt, wait_exponential

# 配置结构化日志
logger = structlog.get_logger()

# Prometheus指标
sql_generation_counter = Counter('text2sql_generation_total', 'Total SQL generation requests')
sql_execution_counter = Counter('text2sql_execution_total', 'Total SQL executions', ['status'])
response_time_histogram = Histogram('text2sql_response_seconds', 'Response time in seconds')
token_usage_counter = Counter('text2sql_tokens_total', 'Total tokens used', ['type'])

# 请求/响应模型
class Text2SQLRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

class Text2SQLResponse(BaseModel):
    sql: str
    result: Optional[List[Dict[str, Any]]] = None
    explanation: Optional[str] = None
    confidence: float
    execution_time_ms: float
    tokens_used: Dict[str, int]

# 初始化FastAPI应用
app = FastAPI(
    title="Text2SQL Service",
    description="女娲智能Text2SQL系统 - 将自然语言转换为SQL查询",
    version="0.1.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Text2SQLEngine:
    """核心Text2SQL引擎"""
    
    def __init__(self):
        self.db_engine = None
        self.async_session = None
        self.anthropic_client = None
        self.vector_db = None
        self.promptx_agents = {}
        self.security_config = {}
        self.config_file_path = Path(__file__).parent.parent / "config" / "security" / "allowed_tables.yml"
        self.config_last_modified = 0
        
    async def initialize(self):
        """初始化所有组件"""
        logger.info("初始化Text2SQL引擎...")
        
        # 数据库连接
        db_url = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        self.db_engine = create_async_engine(db_url, echo=True)
        self.async_session = sessionmaker(self.db_engine, class_=AsyncSession, expire_on_commit=False)
        
        # Claude客户端（通过代理）
        self.anthropic_client = AsyncAnthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            base_url=os.getenv('LLM_PROXY_URL', 'http://llm-proxy:8080')
        )
        
        # 向量数据库
        self.vector_db = chromadb.HttpClient(host=os.getenv('VECTOR_DB_URL', 'http://chromadb:8000'))
        
        # 加载Promptx智能体
        await self._load_promptx_agents()
        
        # 加载安全配置
        await self._load_security_config()
        
        # 启动Token指标导出器
        await self._start_metrics_exporter()
        
        # 初始化Debugger v2
        await self._init_debugger()
        
        logger.info("Text2SQL引擎初始化完成")
    
    async def _load_promptx_agents(self):
        """加载Promptx智能体配置"""
        agents_dir = "/app/promptx/agents"
        if os.path.exists(agents_dir):
            for filename in os.listdir(agents_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(agents_dir, filename), 'r') as f:
                        agent_config = json.load(f)
                        agent_name = agent_config['agent_name']
                        self.promptx_agents[agent_name] = agent_config
                        logger.info(f"加载智能体: {agent_name}")
        
        logger.info("PromptX智能体配置加载完成", agents=list(self.promptx_agents.keys()))
    
    async def _load_security_config(self):
        """加载安全配置"""
        try:
            if self.config_file_path.exists():
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    self.security_config = yaml.safe_load(f)
                self.config_last_modified = self.config_file_path.stat().st_mtime
                logger.info("安全配置加载成功", tables_count=len(self.security_config.get('allowed_tables', [])))
            else:
                # 默认配置
                self.security_config = {
                    'allowed_tables': ['users', 'products', 'orders', 'categories', 'inventory'],
                    'query_limits': {'max_joins': 5, 'max_subqueries': 3}
                }
                logger.warning("安全配置文件不存在，使用默认配置")
        except Exception as e:
            logger.error(f"安全配置加载失败: {str(e)}")
            self.security_config = {'allowed_tables': []}
    
    async def _reload_security_config_if_needed(self):
        """检查并重新加载安全配置（热加载）"""
        try:
            if self.config_file_path.exists():
                current_mtime = self.config_file_path.stat().st_mtime
                if current_mtime > self.config_last_modified:
                    # 记录变更前后差异
                    old_tables = set(self.security_config.get('allowed_tables', []))
                    
                    await self._load_security_config()
                    
                    new_tables = set(self.security_config.get('allowed_tables', []))
                    
                    # 计算变更
                    added_tables = new_tables - old_tables
                    removed_tables = old_tables - new_tables
                    
                    tables_diff = {
                        'added': list(added_tables),
                        'removed': list(removed_tables),
                        'total_before': len(old_tables),
                        'total_after': len(new_tables)
                    }
                    
                    logger.info("安全配置热重载完成", 
                               tables_diff=tables_diff,
                               config_file=str(self.config_file_path),
                               reload_time=datetime.utcnow().isoformat())
                    
                    # SQLGuardian事件记录
                    if added_tables or removed_tables:
                        logger.warning("SQLGuardian白名单变更检测", 
                                     security_event="WHITELIST_CHANGED",
                                     added_tables=list(added_tables),
                                     removed_tables=list(removed_tables))
                        
        except Exception as e:
            logger.error(f"配置热重载失败: {str(e)}")
    
    async def _start_metrics_exporter(self):
        """启动Token指标导出器"""
        try:
            import sys
            sys.path.append('/app/monitoring')
            from tokens_exporter import get_exporter
            
            self.metrics_exporter = get_exporter(port=9100)
            self.metrics_exporter.start_server()
            
            logger.info("Token指标导出器启动成功", port=9100)
            
        except ImportError:
            logger.warning("Token指标导出器模块未找到，跳过启动")
        except Exception as e:
            logger.error(f"启动Token指标导出器失败: {e}")
    
    async def _init_debugger(self):
        """初始化Debugger v2"""
        try:
            from debugger import get_debugger
            
            self.debugger = get_debugger(max_retries=3)
            
            logger.info("Debugger v2初始化成功", max_retries=3)
            
        except ImportError:
            logger.warning("Debugger模块未找到，跳过初始化")
        except Exception as e:
            logger.error(f"初始化Debugger失败: {e}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_sql(self, natural_query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """将自然语言转换为SQL"""
        sql_generation_counter.inc()
        
        try:
            # 1. Schema检索（通过SchemaSage）
            relevant_schema = await self._retrieve_schema(natural_query)
            
            # 2. 构建prompt
            prompt = self._build_prompt(natural_query, relevant_schema, context)
            
            # 3. 调用Claude生成SQL
            response = await self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0.2,
                system="你是一个SQL专家。基于提供的数据库schema，将自然语言查询转换为正确的SQL语句。只返回SQL语句，不要包含其他解释。",
                messages=[{"role": "user", "content": prompt}]
            )
            
            sql = response.content[0].text.strip()
            tokens_used = {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens
            }
            
            # 记录token使用到Prometheus
            token_usage_counter.labels(type='input').inc(tokens_used['input'])
            token_usage_counter.labels(type='output').inc(tokens_used['output'])
            
            # 记录到详细Token指标导出器
            if hasattr(self, 'metrics_exporter'):
                self.metrics_exporter.record_token_usage(
                    model="claude-3-opus-20240229",
                    input_tokens=tokens_used['input'],
                    output_tokens=tokens_used['output'],
                    endpoint="text2sql"
                )
            
            # 4. SQL验证（通过SQLGuardian）
            validation_result = await self._validate_sql(sql)
            
            if validation_result['status'] == 'BLOCK':
                raise ValueError(f"SQL被安全检查拦截: {validation_result['risks']}")
            
            if validation_result.get('fixed_sql'):
                sql = validation_result['fixed_sql']
            
            return {
                'sql': sql,
                'confidence': validation_result.get('confidence', 0.9),
                'tokens_used': tokens_used,
                'validation': validation_result
            }
            
        except Exception as e:
            logger.error(f"SQL生成失败: {str(e)}", exc_info=True)
            raise
    
    async def _retrieve_schema(self, query: str) -> str:
        """检索相关的数据库schema"""
        try:
            # 从向量数据库检索相关schema
            collection = self.vector_db.get_or_create_collection("db_schema")
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            
            if results['documents']:
                return "\n".join(results['documents'][0])
            return ""
        except Exception as e:
            logger.warning(f"Schema检索失败: {str(e)}")
            return ""
    
    def _build_prompt(self, query: str, schema: str, context: Optional[Dict[str, Any]]) -> str:
        """构建发送给Claude的prompt"""
        prompt = f"""数据库Schema:
{schema}

用户查询: {query}
"""
        
        if context:
            prompt += f"\n额外上下文: {json.dumps(context, ensure_ascii=False)}"
        
        prompt += "\n\n请生成对应的SQL查询语句。"
        return prompt
    
    async def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """通过SQLGuardian验证SQL - 强化安全防护"""
        import re
        
        # SQLGuardian配置
        guardian_config = self.promptx_agents.get('SQLGuardian', {})
        
        validation_result = {
            'status': 'PASS',
            'risks': [],
            'suggestions': [],
            'confidence': 0.95,
            'blocked_reason': None
        }
        
        # 1. 正则黑名单 - 严格阻断危险操作
        dangerous_patterns = [
            (r'(?i)\b(drop|delete|update|insert|alter|truncate|create|grant|revoke)\b', 'CRITICAL_OPERATION'),
            (r'(?i)\b(exec|execute|xp_|sp_)\b', 'SYSTEM_COMMAND'),
            (r'(?i)(union.*select|select.*union)', 'POSSIBLE_INJECTION'),
            (r'(?i)(;.*--|--.*)', 'SQL_COMMENT_INJECTION'),
            (r'(?i)(\|\||&&|concat)', 'STRING_MANIPULATION')
        ]
        
        sql_upper = sql.upper().strip()
        
        for pattern, risk_type in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                validation_result['status'] = 'BLOCK'
                validation_result['blocked_reason'] = risk_type
                validation_result['risks'].append(f"Blocked: {risk_type} detected in SQL")
                validation_result['confidence'] = 0.0
                logger.warning(f"SQLGuardian阻断: {risk_type}", sql=sql[:100])
                return validation_result
        
        # 2. 仅允许SELECT操作
        if not sql_upper.startswith('SELECT'):
            validation_result['status'] = 'BLOCK'
            validation_result['blocked_reason'] = 'NON_SELECT_OPERATION'
            validation_result['risks'].append("Only SELECT queries are allowed")
            return validation_result
        
        # 3. SELECT语句安全检查
        select_risks = []
        
        # 检查子查询深度
        subquery_count = sql_upper.count('SELECT') - 1
        if subquery_count > 2:
            select_risks.append("Deep nested subqueries detected")
            validation_result['confidence'] -= 0.1
        
        # 检查JOIN数量
        join_count = len(re.findall(r'\bjoin\b', sql_upper))
        if join_count > 5:
            select_risks.append("Too many JOINs may affect performance")
            validation_result['confidence'] -= 0.05
        
        # 检查通配符使用
        if 'SELECT *' in sql_upper:
            select_risks.append("SELECT * usage - consider specifying columns")
            validation_result['confidence'] -= 0.05
        
        if select_risks:
            validation_result['suggestions'] = select_risks
        
        # 4. 白名单表检查 - 热加载配置
        await self._reload_security_config_if_needed()
        allowed_tables = self.security_config.get('allowed_tables', [])
        
        # 简单表名提取
        from_match = re.search(r'from\s+(\w+)', sql_upper)
        if from_match:
            table_name = from_match.group(1).lower()
            if table_name not in allowed_tables:
                validation_result['status'] = 'WARN'
                validation_result['risks'].append(f"Table '{table_name}' not in whitelist")
                validation_result['confidence'] -= 0.2
        
        logger.info(f"SQLGuardian验证完成", 
                   status=validation_result['status'],
                   confidence=validation_result['confidence'])
        
        return validation_result
    
    async def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """执行SQL并返回结果"""
        try:
            async with self.async_session() as session:
                result = await session.execute(sql)
                
                # 根据SQL类型处理结果
                if sql.strip().upper().startswith('SELECT'):
                    rows = result.fetchall()
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    await session.commit()
                    return [{"affected_rows": result.rowcount}]
                    
        except Exception as e:
            sql_execution_counter.labels(status='failed').inc()
            logger.error(f"SQL执行失败: {str(e)}", sql=sql)
            
            # 触发Debugger v2进行自动修复
            if hasattr(self, 'debugger'):
                logger.info("触发Debugger v2自动修复", sql=sql[:100], error=str(e)[:200])
                
                fix_result = await self.debugger.auto_fix_sql(
                    original_sql=sql,
                    error_message=str(e),
                    context={'execution_context': 'sql_execution'}
                )
                
                if fix_result['success']:
                    logger.info("Debugger修复成功，重新执行SQL", 
                               session_id=fix_result['session_id'])
                    
                    # 重新执行修复后的SQL
                    try:
                        async with self.async_session() as session:
                            result = await session.execute(fix_result['fixed_sql'])
                            
                            if fix_result['fixed_sql'].strip().upper().startswith('SELECT'):
                                rows = result.fetchall()
                                columns = result.keys()
                                
                                sql_execution_counter.labels(status='success_after_fix').inc()
                                
                                return [dict(zip(columns, row)) for row in rows]
                            else:
                                await session.commit()
                                return [{"affected_rows": result.rowcount}]
                                
                    except Exception as retry_error:
                        logger.error(f"修复后SQL仍然失败: {str(retry_error)}")
                        # 记录修复失败但不再重试
                        sql_execution_counter.labels(status='failed_after_fix').inc()
                        
                else:
                    logger.warning("Debugger修复失败", 
                                 session_id=fix_result['session_id'],
                                 error_type=fix_result['error_type'])
            
            raise

# 创建全局引擎实例
engine = Text2SQLEngine()

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    await engine.initialize()

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    return generate_latest()

@app.post("/api/text2sql", response_model=Text2SQLResponse)
async def text2sql(request: Text2SQLRequest):
    """主要的Text2SQL API端点"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        # 生成SQL
        generation_result = await engine.generate_sql(
            request.query,
            request.context
        )
        
        # 执行SQL
        sql = generation_result['sql']
        result = await engine.execute_sql(sql)
        
        sql_execution_counter.labels(status='success').inc()
        
        # 计算响应时间
        execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
        response_time_histogram.observe(execution_time / 1000)
        
        return Text2SQLResponse(
            sql=sql,
            result=result,
            explanation=f"查询已成功执行，返回{len(result)}条结果",
            confidence=generation_result['confidence'],
            execution_time_ms=execution_time,
            tokens_used=generation_result['tokens_used']
        )
        
    except Exception as e:
        logger.error(f"Text2SQL请求失败: {str(e)}", query=request.query)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sql/validate")
async def validate_sql(sql: str):
    """SQL验证端点"""
    validation_result = await engine._validate_sql(sql)
    return validation_result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)