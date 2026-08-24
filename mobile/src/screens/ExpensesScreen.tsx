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
    let iconBg = colors.accentGreenLight;

    if (category === 'wants') {
      iconName = 'cafe';
      iconBg = colors.accentPurpleLight;
    } else if (category === 'savings') {
      iconName = 'wallet';
      iconBg = colors.accentBlueLight;
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
    <View style={[styles.mainWrapper, { paddingTop: Math.max(insets.top, 16) }]}>
      <ScrollView 
        style={styles.container} 
        contentContainerStyle={styles.contentContainer} 
        showsVerticalScrollIndicator={false}
      >
        {/* 1. Top Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{profile.initials || 'SZ'}</Text>
              <View style={styles.activeDot} />
            </View>
            <View style={styles.userGreeting}>
              <Text style={styles.greetingTitle}>Hi, {profile.name || 'Sanatbek'}</Text>
              <Text style={styles.greetingPlan}>Vela Ultra VIP</Text>
            </View>
          </View>
          <View style={styles.headerRight}>
            <TouchableOpacity style={styles.iconButton} onPress={() => setGuideModalVisible(true)} activeOpacity={0.7}>
              <Ionicons name="hardware-chip-outline" size={19} color={colors.text} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.iconButton} onPress={() => setAddModalVisible(true)} activeOpacity={0.7}>
              <Ionicons name="add" size={22} color={colors.text} />
            </TouchableOpacity>
          </View>
        </View>

        {/* 2. VIP Love Banner (Ultra Luxury Pill) */}
        <TouchableOpacity style={styles.vipBanner} activeOpacity={0.85}>
          <View style={styles.vipBannerLeft}>
            <View style={styles.pinkCircle}>
              <Ionicons name="heart" size={13} color={colors.accentPink} />
            </View>
            <Text style={styles.vipBannerText}>Солнышко, я люблю тебя ❤️</Text>
          </View>
          <Ionicons name="chevron-forward" size={16} color={colors.textSecondary} />
        </TouchableOpacity>

        {/* 3. Hero Balance Card (Floating Velvet Finish) */}
        <View style={styles.balanceContainer}>
          <Text style={styles.balanceSubtitle}>TOTAL SPENT THIS MONTH</Text>
          <Text style={styles.balanceAmount}>
            {profile.currency === 'USD' ? '$' : profile.currency === 'HUF' ? 'Ft ' : '€'}
            {totalSpent.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Text>
          <TouchableOpacity style={styles.currencyPill} activeOpacity={0.7}>
            <Text style={styles.currencyPillText}>{profile.currency} · European Union</Text>
            <Ionicons name="chevron-down" size={13} color={colors.textSecondary} style={{ marginLeft: 4 }} />
          </TouchableOpacity>
        </View>

        {/* 4. Revolut 10 Circular Action Buttons */}
        <View style={styles.actionButtonsRow}>
          <View style={styles.actionItem}>
            <TouchableOpacity 
              style={styles.actionCircleDark} 
              onPress={() => setAddModalVisible(true)} 
              activeOpacity={0.7}
            >
              <Ionicons name="add" size={26} color="#FFFFFF" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>Add money</Text>
          </View>

          <View style={styles.actionItem}>
            <TouchableOpacity 
              style={styles.actionCircleGray} 
              onPress={() => setGuideModalVisible(true)} 
              activeOpacity={0.7}
            >
              <Ionicons name="radio-outline" size={22} color={colors.text} />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>NFC Setup</Text>
          </View>

          <View style={styles.actionItem}>
            <TouchableOpacity 
              style={styles.actionCircleGray} 
              onPress={() => setAddModalVisible(true)} 
              activeOpacity={0.7}
            >
              <Ionicons name="pie-chart-outline" size={22} color={colors.text} />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>Analytics</Text>
          </View>

          <View style={styles.actionItem}>
            <TouchableOpacity 
              style={styles.actionCircleGray} 
              onPress={() => setGuideModalVisible(true)} 
              activeOpacity={0.7}
            >
              <Ionicons name="ellipsis-horizontal" size={22} color={colors.text} />
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
              <Ionicons name="phone-portrait-outline" size={20} color={colors.accentBlue} />
            </View>
            <View style={styles.nfcPromoTextContainer}>
              <Text style={styles.nfcPromoTitle}>Automate Apple Pay Tracking</Text>
              <Text style={styles.nfcPromoSubtitle}>Tap to connect iPhone Shortcuts in 3 steps</Text>
            </View>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.accentBlue} />
        </TouchableOpacity>

        {/* 6. Revolut Pockets: 50/30/20 Budget Widget */}
        <View style={styles.cardContainer}>
          <View style={styles.cardHeader}>
            <View style={styles.cardHeaderLeft}>
              <Text style={styles.cardTitle}>Budget Pockets</Text>
              <Text style={styles.cardSubtitle}>50/30/20 Wealth Strategy</Text>
            </View>
            <View style={styles.limitBadge}>
              <Text style={styles.cardLimitText}>€{limit.toLocaleString()} limit</Text>
            </View>
          </View>

          {/* Needs Pocket (50%) */}
          <View style={styles.pocketRow}>
            <View style={styles.pocketInfo}>
              <View style={[styles.pocketDot, { backgroundColor: colors.accentGreen }]} />
              <Text style={styles.pocketName}>Needs (50%)</Text>
            </View>
            <Text style={styles.pocketAmount}>
              €{needsSpent.toFixed(2)} <Text style={styles.pocketMax}>/ €{needsLimit.toFixed(0)}</Text>
            </Text>
          </View>
          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, { width: `${needsPercent}%`, backgroundColor: colors.accentGreen }]} />
          </View>

          {/* Wants Pocket (30%) */}
          <View style={[styles.pocketRow, { marginTop: 14 }]}>
            <View style={styles.pocketInfo}>
              <View style={[styles.pocketDot, { backgroundColor: colors.accentPurple }]} />
              <Text style={styles.pocketName}>Wants (30%)</Text>
            </View>
            <Text style={styles.pocketAmount}>
              €{wantsSpent.toFixed(2)} <Text style={styles.pocketMax}>/ €{wantsLimit.toFixed(0)}</Text>
            </Text>
          </View>
          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, { width: `${wantsPercent}%`, backgroundColor: colors.accentPurple }]} />
          </View>

          {/* Savings Pocket (20%) */}
          <View style={[styles.pocketRow, { marginTop: 14 }]}>
            <View style={styles.pocketInfo}>
              <View style={[styles.pocketDot, { backgroundColor: colors.accentBlue }]} />
              <Text style={styles.pocketName}>Savings (20%)</Text>
            </View>
            <Text style={styles.pocketAmount}>
              €{savingsSpent.toFixed(2)} <Text style={styles.pocketMax}>/ €{savingsLimit.toFixed(0)}</Text>
            </Text>
          </View>
          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, { width: `${savingsPercent}%`, backgroundColor: colors.accentBlue }]} />
          </View>
        </View>

        {/* 7. Recent Transactions Feed */}
        <View style={styles.transactionsHeader}>
          <Text style={styles.sectionTitle}>Transactions</Text>
          <TouchableOpacity onPress={() => setAddModalVisible(true)} activeOpacity={0.7}>
            <Text style={styles.seeAllText}>+ Add</Text>
          </TouchableOpacity>
        </View>

        {transactions.length === 0 ? (
          <View style={styles.zeroStateCard}>
            <View style={styles.zeroStateIconCircle}>
              <Ionicons name="receipt-outline" size={28} color={colors.textSecondary} />
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
                  <View style={[styles.txIconCircle, { backgroundColor: tx.iconBg || colors.surfaceSecondary }]}>
                    <Ionicons 
                      name={tx.category === 'needs' ? 'cart-outline' : tx.category === 'wants' ? 'cafe-outline' : 'wallet-outline'} 
                      size={19} 
                      color={colors.text} 
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
                    <Ionicons name="trash-outline" size={13} color={colors.textMuted} />
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
    backgroundColor: colors.background,
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
    gap: 12,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    borderWidth: 1,
    borderColor: colors.border,
    ...Platform.select({
      ios: {
        shadowColor: colors.shadowColor,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.04,
        shadowRadius: 4,
      },
      android: {
        elevation: 1,
      },
    }),
  },
  avatarText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
  },
  activeDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.accentGreen,
    position: 'absolute',
    bottom: -1,
    right: -1,
    borderWidth: 2,
    borderColor: colors.surface,
  },
  userGreeting: {
    gap: 1,
  },
  greetingTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
    letterSpacing: -0.2,
  },
  greetingPlan: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.accentBlue,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  iconButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  vipBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.surface,
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 11,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: colors.border,
    ...Platform.select({
      ios: {
        shadowColor: colors.shadowColor,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.03,
        shadowRadius: 6,
      },
      android: {
        elevation: 1,
      },
    }),
  },
  vipBannerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  pinkCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.accentPinkLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  vipBannerText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text,
  },
  balanceContainer: {
    alignItems: 'center',
    marginBottom: 24,
    paddingVertical: 8,
  },
  balanceSubtitle: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textSecondary,
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  balanceAmount: {
    fontSize: 42,
    fontWeight: '800',
    color: colors.text,
    letterSpacing: -1.2,
    marginBottom: 10,
  },
  currencyPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.border,
  },
  currencyPillText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  actionButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
    paddingHorizontal: 4,
  },
  actionItem: {
    alignItems: 'center',
    gap: 6,
  },
  actionCircleDark: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    ...Platform.select({
      ios: {
        shadowColor: colors.primary,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.18,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  actionCircleGray: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    ...Platform.select({
      ios: {
        shadowColor: colors.shadowColor,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.04,
        shadowRadius: 6,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  actionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.text,
  },
  nfcPromoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.accentBlueLight,
    borderRadius: 20,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#D4E7FF',
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
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  nfcPromoTextContainer: {
    gap: 2,
  },
  nfcPromoTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.accentBlue,
  },
  nfcPromoSubtitle: {
    fontSize: 12,
    color: '#004493',
  },
  cardContainer: {
    backgroundColor: colors.surface,
    borderRadius: 24,
    padding: 20,
    marginBottom: 28,
    borderWidth: 1,
    borderColor: colors.border,
    ...Platform.select({
      ios: {
        shadowColor: colors.shadowColor,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.04,
        shadowRadius: 10,
      },
      android: {
        elevation: 2,
      },
    }),
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
    color: colors.text,
    letterSpacing: -0.3,
  },
  cardSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  limitBadge: {
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  cardLimitText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textSecondary,
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
    color: colors.text,
  },
  pocketAmount: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.text,
  },
  pocketMax: {
    fontSize: 12,
    fontWeight: '400',
    color: colors.textSecondary,
  },
  progressBarBg: {
    height: 6,
    backgroundColor: colors.surfaceSecondary,
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
    color: colors.text,
    letterSpacing: -0.3,
  },
  seeAllText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.accentBlue,
  },
  zeroStateCard: {
    backgroundColor: colors.surface,
    borderRadius: 22,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderStyle: 'dashed',
  },
  zeroStateIconCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: colors.surfaceSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  zeroStateTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.text,
    marginBottom: 4,
  },
  zeroStateDesc: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
  transactionsList: {
    backgroundColor: colors.surface,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  transactionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
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
    color: colors.text,
  },
  txSubtitle: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  txRight: {
    alignItems: 'flex-end',
    gap: 4,
  },
  txAmount: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
  },
});
