import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons, Feather } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { useUser } from '../context/UserContext';

export const DashboardScreen: React.FC<{ onNavigateToChat?: () => void }> = ({ onNavigateToChat }) => {
  const insets = useSafeAreaInsets();
  const { profile, vaults, totalSpent, savingsSpent } = useUser();

  const netSurplus = Math.max(0, (profile.monthlyLimit || 2000) - totalSpent);

  return (
    <View style={[styles.mainWrapper, { paddingTop: Math.max(insets.top, 20) }]}>
      <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.screenTitle}>Analytics & Vaults</Text>
            <Text style={styles.screenSubtitle}>Financial Intelligence</Text>
          </View>
          <TouchableOpacity style={styles.monthPill} activeOpacity={0.7}>
            <Text style={styles.monthPillText}>August 2026</Text>
            <Ionicons name="chevron-down" size={12} color="#72777A" style={{ marginLeft: 4 }} />
          </TouchableOpacity>
        </View>

        {/* 1. Net Surplus Hero Card */}
        <View style={styles.heroCard}>
          <View style={styles.heroTop}>
            <Text style={styles.heroLabel}>NET SAVINGS SURPLUS</Text>
            <View style={styles.trendBadge}>
              <Ionicons name="trending-up" size={14} color="#00C853" />
              <Text style={styles.trendText}>On Track</Text>
            </View>
          </View>
          <Text style={styles.heroAmount}>+€{netSurplus.toFixed(2)}</Text>
          <Text style={styles.heroDesc}>Unallocated surplus ready for your savings vaults.</Text>
        </View>

        {/* 2. Revolut Savings Vaults */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Savings Vaults</Text>
          <TouchableOpacity onPress={onNavigateToChat}>
            <Text style={styles.actionLink}>+ New Vault</Text>
          </TouchableOpacity>
        </View>

        {vaults.map((vault) => {
          const progressPercent = Math.min(100, Math.round((vault.currentAmount / vault.targetAmount) * 100)) || 0;
          return (
            <View key={vault.id} style={styles.vaultCard}>
              <View style={styles.vaultHeader}>
                <View style={styles.vaultLeft}>
                  <View style={[styles.vaultIconCircle, { backgroundColor: vault.iconBg }]}>
                    <Ionicons name={vault.iconName as any} size={22} color={vault.iconColor} />
                  </View>
                  <View style={styles.vaultMeta}>
                    <Text style={styles.vaultTitle}>{vault.title}</Text>
                    <Text style={styles.vaultDate}>Target: {vault.targetDate}</Text>
                  </View>
                </View>
                <View style={styles.vaultProgressBadge}>
                  <Text style={styles.vaultPercentText}>{progressPercent}%</Text>
                </View>
              </View>

              <View style={styles.vaultAmountsRow}>
                <Text style={styles.vaultCurrent}>€{vault.currentAmount.toLocaleString()}</Text>
                <Text style={styles.vaultTarget}>of €{vault.targetAmount.toLocaleString()}</Text>
              </View>

              <View style={styles.progressBarBg}>
                <View style={[styles.progressBarFill, { width: `${Math.max(5, progressPercent)}%`, backgroundColor: vault.iconColor }]} />
              </View>
            </View>
          );
        })}

        {/* 3. Debt Strategy Card (Avalanche) */}
        <View style={[styles.sectionHeader, { marginTop: 12 }]}>
          <Text style={styles.sectionTitle}>Debt Strategy</Text>
          <View style={styles.avalancheBadge}>
            <Text style={styles.avalancheText}>Avalanche Method</Text>
          </View>
        </View>

        <View style={styles.debtCard}>
          <View style={styles.debtHeader}>
            <View style={styles.debtLeft}>
              <View style={styles.debtIconCircle}>
                <Ionicons name="card" size={20} color="#FF3366" />
              </View>
              <View>
                <Text style={styles.debtTitle}>Credit Card</Text>
                <Text style={styles.debtApr}>21.5% APR · Highest interest</Text>
              </View>
            </View>
            <TouchableOpacity style={styles.payBtn} onPress={onNavigateToChat}>
              <Text style={styles.payBtnText}>Optimize</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.debtDetails}>
            <View style={styles.debtCol}>
              <Text style={styles.debtColLabel}>CURRENT BALANCE</Text>
              <Text style={styles.debtColValue}>€4,250.00</Text>
            </View>
            <View style={styles.debtDivider} />
            <View style={styles.debtCol}>
              <Text style={styles.debtColLabel}>MINIMUM DUE</Text>
              <Text style={styles.debtColValue}>€125.00</Text>
            </View>
          </View>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
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
    marginBottom: 20,
    paddingTop: 4,
  },
  screenTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#191C1F',
    letterSpacing: -0.5,
  },
  screenSubtitle: {
    fontSize: 12,
    color: '#72777A',
    marginTop: 1,
  },
  monthPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F4F5F7',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  monthPillText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#555A5E',
  },
  heroCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 24,
    padding: 20,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  heroTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  heroLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#72777A',
    letterSpacing: 0.5,
  },
  trendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#E8F8EE',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  trendText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#00C853',
  },
  heroAmount: {
    fontSize: 34,
    fontWeight: '800',
    color: '#00C853',
    letterSpacing: -0.8,
    marginBottom: 4,
  },
  heroDesc: {
    fontSize: 13,
    color: '#72777A',
    lineHeight: 18,
  },
  sectionHeader: {
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
  actionLink: {
    fontSize: 13,
    fontWeight: '600',
    color: '#0075EB',
  },
  vaultCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  vaultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  vaultLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  vaultIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  vaultMeta: {
    gap: 2,
  },
  vaultTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#191C1F',
  },
  vaultDate: {
    fontSize: 12,
    color: '#72777A',
  },
  vaultProgressBadge: {
    backgroundColor: '#F4F5F7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  vaultPercentText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#191C1F',
  },
  vaultAmountsRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 6,
    marginBottom: 8,
  },
  vaultCurrent: {
    fontSize: 16,
    fontWeight: '700',
    color: '#191C1F',
  },
  vaultTarget: {
    fontSize: 13,
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
  avalancheBadge: {
    backgroundColor: '#FFF4E5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  avalancheText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#B25E00',
  },
  debtCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  debtHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  debtLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  debtIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFF0F3',
    alignItems: 'center',
    justifyContent: 'center',
  },
  debtTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#191C1F',
  },
  debtApr: {
    fontSize: 12,
    color: '#FF3366',
    fontWeight: '600',
  },
  payBtn: {
    backgroundColor: '#F4F5F7',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  payBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#191C1F',
  },
  debtDetails: {
    flexDirection: 'row',
    backgroundColor: '#F8F9FA',
    borderRadius: 14,
    padding: 12,
  },
  debtCol: {
    flex: 1,
    alignItems: 'center',
  },
  debtColLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#72777A',
    marginBottom: 4,
  },
  debtColValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#191C1F',
  },
  debtDivider: {
    width: 1,
    backgroundColor: '#EBECEF',
  },
});
