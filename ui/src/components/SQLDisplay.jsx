import React, { useState } from 'react';
import { Card, Typography, Button, Space, message } from 'antd';
import { CopyOutlined, CheckOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Title, Paragraph, Text } = Typography;

const SQLDisplay = ({ sql, explanation }) => {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      message.success(t('copy_success'));
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      message.error(t('copy_failed'));
    }
  };

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          {t('generated_sql')}
        </Title>
        <Button
          type="text"
          icon={copied ? <CheckOutlined /> : <CopyOutlined />}
          onClick={handleCopy}
          style={{ color: copied ? '#52c41a' : undefined }}
        >
          {copied ? t('copied') : t('copy')}
        </Button>
      </div>
      
      <div style={{ marginBottom: 16 }}>
        <div style={{
          background: '#f6f8fa',
          border: '1px solid #d1d9e0',
          borderRadius: '6px',
          padding: '16px',
          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
          fontSize: '14px',
          lineHeight: '1.45',
          overflow: 'auto'
        }}>
          <Text code style={{ background: 'transparent', padding: 0 }}>
            {sql}
          </Text>
        </div>
      </div>

      {explanation && (
        <div>
          <Title level={5}>{t('sql_explanation')}</Title>
          <Paragraph style={{ color: '#666' }}>
            {explanation}
          </Paragraph>
        </div>
      )}
    </Card>
  );
};

export default SQLDisplay;