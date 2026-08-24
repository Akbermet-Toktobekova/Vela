import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  ScrollView, 
  SafeAreaView, 
  Modal, 
  TextInput, 
  Platform 
} from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';

export const ExpensesScreen: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false);
  const [amount, setAmount] = useState('');
  const [merchant, setMerchant] = useState('');

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
        {/* 1. Top Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>SZ</Text>
              <View style={styles.activeDot} />
            </View>
          </View>
          <View style={styles.headerMiddle}>
            <Text style={styles.logoText}>Vela</Text>
            <MaterialCommunityIcons name="check-decagram" size={16} color="#007AFF" style={{ marginLeft: 4 }} />
          </View>
          <View style={styles.headerRight}>
            <TouchableOpacity style={styles.iconButton}>
              <Ionicons name="search" size={20} color="#000" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.iconButton}>
              <Ionicons name="card-outline" size={20} color="#000" />
            </TouchableOpacity>
          </View>
        </View>

        {/* 2. VIP Love Banner */}
        <TouchableOpacity style={styles.vipBanner}>
          <View style={styles.vipBannerLeft}>
            <View style={styles.pinkCircle}>
              <Ionicons name="heart" size={12} color="#FF2D55" />
            </View>
            <Text style={styles.vipBannerText}>VIP Member · Солнышко, я люблю тебя</Text>
          </View>
          <Ionicons name="chevron-forward" size={16} color="#8E8E93" />
        </TouchableOpacity>

        {/* 3. Big Currency Balance */}
        <View style={styles.balanceContainer}>
          <Text style={styles.balanceSubtitle}>Total balance</Text>
          <Text style={styles.balanceAmount}>€1,450.75</Text>
          <TouchableOpacity style={styles.currencyPill}>
            <Text style={styles.currencyPillText}>EUR · European Union</Text>
            <Ionicons name="chevron-down" size={14} color="#8E8E93" style={{ marginLeft: 4 }} />
          </TouchableOpacity>
        </View>

        {/* 4. Action Buttons */}
        <View style={styles.actionButtonsRow}>
          <View style={styles.actionItem}>
            <TouchableOpacity style={styles.actionCircleDark} onPress={() => setModalVisible(true)} activeOpacity={0.8}>
              <Ionicons name="add" size={24} color="#FFF" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>Add money</Text>
          </View>
          <View style={styles.actionItem}>
            <TouchableOpacity style={styles.actionCircleLight} activeOpacity={0.8}>
              <Feather name="repeat" size={20} color="#000" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>Transfer</Text>
          </View>
          <View style={styles.actionItem}>
            <TouchableOpacity style={styles.actionCircleLight} activeOpacity={0.8}>
              <Ionicons name="pie-chart-outline" size={20} color="#000" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>Analytics</Text>
          </View>
          <View style={styles.actionItem}>
            <TouchableOpacity style={styles.actionCircleLight} activeOpacity={0.8}>
              <Ionicons name="ellipsis-horizontal" size={20} color="#000" />
            </TouchableOpacity>
            <Text style={styles.actionLabel}>More</Text>
          </View>
        </View>

        {/* 5. Budget Pockets */}
        <View style={styles.pocketsCard}>
          <View style={styles.pocketsHeader}>
            <Text style={styles.pocketsTitle}>Budget Pockets</Text>
            <Text style={styles.pocketsLimit}>€2,800 limit</Text>
          </View>
          
          <View style={styles.pocketRow}>
            <View style={styles.pocketInfo}>
              <View style={styles.pocketDotGroup}>
                <View style={[styles.pocketDot, { backgroundColor: '#34C759' }]} />
                <Text style={styles.pocketLabel}>Needs (50%)</Text>
              </View>
              <Text style={styles.pocketAmounts}>€754 / €1,400</Text>
            </View>
            <View style={styles.progressBarBg}>
              <View style={[styles.progressBarFill, { width: '54%', backgroundColor: '#34C759' }]} />
            </View>
          </View>

          <View style={styles.pocketRow}>
            <View style={styles.pocketInfo}>
              <View style={styles.pocketDotGroup}>
                <View style={[styles.pocketDot, { backgroundColor: '#AF52DE' }]} />
                <Text style={styles.pocketLabel}>Wants (30%)</Text>
              </View>
              <Text style={styles.pocketAmounts}>€410 / €840</Text>
            </View>
            <View style={styles.progressBarBg}>
              <View style={[styles.progressBarFill, { width: '49%', backgroundColor: '#AF52DE' }]} />
            </View>
          </View>

          <View style={styles.pocketRow}>
            <View style={styles.pocketInfo}>
              <View style={styles.pocketDotGroup}>
                <View style={[styles.pocketDot, { backgroundColor: '#007AFF' }]} />
                <Text style={styles.pocketLabel}>Savings (20%)</Text>
              </View>
              <Text style={styles.pocketAmounts}>€286 / €560</Text>
            </View>
            <View style={styles.progressBarBg}>
              <View style={[styles.progressBarFill, { width: '51%', backgroundColor: '#007AFF' }]} />
            </View>
          </View>
        </View>

        {/* 6. Transactions */}
        <View style={styles.transactionsSection}>
          <View style={styles.transactionsHeader}>
            <Text style={styles.transactionsTitle}>Transactions</Text>
            <TouchableOpacity>
              <Text style={styles.seeAllText}>See all</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.dateHeader}>Today</Text>
          
          <View style={styles.transactionItem}>
            <View style={[styles.txIconCircle, { backgroundColor: '#E3F2E1' }]}>
              <Ionicons name="cart-outline" size={20} color="#34C759" />
            </View>
            <View style={styles.txDetails}>
              <Text style={styles.txName}>SPAR Supermarket</Text>
              <Text style={styles.txSubtitle}>14:32 · Groceries · Apple Pay</Text>
            </View>
            <Text style={styles.txAmountNegative}>-€26.40</Text>
          </View>

          <View style={styles.transactionItem}>
            <View style={[styles.txIconCircle, { backgroundColor: '#FFF0D4' }]}>
              <Ionicons name="cafe-outline" size={20} color="#FF9500" />
            </View>
            <View style={styles.txDetails}>
              <Text style={styles.txName}>Starbucks Coffee</Text>
              <Text style={styles.txSubtitle}>09:15 · Cafe · Apple Pay</Text>
            </View>
            <Text style={styles.txAmountNegative}>-€4.80</Text>
          </View>

          <Text style={styles.dateHeader}>Yesterday</Text>

          <View style={styles.transactionItem}>
            <View style={[styles.txIconCircle, { backgroundColor: '#F0E5FC' }]}>
              <Ionicons name="cube-outline" size={20} color="#AF52DE" />
            </View>
            <View style={styles.txDetails}>
              <Text style={styles.txName}>Amazon Prime</Text>
              <Text style={styles.txSubtitle}>18:40 · Shopping · Online</Text>
            </View>
            <Text style={styles.txAmountNegative}>-€32.50</Text>
          </View>

          <View style={styles.transactionItem}>
            <View style={[styles.txIconCircle, { backgroundColor: '#E3F2E1' }]}>
              <Ionicons name="arrow-down" size={20} color="#34C759" />
            </View>
            <View style={styles.txDetails}>
              <Text style={styles.txName}>Salary / Transfer</Text>
              <Text style={styles.txSubtitle}>10:00 · P2P Transfer</Text>
            </View>
            <Text style={styles.txAmountPositive}>+€620.00</Text>
          </View>
        </View>
        <View style={{ height: 40 }} />
      </ScrollView>

      {/* 7. Add Expense Modal */}
      <Modal visible={modalVisible} animationType="slide" transparent={true}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add Expense</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)} style={styles.closeButton}>
                <Ionicons name="close" size={24} color="#000" />
              </TouchableOpacity>
            </View>
            
            <TextInput 
              style={styles.input} 
              placeholder="Merchant Name" 
              value={merchant}
              onChangeText={setMerchant}
              placeholderTextColor="#8E8E93"
            />
            <TextInput 
              style={styles.input} 
              placeholder="Amount (€)" 
              keyboardType="decimal-pad"
              value={amount}
              onChangeText={setAmount}
              placeholderTextColor="#8E8E93"
            />

            <Text style={styles.categoryLabel}>Category</Text>
            <View style={styles.categoryRow}>
              <TouchableOpacity style={styles.categoryPill}>
                <Text style={styles.categoryPillText}>Needs</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.categoryPillSelected}>
                <Text style={styles.categoryPillTextSelected}>Wants</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.categoryPill}>
                <Text style={styles.categoryPillText}>Savings</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.addButton} onPress={() => setModalVisible(false)}>
              <Text style={styles.addButtonText}>Add Expense</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  headerLeft: {
    flex: 1,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  avatarText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
  },
  activeDot: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#34C759',
    borderWidth: 2,
    borderColor: '#FFF',
  },
  headerMiddle: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#000',
  },
  headerRight: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  iconButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  vipBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F8F8F8',
    borderRadius: 24,
    paddingVertical: 10,
    paddingHorizontal: 16,
    marginBottom: 32,
  },
  vipBannerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  pinkCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#FFE6EB',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  vipBannerText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#000',
  },
  balanceContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  balanceSubtitle: {
    fontSize: 15,
    color: '#8E8E93',
    fontWeight: '500',
    marginBottom: 8,
  },
  balanceAmount: {
    fontSize: 38,
    fontWeight: '800',
    color: '#000',
    marginBottom: 16,
  },
  currencyPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
  },
  currencyPillText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#000',
  },
  actionButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 40,
    paddingHorizontal: 10,
  },
  actionItem: {
    alignItems: 'center',
  },
  actionCircleDark: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#000',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  actionCircleLight: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  actionLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: '#000',
  },
  pocketsCard: {
    backgroundColor: '#FFF',
    borderRadius: 24,
    padding: 20,
    marginBottom: 32,
    borderWidth: 1,
    borderColor: '#F2F2F7',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
  },
  pocketsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginBottom: 20,
  },
  pocketsTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#000',
  },
  pocketsLimit: {
    fontSize: 13,
    color: '#8E8E93',
    fontWeight: '500',
  },
  pocketRow: {
    marginBottom: 16,
  },
  pocketInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  pocketDotGroup: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  pocketDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  pocketLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
  },
  pocketAmounts: {
    fontSize: 14,
    fontWeight: '500',
    color: '#8E8E93',
  },
  progressBarBg: {
    height: 6,
    backgroundColor: '#F2F2F7',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  transactionsSection: {
    marginBottom: 20,
  },
  transactionsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  transactionsTitle: {
    fontSize: 19,
    fontWeight: '700',
    color: '#000',
  },
  seeAllText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#007AFF',
  },
  dateHeader: {
    fontSize: 13,
    fontWeight: '600',
    color: '#8E8E93',
    marginBottom: 12,
    marginTop: 8,
  },
  transactionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  txIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  txDetails: {
    flex: 1,
  },
  txName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 2,
  },
  txSubtitle: {
    fontSize: 13,
    color: '#8E8E93',
    fontWeight: '500',
  },
  txAmountNegative: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
  },
  txAmountPositive: {
    fontSize: 16,
    fontWeight: '600',
    color: '#34C759',
  },
  modalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    minHeight: 400,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
  },
  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  input: {
    backgroundColor: '#F8F8F8',
    borderRadius: 16,
    padding: 16,
    fontSize: 16,
    marginBottom: 16,
    color: '#000',
  },
  categoryLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#000',
    marginBottom: 12,
    marginTop: 8,
  },
  categoryRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 32,
  },
  categoryPill: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
  },
  categoryPillSelected: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 16,
    backgroundColor: '#000',
    alignItems: 'center',
  },
  categoryPillText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
  },
  categoryPillTextSelected: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFF',
  },
  addButton: {
    backgroundColor: '#000',
    borderRadius: 24,
    paddingVertical: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 'auto',
  },
  addButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  }
});
