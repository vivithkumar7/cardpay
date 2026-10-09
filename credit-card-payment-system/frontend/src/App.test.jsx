import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import axios from "axios";
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

  it("refreshes an expired access token and retries the original request", async () => {
    localStorage.setItem("access", "expired-access-token");
    localStorage.setItem("refresh", "valid-refresh-token");
    const refreshRequest = vi.spyOn(axios, "post").mockResolvedValue({
      data: { access: "new-access-token", refresh: "rotated-refresh-token" },
    });
    let requestCount = 0;
    django.defaults.adapter = vi.fn(config => {
      requestCount += 1;
      if (requestCount === 1) {
        return Promise.reject({
          config,
          response: { config, status: 401, data: { detail: "Token expired." } },
        });
      }
      return Promise.resolve({
        config,
        status: 200,
        statusText: "OK",
        headers: {},
        data: { username: "demo-user" },
      });
    });

    const response = await django.get("/api/auth/me/");

    expect(response.data.username).toBe("demo-user");
    expect(requestCount).toBe(2);
    expect(refreshRequest).toHaveBeenCalledWith(
      "http://localhost:8000/api/auth/refresh/",
      { refresh: "valid-refresh-token" },
    );
    expect(localStorage.getItem("access")).toBe("new-access-token");
    expect(localStorage.getItem("refresh")).toBe("rotated-refresh-token");
  });

  it("renders dashboard metrics and recent transactions from the summary API", async () => {
    localStorage.setItem("access", "dashboard-test-token");
    vi.spyOn(django, "get").mockImplementation((url) => {
      if (url === "/api/auth/me/") {
        localStorage.setItem("access", "refreshed-dashboard-token");
        return Promise.resolve({ data: { username: "demo-user" } });
      }
      if (url === "/api/cards/") return Promise.resolve({ data: [] });
      if (url === "/api/transactions/") return Promise.resolve({ data: { count: 2, next: null, previous: null, results: [
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
      ] } });
      if (url === "/api/transactions/analytics/usage/") return Promise.resolve({ data: {
        monthly_spending: [{ month: "2026-05", spending: "0.00" }, { month: "2026-06", spending: "0.00" }, { month: "2026-07", spending: "0.00" }, { month: "2026-08", spending: "0.00" }, { month: "2026-09", spending: "0.00" }, { month: "2026-10", spending: "125.50" }],
        category_spending: [{ category: "FOOD", label: "Food & dining", spending: "125.50" }],
        credit_limit: "874.50",
        credit_spending: "125.50",
        credit_utilization_percentage: "14.35",
        transaction_status_counts: { SUCCESS: 1, FAILED: 1, PENDING: 0 },
        daily_activity: [],
      } });
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
    const themeToggle = screen.getByRole("button", { name: "Toggle color theme" });
    expect(themeToggle.getAttribute("aria-pressed")).toBe("false");
    expect(themeToggle.querySelector("[data-theme-icon='moon']")).toBeTruthy();
    fireEvent.click(themeToggle);
    expect(document.querySelector(".app-shell").getAttribute("data-theme")).toBe("dark");
    expect(localStorage.getItem("theme")).toBe("dark");
    const darkThemeToggle = screen.getByRole("button", { name: "Toggle color theme" });
    expect(darkThemeToggle.getAttribute("aria-pressed")).toBe("true");
    expect(darkThemeToggle.querySelector("[data-theme-icon='sun']")).toBeTruthy();
    fireEvent.click(darkThemeToggle);
    expect(document.querySelector(".app-shell").getAttribute("data-theme")).toBe("light");
    expect(screen.getByText("Total amount spent")).toBeTruthy();
    expect(screen.getByText("Available credit")).toBeTruthy();
    expect(screen.getByRole("img", { name: "Line chart of monthly spending over the last six months" })).toBeTruthy();
    expect(screen.getByRole("img", { name: "Pie chart of spending by category" })).toBeTruthy();
    expect(await screen.findByText("Food & dining")).toBeTruthy();
    expect(screen.getByText("Credit utilization")).toBeTruthy();
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

  it("filters, sorts, and pages through server-paginated transactions", async () => {
    localStorage.setItem("access", "transactions-test-token");
    vi.spyOn(django, "get").mockImplementation((url, config) => {
      if (url === "/api/auth/me/") return Promise.resolve({ data: { username: "history-user" } });
      if (url === "/api/transactions/") {
        const page = config.params.page;
        return Promise.resolve({ data: {
          count: 21,
          next: page === 1 ? "/api/transactions/?page=2" : null,
          previous: page === 2 ? "/api/transactions/?page=1" : null,
          results: [{
            id: page,
            amount: "25.00",
            status: "SUCCESS",
            reference: `TX-PAGE-${page}`,
            created_at: "2026-10-07T10:00:00Z",
            card_mask: "************1111",
          }],
        } });
      }
      return Promise.resolve({ data: [] });
    });

    render(<MemoryRouter initialEntries={["/transactions"]}><App /></MemoryRouter>);
    expect(await screen.findByText("TX-PAGE-1")).toBeTruthy();
    expect(django.get).toHaveBeenCalledWith("/api/transactions/", {
      params: expect.objectContaining({ page: 1, page_size: 20, ordering: "-created_at" }),
    });

    fireEvent.change(screen.getByLabelText("Filter by status"), { target: { value: "SUCCESS" } });
    await waitFor(() => {
      expect(django.get).toHaveBeenLastCalledWith("/api/transactions/", {
        params: expect.objectContaining({ status: "SUCCESS", page: 1 }),
      });
    });
    fireEvent.click(screen.getByRole("button", { name: /Amount/ }));
    await waitFor(() => {
      expect(django.get).toHaveBeenLastCalledWith("/api/transactions/", {
        params: expect.objectContaining({ status: "SUCCESS", ordering: "amount", page: 1 }),
      });
    });
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => {
      expect(django.get).toHaveBeenLastCalledWith("/api/transactions/", {
        params: expect.objectContaining({ status: "SUCCESS", ordering: "amount", page: 2 }),
      });
    });
  });

  it("shows system health and downloads analytics reports from the admin dashboard", async () => {
    localStorage.setItem("access", "admin-dashboard-token");
    const health = {
      status: "healthy",
      database: "healthy",
      api_requests: 24,
      api_failures: 2,
      slow_requests: 1,
      average_response_time_ms: 42.5,
      uptime_seconds: 3600,
      checked_at: "2026-10-09T06:00:00Z",
      monitoring_scope: "This application process",
    };
    vi.spyOn(django, "get").mockImplementation((url) => {
      if (url === "/api/auth/me/") return Promise.resolve({ data: { username: "admin-user", is_staff: true } });
      if (url === "/api/admin/summary/") return Promise.resolve({ data: {
        total_transactions: 24,
        successful: 18,
        failed: 4,
        pending: 2,
        total_amount: "12500.00",
        flagged_transactions: 0,
        daily: { date: "2026-10-09", total_transactions: 2, successful: 1, failed: 1, pending: 0, total_amount: "250.00" },
      } });
      if (url === "/api/admin/cards/") return Promise.resolve({ data: [] });
      if (url === "/api/admin/system-health/") return Promise.resolve({ data: health });
      if (url === "/api/admin/analytics/export/") return Promise.resolve({ data: new Blob(["report"]) });
      return Promise.resolve({ data: [] });
    });
    vi.stubGlobal("URL", { createObjectURL: vi.fn(() => "blob:analytics"), revokeObjectURL: vi.fn() });
    const downloadClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    render(<MemoryRouter initialEntries={["/admin-dashboard"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Admin dashboard" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "System health" })).toBeTruthy();
    expect(screen.getByText("42.5 ms")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Refresh health" }));
    await waitFor(() => expect(django.get).toHaveBeenCalledWith("/api/admin/system-health/"));

    fireEvent.click(screen.getByRole("button", { name: "Export CSV" }));
    await waitFor(() => expect(django.get).toHaveBeenCalledWith("/api/admin/analytics/export/", {
      params: { file_format: "csv" },
      responseType: "blob",
    }));
    fireEvent.click(screen.getByRole("button", { name: "Export PDF" }));
    await waitFor(() => expect(django.get).toHaveBeenCalledWith("/api/admin/analytics/export/", {
      params: { file_format: "pdf" },
      responseType: "blob",
    }));
    expect(downloadClick).toHaveBeenCalledTimes(2);
  });

  it("shows the admin navigation link to signed-in users while keeping dashboard access restricted", async () => {
    localStorage.setItem("access", "regular-user-token");
    vi.spyOn(django, "get").mockImplementation((url) => {
      if (url === "/api/auth/me/") return Promise.resolve({ data: { username: "regular-user", is_staff: false } });
      if (url.startsWith("/api/admin/")) {
        return Promise.reject({ response: { status: 403 } });
      }
      if (url === "/api/transactions/") {
        return Promise.resolve({ data: { count: 0, next: null, previous: null, results: [] } });
      }
      return Promise.resolve({ data: [] });
    });

    render(<MemoryRouter initialEntries={["/transactions"]}><App /></MemoryRouter>);
    const adminLink = await screen.findByRole("link", { name: "Admin" });

    fireEvent.click(adminLink);
    expect(await screen.findByText("Staff access required")).toBeTruthy();
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

  it("downloads the selected monthly statement as a PDF", async () => {
    localStorage.setItem("access", "statement-test-token");
    vi.spyOn(django, "get").mockImplementation(url => {
      if (url === "/api/auth/me/") return Promise.resolve({ data: { username: "statement-user" } });
      if (url === "/api/cards/") return Promise.resolve({ data: [] });
      if (url === "/api/transactions/") return Promise.resolve({ data: [] });
      if (url === "/api/transactions/statement/") return Promise.resolve({ data: new Blob(["%PDF"]) });
      return Promise.resolve({ data: [] });
    });
    vi.spyOn(fastapi, "get").mockResolvedValue({
      data: {
        total_transactions: 0,
        total_amount_spent: "0.00",
        current_month_spending: "0.00",
        available_credit_limit: "0.00",
        last_5_transactions: [],
      },
    });
    const createObjectURL = vi.fn(() => "blob:statement");
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL: vi.fn() });
    const downloadClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Download PDF" }));

    const today = new Date();
    const month = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
    expect(django.get).toHaveBeenCalledWith("/api/transactions/statement/", {
      params: { month },
      responseType: "blob",
    });
    await waitFor(() => {
      expect(createObjectURL).toHaveBeenCalledOnce();
      expect(downloadClick).toHaveBeenCalledOnce();
    });
  });

  it("restores the saved theme across app remounts", () => {
    localStorage.setItem("theme", "dark");
    const firstRender = render(<MemoryRouter initialEntries={["/login"]}><App /></MemoryRouter>);

    expect(document.querySelector(".app-shell").getAttribute("data-theme")).toBe("dark");

    firstRender.unmount();
    render(<MemoryRouter initialEntries={["/register"]}><App /></MemoryRouter>);

    expect(document.querySelector(".app-shell").getAttribute("data-theme")).toBe("dark");
  });
});