'use client';

import { useState } from 'react';
import Layout from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Icons } from '@/components/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatCurrency } from '@/lib/utils';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';

interface CardItem {
  id: string;
  card_name: string;
  card_color: string;
  currency: string;
  status: string;
  spending_limit: number;
  spent_amount: number;
  is_frozen: boolean;
  employee_name?: string;
  last_four?: string;
}

export default function CardsPage() {
  const queryClient = useQueryClient();
  const { isLoading: authLoading, user, logout } = useAuth();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showFreezeModal, setShowFreezeModal] = useState(false);
  const [selectedCard, setSelectedCard] = useState<CardItem | null>(null);
  const [formData, setFormData] = useState({
    card_name: '',
    currency: 'USD',
    spending_limit: '',
  });

  const { data, isLoading: dataLoading } = useQuery({
    queryKey: ['cards'],
    queryFn: async () => {
      const { data } = await api.get('/cards');
      return data.items || data; // Handle both paginated and plain array responses
    },
    enabled: !authLoading,
  });

  const freezeMutation = useMutation({
    mutationFn: async ({ cardId, frozen }: { cardId: string; frozen: boolean }) => {
      const { data } = await api.put(`/cards/${cardId}/status`, { is_frozen: frozen });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] });
      setShowFreezeModal(false);
      setSelectedCard(null);
    },
  });

  const updateLimitMutation = useMutation({
    mutationFn: async ({ cardId, limit }: { cardId: string; limit: number }) => {
      const { data } = await api.put(`/cards/${cardId}/limit`, { spending_limit: limit });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] });
      setShowEditModal(false);
      setSelectedCard(null);
    },
  });

  const createMutation = useMutation({
    mutationFn: async (cardData: any) => {
      const { data } = await api.post('/cards', cardData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] });
      setShowCreateModal(false);
      setFormData({ card_name: '', currency: 'USD', spending_limit: '' });
    },
  });

  const isLoading = authLoading || dataLoading;

  const handleFreeze = (card: CardItem) => {
    setSelectedCard(card);
    setShowFreezeModal(true);
  };

  const handleFreezeConfirm = () => {
    if (selectedCard) {
      freezeMutation.mutate({ 
        cardId: selectedCard.id, 
        frozen: !selectedCard.is_frozen 
      });
    }
  };

  const handleEdit = (card: CardItem) => {
    setSelectedCard(card);
    setFormData({
      card_name: card.card_name,
      currency: card.currency,
      spending_limit: card.spending_limit.toString(),
    });
    setShowEditModal(true);
  };

  const handleUpdateLimit = () => {
    if (selectedCard && formData.spending_limit) {
      updateLimitMutation.mutate({
        cardId: selectedCard.id,
        limit: Number(formData.spending_limit),
      });
    }
  };

  const handleCreate = () => {
    createMutation.mutate({
      ...formData,
      spending_limit: Number(formData.spending_limit),
    });
  };

  const handleExport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      cards: data || [],
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cards-${new Date().toISOString().split('T')[0]}.json`;
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

  return (
    <Layout user={user} onLogout={logout}>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-2xs font-black text-brand uppercase tracking-widest">
              Expense Management
            </p>
            <h1 className="text-3xl font-bold text-ink mt-1">Team Cards</h1>
            <p className="text-text-muted mt-1">
              Virtual and physical spend cards for your team
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={handleExport}>
              <Icons.download className="mr-2" size={16} />
              Export
            </Button>
            <Button variant="primary" onClick={() => setShowCreateModal(true)}>
              <Icons.card className="mr-2" size={16} />
              Create Card
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.map((card: CardItem) => {
            const progress = (card.spent_amount / card.spending_limit) * 100;
            return (
              <Card key={card.id} hover>
                <div className="space-y-4">
                  {/* Card Visual */}
                  <div 
                    className="rounded-xl p-6 text-white relative overflow-hidden"
                    style={{ backgroundColor: card.card_color || '#1D4ED8' }}
                  >
                    <div className="flex justify-between items-start mb-8">
                      <div>
                        <p className="text-xs uppercase tracking-wider opacity-80">
                          {card.currency}
                        </p>
                        <p className="text-lg font-bold">{card.card_name}</p>
                      </div>
                      {card.is_frozen && (
                        <Badge variant="danger" size="sm">
                          Frozen
                        </Badge>
                      )}
                    </div>
                    <div className="mt-12">
                      <p className="text-2xs opacity-60 mb-1">Available</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(card.spending_limit - card.spent_amount, card.currency)}
                      </p>
                    </div>
                  </div>

                  {/* Card Details */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-text-muted">Spent</span>
                      <span className="font-semibold text-ink">
                        {formatCurrency(card.spent_amount, card.currency)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-text-muted">Limit</span>
                      <span className="font-semibold text-ink">
                        {formatCurrency(card.spending_limit, card.currency)}
                      </span>
                    </div>
                    <div className="w-full bg-canvas-subtle rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all ${
                          progress > 90 ? 'bg-danger' :
                          progress > 70 ? 'bg-warning' : 'bg-success'
                        }`}
                        style={{ width: `${Math.min(progress, 100)}%` }}
                      />
                    </div>
                    {card.employee_name && (
                      <p className="text-xs text-text-muted pt-2">
                        Assigned to: {card.employee_name}
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-2">
                    <Button 
                      variant="secondary" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => handleEdit(card)}
                    >
                      Edit Limit
                    </Button>
                    <Button 
                      variant={card.is_frozen ? 'primary' : 'secondary'}
                      size="sm"
                      onClick={() => handleFreeze(card)}
                    >
                      {card.is_frozen ? 'Unfreeze' : 'Freeze'}
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        {(!data || data.length === 0) && (
          <Card>
            <div className="text-center py-12">
              <Icons.card className="mx-auto text-text-muted mb-4" size={48} />
              <p className="text-text-body mb-2">No cards yet</p>
              <p className="text-sm text-text-muted mb-4">
                Create your first card to get started
              </p>
              <Button variant="primary" onClick={() => setShowCreateModal(true)}>
                Create Card
              </Button>
            </div>
          </Card>
        )}
      </div>

      {/* Create Card Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Card"
        subtitle="Issue a new spend card"
        size="md"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleCreate}
              isLoading={createMutation.isPending}
            >
              Create Card
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input
            label="Card Name"
            value={formData.card_name}
            onChange={(e) => setFormData({ ...formData, card_name: e.target.value })}
            placeholder="e.g., John's Expense Card"
            required
          />
          <div>
            <label className="block text-sm font-semibold text-ink mb-2">
              Currency
            </label>
            <select
              value={formData.currency}
              onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
              className="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent outline-none transition-all"
            >
              <option value="USD">USD - US Dollar</option>
              <option value="NGN">NGN - Nigerian Naira</option>
              <option value="EUR">EUR - Euro</option>
              <option value="GBP">GBP - British Pound</option>
            </select>
          </div>
          <Input
            label="Spending Limit"
            type="number"
            value={formData.spending_limit}
            onChange={(e) => setFormData({ ...formData, spending_limit: e.target.value })}
            placeholder="1000"
            required
          />
        </div>
      </Modal>

      {/* Edit Card Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Card Limit"
        subtitle={selectedCard?.card_name || ''}
        size="md"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleUpdateLimit}
              isLoading={updateLimitMutation.isPending}
            >
              Update Limit
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="p-4 bg-canvas-subtle rounded-lg">
            <p className="text-sm text-text-muted mb-1">Current Limit</p>
            <p className="text-2xl font-bold text-ink">
              {selectedCard && formatCurrency(selectedCard.spending_limit, selectedCard.currency)}
            </p>
          </div>
          <Input
            label="New Spending Limit"
            type="number"
            value={formData.spending_limit}
            onChange={(e) => setFormData({ ...formData, spending_limit: e.target.value })}
            required
          />
        </div>
      </Modal>

      {/* Freeze Confirmation Modal */}
      <Modal
        isOpen={showFreezeModal}
        onClose={() => setShowFreezeModal(false)}
        title={selectedCard?.is_frozen ? 'Unfreeze Card' : 'Freeze Card'}
        subtitle={selectedCard?.card_name || ''}
        size="sm"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowFreezeModal(false)}>
              Cancel
            </Button>
            <Button 
              variant={selectedCard?.is_frozen ? 'primary' : 'danger'}
              onClick={handleFreezeConfirm}
              isLoading={freezeMutation.isPending}
            >
              {selectedCard?.is_frozen ? 'Unfreeze' : 'Freeze'} Card
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <p className="text-text-body">
            {selectedCard?.is_frozen 
              ? 'Are you sure you want to unfreeze this card? It will be available for use immediately.'
              : 'Are you sure you want to freeze this card? It will be temporarily disabled.'}
          </p>
        </div>
      </Modal>
    </Layout>
  );
}
