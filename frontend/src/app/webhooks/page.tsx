'use client';

import Layout from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Icons } from '@/components/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatDateTime, getStatusVariant } from '@/lib/utils';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { useState } from 'react';

export default function WebhooksPage() {
  const queryClient = useQueryClient();
  const { isLoading: authLoading, user, logout } = useAuth();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedWebhook, setSelectedWebhook] = useState<any>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  const { data, isLoading: dataLoading } = useQuery({
    queryKey: ['webhooks'],
    queryFn: async () => {
      const { data } = await api.get('/webhooks/events');
      return data;
    },
    enabled: !authLoading,
  });

  const retryMutation = useMutation({
    mutationFn: async (webhookId: string) => {
      const { data } = await api.post(`/webhooks/events/${webhookId}/retry`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
    },
  });

  const simulateMutation = useMutation({
    mutationFn: async (eventData: any) => {
      const { data } = await api.post('/webhooks/simulate', eventData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
    },
  });

  const isLoading = authLoading || dataLoading;

  const handleViewDetails = (webhook: any) => {
    setSelectedWebhook(webhook);
    setShowDetailsModal(true);
  };

  const handleRetry = (webhookId: string) => {
    retryMutation.mutate(webhookId);
  };

  const handleSimulate = () => {
    const mockEvent = {
      event_type: 'employee.linked',
      payload: {
        employee_id: 'emp-001',
        status: 'active',
        timestamp: new Date().toISOString(),
      },
      signature_valid: true,
    };
    simulateMutation.mutate(mockEvent);
  };

  const handleExport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      webhooks: data?.items || [],
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `webhooks-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredWebhooks = data?.items?.filter((webhook: any) => {
    if (statusFilter === 'all') return true;
    if (statusFilter === 'processed') return webhook.processed;
    if (statusFilter === 'pending') return !webhook.processed;
    if (statusFilter === 'valid') return webhook.signature_valid;
    return true;
  }) || [];

  if (isLoading) {
    return (
      <Layout user={user} onLogout={logout}>
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={logout}>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-2xs font-black text-brand uppercase tracking-widest">
              Event Verification
            </p>
            <h1 className="text-3xl font-bold text-ink mt-1">Webhook Command Center</h1>
            <p className="text-text-muted mt-1">
              Verified BMONI events with HMAC-SHA256 signatures
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={handleExport}>
              <Icons.download className="mr-2" size={16} />
              Export
            </Button>
            <Button variant="primary" onClick={handleSimulate}>
              <Icons.webhook className="mr-2" size={16} />
              Simulate Webhook
            </Button>
          </div>
        </div>

        <Card>
          <div className="flex gap-3 mb-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent outline-none transition-all"
            >
              <option value="all">All Events</option>
              <option value="processed">Processed</option>
              <option value="pending">Pending</option>
              <option value="valid">Valid Signatures</option>
            </select>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredWebhooks.length === 0 ? (
                <div className="text-center py-12">
                  <Icons.webhook className="mx-auto text-text-muted mb-4" size={48} />
                  <p className="text-text-body">No webhooks found</p>
                  <p className="text-sm text-text-muted">Try adjusting your filters</p>
                </div>
              ) : (
                filteredWebhooks.map((event: any) => (
                  <div
                    key={event.id}
                    className="flex items-center justify-between p-4 bg-canvas-subtle rounded-lg hover:bg-canvas transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {event.signature_valid && (
                        <div className="w-6 h-6 bg-success-bg rounded-full flex items-center justify-center">
                          <Icons.check className="text-success" size={14} />
                        </div>
                      )}
                      {!event.signature_valid && (
                        <div className="w-6 h-6 bg-danger-bg rounded-full flex items-center justify-center">
                          <Icons.x className="text-danger" size={14} />
                        </div>
                      )}
                      <div>
                        <p className="text-sm font-mono font-semibold text-ink">
                          {event.event_type}
                        </p>
                        <p className="text-xs text-text-muted">
                          {formatDateTime(event.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {event.processed && (
                        <span className="text-xs text-success font-bold uppercase tracking-wider">
                          Processed
                        </span>
                      )}
                      {!event.processed && event.state === 'FAILED' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRetry(event.id)}
                          isLoading={retryMutation.isPending}
                        >
                          Retry
                        </Button>
                      )}
                      <Badge variant={getStatusVariant(event.state)} size="sm">
                        {event.state}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewDetails(event)}
                      >
                        View
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </Card>
      </div>

      {/* Webhook Details Modal */}
      <Modal
        isOpen={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        title="Webhook Details"
        subtitle={selectedWebhook?.event_type || ''}
        size="lg"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowDetailsModal(false)}>
              Close
            </Button>
            {!selectedWebhook?.processed && selectedWebhook?.state === 'FAILED' && (
              <Button
                variant="primary"
                onClick={() => handleRetry(selectedWebhook.id)}
                isLoading={retryMutation.isPending}
              >
                Retry Webhook
              </Button>
            )}
          </div>
        }
      >
        {selectedWebhook && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-text-muted">Event Type</p>
                <p className="font-semibold text-ink font-mono">{selectedWebhook.event_type}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted">State</p>
                <Badge variant={getStatusVariant(selectedWebhook.state)} size="sm">
                  {selectedWebhook.state}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-text-muted">Signature Valid</p>
                <Badge variant={selectedWebhook.signature_valid ? 'success' : 'danger'} size="sm">
                  {selectedWebhook.signature_valid ? 'Valid' : 'Invalid'}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-text-muted">Processed</p>
                <Badge variant={selectedWebhook.processed ? 'success' : 'warning'} size="sm">
                  {selectedWebhook.processed ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div className="col-span-2">
                <p className="text-sm text-text-muted">Received At</p>
                <p className="font-semibold text-ink">{formatDateTime(selectedWebhook.created_at)}</p>
              </div>
            </div>
            
            <div>
              <p className="text-sm text-text-muted mb-2">Payload</p>
              <pre className="bg-canvas-subtle p-4 rounded-lg overflow-x-auto text-xs font-mono">
                {JSON.stringify(selectedWebhook.payload, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </Modal>
    </Layout>
  );
}
