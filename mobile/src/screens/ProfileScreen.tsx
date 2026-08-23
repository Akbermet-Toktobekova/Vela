import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  TextInput,
  Alert,
} from "react-native";
import { UserProfile } from "../types";
import { colors } from "../theme/colors";
import { api } from "../services/api";

export const ProfileScreen: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [incomeInput, setIncomeInput] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    const data = await api.getProfile();
    setProfile(data);
    setIncomeInput(data.monthly_income.toString());
  };

  const handleSaveProfile = async () => {
    if (!profile) return;
    setSaving(true);

    const updated = {
      ...profile,
      monthly_income: parseFloat(incomeInput) || profile.monthly_income,
    };

    await api.updateProfile(updated);
    setProfile(updated);
    setSaving(false);
    Alert.alert("Saved", "Financial profile updated successfully!");
  };

  if (!profile) return null;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Financial Profile</Text>
          <Text style={styles.headerSubtitle}>
            Persistent context used by your multi-agent advisors
          </Text>
        </View>

        {/* Income Card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Monthly Net Income</Text>
          <View style={styles.inputRow}>
            <Text style={styles.currencySymbol}>$</Text>
            <TextInput
              style={styles.textInput}
              value={incomeInput}
              onChangeText={setIncomeInput}
              keyboardType="numeric"
              placeholder="3500"
              placeholderTextColor={colors.textMuted}
            />
          </View>
        </View>

        {/* Expenses List */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Monthly Expense Breakdown</Text>
          {profile.expenses.map((expense, idx) => (
            <View key={idx} style={styles.listItem}>
              <View>
                <Text style={styles.itemTitle}>{expense.category}</Text>
                <Text style={styles.itemTag}>
                  {expense.is_essential ? "Needs (Essential)" : "Wants (Discretionary)"}
                </Text>
              </View>
              <Text style={styles.itemAmount}>${expense.amount.toLocaleString()}</Text>
            </View>
          ))}
        </View>

        {/* Debts List */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Debts & Interest Rates</Text>
          {profile.debts.map((debt, idx) => (
            <View key={idx} style={styles.listItem}>
              <View>
                <Text style={styles.itemTitle}>{debt.name}</Text>
                <Text style={styles.itemTag}>{debt.interest_rate}% APR</Text>
              </View>
              <Text style={[styles.itemAmount, { color: colors.accentDanger }]}>
                ${debt.balance.toLocaleString()}
              </Text>
            </View>
          ))}
        </View>

        {/* Save Button */}
        <TouchableOpacity
          style={styles.saveButton}
          onPress={handleSaveProfile}
          disabled={saving}
        >
          <Text style={styles.saveButtonText}>
            {saving ? "Saving..." : "Save & Sync with Advisors"}
          </Text>
        </TouchableOpacity>
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
  headerTitle: {
    fontSize: 22,
    fontWeight: "800",
    color: colors.textPrimary,
  },
  headerSubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 4,
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
    fontSize: 15,
    fontWeight: "700",
    color: colors.textPrimary,
    marginBottom: 12,
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 10,
    paddingHorizontal: 14,
  },
  currencySymbol: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.accent,
    marginRight: 6,
  },
  textInput: {
    flex: 1,
    color: colors.textPrimary,
    fontSize: 16,
    fontWeight: "600",
    paddingVertical: 10,
  },
  listItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  itemTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textPrimary,
  },
  itemTag: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  itemAmount: {
    fontSize: 15,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  saveButton: {
    backgroundColor: colors.primary,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 10,
  },
  saveButtonText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },
});
