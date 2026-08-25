import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Modal, 
  TouchableOpacity, 
  TextInput, 
  Alert, 
  Platform, 
  Linking 
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';

interface OnboardingModalProps {
  visible: boolean;
  onComplete: (name: string, monthlyLimit: number, currency: string) => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({ visible, onComplete }) => {
  const [step, setStep] = useState<1 | 2>(1);
  const [name, setName] = useState('');
  const [limit, setLimit] = useState('2000');
  const [currency, setCurrency] = useState('EUR');

  const handleNext = () => {
    if (!name.trim()) {
      Alert.alert('Please enter your name', 'We need your name to personalize your finance twin.');
      return;
    }
    if (Platform.OS === 'android') {
      setStep(2);
    } else {
      finishOnboarding();
    }
  };

  const handleOpenNotificationSettings = () => {
    if (Platform.OS === 'android') {
      // Direct intent to Android Notification Listener Access Settings
      Linking.sendIntent('android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS').catch(() => {
        Linking.openSettings();
      });
    }
  };

  const finishOnboarding = () => {
    const numLimit = parseFloat(limit) || 2000;
    onComplete(name.trim(), numLimit, currency);
  };

  return (
    <Modal visible={visible} animationType="fade" transparent={true}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          {step === 1 ? (
            <>
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

              {/* Currency Selector */}
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>PRIMARY CURRENCY</Text>
                <View style={styles.currencyRow}>
                  {['EUR', 'HUF', 'KGS', 'USD'].map((c) => (
                    <TouchableOpacity
                      key={c}
                      style={[styles.currencyPill, currency === c && styles.currencyPillActive]}
                      onPress={() => setCurrency(c)}
                    >
                      <Text style={[styles.currencyText, currency === c && styles.currencyTextActive]}>{c}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {/* Action Button */}
              <TouchableOpacity style={styles.continueBtn} onPress={handleNext} activeOpacity={0.85}>
                <Text style={styles.continueBtnText}>{Platform.OS === 'android' ? 'Next: Auto-Tracking' : 'Get Started'}</Text>
                <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
              </TouchableOpacity>
            </>
          ) : (
            <>
              <View style={[styles.logoIcon, { backgroundColor: '#E8F8EE' }]}>
                <Ionicons name="notifications-outline" size={28} color="#009A6B" />
              </View>

              <Text style={styles.welcomeTitle}>Enable Auto-Tracking</Text>
              <Text style={styles.welcomeSubtitle}>
                Vela can automatically track every payment from Revolut, OTP, MBank, Optima & cards right from bank notifications.
              </Text>

              <View style={styles.permissionBox}>
                <View style={styles.permissionItem}>
                  <Ionicons name="shield-checkmark" size={20} color="#009A6B" />
                  <Text style={styles.permissionItemText}>100% Offline & Private (processed locally)</Text>
                </View>
                <View style={styles.permissionItem}>
                  <Ionicons name="flash" size={20} color="#0075EB" />
                  <Text style={styles.permissionItemText}>Instant 0-tap 50/30/20 budget logging</Text>
                </View>
              </View>

              {/* Direct Grant Permission Button */}
              <TouchableOpacity 
                style={[styles.continueBtn, { backgroundColor: '#009A6B', marginBottom: 10 }]} 
                onPress={handleOpenNotificationSettings} 
                activeOpacity={0.85}
              >
                <Ionicons name="settings-outline" size={18} color="#FFFFFF" />
                <Text style={styles.continueBtnText}>Grant Notification Access</Text>
              </TouchableOpacity>

              {/* Skip / Finish Button */}
              <TouchableOpacity style={styles.skipBtn} onPress={finishOnboarding} activeOpacity={0.85}>
                <Text style={styles.skipBtnText}>I've Enabled It / Skip for Now</Text>
              </TouchableOpacity>
            </>
          )}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    width: '100%',
    maxWidth: 380,
    padding: 24,
    alignItems: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 10 },
        shadowOpacity: 0.15,
        shadowRadius: 20,
      },
      android: {
        elevation: 8,
      },
    }),
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
    fontSize: 22,
    fontWeight: '800',
    color: '#191C1F',
    marginBottom: 6,
    textAlign: 'center',
  },
  welcomeSubtitle: {
    fontSize: 13,
    color: '#72777A',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 18,
    paddingHorizontal: 8,
  },
  inputGroup: {
    width: '100%',
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#72777A',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#F4F5F7',
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 15,
    color: '#191C1F',
    fontWeight: '600',
    borderWidth: 1,
    borderColor: '#E9EAEF',
  },
  currencyRow: {
    flexDirection: 'row',
    gap: 8,
  },
  currencyPill: {
    flex: 1,
    backgroundColor: '#F4F5F7',
    paddingVertical: 10,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E9EAEF',
  },
  currencyPillActive: {
    backgroundColor: '#191C1F',
    borderColor: '#191C1F',
  },
  currencyText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#72777A',
  },
  currencyTextActive: {
    color: '#FFFFFF',
  },
  permissionBox: {
    width: '100%',
    backgroundColor: '#F4F5F7',
    borderRadius: 16,
    padding: 14,
    gap: 10,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#E9EAEF',
  },
  permissionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  permissionItemText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#191C1F',
    flex: 1,
  },
  continueBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#191C1F',
    width: '100%',
    paddingVertical: 15,
    borderRadius: 16,
    marginTop: 8,
  },
  continueBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  skipBtn: {
    paddingVertical: 10,
    alignItems: 'center',
    width: '100%',
  },
  skipBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#72777A',
  },
});
