'use client';

import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Layout from '@/components/layout/Layout';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Icons } from '@/components/icons';
import { formatCurrency, getStatusVariant } from '@/lib/utils';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isLoading: authLoading, user, logout } = useAuth();
  
  const { data: dashboard, isLoading: dataLoading, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/summary');
      return data;
    },
    enabled: !authLoading,
  });

  const isLoading = authLoading || dataLoading;

  const handleRefresh = () => {
    refetch();
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  };

  const handleExport = () => {
    // Export dashboard data as JSON
    const exportData = {
      timestamp: new Date().toISOString(),
      summary: dashboard,
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dashboard-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <Layout user={user} onLogout={logout}>
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
        </div>
      </Layout>
    );
  }

  const metrics = [
    {
      label: 'Total Employees',
      value: dashboard?.total_employees || 0,
      icon: Icons.users,
      trend: '+2 this month',
      trendUp: true,
    },
    {
      label: 'Ready to Pay',
      value: dashboard?.ready_employees || 0,
      icon: Icons.check,
      trend: '100% ready',
      trendUp: true,
    },
    {
      label: 'Stuck Employees',
      value: dashboard?.stuck_employees || 0,
      icon: Icons.alert,
      trend: 'Needs attention',
      trendUp: false,
    },
    {
      label: 'High Risk Items',
      value: dashboard?.high_risk_items || 0,
      icon: Icons.shield,
      trend: 'Review required',
      trendUp: false,
    },
  ];

  return (
    <Layout user={user} onLogout={logout}>
      <div className="space-y-8 animate-fade-in">
        {/* Hero Header */}
        <div className="gradient-navy rounded-2xl p-8 text-white shadow-lg">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Icons.sparkles className="text-gold" size={20} />
                <span className="text-gold-text text-xs font-bold uppercase tracking-widest">
                  Payroll Operations
                </span>
              </div>
              <h1 className="text-4xl font-bold mb-2">Dashboard</h1>
              <p className="text-blue-100 text-sm">
                Real-time overview of your borderless team payroll
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="secondary" size="sm" onClick={handleRefresh}>
                <Icons.refresh className="mr-2" size={16} />
                Refresh
              </Button>
              <Button variant="primary" size="sm" onClick={handleExport}>
                <Icons.download className="mr-2" size={16} />
                Export
              </Button>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.map((metric, idx) => {
            const Icon = metric.icon;
            return (
              <Card key={idx} hover>
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-brand-soft rounded-lg flex items-center justify-center">
                    <Icon className="text-brand" size={24} />
                  </div>
                  {metric.trendUp ? (
                    <Icons.trendUp className="text-success" size={16} />
                  ) : (
                    <Icons.trendDown className="text-danger" size={16} />
                  )}
                </div>
                <div>
                  <p className="text-text-muted text-sm mb-1">{metric.label}</p>
                  <p className="text-3xl font-bold text-ink">{metric.value}</p>
                  <p className={`text-xs mt-2 ${metric.trendUp ? 'text-success' : 'text-danger'}`}>
                    {metric.trend}
                  </p>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Wallet Balances */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader 
              title="Wallet Balances" 
              subtitle="Multi-currency holdings"
              action={
                <Button variant="ghost" size="sm" onClick={handleRefresh}>
                  <Icons.refresh size={16} />
                </Button>
              }
            />
            <div className="space-y-3">
              {dashboard?.wallet_balances?.map((wallet: any) => (
                <div
                  key={wallet.id}
                  className="flex items-center justify-between p-4 bg-canvas-subtle rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 gradient-navy-subtle rounded-lg flex items-center justify-center text-white text-sm font-bold">
                      {wallet.wallet_code.substring(0, 2)}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-ink">{wallet.wallet_code}</p>
                      <p className="text-xs text-text-muted">{wallet.currency}</p>
                    </div>
                  </div>
                  <p className="text-lg font-bold text-ink font-mono">
                    {formatCurrency(wallet.balance, wallet.currency)}
                  </p>
                </div>
              ))}
            </div>
          </Card>

          {/* Payroll Totals */}
          <Card>
            <CardHeader 
              title="Payroll Totals" 
              subtitle="Current batch by currency"
              action={
                <Button variant="ghost" size="sm" onClick={() => router.push('/payroll')}>
                  View All <Icons.chevronRight size={16} />
                </Button>
              }
            />
            <div className="space-y-3">
              {Object.entries(dashboard?.payroll_totals_by_currency || {}).map(([currency, amount]) => (
                <div
                  key={currency}
                  className="flex items-center justify-between p-4 bg-canvas-subtle rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-brand rounded-lg flex items-center justify-center text-white text-sm font-bold">
                      {currency.charAt(0)}
                    </div>
                    <p className="text-sm font-semibold text-ink">{currency}</p>
                  </div>
                  <p className="text-lg font-bold text-ink font-mono">
                    {formatCurrency(amount as number, currency)}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Shortfalls Alert */}
        {dashboard?.forecast_shortfalls?.length > 0 && (
          <Card className="border-warning/50 bg-warning-bg">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-warning rounded-lg flex items-center justify-center flex-shrink-0">
                <Icons.alert className="text-white" size={24} />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-warning-text mb-2">
                  Wallet Shortfalls Detected
                </h3>
                <p className="text-sm text-warning-text mb-4">
                  Top up these wallets before processing payroll
                </p>
                <div className="space-y-2">
                  {dashboard.forecast_shortfalls.map((shortfall: any) => (
                    <div
                      key={shortfall.currency}
                      className="flex items-center justify-between p-3 bg-white/60 rounded-lg"
                    >
                      <span className="text-sm font-semibold text-warning-text">
                        {shortfall.wallet_code}
                      </span>
                      <span className="text-sm font-bold text-danger font-mono">
                        Short by {formatCurrency(shortfall.shortfall, shortfall.currency)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Recent Webhooks */}
        <Card>
          <CardHeader 
            title="Recent Webhook Events" 
            subtitle="Verified BMONI events"
            action={
              <Button variant="ghost" size="sm" onClick={() => router.push('/webhooks')}>
                View All <Icons.chevronRight size={16} />
              </Button>
            }
          />
          <div className="space-y-2">
            {dashboard?.recent_webhooks?.slice(0, 5).map((event: any) => (
              <div
                key={event.id}
                className="flex items-center justify-between p-3 bg-canvas-subtle rounded-lg"
              >
                <div className="flex items-center gap-3">
                  {event.signature_valid && (
                    <div className="w-6 h-6 bg-success-bg rounded-full flex items-center justify-center">
                      <Icons.check className="text-success" size={14} />
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-mono font-semibold text-ink">
                      {event.event_type}
                    </p>
                    <p className="text-xs text-text-muted">
                      {new Date(event.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <Badge variant={getStatusVariant(event.state)} size="sm">
                  {event.state}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Layout>
  );
}
