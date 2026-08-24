import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity, 
  Modal, 
  TextInput, 
  Platform 
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useUser, VaultGoal } from '../context/UserContext';
import { FloatingAuroraBackground } from '../components/FloatingAuroraBackground';

export const DashboardScreen: React.FC<{ onNavigateToChat?: () => void }> = ({ onNavigateToChat }) => {
  const insets = useSafeAreaInsets();
  const { profile, vaults, totalSpent, savingsSpent } = useUser();

  const [period, setPeriod] = useState<'month' | 'quarter' | 'year'>('month');
  const [newVaultModal, setNewVaultModal] = useState(false);
  const [vaultTitle, setVaultTitle] = useState('');
  const [vaultTarget, setVaultTarget] = useState('');

  const monthlyBudget = profile.monthlyLimit || 2000;
  const netSurplus = Math.max(0, monthlyBudget - totalSpent);

  const handleCreateVault = () => {
    if (!vaultTitle.trim() || !vaultTarget) return;
    const target = parseFloat(vaultTarget);
    if (isNaN(target) || target <= 0) return;

    // Add new vault goal dynamically
    const newVault: VaultGoal = {
      id: Date.now().toString(),
      title: vaultTitle.trim(),
      targetAmount: target,
      currentAmount: 0,
      targetDate: '2027',
      iconName: 'wallet-outline',
      iconColor: '#0075EB',
      iconBg: 'rgba(0, 117, 235, 0.15)',
    };
    vaults.push(newVault);
    setVaultTitle('');
    setVaultTarget('');
    setNewVaultModal(false);
  };

  return (
    <FloatingAuroraBackground theme="cobalt">
      <ScrollView 
        style={styles.container} 
        contentContainerStyle={[styles.contentContainer, { paddingTop: Math.max(insets.top, 14) }]} 
        showsVerticalScrollIndicator={false}
      >
        {/* 1. Header with Period Selector */}
        <View style={styles.header}>
          <View>
            <Text style={styles.headerTitle}>Analytics & Vaults</Text>
            <Text style={styles.headerSubtitle}>Financial Intelligence · Wealth Flow</Text>
          </View>

          {/* Period Filter Capsule */}
          <View style={styles.periodCapsule}>
            <TouchableOpacity 
              style={[styles.periodBtn, period === 'month' && styles.periodBtnActive]}
              onPress={() => setPeriod('month')}
            >
              <Text style={[styles.periodText, period === 'month' && styles.periodTextActive]}>1M</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.periodBtn, period === 'quarter' && styles.periodBtnActive]}
              onPress={() => setPeriod('quarter')}
            >
              <Text style={[styles.periodText, period === 'quarter' && styles.periodTextActive]}>3M</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.periodBtn, period === 'year' && styles.periodBtnActive]}
              onPress={() => setPeriod('year')}
            >
              <Text style={[styles.periodText, period === 'year' && styles.periodTextActive]}>1Y</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 2. Hero Net Surplus Card (Floating Glass Finish) */}
        <View style={styles.heroSection}>
          <Text style={styles.heroLabel}>NET SAVINGS SURPLUS</Text>
          <Text style={styles.heroAmount}>+€{netSurplus.toFixed(2)}</Text>
          <View style={styles.rateBadge}>
            <Ionicons name="trending-up" size={14} color="#00C853" />
            <Text style={styles.rateText}>On Track · €{(totalSpent / (monthlyBudget || 1) * 100).toFixed(0)}% budget consumed</Text>
          </View>
        </View>

        {/* 3. Action Buttons Row */}
        <View style={styles.actionRow}>
          <View style={styles.actionItem}>
            <TouchableOpacity style={styles.actionGlassCircle} onPress={() => setNewVaultModal(true)} activeOpacity={0.75}>
              <Ionicons name="add" size={24} color="#FFFFFF" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>New Vault</Text>
          </View>

          <View style={styles.actionItem}>
            <TouchableOpacity style={styles.actionGlassCircle} onPress={onNavigateToChat} activeOpacity={0.75}>
              <Ionicons name="sparkles" size={20} color="#FFFFFF" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>AI Advice</Text>
          </View>

          <View style={styles.actionItem}>
            <TouchableOpacity style={styles.actionGlassCircle} activeOpacity={0.75}>
              <Ionicons name="pie-chart-outline" size={20} color="#FFFFFF" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>Breakdown</Text>
          </View>

          <View style={styles.actionItem}>
            <TouchableOpacity style={styles.actionGlassCircle} activeOpacity={0.75}>
              <Ionicons name="calendar-outline" size={20} color="#FFFFFF" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>Forecast</Text>
          </View>
        </View>

        {/* 4. Bottom Frosted Sheet for Vaults & Debt */}
        <View style={styles.frostedSheetContainer}>
          {/* Section: Savings Vaults */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Savings Vaults</Text>
            <TouchableOpacity onPress={() => setNewVaultModal(true)}>
              <Text style={styles.actionLink}>+ Create</Text>
            </TouchableOpacity>
          </View>

          {vaults.map((vault) => {
            const progressPercent = Math.min(100, Math.round((vault.currentAmount / vault.targetAmount) * 100)) || 0;
            return (
              <View key={vault.id} style={styles.vaultCard}>
                <View style={styles.vaultHeader}>
                  <View style={styles.vaultLeft}>
                    <View style={[styles.vaultIconCircle, { backgroundColor: vault.iconBg || '#E5F2FF' }]}>
                      <Ionicons name={(vault.iconName as any) || 'shield-checkmark'} size={20} color={vault.iconColor || '#0075EB'} />
                    </View>
                    <View>
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
                  <View style={[styles.progressBarFill, { width: `${Math.max(5, progressPercent)}%`, backgroundColor: vault.iconColor || '#0075EB' }]} />
                </View>
              </View>
            );
          })}

          {/* Section: Debt Strategy */}
          <View style={[styles.sectionHeader, { marginTop: 16 }]}>
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
        </View>
      </ScrollView>

      {/* New Vault Modal */}
      <Modal visible={newVaultModal} animationType="slide" transparent={true} onRequestClose={() => setNewVaultModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>Create Savings Vault</Text>
            <Text style={styles.modalSubtitle}>Set aside money automatically for goals</Text>

            <TextInput
              style={styles.modalInput}
              placeholder="Goal Name (e.g. MacBook Pro, Japan)"
              placeholderTextColor="#9DA2A6"
              value={vaultTitle}
              onChangeText={setVaultTitle}
            />

            <TextInput
              style={styles.modalInput}
              placeholder="Target Amount (€)"
              placeholderTextColor="#9DA2A6"
              value={vaultTarget}
              onChangeText={setVaultTarget}
              keyboardType="numeric"
            />

            <TouchableOpacity style={styles.modalSaveBtn} onPress={handleCreateVault} activeOpacity={0.8}>
              <Text style={styles.modalSaveBtnText}>Save Vault</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.modalCancelBtn} onPress={() => setNewVaultModal(false)}>
              <Text style={styles.modalCancelBtnText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </FloatingAuroraBackground>
  );
};

const styles = StyleSheet.create({
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
  headerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -0.4,
  },
  headerSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  periodCapsule: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 14,
    padding: 3,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  periodBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 11,
  },
  periodBtnActive: {
    backgroundColor: '#FFFFFF',
  },
  periodText: {
    fontSize: 11,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.9)',
  },
  periodTextActive: {
    color: '#123BB5',
  },
  heroSection: {
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  heroLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.85)',
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  heroAmount: {
    fontSize: 48,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -1.2,
    marginBottom: 10,
  },
  rateBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  rateText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
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
    backgroundColor: 'rgba(255,255,255,0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.4)',
  },
  actionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  frostedSheetContainer: {
    backgroundColor: 'rgba(240, 245, 255, 0.96)',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 16,
    paddingTop: 20,
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
    color: '#111417',
    letterSpacing: -0.3,
  },
  actionLink: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0075EB',
  },
  vaultCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 18,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#D8E2F0',
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
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  vaultTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111417',
  },
  vaultDate: {
    fontSize: 12,
    color: '#646B73',
  },
  vaultProgressBadge: {
    backgroundColor: '#F4F6F9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  vaultPercentText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#111417',
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
    color: '#111417',
  },
  vaultTarget: {
    fontSize: 13,
    color: '#646B73',
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
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: '#D8E2F0',
  },
  debtHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
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
    backgroundColor: '#FFF0F4',
    alignItems: 'center',
    justifyContent: 'center',
  },
  debtTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111417',
  },
  debtApr: {
    fontSize: 12,
    color: '#FF3366',
    fontWeight: '600',
  },
  payBtn: {
    backgroundColor: '#111417',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 12,
  },
  payBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  debtDetails: {
    flexDirection: 'row',
    backgroundColor: '#F8F9FB',
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
    color: '#646B73',
    marginBottom: 4,
  },
  debtColValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111417',
  },
  debtDivider: {
    width: 1,
    backgroundColor: '#ECEEF2',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 20,
    paddingTop: 14,
    paddingBottom: Platform.OS === 'ios' ? 40 : 24,
  },
  modalHandle: {
    width: 36,
    height: 4,
    backgroundColor: '#E0E2E6',
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#111417',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 13,
    color: '#646B73',
    marginBottom: 18,
  },
  modalInput: {
    height: 48,
    backgroundColor: '#F4F5F7',
    borderRadius: 14,
    paddingHorizontal: 14,
    fontSize: 15,
    fontWeight: '600',
    color: '#111417',
    borderWidth: 1,
    borderColor: '#ECEEF2',
    marginBottom: 14,
  },
  modalSaveBtn: {
    backgroundColor: '#111417',
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 6,
  },
  modalSaveBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  modalCancelBtn: {
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 4,
  },
  modalCancelBtnText: {
    color: '#646B73',
    fontSize: 14,
    fontWeight: '600',
  },
});
