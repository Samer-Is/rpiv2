import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { api, Branch } from '../services/api';

// Multiplier settings interface
export interface MultiplierSettings {
  min_multiplier: number;
  max_multiplier: number;
  demand_high: number;
  demand_low: number;
  supply_high: number;
  supply_low: number;
  event_max: number;
}

interface AppContextType {
  // Branch & User
  branches: Branch[];
  selectedBranch: number;
  setSelectedBranch: (id: number) => void;
  userRole: string;
  setUserRole: (role: string) => void;
  
  // Multipliers
  multipliers: MultiplierSettings;
  setMultipliers: (settings: MultiplierSettings) => void;
  
  // Loading
  branchesLoading: boolean;
}

const defaultMultipliers: MultiplierSettings = {
  min_multiplier: 0.80,
  max_multiplier: 2.50,
  demand_high: 1.20,
  demand_low: 0.85,
  supply_high: 1.15,
  supply_low: 0.90,
  event_max: 1.60,
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<number>(122);
  const [userRole, setUserRole] = useState<string>('Branch Manager');
  const [multipliers, setMultipliers] = useState<MultiplierSettings>(defaultMultipliers);
  const [branchesLoading, setBranchesLoading] = useState(true);

  // Load branches on mount
  useEffect(() => {
    const loadBranches = async () => {
      try {
        const data = await api.getBranches();
        setBranches(data);
      } catch (err) {
        console.error('Failed to load branches:', err);
      } finally {
        setBranchesLoading(false);
      }
    };
    loadBranches();
  }, []);

  // Load multipliers from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('multiplierSettings');
    if (saved) {
      try {
        setMultipliers(JSON.parse(saved));
      } catch {
        // Use defaults
      }
    }
  }, []);

  // Save multipliers to localStorage when they change
  const handleSetMultipliers = useCallback((settings: MultiplierSettings) => {
    setMultipliers(settings);
    localStorage.setItem('multiplierSettings', JSON.stringify(settings));
  }, []);

  return (
    <AppContext.Provider value={{
      branches,
      selectedBranch,
      setSelectedBranch,
      userRole,
      setUserRole,
      multipliers,
      setMultipliers: handleSetMultipliers,
      branchesLoading,
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};

export const USER_ROLES = ['Branch Manager', 'Regional Manager', 'Pricing Manager', 'Executive'];

