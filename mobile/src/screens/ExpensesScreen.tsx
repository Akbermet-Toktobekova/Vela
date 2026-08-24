import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  ScrollView, 
  Platform 
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { useUser, TransactionItem } from '../context/UserContext';
import { AddExpenseModal } from '../components/AddExpenseModal';
import { ApplePayGuideModal } from '../components/ApplePayGuideModal';
import { OnboardingModal } from '../components/OnboardingModal';

export const ExpensesScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const { 
    profile, 
    transactions, 
    totalSpent, 
    needsSpent, 
    wantsSpent, 
    savingsSpent, 
    addTransaction, 
    deleteTransaction,
    updateProfile 
  } = useUser();

  const [addModalVisible, setAddModalVisible] = useState(false);
  const [guideModalVisible, setGuideModalVisible] = useState(false);

  const handleAddExpense = (merchant: string, amount: number, category: 'needs' | 'wants' | 'savings') => {
    let iconName = 'cart';
    let iconBg = '#E8F8EE';

    if (category === 'wants') {
      iconName = 'cafe';
      iconBg = '#F5EDFC';
    } else if (category === 'savings') {
      iconName = 'wallet';
      iconBg = '#E5F2FF';
    }

    addTransaction({
      merchant,
      amount,
      category,
      source: 'manual',
      iconName,
      iconBg,
    });
  };

  // Calculations for budget pockets
  const limit = profile.monthlyLimit || 2000;
  const needsLimit = limit * 0.5;
  const wantsLimit = limit * 0.3;
  const savingsLimit = limit * 0.2;

  const needsPercent = Math.min(100, Math.round((needsSpent / needsLimit) * 100)) || 0;
  const wantsPercent = Math.min(100, Math.round((wantsSpent / wantsLimit) * 100)) || 0;
  const savingsPercent = Math.min(100, Math.round((savingsSpent / savingsLimit) * 100)) || 0;

  return (
    <View style={[styles.mainWrapper, { paddingTop: Math.max(insets.top, 20) }]}>
      <ScrollView 
        style={styles.container} 
        contentContainerStyle={styles.contentContainer} 
        showsVerticalScrollIndicator={false}
      >
        {/* 1. Top Header (Safe from Dynamic Island) */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{profile.initials || 'SZ'}</Text>
              <View style={styles.activeDot} />
            </View>
          </View>
          <View style={styles.headerMiddle}>
            <Text style={styles.logoText}>Vela</Text>
            <MaterialCommunityIcons name="check-decagram" size={16} color="#0075EB" style={{ marginLeft: 4 }} />
          </View>
          <View style={styles.headerRight}>
            <TouchableOpacity style={styles.iconButton} onPress={() => setGuideModalVisible(true)}>
              <Ionicons name="hardware-chip-outline" size={20} color="#191C1F" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.iconButton} onPress={() => setAddModalVisible(true)}>
              <Ionicons name="add" size={22} color="#191C1F" />
            </TouchableOpacity>
          </View>
        </View>

        {/* 2. VIP Love Banner (Revolut Ultra Style) */}
        <TouchableOpacity style={styles.vipBanner} activeOpacity={0.8}>
          <View style={styles.vipBannerLeft}>
            <View style={styles.pinkCircle}>
              <Ionicons name="heart" size={12} color="#FF2D55" />
            </View>
            <Text style={styles.vipBannerText}>VIP Member · Солнышко, я люблю тебя ❤️</Text>
          </View>
          <Ionicons name="chevron-forward" size={16} color="#8E8E93" />
        </TouchableOpacity>

        {/* 3. Big Currency Balance Hero */}
        <View style={styles.balanceContainer}>
          <Text style={styles.balanceSubtitle}>Spent this month</Text>
          <Text style={styles.balanceAmount}>
            {profile.currency === 'USD' ? '$' : profile.currency === 'HUF' ? 'Ft ' : '€'}
            {totalSpent.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Text>
          <TouchableOpacity style={styles.currencyPill} activeOpacity={0.7}>
            <Text style={styles.currencyPillText}>{profile.currency} · European Union</Text>
            <Ionicons name="chevron-down" size={13} color="#72777A" style={{ marginLeft: 4 }} />
          </TouchableOpacity>
        </View>

        {/* 4. Revolut 10 Circular Action Buttons */}
        <View style={styles.actionButtonsRow}>
          <View style={styles.actionItem}>
            <TouchableOpacity 
              style={styles.actionCircleDark} 
              onPress={() => setAddModalVisible(true)} 
              activeOpacity={0.8}
            >
              <Ionicons name="add" size={24} color="#FFFFFF" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>Add money</Text>
          </View>

          <View style={styles.actionItem}>
            <TouchableOpacity 
              style={styles.actionCircleGray} 
              onPress={() => setGuideModalVisible(true)} 
              activeOpacity={0.8}
            >
              <Ionicons name="radio-outline" size={22} color="#191C1F" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>NFC Setup</Text>
          </View>

          <View style={styles.actionItem}>
            <TouchableOpacity 
              style={styles.actionCircleGray} 
              onPress={() => setAddModalVisible(true)} 
              activeOpacity={0.8}
            >
              <Ionicons name="pie-chart-outline" size={22} color="#191C1F" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>Analytics</Text>
          </View>

          <View style={styles.actionItem}>
            <TouchableOpacity 
              style={styles.actionCircleGray} 
              onPress={() => setGuideModalVisible(true)} 
              activeOpacity={0.8}
            >
              <Ionicons name="ellipsis-horizontal" size={22} color="#191C1F" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>More</Text>
          </View>
        </View>

        {/* 5. Apple Pay NFC Live Ingestion Shortcut Card */}
        <TouchableOpacity 
          style={styles.nfcPromoCard} 
          onPress={() => setGuideModalVisible(true)}
          activeOpacity={0.85}
        >
          <View style={styles.nfcPromoLeft}>
            <View style={styles.nfcBadgeIcon}>
              <Ionicons name="phone-portrait-outline" size={20} color="#0075EB" />
            </View>
            <View style={styles.nfcPromoTextContainer}>
              <Text style={styles.nfcPromoTitle}>Automate Apple Pay NFC</Text>
              <Text style={styles.nfcPromoSubtitle}>Tap to connect iPhone Shortcuts in 3 steps</Text>
            </View>
          </View>
          <Ionicons name="chevron-forward" size={18} color="#0075EB" />
        </TouchableOpacity>

        {/* 6. Revolut Pockets: 50/30/20 Budget Widget */}
        <View style={styles.cardContainer}>
          <View style={styles.cardHeader}>
            <View style={styles.cardHeaderLeft}>
              <Text style={styles.cardTitle}>Budget Pockets</Text>
              <Text style={styles.cardSubtitle}>50/30/20 Strategy</Text>
            </View>
            <Text style={styles.cardLimitText}>€{limit.toLocaleString()} limit</Text>
          </View>

          {/* Needs Pocket (50%) */}
          <View style={styles.pocketRow}>
            <View style={styles.pocketInfo}>
              <View style={[styles.pocketDot, { backgroundColor: '#00C853' }]} />
              <Text style={styles.pocketName}>Needs (50%)</Text>
            </View>
            <Text style={styles.pocketAmount}>
              €{needsSpent.toFixed(2)} <Text style={styles.pocketMax}>/ €{needsLimit.toFixed(0)}</Text>
            </Text>
          </View>
          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, { width: `${needsPercent}%`, backgroundColor: '#00C853' }]} />
          </View>

          {/* Wants Pocket (30%) */}
          <View style={[styles.pocketRow, { marginTop: 14 }]}>
            <View style={styles.pocketInfo}>
              <View style={[styles.pocketDot, { backgroundColor: '#7B61FF' }]} />
              <Text style={styles.pocketName}>Wants (30%)</Text>
            </View>
            <Text style={styles.pocketAmount}>
              €{wantsSpent.toFixed(2)} <Text style={styles.pocketMax}>/ €{wantsLimit.toFixed(0)}</Text>
            </Text>
          </View>
          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, { width: `${wantsPercent}%`, backgroundColor: '#7B61FF' }]} />
          </View>

          {/* Savings Pocket (20%) */}
          <View style={[styles.pocketRow, { marginTop: 14 }]}>
            <View style={styles.pocketInfo}>
              <View style={[styles.pocketDot, { backgroundColor: '#0075EB' }]} />
              <Text style={styles.pocketName}>Savings (20%)</Text>
            </View>
            <Text style={styles.pocketAmount}>
              €{savingsSpent.toFixed(2)} <Text style={styles.pocketMax}>/ €{savingsLimit.toFixed(0)}</Text>
            </Text>
          </View>
          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, { width: `${savingsPercent}%`, backgroundColor: '#0075EB' }]} />
          </View>
        </View>

        {/* 7. Recent Transactions Feed */}
        <View style={styles.transactionsHeader}>
          <Text style={styles.sectionTitle}>Transactions</Text>
          <TouchableOpacity onPress={() => setAddModalVisible(true)}>
            <Text style={styles.seeAllText}>+ Add</Text>
          </TouchableOpacity>
        </View>

        {transactions.length === 0 ? (
          <View style={styles.zeroStateCard}>
            <View style={styles.zeroStateIconCircle}>
              <Ionicons name="receipt-outline" size={32} color="#72777A" />
            </View>
            <Text style={styles.zeroStateTitle}>No expenses yet</Text>
            <Text style={styles.zeroStateDesc}>
              Tap «Add money» to record your first expense or pay with Apple Pay to track automatically.
            </Text>
          </View>
        ) : (
          <View style={styles.transactionsList}>
            {transactions.map((tx) => (
              <View key={tx.id} style={styles.transactionItem}>
                <View style={styles.txLeft}>
                  <View style={[styles.txIconCircle, { backgroundColor: tx.iconBg || '#F4F5F7' }]}>
                    <Ionicons 
                      name={tx.category === 'needs' ? 'cart-outline' : tx.category === 'wants' ? 'cafe-outline' : 'wallet-outline'} 
                      size={20} 
                      color="#191C1F" 
                    />
                  </View>
                  <View style={styles.txMeta}>
                    <Text style={styles.txMerchant}>{tx.merchant}</Text>
                    <Text style={styles.txSubtitle}>
                      {tx.timeFormatted} · {tx.category.toUpperCase()} · {tx.source === 'apple_pay' ? 'Apple Pay' : 'Manual'}
                    </Text>
                  </View>
                </View>
                <View style={styles.txRight}>
                  <Text style={styles.txAmount}>-€{tx.amount.toFixed(2)}</Text>
                  <TouchableOpacity onPress={() => deleteTransaction(tx.id)} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                    <Ionicons name="trash-outline" size={14} color="#C6C6CD" />
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>

      {/* Modals */}
      <AddExpenseModal
        visible={addModalVisible}
        onClose={() => setAddModalVisible(false)}
        onAdd={handleAddExpense}
      />

      <ApplePayGuideModal
        visible={guideModalVisible}
        onClose={() => setGuideModalVisible(false)}
      />

      <OnboardingModal
        visible={profile.isFirstLaunch}
        onComplete={(name, monthlyLimit, currency) => {
          const initials = name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2) || 'SZ';
          updateProfile({ name, initials, monthlyLimit, currency, isFirstLaunch: false });
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  mainWrapper: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
    paddingTop: 4,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#F4F5F7',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  avatarText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#191C1F',
  },
  activeDot: {
    width: 9,
    height: 9,
    borderRadius: 4.5,
    backgroundColor: '#00C853',
    position: 'absolute',
    bottom: -1,
    right: -1,
    borderWidth: 1.5,
    borderColor: '#FFFFFF',
  },
  headerMiddle: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  logoText: {
    fontSize: 20,
    fontWeight: '800',
    color: '#191C1F',
    letterSpacing: -0.5,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  iconButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F4F5F7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  vipBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F8F9FA',
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  vipBannerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  pinkCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#FFF0F3',
    alignItems: 'center',
    justifyContent: 'center',
  },
  vipBannerText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#191C1F',
  },
  balanceContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  balanceSubtitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#72777A',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  balanceAmount: {
    fontSize: 38,
    fontWeight: '800',
    color: '#191C1F',
    letterSpacing: -1,
    marginBottom: 8,
  },
  currencyPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F4F5F7',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  currencyPillText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#555A5E',
  },
  actionButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
    paddingHorizontal: 6,
  },
  actionItem: {
    alignItems: 'center',
    gap: 6,
  },
  actionCircleDark: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#191C1F',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  actionCircleGray: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#F4F5F7',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  actionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#191C1F',
  },
  nfcPromoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#E5F2FF',
    borderRadius: 20,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#D0E6FF',
  },
  nfcPromoLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  nfcBadgeIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  nfcPromoTextContainer: {
    gap: 2,
  },
  nfcPromoTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0058BC',
  },
  nfcPromoSubtitle: {
    fontSize: 12,
    color: '#004493',
  },
  cardContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 18,
    marginBottom: 28,
    borderWidth: 1,
    borderColor: '#EBECEF',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.03,
    shadowRadius: 10,
    elevation: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  cardHeaderLeft: {
    gap: 2,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#191C1F',
    letterSpacing: -0.3,
  },
  cardSubtitle: {
    fontSize: 12,
    color: '#72777A',
  },
  cardLimitText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#72777A',
  },
  pocketRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  pocketInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  pocketDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  pocketName: {
    fontSize: 13,
    fontWeight: '600',
    color: '#191C1F',
  },
  pocketAmount: {
    fontSize: 13,
    fontWeight: '700',
    color: '#191C1F',
  },
  pocketMax: {
    fontSize: 12,
    fontWeight: '400',
    color: '#72777A',
  },
  progressBarBg: {
    height: 6,
    backgroundColor: '#F4F5F7',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  transactionsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#191C1F',
    letterSpacing: -0.3,
  },
  seeAllText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0075EB',
  },
  zeroStateCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#EBECEF',
    borderStyle: 'dashed',
  },
  zeroStateIconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#EDEEEF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  zeroStateTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#191C1F',
    marginBottom: 4,
  },
  zeroStateDesc: {
    fontSize: 13,
    color: '#72777A',
    textAlign: 'center',
    lineHeight: 18,
  },
  transactionsList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#EBECEF',
    overflow: 'hidden',
  },
  transactionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F4F5F7',
  },
  txLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  txIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  txMeta: {
    gap: 2,
  },
  txMerchant: {
    fontSize: 14,
    fontWeight: '700',
    color: '#191C1F',
  },
  txSubtitle: {
    fontSize: 11,
    color: '#72777A',
    fontWeight: '500',
  },
  txRight: {
    alignItems: 'flex-end',
    gap: 4,
  },
  txAmount: {
    fontSize: 14,
    fontWeight: '700',
    color: '#191C1F',
  },
});
