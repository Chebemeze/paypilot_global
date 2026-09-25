'use client';

import { useState } from 'react';
import Layout from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Table } from '@/components/ui/Table';
import { Modal } from '@/components/ui/Modal';
import { Icons } from '@/components/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getStatusVariant } from '@/lib/utils';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';

interface Employee {
  id: string;
  full_name: string;
  email: string;
  country: string;
  preferred_currency: string;
  onboarding_status: string;
  department?: string;
  role?: string;
  expected_salary?: number;
}

export default function EmployeesPage() {
  const queryClient = useQueryClient();
  const { isLoading: authLoading, user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    country: '',
    department: '',
    role: '',
    expected_salary: '',
    preferred_currency: 'USD',
  });

  const { data, isLoading: dataLoading } = useQuery({
    queryKey: ['employees'],
    queryFn: async () => {
      const { data } = await api.get('/employees');
      return data;
    },
    enabled: !authLoading,
  });

  const createMutation = useMutation({
    mutationFn: async (employeeData: any) => {
      const { data } = await api.post('/employees', employeeData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      setShowCreateModal(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, ...employeeData }: any) => {
      const { data } = await api.put(`/employees/${id}`, employeeData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      setShowEditModal(false);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/employees/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      setShowDeleteModal(false);
      setSelectedEmployee(null);
    },
  });

  const inviteMutation = useMutation({
    mutationFn: async (employeeId: string) => {
      const { data } = await api.post(`/employees/${employeeId}/invite`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
  });

  const reminderMutation = useMutation({
    mutationFn: async (employeeId: string) => {
      const { data } = await api.post(`/employees/${employeeId}/reminder`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
  });

  const isLoading = authLoading || dataLoading;

  const resetForm = () => {
    setFormData({
      full_name: '',
      email: '',
      country: '',
      department: '',
      role: '',
      expected_salary: '',
      preferred_currency: 'USD',
    });
  };

  const handleCreate = () => {
    createMutation.mutate({
      ...formData,
      expected_salary: Number(formData.expected_salary),
    });
  };

  const handleUpdate = () => {
    if (!selectedEmployee) return;
    updateMutation.mutate({
      id: selectedEmployee.id,
      ...formData,
      expected_salary: Number(formData.expected_salary),
    });
  };

  const handleDelete = () => {
    if (!selectedEmployee) return;
    deleteMutation.mutate(selectedEmployee.id);
  };

  const handleInvite = (employee: Employee) => {
    inviteMutation.mutate(employee.id);
  };

  const handleReminder = (employee: Employee) => {
    reminderMutation.mutate(employee.id);
  };

  const handleView = (employee: Employee) => {
    setSelectedEmployee(employee);
    setShowViewModal(true);
  };

  const handleEdit = (employee: Employee) => {
    setSelectedEmployee(employee);
    setFormData({
      full_name: employee.full_name,
      email: employee.email,
      country: employee.country,
      department: employee.department || '',
      role: employee.role || '',
      expected_salary: employee.expected_salary?.toString() || '',
      preferred_currency: employee.preferred_currency,
    });
    setShowEditModal(true);
  };

  const handleDeleteConfirm = (employee: Employee) => {
    setSelectedEmployee(employee);
    setShowDeleteModal(true);
  };

  const filteredEmployees = data?.items?.filter((employee: Employee) =>
    employee.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    employee.email.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const columns = [
    {
      key: 'name',
      label: 'Employee',
      render: (item: Employee) => (
        <div>
          <p className="font-semibold text-ink">{item.full_name}</p>
          <p className="text-xs text-text-muted">{item.email}</p>
        </div>
      ),
    },
    { key: 'country', label: 'Country' },
    { key: 'preferred_currency', label: 'Currency' },
    {
      key: 'onboarding_status',
      label: 'Status',
      render: (item: Employee) => (
        <Badge variant={getStatusVariant(item.onboarding_status)} size="sm">
          {item.onboarding_status.replace(/_/g, ' ')}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: '',
      render: (item: Employee) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => handleView(item)}>
            View
          </Button>
          <Button variant="ghost" size="sm" onClick={() => handleEdit(item)}>
            Edit
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => handleDeleteConfirm(item)}
            className="text-danger hover:text-danger"
          >
            Delete
          </Button>
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
              Team Management
            </p>
            <h1 className="text-3xl font-bold text-ink mt-1">Employees</h1>
            <p className="text-text-muted mt-1">
              Manage your remote team's onboarding and payroll readiness
            </p>
          </div>
          <Button variant="primary" onClick={() => setShowCreateModal(true)}>
            <Icons.users className="mr-2" size={16} />
            Add Employee
          </Button>
        </div>

        <Card>
          <div className="flex gap-3 mb-4">
            <Input
              placeholder="Search by name or email..."
              icon={<Icons.search size={16} />}
              className="flex-1"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <Table data={filteredEmployees} columns={columns} />
        </Card>
      </div>

      {/* Create Employee Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Add New Employee"
        subtitle="Add a new team member to your payroll"
        size="lg"
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
              Create Employee
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input
            label="Full Name"
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            required
          />
          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Country"
              value={formData.country}
              onChange={(e) => setFormData({ ...formData, country: e.target.value })}
              required
            />
            <Input
              label="Department"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Role"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            />
            <Input
              label="Expected Salary"
              type="number"
              value={formData.expected_salary}
              onChange={(e) => setFormData({ ...formData, expected_salary: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-ink mb-2">
              Preferred Currency
            </label>
            <select
              value={formData.preferred_currency}
              onChange={(e) => setFormData({ ...formData, preferred_currency: e.target.value })}
              className="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent outline-none transition-all"
            >
              <option value="USD">USD - US Dollar</option>
              <option value="NGN">NGN - Nigerian Naira</option>
              <option value="EUR">EUR - Euro</option>
              <option value="GBP">GBP - British Pound</option>
              <option value="MXN">MXN - Mexican Peso</option>
              <option value="CAD">CAD - Canadian Dollar</option>
            </select>
          </div>
        </div>
      </Modal>

      {/* Edit Employee Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Employee"
        subtitle="Update employee information"
        size="lg"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleUpdate}
              isLoading={updateMutation.isPending}
            >
              Save Changes
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input
            label="Full Name"
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            required
          />
          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Country"
              value={formData.country}
              onChange={(e) => setFormData({ ...formData, country: e.target.value })}
              required
            />
            <Input
              label="Department"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Role"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            />
            <Input
              label="Expected Salary"
              type="number"
              value={formData.expected_salary}
              onChange={(e) => setFormData({ ...formData, expected_salary: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-ink mb-2">
              Preferred Currency
            </label>
            <select
              value={formData.preferred_currency}
              onChange={(e) => setFormData({ ...formData, preferred_currency: e.target.value })}
              className="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent outline-none transition-all"
            >
              <option value="USD">USD - US Dollar</option>
              <option value="NGN">NGN - Nigerian Naira</option>
              <option value="EUR">EUR - Euro</option>
              <option value="GBP">GBP - British Pound</option>
              <option value="MXN">MXN - Mexican Peso</option>
              <option value="CAD">CAD - Canadian Dollar</option>
            </select>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Employee"
        subtitle="This action cannot be undone"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="danger" 
              onClick={handleDelete}
              isLoading={deleteMutation.isPending}
            >
              Delete Employee
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <p className="text-text-body">
            Are you sure you want to delete <strong>{selectedEmployee?.full_name}</strong>?
          </p>
          <p className="text-sm text-text-muted">
            This will permanently remove the employee from your payroll system.
          </p>
        </div>
      </Modal>

      {/* View Employee Modal */}
      <Modal
        isOpen={showViewModal}
        onClose={() => setShowViewModal(false)}
        title="Employee Details"
        subtitle={selectedEmployee?.full_name || ''}
        size="lg"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowViewModal(false)}>
              Close
            </Button>
            <Button 
              variant="primary" 
              onClick={() => {
                setShowViewModal(false);
                if (selectedEmployee) handleEdit(selectedEmployee);
              }}
            >
              Edit Employee
            </Button>
          </div>
        }
      >
        {selectedEmployee && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-text-muted">Email</p>
                <p className="font-semibold text-ink">{selectedEmployee.email}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted">Country</p>
                <p className="font-semibold text-ink">{selectedEmployee.country}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted">Department</p>
                <p className="font-semibold text-ink">{selectedEmployee.department || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted">Role</p>
                <p className="font-semibold text-ink">{selectedEmployee.role || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted">Expected Salary</p>
                <p className="font-semibold text-ink">
                  {selectedEmployee.preferred_currency} {selectedEmployee.expected_salary?.toLocaleString() || '0'}
                </p>
              </div>
              <div>
                <p className="text-sm text-text-muted">Status</p>
                <Badge variant={getStatusVariant(selectedEmployee.onboarding_status)} size="sm">
                  {selectedEmployee.onboarding_status.replace(/_/g, ' ')}
                </Badge>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </Layout>
  );
}
