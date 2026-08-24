import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';

export const LearnScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(1); // Default to option 1

  return (
    <View style={[styles.mainWrapper, { paddingTop: Math.max(insets.top, 20) }]}>
      <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.screenTitle}>Academy</Text>
            <Text style={styles.screenSubtitle}>Daily bite-sized finance clarity</Text>
          </View>
          <View style={styles.streakBadge}>
            <Ionicons name="flame" size={16} color="#FF3366" />
            <Text style={styles.streakText}>5 days streak</Text>
          </View>
        </View>

        {/* 1. Daily Bite Hero Card */}
        <View style={styles.lessonCard}>
          <View style={styles.lessonTop}>
            <View style={styles.lessonTag}>
              <Text style={styles.lessonTagText}>LESSON OF THE DAY</Text>
            </View>
            <View style={styles.readTime}>
              <Ionicons name="time-outline" size={13} color="#72777A" />
              <Text style={styles.readTimeText}>2 min read</Text>
            </View>
          </View>

          <Text style={styles.lessonTitle}>How compound interest works</Text>
          <Text style={styles.lessonDesc}>
            Discover how small daily investments compound exponentially over time when reinvested automatically.
          </Text>

          <View style={styles.lessonFooter}>
            <View style={styles.indicatorDot} />
            <TouchableOpacity style={styles.startBtn} activeOpacity={0.8}>
              <Text style={styles.startBtnText}>Start Reading</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 2. Knowledge Check Quiz */}
        <View style={styles.sectionHeader}>
          <Ionicons name="bulb-outline" size={18} color="#191C1F" />
          <Text style={styles.sectionTitle}>Knowledge Check</Text>
        </View>

        <View style={styles.quizCard}>
          <Text style={styles.quizQuestion}>
            If you start investing $100 a month at age 20 versus age 30, assuming an 8% annual return, roughly how much more will you have at age 60?
          </Text>

          {/* Options */}
          <TouchableOpacity 
            style={[styles.optionItem, selectedAnswer === 0 && styles.optionSelected]} 
            onPress={() => setSelectedAnswer(0)}
            activeOpacity={0.7}
          >
            <Text style={[styles.optionText, selectedAnswer === 0 && styles.optionTextSelected]}>
              About the same
            </Text>
            <View style={[styles.radioCircle, selectedAnswer === 0 && styles.radioCircleSelected]}>
              {selectedAnswer === 0 && <View style={styles.radioInner} />}
            </View>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.optionItem, selectedAnswer === 1 && styles.optionSelected]} 
            onPress={() => setSelectedAnswer(1)}
            activeOpacity={0.7}
          >
            <Text style={[styles.optionText, selectedAnswer === 1 && styles.optionTextSelected]}>
              Twice as much
            </Text>
            <View style={[styles.radioCircle, selectedAnswer === 1 && styles.radioCircleSelected]}>
              {selectedAnswer === 1 && <View style={styles.radioInner} />}
            </View>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.optionItem, selectedAnswer === 2 && styles.optionSelected]} 
            onPress={() => setSelectedAnswer(2)}
            activeOpacity={0.7}
          >
            <Text style={[styles.optionText, selectedAnswer === 2 && styles.optionTextSelected]}>
              Half as much
            </Text>
            <View style={[styles.radioCircle, selectedAnswer === 2 && styles.radioCircleSelected]}>
              {selectedAnswer === 2 && <View style={styles.radioInner} />}
            </View>
          </TouchableOpacity>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  mainWrapper: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
    paddingTop: 4,
  },
  screenTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#191C1F',
    letterSpacing: -0.5,
  },
  screenSubtitle: {
    fontSize: 12,
    color: '#72777A',
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFF0F3',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  streakText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FF3366',
  },
  lessonCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 24,
    padding: 20,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  lessonTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  lessonTag: {
    backgroundColor: '#E5F2FF',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  lessonTagText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0075EB',
    letterSpacing: 0.5,
  },
  readTime: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  readTimeText: {
    fontSize: 11,
    color: '#72777A',
    fontWeight: '500',
  },
  lessonTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#191C1F',
    marginBottom: 6,
    letterSpacing: -0.3,
  },
  lessonDesc: {
    fontSize: 13,
    color: '#555A5E',
    lineHeight: 18,
    marginBottom: 16,
  },
  lessonFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  indicatorDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#0075EB',
  },
  startBtn: {
    backgroundColor: '#191C1F',
    paddingHorizontal: 18,
    paddingVertical: 9,
    borderRadius: 14,
  },
  startBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#191C1F',
  },
  quizCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  quizQuestion: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '600',
    color: '#191C1F',
    marginBottom: 16,
  },
  optionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderRadius: 14,
    backgroundColor: '#F8F9FA',
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  optionSelected: {
    backgroundColor: '#191C1F',
    borderColor: '#191C1F',
  },
  optionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#191C1F',
  },
  optionTextSelected: {
    color: '#FFFFFF',
  },
  radioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#C6C6CD',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioCircleSelected: {
    borderColor: '#FFFFFF',
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#FFFFFF',
  },
});
