import React from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import { colors } from '../theme/colors';

interface ApplePayGuideModalProps {
  visible: boolean;
  onClose: () => void;
}

export const ApplePayGuideModal: React.FC<ApplePayGuideModalProps> = ({ visible, onClose }) => {
  return (
    <Modal visible={visible} animationType="slide" transparent={true} onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.sheetContainer}>
          {/* Handle */}
          <View style={styles.handle} />

          {/* Header */}
          <View style={styles.header}>
            <View style={styles.headerLeft}>
              <View style={styles.iconCircle}>
                <Ionicons name="card" size={22} color="#0075EB" />
              </View>
              <View>
                <Text style={styles.title}>Apple Pay NFC Setup</Text>
                <Text style={styles.subtitle}>Automate instant tracking on iPhone</Text>
              </View>
            </View>
            <TouchableOpacity style={styles.closeBtn} onPress={onClose}>
              <Ionicons name="close" size={20} color={colors.textSecondary} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.scrollContent} showsVerticalScrollIndicator={false}>
            {/* Step 1 */}
            <View style={styles.stepCard}>
              <View style={styles.stepNumberBadge}>
                <Text style={styles.stepNumberText}>1</Text>
              </View>
              <View style={styles.stepTextContainer}>
                <Text style={styles.stepTitle}>Open «Shortcuts» (Команды)</Text>
                <Text style={styles.stepDesc}>Open the standard Apple Shortcuts app on your iPhone and go to the "Automation" (Автоматизация) tab at the bottom.</Text>
              </View>
            </View>

            {/* Step 2 */}
            <View style={styles.stepCard}>
              <View style={styles.stepNumberBadge}>
                <Text style={styles.stepNumberText}>2</Text>
              </View>
              <View style={styles.stepTextContainer}>
                <Text style={styles.stepTitle}>Create Apple Pay Trigger</Text>
                <Text style={styles.stepDesc}>Tap (+) ➔ Select "Transaction" (Оплата картой) ➔ Choose any card / Apple Pay ➔ Select "Run Immediately" (Запуск сразу без подтверждения).</Text>
              </View>
            </View>

            {/* Step 3 */}
            <View style={styles.stepCard}>
              <View style={styles.stepNumberBadge}>
                <Text style={styles.stepNumberText}>3</Text>
              </View>
              <View style={styles.stepTextContainer}>
                <Text style={styles.stepTitle}>Add Webhook Action</Text>
                <Text style={styles.stepDesc}>Add action "Get Contents of URL" (Получить содержимое URL) with POST method:</Text>
                <View style={styles.codeBlock}>
                  <Text style={styles.codeText}>http://10.95.147.37:8000/api/expenses/ingest</Text>
                </View>
              </View>
            </View>

            {/* Security note */}
            <View style={styles.securityNote}>
              <Ionicons name="shield-checkmark" size={18} color="#00C853" />
              <Text style={styles.securityText}>
                100% Secure: Shortcuts only transmits merchant name and amount. No card numbers or banking passwords can ever be accessed.
              </Text>
            </View>

            <TouchableOpacity style={styles.doneButton} onPress={onClose} activeOpacity={0.8}>
              <Text style={styles.doneButtonText}>Got it, ready to track</Text>
            </TouchableOpacity>

            <View style={{ height: 24 }} />
          </ScrollView>
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
  sheetContainer: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    maxHeight: '85%',
    paddingHorizontal: 20,
    paddingTop: 12,
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
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#E5F2FF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#191C1F',
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 13,
    color: '#72777A',
    marginTop: 2,
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F4F5F7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollContent: {
    paddingBottom: 20,
  },
  stepCard: {
    flexDirection: 'row',
    gap: 14,
    backgroundColor: '#F8F9FA',
    borderRadius: 18,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  stepNumberBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#191C1F',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumberText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  stepTextContainer: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#191C1F',
    marginBottom: 4,
  },
  stepDesc: {
    fontSize: 13,
    color: '#555A5E',
    lineHeight: 18,
  },
  codeBlock: {
    backgroundColor: '#EDEEEF',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginTop: 8,
  },
  codeText: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 11,
    color: '#0058BC',
    fontWeight: '600',
  },
  securityNote: {
    flexDirection: 'row',
    gap: 10,
    backgroundColor: '#E8F8EE',
    borderRadius: 14,
    padding: 14,
    alignItems: 'center',
    marginVertical: 14,
  },
  securityText: {
    flex: 1,
    fontSize: 12,
    color: '#007A33',
    lineHeight: 16,
    fontWeight: '500',
  },
  doneButton: {
    backgroundColor: '#191C1F',
    borderRadius: 16,
    paddingVertical: 15,
    alignItems: 'center',
    marginTop: 6,
  },
  doneButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});
