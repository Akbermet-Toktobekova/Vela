import React, { useState, useEffect, useRef } from 'react';
import { 
  StyleSheet, 
  View, 
  Text, 
  ScrollView, 
  TouchableOpacity, 
  Platform, 
  Animated, 
  Linking, 
  Alert, 
  TextInput, 
  Modal, 
  StatusBar 
} from 'react-native';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';

export interface NFCTransaction {
  id: string;
  merchant: string;
  amount: number;
  currency: string;
  category: 'needs' | 'wants' | 'savings';
  source: 'nfc_auto' | 'notification' | 'manual';
  timeFormatted: string;
  timestamp: string;
  iconName: string;
  iconBg: string;
}

export function parseNotification(text: string): { merchant: string; amount: number; category: 'needs' | 'wants' | 'savings' } | null {
  if (!text) return null;
  const numMatch = text.match(/(?:€|\$|Ft|EUR|HUF|KGS)?\s*(\d+[.,]?\d*)\s*(?:€|\$|Ft|EUR|HUF|KGS|евро|сом)?/i);
  let amount = 14.50;
  if (numMatch && numMatch[1]) {
    amount = parseFloat(numMatch[1].replace(',', '.'));
  }

  let merchant = 'SPAR Supermarket';
  if (/starbucks/i.test(text)) merchant = 'Starbucks Coffee';
  else if (/lidl/i.test(text)) merchant = 'Lidl Store';
  else if (/aldi/i.test(text)) merchant = 'Aldi Market';
  else if (/uber|bolt/i.test(text)) merchant = 'Bolt Ride';
  else if (/mcdonald/i.test(text)) merchant = "McDonald's";

  let category: 'needs' | 'wants' | 'savings' = 'needs';
  if (/starbucks|cafe|coffee|mcdonald/i.test(merchant)) category = 'wants';

  return { merchant, amount, category };
}

function MainScreen() {
  const insets = useSafeAreaInsets();
  const [transactions, setTransactions] = useState<NFCTransaction[]>([]);
  const [hasPermission, setHasPermission] = useState<boolean>(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [customMerchant, setCustomMerchant] = useState('');
  const [customAmount, setCustomAmount] = useState('');

  // Floating background animation
  const anim1 = useRef(new Animated.Value(0)).current;
  const anim2 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    loadTransactions();

    Animated.loop(
      Animated.sequence([
        Animated.timing(anim1, { toValue: 1, duration: 6000, useNativeDriver: true }),
        Animated.timing(anim1, { toValue: 0, duration: 6000, useNativeDriver: true }),
      ])
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(anim2, { toValue: 1, duration: 8000, useNativeDriver: true }),
        Animated.timing(anim2, { toValue: 0, duration: 8000, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const loadTransactions = async () => {
    try {
      const stored = await AsyncStorage.getItem('@vela_nfc_logs');
      if (stored) {
        setTransactions(JSON.parse(stored));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const saveTransactions = async (newTxList: NFCTransaction[]) => {
    setTransactions(newTxList);
    await AsyncStorage.setItem('@vela_nfc_logs', JSON.stringify(newTxList));
  };

  const handleOpenSettings = () => {
    if (Platform.OS === 'android') {
      Linking.sendIntent('android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS').catch(() => {
        Linking.openSettings();
      });
      setHasPermission(true);
    } else {
      Alert.alert('Apple iOS', 'On iPhone, NFC auto-tracking connects via Apple Shortcuts automation.');
    }
  };

  const addLog = (merchant: string, amount: number, category: 'needs' | 'wants' | 'savings', source: 'nfc_auto' | 'manual' = 'nfc_auto') => {
    const now = new Date();
    const timeFormatted = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let iconName = 'cart';
    let iconBg = '#E8F8EE';
    if (category === 'wants') {
      iconName = 'cafe';
      iconBg = '#F5EDFC';
    }

    const newTx: NFCTransaction = {
      id: Date.now().toString(),
      merchant,
      amount,
      currency: 'EUR',
      category,
      source,
      timeFormatted,
      timestamp: now.toISOString(),
      iconName,
      iconBg,
    };

    const updated = [newTx, ...transactions];
    saveTransactions(updated);
  };

  const simulatePayment = (type: 'spar' | 'starbucks' | 'lidl') => {
    if (type === 'spar') {
      addLog('SPAR Supermarket', 26.40, 'needs', 'nfc_auto');
    } else if (type === 'starbucks') {
      addLog('Starbucks Coffee', 4.80, 'wants', 'nfc_auto');
    } else {
      addLog('Lidl Groceries', 18.90, 'needs', 'nfc_auto');
    }
  };

  const clearLogs = () => {
    saveTransactions([]);
  };

  const totalSpent = transactions.reduce((sum, t) => sum + t.amount, 0);

  const transX1 = anim1.interpolate({ inputRange: [0, 1], outputRange: [-20, 25] });
  const transY1 = anim1.interpolate({ inputRange: [0, 1], outputRange: [-15, 20] });
  const transX2 = anim2.interpolate({ inputRange: [0, 1], outputRange: [20, -25] });

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />

      {/* Floating Mint Aurora */}
      <View style={StyleSheet.absoluteFill}>
        <LinearGradient colors={['#004D34', '#007F55', '#10C888']} style={StyleSheet.absoluteFill} />
        <Animated.View style={[styles.glowOrb, { transform: [{ translateX: transX1 }, { translateY: transY1 }] }]} />
        <Animated.View style={[styles.glowOrbSmall, { transform: [{ translateX: transX2 }] }]} />
      </View>

      <ScrollView 
        style={styles.scroll} 
        contentContainerStyle={[styles.content, { paddingTop: Math.max(insets.top, 16) }]}
        showsVerticalScrollIndicator={false}
      >
        {/* 1. Header */}
        <View style={styles.header}>
          <View style={styles.logoRow}>
            <View style={styles.logoCircle}>
              <Ionicons name="sparkles" size={18} color="#003D26" />
            </View>
            <View>
              <Text style={styles.brandTitle}>Vela NFC Logger</Text>
              <Text style={styles.brandSubtitle}>Android Autonomous Engine</Text>
            </View>
          </View>

          <View style={styles.statusPill}>
            <View style={[styles.statusDot, { backgroundColor: hasPermission ? '#53E16F' : '#FFB74D' }]} />
            <Text style={styles.statusPillText}>{hasPermission ? 'Active' : 'Setup'}</Text>
          </View>
        </View>

        {/* 2. Hero Spend Card */}
        <View style={styles.heroCard}>
          <Text style={styles.heroSub}>TOTAL CAPTURED SPENDING</Text>
          <Text style={styles.heroAmount}>€{totalSpent.toFixed(2)}</Text>
          <View style={styles.badgeRow}>
            <View style={styles.heroBadge}>
              <Ionicons name="radio" size={12} color="#005A3D" />
              <Text style={styles.heroBadgeText}>{transactions.length} NFC Logs Auto-saved</Text>
            </View>
          </View>
        </View>

        {/* 3. Permission Banner (1-Click Android Setup) */}
        {!hasPermission && (
          <TouchableOpacity style={styles.permissionCard} onPress={handleOpenSettings} activeOpacity={0.85}>
            <View style={styles.permIconCircle}>
              <Ionicons name="notifications-outline" size={22} color="#007F55" />
            </View>
            <View style={styles.permTextContainer}>
              <Text style={styles.permTitle}>Включить перехват оплат NFC</Text>
              <Text style={styles.permDesc}>Нажми, чтобы дать доступ к уведомлениям банков в настройках Android</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color="#007F55" />
          </TouchableOpacity>
        )}

        {/* 4. Action Testing Buttons */}
        <View style={styles.testSection}>
          <Text style={styles.sectionHeader}>QUICK NFC TAP SIMULATION</Text>
          <View style={styles.testBtnRow}>
            <TouchableOpacity style={styles.testBtn} onPress={() => simulatePayment('spar')} activeOpacity={0.8}>
              <Text style={styles.testBtnEmoji}>🛒</Text>
              <Text style={styles.testBtnText}>SPAR · €26.40</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.testBtn} onPress={() => simulatePayment('starbucks')} activeOpacity={0.8}>
              <Text style={styles.testBtnEmoji}>☕</Text>
              <Text style={styles.testBtnText}>Starbucks · €4.80</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.testBtn} onPress={() => setModalVisible(true)} activeOpacity={0.8}>
              <Text style={styles.testBtnEmoji}>➕</Text>
              <Text style={styles.testBtnText}>Manual Log</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 5. Live Feed Bottom Sheet */}
        <View style={styles.feedSheet}>
          <View style={styles.feedHeader}>
            <Text style={styles.feedTitle}>Live Transaction Feed</Text>
            {transactions.length > 0 && (
              <TouchableOpacity onPress={clearLogs}>
                <Text style={styles.clearText}>Clear All</Text>
              </TouchableOpacity>
            )}
          </View>

          {transactions.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="receipt-outline" size={32} color="#007F55" style={{ marginBottom: 8 }} />
              <Text style={styles.emptyTitle}>No NFC transactions yet</Text>
              <Text style={styles.emptyDesc}>
                Tap buttons above to simulate, or pay at a store terminal via Google Pay!
              </Text>
            </View>
          ) : (
            <View style={styles.txList}>
              {transactions.map((t) => (
                <View key={t.id} style={styles.txItem}>
                  <View style={styles.txLeft}>
                    <View style={[styles.txIconCircle, { backgroundColor: t.iconBg }]}>
                      <Ionicons name={t.category === 'needs' ? 'cart-outline' : 'cafe-outline'} size={18} color="#003D26" />
                    </View>
                    <View>
                      <Text style={styles.txMerchant}>{t.merchant}</Text>
                      <Text style={styles.txMeta}>
                        {t.timeFormatted} · {t.source === 'nfc_auto' ? 'NFC Auto-Log' : 'Manual'}
                      </Text>
                    </View>
                  </View>
                  <Text style={styles.txAmount}>-€{t.amount.toFixed(2)}</Text>
                </View>
              ))}
            </View>
          )}

          <View style={{ height: 30 }} />
        </View>
      </ScrollView>

      {/* Manual Modal */}
      <Modal visible={modalVisible} animationType="slide" transparent onRequestClose={() => setModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <Text style={styles.modalTitle}>Manual Expense Entry</Text>
            
            <TextInput
              style={styles.modalInput}
              placeholder="Merchant (e.g. SPAR)"
              placeholderTextColor="#9DA2A6"
              value={customMerchant}
              onChangeText={setCustomMerchant}
            />

            <TextInput
              style={styles.modalInput}
              placeholder="Amount (e.g. 15.50)"
              placeholderTextColor="#9DA2A6"
              value={customAmount}
              onChangeText={setCustomAmount}
              keyboardType="decimal-pad"
            />

            <TouchableOpacity 
              style={styles.modalSaveBtn} 
              onPress={() => {
                const amt = parseFloat(customAmount.replace(',', '.'));
                if (customMerchant.trim() && !isNaN(amt) && amt > 0) {
                  addLog(customMerchant.trim(), amt, 'needs', 'manual');
                  setCustomMerchant('');
                  setCustomAmount('');
                  setModalVisible(false);
                }
              }}
            >
              <Text style={styles.modalSaveBtnText}>Save Log</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.modalCancelBtn} onPress={() => setModalVisible(false)}>
              <Text style={styles.modalCancelBtnText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <MainScreen />
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#004D34',
  },
  scroll: {
    flex: 1,
  },
  content: {
    paddingBottom: 24,
  },
  glowOrb: {
    position: 'absolute',
    top: 50,
    right: -40,
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: 'rgba(110, 231, 183, 0.28)',
  },
  glowOrbSmall: {
    position: 'absolute',
    top: 200,
    left: -50,
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: 'rgba(16, 200, 136, 0.25)',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 18,
    marginBottom: 20,
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  logoCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(255, 255, 255, 0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  brandSubtitle: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '500',
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusPillText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  heroCard: {
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  heroSub: {
    fontSize: 12,
    fontWeight: '700',
    color: 'rgba(255, 255, 255, 0.8)',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  heroAmount: {
    fontSize: 46,
    fontWeight: '900',
    color: '#FFFFFF',
    letterSpacing: -1,
    marginBottom: 10,
  },
  badgeRow: {
    flexDirection: 'row',
  },
  heroBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.35)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
  },
  heroBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#003D26',
  },
  permissionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 18,
    gap: 12,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  permIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E8F8EE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  permTextContainer: {
    flex: 1,
  },
  permTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#003D26',
    marginBottom: 2,
  },
  permDesc: {
    fontSize: 11,
    color: '#72777A',
    lineHeight: 15,
  },
  testSection: {
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: '800',
    color: 'rgba(255, 255, 255, 0.85)',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  testBtnRow: {
    flexDirection: 'row',
    gap: 8,
  },
  testBtn: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.32)',
    paddingVertical: 12,
    borderRadius: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.45)',
  },
  testBtnEmoji: {
    fontSize: 18,
    marginBottom: 4,
  },
  testBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  feedSheet: {
    backgroundColor: 'rgba(240, 252, 246, 0.98)',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 16,
    paddingTop: 18,
    minHeight: 350,
  },
  feedHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  feedTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#002E1C',
  },
  clearText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#D32F2F',
  },
  emptyState: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#D4EFE3',
    borderStyle: 'dashed',
    marginTop: 10,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#002E1C',
    marginBottom: 4,
  },
  emptyDesc: {
    fontSize: 12,
    color: '#005A3D',
    textAlign: 'center',
    lineHeight: 16,
  },
  txList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#D4EFE3',
    overflow: 'hidden',
  },
  txItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  txMerchant: {
    fontSize: 14,
    fontWeight: '700',
    color: '#002E1C',
  },
  txMeta: {
    fontSize: 11,
    color: '#005A3D',
    fontWeight: '500',
  },
  txAmount: {
    fontSize: 14,
    fontWeight: '800',
    color: '#D32F2F',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    gap: 12,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#191C1F',
    marginBottom: 8,
  },
  modalInput: {
    backgroundColor: '#F4F5F7',
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 15,
    color: '#191C1F',
    borderWidth: 1,
    borderColor: '#E9EAEF',
  },
  modalSaveBtn: {
    backgroundColor: '#007F55',
    paddingVertical: 14,
    borderRadius: 16,
    alignItems: 'center',
    marginTop: 6,
  },
  modalSaveBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  modalCancelBtn: {
    paddingVertical: 10,
    alignItems: 'center',
  },
  modalCancelBtnText: {
    color: '#72777A',
    fontSize: 14,
    fontWeight: '600',
  },
});
