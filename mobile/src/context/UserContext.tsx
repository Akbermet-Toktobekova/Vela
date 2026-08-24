import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface UserProfile {
  name: string;
  initials: string;
  currency: string;
  monthlyLimit: number;
  isFirstLaunch: boolean;
}

export interface TransactionItem {
  id: string;
  merchant: string;
  amount: number;
  category: 'needs' | 'wants' | 'savings';
  source: 'apple_pay' | 'google_pay' | 'nfc' | 'manual' | 'open_banking';
  timestamp: string;
  timeFormatted: string;
  iconName: string;
  iconBg: string;
}

export interface VaultGoal {
  id: string;
  title: string;
  targetAmount: number;
  currentAmount: number;
  targetDate: string;
  iconName: string;
  iconColor: string;
  iconBg: string;
}

interface UserContextType {
  profile: UserProfile;
  transactions: TransactionItem[];
  vaults: VaultGoal[];
  totalSpent: number;
  needsSpent: number;
  wantsSpent: number;
  savingsSpent: number;
  isLoading: boolean;
  updateProfile: (profile: Partial<UserProfile>) => Promise<void>;
  addTransaction: (tx: Omit<TransactionItem, 'id' | 'timestamp' | 'timeFormatted'>) => Promise<void>;
  deleteTransaction: (id: string) => Promise<void>;
  addVault: (vault: Omit<VaultGoal, 'id' | 'currentAmount'>) => Promise<void>;
  resetAccount: () => Promise<void>;
}

const DEFAULT_PROFILE: UserProfile = {
  name: 'Sanatbek',
  initials: 'SZ',
  currency: 'EUR',
  monthlyLimit: 2000,
  isFirstLaunch: false,
};

const DEFAULT_VAULTS: VaultGoal[] = [
  {
    id: '1',
    title: 'Emergency Fund',
    targetAmount: 6000,
    currentAmount: 0,
    targetDate: 'Dec 2026',
    iconName: 'shield-checkmark',
    iconColor: '#00C853',
    iconBg: '#E8F8EE',
  },
  {
    id: '2',
    title: 'Trip to Japan',
    targetAmount: 3000,
    currentAmount: 0,
    targetDate: 'Oct 2026',
    iconName: 'airplane',
    iconColor: '#0075EB',
    iconBg: '#E5F2FF',
  },
];

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [vaults, setVaults] = useState<VaultGoal[]>(DEFAULT_VAULTS);
  const [isLoading, setIsLoading] = useState(true);

  // Load from AsyncStorage on mount
  useEffect(() => {
    loadPersistedData();
  }, []);

  const loadPersistedData = async () => {
    try {
      const storedProfile = await AsyncStorage.getItem('@vela_user_profile');
      const storedTx = await AsyncStorage.getItem('@vela_transactions');
      const storedVaults = await AsyncStorage.getItem('@vela_vaults');

      if (storedProfile) {
        setProfile(JSON.parse(storedProfile));
      } else {
        setProfile({ ...DEFAULT_PROFILE, isFirstLaunch: true });
      }

      if (storedTx) {
        setTransactions(JSON.parse(storedTx));
      } else {
        setTransactions([]);
      }

      if (storedVaults) {
        setVaults(JSON.parse(storedVaults));
      }
    } catch (e) {
      console.error('Error loading persisted user data', e);
    } finally {
      setIsLoading(false);
    }
  };

  const updateProfile = async (newProfile: Partial<UserProfile>) => {
    const updated = { ...profile, ...newProfile };
    setProfile(updated);
    await AsyncStorage.setItem('@vela_user_profile', JSON.stringify(updated));
  };

  const addTransaction = async (tx: Omit<TransactionItem, 'id' | 'timestamp' | 'timeFormatted'>) => {
    const now = new Date();
    const timeFormatted = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const newTx: TransactionItem = {
      ...tx,
      id: Date.now().toString(),
      timestamp: now.toISOString(),
      timeFormatted: timeFormatted,
    };

    const updated = [newTx, ...transactions];
    setTransactions(updated);
    await AsyncStorage.setItem('@vela_transactions', JSON.stringify(updated));
  };

  const deleteTransaction = async (id: string) => {
    const updated = transactions.filter((t) => t.id !== id);
    setTransactions(updated);
    await AsyncStorage.setItem('@vela_transactions', JSON.stringify(updated));
  };

  const addVault = async (vault: Omit<VaultGoal, 'id' | 'currentAmount'>) => {
    const newVault: VaultGoal = {
      ...vault,
      id: Date.now().toString(),
      currentAmount: 0,
    };
    const updated = [...vaults, newVault];
    setVaults(updated);
    await AsyncStorage.setItem('@vela_vaults', JSON.stringify(updated));
  };

  const resetAccount = async () => {
    setTransactions([]);
    setProfile({ ...DEFAULT_PROFILE, isFirstLaunch: true });
    await AsyncStorage.removeItem('@vela_transactions');
    await AsyncStorage.removeItem('@vela_user_profile');
    await AsyncStorage.removeItem('@vela_vaults');
  };

  // Calculations
  const totalSpent = transactions.reduce((sum, t) => sum + t.amount, 0);
  const needsSpent = transactions.filter((t) => t.category === 'needs').reduce((sum, t) => sum + t.amount, 0);
  const wantsSpent = transactions.filter((t) => t.category === 'wants').reduce((sum, t) => sum + t.amount, 0);
  const savingsSpent = transactions.filter((t) => t.category === 'savings').reduce((sum, t) => sum + t.amount, 0);

  return (
    <UserContext.Provider
      value={{
        profile,
        transactions,
        vaults,
        totalSpent,
        needsSpent,
        wantsSpent,
        savingsSpent,
        isLoading,
        updateProfile,
        addTransaction,
        deleteTransaction,
        addVault,
        resetAccount,
      }}
    >
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
