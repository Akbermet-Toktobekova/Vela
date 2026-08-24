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
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
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
      {/* 1. Revolut 10 Luminous Silk Cobalt Gradient Canvas */}
      <LinearGradient
        colors={['#1754EE', '#2A72FF', '#5093FF', '#82B5FF']}
        start={{ x: 0.1, y: 0 }}
        end={{ x: 0.9, y: 0.55 }}
        style={styles.gradientBg}
      >
        <ScrollView 
          style={styles.container} 
          contentContainerStyle={[styles.contentContainer, { paddingTop: Math.max(insets.top, 16) }]} 
          showsVerticalScrollIndicator={false}
        >
          {/* Top Revolut Header */}
          <View style={styles.header}>
            <View style={styles.avatarPill}>
              <Text style={styles.avatarText}>{profile.initials || 'SZ'}</Text>
            </View>

            {/* Revolut Capsule Search Bar */}
            <TouchableOpacity style={styles.searchCapsule} activeOpacity={0.8} onPress={() => setAddModalVisible(true)}>
              <Ionicons name="search" size={16} color="rgba(255,255,255,0.85)" />
              <Text style={styles.searchText}>Search expenses or merchants</Text>
            </TouchableOpacity>

            <View style={styles.headerIconsRow}>
              <TouchableOpacity style={styles.headerGlassIcon} onPress={() => setGuideModalVisible(true)} activeOpacity={0.7}>
                <Ionicons name="bar-chart" size={18} color="#FFFFFF" />
              </TouchableOpacity>
              <TouchableOpacity style={styles.headerGlassIcon} onPress={() => setGuideModalVisible(true)} activeOpacity={0.7}>
                <Ionicons name="globe-outline" size={18} color="#FFFFFF" />
              </TouchableOpacity>
            </View>
          </View>

          {/* Hero Revolut Title & Balance */}
          <View style={styles.heroSection}>
            <Text style={styles.heroTitle}>Master your wealth</Text>
            <Text style={styles.heroSubtitle}>
              Spent this month: <Text style={styles.heroSpentHighlight}>€{totalSpent.toFixed(2)}</Text> of €{limit.toLocaleString()}
            </Text>

            {/* Glass CTA Pill Button */}
            <TouchableOpacity style={styles.glassCtaBtn} onPress={() => setAddModalVisible(true)} activeOpacity={0.8}>
              <Ionicons name="add" size={18} color="#FFFFFF" style={{ marginRight: 4 }} />
              <Text style={styles.glassCtaText}>Add new expense</Text>
            </TouchableOpacity>
          </View>

          {/* Frosted Security / VIP Alert Card (Exact Revolut Style) */}
          <View style={styles.securityAlertCard}>
            <View style={styles.alertCardContent}>
              <View style={styles.alertIconCircle}>
                <Ionicons name="heart" size={20} color="#FF3366" />
              </View>
              <View style={styles.alertTextContainer}>
                <Text style={styles.alertTitle}>Vela VIP Perk Active</Text>
                <Text style={styles.alertSubtitle}>Солнышко, я люблю тебя ❤️</Text>
              </View>
            </View>
            <TouchableOpacity 
              style={styles.alertActionBtn} 
              onPress={() => setGuideModalVisible(true)}
              activeOpacity={0.8}
            >
              <Text style={styles.alertActionText}>Apple Pay NFC Setup</Text>
            </TouchableOpacity>
          </View>

          {/* White Bottom Canvas Container for Cards & Pockets */}
          <View style={styles.bottomWhiteCard}>
            {/* Quick Segment Pills (Stocks / ETFs style in Revolut) */}
            <View style={styles.filterPillsRow}>
              <TouchableOpacity style={[styles.filterPill, styles.filterPillActive]}>
                <Text style={[styles.filterPillText, styles.filterPillTextActive]}>Budget Pockets</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.filterPill} onPress={() => setAddModalVisible(true)}>
                <Text style={styles.filterPillText}>Recent History</Text>
              </TouchableOpacity>
            </View>

            {/* Revolut Pockets Widget */}
            <View style={styles.pocketsWidget}>
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

              <View style={[styles.pocketRow, { marginTop: 16 }]}>
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

              <View style={[styles.pocketRow, { marginTop: 16 }]}>
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

            {/* Transactions Header */}
            <View style={styles.transactionsHeader}>
              <Text style={styles.sectionTitle}>Transactions</Text>
              <TouchableOpacity onPress={() => setAddModalVisible(true)}>
                <Text style={styles.seeAllText}>+ Add</Text>
              </TouchableOpacity>
            </View>

            {transactions.length === 0 ? (
              <View style={styles.zeroStateCard}>
                <Ionicons name="receipt-outline" size={26} color="#72777A" style={{ marginBottom: 6 }} />
                <Text style={styles.zeroStateTitle}>No transactions recorded</Text>
                <Text style={styles.zeroStateDesc}>
                  Tap «Add new expense» or pay with Apple Pay to see live analytics here.
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
                          size={19} 
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
    backgroundColor: '#1754EE',
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
    marginBottom: 24,
  },
  avatarPill: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(255,255,255,0.25)',
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
    backgroundColor: 'rgba(255,255,255,0.2)',
    height: 38,
    borderRadius: 19,
    paddingHorizontal: 14,
    marginHorizontal: 10,
    gap: 8,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
  },
  searchText: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.85)',
    fontWeight: '500',
  },
  headerIconsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  headerGlassIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
  },
  heroSection: {
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 28,
  },
  heroTitle: {
    fontSize: 34,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -1,
    textAlign: 'center',
    marginBottom: 6,
  },
  heroSubtitle: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.85)',
    fontWeight: '500',
    textAlign: 'center',
    marginBottom: 20,
  },
  heroSpentHighlight: {
    fontWeight: '700',
    color: '#FFFFFF',
  },
  glassCtaBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.25)',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.4)',
  },
  glassCtaText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  securityAlertCard: {
    backgroundColor: 'rgba(255,255,255,0.92)',
    borderRadius: 24,
    padding: 18,
    marginHorizontal: 16,
    marginBottom: 20,
    ...Platform.select({
      ios: {
        shadowColor: '#001A4D',
        shadowOffset: { width: 0, height: 6 },
        shadowOpacity: 0.12,
        shadowRadius: 14,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  alertCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 14,
  },
  alertIconCircle: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#FFF0F4',
    alignItems: 'center',
    justifyContent: 'center',
  },
  alertTextContainer: {
    flex: 1,
    gap: 2,
  },
  alertTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111417',
  },
  alertSubtitle: {
    fontSize: 13,
    color: '#646B73',
    fontWeight: '500',
  },
  alertActionBtn: {
    backgroundColor: '#111417',
    borderRadius: 16,
    paddingVertical: 13,
    alignItems: 'center',
  },
  alertActionText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  bottomWhiteCard: {
    backgroundColor: '#F8F9FB',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 16,
    paddingTop: 20,
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
  pocketsWidget: {
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
  transactionsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111417',
    letterSpacing: -0.3,
  },
  seeAllText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0075EB',
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
