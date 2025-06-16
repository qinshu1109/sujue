import React from 'react';
import { Card, Table, Typography, Empty } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;

const ResultTable = ({ columns, data, loading }) => {
  const { t } = useTranslation();

  if (!columns || !data) {
    return null;
  }

  return (
    <Card>
      <Title level={4}>{t('query_results')}</Title>
      
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            t('table_pagination', { 
              start: range[0], 
              end: range[1], 
              total 
            }),
          pageSizeOptions: ['10', '20', '50', '100']
        }}
        scroll={{ x: 'max-content' }}
        locale={{
          emptyText: (
            <Empty
              description={t('no_data')}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )
        }}
        size="middle"
      />
      
      {data && data.length > 0 && (
        <div style={{ marginTop: 16, fontSize: '12px', color: '#999' }}>
          {t('total_records', { count: data.length })}
        </div>
      )}
    </Card>
  );
};

export default ResultTable;