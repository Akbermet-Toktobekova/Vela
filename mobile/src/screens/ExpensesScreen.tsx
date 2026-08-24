import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from "react-native";
import { ExpenseSummary, Transaction, TransactionSource } from "../types";
import { colors } from "../theme/colors";
import { api } from "../services/api";

const SIMULATION_PRESETS = [
  { label: "☕ NFC Coffee (€4.80)", merchant: "STARBUCKS DEAK BP", amount: 4.80, source: "nfc_tap" as TransactionSource },
  { label: "🛒 SPAR Grocery (€26.40)", merchant: "POS 041 SPAR CORVIN HU", amount: 26.40, source: "apple_pay" as TransactionSource },
  { label: "📦 Amazon Online (€32.50)", merchant: "AMAZON EU SARL LUX", amount: 32.50, source: "open_banking" as TransactionSource },
  { label: "💸 Transfer to Alex (€15.00)", merchant: "Transfer to Alex - Lunch Split", amount: 15.00, source: "open_banking" as TransactionSource },
  { label: "🍔 Wolt Delivery (€14.50)", merchant: "WOLT RESTAURANT BP", amount: 14.50, source: "google_wallet" as TransactionSource },
  { label: "🚕 Bolt Taxi (€9.20)", merchant: "BOLT.EU/TAXI BUDAPEST", amount: 9.20, source: "apple_pay" as TransactionSource },
];

export const ExpensesScreen: React.FC = () => {
  const [summary, setSummary] = useState<ExpenseSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [lastIngestedId, setLastIngestedId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const data = await api.getExpensesSummary();
      setSummary(data);
    } catch {
      // Handled in api client
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateTap = async (preset: typeof SIMULATION_PRESETS[0]) => {
    setSimulating(true);
    try {
      const newTx = await api.simulateTapToPay(preset.merchant, preset.amount, preset.source);
      setLastIngestedId(newTx.id);
      await loadData();
    } catch {
      Alert.alert("Error", "Could not ingest simulated transaction");
    } finally {
      setSimulating(false);
    }
  };

  const getSourceBadge = (source: TransactionSource) => {
    switch (source) {
      case "apple_pay":
        return { label: "🍏 Apple Pay", bg: "#1E293B", text: "#F8FAFC" };
      case "google_wallet":
        return { label: "🤖 Google Wallet", bg: "#1E3A8A", text: "#93C5FD" };
      case "nfc_tap":
        return { label: "📲 NFC Tap", bg: "#065F46", text: "#34D399" };
      case "open_banking":
        return { label: "🏦 Open Banking", bg: "#312E81", text: "#C7D2FE" };
      default:
        return { label: "💳 Card", bg: "#334155", text: "#94A3B8" };
    }
  };

  if (loading || !summary) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Syncing live transaction stream...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {/* Love Banner */}
        <View style={styles.loveBanner}>
          <Text style={styles.loveBannerText}>Солнышко, я люблю тебя ❤️</Text>
        </View>

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Live Expense Tracker</Text>
          <Text style={styles.headerSubtitle}>
            Automated Ingestion from Phone NFC, Wallet & PSD2 Banks
          </Text>
        </View>

        {/* Total Spending Card */}
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Total Tracked Spending</Text>
          <Text style={styles.totalAmount}>€{summary.total_spent.toLocaleString()}</Text>

          {/* Needs vs Wants Breakdown Progress Bar */}
          <View style={styles.breakdownBarContainer}>
            <View style={styles.barLabelRow}>
              <Text style={styles.needsText}>
                Needs: €{summary.needs_total.toLocaleString()} ({summary.needs_percentage}%)
              </Text>
              <Text style={styles.wantsText}>
                Wants: €{summary.wants_total.toLocaleString()} ({summary.wants_percentage}%)
              </Text>
            </View>
            <View style={styles.barTrack}>
              <View
                style={[
                  styles.barNeedsFill,
                  { width: `${Math.min(summary.needs_percentage, 100)}%` },
                ]}
              />
              <View
                style={[
                  styles.barWantsFill,
                  { width: `${Math.min(summary.wants_percentage, 100)}%` },
                ]}
              />
            </View>
          </View>
        </View>

        {/* Interactive NFC Tap Simulator */}
        <View style={styles.simulatorCard}>
          <View style={styles.simHeaderRow}>
            <Text style={styles.simTitle}>⚡ Test Live NFC Tap-to-Pay</Text>
            {simulating && <ActivityIndicator size="small" color={colors.accent} />}
          </View>
          <Text style={styles.simSubtitle}>
            Tap any button to simulate an instant purchase and watch it auto-categorize in real time:
          </Text>

          <View style={styles.presetGrid}>
            {SIMULATION_PRESETS.map((preset, idx) => (
              <TouchableOpacity
                key={idx}
                style={styles.presetButton}
                onPress={() => handleSimulateTap(preset)}
                disabled={simulating}
              >
                <Text style={styles.presetButtonText}>{preset.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Category Breakdown */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Spending by Category</Text>
          {summary.category_breakdown.map((cat, idx) => (
            <View key={idx} style={styles.categoryRow}>
              <View style={styles.catLeft}>
                <Text style={styles.catIcon}>{cat.icon}</Text>
                <View>
                  <Text style={styles.catName}>{cat.category}</Text>
                  <Text style={styles.catBucket}>
                    {cat.bucket === "needs" ? "Needs (50%)" : "Wants (30%)"}
                  </Text>
                </View>
              </View>
              <View style={styles.catRight}>
                <Text style={styles.catAmount}>€{cat.amount.toFixed(2)}</Text>
                <Text style={styles.catPct}>{cat.percentage}%</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Live Transaction Stream */}
        <View style={styles.card}>
          <View style={styles.streamHeaderRow}>
            <Text style={styles.sectionTitle}>Live Ingestion Feed</Text>
            <View style={styles.liveIndicator}>
              <View style={styles.liveDot} />
              <Text style={styles.liveText}>Live Sync</Text>
            </View>
          </View>

          {summary.recent_transactions.map((tx) => {
            const badge = getSourceBadge(tx.source);
            const isJustAdded = lastIngestedId === tx.id;

            return (
              <View
                key={tx.id}
                style={[
                  styles.transactionItem,
                  isJustAdded && styles.transactionItemHighlighted,
                ]}
              >
                <View style={styles.txIconContainer}>
                  <Text style={styles.txIcon}>{tx.icon}</Text>
                </View>

                <View style={styles.txMiddle}>
                  <Text style={styles.txTitle}>{tx.clean_merchant}</Text>
                  <Text style={styles.txSubtitle} numberOfLines={1}>
                    {tx.raw_merchant}
                  </Text>
                  <View style={styles.badgeRow}>
                    <View style={[styles.sourcePill, { backgroundColor: badge.bg }]}>
                      <Text style={[styles.sourcePillText, { color: badge.text }]}>
                        {badge.label}
                      </Text>
                    </View>
                    <Text style={styles.txTime}>{tx.timestamp}</Text>
                  </View>
                </View>

                <View style={styles.txRight}>
                  <Text style={styles.txAmount}>-€{tx.amount.toFixed(2)}</Text>
                  <Text
                    style={[
                      styles.bucketTag,
                      tx.bucket === "needs" ? styles.bucketNeeds : styles.bucketWants,
                    ]}
                  >
                    {tx.bucket === "needs" ? "Needs" : "Wants"}
                  </Text>
                </View>
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
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    color: colors.textSecondary,
    marginTop: 12,
    fontSize: 14,
  },
  header: {
    marginBottom: 16,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: "800",
    color: colors.textPrimary,
  },
  headerSubtitle: {
    fontSize: 13,
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
  cardLabel: {
    fontSize: 13,
    color: colors.textSecondary,
    fontWeight: "600",
    textTransform: "uppercase",
  },
  totalAmount: {
    fontSize: 32,
    fontWeight: "900",
    color: colors.textPrimary,
    marginVertical: 8,
  },
  breakdownBarContainer: {
    marginTop: 8,
  },
  barLabelRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 6,
  },
  needsText: {
    fontSize: 12,
    color: colors.accent,
    fontWeight: "700",
  },
  wantsText: {
    fontSize: 12,
    color: colors.primaryLight,
    fontWeight: "700",
  },
  barTrack: {
    height: 10,
    backgroundColor: colors.background,
    borderRadius: 5,
    flexDirection: "row",
    overflow: "hidden",
  },
  barNeedsFill: {
    height: "100%",
    backgroundColor: colors.accent,
  },
  barWantsFill: {
    height: "100%",
    backgroundColor: colors.primary,
  },
  simulatorCard: {
    backgroundColor: "#1E1B4B",
    borderWidth: 1,
    borderColor: "#4338CA",
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  simHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  simTitle: {
    fontSize: 15,
    fontWeight: "800",
    color: "#E0E7FF",
  },
  simSubtitle: {
    fontSize: 12,
    color: "#A5B4FC",
    marginBottom: 12,
    lineHeight: 16,
  },
  presetGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  presetButton: {
    backgroundColor: "#312E81",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#6366F1",
    width: "48%",
    marginBottom: 8,
    alignItems: "center",
  },
  presetButtonText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "700",
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: colors.textPrimary,
    marginBottom: 14,
  },
  categoryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  catLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  catIcon: {
    fontSize: 22,
    marginRight: 12,
  },
  catName: {
    fontSize: 14,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  catBucket: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  catRight: {
    alignItems: "flex-end",
  },
  catAmount: {
    fontSize: 14,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  catPct: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 2,
  },
  streamHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  liveIndicator: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#064E3B",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.accent,
    marginRight: 5,
  },
  liveText: {
    color: "#D1FAE5",
    fontSize: 10,
    fontWeight: "700",
    textTransform: "uppercase",
  },
  transactionItem: {
    flexDirection: "row",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
    alignItems: "center",
  },
  transactionItemHighlighted: {
    backgroundColor: "#064E3B22",
    borderRadius: 8,
    paddingHorizontal: 6,
  },
  txIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.background,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  txIcon: {
    fontSize: 20,
  },
  txMiddle: {
    flex: 1,
    marginRight: 8,
  },
  txTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  txSubtitle: {
    fontSize: 11,
    color: colors.textMuted,
    marginVertical: 2,
  },
  badgeRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 2,
  },
  sourcePill: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: 6,
  },
  sourcePillText: {
    fontSize: 10,
    fontWeight: "700",
  },
  txTime: {
    fontSize: 10,
    color: colors.textMuted,
  },
  txRight: {
    alignItems: "flex-end",
  },
  txAmount: {
    fontSize: 15,
    fontWeight: "800",
    color: colors.textPrimary,
    marginBottom: 4,
  },
  bucketTag: {
    fontSize: 10,
    fontWeight: "700",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  bucketNeeds: {
    backgroundColor: "#065F46",
    color: "#34D399",
  },
  bucketWants: {
    backgroundColor: "#312E81",
    color: "#C7D2FE",
  },
  loveBanner: {
    backgroundColor: "#83184333",
    borderColor: "#F43F5E",
    borderWidth: 1.5,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 16,
    marginBottom: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  loveBannerText: {
    fontSize: 16,
    fontWeight: "800",
    color: "#FDA4AF",
    letterSpacing: 0.5,
  },
});
