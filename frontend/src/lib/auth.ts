import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export function useAuth() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    // Check if we're on the login page - don't redirect if already there
    if (typeof window !== 'undefined' && window.location.pathname === '/login') {
      setIsLoading(false);
      return;
    }
    
    if (!token) {
      router.push('/login');
      setIsLoading(false);
      return;
    }

    try {
      if (userData) {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        setIsAuthenticated(true);
      }
    } catch (e) {
      // Invalid user data, clear everything
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      router.push('/login');
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  const logout = () => {
    // Clear all auth data
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Clear any cached data
    if (typeof window !== 'undefined') {
      window.sessionStorage.clear();
    }
    
    // Force redirect to login
    window.location.href = '/login';
  };

  return { isAuthenticated, isLoading, user, logout };
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
