import React, { useState } from 'react';
import { Card, Input, Button, Space, Typography } from 'antd';
import { SendOutlined, ClearOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { TextArea } = Input;
const { Title } = Typography;

const QueryInput = ({ onSubmit, loading }) => {
  const { t } = useTranslation();
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = () => {
    if (inputValue.trim()) {
      onSubmit(inputValue.trim());
    }
  };

  const handleClear = () => {
    setInputValue('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit();
    }
  };

  return (
    <Card>
      <Title level={4}>{t('query_input_title')}</Title>
      <Space direction="vertical" style={{ width: '100%' }}>
        <TextArea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder={t('query_input_placeholder')}
          rows={4}
          maxLength={1000}
          showCount
          disabled={loading}
        />
        <Space>
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSubmit}
            loading={loading}
            disabled={!inputValue.trim()}
          >
            {t('submit_query')}
          </Button>
          <Button
            icon={<ClearOutlined />}
            onClick={handleClear}
            disabled={loading || !inputValue}
          >
            {t('clear')}
          </Button>
        </Space>
        <div style={{ fontSize: '12px', color: '#999' }}>
          {t('query_input_tip')}
        </div>
      </Space>
    </Card>
  );
};

export default QueryInput;