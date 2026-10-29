"""Journey E: Micro-lessons loader, contextual recommendation matching, and idempotent progress tracking (T18).

All lesson content is loaded from `content/lessons/index.json` and `content/lessons/*.md`.
Progress is stored inside the user's transactional `State` (`state.history`) so that `DELETE /v1/data`
erases all lesson progress alongside financial data.
"""

from datetime import date
import json
from pathlib import Path
import re
from typing import Annotated
from pydantic import Field

from .decision import evaluate_decision
from .domain import Record, State, recommendation

REPO_ROOT = Path(__file__).resolve().parents[3]
LESSONS_INDEX_PATH = REPO_ROOT / "content" / "lessons" / "index.json"


class LessonQuizView(Record):
    question: str = Field(min_length=1, max_length=400)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_index: Annotated[int, Field(strict=True, ge=0, le=5)]
    explanation: str = Field(min_length=1, max_length=600)


class LessonIndexEntry(Record):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=400)
    file: str = Field(min_length=1, max_length=200)
    related_actions: list[str] = Field(min_length=1)
    reviewed: bool = False
    quiz: LessonQuizView


class LessonSummaryView(Record):
    id: str
    title: str
    summary: str
    related_actions: list[str]
    reviewed: bool = False
    completed: bool = False
    selected_index: int | None = None
    correct: bool | None = None
    completed_on: date | None = None
    recommended_for_current_step: bool = False


class LessonDetailView(LessonSummaryView):
    body_markdown: str
    paragraphs: list[str] = Field(default_factory=list)
    quiz: LessonQuizView


class LessonsListView(Record):
    revision: int
    active_action_id: str
    active_recommendation_kind: str
    active_recommendation_message: str
    recommended_lesson: LessonSummaryView | None = None
    recommended_lessons: list[LessonSummaryView] = Field(default_factory=list)
    completed_count: int
    total_count: int
    lessons: list[LessonSummaryView]


class LessonProgressCommand(Record):
    revision: Annotated[int, Field(strict=True, ge=0)] | None = None
    selected_index: Annotated[int, Field(strict=True, ge=0, le=10)] | None = None
    completed: bool = True


def load_lessons_index(path: Path | None = None) -> list[LessonIndexEntry]:
    """Loads and validates `content/lessons/index.json`."""
    target = path or LESSONS_INDEX_PATH
    raw = json.loads(target.read_text(encoding="utf-8"))
    return [LessonIndexEntry.model_validate(item) for item in raw]


def _read_lesson_markdown(rel_path: str) -> tuple[str, list[str]]:
    """Reads a lesson markdown file, stripping YAML frontmatter and trailing Quick Check section."""
    full_path = (REPO_ROOT / rel_path).resolve()
    if not full_path.exists():
        raise FileNotFoundError(f"Lesson file not found: {rel_path}")
    text = full_path.read_text(encoding="utf-8")
    # Strip YAML frontmatter
    without_fm = re.sub(r"(?s)\A---\r?\n.*?\r?\n---\r?\n*", "", text).strip()
    # Strip trailing Quick Check section (already structured in `quiz`)
    prose_part = re.split(r"\r?\n---\r?\n+\s*###\s+Quick Check\b", without_fm, maxsplit=1)[0].strip()

    paragraphs: list[str] = []
    for block in re.split(r"\r?\n\s*\r?\n", prose_part):
        cleaned = block.strip()
        if not cleaned or cleaned.startswith("# "):
            continue
        paragraphs.append(cleaned)

    body_markdown = "\n\n".join(paragraphs) if paragraphs else prose_part
    return body_markdown, paragraphs


def extract_lesson_progress(state: State) -> dict[str, dict]:
    """Extracts the latest progress dictionary per `lesson_id` from `state.history`."""
    progress: dict[str, dict] = {}
    for entry in state.history:
        if isinstance(entry, dict) and entry.get("event") == "lesson_progress":
            lid = entry.get("lesson_id")
            if isinstance(lid, str) and lid:
                progress[lid] = entry
    return progress


def resolve_contextual_action_id(
    state: State,
    today: date,
    explicit_action_id: str | None = None,
) -> tuple[str, str, str]:
    """Determines the active catalogue `action_id` and recommendation summary for contextual lesson matching."""
    if state.personal.planning.active:
        from .planning import planning_view
        facts = planning_view(state, today)
        kind = facts.recommendation_kind
        action = {'clarify': 'clarify_material_unknown', 'shortfall': 'external_assistance_shortfall',
                  'save': 'contribute_savings_goal'}.get(kind, 'maintain_current_plan')
        return explicit_action_id or action, kind, facts.message
    rec = recommendation(state, today)
    rec_kind = str(rec.get("kind", "maintain"))
    rec_msg = str(rec.get("message", ""))

    if explicit_action_id:
        return explicit_action_id, rec_kind, rec_msg

    decision = evaluate_decision(state, today)
    if rec_kind == "clarify":
        return "clarify_material_unknown", rec_kind, rec_msg
    if rec_kind == "shortfall":
        if decision.selected_action_id in ("pause_optional_allocation", "external_assistance_shortfall"):
            return decision.selected_action_id, rec_kind, rec_msg
        return "external_assistance_shortfall", rec_kind, rec_msg
    if decision.selected_action_id != "maintain_current_plan":
        return decision.selected_action_id, rec_kind, rec_msg
    if rec_kind == "save":
        return "contribute_savings_goal", rec_kind, rec_msg
    return "maintain_current_plan", rec_kind, rec_msg


def _build_summary(
    entry: LessonIndexEntry,
    progress_map: dict[str, dict],
    active_action_id: str,
) -> LessonSummaryView:
    prog = progress_map.get(entry.id)
    completed = bool(prog.get("completed", False)) if prog else False
    selected_index = prog.get("selected_index") if prog else None
    correct = prog.get("correct") if prog else None
    completed_on_raw = prog.get("completed_on") if prog else None
    completed_on = date.fromisoformat(completed_on_raw) if isinstance(completed_on_raw, str) else None

    return LessonSummaryView(
        id=entry.id,
        title=entry.title,
        summary=entry.summary,
        related_actions=list(entry.related_actions),
        reviewed=entry.reviewed,
        completed=completed,
        selected_index=selected_index,
        correct=correct,
        completed_on=completed_on,
        recommended_for_current_step=(active_action_id in entry.related_actions),
    )


def list_lessons(
    state: State,
    today: date,
    action_id: str | None = None,
    index_path: Path | None = None,
) -> LessonsListView:
    """Returns all lessons with user progress and contextual recommendations for the current step."""
    entries = load_lessons_index(index_path)
    progress_map = extract_lesson_progress(state)
    active_action_id, rec_kind, rec_msg = resolve_contextual_action_id(state, today, explicit_action_id=action_id)

    summaries = [_build_summary(item, progress_map, active_action_id) for item in entries]
    recommended_list = [item for item in summaries if item.recommended_for_current_step]
    if not recommended_list and summaries:
        # Fallback to maintain_current_plan lessons if an unrecognized action_id was passed
        recommended_list = [item for item in summaries if "maintain_current_plan" in item.related_actions]

    primary_recommended: LessonSummaryView | None = None
    if recommended_list:
        uncompleted = [item for item in recommended_list if not item.completed]
        primary_recommended = uncompleted[0] if uncompleted else recommended_list[0]

    completed_count = sum(1 for item in summaries if item.completed)

    return LessonsListView(
        revision=state.revision,
        active_action_id=active_action_id,
        active_recommendation_kind=rec_kind,
        active_recommendation_message=rec_msg,
        recommended_lesson=primary_recommended,
        recommended_lessons=recommended_list,
        completed_count=completed_count,
        total_count=len(summaries),
        lessons=summaries,
    )


def get_lesson_detail(
    lesson_id: str,
    state: State,
    today: date,
    index_path: Path | None = None,
) -> LessonDetailView:
    """Returns full content, quiz, and progress for a single lesson, or raises KeyError if not found."""
    entries = load_lessons_index(index_path)
    entry = next((item for item in entries if item.id == lesson_id), None)
    if entry is None:
        raise KeyError(f"Lesson '{lesson_id}' not found.")

    progress_map = extract_lesson_progress(state)
    active_action_id, _, _ = resolve_contextual_action_id(state, today)
    summary = _build_summary(entry, progress_map, active_action_id)
    body_markdown, paragraphs = _read_lesson_markdown(entry.file)

    return LessonDetailView(
        **summary.model_dump(),
        body_markdown=body_markdown,
        paragraphs=paragraphs,
        quiz=entry.quiz,
    )


def record_lesson_progress(
    state: State,
    lesson_id: str,
    today: date,
    selected_index: int | None = None,
    completed: bool = True,
    index_path: Path | None = None,
) -> dict:
    """Idempotently records or updates lesson progress inside `state.history`."""
    entries = load_lessons_index(index_path)
    entry = next((item for item in entries if item.id == lesson_id), None)
    if entry is None:
        raise KeyError(f"Lesson '{lesson_id}' not found.")

    if selected_index is not None:
        if selected_index < 0 or selected_index >= len(entry.quiz.options):
            raise ValueError("Selected quiz option is out of range.")
        correct: bool | None = selected_index == entry.quiz.correct_index
    else:
        correct = None

    record = {
        "event": "lesson_progress",
        "lesson_id": lesson_id,
        "completed": completed,
        "selected_index": selected_index,
        "correct": correct,
        "completed_on": today.isoformat() if completed else None,
    }

    # Update in place if an entry for this lesson_id already exists so state.history stays compact and idempotent
    for idx, item in enumerate(state.history):
        if isinstance(item, dict) and item.get("event") == "lesson_progress" and item.get("lesson_id") == lesson_id:
            state.history[idx] = record
            return record

    state.history.append(record)
    return record
