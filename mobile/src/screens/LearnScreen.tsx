import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity, 
  Alert 
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { FloatingAuroraBackground } from '../components/FloatingAuroraBackground';

interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

const QUIZ_DATA: QuizQuestion = {
  id: 1,
  question: 'If you start investing €100 a month at age 20 versus age 30, assuming an 8% annual return, roughly how much more will you have at age 60?',
  options: ['About the same', 'Twice as much (~€310,000 vs €149,000)', 'Half as much'],
  correctIndex: 1,
  explanation: 'Compound interest exerts exponential power over time: starting 10 years earlier yields more than double the final wealth!',
};

export const LearnScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const [streakCount, setStreakCount] = useState(5);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);

  const handleSelectOption = (idx: number) => {
    if (isAnswered) return;
    setSelectedOption(idx);
    setIsAnswered(true);

    if (idx === QUIZ_DATA.correctIndex) {
      setStreakCount((prev) => prev + 1);
    }
  };

  return (
    <FloatingAuroraBackground theme="teal">
      <ScrollView 
        style={styles.container} 
        contentContainerStyle={[styles.contentContainer, { paddingTop: Math.max(insets.top, 14) }]} 
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.headerTitle}>Vela Academy</Text>
            <Text style={styles.headerSubtitle}>Daily Micro-learning · High ROI Knowledge</Text>
          </View>
          <View style={styles.streakPill}>
            <Ionicons name="flame" size={16} color="#FF9500" />
            <Text style={styles.streakText}>{streakCount} days</Text>
          </View>
        </View>

        {/* 1. Daily Bite Hero Lesson Card */}
        <View style={styles.lessonCard}>
          <View style={styles.lessonTop}>
            <View style={styles.lessonBadge}>
              <Text style={styles.lessonBadgeText}>LESSON OF THE DAY</Text>
            </View>
            <View style={styles.readTimeRow}>
              <Ionicons name="time-outline" size={13} color="#646B73" />
              <Text style={styles.readTimeText}>2 min read</Text>
            </View>
          </View>

          <Text style={styles.lessonTitle}>The Eighth Wonder: Compound Interest</Text>
          <Text style={styles.lessonDesc}>
            Discover how small, consistent monthly contributions multiply exponentially when reinvested early and left untouched.
          </Text>

          <View style={styles.lessonFooter}>
            <View style={styles.progressDots}>
              <View style={[styles.dot, styles.dotActive]} />
              <View style={styles.dot} />
              <View style={styles.dot} />
            </View>
            <TouchableOpacity 
              style={styles.startBtn} 
              onPress={() => Alert.alert('Lesson Completed! +50 XP', 'You have unlocked the Compound Interest badge!')}
              activeOpacity={0.8}
            >
              <Text style={styles.startBtnText}>Start Reading</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 2. Interactive Knowledge Check Section */}
        <View style={styles.frostedSheetContainer}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <Ionicons name="bulb-outline" size={20} color="#111417" />
              <Text style={styles.sectionTitle}>Daily Knowledge Check</Text>
            </View>
            <Text style={styles.xpBadge}>+100 XP</Text>
          </View>

          <View style={styles.quizCard}>
            <Text style={styles.quizQuestion}>{QUIZ_DATA.question}</Text>

            {QUIZ_DATA.options.map((opt, idx) => {
              const isSelected = selectedOption === idx;
              const isCorrect = idx === QUIZ_DATA.correctIndex;
              let optionStyle = styles.optionItem;
              let textStyle = styles.optionText;

              if (isAnswered) {
                if (isCorrect) {
                  optionStyle = [styles.optionItem, styles.optionCorrect] as any;
                  textStyle = [styles.optionText, styles.optionTextCorrect] as any;
                } else if (isSelected && !isCorrect) {
                  optionStyle = [styles.optionItem, styles.optionWrong] as any;
                  textStyle = [styles.optionText, styles.optionTextWrong] as any;
                }
              } else if (isSelected) {
                optionStyle = [styles.optionItem, styles.optionSelected] as any;
                textStyle = [styles.optionText, styles.optionTextSelected] as any;
              }

              return (
                <TouchableOpacity 
                  key={idx} 
                  style={optionStyle}
                  onPress={() => handleSelectOption(idx)}
                  activeOpacity={0.75}
                >
                  <Text style={textStyle}>{opt}</Text>
                  <View style={styles.radioContainer}>
                    {isAnswered && isCorrect && <Ionicons name="checkmark-circle" size={20} color="#00C853" />}
                    {isAnswered && isSelected && !isCorrect && <Ionicons name="close-circle" size={20} color="#FF3B30" />}
                    {!isAnswered && <View style={[styles.radioCircle, isSelected && styles.radioCircleActive]} />}
                  </View>
                </TouchableOpacity>
              );
            })}

            {isAnswered && (
              <View style={styles.explanationBox}>
                <Ionicons name="information-circle" size={18} color="#0891B2" />
                <Text style={styles.explanationText}>{QUIZ_DATA.explanation}</Text>
              </View>
            )}
          </View>

          <View style={{ height: 40 }} />
        </View>
      </ScrollView>
    </FloatingAuroraBackground>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -0.4,
  },
  headerSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  streakPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255,255,255,0.22)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  streakText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  lessonCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 20,
    marginHorizontal: 16,
    marginBottom: 22,
    borderWidth: 1,
    borderColor: '#D4EBEF',
  },
  lessonTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  lessonBadge: {
    backgroundColor: '#E0F7FA',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  lessonBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0891B2',
    letterSpacing: 0.5,
  },
  readTimeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  readTimeText: {
    fontSize: 11,
    color: '#646B73',
    fontWeight: '500',
  },
  lessonTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111417',
    marginBottom: 6,
    letterSpacing: -0.3,
  },
  lessonDesc: {
    fontSize: 13,
    color: '#646B73',
    lineHeight: 18,
    marginBottom: 16,
  },
  lessonFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  progressDots: {
    flexDirection: 'row',
    gap: 4,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#ECEEF2',
  },
  dotActive: {
    backgroundColor: '#0891B2',
    width: 14,
  },
  startBtn: {
    backgroundColor: '#111417',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 14,
  },
  startBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  frostedSheetContainer: {
    backgroundColor: 'rgba(240, 253, 250, 0.96)',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111417',
  },
  xpBadge: {
    fontSize: 12,
    fontWeight: '800',
    color: '#0891B2',
    backgroundColor: '#E0F7FA',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  quizCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: '#D4EBEF',
  },
  quizQuestion: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '700',
    color: '#111417',
    marginBottom: 16,
  },
  optionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderRadius: 14,
    backgroundColor: '#F8F9FB',
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#ECEEF2',
  },
  optionSelected: {
    backgroundColor: '#111417',
    borderColor: '#111417',
  },
  optionCorrect: {
    backgroundColor: '#E8F8EE',
    borderColor: '#00C853',
  },
  optionWrong: {
    backgroundColor: '#FFF0F3',
    borderColor: '#FF3B30',
  },
  optionText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#111417',
    flex: 1,
    paddingRight: 10,
  },
  optionTextSelected: {
    color: '#FFFFFF',
  },
  optionTextCorrect: {
    color: '#007A33',
    fontWeight: '700',
  },
  optionTextWrong: {
    color: '#93000A',
  },
  radioContainer: {
    width: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: '#C6C6CD',
  },
  radioCircleActive: {
    borderColor: '#111417',
  },
  explanationBox: {
    flexDirection: 'row',
    gap: 8,
    backgroundColor: '#F0FDFA',
    borderRadius: 12,
    padding: 12,
    marginTop: 10,
    alignItems: 'center',
  },
  explanationText: {
    flex: 1,
    fontSize: 12,
    color: '#0E7490',
    lineHeight: 16,
    fontWeight: '500',
  },
});
