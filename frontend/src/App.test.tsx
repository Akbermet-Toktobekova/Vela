import { afterEach, describe, it, expect, vi } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { App } from "./main";
import { money } from "./api";
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
describe("FinAgent", () => {
  it("formats integer minor units", () => expect(money(12345)).toBe("$123.45"));
  it("loads a synthetic persona through the API", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      json: async () => ({
        error: { message: "Load a synthetic persona to start" },
      }),
    } as Response);
    render(<App />);
    await screen.findByText("Load a synthetic persona to start");
    fireEvent.click(screen.getByRole("button", { name: /Alex · Debt payoff/ }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/demo/P2",
        expect.objectContaining({ method: "POST" }),
      ),
    );
  });
  it("renders the guarded overview without recommendation controls", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        profile: {
          id: "P2",
          name: "Alex",
          currency: "USD",
          cash_balance: 100,
          monthly_income: 100000,
          min_cash_buffer: 50000,
          fixed_costs: [],
          savings: [],
          debts: [],
          emergency_months: 3,
        },
        date: "2026-10-22",
        overview: { safe_to_spend: 0, reserved: 0, days_to_income: 10 },
        guard: {
          reason: "Coaching is taking a pause.",
          until: "2026-10-24T00:00:00Z",
        },
        recommendation: null,
        lesson: null,
        rules: [],
        history: [],
        analysis: { recurring: [] },
        disclaimer: "Educational guidance only.",
      }),
    } as Response);
    render(<App />);
    await screen.findByText("Let’s pause the next steps.");
    expect(screen.queryByText("Let’s do this")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Assistant/ }));
    await screen.findByText("A question is a good place to start.");
  });
});

import fixture from "./fixtures/today.json";
describe("Main recommendation flow", () => {
  it("accepts a recommendation and displays its committed state", async () => {
    const data = structuredClone(fixture);
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async (url) => {
        if (String(url).endsWith("/accept"))
          data.recommendation.status = "accepted";
        return { ok: true, json: async () => data } as Response;
      });
    render(<App />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Let’s do this" }),
    );
    await screen.findByText(/Recommendation accepted/);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/recommendations/" + data.recommendation.id + "/accept",
      expect.objectContaining({ method: "POST" }),
    );
    expect(
      screen.queryByRole("button", { name: "Let’s do this" }),
    ).not.toBeInTheDocument();
  });
  it("sends integer minor units when adjusting and supports Escape", async () => {
    const data = structuredClone(fixture);
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue({ ok: true, json: async () => data } as Response);
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Adjust" }));
    await screen.findByRole("dialog", { name: "Adjust recommendation" });
    fireEvent.change(screen.getByLabelText("Amount in major currency units"), {
      target: { value: "25.50" },
    });
    fireEvent.submit(
      screen
        .getByRole("button", { name: /Check & save adjustment/ })
        .closest("form")!,
    );
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/recommendations/" + data.recommendation.id + "/adjust",
        expect.objectContaining({
          body: JSON.stringify({ amount: 2550, schedule_day: 1 }),
        }),
      ),
    );
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Adjust" }));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
  it("sends a what-if message and shows tool-grounded facts", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(
      async (url) =>
        ({
          ok: true,
          json: async () =>
            String(url).endsWith("/assistant/messages")
              ? {
                  text: "This is a scenario, not a change to your plan.",
                  facts: { interest_saved: 12345 },
                  tools: ["simulate_extra_payment"],
                }
              : fixture,
        }) as Response,
    );
    render(<App />);
    await screen.findByText("Good morning, Alex.");
    fireEvent.click(screen.getByRole("button", { name: /Assistant/ }));
    fireEvent.click(
      await screen.findByRole("button", {
        name: "What if I pay $50 more toward debt?",
      }),
    );
    await screen.findByText("This is a scenario, not a change to your plan.");
    expect(screen.getByText("$123.45")).toBeInTheDocument();
  });
});
