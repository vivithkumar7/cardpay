import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { django, fastapi } from "./api";

describe("application routes", () => {
  let originalDjangoAdapter;

  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    originalDjangoAdapter = django.defaults.adapter;
  });

  afterEach(() => {
    django.defaults.adapter = originalDjangoAdapter;
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("renders the login page", () => {
    render(<MemoryRouter initialEntries={["/login"]}><App /></MemoryRouter>);

    expect(screen.getByLabelText("Username")).toBeTruthy();
    expect(screen.getByLabelText("Password")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Create an account" })).toBeTruthy();
  });

  it("redirects protected pages to login when signed out", () => {
    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

    expect(screen.getByLabelText("Username")).toBeTruthy();
  });

  it("returns to login when an access token is rejected without a refresh token", async () => {
    localStorage.setItem("access", "expired-access-token");
    django.defaults.adapter = config => Promise.reject({ config, response: { status: 401 } });

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

    expect(await screen.findByLabelText("Username")).toBeTruthy();
    expect(localStorage.getItem("access")).toBeNull();
  });

  it("renders dashboard metrics and recent transactions from the summary API", async () => {
    localStorage.setItem("access", "dashboard-test-token");
    vi.spyOn(django, "get").mockImplementation((url) => {
      if (url === "/api/auth/me/") {
        localStorage.setItem("access", "refreshed-dashboard-token");
        return Promise.resolve({ data: { username: "demo-user" } });
      }
      if (url === "/api/cards/") return Promise.resolve({ data: [] });
      if (url === "/api/transactions/") return Promise.resolve({ data: [
        {
          id: 1,
          amount: "125.50",
          status: "SUCCESS",
          reference: "TX-DASHBOARD-TEST",
          created_at: "2026-10-07T10:00:00Z",
          card_mask: "************1111",
        },
        {
          id: 2,
          amount: "35.00",
          status: "FAILED",
          reference: "TX-FAILED-NO-INVOICE",
          created_at: "2026-10-06T10:00:00Z",
          card_mask: "************1111",
        },
      ] });
      return Promise.resolve({ data: [] });
    });
    vi.spyOn(fastapi, "get").mockResolvedValue({
      data: {
        total_transactions: 1,
        total_amount_spent: "125.50",
        current_month_spending: "125.50",
        available_credit_limit: "874.50",
        last_5_transactions: [{
          id: 1,
          amount: "125.50",
          status: "SUCCESS",
          reference: "TX-DASHBOARD-TEST",
          created_at: "2026-10-07T10:00:00Z",
          card_mask: "************1111",
        }],
      },
    });

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

    const dashboardHeading = await screen.findByRole("heading", { level: 1 });
    expect(dashboardHeading.textContent).toContain("Welcome back, demo-user");
    expect(screen.getByText("Total amount spent")).toBeTruthy();
    expect(screen.getByText("Available credit")).toBeTruthy();
    expect(screen.getAllByText("TX-DASHBOARD-TEST").length).toBeGreaterThan(0);
    expect(screen.getByText("************1111")).toBeTruthy();
    const quickActions = screen.getByRole("region", { name: "Quick actions" });
    expect(within(quickActions).getByRole("link", { name: /My Cards/ }).getAttribute("href")).toBe("/cards");
    expect(within(quickActions).getByRole("link", { name: /Make Payment/ }).getAttribute("href")).toBe("/payment");
    expect(within(quickActions).getByRole("link", { name: /Transactions/ }).getAttribute("href")).toBe("/transactions");
    const invoices = screen.getByRole("region", { name: "Recent invoices" });
    expect(within(invoices).getByText("TX-DASHBOARD-TEST")).toBeTruthy();
    expect(within(invoices).queryByText("TX-FAILED-NO-INVOICE")).toBeNull();
    fireEvent.click(within(invoices).getByRole("button", { name: /View receipt/ }));
    const receipt = await screen.findByRole("dialog", { name: "Payment receipt" });
    expect(within(receipt).getByText("TX-DASHBOARD-TEST")).toBeTruthy();
    const createObjectURL = vi.fn(() => "blob:receipt");
    vi.stubGlobal("URL", {
      createObjectURL,
      revokeObjectURL: vi.fn(),
    });
    const downloadClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function () {
      expect(this.download).toBe("PaySecure-invoice-TX-DASHBOARD-TEST.html");
    });
    vi.useFakeTimers();
    fireEvent.click(within(receipt).getByRole("button", { name: /Download invoice/ }));
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(downloadClick).toHaveBeenCalledOnce();
    vi.advanceTimersByTime(1000);
    expect(fastapi.get).toHaveBeenCalledWith("/dashboard/summary", {
      headers: { Authorization: "Bearer refreshed-dashboard-token" },
    });
  });

  it("shows a sign-in prompt when the dashboard summary JWT is rejected", async () => {
    localStorage.setItem("access", "expired-dashboard-token");
    vi.spyOn(django, "get").mockImplementation((url) => {
      if (url === "/api/auth/me/") return Promise.resolve({ data: { username: "demo-user" } });
      return Promise.resolve({ data: [] });
    });
    vi.spyOn(fastapi, "get").mockRejectedValue({ response: { status: 401 } });

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain(
      "Your session has expired. Sign in again to load your dashboard."
    );
    expect(screen.getByRole("link", { name: "Sign in" })).toBeTruthy();
  });

  it("shows loading skeletons while the dashboard summary is pending", () => {
    localStorage.setItem("access", "dashboard-test-token");
    vi.spyOn(django, "get").mockImplementation(() => new Promise(() => {}));
    vi.spyOn(fastapi, "get").mockImplementation(() => new Promise(() => {}));

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

    expect(screen.getByRole("status", { name: "Loading dashboard" })).toBeTruthy();
  });
});