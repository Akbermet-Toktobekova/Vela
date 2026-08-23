import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
} from "react-native";
import { MicroLesson } from "../types";
import { colors } from "../theme/colors";
import { api } from "../services/api";

export const MicroLearningScreen: React.FC = () => {
  const [lesson, setLesson] = useState<MicroLesson | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);

  useEffect(() => {
    loadLesson();
  }, []);

  const loadLesson = async () => {
    const data = await api.getDailyLesson();
    setLesson(data);
  };

  if (!lesson) return null;

  const handleOptionSelect = (optionId: string) => {
    if (quizSubmitted) return;
    setSelectedOption(optionId);
  };

  const handleSubmitQuiz = () => {
    if (selectedOption) {
      setQuizSubmitted(true);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.categoryBadge}>
            <Text style={styles.categoryText}>{lesson.category}</Text>
          </View>
          <Text style={styles.streakText}>🔥 5 Day Streak</Text>
        </View>

        <Text style={styles.lessonTitle}>{lesson.title}</Text>
        <Text style={styles.readTime}>⏱️ {lesson.read_time_minutes} min daily bite</Text>

        {/* Content Card */}
        <View style={styles.contentCard}>
          <Text style={styles.bodyText}>{lesson.content}</Text>

          <View style={styles.takeawayBox}>
            <Text style={styles.takeawayHeader}>💡 Key Takeaway</Text>
            <Text style={styles.takeawayText}>{lesson.key_takeaway}</Text>
          </View>
        </View>

        {/* Interactive Quiz */}
        {lesson.quiz && (
          <View style={styles.quizCard}>
            <Text style={styles.quizHeader}>🧠 Knowledge Check</Text>
            <Text style={styles.quizQuestion}>{lesson.quiz.question}</Text>

            {lesson.quiz.options.map((option) => {
              const isSelected = selectedOption === option.id;
              let optionStyle = styles.optionButton;
              let textStyle = styles.optionText;

              if (quizSubmitted) {
                if (option.is_correct) {
                  optionStyle = styles.optionCorrect;
                  textStyle = styles.optionTextSuccess;
                } else if (isSelected && !option.is_correct) {
                  optionStyle = styles.optionIncorrect;
                  textStyle = styles.optionTextDanger;
                }
              } else if (isSelected) {
                optionStyle = styles.optionSelected;
              }

              return (
                <TouchableOpacity
                  key={option.id}
                  style={[styles.optionBase, optionStyle]}
                  onPress={() => handleOptionSelect(option.id)}
                  disabled={quizSubmitted}
                >
                  <Text style={[styles.optionBaseText, textStyle]}>{option.text}</Text>
                </TouchableOpacity>
              );
            })}

            {!quizSubmitted ? (
              <TouchableOpacity
                style={[
                  styles.submitButton,
                  !selectedOption && styles.submitButtonDisabled,
                ]}
                onPress={handleSubmitQuiz}
                disabled={!selectedOption}
              >
                <Text style={styles.submitButtonText}>Check Answer</Text>
              </TouchableOpacity>
            ) : (
              <View style={styles.explanationBox}>
                <Text style={styles.explanationTitle}>
                  {lesson.quiz.options.find((o) => o.id === selectedOption)?.is_correct
                    ? "🎉 Correct!"
                    : "💡 Explanation:"}
                </Text>
                <Text style={styles.explanationText}>{lesson.quiz.explanation}</Text>
              </View>
            )}
          </View>
        )}
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
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  categoryBadge: {
    backgroundColor: "#312E81",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  categoryText: {
    color: colors.primaryLight,
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase",
  },
  streakText: {
    color: "#F59E0B",
    fontSize: 13,
    fontWeight: "700",
  },
  lessonTitle: {
    fontSize: 22,
    fontWeight: "800",
    color: colors.textPrimary,
    lineHeight: 28,
    marginBottom: 6,
  },
  readTime: {
    fontSize: 12,
    color: colors.textMuted,
    marginBottom: 16,
  },
  contentCard: {
    backgroundColor: colors.cardBackground,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 16,
    padding: 18,
    marginBottom: 18,
  },
  bodyText: {
    fontSize: 15,
    lineHeight: 24,
    color: colors.textPrimary,
  },
  takeawayBox: {
    marginTop: 16,
    backgroundColor: "#064E3B",
    padding: 14,
    borderRadius: 10,
    borderLeftWidth: 4,
    borderLeftColor: colors.accent,
  },
  takeawayHeader: {
    fontSize: 13,
    fontWeight: "700",
    color: colors.accent,
    marginBottom: 4,
  },
  takeawayText: {
    fontSize: 13,
    color: "#D1FAE5",
    lineHeight: 18,
  },
  quizCard: {
    backgroundColor: colors.cardBackground,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 16,
    padding: 18,
  },
  quizHeader: {
    fontSize: 16,
    fontWeight: "800",
    color: colors.textPrimary,
    marginBottom: 8,
  },
  quizQuestion: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.textSecondary,
    marginBottom: 14,
    lineHeight: 20,
  },
  optionBase: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 10,
  },
  optionButton: {
    backgroundColor: colors.background,
    borderColor: colors.cardBorder,
  },
  optionSelected: {
    backgroundColor: "#312E81",
    borderColor: colors.primary,
  },
  optionCorrect: {
    backgroundColor: "#064E3B",
    borderColor: colors.accent,
  },
  optionIncorrect: {
    backgroundColor: "#7F1D1D",
    borderColor: colors.accentDanger,
  },
  optionBaseText: {
    fontSize: 14,
  },
  optionText: {
    color: colors.textPrimary,
  },
  optionTextSuccess: {
    color: "#D1FAE5",
    fontWeight: "700",
  },
  optionTextDanger: {
    color: "#FEE2E2",
    fontWeight: "700",
  },
  submitButton: {
    backgroundColor: colors.primary,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 6,
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
  },
  explanationBox: {
    marginTop: 14,
    padding: 12,
    backgroundColor: colors.background,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  explanationTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: colors.textPrimary,
    marginBottom: 4,
  },
  explanationText: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 18,
  },
});
