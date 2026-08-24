import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, SafeAreaView, Platform } from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';

export default function LearnScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Academy</Text>
          <View style={styles.streakBadge}>
            <MaterialCommunityIcons name="fire" size={18} color="#FF7A00" />
            <Text style={styles.streakText}>5 day streak</Text>
          </View>
        </View>

        {/* Daily Bite */}
        <Text style={styles.sectionTitle}>Daily Bite</Text>
        <TouchableOpacity style={styles.biteCard}>
          <View style={styles.biteContent}>
            <View style={styles.biteBadge}>
              <Feather name="clock" size={12} color="#8A8D93" style={styles.biteBadgeIcon} />
              <Text style={styles.biteBadgeText}>2 min read</Text>
            </View>
            <Text style={styles.biteTitle}>The 50/30/20 Rule</Text>
            <Text style={styles.biteDesc}>A simple framework to manage your monthly income effectively.</Text>
          </View>
          <View style={styles.biteAction}>
            <Text style={styles.biteActionText}>Start</Text>
            <Feather name="arrow-right" size={16} color="#007AFF" />
          </View>
        </TouchableOpacity>

        {/* Modules */}
        <Text style={styles.sectionTitle}>Learn & Earn</Text>
        
        <View style={styles.moduleCard}>
          <View style={styles.moduleIconWrapper}>
            <Ionicons name="stats-chart" size={24} color="#8C52FF" />
          </View>
          <View style={styles.moduleInfo}>
            <Text style={styles.moduleTitle}>Investing Basics</Text>
            <Text style={styles.moduleSubtitle}>4 lessons • Earn $5</Text>
          </View>
          <Feather name="chevron-right" size={20} color="#C4C4C4" />
        </View>

        <View style={styles.moduleCard}>
          <View style={[styles.moduleIconWrapper, { backgroundColor: '#E5F8ED' }]}>
            <MaterialCommunityIcons name="shield-check-outline" size={24} color="#00C853" />
          </View>
          <View style={styles.moduleInfo}>
            <Text style={styles.moduleTitle}>Crypto Security</Text>
            <Text style={styles.moduleSubtitle}>3 lessons • Earn $3</Text>
          </View>
          <Feather name="chevron-right" size={20} color="#C4C4C4" />
        </View>

        {/* Knowledge Check */}
        <View style={styles.quizContainer}>
          <Text style={styles.quizHeader}>Knowledge Check</Text>
          <Text style={styles.quizQuestion}>What is compound interest?</Text>
          
          <TouchableOpacity style={styles.quizOption}>
            <View style={styles.radioOuter}>
              <View style={styles.radioInner} />
            </View>
            <Text style={styles.quizOptionText}>Interest on initial principal only</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={[styles.quizOption, styles.quizOptionSelected]}>
            <View style={[styles.radioOuter, styles.radioOuterSelected]}>
              <View style={[styles.radioInner, styles.radioInnerSelected]} />
            </View>
            <Text style={[styles.quizOptionText, styles.quizOptionTextSelected]}>Interest on principal plus accumulated interest</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.quizOption}>
            <View style={styles.radioOuter}>
              <View style={styles.radioInner} />
            </View>
            <Text style={styles.quizOptionText}>A fee charged by banks</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.submitButton}>
            <Text style={styles.submitButtonText}>Check answer</Text>
          </TouchableOpacity>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  scroll: { flex: 1 },
  content: { padding: 20, paddingBottom: 40 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32, marginTop: Platform.OS === 'android' ? 24 : 0 },
  title: { fontSize: 32, fontWeight: 'bold', color: '#191C1F' },
  streakBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF2E5', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, gap: 4 },
  streakText: { fontSize: 13, fontWeight: '700', color: '#FF7A00' },
  sectionTitle: { fontSize: 20, fontWeight: '700', color: '#191C1F', marginBottom: 16, marginTop: 8 },
  biteCard: { backgroundColor: '#FFFFFF', borderRadius: 16, overflow: 'hidden', marginBottom: 32, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 8, elevation: 2, borderWidth: 1, borderColor: '#EAECEF' },
  biteContent: { padding: 20 },
  biteBadge: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  biteBadgeIcon: { marginRight: 4 },
  biteBadgeText: { fontSize: 12, fontWeight: '600', color: '#8A8D93', textTransform: 'uppercase', letterSpacing: 0.5 },
  biteTitle: { fontSize: 22, fontWeight: 'bold', color: '#191C1F', marginBottom: 8 },
  biteDesc: { fontSize: 15, color: '#5A5D65', lineHeight: 22 },
  biteAction: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#F8F9FA', paddingHorizontal: 20, paddingVertical: 16, borderTopWidth: 1, borderTopColor: '#EAECEF' },
  biteActionText: { fontSize: 15, fontWeight: '600', color: '#007AFF' },
  moduleCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', padding: 16, borderRadius: 16, marginBottom: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.03, shadowRadius: 4, elevation: 1, borderWidth: 1, borderColor: '#EAECEF' },
  moduleIconWrapper: { width: 48, height: 48, borderRadius: 12, backgroundColor: '#F4EEFF', alignItems: 'center', justifyContent: 'center', marginRight: 16 },
  moduleInfo: { flex: 1 },
  moduleTitle: { fontSize: 16, fontWeight: '600', color: '#191C1F', marginBottom: 4 },
  moduleSubtitle: { fontSize: 13, color: '#8A8D93' },
  quizContainer: { marginTop: 32, backgroundColor: '#FFFFFF', borderRadius: 16, padding: 20, borderWidth: 1, borderColor: '#EAECEF', shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 8, elevation: 2 },
  quizHeader: { fontSize: 13, fontWeight: '700', color: '#8A8D93', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 },
  quizQuestion: { fontSize: 20, fontWeight: 'bold', color: '#191C1F', marginBottom: 20, lineHeight: 28 },
  quizOption: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, paddingHorizontal: 16, borderRadius: 12, borderWidth: 1, borderColor: '#EAECEF', marginBottom: 12 },
  quizOptionSelected: { borderColor: '#191C1F', backgroundColor: '#F8F9FA' },
  radioOuter: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: '#C4C4C4', alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  radioOuterSelected: { borderColor: '#191C1F' },
  radioInner: { width: 10, height: 10, borderRadius: 5, backgroundColor: 'transparent' },
  radioInnerSelected: { backgroundColor: '#191C1F' },
  quizOptionText: { flex: 1, fontSize: 15, color: '#191C1F', fontWeight: '500' },
  quizOptionTextSelected: { fontWeight: '600' },
  submitButton: { backgroundColor: '#191C1F', borderRadius: 24, paddingVertical: 14, alignItems: 'center', marginTop: 12 },
  submitButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '600' }
});
