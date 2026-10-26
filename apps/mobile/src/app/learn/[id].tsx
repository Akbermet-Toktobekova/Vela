import React, { useEffect, useState } from 'react';
import { Pressable, View } from 'react-native';
import { router, useLocalSearchParams, Href } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Copy, Loading, Notice, Row, Screen } from '../../components/ui';
import { StateGate } from '../../components/StateGate';
import { FinancialState, LessonDetailView, LessonProgressCommand, request } from '../../lib/api';
import { radius, space, usePalette } from '../../theme';

function formatActionTag(actionId: string): string {
  return actionId.replace(/_/g, ' ');
}

function LessonDetailContent({lessonId, state}: {lessonId: string; state: FinancialState}) {
  const p = usePalette();
  const cache = useQueryClient();
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [submitError, setSubmitError] = useState('');

  const detailQuery = useQuery({
    queryKey: ['lesson', lessonId, state.revision],
    queryFn: () => request<LessonDetailView>(`/v1/lessons/${encodeURIComponent(lessonId)}`),
    enabled: !!lessonId,
  });

  useEffect(() => {
    if (detailQuery.data && detailQuery.data.selected_index !== null && selectedIdx === null) {
      setSelectedIdx(detailQuery.data.selected_index);
    }
  }, [detailQuery.data, selectedIdx]);

  const progressMutation = useMutation({
    mutationFn: (payload: LessonProgressCommand) => {
      const idemKey = `lesson-prog-${lessonId}-rev${state.revision}-opt${payload.selected_index ?? 'none'}-${payload.completed ? 1 : 0}`;
      return request<LessonDetailView>(
        `/v1/lessons/${encodeURIComponent(lessonId)}/progress`,
        'POST',
        payload,
        idemKey,
      );
    },
    onSuccess: updated => {
      setSubmitError('');
      cache.setQueryData(['lesson', lessonId, state.revision], updated);
      cache.invalidateQueries({queryKey: ['lessons']});
      cache.invalidateQueries({queryKey: ['state']});
    },
    onError: err => {
      setSubmitError(err instanceof Error ? err.message : 'Could not save lesson progress.');
    },
  });

  if (detailQuery.isPending && !detailQuery.data) {
    return <Loading />;
  }

  if (detailQuery.error || !detailQuery.data) {
    return (
      <Card>
        <Notice>{detailQuery.error instanceof Error ? detailQuery.error.message : 'Lesson not found.'}</Notice>
        <Button label="Back to lessons" secondary onPress={() => router.push('/learn' as Href)} />
      </Card>
    );
  }

  const lesson = progressMutation.data ?? detailQuery.data;
  const activeSelection = selectedIdx ?? lesson.selected_index;
  const hasSubmitted = lesson.completed || progressMutation.isSuccess;
  const isSelectedCorrect = activeSelection !== null && activeSelection === lesson.quiz.correct_index;

  function submitQuiz() {
    if (activeSelection === null) {
      setSubmitError('Select an answer option first.');
      return;
    }
    setSubmitError('');
    progressMutation.mutate({
      revision: state.revision,
      selected_index: activeSelection,
      completed: true,
    });
  }

  return (
    <>
      <Card soft={lesson.recommended_for_current_step}>
        <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: space.xs}}>
          <Copy variant="small" muted>
            {lesson.recommended_for_current_step ? 'Suggested for your current step' : 'Micro-lesson'}
          </Copy>
          <Copy variant="small" color={lesson.completed ? p.accent : p.muted}>
            {lesson.completed ? `Completed ✓${lesson.completed_on ? ` (${lesson.completed_on})` : ''}` : 'In progress'}
          </Copy>
        </View>

        <Copy variant="title">{lesson.title}</Copy>
        <Copy muted>{lesson.summary}</Copy>

        <Row
          label="Editorial review status"
          value={lesson.reviewed ? 'Reviewed' : 'Synthetic draft (unreviewed)'}
        />
        <Row
          label="Related plan steps"
          value={lesson.related_actions.map(formatActionTag).join(', ')}
        />
      </Card>

      <Card>
        {lesson.paragraphs.map((paragraph, index) => (
          <Copy key={index}>{paragraph}</Copy>
        ))}
        <Copy variant="small" muted>
          Educational content only. Vela does not provide investment, tax, or legal advice, and all EUR examples are synthetic.
        </Copy>
      </Card>

      <Card>
        <Copy variant="small" muted>Quick Check</Copy>
        <Copy variant="title">{lesson.quiz.question}</Copy>

        <View style={{gap: space.xs, paddingVertical: space.xs}}>
          {lesson.quiz.options.map((optionText, idx) => {
            const chosen = activeSelection === idx;
            const showCorrectHighlight = hasSubmitted && idx === lesson.quiz.correct_index;
            return (
              <Pressable
                key={idx}
                accessibilityRole="button"
                onPress={() => setSelectedIdx(idx)}
                style={{
                  padding: space.sm,
                  borderRadius: radius.button,
                  borderWidth: chosen || showCorrectHighlight ? 1.5 : 1,
                  borderColor: showCorrectHighlight ? p.accent : chosen ? p.text : p.border,
                  backgroundColor: chosen ? p.soft : p.surface,
                  gap: 4,
                }}
              >
                <Copy variant="small" muted>Option {idx + 1}{showCorrectHighlight ? ' · Correct answer' : ''}</Copy>
                <Copy>{optionText}</Copy>
              </Pressable>
            );
          })}
        </View>

        {submitError ? <Notice>{submitError}</Notice> : null}

        {hasSubmitted && activeSelection !== null && (
          <Notice>
            {isSelectedCorrect ? 'Correct. ' : 'Not quite — review the explanation below. '}
            {lesson.quiz.explanation}
          </Notice>
        )}

        <Button
          label={lesson.completed ? 'Save answer again (idempotent)' : 'Check answer & mark complete'}
          disabled={progressMutation.isPending || activeSelection === null}
          onPress={submitQuiz}
        />
      </Card>

      <Button label="Back to all lessons" secondary onPress={() => router.push('/learn' as Href)} />
    </>
  );
}

export default function LessonDetailScreen() {
  const params = useLocalSearchParams<{id?: string | string[]}>();
  const lessonId = Array.isArray(params.id) ? (params.id[0] ?? '') : (params.id ?? '');

  return (
    <Screen title="Lesson" eyebrow="Learn">
      <StateGate>{state => <LessonDetailContent lessonId={lessonId} state={state} />}</StateGate>
    </Screen>
  );
}
