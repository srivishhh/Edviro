import React, { createContext, useContext, useState, type ReactNode } from 'react';

export type UserRole = 'technician' | 'admin';

export interface User {
  role: UserRole;
  name: string;
  email: string;
  badge: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (role: UserRole, name?: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const savedRole = localStorage.getItem('gsense-user-role') as UserRole | null;
    const savedName = localStorage.getItem('gsense-user-name');
    if (savedRole) {
      return {
        role: savedRole,
        name: savedName || (savedRole === 'admin' ? 'Operations Admin' : 'Alex Mercer'),
        email: savedRole === 'admin' ? 'admin@gsense.facility' : 'alex.mercer@gsense.facility',
        badge: savedRole === 'admin' ? 'Security Operations Lead' : 'Lead HVAC Specialist',
      };
    }
    return null;
  });

  const login = (role: UserRole, name?: string) => {
    const newUser: User = {
      role,
      name: name || (role === 'admin' ? 'Operations Admin' : 'Alex Mercer'),
      email: role === 'admin' ? 'admin@gsense.facility' : 'alex.mercer@gsense.facility',
      badge: role === 'admin' ? 'Security Operations Lead' : 'Lead HVAC Specialist',
    };
    setUser(newUser);
    localStorage.setItem('gsense-user-role', role);
    localStorage.setItem('gsense-user-name', newUser.name);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('gsense-user-role');
    localStorage.removeItem('gsense-user-name');
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
