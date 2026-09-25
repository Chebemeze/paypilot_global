'use client';

import { useState, useRef } from 'react';
import Layout from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Table } from '@/components/ui/Table';
import { Modal } from '@/components/ui/Modal';
import { Icons } from '@/components/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatCurrency, getStatusVariant } from '@/lib/utils';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';

interface PayrollBatch {
  id: string;
  batch_name: string;
  status: string;
  total_items: number;
  total_amount_usd: number;
  safety_score?: number;
  safety_label?: string;
  created_at: string;
}

export default function PayrollPage() {
  const queryClient = useQueryClient();
  const { isLoading: authLoading, user, logout } = useAuth();
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState<PayrollBatch | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading: dataLoading } = useQuery({
    queryKey: ['batches'],
    queryFn: async () => {
      const { data } = await api.get('/payroll/batches');
      return data;
    },
    enabled: !authLoading,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/payroll/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['batches'] });
      setUploadStatus('success');
      setUploadMessage(`Successfully uploaded ${data.items_count || 0} payroll items`);
      setTimeout(() => {
        setShowUploadModal(false);
        setUploadStatus('idle');
        setUploadMessage('');
        setUploadFile(null);
      }, 2000);
    },
    onError: (error: any) => {
      setUploadStatus('error');
      setUploadMessage(error.response?.data?.detail || 'Upload failed');
    },
  });

  const approveMutation = useMutation({
    mutationFn: async (batchId: string) => {
      const { data } = await api.post(`/payroll/batches/${batchId}/approve`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] });
      setShowDetailsModal(false);
    },
  });

  const simulateMutation = useMutation({
    mutationFn: async (batchId: string) => {
      const { data } = await api.post(`/payroll/batches/${batchId}/simulate-disbursement`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] });
    },
  });

  const scoreRiskMutation = useMutation({
    mutationFn: async (batchId: string) => {
      const { data } = await api.post(`/payroll/batches/${batchId}/score-risk`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] });
      setShowDetailsModal(false);
    },
  });

  const isLoading = authLoading || dataLoading;

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setUploadFile(file);
        setUploadStatus('idle');
        setUploadMessage('');
      } else {
        setUploadStatus('error');
        setUploadMessage('Please select a CSV file');
      }
    }
  };

  const handleUpload = () => {
    if (uploadFile) {
      setUploadStatus('uploading');
      uploadMutation.mutate(uploadFile);
    }
  };

  const handleViewDetails = (batch: PayrollBatch) => {
    setSelectedBatch(batch);
    setShowDetailsModal(true);
  };

  const handleApprove = () => {
    if (selectedBatch) {
      approveMutation.mutate(selectedBatch.id);
    }
  };

  const handleSimulate = () => {
    if (selectedBatch) {
      simulateMutation.mutate(selectedBatch.id);
    }
  };

  const handleScoreRisk = () => {
    if (selectedBatch) {
      scoreRiskMutation.mutate(selectedBatch.id);
    }
  };

  const handleExport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      batches: data?.items || [],
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `payroll-batches-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const columns = [
    {
      key: 'batch_name',
      label: 'Batch',
      render: (item: PayrollBatch) => (
        <div>
          <p className="font-semibold text-ink">{item.batch_name}</p>
          <p className="text-xs text-text-muted">
            {new Date(item.created_at).toLocaleDateString()}
          </p>
        </div>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (item: PayrollBatch) => (
        <Badge variant={getStatusVariant(item.status)} size="sm">
          {item.status.replace(/_/g, ' ')}
        </Badge>
      ),
    },
    { key: 'total_items', label: 'Items' },
    {
      key: 'safety_score',
      label: 'Safety Score',
      render: (item: PayrollBatch) => (
        item.safety_score ? (
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-ink">{item.safety_score}</span>
            <Badge variant={getStatusVariant(item.safety_label || 'unknown')} size="sm">
              {item.safety_label?.replace(/_/g, ' ')}
            </Badge>
          </div>
        ) : '—'
      ),
    },
    {
      key: 'total_amount_usd',
      label: 'Total (USD)',
      render: (item: PayrollBatch) => (
        <span className="font-mono font-bold">
          {formatCurrency(item.total_amount_usd, 'USD')}
        </span>
      ),
    },
    {
      key: 'actions',
      label: '',
      render: (item: PayrollBatch) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => handleViewDetails(item)}>
            Review
          </Button>
          {item.status === 'RISK_SCORING' && (
            <Button 
              variant="primary" 
              size="sm" 
              onClick={() => {
                setSelectedBatch(item);
                handleScoreRisk();
              }}
            >
              Score Risk
            </Button>
          )}
          {item.status === 'APPROVED' && (
            <Button 
              variant="secondary" 
              size="sm" 
              onClick={() => {
                setSelectedBatch(item);
                handleSimulate();
              }}
            >
              Simulate
            </Button>
          )}
        </div>
      ),
    },
  ];

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
              Payroll Operations
            </p>
            <h1 className="text-3xl font-bold text-ink mt-1">Payroll Batches</h1>
            <p className="text-text-muted mt-1">
              Upload CSVs, score risk, and approve payments
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={handleExport}>
              <Icons.download className="mr-2" size={16} />
              Export
            </Button>
            <Button variant="primary" onClick={() => setShowUploadModal(true)}>
              <Icons.upload className="mr-2" size={16} />
              Upload CSV
            </Button>
          </div>
        </div>

        <Card>
          <Table data={data?.items || []} columns={columns} />
        </Card>
      </div>

      {/* Upload CSV Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        title="Upload Payroll CSV"
        subtitle="Upload a CSV file with payroll data"
        size="md"
        footer={
          <div className="flex justify-end gap-3">
            <Button 
              variant="secondary" 
              onClick={() => setShowUploadModal(false)}
              disabled={uploadStatus === 'uploading'}
            >
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleUpload}
              isLoading={uploadStatus === 'uploading'}
              disabled={!uploadFile}
            >
              Upload File
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Icons.upload className="mx-auto text-text-muted mb-4" size={48} />
            <p className="text-sm text-text-body mb-2">
              {uploadFile ? uploadFile.name : 'Click to select a CSV file'}
            </p>
            <Button 
              variant="secondary" 
              size="sm" 
              onClick={() => fileInputRef.current?.click()}
            >
              Choose File
            </Button>
          </div>
          
          {uploadMessage && (
            <div className={`p-4 rounded-lg ${
              uploadStatus === 'success' ? 'bg-success-bg border border-success/20' :
              uploadStatus === 'error' ? 'bg-danger-bg border border-danger/20' :
              'bg-info-bg border border-info/20'
            }`}>
              <p className={`text-sm ${
                uploadStatus === 'success' ? 'text-success-text' :
                uploadStatus === 'error' ? 'text-danger-text' :
                'text-info-text'
              }`}>
                {uploadMessage}
              </p>
            </div>
          )}
        </div>
      </Modal>

      {/* Batch Details Modal */}
      <Modal
        isOpen={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        title="Batch Details"
        subtitle={selectedBatch?.batch_name || ''}
        size="lg"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowDetailsModal(false)}>
              Close
            </Button>
            {selectedBatch?.status === 'RISK_SCORING' && (
              <Button 
                variant="primary" 
                onClick={handleScoreRisk}
                isLoading={scoreRiskMutation.isPending}
              >
                Score Risk
              </Button>
            )}
            {selectedBatch?.status === 'READY_FOR_APPROVAL' && (
              <Button 
                variant="primary" 
                onClick={handleApprove}
                isLoading={approveMutation.isPending}
              >
                Approve Batch
              </Button>
            )}
            {selectedBatch?.status === 'APPROVED' && (
              <Button 
                variant="secondary" 
                onClick={handleSimulate}
                isLoading={simulateMutation.isPending}
              >
                Simulate Disbursement
              </Button>
            )}
          </div>
        }
      >
        {selectedBatch && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-text-muted">Batch Name</p>
                <p className="font-semibold text-ink">{selectedBatch.batch_name}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted">Status</p>
                <Badge variant={getStatusVariant(selectedBatch.status)} size="sm">
                  {selectedBatch.status.replace(/_/g, ' ')}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-text-muted">Total Items</p>
                <p className="font-semibold text-ink">{selectedBatch.total_items}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted">Total Amount (USD)</p>
                <p className="font-semibold text-ink font-mono">
                  {formatCurrency(selectedBatch.total_amount_usd, 'USD')}
                </p>
              </div>
              <div>
                <p className="text-sm text-text-muted">Created</p>
                <p className="font-semibold text-ink">
                  {new Date(selectedBatch.created_at).toLocaleString()}
                </p>
              </div>
              {selectedBatch.safety_score && (
                <>
                  <div>
                    <p className="text-sm text-text-muted">Safety Score</p>
                    <p className="font-semibold text-ink">{selectedBatch.safety_score}</p>
                  </div>
                  <div>
                    <p className="text-sm text-text-muted">Safety Label</p>
                    <Badge variant={getStatusVariant(selectedBatch.safety_label || 'unknown')} size="sm">
                      {selectedBatch.safety_label?.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </Modal>
    </Layout>
  );
}
