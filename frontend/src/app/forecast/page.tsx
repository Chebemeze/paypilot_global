'use client';

import Layout from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Icons } from '@/components/icons';
import { useQuery } from '@tanstack/react-query';
import { formatCurrency, getStatusVariant } from '@/lib/utils';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { useState } from 'react';

export default function ForecastPage() {
  const { isLoading: authLoading, user, logout } = useAuth();
  const [selectedForecast, setSelectedForecast] = useState<any>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  const { data, isLoading: dataLoading, refetch } = useQuery({
    queryKey: ['forecast'],
    queryFn: async () => {
      const { data } = await api.get('/forecast/payroll-runway');
      return data;
    },
    enabled: !authLoading,
  });

  const isLoading = authLoading || dataLoading;

  const handleViewDetails = (forecast: any) => {
    setSelectedForecast(forecast);
    setShowDetailsModal(true);
  };

  const handleExport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      forecasts: data?.forecasts || [],
      summary: {
        total_wallets: data?.forecasts?.length || 0,
        shortfall_count: data?.forecasts?.filter((f: any) => f.status === 'SHORTFALL').length || 0,
        surplus_count: data?.forecasts?.filter((f: any) => f.status === 'SURPLUS').length || 0,
      },
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `forecast-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleRefresh = () => {
    refetch();
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

  const totalShortfall = data?.forecasts
    ?.filter((f: any) => f.status === 'SHORTFALL')
    .reduce((sum: number, f: any) => sum + (f.shortfall || 0), 0) || 0;

  const totalSurplus = data?.forecasts
    ?.filter((f: any) => f.status === 'SURPLUS')
    .reduce((sum: number, f: any) => sum + (f.surplus || 0), 0) || 0;

  return (
    <Layout user={user} onLogout={logout}>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-2xs font-black text-brand uppercase tracking-widest">
              Funding Intelligence
            </p>
            <h1 className="text-3xl font-bold text-ink mt-1">Wallet Funding Forecast</h1>
            <p className="text-text-muted mt-1">
              Real-time analysis of wallet balances against payroll obligations
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={handleRefresh}>
              <Icons.refresh className="mr-2" size={16} />
              Refresh
            </Button>
            <Button variant="secondary" onClick={handleExport}>
              <Icons.download className="mr-2" size={16} />
              Export
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-brand-soft rounded-lg flex items-center justify-center">
                <Icons.wallet className="text-brand" size={24} />
              </div>
              <div>
                <p className="text-sm text-text-muted">Total Wallets</p>
                <p className="text-2xl font-bold text-ink">{data?.forecasts?.length || 0}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-success-bg rounded-lg flex items-center justify-center">
                <Icons.trendUp className="text-success" size={24} />
              </div>
              <div>
                <p className="text-sm text-text-muted">Total Surplus</p>
                <p className="text-2xl font-bold text-success font-mono">
                  {formatCurrency(totalSurplus, 'USD')}
                </p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-danger-bg rounded-lg flex items-center justify-center">
                <Icons.trendDown className="text-danger" size={24} />
              </div>
              <div>
                <p className="text-sm text-text-muted">Total Shortfall</p>
                <p className="text-2xl font-bold text-danger font-mono">
                  {formatCurrency(totalShortfall, 'USD')}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Forecast Cards */}
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data?.forecasts?.map((forecast: any) => (
              <Card key={forecast.currency} hover>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-sm font-bold text-ink">{forecast.wallet_code}</p>
                    <p className="text-xs text-text-muted">{forecast.currency}</p>
                  </div>
                  <Badge variant={getStatusVariant(forecast.status)} size="md">
                    {forecast.status}
                  </Badge>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-text-muted font-semibold">Balance</span>
                    <span className="text-sm font-bold text-ink font-mono">
                      {formatCurrency(forecast.balance, forecast.currency)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-text-muted font-semibold">Required</span>
                    <span className="text-sm font-bold text-ink font-mono">
                      {formatCurrency(forecast.required, forecast.currency)}
                    </span>
                  </div>
                  <div className="gold-line my-3"></div>
                  <div className="flex justify-between items-center">
                    {forecast.status === 'SHORTFALL' ? (
                      <>
                        <span className="text-xs font-bold text-danger uppercase tracking-wider">
                          Shortfall
                        </span>
                        <span className="text-lg font-bold text-danger font-mono">
                          {formatCurrency(forecast.shortfall, forecast.currency)}
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="text-xs font-bold text-success uppercase tracking-wider">
                          Surplus
                        </span>
                        <span className="text-lg font-bold text-success font-mono">
                          {formatCurrency(forecast.surplus, forecast.currency)}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <p className="text-xs text-text-muted mt-4">{forecast.message}</p>

                <div className="mt-4 pt-4 border-t border-border">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full"
                    onClick={() => handleViewDetails(forecast)}
                  >
                    View Details
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Forecast Details Modal */}
      <Modal
        isOpen={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        title="Wallet Forecast Details"
        subtitle={`${selectedForecast?.wallet_code} - ${selectedForecast?.currency}`}
        size="lg"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowDetailsModal(false)}>
              Close
            </Button>
          </div>
        }
      >
        {selectedForecast && (
          <div className="space-y-6">
            {/* Overview */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-text-muted">Status</p>
                <Badge variant={getStatusVariant(selectedForecast.status)} size="md">
                  {selectedForecast.status}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-text-muted">Currency</p>
                <p className="font-semibold text-ink">{selectedForecast.currency}</p>
              </div>
            </div>

            {/* Financial Summary */}
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-canvas-subtle rounded-lg">
                <span className="text-sm text-text-muted">Current Balance</span>
                <span className="text-lg font-bold text-ink font-mono">
                  {formatCurrency(selectedForecast.balance, selectedForecast.currency)}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-canvas-subtle rounded-lg">
                <span className="text-sm text-text-muted">Required for Payroll</span>
                <span className="text-lg font-bold text-ink font-mono">
                  {formatCurrency(selectedForecast.required, selectedForecast.currency)}
                </span>
              </div>
              <div className="gold-line my-3"></div>
              <div className="flex justify-between items-center p-3 bg-canvas-subtle rounded-lg">
                {selectedForecast.status === 'SHORTFALL' ? (
                  <>
                    <span className="text-sm font-bold text-danger">Shortfall Amount</span>
                    <span className="text-xl font-bold text-danger font-mono">
                      {formatCurrency(selectedForecast.shortfall, selectedForecast.currency)}
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-sm font-bold text-success">Surplus Amount</span>
                    <span className="text-xl font-bold text-success font-mono">
                      {formatCurrency(selectedForecast.surplus, selectedForecast.currency)}
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Message */}
            <div className="p-4 bg-info-bg border border-info/20 rounded-lg">
              <p className="text-sm text-info-text">{selectedForecast.message}</p>
            </div>

            {/* Recommendations */}
            {selectedForecast.status === 'SHORTFALL' && (
              <div className="p-4 bg-warning-bg border border-warning/20 rounded-lg">
                <p className="text-sm font-bold text-warning-text mb-2">⚠️ Action Required</p>
                <p className="text-sm text-warning-text">
                  This wallet requires additional funding before payroll can be processed.
                  Please top up the wallet to ensure all payments can be completed.
                </p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </Layout>
  );
}
