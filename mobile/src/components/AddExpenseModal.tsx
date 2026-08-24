import React, { useState } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, TextInput, Alert, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';

interface AddExpenseModalProps {
  visible: boolean;
  onClose: () => void;
  onAdd: (merchant: string, amount: number, category: 'needs' | 'wants' | 'savings') => void;
}

export const AddExpenseModal: React.FC<AddExpenseModalProps> = ({ visible, onClose, onAdd }) => {
  const [merchant, setMerchant] = useState('');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState<'needs' | 'wants' | 'savings'>('needs');

  const handleSave = () => {
    const numAmount = parseFloat(amount.replace(',', '.'));
    if (!merchant.trim() || isNaN(numAmount) || numAmount <= 0) {
      Alert.alert('Invalid Entry', 'Please enter a valid merchant name and amount.');
      return;
    }

    onAdd(merchant.trim(), numAmount, category);
    setMerchant('');
    setAmount('');
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={true} onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <View style={styles.handle} />

          <View style={styles.header}>
            <Text style={styles.title}>Add Expense</Text>
            <TouchableOpacity style={styles.closeBtn} onPress={onClose}>
              <Ionicons name="close" size={20} color="#72777A" />
            </TouchableOpacity>
          </View>

          {/* Amount input hero */}
          <View style={styles.amountBox}>
            <Text style={styles.currencySymbol}>€</Text>
            <TextInput
              style={styles.amountInput}
              placeholder="0.00"
              placeholderTextColor="#C6C6CD"
              value={amount}
              onChangeText={setAmount}
              keyboardType="decimal-pad"
              autoFocus
            />
          </View>

          {/* Merchant Input */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>MERCHANT / DESCRIPTION</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. SPAR, Starbucks, Zara"
              placeholderTextColor="#9DA2A6"
              value={merchant}
              onChangeText={setMerchant}
            />
          </View>

          {/* Category Selector */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>BUDGET POCKET</Text>
            <View style={styles.catRow}>
              <TouchableOpacity
                style={[styles.catPill, category === 'needs' && styles.catPillNeeds]}
                onPress={() => setCategory('needs')}
              >
                <View style={[styles.dot, { backgroundColor: '#00C853' }]} />
                <Text style={[styles.catText, category === 'needs' && styles.catTextActive]}>Needs (50%)</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.catPill, category === 'wants' && styles.catPillWants]}
                onPress={() => setCategory('wants')}
              >
                <View style={[styles.dot, { backgroundColor: '#7B61FF' }]} />
                <Text style={[styles.catText, category === 'wants' && styles.catTextActive]}>Wants (30%)</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.catPill, category === 'savings' && styles.catPillSavings]}
                onPress={() => setCategory('savings')}
              >
                <View style={[styles.dot, { backgroundColor: '#0075EB' }]} />
                <Text style={[styles.catText, category === 'savings' && styles.catTextActive]}>Savings (20%)</Text>
              </TouchableOpacity>
            </View>
          </View>

          <TouchableOpacity style={styles.saveBtn} onPress={handleSave} activeOpacity={0.8}>
            <Text style={styles.saveBtnText}>Save Expense</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: Platform.OS === 'ios' ? 40 : 24,
  },
  handle: {
    width: 36,
    height: 4,
    backgroundColor: '#E0E2E6',
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#191C1F',
    letterSpacing: -0.4,
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F4F5F7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  amountBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F8F9FA',
    borderRadius: 20,
    paddingVertical: 14,
    paddingHorizontal: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  currencySymbol: {
    fontSize: 32,
    fontWeight: '700',
    color: '#72777A',
    marginRight: 6,
  },
  amountInput: {
    fontSize: 36,
    fontWeight: '800',
    color: '#191C1F',
    minWidth: 120,
  },
  inputGroup: {
    marginBottom: 18,
  },
  inputLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#72777A',
    marginBottom: 8,
    letterSpacing: 0.5,
  },
  input: {
    height: 48,
    backgroundColor: '#F4F5F7',
    borderRadius: 14,
    paddingHorizontal: 14,
    fontSize: 16,
    fontWeight: '600',
    color: '#191C1F',
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  catRow: {
    flexDirection: 'row',
    gap: 8,
  },
  catPill: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    height: 40,
    backgroundColor: '#F4F5F7',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  catPillNeeds: {
    backgroundColor: '#E8F8EE',
    borderColor: '#00C853',
  },
  catPillWants: {
    backgroundColor: '#F5EDFC',
    borderColor: '#7B61FF',
  },
  catPillSavings: {
    backgroundColor: '#E5F2FF',
    borderColor: '#0075EB',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  catText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#555A5E',
  },
  catTextActive: {
    color: '#191C1F',
    fontWeight: '700',
  },
  saveBtn: {
    backgroundColor: '#191C1F',
    borderRadius: 16,
    paddingVertical: 15,
    alignItems: 'center',
    marginTop: 8,
  },
  saveBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});
