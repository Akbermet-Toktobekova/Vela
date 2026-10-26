import React, { useState } from 'react';
import { View } from 'react-native';
import { router, Href } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Chip, Copy, Loading, Notice, Row, Screen } from '../components/ui';
import { StateGate } from '../components/StateGate';
import { FinancialState, LessonsListView, LessonSummaryView, request } from '../lib/api';
import { space, usePalette } from '../theme';

type FilterMode = 'all' | 'recommended' | 'completed' | 'todo';

function formatActionTag(actionId: string): string {
  return actionId.replace(/_/g, ' ');
}

function LessonCard({lesson}: {lesson: LessonSummaryView}) {
  const p = usePalette();
  return (
    <Card soft={lesson.recommended_for_current_step}>
      <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: space.xs}}>
        <Copy variant="small" muted>
          {lesson.completed
            ? `Completed${lesson.completed_on ? ` · ${lesson.completed_on}` : ''}`
            : lesson.recommended_for_current_step
              ? 'Suggested for your current step'
              : '2 min read · 1 quick check'}
        </Copy>
        <Copy variant="small" color={lesson.completed ? p.accent : p.muted}>
          {lesson.completed ? 'Done ✓' : 'Unreviewed draft'}
        </Copy>
      </View>

      <Copy variant="title">{lesson.title}</Copy>
      <Copy muted>{lesson.summary}</Copy>

      <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs}}>
        {lesson.related_actions.map(action => (
          <View
            key={action}
            style={{
              paddingHorizontal: 8,
              paddingVertical: 3,
              borderRadius: 999,
              borderWidth: 0.5,
              borderColor: p.border,
              backgroundColor: p.surface,
            }}
          >
            <Copy variant="small" muted>{formatActionTag(action)}</Copy>
          </View>
        ))}
      </View>

      <Button
        label={lesson.completed ? 'Review lesson & quiz' : 'Read lesson'}
        small
        secondary={lesson.completed}
        onPress={() => router.push(`/learn/${lesson.id}` as Href)}
      />
    </Card>
  );
}

function LearnContent({state}: {state: FinancialState}) {
  const [filter, setFilter] = useState<FilterMode>('all');

  const lessonsQuery = useQuery({
    queryKey: ['lessons', state.revision],
    queryFn: () => request<LessonsListView>('/v1/lessons'),
  });

  if (lessonsQuery.isPending && !lessonsQuery.data) {
    return <Loading />;
  }

  if (lessonsQuery.error) {
    return <Notice>{lessonsQuery.error instanceof Error ? lessonsQuery.error.message : 'Could not load lessons.'}</Notice>;
  }

  const data = lessonsQuery.data;
  if (!data) return null;

  const primaryLesson = data.recommended_lesson;
  const filteredLessons = data.lessons.filter(item => {
    if (filter === 'recommended') return item.recommended_for_current_step;
    if (filter === 'completed') return item.completed;
    if (filter === 'todo') return !item.completed;
    return true;
  });

  return (
    <>
      {primaryLesson && (
        <Card soft>
          <Copy variant="small" muted>
            Contextual guide · matched to {formatActionTag(data.active_action_id)}
          </Copy>
          <Copy variant="title">Why this step: {primaryLesson.title}</Copy>
          <Copy muted>{primaryLesson.summary}</Copy>
          {!!data.active_recommendation_message && (
            <Notice>Current recommendation: {data.active_recommendation_message}</Notice>
          )}
          <Button
            label={primaryLesson.completed ? 'Review recommended lesson' : 'Open recommended lesson'}
            onPress={() => router.push(`/learn/${primaryLesson.id}` as Href)}
          />
          {data.recommended_lessons.length > 1 && (
            <View style={{gap: space.xs, paddingTop: space.xs}}>
              <Copy variant="small" muted>Also related to your current step:</Copy>
              <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs}}>
                {data.recommended_lessons
                  .filter(item => item.id !== primaryLesson.id)
                  .map(item => (
                    <Chip
                      key={item.id}
                      label={item.title}
                      active={item.completed}
                      onPress={() => router.push(`/learn/${item.id}` as Href)}
                    />
                  ))}
              </View>
            </View>
          )}
        </Card>
      )}

      <Card>
        <Copy variant="title">Learning progress</Copy>
        <Row
          label="Completed micro-lessons"
          value={`${data.completed_count} of ${data.total_count}`}
          bold
        />
        <Copy variant="small" muted>
          Short, calm guides on buffers, APR, repayment strategies, and cash flow. Progress is cleared if you erase your data in Settings.
        </Copy>
        <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs, paddingTop: space.xs}}>
          <Chip label={`All (${data.total_count})`} active={filter === 'all'} onPress={() => setFilter('all')} />
          <Chip
            label={`For current step (${data.recommended_lessons.length})`}
            active={filter === 'recommended'}
            onPress={() => setFilter('recommended')}
          />
          <Chip
            label={`To read (${data.total_count - data.completed_count})`}
            active={filter === 'todo'}
            onPress={() => setFilter('todo')}
          />
          <Chip
            label={`Completed (${data.completed_count})`}
            active={filter === 'completed'}
            onPress={() => setFilter('completed')}
          />
        </View>
      </Card>

      {filteredLessons.length === 0 ? (
        <Card>
          <Copy muted>No lessons match this filter yet.</Copy>
        </Card>
      ) : (
        filteredLessons.map(lesson => <LessonCard key={lesson.id} lesson={lesson} />)
      )}
    </>
  );
}

export default function LearnScreen() {
  return (
    <Screen title="Learn" eyebrow="Financial Essentials">
      <StateGate>{state => <LearnContent state={state} />}</StateGate>
    </Screen>
  );
}
