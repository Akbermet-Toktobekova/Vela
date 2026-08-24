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
      {/* 1. Authentic Revolut Mint Emerald Aurora Silk Gradient */}
      <LinearGradient
        colors={['#009A6B', '#00B87C', '#10C888', '#34D399', '#6EE7B7']}
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
              <Ionicons name="search" size={17} color="rgba(0,40,25,0.75)" />
              <Text style={styles.searchText}>Search</Text>
            </TouchableOpacity>

            <View style={styles.headerIconsRow}>
              <TouchableOpacity style={styles.headerGlassCardBtn} onPress={() => setGuideModalVisible(true)} activeOpacity={0.8}>
                <Ionicons name="bar-chart" size={18} color="#003D26" />
              </TouchableOpacity>
              <TouchableOpacity style={styles.headerGlassCardBtn} onPress={() => setGuideModalVisible(true)} activeOpacity={0.8}>
                <Ionicons name="card" size={18} color="#003D26" />
              </TouchableOpacity>
            </View>
          </View>

          {/* Hero Revolut Group / Account Name & Balance */}
          <View style={styles.heroSection}>
            <Text style={styles.accountLabel}>{profile.name || 'Sanatbek'} · Personal</Text>
            
            <Text style={styles.amountHeroText}>
              {profile.currency === 'HUF' ? `Ft ${totalSpent.toFixed(2)}` : profile.currency === 'USD' ? `$${totalSpent.toFixed(2)}` : `€${totalSpent.toFixed(2)}`}
            </Text>

            {/* Pagination Carousel Indicator Capsule */}
            <View style={styles.carouselCapsule}>
              <View style={[styles.carouselDot, styles.carouselDotActive]} />
              <View style={styles.carouselDot} />
              <View style={styles.carouselDot} />
              <View style={styles.carouselDot} />
            </View>
          </View>

          {/* Revolut 4 Frosted Action Circles Row */}
          <View style={styles.actionRow}>
            <View style={styles.actionItem}>
              <TouchableOpacity style={styles.actionGlassCircle} onPress={() => setAddModalVisible(true)} activeOpacity={0.8}>
                <Ionicons name="add" size={24} color="#003D26" />
              </TouchableOpacity>
              <Text style={styles.actionLabel}>Add money</Text>
            </View>

            <View style={styles.actionItem}>
              <TouchableOpacity style={styles.actionGlassCircle} onPress={() => setGuideModalVisible(true)} activeOpacity={0.8}>
                <Ionicons name="swap-horizontal" size={22} color="#003D26" />
              </TouchableOpacity>
              <Text style={styles.actionLabel}>Move</Text>
            </View>

            <View style={styles.actionItem}>
              <TouchableOpacity style={styles.actionGlassCircle} onPress={() => setGuideModalVisible(true)} activeOpacity={0.8}>
                <Ionicons name="information-circle-outline" size={22} color="#003D26" />
              </TouchableOpacity>
              <Text style={styles.actionLabel}>Info</Text>
            </View>

            <View style={styles.actionItem}>
              <TouchableOpacity style={styles.actionGlassCircle} onPress={() => setGuideModalVisible(true)} activeOpacity={0.8}>
                <Ionicons name="ellipsis-horizontal" size={22} color="#003D26" />
              </TouchableOpacity>
              <Text style={styles.actionLabel}>More</Text>
            </View>
          </View>

          {/* Story / Perk Banner Card (Light Mint Card with Snowflake / Heart icon) */}
          <View style={styles.storyCard}>
            <View style={styles.storyHeader}>
              <View style={styles.snowflakeCircle}>
                <Ionicons name="heart" size={20} color="#FF3366" />
              </View>
              <View style={styles.storyTextContainer}>
                <Text style={styles.storyTitle}>Солнышко, я люблю тебя ❤️</Text>
                <Text style={styles.storySubtitle}>Vela Ultra automated tracking is active on your device.</Text>
              </View>
            </View>
            <TouchableOpacity 
              style={styles.reviewBtn} 
              onPress={() => setGuideModalVisible(true)}
              activeOpacity={0.85}
            >
              <Text style={styles.reviewBtnText}>Apple Pay NFC Setup</Text>
            </TouchableOpacity>
          </View>

          {/* Frosted Mint Bottom Container for Pockets & Feed */}
          <View style={styles.frostedSheetContainer}>
            {/* Quick Summary Card */}
            <View style={styles.summaryCard}>
              <View style={styles.summaryLeft}>
                <View style={styles.countryFlagCircle}>
                  <Text style={{ fontSize: 18 }}>🇭🇺</Text>
                </View>
                <View>
                  <Text style={styles.summaryTitle}>Personal ➔ Budget Limit</Text>
                  <Text style={styles.summaryDate}>Monthly: €{limit.toLocaleString()}</Text>
                </View>
              </View>
              <Text style={styles.summaryAmount}>+€{(limit - totalSpent).toFixed(0)}</Text>
            </View>

            {/* Pockets Card */}
            <View style={styles.pocketsCard}>
              <Text style={styles.pocketsCardHeader}>BUDGET POCKETS (50/30/20)</Text>
              
              <View style={styles.pocketRow}>
                <View style={styles.pocketInfo}>
                  <View style={[styles.pocketDot, { backgroundColor: '#009A6B' }]} />
                  <Text style={styles.pocketName}>Needs (50%)</Text>
                </View>
                <Text style={styles.pocketAmount}>
                  €{needsSpent.toFixed(2)} <Text style={styles.pocketMax}>/ €{needsLimit.toFixed(0)}</Text>
                </Text>
              </View>
              <View style={styles.progressBarBg}>
                <View style={[styles.progressBarFill, { width: `${needsPercent}%`, backgroundColor: '#009A6B' }]} />
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

            {/* Transactions Header */}
            <View style={styles.transactionsHeader}>
              <Text style={styles.sectionTitle}>Transactions</Text>
              <TouchableOpacity onPress={() => setAddModalVisible(true)}>
                <Text style={styles.seeAllText}>See all</Text>
              </TouchableOpacity>
            </View>

            {/* Transactions List */}
            {transactions.length === 0 ? (
              <View style={styles.zeroStateCard}>
                <Ionicons name="receipt-outline" size={26} color="#005A3D" style={{ marginBottom: 6 }} />
                <Text style={styles.zeroStateTitle}>No transactions recorded</Text>
                <Text style={styles.zeroStateDesc}>
                  Tap «Add money» above or pay with Apple Pay to see live expenses.
                </Text>
              </View>
            ) : (
              <View style={styles.transactionsList}>
                {transactions.map((tx) => (
                  <View key={tx.id} style={styles.transactionItem}>
                    <View style={styles.txLeft}>
                      <View style={[styles.txIconCircle, { backgroundColor: tx.iconBg || '#EAF6F0' }]}>
                        <Ionicons 
                          name={tx.category === 'needs' ? 'cart-outline' : tx.category === 'wants' ? 'cafe-outline' : 'wallet-outline'} 
                          size={18} 
                          color="#003D26" 
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
                        <Ionicons name="trash-outline" size={13} color="#8DA99E" />
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
    backgroundColor: '#009A6B',
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
  avatarCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(0, 45, 30, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.4)',
  },
  avatarText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#003D26',
  },
  searchCapsule: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.28)',
    height: 40,
    borderRadius: 20,
    paddingHorizontal: 14,
    marginHorizontal: 10,
    gap: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.4)',
  },
  searchText: {
    fontSize: 14,
    color: 'rgba(0, 45, 30, 0.85)',
    fontWeight: '500',
  },
  headerIconsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  headerGlassCardBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.28)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.4)',
  },
  heroSection: {
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  accountLabel: {
    fontSize: 15,
    color: 'rgba(0, 45, 30, 0.85)',
    fontWeight: '600',
    marginBottom: 6,
  },
  amountHeroText: {
    fontSize: 48,
    fontWeight: '800',
    color: '#002E1C',
    letterSpacing: -1.2,
    marginBottom: 16,
  },
  carouselCapsule: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(0, 45, 30, 0.15)',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 12,
  },
  carouselDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: 'rgba(0, 45, 30, 0.35)',
  },
  carouselDotActive: {
    backgroundColor: '#002E1C',
    width: 6,
    height: 6,
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
    backgroundColor: 'rgba(255, 255, 255, 0.35)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.5)',
  },
  actionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#002E1C',
  },
  storyCard: {
    backgroundColor: 'rgba(230, 248, 240, 0.95)',
    borderRadius: 24,
    padding: 18,
    marginHorizontal: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.7)',
    ...Platform.select({
      ios: {
        shadowColor: '#002E1C',
        shadowOffset: { width: 0, height: 6 },
        shadowOpacity: 0.08,
        shadowRadius: 12,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  storyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 14,
  },
  snowflakeCircle: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  storyTextContainer: {
    flex: 1,
    gap: 2,
  },
  storyTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#002E1C',
    letterSpacing: -0.2,
  },
  storySubtitle: {
    fontSize: 12,
    color: '#005A3D',
    lineHeight: 16,
  },
  reviewBtn: {
    backgroundColor: '#111417',
    borderRadius: 16,
    paddingVertical: 13,
    alignItems: 'center',
  },
  reviewBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  frostedSheetContainer: {
    backgroundColor: 'rgba(240, 252, 246, 0.96)',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 16,
    paddingTop: 18,
  },
  summaryCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#D4EFE3',
  },
  summaryLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  countryFlagCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#EAF6F0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  summaryTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#002E1C',
  },
  summaryDate: {
    fontSize: 12,
    color: '#005A3D',
  },
  summaryAmount: {
    fontSize: 15,
    fontWeight: '800',
    color: '#009A6B',
  },
  pocketsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 18,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#D4EFE3',
  },
  pocketsCardHeader: {
    fontSize: 11,
    fontWeight: '800',
    color: '#005A3D',
    letterSpacing: 0.5,
    marginBottom: 12,
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
    color: '#002E1C',
  },
  pocketAmount: {
    fontSize: 13,
    fontWeight: '700',
    color: '#002E1C',
  },
  pocketMax: {
    fontSize: 12,
    fontWeight: '400',
    color: '#005A3D',
  },
  progressBarBg: {
    height: 6,
    backgroundColor: '#EAF6F0',
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
    color: '#002E1C',
    letterSpacing: -0.3,
  },
  seeAllText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#009A6B',
  },
  zeroStateCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#D4EFE3',
    borderStyle: 'dashed',
  },
  zeroStateTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#002E1C',
    marginBottom: 4,
  },
  zeroStateDesc: {
    fontSize: 13,
    color: '#005A3D',
    textAlign: 'center',
    lineHeight: 18,
  },
  transactionsList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#D4EFE3',
    overflow: 'hidden',
  },
  transactionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F8F4',
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
    color: '#002E1C',
  },
  txSubtitle: {
    fontSize: 11,
    color: '#005A3D',
    fontWeight: '500',
  },
  txRight: {
    alignItems: 'flex-end',
    gap: 4,
  },
  txAmount: {
    fontSize: 14,
    fontWeight: '700',
    color: '#002E1C',
  },
});
