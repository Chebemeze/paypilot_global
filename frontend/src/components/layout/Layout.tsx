'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Icons } from '@/components/icons';

interface LayoutProps {
  children: React.ReactNode;
  user?: any;
  onLogout?: () => void;
}

export default function Layout({ children, user, onLogout }: LayoutProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Icons.dashboard },
    { href: '/employees', label: 'Employees', icon: Icons.users },
    { href: '/payroll', label: 'Payroll', icon: Icons.wallet },
    { href: '/forecast', label: 'Forecast', icon: Icons.chart },
    { href: '/webhooks', label: 'Webhooks', icon: Icons.webhook },
    { href: '/copilot', label: 'Copilot', icon: Icons.sparkles },
    { href: '/cards', label: 'Cards', icon: Icons.card },
  ];

  const displayName = user?.full_name || 'Sarah Johnson';
  const displayRole = user?.role || 'Admin';

  return (
    <div className="min-h-screen bg-canvas-subtle flex">
      {/* Sidebar */}
      <aside
        className={cn(
          'bg-white border-r border-border flex flex-col transition-all duration-300',
          collapsed ? 'w-20' : 'w-64'
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 gradient-navy-subtle rounded-lg flex items-center justify-center text-white font-bold text-xl">
              P
            </div>
            {!collapsed && (
              <div>
                <h1 className="text-sm font-bold text-ink">PayPilot</h1>
                <p className="text-2xs text-gold-text font-semibold uppercase tracking-wider">Global</p>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 hover:bg-canvas-subtle rounded-lg transition-colors"
          >
            <Icons.chevronRight
              className={cn(
                'text-text-muted transition-transform',
                collapsed && 'rotate-180'
              )}
              size={16}
            />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                  isActive
                    ? 'bg-brand-soft text-brand font-semibold'
                    : 'text-text-body hover:bg-canvas-subtle hover:text-ink'
                )}
              >
                <Icon size={20} />
                {!collapsed && <span className="text-sm">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-border">
          {!collapsed && (
            <div className="px-3 py-2 mb-2">
              <p className="text-xs text-text-muted font-medium">{displayName}</p>
              <p className="text-2xs text-text-muted">{displayRole}</p>
            </div>
          )}
          <button
            onClick={onLogout}
            className="flex items-center gap-3 w-full px-3 py-2 text-text-body hover:bg-danger-bg hover:text-danger rounded-lg transition-colors"
          >
            <Icons.logout size={20} />
            {!collapsed && <span className="text-sm">Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
