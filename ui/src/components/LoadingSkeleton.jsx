import React from 'react';
import { Skeleton, Card, Layout } from 'antd';

const { Header, Content } = Layout;

const LoadingSkeleton = () => {
  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Skeleton.Input style={{ width: 300, height: 32 }} active />
          <Skeleton.Input style={{ width: 120, height: 24 }} active />
        </div>
      </Header>
      
      <Content className="app-content">
        <div className="content-wrapper">
          <Card style={{ marginBottom: 16 }}>
            <Skeleton.Input style={{ width: 200, height: 24, marginBottom: 16 }} active />
            <Skeleton.Input style={{ width: '100%', height: 96, marginBottom: 12 }} active />
            <div style={{ display: 'flex', gap: 8 }}>
              <Skeleton.Button size="default" active />
              <Skeleton.Button size="default" active />
            </div>
          </Card>
          
          <Card style={{ marginBottom: 16 }}>
            <Skeleton.Input style={{ width: 150, height: 24, marginBottom: 16 }} active />
            <Skeleton paragraph={{ rows: 3 }} active />
          </Card>
          
          <Card>
            <Skeleton.Input style={{ width: 120, height: 24, marginBottom: 16 }} active />
            <Skeleton paragraph={{ rows: 4 }} active />
          </Card>
        </div>
      </Content>
    </Layout>
  );
};

export default LoadingSkeleton;