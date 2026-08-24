import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  ScrollView,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  TextInput,
  Alert
} from 'react-native';
import { colors } from '../theme/colors';
import { ExpenseSummary, Transaction, TransactionSource } from '../types';
import { api } from '../services/api';

export const ExpensesScreen: React.FC = () => {
  const [summary, setSummary] = useState<ExpenseSummary | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [newMerchant, setNewMerchant] = useState('');
  const [newAmount, setNewAmount] = useState('');
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    // In a real app we'd fetch this
    const fetchSummary = async () => {
      try {
        const data = await api.getExpensesSummary();
        setSummary(data);
      } catch (error) {
        console.error('Failed to fetch summary', error);
      }
    };
    fetchSummary();
  }, []);

  const handleSaveExpense = async () => {
    if (!newMerchant || !newAmount) {
      Alert.alert('Error', 'Please enter merchant and amount.');
      return;
    }
    const amountNum = parseFloat(newAmount);
    if (isNaN(amountNum)) {
      Alert.alert('Error', 'Invalid amount.');
      return;
    }

    try {
      Alert.alert('Success', 'Expense added!');
      setModalVisible(false);
      setNewMerchant('');
      setNewAmount('');
    } catch (e) {
      console.error(e);
      Alert.alert('Error', 'Failed to add expense.');
    }
  };

  const handleQuickLog = (merchant: string, amount: number, emoji: string) => {
      setNewMerchant(merchant);
      setNewAmount(amount.toString());
      setModalVisible(true);
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
        {/* Love pill banner */}
        <View style={styles.loveBanner}>
          <Text style={styles.loveText}>Солнышко, я люблю тебя ❤️</Text>
        </View>

        {/* Live status indicator */}
        <View style={styles.statusContainer}>
          <View style={styles.statusDot} />
          <Text style={styles.statusText}>Live Stream Active</Text>
        </View>

        {/* Hero metric */}
        <View style={styles.heroContainer}>
          <Text style={styles.heroLabel}>SPENT THIS MONTH</Text>
          <Text style={styles.heroAmount}>€1,450.75</Text>
        </View>

        {/* Budget Flow card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Budget Flow</Text>
            <Text style={styles.cardSubtitle}>€2,800 limit</Text>
          </View>
          
          <View style={styles.barContainer}>
            <View style={[styles.barSegment, { flex: 52, backgroundColor: '#53E16F', borderTopLeftRadius: 8, borderBottomLeftRadius: 8 }]} />
            <View style={[styles.barSegment, { flex: 28, backgroundColor: '#FFDAD6' }]} />
            <View style={[styles.barSegment, { flex: 20, backgroundColor: '#0058BC', borderTopRightRadius: 8, borderBottomRightRadius: 8 }]} />
          </View>

          <View style={styles.legendContainer}>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#53E16F' }]} />
              <Text style={styles.legendText}>Needs 52%</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#FFDAD6' }]} />
              <Text style={styles.legendText}>Wants 28%</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#0058BC' }]} />
              <Text style={styles.legendText}>Savings 20%</Text>
            </View>
          </View>
        </View>

        {/* Quick Log section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Quick Log</Text>
            <TouchableOpacity onPress={() => setModalVisible(true)}>
              <Text style={styles.addButton}>Add +</Text>
            </TouchableOpacity>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.quickLogScroll}>
            {[
              { label: 'Coffee', emoji: '☕', amount: 4.80 },
              { label: 'SPAR', emoji: '🛒', amount: 26.40 },
              { label: 'Amazon', emoji: '📦', amount: 32.50 },
              { label: 'P2P', emoji: '💸', amount: 15.00 },
            ].map((item, index) => (
              <TouchableOpacity key={index} style={styles.quickLogPill} onPress={() => handleQuickLog(item.label, item.amount, item.emoji)}>
                <Text style={styles.quickLogEmoji}>{item.emoji}</Text>
                <View>
                  <Text style={styles.quickLogLabel}>{item.label}</Text>
                  <Text style={styles.quickLogAmount}>€{item.amount.toFixed(2)}</Text>
                </View>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Live Feed section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Live Feed</Text>
          <View style={styles.card}>
             {[
               { id: '1', emoji: '☕', name: 'Coffee Roasters', time: '10:42 AM', amount: '4.80', type: 'WANTS' },
               { id: '2', emoji: '🛒', name: 'SPAR Supermarket', time: 'Yesterday', amount: '42.50', type: 'NEEDS' },
             ].map((tx, idx, arr) => (
               <View key={tx.id} style={[styles.transactionRow, idx === arr.length - 1 && { borderBottomWidth: 0 }]}>
                 <View style={styles.transactionIconContainer}>
                   <Text style={styles.transactionEmoji}>{tx.emoji}</Text>
                 </View>
                 <View style={styles.transactionDetails}>
                   <Text style={styles.transactionName}>{tx.name}</Text>
                   <Text style={styles.transactionTime}>{tx.time}</Text>
                 </View>
                 <View style={styles.transactionRight}>
                   <Text style={styles.transactionAmount}>€{tx.amount}</Text>
                   <View style={[styles.badge, tx.type === 'NEEDS' ? styles.badgeNeeds : styles.badgeWants]}>
                     <Text style={[styles.badgeText, tx.type === 'NEEDS' ? styles.badgeTextNeeds : styles.badgeTextWants]}>{tx.type}</Text>
                   </View>
                 </View>
               </View>
             ))}
          </View>
        </View>

      </ScrollView>

      {/* Manual Entry Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add Expense</Text>
            
            <TextInput
              style={styles.input}
              placeholder="Merchant Name"
              placeholderTextColor={colors.textMuted || '#76777D'}
              value={newMerchant}
              onChangeText={setNewMerchant}
            />
            
            <TextInput
              style={styles.input}
              placeholder="Amount (€)"
              placeholderTextColor={colors.textMuted || '#76777D'}
              value={newAmount}
              onChangeText={setNewAmount}
              keyboardType="decimal-pad"
            />
            
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.modalCancel} onPress={() => setModalVisible(false)}>
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalSave} onPress={handleSaveExpense}>
                <Text style={styles.modalSaveText}>Save</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background || '#FFFFFF',
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    padding: 24,
    paddingTop: 12,
    paddingBottom: 40,
  },
  loveBanner: {
    backgroundColor: colors.loveBg || '#0070EB',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 999,
    alignSelf: 'center',
    marginBottom: 24,
  },
  loveText: {
    color: colors.loveAccent || '#FFFFFF',
    fontWeight: '600',
    fontSize: 14,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'center',
    backgroundColor: '#F3F4F6',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 999,
    marginBottom: 24,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#34C759',
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.textSecondary || '#45464C',
  },
  heroContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  heroLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textMuted || '#76777D',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  heroAmount: {
    fontSize: 48,
    fontWeight: '700',
    color: colors.textPrimary || '#191C1D',
  },
  card: {
    backgroundColor: colors.surface || '#F8F9FA',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder || '#C6C6CD',
    padding: 20,
    marginBottom: 24,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.textPrimary || '#191C1D',
  },
  cardSubtitle: {
    fontSize: 15,
    fontWeight: '500',
    color: colors.textMuted || '#76777D',
  },
  barContainer: {
    flexDirection: 'row',
    height: 12,
    marginBottom: 16,
  },
  barSegment: {
    height: '100%',
  },
  legendContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  legendText: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textSecondary || '#45464C',
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.textPrimary || '#191C1D',
  },
  addButton: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.primary || '#0058BC',
  },
  quickLogScroll: {
    marginHorizontal: -24,
    paddingHorizontal: 24,
  },
  quickLogPill: {
    backgroundColor: colors.surface || '#F8F9FA',
    borderWidth: 1,
    borderColor: colors.cardBorder || '#C6C6CD',
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
    minWidth: 120,
  },
  quickLogEmoji: {
    fontSize: 24,
    marginRight: 10,
  },
  quickLogLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary || '#191C1D',
    marginBottom: 2,
  },
  quickLogAmount: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textMuted || '#76777D',
  },
  transactionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.cardBorder || '#C6C6CD',
  },
  transactionIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E8F0FE',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  transactionEmoji: {
    fontSize: 20,
  },
  transactionDetails: {
    flex: 1,
  },
  transactionName: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary || '#191C1D',
    marginBottom: 4,
  },
  transactionTime: {
    fontSize: 13,
    color: colors.textMuted || '#76777D',
  },
  transactionRight: {
    alignItems: 'flex-end',
  },
  transactionAmount: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary || '#191C1D',
    marginBottom: 6,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeNeeds: {
    backgroundColor: '#E6F9EB',
  },
  badgeWants: {
    backgroundColor: '#FFECEB',
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  badgeTextNeeds: {
    color: colors.needsColor || '#1A8934',
  },
  badgeTextWants: {
    color: colors.wantsColor || '#D93226',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '85%',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 8,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.textPrimary || '#191C1D',
    marginBottom: 20,
    textAlign: 'center',
  },
  input: {
    borderWidth: 1,
    borderColor: colors.cardBorder || '#C6C6CD',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
    color: colors.textPrimary || '#191C1D',
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  modalCancel: {
    flex: 1,
    paddingVertical: 12,
    marginRight: 8,
    alignItems: 'center',
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  modalCancelText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textSecondary || '#45464C',
  },
  modalSave: {
    flex: 1,
    paddingVertical: 12,
    marginLeft: 8,
    alignItems: 'center',
    borderRadius: 8,
    backgroundColor: colors.primary || '#0058BC',
  },
  modalSaveText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  }
});
