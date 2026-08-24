import React, { useState } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, TextInput, Alert, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';

interface OnboardingModalProps {
  visible: boolean;
  onComplete: (name: string, monthlyLimit: number, currency: string) => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({ visible, onComplete }) => {
  const [name, setName] = useState('');
  const [limit, setLimit] = useState('2000');
  const [currency, setCurrency] = useState('EUR');

  const handleFinish = () => {
    if (!name.trim()) {
      Alert.alert('Please enter your name', 'We need your name to personalize your finance twin.');
      return;
    }
    const numLimit = parseFloat(limit) || 2000;
    onComplete(name.trim(), numLimit, currency);
  };

  return (
    <Modal visible={visible} animationType="fade" transparent={true}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.logoIcon}>
            <Ionicons name="sparkles" size={28} color="#0075EB" />
          </View>

          <Text style={styles.welcomeTitle}>Welcome to Vela</Text>
          <Text style={styles.welcomeSubtitle}>Your intelligent, automated personal finance companion.</Text>

          {/* Name input */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>WHAT IS YOUR NAME?</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. Sanatbek"
              placeholderTextColor="#9DA2A6"
              value={name}
              onChangeText={setName}
              autoFocus
            />
          </View>

          {/* Monthly Budget */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>MONTHLY TARGET BUDGET (€)</Text>
            <TextInput
              style={styles.input}
              placeholder="2000"
              placeholderTextColor="#9DA2A6"
              value={limit}
              onChangeText={setLimit}
              keyboardType="numeric"
            />
          </View>

          {/* Currency selection */}
          <View style={styles.currencyRow}>
            {['EUR', 'USD', 'HUF', 'GBP'].map((curr) => {
              const isSelected = currency === curr;
              return (
                <TouchableOpacity
                  key={curr}
                  style={[styles.currPill, isSelected && styles.currPillActive]}
                  onPress={() => setCurrency(curr)}
                >
                  <Text style={[styles.currText, isSelected && styles.currTextActive]}>{curr}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <TouchableOpacity style={styles.startBtn} onPress={handleFinish} activeOpacity={0.8}>
            <Text style={styles.startBtnText}>Start with Fresh Balance</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  card: {
    width: '100%',
    maxWidth: 380,
    backgroundColor: '#FFFFFF',
    borderRadius: 28,
    padding: 24,
    alignItems: 'center',
  },
  logoIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#E5F2FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#191C1F',
    letterSpacing: -0.5,
  },
  welcomeSubtitle: {
    fontSize: 14,
    color: '#72777A',
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 24,
  },
  inputGroup: {
    width: '100%',
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#72777A',
    marginBottom: 6,
    letterSpacing: 0.5,
  },
  input: {
    width: '100%',
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
  currencyRow: {
    flexDirection: 'row',
    gap: 8,
    width: '100%',
    marginBottom: 24,
  },
  currPill: {
    flex: 1,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#F4F5F7',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  currPillActive: {
    backgroundColor: '#191C1F',
    borderColor: '#191C1F',
  },
  currText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#72777A',
  },
  currTextActive: {
    color: '#FFFFFF',
  },
  startBtn: {
    width: '100%',
    backgroundColor: '#0075EB',
    borderRadius: 16,
    paddingVertical: 15,
    alignItems: 'center',
  },
  startBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});
