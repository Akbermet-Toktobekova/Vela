import React, { useState } from 'react';
import { SafeAreaView, ScrollView, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

export const LearnScreen: React.FC = () => {
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(1); // 'Twice as much' active by default

  const handleSelect = (index: number) => {
    setSelectedAnswer(index);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Header Section */}
        <View style={styles.header}>
          <View style={styles.titleContainer}>
            <Text style={styles.title}>Daily Bite</Text>
            <Text style={styles.subtitle}>Your daily dose of financial clarity.</Text>
          </View>
          <View style={styles.streakBadge}>
            <Text style={styles.streakEmoji}>🔥</Text>
            <Text style={styles.streakText}>5 days streak</Text>
          </View>
        </View>

        {/* Lesson Card */}
        <View style={[styles.card, styles.lessonCard]}>
          <View style={styles.cardHeader}>
            <View style={styles.lessonBadge}>
              <Text style={styles.lessonBadgeText}>LESSON OF THE DAY</Text>
            </View>
            <View style={styles.timeBadge}>
              <Text style={styles.timeBadgeText}>⏱ 2 min read</Text>
            </View>
          </View>
          <Text style={styles.lessonTitle}>How compound interest works</Text>
          <Text style={styles.lessonDescription} numberOfLines={2}>
            Discover how your money can grow exponentially over time by earning interest on both your initial principal and accumulated interest.
          </Text>
          <View style={styles.lessonFooter}>
            <View style={styles.progressDot} />
            <TouchableOpacity style={styles.startButton}>
              <Text style={styles.startButtonText}>Start Reading</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Knowledge Check Section */}
        <View style={styles.knowledgeSection}>
          <Text style={styles.sectionTitle}>🧠 Knowledge Check</Text>
          <View style={[styles.card, styles.questionCard]}>
            <Text style={styles.questionText}>
              If you start investing $100 a month at age 20 versus age 30, assuming an 8% annual return, roughly how much more will you have at age 60?
            </Text>
            
            <TouchableOpacity
              style={[styles.optionButton, selectedAnswer === 0 && styles.optionButtonActive]}
              onPress={() => handleSelect(0)}
              activeOpacity={0.8}
            >
              <Text style={[styles.optionText, selectedAnswer === 0 && styles.optionTextActive]}>About the same</Text>
              <View style={[styles.radioCircle, selectedAnswer === 0 && styles.radioCircleActive]}>
                {selectedAnswer === 0 && <Text style={styles.checkmark}>✅</Text>}
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.optionButton, selectedAnswer === 1 && styles.optionButtonActive]}
              onPress={() => handleSelect(1)}
              activeOpacity={0.8}
            >
              <Text style={[styles.optionText, selectedAnswer === 1 && styles.optionTextActive]}>Twice as much</Text>
              <View style={[styles.radioCircle, selectedAnswer === 1 && styles.radioCircleActive]}>
                {selectedAnswer === 1 && <Text style={styles.checkmark}>✅</Text>}
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.optionButton, selectedAnswer === 2 && styles.optionButtonActive]}
              onPress={() => handleSelect(2)}
              activeOpacity={0.8}
            >
              <Text style={[styles.optionText, selectedAnswer === 2 && styles.optionTextActive]}>Half as much</Text>
              <View style={[styles.radioCircle, selectedAnswer === 2 && styles.radioCircleActive]}>
                {selectedAnswer === 2 && <Text style={styles.checkmark}>✅</Text>}
              </View>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollContent: {
    padding: 24,
  },
  header: {
    marginBottom: 32,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  titleContainer: {
    flex: 1,
    paddingRight: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#191C1D',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#45464C',
    lineHeight: 22,
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E1E3E4',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 100,
  },
  streakEmoji: {
    fontSize: 14,
    marginRight: 4,
  },
  streakText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#191C1D',
  },
  card: {
    backgroundColor: '#F8F9FA',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#C6C6CD',
    padding: 20,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.04,
    shadowRadius: 30,
    elevation: 4,
  },
  lessonCard: {
    marginBottom: 40,
    backgroundColor: '#F8F9FA',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  lessonBadge: {
    backgroundColor: '#E8F1FF',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  lessonBadgeText: {
    color: '#0056D2',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  timeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeBadgeText: {
    fontSize: 14,
    color: '#45464C',
    fontWeight: '500',
  },
  lessonTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#191C1D',
    marginBottom: 12,
  },
  lessonDescription: {
    fontSize: 15,
    color: '#45464C',
    lineHeight: 22,
    marginBottom: 20,
  },
  lessonFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  progressDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#0056D2',
  },
  startButton: {
    backgroundColor: '#000000',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 100,
  },
  startButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 15,
  },
  knowledgeSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#191C1D',
    marginBottom: 16,
  },
  questionCard: {
    padding: 20,
  },
  questionText: {
    fontSize: 16,
    color: '#191C1D',
    lineHeight: 24,
    fontWeight: '500',
    marginBottom: 24,
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#C6C6CD',
    borderRadius: 100,
    paddingVertical: 16,
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  optionButtonActive: {
    backgroundColor: '#000000',
    borderColor: '#000000',
  },
  optionText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#191C1D',
  },
  optionTextActive: {
    color: '#FFFFFF',
  },
  radioCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#C6C6CD',
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioCircleActive: {
    borderColor: 'transparent',
    backgroundColor: 'transparent',
    borderWidth: 0,
  },
  checkmark: {
    fontSize: 16,
  },
});
