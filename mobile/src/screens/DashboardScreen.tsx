import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, SafeAreaView } from 'react-native';

// Assuming colors from '../theme/colors' per instructions, but defining fallbacks in stylesheet to ensure it works.
// import { colors } from '../theme/colors';

export interface DashboardScreenProps {
  onNavigateToChat?: () => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ onNavigateToChat }) => {
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        
        {/* Net Surplus Hero */}
        <View style={styles.heroSection}>
          <Text style={styles.heroLabel}>Net Surplus</Text>
          <View style={styles.heroValueContainer}>
            <Text style={styles.heroValue}>+€620.00</Text>
            <Text style={styles.heroTrend}>📈</Text>
          </View>
        </View>

        {/* Savings Goals Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Savings Goals</Text>
            <TouchableOpacity>
              <Text style={styles.linkText}>View All</Text>
            </TouchableOpacity>
          </View>

          {/* Emergency Fund Card */}
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.iconTitleRow}>
                <View style={[styles.iconCircle, { backgroundColor: '#E8F5E9' }]}>
                  <Text style={styles.iconEmoji}>🌱</Text>
                </View>
                <Text style={styles.cardTitle}>Emergency Fund</Text>
              </View>
              <View style={styles.badgeContainer}>
                <Text style={styles.badgeText}>Ends Dec 2026</Text>
              </View>
            </View>
            <View style={styles.progressContainer}>
              <View style={styles.amountsRow}>
                <Text style={styles.amountText}>€2,800</Text>
                <Text style={styles.targetAmountText}>/ €6,000</Text>
              </View>
              <View style={styles.progressBarBackground}>
                <View style={[styles.progressBarFill, { width: '46.7%', backgroundColor: '#53E16F' }]} />
              </View>
            </View>
          </View>

          {/* Trip to Japan Card */}
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.iconTitleRow}>
                <View style={[styles.iconCircle, { backgroundColor: '#E3F2FD' }]}>
                  <Text style={styles.iconEmoji}>✈️</Text>
                </View>
                <Text style={styles.cardTitle}>Trip to Japan</Text>
              </View>
            </View>
            <View style={styles.progressContainer}>
              <View style={styles.amountsRow}>
                <Text style={styles.amountText}>€950</Text>
                <Text style={styles.targetAmountText}>/ €3,000</Text>
              </View>
              <View style={styles.progressBarBackground}>
                <View style={[styles.progressBarFill, { width: '31.7%', backgroundColor: '#0058BC' }]} />
              </View>
            </View>
          </View>
        </View>

        {/* Debt Strategy Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Debt Strategy</Text>
          </View>

          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.iconTitleRow}>
                <View style={[styles.iconCircle, { backgroundColor: '#F3E5F5' }]}>
                  <Text style={styles.iconEmoji}>💳</Text>
                </View>
                <View>
                  <Text style={styles.cardTitle}>Credit Card</Text>
                  <Text style={styles.dangerText}>21.5% APR</Text>
                </View>
              </View>
              <View style={[styles.badgeContainer, { backgroundColor: '#FFF3E0' }]}>
                <Text style={[styles.badgeText, { color: '#E65100' }]}>Avalanche Strategy</Text>
              </View>
            </View>
            
            <View style={styles.debtDetailsContainer}>
              <View style={styles.debtDetailRow}>
                <Text style={styles.debtDetailLabel}>Current Balance:</Text>
                <Text style={styles.debtDetailValue}>€4,250.00</Text>
              </View>
              <View style={styles.debtDetailRow}>
                <Text style={styles.debtDetailLabel}>Minimum Due:</Text>
                <Text style={styles.debtDetailValue}>€125.00</Text>
              </View>
            </View>
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
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 40,
    paddingBottom: 40,
  },
  heroSection: {
    alignItems: 'center',
    marginBottom: 40,
  },
  heroLabel: {
    fontSize: 16,
    color: '#45464C',
    fontWeight: '500',
    marginBottom: 8,
  },
  heroValueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroValue: {
    fontSize: 48,
    fontWeight: '700',
    color: '#53E16F',
    letterSpacing: -1,
  },
  heroTrend: {
    fontSize: 24,
    marginLeft: 8,
  },
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '600',
    color: '#191C1D',
  },
  linkText: {
    fontSize: 16,
    color: '#0058BC',
    fontWeight: '500',
  },
  card: {
    backgroundColor: '#F8F9FA',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#C6C6CD',
    padding: 24,
    marginBottom: 16,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 20,
  },
  iconTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  iconEmoji: {
    fontSize: 24,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#191C1D',
  },
  dangerText: {
    fontSize: 14,
    color: '#BA1A1A',
    fontWeight: '500',
    marginTop: 4,
  },
  badgeContainer: {
    backgroundColor: '#E0E0E0',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    fontSize: 12,
    color: '#45464C',
    fontWeight: '600',
  },
  progressContainer: {
    marginTop: 8,
  },
  amountsRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 8,
  },
  amountText: {
    fontSize: 20,
    fontWeight: '700',
    color: '#191C1D',
  },
  targetAmountText: {
    fontSize: 16,
    color: '#45464C',
    fontWeight: '500',
    marginLeft: 4,
  },
  progressBarBackground: {
    height: 8,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  debtDetailsContainer: {
    marginTop: 8,
  },
  debtDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  debtDetailLabel: {
    fontSize: 16,
    color: '#45464C',
  },
  debtDetailValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#191C1D',
  },
});
