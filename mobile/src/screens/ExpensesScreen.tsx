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
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { useUser } from '../context/UserContext';
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

  const limit = profile.monthlyLimit || 2000;
  const needsLimit = limit * 0.5;
  const wantsLimit = limit * 0.3;
  const savingsLimit = limit * 0.2;

  const needsPercent = Math.min(100, Math.round((needsSpent / needsLimit) * 100)) || 0;
  const wantsPercent = Math.min(100, Math.round((wantsSpent / wantsLimit) * 100)) || 0;
  const savingsPercent = Math.min(100, Math.round((savingsSpent / savingsLimit) * 100)) || 0;

  return (
    <View style={styles.mainWrapper}>
      {/* 1. Authentic Revolut Radial/Linear Aurora Mesh Gradient */}
      <LinearGradient
        colors={['#1E16E2', '#3D25F4', '#5515EE', '#7A22E8', '#9B2DF0']}
        start={{ x: 0.1, y: 0.0 }}
        end={{ x: 0.9, y: 0.7 }}
        style={styles.gradientBg}
      >
        <ScrollView 
          style={styles.container} 
          contentContainerStyle={[styles.contentContainer, { paddingTop: Math.max(insets.top, 14) }]} 
          showsVerticalScrollIndicator={false}
        >
          {/* Top Revolut Header */}
          <View style={styles.header}>
            <View style={styles.avatarCircle}>
              <Text style={styles.avatarText}>{profile.initials || 'SZ'}</Text>
            </View>

            {/* Revolut Capsule Search Bar */}
            <TouchableOpacity style={styles.searchCapsule} activeOpacity={0.8} onPress={() => setAddModalVisible(true)}>
              <Ionicons name="search" size={17} color="rgba(255,255,255,0.85)" />
              <Text style={styles.searchText}>Search</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.headerGlassCardBtn} onPress={() => setGuideModalVisible(true)} activeOpacity={0.8}>
              <Ionicons name="card" size={18} color="#FFFFFF" />
            </TouchableOpacity>
          </View>

          {/* Hero Revolut Points / Spent Balance */}
          <View style={styles.heroSection}>
            <Text style={styles.planLabel}>Vela Ultra plan</Text>
            
            <View style={styles.amountHeroRow}>
              <View style={styles.polyHexagon}>
                <Ionicons name="sparkles" size={18} color="#2A24F4" />
              </View>
              <Text style={styles.amountHeroText}>
                {Math.round(totalSpent)}
              </Text>
            </View>

            <Text style={styles.rateLabel}>
              Spent this month · €{totalSpent.toFixed(2)} of €{limit.toLocaleString()}
            </Text>

            {/* Frosted Upgrade/Add Pill Button */}
            <TouchableOpacity style={styles.frostedPillBtn} onPress={() => setAddModalVisible(true)} activeOpacity={0.8}>
              <Text style={styles.frostedPillText}>+ Add expense</Text>
            </TouchableOpacity>
          </View>

          {/* Revolut 4 Frosted Action Circles Row */}
          <View style={styles.actionRow}>
            <View style={styles.actionItem}>
              <TouchableOpacity style={styles.actionGlassCircle} onPress={() => setAddModalVisible(true)} activeOpacity={0.8}>
                <Ionicons name="add" size={24} color="#FFFFFF" />
              </TouchableOpacity>
              <Text style={styles.actionLabel}>Add</Text>
            </View>

            <View style={styles.actionItem}>
              <TouchableOpacity style={styles.actionGlassCircle} onPress={() => setGuideModalVisible(true)} activeOpacity={0.8}>
                <Ionicons name="radio-outline" size={20} color="#FFFFFF" />
              </TouchableOpacity>
              <Text style={styles.actionLabel}>NFC Setup</Text>
            </View>

            <View style={styles.actionItem}>
              <TouchableOpacity style={styles.actionGlassCircle} onPress={() => setGuideModalVisible(true)} activeOpacity={0.8}>
                <Ionicons name="diamond-outline" size={20} color="#FFFFFF" />
              </TouchableOpacity>
              <Text style={styles.actionLabel}>VIP Perks</Text>
            </View>

            <View style={styles.actionItem}>
              <TouchableOpacity style={styles.actionGlassCircle} onPress={() => setGuideModalVisible(true)} activeOpacity={0.8}>
                <Ionicons name="ellipsis-horizontal" size={20} color="#FFFFFF" />
              </TouchableOpacity>
              <Text style={styles.actionLabel}>More</Text>
            </View>
          </View>

          {/* Story / Perk Banner Card (White Revolut Card) */}
          <TouchableOpacity style={styles.storyCard} activeOpacity={0.9} onPress={() => setGuideModalVisible(true)}>
            <View style={styles.storyLeft}>
              <Text style={styles.storyTitle}>Солнышко, я люблю тебя ❤️</Text>
              <Text style={styles.storySubtitle}>Tap to connect instant Apple Pay NFC live tracking</Text>
            </View>
            <View style={styles.storyCardsGraphic}>
              <View style={[styles.miniCard, styles.miniCardBack]} />
              <View style={[styles.miniCard, styles.miniCardFront]}>
                <Ionicons name="card" size={14} color="#FFFFFF" />
              </View>
            </View>
          </TouchableOpacity>

          {/* Frosted Glass Bottom Container for Pockets & Feed */}
          <View style={styles.frostedSheetContainer}>
            {/* Quick Segment Filter Pills */}
            <View style={styles.filterPillsRow}>
              <TouchableOpacity style={[styles.filterPill, styles.filterPillActive]}>
                <Text style={[styles.filterPillText, styles.filterPillTextActive]}>Budget Pockets</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.filterPill} onPress={() => setAddModalVisible(true)}>
                <Text style={styles.filterPillText}>Transactions</Text>
              </TouchableOpacity>
            </View>

            {/* Pockets Card */}
            <View style={styles.pocketsCard}>
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

            {/* Transactions List */}
            {transactions.length === 0 ? (
              <View style={styles.zeroStateCard}>
                <Ionicons name="receipt-outline" size={26} color="#72777A" style={{ marginBottom: 6 }} />
                <Text style={styles.zeroStateTitle}>No expenses yet</Text>
                <Text style={styles.zeroStateDesc}>
                  Tap «Add» above or pay with Apple Pay to see live expenses.
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
                          size={18} 
                          color="#111417" 
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
                        <Ionicons name="trash-outline" size={13} color="#949BA2" />
                      </TouchableOpacity>
                    </View>
                  </View>
                ))}
              </View>
            )}

            <View style={{ height: 40 }} />
          </View>
        </ScrollView>
      </LinearGradient>

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
    backgroundColor: '#1E16E2',
  },
  gradientBg: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  avatarCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(255,255,255,0.22)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  avatarText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  searchCapsule: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.18)',
    height: 40,
    borderRadius: 20,
    paddingHorizontal: 14,
    marginHorizontal: 10,
    gap: 8,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
  },
  searchText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    fontWeight: '500',
  },
  headerGlassCardBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
  },
  heroSection: {
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 26,
  },
  planLabel: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    fontWeight: '600',
    marginBottom: 8,
  },
  amountHeroRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
  },
  polyHexagon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    transform: [{ rotate: '45deg' }],
  },
  amountHeroText: {
    fontSize: 52,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -1.5,
  },
  rateLabel: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.85)',
    fontWeight: '500',
    marginBottom: 16,
  },
  frostedPillBtn: {
    backgroundColor: 'rgba(255,255,255,0.22)',
    paddingHorizontal: 28,
    paddingVertical: 10,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
  },
  frostedPillText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 12,
    marginBottom: 24,
  },
  actionItem: {
    alignItems: 'center',
    gap: 8,
  },
  actionGlassCircle: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  actionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  storyCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 18,
    marginHorizontal: 16,
    marginBottom: 20,
    ...Platform.select({
      ios: {
        shadowColor: '#000000',
        shadowOffset: { width: 0, height: 6 },
        shadowOpacity: 0.12,
        shadowRadius: 12,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  storyLeft: {
    flex: 1,
    gap: 4,
    paddingRight: 10,
  },
  storyTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111417',
    letterSpacing: -0.2,
  },
  storySubtitle: {
    fontSize: 12,
    color: '#646B73',
    lineHeight: 16,
  },
  storyCardsGraphic: {
    width: 54,
    height: 38,
    position: 'relative',
  },
  miniCard: {
    position: 'absolute',
    width: 44,
    height: 28,
    borderRadius: 6,
  },
  miniCardBack: {
    top: 0,
    right: 0,
    backgroundColor: '#1E16E2',
    opacity: 0.6,
  },
  miniCardFront: {
    bottom: 0,
    left: 0,
    backgroundColor: '#111417',
    alignItems: 'center',
    justifyContent: 'center',
  },
  frostedSheetContainer: {
    backgroundColor: '#F8F9FB',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 16,
    paddingTop: 18,
  },
  filterPillsRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  filterPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#ECEEF2',
  },
  filterPillActive: {
    backgroundColor: '#111417',
    borderColor: '#111417',
  },
  filterPillText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#646B73',
  },
  filterPillTextActive: {
    color: '#FFFFFF',
  },
  pocketsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 18,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#ECEEF2',
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
    color: '#111417',
  },
  pocketAmount: {
    fontSize: 13,
    fontWeight: '700',
    color: '#111417',
  },
  pocketMax: {
    fontSize: 12,
    fontWeight: '400',
    color: '#72777A',
  },
  progressBarBg: {
    height: 6,
    backgroundColor: '#F1F3F6',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  zeroStateCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ECEEF2',
    borderStyle: 'dashed',
  },
  zeroStateTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111417',
    marginBottom: 4,
  },
  zeroStateDesc: {
    fontSize: 13,
    color: '#646B73',
    textAlign: 'center',
    lineHeight: 18,
  },
  transactionsList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ECEEF2',
    overflow: 'hidden',
  },
  transactionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F7',
  },
  txLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  txIconCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
  },
  txMeta: {
    gap: 2,
  },
  txMerchant: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111417',
  },
  txSubtitle: {
    fontSize: 11,
    color: '#646B73',
    fontWeight: '500',
  },
  txRight: {
    alignItems: 'flex-end',
    gap: 4,
  },
  txAmount: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111417',
  },
});
