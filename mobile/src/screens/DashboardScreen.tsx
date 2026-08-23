import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
} from "react-native";
import { UserProfile } from "../types";
import { colors } from "../theme/colors";
import { api } from "../services/api";

interface Props {
  onNavigateToChat: () => void;
}

export const DashboardScreen: React.FC<Props> = ({ onNavigateToChat }) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    const data = await api.getProfile();
    setProfile(data);
  };

  if (!profile) return null;

  const totalIncome = profile.monthly_income;
  const essentialExpenses = profile.expenses
    .filter((e) => e.is_essential)
    .reduce((sum, e) => sum + e.amount, 0);
  const wantsExpenses = profile.expenses
    .filter((e) => !e.is_essential)
    .reduce((sum, e) => sum + e.amount, 0);
  const totalExpenses = essentialExpenses + wantsExpenses;
  const netSurplus = totalIncome - totalExpenses;

  const totalDebt = profile.debts.reduce((sum, d) => sum + d.balance, 0);
  const totalSaved = profile.savings_goals.reduce((sum, g) => sum + g.current_amount, 0);
  const totalSavingsTarget = profile.savings_goals.reduce((sum, g) => sum + g.target_amount, 0);

  const needsPct = totalIncome > 0 ? (essentialExpenses / totalIncome) * 100 : 0;
  const wantsPct = totalIncome > 0 ? (wantsExpenses / totalIncome) * 100 : 0;
  const surplusPct = totalIncome > 0 ? (netSurplus / totalIncome) * 100 : 0;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerGreeting}>Welcome back, Akbermet 👋</Text>
          <Text style={styles.headerSubtitle}>Here is your live financial snapshot</Text>
        </View>

        {/* Top Cash Flow Card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Monthly Cash Flow</Text>
          <View style={styles.metricRow}>
            <View>
              <Text style={styles.metricLabel}>Net Income</Text>
              <Text style={styles.metricValue}>${totalIncome.toLocaleString()}</Text>
            </View>
            <View>
              <Text style={styles.metricLabel}>Total Expenses</Text>
              <Text style={[styles.metricValue, { color: colors.accentDanger }]}>
                -${totalExpenses.toLocaleString()}
              </Text>
            </View>
            <View>
              <Text style={styles.metricLabel}>Free Surplus</Text>
              <Text style={[styles.metricValue, { color: colors.accent }]}>
                +${netSurplus.toLocaleString()}
              </Text>
            </View>
          </View>

          {/* 50/30/20 Breakdown Bars */}
          <View style={styles.progressSection}>
            <Text style={styles.progressHeader}>50 / 30 / 20 Framework</Text>
            
            {/* Needs Bar */}
            <View style={styles.barItem}>
              <View style={styles.barLabelRow}>
                <Text style={styles.barLabel}>Needs (Essential: ${essentialExpenses.toLocaleString()})</Text>
                <Text style={styles.barPct}>{needsPct.toFixed(1)}% / 50%</Text>
              </View>
              <View style={styles.barTrack}>
                <View
                  style={[
                    styles.barFill,
                    {
                      width: `${Math.min(needsPct, 100)}%`,
                      backgroundColor: needsPct > 55 ? colors.accentWarning : colors.primary,
                    },
                  ]}
                />
              </View>
            </View>

            {/* Wants Bar */}
            <View style={styles.barItem}>
              <View style={styles.barLabelRow}>
                <Text style={styles.barLabel}>Wants (Discretionary: ${wantsExpenses.toLocaleString()})</Text>
                <Text style={styles.barPct}>{wantsPct.toFixed(1)}% / 30%</Text>
              </View>
              <View style={styles.barTrack}>
                <View
                  style={[
                    styles.barFill,
                    {
                      width: `${Math.min(wantsPct, 100)}%`,
                      backgroundColor: wantsPct > 35 ? colors.accentDanger : colors.primaryLight,
                    },
                  ]}
                />
              </View>
            </View>

            {/* Savings & Surplus Bar */}
            <View style={styles.barItem}>
              <View style={styles.barLabelRow}>
                <Text style={styles.barLabel}>Surplus Capacity</Text>
                <Text style={[styles.barPct, { color: colors.accent }]}>
                  {surplusPct.toFixed(1)}% / 20%
                </Text>
              </View>
              <View style={styles.barTrack}>
                <View
                  style={[
                    styles.barFill,
                    {
                      width: `${Math.min(surplusPct, 100)}%`,
                      backgroundColor: colors.accent,
                    },
                  ]}
                />
              </View>
            </View>
          </View>
        </View>

        {/* Debt Elimination Card */}
        <View style={styles.card}>
          <View style={styles.cardHeaderRow}>
            <Text style={styles.cardTitle}>Outstanding Liabilities</Text>
            <Text style={[styles.badgeText, { color: colors.accentDanger }]}>
              ${totalDebt.toLocaleString()} total
            </Text>
          </View>

          {profile.debts.map((debt, index) => (
            <View key={index} style={styles.debtItemRow}>
              <View>
                <Text style={styles.debtName}>{debt.name}</Text>
                <Text style={styles.debtSub}>
                  Min: ${debt.minimum_payment}/mo • {debt.interest_rate}% APR
                </Text>
              </View>
              <Text style={styles.debtBalance}>${debt.balance.toLocaleString()}</Text>
            </View>
          ))}

          <TouchableOpacity style={styles.actionButton} onPress={onNavigateToChat}>
            <Text style={styles.actionButtonText}>Optimize Payoff Plan (Avalanche)</Text>
          </TouchableOpacity>
        </View>

        {/* Savings Goals Card */}
        <View style={styles.card}>
          <View style={styles.cardHeaderRow}>
            <Text style={styles.cardTitle}>Savings & Milestones</Text>
            <Text style={[styles.badgeText, { color: colors.accent }]}>
              ${totalSaved.toLocaleString()} / ${totalSavingsTarget.toLocaleString()}
            </Text>
          </View>

          {profile.savings_goals.map((goal, index) => {
            const pct = goal.target_amount > 0 ? (goal.current_amount / goal.target_amount) * 100 : 0;
            return (
              <View key={index} style={styles.goalItem}>
                <View style={styles.barLabelRow}>
                  <Text style={styles.goalName}>{goal.name}</Text>
                  <Text style={styles.goalPct}>{pct.toFixed(0)}%</Text>
                </View>
                <View style={styles.barTrack}>
                  <View
                    style={[
                      styles.barFill,
                      { width: `${Math.min(pct, 100)}%`, backgroundColor: colors.accent },
                    ]}
                  />
                </View>
                <Text style={styles.goalAmounts}>
                  ${goal.current_amount.toLocaleString()} of ${goal.target_amount.toLocaleString()}
                </Text>
              </View>
            );
          })}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 20,
  },
  headerGreeting: {
    fontSize: 22,
    fontWeight: "800",
    color: colors.textPrimary,
  },
  headerSubtitle: {
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: 3,
  },
  card: {
    backgroundColor: colors.cardBackground,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 16,
    padding: 18,
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.textPrimary,
    marginBottom: 12,
  },
  cardHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  badgeText: {
    fontWeight: "700",
    fontSize: 13,
  },
  metricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
    paddingBottom: 14,
    marginBottom: 14,
  },
  metricLabel: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: "800",
    color: colors.textPrimary,
  },
  progressSection: {
    marginTop: 4,
  },
  progressHeader: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.textSecondary,
    marginBottom: 10,
  },
  barItem: {
    marginBottom: 10,
  },
  barLabelRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  barLabel: {
    fontSize: 12,
    color: colors.textPrimary,
  },
  barPct: {
    fontSize: 12,
    fontWeight: "700",
    color: colors.textSecondary,
  },
  barTrack: {
    height: 8,
    backgroundColor: colors.background,
    borderRadius: 4,
    overflow: "hidden",
  },
  barFill: {
    height: "100%",
    borderRadius: 4,
  },
  debtItemRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  debtName: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  debtSub: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  debtBalance: {
    fontSize: 15,
    fontWeight: "700",
    color: colors.accentDanger,
  },
  actionButton: {
    marginTop: 14,
    backgroundColor: colors.primary,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center",
  },
  actionButtonText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "700",
  },
  goalItem: {
    marginBottom: 14,
  },
  goalName: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  goalPct: {
    fontSize: 12,
    fontWeight: "700",
    color: colors.accent,
  },
  goalAmounts: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 4,
  },
});
