import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, SafeAreaView } from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';

interface DashboardScreenProps {
  onNavigateToChat?: () => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ onNavigateToChat }) => {
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.profileButton}>
            <Text style={styles.profileInitials}>S</Text>
          </TouchableOpacity>
          <View style={styles.monthSelector}>
            <Text style={styles.monthText}>August 2026</Text>
            <Ionicons name="chevron-down" size={16} color="#000" style={styles.chevron} />
          </View>
          <TouchableOpacity style={styles.chatButton} onPress={onNavigateToChat}>
            <Ionicons name="chatbubbles-outline" size={24} color="#000" />
          </TouchableOpacity>
        </View>

        <Text style={styles.screenTitle}>Analytics & Vaults</Text>

        {/* Net Surplus Hero */}
        <View style={styles.heroCard}>
          <Text style={styles.heroSubtitle}>Net savings surplus this month</Text>
          <View style={styles.heroAmountContainer}>
            <Text style={styles.heroAmount}>+€620.00</Text>
            <View style={styles.trendingPill}>
              <Feather name="trending-up" size={14} color="#059669" />
            </View>
          </View>
        </View>

        {/* Savings Vaults Section */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Savings Vaults</Text>
          <TouchableOpacity style={styles.newVaultButton}>
            <Text style={styles.newVaultText}>+ New Vault</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.vaultsContainer}>
          {/* Vault 1 */}
          <View style={styles.vaultCard}>
            <View style={styles.vaultHeader}>
              <View style={styles.vaultIconContainerGreen}>
                <MaterialCommunityIcons name="shield-star-outline" size={24} color="#059669" />
              </View>
              <View style={styles.vaultInfo}>
                <Text style={styles.vaultName}>Emergency Fund</Text>
                <Text style={styles.vaultTarget}>Target: Dec 2026</Text>
              </View>
            </View>
            <Text style={styles.vaultAmount}>€2,800 <Text style={styles.vaultTotal}>of €6,000</Text></Text>
            <View style={styles.progressBarBackground}>
              <View style={[styles.progressBarFill, { width: '46.7%' }]} />
            </View>
          </View>

          {/* Vault 2 */}
          <View style={styles.vaultCard}>
            <View style={styles.vaultHeader}>
              <View style={styles.vaultIconContainerBlue}>
                <Ionicons name="airplane-outline" size={24} color="#2563EB" />
              </View>
              <View style={styles.vaultInfo}>
                <Text style={styles.vaultName}>Trip to Japan</Text>
                <Text style={styles.vaultTarget}>Target: Oct 2026</Text>
              </View>
            </View>
            <Text style={styles.vaultAmount}>€950 <Text style={styles.vaultTotal}>of €3,000</Text></Text>
            <View style={styles.progressBarBackground}>
              <View style={[styles.progressBarFill, { width: '31.7%', backgroundColor: '#2563EB' }]} />
            </View>
          </View>
        </View>

        {/* Debt Payoff Section */}
        <View style={styles.sectionHeader}>
          <View style={styles.debtHeaderTitleRow}>
            <Text style={styles.sectionTitle}>Debt Payoff</Text>
            <View style={styles.strategyBadge}>
              <Text style={styles.strategyBadgeText}>Avalanche</Text>
            </View>
          </View>
        </View>

        <View style={styles.creditCardCard}>
          <View style={styles.ccTopRow}>
            <View style={styles.ccIconContainer}>
              <MaterialCommunityIcons name="credit-card-outline" size={28} color="#1F2937" />
            </View>
            <View style={styles.ccInfo}>
              <Text style={styles.ccName}>Credit Card · 21.5% APR</Text>
              <Text style={styles.ccBalance}>Balance: €4,250.00</Text>
            </View>
          </View>
          <View style={styles.ccBottomRow}>
            <View style={styles.ccDueInfo}>
              <Text style={styles.ccMinDueLabel}>Min Due</Text>
              <Text style={styles.ccMinDueAmount}>€125.00</Text>
            </View>
            <TouchableOpacity style={styles.payEarlyButton}>
              <Text style={styles.payEarlyText}>Pay early</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  container: {
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  profileButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileInitials: {
    fontSize: 14,
    fontWeight: '700',
    color: '#374151',
  },
  monthSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  monthText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginRight: 4,
  },
  chevron: {
    marginTop: 2,
  },
  chatButton: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  screenTitle: {
    fontSize: 32,
    fontWeight: '800',
    color: '#111827',
    marginBottom: 24,
    letterSpacing: -0.5,
  },
  heroCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 24,
    padding: 24,
    marginBottom: 32,
  },
  heroSubtitle: {
    fontSize: 15,
    fontWeight: '500',
    color: '#6B7280',
    marginBottom: 8,
  },
  heroAmountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  heroAmount: {
    fontSize: 40,
    fontWeight: '800',
    color: '#059669',
    letterSpacing: -1,
  },
  trendingPill: {
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginLeft: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  newVaultButton: {
    backgroundColor: '#EFF6FF',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
  },
  newVaultText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2563EB',
  },
  vaultsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 32,
  },
  vaultCard: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F3F4F6',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.03,
    shadowRadius: 8,
    elevation: 2,
  },
  vaultHeader: {
    marginBottom: 16,
  },
  vaultIconContainerGreen: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#D1FAE5',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  vaultIconContainerBlue: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#DBEAFE',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  vaultInfo: {},
  vaultName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  vaultTarget: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  vaultAmount: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  vaultTotal: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  progressBarBackground: {
    height: 6,
    backgroundColor: '#F3F4F6',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#059669',
    borderRadius: 3,
  },
  debtHeaderTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  strategyBadge: {
    backgroundColor: '#FEF2F2',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 12,
    marginLeft: 12,
  },
  strategyBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#DC2626',
    textTransform: 'uppercase',
  },
  creditCardCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 12,
    elevation: 3,
  },
  ccTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  ccIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  ccInfo: {
    flex: 1,
  },
  ccName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  ccBalance: {
    fontSize: 15,
    fontWeight: '500',
    color: '#4B5563',
  },
  ccBottomRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    paddingTop: 16,
  },
  ccDueInfo: {},
  ccMinDueLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: '#6B7280',
    marginBottom: 4,
  },
  ccMinDueAmount: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  payEarlyButton: {
    backgroundColor: '#111827',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 20,
  },
  payEarlyText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
