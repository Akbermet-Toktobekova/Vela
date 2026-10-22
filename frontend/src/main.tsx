import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowUpRight,
  ArrowRight,
  Check,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Home,
  Leaf,
  MessageCircle,
  MoreHorizontal,
  Moon,
  Plus,
  Send,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Sun,
  Upload,
  Wallet,
  X,
  BookOpen,
  Play,
  Pause,
  RefreshCw,
} from "lucide-react";
import { api, label, money, Today, Profile, Rec, Rule } from "./api";
import "./styles.css";

export function App() {
  const [data, setData] = useState<Today | null>(null),
    [tab, setTab] = useState("Today"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [dark, setDark] = useState(false),
    [modal, setModal] = useState<"adjust" | "profile" | "import" | null>(null),
    [notice, setNotice] = useState(""),
    [noProfile, setNoProfile] = useState(false);
  async function load() {
    try {
      setData(await api<Today>("/today"));
      setNoProfile(false);
    } catch (e) {
      setNoProfile(true);
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void load();
  }, [tab]);
  useEffect(() => {
    if (!modal) return;
    const previous = document.activeElement as HTMLElement | null;
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]');
    const nodes = () =>
      Array.from(
        dialog?.querySelectorAll<HTMLElement>(
          "button:not([disabled]),input,select,textarea,summary",
        ) || [],
      );
    nodes()[0]?.focus();
    function key(e: KeyboardEvent) {
      if (e.key === "Escape") setModal(null);
      if (e.key === "Tab") {
        const items = nodes(),
          first = items[0],
          last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    }
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      previous?.focus();
    };
  }, [modal]);
  async function act(action: () => Promise<unknown>, message = "") {
    setBusy(true);
    setError("");
    try {
      await action();
      await load();
      setNotice(message);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const p = data?.profile;
  const fmt = (n: number) => money(n, p?.currency);
  async function switchPersona(key: string) {
    await act(
      () => api("/demo/" + key, {}),
      "Synthetic profile loaded. Your demo starts on October 22.",
    );
  }
  async function decide(action: string, body: unknown = {}) {
    if (!data?.recommendation) return;
    await act(
      () =>
        api("/recommendations/" + data.recommendation!.id + "/" + action, body),
      action === "decline"
        ? "Noted. We’ll give this idea some space."
        : "Your plan is updated. Transfers run only in the simulation.",
    );
    setModal(null);
  }
  return (
    <div className={dark ? "app dark" : "app"}>
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setTab("Today");
          }}
        >
          <span className="brand-icon">
            <Leaf size={23} />
          </span>
          finagent<span className="brand-dot">.</span>
        </a>
        <div className="workspace-label">YOUR FINANCIAL SPACE</div>
        <nav aria-label="Main navigation">
          {[
            { name: "Today", icon: Home },
            { name: "Assistant", icon: MessageCircle },
            { name: "My Plan", icon: SlidersHorizontal },
          ].map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={tab === name ? "nav-item active" : "nav-item"}
              onClick={() => setTab(name)}
            >
              <Icon size={19} />
              {name}
              {name === "Assistant" && <span className="tiny">AI</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="private-note">
            <ShieldCheck size={19} />
            <div>
              <strong>Your space. Your pace.</strong>
              <p>
                {data?.provider === "anthropic"
                  ? "Anthropic explanations enabled."
                  : "Offline explanations. Local storage."}
              </p>
            </div>
          </div>
          <button className="theme-toggle" onClick={() => setDark(!dark)}>
            {dark ? <Sun size={17} /> : <Moon size={17} />}{" "}
            {dark ? "Light appearance" : "Dark appearance"}
          </button>
          <div className="user">
            <span className="avatar">{p?.name[0] || "F"}</span>
            <div>
              <strong>{p?.name || "Welcome"}</strong>
              <span>Personal workspace</span>
            </div>
            <MoreHorizontal size={19} />
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span className="breadcrumb">
            My workspace <ChevronRight size={14} />
            <strong>{tab}</strong>
          </span>
          <div className="top-actions">
            <span className="demo-badge">
              <span /> SIMULATION MODE
            </span>
            <label className="persona-select">
              <span className="sr-only">Demo persona</span>
              <select
                value={p?.id || ""}
                onChange={(e) => void switchPersona(e.target.value)}
                disabled={busy}
              >
                <option value="" disabled>
                  Choose a persona
                </option>
                <option value="P1">Maya · Student</option>
                <option value="P2">Alex · Professional</option>
                <option value="P3">Sam · Freelancer</option>
                <option value="P4">Jordan · Professional</option>
              </select>
              <ChevronDown size={14} />
            </label>
          </div>
        </header>
        <main>
          <div role="status" aria-live="polite">
            {notice && (
              <div className="notice">
                {notice}
                <button
                  aria-label="Dismiss message"
                  onClick={() => setNotice("")}
                >
                  <X size={16} />
                </button>
              </div>
            )}
          </div>
          {error && (
            <div role="alert" className="notice attention">
              {error}
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {!data ? (
            <div className="welcome card">
              <Leaf size={40} />
              <h1>A little more breathing room.</h1>
              <p>
                Meet FinAgent. A calm place to explore your budget, debt, and
                savings.
              </p>
              <p>Choose a synthetic profile to try the complete simulation.</p>
              <div className="welcome-actions">
                {["P1", "P2", "P3", "P4"].map((id, i) => (
                  <button
                    className="button primary"
                    key={id}
                    disabled={busy}
                    onClick={() => void switchPersona(id)}
                  >
                    {
                      [
                        "Maya · Student",
                        "Alex · Debt payoff",
                        "Sam · Safety net",
                        "Jordan · Budget",
                      ][i]
                    }{" "}
                    <ArrowRight size={16} />
                  </button>
                ))}
              </div>
              {!noProfile && <p>Loading your space…</p>}
            </div>
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">
                    {tab === "Today"
                      ? new Date(data.date + "T12:00:00").toLocaleDateString(
                          "en-US",
                          {
                            weekday: "long",
                            month: "long",
                            day: "numeric",
                            year: "numeric",
                          },
                        )
                      : "A LITTLE CLARITY GOES A LONG WAY"}
                  </div>
                  <h1>
                    {tab === "Today"
                      ? `Good morning, ${p!.name}.`
                      : tab === "Assistant"
                        ? "Let’s think it through."
                        : "A plan that feels like you."}
                  </h1>
                  <p>
                    {tab === "Today"
                      ? "Small steps today. More possibilities tomorrow."
                      : tab === "Assistant"
                        ? "Ask a question. Explore an option. You’re always in control."
                        : "Your priorities, your boundaries, your next steps."}
                  </p>
                </div>
                {tab === "Today" && (
                  <button
                    className="button subtle"
                    disabled={busy}
                    onClick={() =>
                      void act(
                        () => api("/replay/advance", { days: 7 }),
                        "Advanced the synthetic clock by one week.",
                      )
                    }
                  >
                    <Play size={15} /> Replay a week
                  </button>
                )}
              </div>
              {tab === "Today" && (
                <div className="dashboard">
                  <div className="main-column">
                    <section className="cash-card card">
                      <div className="section-label">
                        <span>
                          <Wallet size={17} /> YOUR EVERYDAY MONEY
                        </span>
                        <CircleHelp size={16} />
                      </div>
                      <div className="cash-title">Safe to spend today</div>
                      <div className="hero-number">
                        {fmt(data.overview.safe_to_spend).split(".")[0]}
                        <span>
                          .
                          {fmt(data.overview.safe_to_spend).split(".")[1] ||
                            "00"}
                        </span>
                      </div>
                      <div className="calm-caption">
                        <span className="status-dot" />
                        {data.guard
                          ? "Let’s make a little space for your essentials."
                          : "Your essentials and cash buffer are accounted for."}
                      </div>
                      <div className="cash-divider" />
                      <div className="cash-details">
                        <div>
                          <span>Available cash</span>
                          <strong>{fmt(p!.cash_balance)}</strong>
                        </div>
                        <div>
                          <span>Upcoming commitments</span>
                          <strong>{fmt(data.overview.reserved)}</strong>
                        </div>
                        <div>
                          <span>Your protected buffer</span>
                          <strong>{fmt(p!.min_cash_buffer)}</strong>
                        </div>
                      </div>
                      <div className="contour c1" />
                      <div className="contour c2" />
                      <div className="contour c3" />
                    </section>
                    {data.guard ? (
                      <section className="card recommendation">
                        <div className="section-label">
                          <ShieldCheck size={18} /> A LITTLE BREATHING ROOM
                        </div>
                        <h2>Let’s pause the next steps.</h2>
                        <p>{data.guard.reason}</p>
                        <p>
                          Coaching is paused until{" "}
                          {new Date(data.guard.until).toLocaleString()}. Your
                          overview and plan are still here.
                        </p>
                      </section>
                    ) : data.recommendation ? (
                      <Recommendation
                        rec={data.recommendation}
                        fmt={fmt}
                        busy={busy}
                        decide={decide}
                        adjust={() => setModal("adjust")}
                        why={() => setTab("Assistant")}
                      />
                    ) : (
                      <section className="card">
                        <h2>A quiet day for your plan.</h2>
                        <p>
                          There’s no new action right now. We’ll reassess when
                          the next daily window opens.
                        </p>
                        <button
                          className="button"
                          onClick={() =>
                            void act(() => api("/recommendations/refresh", {}))
                          }
                        >
                          <RefreshCw size={16} /> Check my plan
                        </button>
                      </section>
                    )}
                    <div className="transparency">
                      <ShieldCheck size={17} />
                      <p>
                        Calculated with care. Every figure comes from your plan.
                        <br />
                        <span>You decide what happens next.</span>
                      </p>
                    </div>
                  </div>
                  <div className="side-column">
                    <section className="card cushion">
                      <div className="section-label">
                        <span className="icon-square">
                          <Leaf size={19} />
                        </span>{" "}
                        A SOFTER LANDING
                      </div>
                      <h2>Your safety net</h2>
                      <div className="cushion-number">
                        {fmt(data.overview.emergency_saved)}
                      </div>
                      <p>
                        {data.overview.cushion_months} months of essential
                        costs, set aside.
                      </p>
                      <progress
                        aria-label="Emergency fund progress"
                        value={data.overview.emergency_saved}
                        max={Math.max(1, data.overview.emergency_target)}
                      />
                      <div className="progress-labels">
                        <span>Current savings</span>
                        <span>{fmt(data.overview.emergency_target)} goal</span>
                      </div>
                      <div className="soft-panel">
                        <Leaf size={16} />
                        <span>
                          Aim for {p!.emergency_months} months of essential
                          costs, one small contribution at a time.
                        </span>
                      </div>
                      <button
                        className="text-button"
                        onClick={() => setTab("My Plan")}
                      >
                        View your savings plan <ArrowUpRight size={17} />
                      </button>
                    </section>
                    {data.lesson && (
                      <section className="card lesson">
                        <div className="section-label">
                          <BookOpen size={17} /> A MINUTE FOR YOUR MONEY{" "}
                          <span className="new-badge">DAILY</span>
                        </div>
                        <h2>{data.lesson.title}</h2>
                        <p>
                          {data.lesson.body.split(". ").slice(0, 2).join(". ")}.
                        </p>
                        <details>
                          <summary>
                            Learn something small <ArrowRight size={16} />
                          </summary>
                          <p>{data.lesson.body}</p>
                          <strong>{data.lesson.question}</strong>
                          <div className="quiz">
                            {data.lesson.options.map((option, index) => (
                              <button
                                disabled={data.lesson!.answered || busy}
                                key={option}
                                className="button"
                                onClick={() =>
                                  void act(() =>
                                    api(
                                      "/lessons/" + data.lesson!.id + "/answer",
                                      { answer: index },
                                    ),
                                  )
                                }
                              >
                                {option}
                              </button>
                            ))}
                          </div>
                          {data.lesson.answered && (
                            <p role="status">
                              {data.lesson.correct
                                ? "That’s right."
                                : "A useful thing to remember:"}{" "}
                              {data.lesson.explanation}
                            </p>
                          )}
                        </details>
                      </section>
                    )}
                    <section className="assistant-nudge">
                      <span className="icon-square">
                        <Sparkles size={20} />
                      </span>
                      <div>
                        <strong>Have a “what if” in mind?</strong>
                        <p>We can work through it together.</p>
                        <button
                          className="text-button"
                          onClick={() => setTab("Assistant")}
                        >
                          Ask your assistant <ArrowRight size={16} />
                        </button>
                      </div>
                    </section>
                  </div>
                </div>
              )}
              {tab === "Assistant" && <Assistant fmt={fmt} />}
              {tab === "My Plan" && (
                <div className="plan-grid">
                  <section className="card">
                    <div className="card-title">
                      <h2>Your starting point</h2>
                      <button
                        className="button small"
                        onClick={() => setModal("profile")}
                      >
                        Edit plan
                      </button>
                    </div>
                    <dl className="profile-details">
                      <div>
                        <dt>Priority</dt>
                        <dd>{label(p!.priority)}</dd>
                      </div>
                      <div>
                        <dt>Monthly income</dt>
                        <dd>{fmt(p!.monthly_income)}</dd>
                      </div>
                      <div>
                        <dt>Protected buffer</dt>
                        <dd>{fmt(p!.min_cash_buffer)}</dd>
                      </div>
                      <div>
                        <dt>Income day</dt>
                        <dd>{p!.income_day}</dd>
                      </div>
                    </dl>
                    {data.goal_projection && (
                      <div className="goal-summary soft-panel">
                        <div>
                          <strong>{data.goal_projection.account}</strong>
                          <p>
                            {data.goal_projection.projected_date
                              ? `At your current contribution: ${new Date(data.goal_projection.projected_date + "T12:00:00").toLocaleDateString("en-US", { month: "long", year: "numeric" })}`
                              : "Choose a contribution to estimate your goal date."}
                          </p>
                          {data.goal_projection.target_date && (
                            <p>
                              Your target: {data.goal_projection.target_date}.{" "}
                              {data.goal_projection.on_schedule === false
                                ? "A smaller target, later date, or affordable contribution change may help."
                                : "Your estimate is within the chosen timeline."}
                            </p>
                          )}
                          {data.timeline_change && (
                            <p>
                              Plan update:{" "}
                              {data.timeline_change.before?.projected_date ||
                                "No estimated date"}{" "}
                              →{" "}
                              {data.timeline_change.after.projected_date ||
                                "No estimated date"}
                              .
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                    <h3>Debts & savings</h3>
                    {[...p!.debts, ...p!.savings].map((a) => (
                      <div className="account-row" key={a.name}>
                        <span>{a.name}</span>
                        <strong>{fmt(a.balance)}</strong>
                      </div>
                    ))}
                    <button
                      className="text-button"
                      onClick={() => setModal("import")}
                    >
                      <Upload size={16} /> Import a statement
                    </button>
                  </section>
                  <section className="card">
                    <h2>Let’s check a few things</h2>
                    <p>
                      Recurring patterns are suggestions until you confirm them.
                    </p>
                    {data.analysis.recurring.map((r) => (
                      <div className="assumption" key={r.merchant}>
                        <div>
                          <strong>{r.merchant}</strong>
                          <span>{fmt(r.amount)} / month</span>
                        </div>
                        <button
                          disabled={r.confirmed || busy}
                          className="button small"
                          onClick={() =>
                            void act(
                              () =>
                                api("/assumptions/confirm", {
                                  merchant: r.merchant,
                                }),
                              "Recurring cost added to your plan.",
                            )
                          }
                        >
                          {r.confirmed ? (
                            <>
                              <Check size={14} /> Confirmed
                            </>
                          ) : (
                            "Confirm"
                          )}
                        </button>
                      </div>
                    ))}
                  </section>
                  <section className="card full">
                    <div className="card-title">
                      <div>
                        <h2>Your everyday rules</h2>
                        <p>
                          Small actions, with your approval. Every transfer is
                          simulated.
                        </p>
                      </div>
                      <span className="badge">{data.rules.length} rules</span>
                    </div>
                    {!data.rules.length ? (
                      <div className="empty">
                        Accept a recommendation to create your first rule.
                      </div>
                    ) : (
                      data.rules.map((rule) => (
                        <RuleRow
                          key={rule.id}
                          rule={rule}
                          fmt={fmt}
                          busy={busy}
                          update={(body) =>
                            act(
                              () => api("/rules/" + rule.id, body, "PATCH"),
                              "Rule updated.",
                            )
                          }
                        />
                      ))
                    )}
                  </section>
                  <section className="card full">
                    <div className="card-title">
                      <h2>Your plan, as it unfolds</h2>
                      <span className="badge">HISTORY</span>
                    </div>
                    <History events={data.history} />
                  </section>
                  <section className="privacy-row full">
                    <span>
                      <ShieldCheck size={17} /> Local data. Simulated actions.
                      Always your choice.
                    </span>
                    <button
                      className="text-button"
                      onClick={() => {
                        if (
                          window.confirm(
                            "Delete this local profile, imported transactions, history, and cached explanations?",
                          )
                        )
                          void act(async () => {
                            await api("/data", undefined, "DELETE");
                            setData(null);
                          }, "Your local data has been deleted.");
                      }}
                    >
                      Delete my data
                    </button>
                  </section>
                </div>
              )}
              <footer>
                <span>
                  <Leaf size={14} /> Made for progress, at your pace.
                </span>
                <span>{data.disclaimer}</span>
              </footer>
            </>
          )}
        </main>
      </div>
      {modal && data && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
          <section
            role="dialog"
            aria-modal="true"
            aria-label={
              modal === "adjust"
                ? "Adjust recommendation"
                : modal === "profile"
                  ? "Edit profile"
                  : "Import statement"
            }
            className="modal card"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="modal-close"
              aria-label="Close dialog"
              onClick={() => setModal(null)}
            >
              <X size={21} />
            </button>
            {modal === "adjust" && (
              <Adjust
                rec={data.recommendation!}
                submit={(body) => decide("adjust", body)}
                busy={busy}
              />
            )}
            {modal === "profile" && (
              <ProfileForm
                profile={data.profile}
                busy={busy}
                save={async (profile) => {
                  await act(
                    () => api("/profile", profile, "PUT"),
                    "Your plan has been recalculated.",
                  );
                  setModal(null);
                }}
              />
            )}
            {modal === "import" && (
              <ImportForm
                submit={(body) =>
                  act(
                    () => api("/import/statement", body),
                    "Statement processed. Your current cash balance is unchanged; update it in your profile if needed.",
                  )
                }
                busy={busy}
              />
            )}
          </section>
        </div>
      )}
    </div>
  );
}
function Recommendation({
  rec,
  fmt,
  busy,
  decide,
  adjust,
  why,
}: {
  rec: Rec;
  fmt: (n: number) => string;
  busy: boolean;
  decide: (s: string, b?: unknown) => Promise<void>;
  adjust: () => void;
  why: () => void;
}) {
  const facts = rec.reason_facts;
  return (
    <section className="card recommendation">
      <div className="recommendation-top">
        <div className="section-label">
          <span className="icon-square">
            <Sparkles size={18} />
          </span>{" "}
          YOUR NEXT SMALL STEP
        </div>
        <span className="badge">FOR YOUR {rec.chosen.agent.toUpperCase()}</span>
      </div>
      <h2>{rec.chosen.title}</h2>
      <p>{rec.explanation_text}</p>
      <div className="impact-grid">
        <div>
          <span>Suggested amount</span>
          <strong>{fmt(facts.amount)}</strong>
          <small>
            {rec.chosen.type === "weekend_habit"
              ? "per matching transaction"
              : "per month"}
          </small>
        </div>
        <div>
          <span>
            {facts.interest_saved !== undefined
              ? "Interest you could save"
              : "Cash buffer after"}
          </span>
          <strong>{fmt(facts.interest_saved ?? facts.buffer_after)}</strong>
          <small>
            {facts.months_saved
              ? `${facts.months_saved} months sooner`
              : "your essentials stay protected"}
          </small>
        </div>
      </div>
      <div className="alternative">
        <span className="alternative-icon">↗</span>
        <div>
          <strong>Another path we considered</strong>
          <p>{rec.alternative}</p>
          <small>{rec.alternative_reason}</small>
        </div>
      </div>
      {rec.status === "pending" ? (
        <div className="recommendation-actions">
          <button
            className="button primary"
            disabled={busy}
            onClick={() => void decide("accept")}
          >
            <Check size={16} /> Let’s do this
          </button>
          <button className="button" onClick={adjust} disabled={busy}>
            Adjust
          </button>
          <button
            className="text-button"
            disabled={busy}
            onClick={() => void decide("decline")}
          >
            Not now
          </button>
        </div>
      ) : (
        <div className="decision-state">
          <Check size={17} />
          {rec.status === "superseded"
            ? "Your plan changed. A fresh recommendation can arrive in the next daily window."
            : `Recommendation ${rec.status}. You’re in control of what comes next.`}
        </div>
      )}
      <div className="recommendation-foot">
        <button onClick={why}>
          <MessageCircle size={15} /> Why this step?
        </button>
        <details>
          <summary>
            See the calculation <ChevronDown size={13} />
          </summary>
          <dl className="fact-list">
            {Object.entries(facts).map(([k, v]) => (
              <div key={k}>
                <dt>{label(k)}</dt>
                <dd>{/months|services|transactions/.test(k) ? v : fmt(v)}</dd>
              </div>
            ))}
          </dl>
          <p>{rec.do_nothing}</p>
        </details>
      </div>
    </section>
  );
}
function Adjust({
  rec,
  submit,
  busy,
}: {
  rec: Rec;
  submit: (b: unknown) => Promise<void>;
  busy: boolean;
}) {
  const [amount, setAmount] = useState(
      (rec.chosen.params.amount / 100).toFixed(2),
    ),
    [day, setDay] = useState(rec.chosen.params.schedule_day);
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void submit({
          amount: Math.round(Number(amount) * 100),
          schedule_day: day,
        });
      }}
    >
      <div className="eyebrow">MAKE IT YOURS</div>
      <h2>A step that fits.</h2>
      <p>We’ll check the new amount against your cash buffer before saving.</p>
      <label>
        Amount in major currency units
        <input
          autoFocus
          required
          type="number"
          min="0"
          step="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </label>
      <label>
        Scheduled day of month
        <input
          required
          type="number"
          min="1"
          max="28"
          value={day}
          onChange={(e) => setDay(Number(e.target.value))}
        />
      </label>
      <button className="button primary" disabled={busy}>
        Check & save adjustment <ArrowRight size={16} />
      </button>
    </form>
  );
}
function Assistant({ fmt }: { fmt: (n: number) => string }) {
  const [input, setInput] = useState(""),
    [busy, setBusy] = useState(false),
    [messages, setMessages] = useState<
      {
        role: string;
        text: string;
        facts?: Record<string, unknown>;
        tools?: string[];
      }[]
    >([]);
  async function send(text: string) {
    if (!text.trim() || busy) return;
    setMessages((old) => [...old, { role: "user", text }]);
    setInput("");
    setBusy(true);
    try {
      const reply = await api<{
        text: string;
        facts: Record<string, unknown>;
        tools: string[];
      }>("/assistant/messages", { message: text });
      setMessages((old) => [...old, { role: "assistant", ...reply }]);
    } catch (e) {
      setMessages((old) => [
        ...old,
        { role: "assistant", text: (e as Error).message },
      ]);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="chat card">
      <div className="chat-header">
        <span className="icon-square">
          <Sparkles size={21} />
        </span>
        <div>
          <strong>Your financial thinking partner</strong>
          <span>Grounded in your plan. Guided by you.</span>
        </div>
        <span className="badge">PRIVATE</span>
      </div>
      <div className="messages" aria-live="polite">
        {!messages.length && (
          <div className="chat-welcome">
            <div className="large-leaf">
              <Leaf size={34} />
            </div>
            <h2>A question is a good place to start.</h2>
            <p>
              I can explain your next step, explore a different payment,
              <br />
              or help you understand your own numbers.
            </p>
            <div className="suggestions">
              {[
                "Why this recommendation?",
                "What if I pay $50 more toward debt?",
                "What if my income decreases by 10%?",
                "What if I save $25 more?",
                "Confirm Spotify is a recurring cost",
              ].map((prompt) => (
                <button key={prompt} onClick={() => void send(prompt)}>
                  {prompt}
                  <ArrowUpRight size={15} />
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={"message " + m.role}>
            <span className="message-label">
              {m.role === "user" ? "You" : "FinAgent"}
            </span>
            <p>{m.text}</p>
            {m.facts && (
              <dl className="fact-list">
                {Object.entries(m.facts)
                  .filter(
                    ([, v]) => typeof v === "number" || typeof v === "string",
                  )
                  .map(([k, v]) => (
                    <div key={k}>
                      <dt>{label(k)}</dt>
                      <dd>
                        {typeof v === "number"
                          ? /months/.test(k)
                            ? v
                            : fmt(v)
                          : String(v)}
                      </dd>
                    </div>
                  ))}
              </dl>
            )}
            {m.tools && (
              <small>Calculated with: {m.tools.map(label).join(" · ")}</small>
            )}
          </div>
        ))}
        {busy && <p>Looking at your plan…</p>}
      </div>
      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault();
          void send(input);
        }}
      >
        <input
          aria-label="Message your assistant"
          placeholder="What’s on your mind?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={2000}
        />
        <button
          className="button primary"
          aria-label="Send message"
          disabled={busy || !input.trim()}
        >
          <Send size={19} />
        </button>
      </form>
      <p className="chat-disclaimer">
        Educational guidance only. Scenarios don’t change your plan.
      </p>
    </section>
  );
}
function RuleRow({
  rule,
  fmt,
  busy,
  update,
}: {
  rule: Rule;
  fmt: (n: number) => string;
  busy: boolean;
  update: (body: unknown) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false),
    [amount, setAmount] = useState(String(rule.amount / 100));
  return (
    <div className="rule-row">
      <span className="icon-square">
        <RefreshCw size={18} />
      </span>
      <div>
        <strong>{rule.name}</strong>
        <p>
          {fmt(rule.amount)} → {rule.account} ·{" "}
          {rule.trigger.kind === "schedule" ? "day " : ""}
          {rule.trigger.value} · {rule.status}
        </p>
        {editing && (
          <form
            className="inline-form"
            onSubmit={(e) => {
              e.preventDefault();
              void update({ amount: Math.round(Number(amount) * 100) }).then(
                () => setEditing(false),
              );
            }}
          >
            <input
              aria-label="Rule amount"
              type="number"
              step="0.01"
              min="0.01"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
            <button className="button small">Save</button>
          </form>
        )}
      </div>
      <button className="button small" onClick={() => setEditing(!editing)}>
        Edit
      </button>
      <button
        className="button small"
        disabled={busy}
        onClick={() =>
          void update({
            status: rule.status === "active" ? "paused" : "active",
          })
        }
      >
        {rule.status === "active" ? <Pause size={14} /> : <Play size={14} />}{" "}
        {rule.status === "active" ? "Pause" : "Resume"}
      </button>
    </div>
  );
}
function History({ events }: { events: Today["history"] }) {
  const [filter, setFilter] = useState("all");
  return (
    <>
      <label className="filter">
        Show
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All activity</option>
          {[
            "recommendation",
            "decision",
            "plan_change",
            "rule_run",
            "guard_suppression",
            "lesson_completed",
          ].map((x) => (
            <option key={x} value={x}>
              {label(x)}
            </option>
          ))}
        </select>
      </label>
      <div className="timeline">
        {events
          .filter((e) => filter === "all" || e.type === filter)
          .map((e) => (
            <div className="timeline-item" key={e.id}>
              <span className="timeline-dot" />
              <div>
                <strong>{label(e.type)}</strong>
                <p>
                  {String(
                    e.payload.title ||
                      e.payload.reason ||
                      e.payload.status ||
                      e.payload.outcome ||
                      "Your plan was updated",
                  )}
                </p>
              </div>
              <time>
                {new Date(e.timestamp).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                })}
              </time>
            </div>
          ))}
      </div>
    </>
  );
}
function ProfileForm({
  profile,
  save,
  busy,
}: {
  profile: Profile;
  save: (p: Profile) => Promise<void>;
  busy: boolean;
}) {
  const [p, setP] = useState(structuredClone(profile));
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void save(p);
      }}
    >
      <div className="eyebrow">YOUR STARTING POINT</div>
      <h2>Edit your plan</h2>
      <div className="form-grid">
        <label>
          Name
          <input
            required
            value={p.name}
            onChange={(e) => setP({ ...p, name: e.target.value })}
          />
        </label>
        <label>
          Priority
          <select
            value={p.priority}
            onChange={(e) => setP({ ...p, priority: e.target.value })}
          >
            <option value="debt">Debt</option>
            <option value="savings">Savings</option>
            <option value="budget">Budget</option>
          </select>
        </label>
        {(["monthly_income", "cash_balance", "min_cash_buffer"] as const).map(
          (k) => (
            <label key={k}>
              {label(k)}
              <input
                required
                type="number"
                min="0"
                step="0.01"
                value={p[k] / 100}
                onChange={(e) =>
                  setP({ ...p, [k]: Math.round(Number(e.target.value) * 100) })
                }
              />
            </label>
          ),
        )}
        <label>
          Income day
          <input
            type="number"
            required
            min="1"
            max="28"
            value={p.income_day}
            onChange={(e) => setP({ ...p, income_day: Number(e.target.value) })}
          />
        </label>
        <label>
          Auto-save %
          <input
            required
            type="number"
            min="0"
            max="10"
            value={p.auto_save_pct}
            onChange={(e) =>
              setP({ ...p, auto_save_pct: Number(e.target.value) })
            }
          />
        </label>
        <label>
          Emergency target (months)
          <input
            type="number"
            required
            min="1"
            max="12"
            value={p.emergency_months}
            onChange={(e) =>
              setP({ ...p, emergency_months: Number(e.target.value) })
            }
          />
        </label>
      </div>
      <h3>Fixed costs</h3>
      {p.fixed_costs.map((c, i) => (
        <div className="editable-row" key={i}>
          <input
            aria-label="Cost name"
            required
            value={c.name}
            onChange={(e) => {
              const costs = [...p.fixed_costs];
              costs[i] = { ...c, name: e.target.value };
              setP({ ...p, fixed_costs: costs });
            }}
          />
          <input
            aria-label="Cost amount"
            required
            type="number"
            min="0"
            step="0.01"
            value={c.amount / 100}
            onChange={(e) => {
              const costs = [...p.fixed_costs];
              costs[i] = {
                ...c,
                amount: Math.round(Number(e.target.value) * 100),
              };
              setP({ ...p, fixed_costs: costs });
            }}
          />
          <input
            aria-label="Cost due day"
            required
            type="number"
            min="1"
            max="28"
            value={c.due_day}
            onChange={(e) => {
              const costs = [...p.fixed_costs];
              costs[i] = { ...c, due_day: Number(e.target.value) };
              setP({ ...p, fixed_costs: costs });
            }}
          />
          <button
            type="button"
            aria-label={"Remove " + c.name}
            onClick={() =>
              setP({
                ...p,
                fixed_costs: p.fixed_costs.filter((_, j) => j !== i),
              })
            }
          >
            <X size={16} />
          </button>
        </div>
      ))}
      <button
        type="button"
        className="text-button"
        onClick={() =>
          setP({
            ...p,
            fixed_costs: [
              ...p.fixed_costs,
              { name: "New cost", amount: 0, due_day: 1, category: "bills" },
            ],
          })
        }
      >
        <Plus size={16} /> Add cost
      </button>
      <h3>Debts</h3>
      {p.debts.map((d, i) => (
        <div className="editable-row debt" key={i}>
          {(["name", "balance", "annual_rate", "min_payment"] as const).map(
            (k) => (
              <label key={k}>
                {label(k)}
                <input
                  required
                  type={k === "name" ? "text" : "number"}
                  min="0"
                  max={k === "annual_rate" ? 100 : undefined}
                  step="0.01"
                  value={
                    k === "balance" || k === "min_payment" ? d[k] / 100 : d[k]
                  }
                  onChange={(e) => {
                    const debts = [...p.debts];
                    debts[i] = {
                      ...d,
                      [k]:
                        k === "balance" || k === "min_payment"
                          ? Math.round(Number(e.target.value) * 100)
                          : e.target.value,
                    };
                    setP({ ...p, debts });
                  }}
                />
              </label>
            ),
          )}
          <button
            type="button"
            aria-label={"Remove " + d.name}
            onClick={() =>
              setP({ ...p, debts: p.debts.filter((_, j) => j !== i) })
            }
          >
            <X size={16} />
          </button>
        </div>
      ))}
      <button
        type="button"
        className="text-button"
        onClick={() =>
          setP({
            ...p,
            debts: [
              ...p.debts,
              {
                name: "New debt",
                balance: 0,
                annual_rate: "0",
                min_payment: 0,
              },
            ],
          })
        }
      >
        <Plus size={16} /> Add debt
      </button>
      <h3>Savings accounts</h3>
      {p.savings.map((s, i) => (
        <div className="editable-row" key={i}>
          <input
            aria-label="Account name"
            required
            value={s.name}
            onChange={(e) => {
              const savings = [...p.savings];
              savings[i] = { ...s, name: e.target.value };
              setP({ ...p, savings });
            }}
          />
          <input
            aria-label="Savings balance"
            required
            type="number"
            min="0"
            step="0.01"
            value={s.balance / 100}
            onChange={(e) => {
              const savings = [...p.savings];
              savings[i] = {
                ...s,
                balance: Math.round(Number(e.target.value) * 100),
              };
              setP({ ...p, savings });
            }}
          />
          <select
            aria-label="Savings kind"
            value={s.kind}
            onChange={(e) => {
              const savings = [...p.savings];
              savings[i] = { ...s, kind: e.target.value };
              setP({ ...p, savings });
            }}
          >
            <option value="emergency">Emergency</option>
            <option value="goal">Goal</option>
          </select>
          <button
            type="button"
            aria-label={"Remove " + s.name}
            onClick={() =>
              setP({ ...p, savings: p.savings.filter((_, j) => j !== i) })
            }
          >
            <X size={16} />
          </button>
        </div>
      ))}
      <button
        type="button"
        className="text-button"
        onClick={() =>
          setP({
            ...p,
            savings: [
              ...p.savings,
              { name: "New account", balance: 0, kind: "goal" },
            ],
          })
        }
      >
        <Plus size={16} /> Add account
      </button>
      <label>
        Goal savings account
        <select
          value={String(p.goal.linked_account || "")}
          onChange={(e) =>
            setP({ ...p, goal: { ...p.goal, linked_account: e.target.value } })
          }
        >
          <option value="">Use emergency fund</option>
          {p.savings.map((a) => (
            <option key={a.name} value={a.name}>
              {a.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Goal amount
        <input
          type="number"
          min="0"
          step="0.01"
          value={Number(p.goal.target_amount || 0) / 100}
          onChange={(e) =>
            setP({
              ...p,
              goal: {
                ...p.goal,
                target_amount: Math.round(Number(e.target.value) * 100),
              },
            })
          }
        />
      </label>
      <label>
        Goal date
        <input
          type="date"
          value={String(p.goal.target_date || "")}
          onChange={(e) =>
            setP({ ...p, goal: { ...p.goal, target_date: e.target.value } })
          }
        />
      </label>
      <button className="button primary" disabled={busy}>
        Save & recalculate <ArrowRight size={16} />
      </button>
    </form>
  );
}
function ImportForm({
  submit,
  busy,
}: {
  submit: (b: FormData) => Promise<void>;
  busy: boolean;
}) {
  const [file, setFile] = useState<File | null>(null),
    [mapping, setMapping] = useState("{}"),
    [keywords, setKeywords] = useState(
      '{"tesco":"groceries","spotify":"subscriptions"}',
    ),
    [report, setReport] = useState<Record<string, unknown> | null>(null),
    [error, setError] = useState("");
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!file) return;
        try {
          JSON.parse(mapping);
          JSON.parse(keywords);
        } catch {
          setError("Use valid JSON for column mapping and category keywords.");
          return;
        }
        const body = new FormData();
        body.append("file", file);
        body.append("mapping", mapping);
        body.append("keywords", keywords);
        void submit(body).then(async () =>
          setReport(await api("/import/summary")),
        );
      }}
    >
      <div className="eyebrow">A CLEARER PICTURE</div>
      <h2>Bring your statement.</h2>
      <p>
        Your CSV is processed on this device. Import adds transaction history;
        it does not change your cash balance.
      </p>
      <label>
        CSV file
        <input
          autoFocus
          required
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
      </label>
      <details>
        <summary>Column mapping & categories</summary>
        <label>
          Mapping (JSON)
          <textarea
            value={mapping}
            onChange={(e) => setMapping(e.target.value)}
          />
        </label>
        <small>
          Example:{" "}
          {
            '{"date":"Booking","amount":"Value","description":"Details","date_format":"%d/%m/%Y"}'
          }
        </small>
        <label>
          Category keywords (JSON)
          <textarea
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
          />
        </label>
      </details>
      {error && <p role="alert">{error}</p>}
      <button className="button primary" disabled={busy || !file}>
        <Upload size={16} /> Import locally
      </button>
      {report && (
        <div className="import-report">
          <h3>Import results</h3>
          <pre>{JSON.stringify(report, null, 2)}</pre>
        </div>
      )}
    </form>
  );
}
if (document.getElementById("root"))
  createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
