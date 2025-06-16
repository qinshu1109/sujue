import React, { useState, Suspense } from 'react';
import { Layout, Switch, Space, Typography, ConfigProvider, message, Spin } from 'antd';
import { useTranslation } from 'react-i18next';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import QueryInput from './components/QueryInput';
import SQLDisplay from './components/SQLDisplay';
import ResultTable from './components/ResultTable';
import { completeQuery } from './services/api';
import './App.css';

const { Header, Content } = Layout;
const { Title } = Typography;

function App() {
  const { t, i18n } = useTranslation();
  const [query, setQuery] = useState('');
  const [sqlResult, setSqlResult] = useState(null);
  const [tableData, setTableData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleLanguageChange = (checked) => {
    const newLang = checked ? 'en' : 'zh';
    i18n.changeLanguage(newLang);
    // 保存到localStorage
    localStorage.setItem('i18nextLng', newLang);
  };

  const handleQuerySubmit = async (queryText) => {
    setQuery(queryText);
    setLoading(true);
    setSqlResult(null);
    setTableData(null);
    
    try {
      // 使用真实API进行完整查询流程
      const result = await completeQuery(queryText);
      
      setSqlResult({
        sql: result.sql,
        explanation: result.explanation
      });
      
      setTableData({
        columns: result.columns,
        data: result.data
      });
      
      message.success(t('query_success'));
    } catch (error) {
      console.error('Query failed:', error);
      message.error(t('query_failed'));
    } finally {
      setLoading(false);
    }
  };

  const antdLocale = i18n.language === 'zh' ? zhCN : enUS;

  return (
    <ConfigProvider locale={antdLocale}>
      <Layout className="app-layout">
        <Header className="app-header">
          <div className="header-content">
            <Title level={2} style={{ color: 'white', margin: 0 }}>
              {t('app_title')}
            </Title>
            <Space>
              <span style={{ color: 'white' }}>{t('language_chinese')}</span>
              <Switch
                checked={i18n.language === 'en'}
                onChange={handleLanguageChange}
              />
              <span style={{ color: 'white' }}>{t('language_english')}</span>
            </Space>
          </div>
        </Header>
        
        <Content className="app-content">
          <div className="content-wrapper">
            <QueryInput
              onSubmit={handleQuerySubmit}
              loading={loading}
            />
            
            {sqlResult && (
              <SQLDisplay
                sql={sqlResult.sql}
                explanation={sqlResult.explanation}
              />
            )}
            
            {tableData && (
              <ResultTable
                columns={tableData.columns}
                data={tableData.data}
                loading={loading}
              />
            )}
          </div>
        </Content>
      </Layout>
    </ConfigProvider>
  );
}

export default App;