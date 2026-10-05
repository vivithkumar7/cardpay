import React, { useEffect, useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { django, fastapi } from "./api";

function Layout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const isAuthPage = location.pathname === "/login" || location.pathname === "/register";
  const isAuthenticated = Boolean(localStorage.getItem("access") || sessionStorage.getItem("access"));

  useEffect(() => {
    let active = true;
    if (!isAuthenticated) {
      setUser(null);
      return () => { active = false; };
    }
    django.get("/api/auth/me/").then(r => {
      if (active) setUser(r.data);
    }).catch(() => {
      if (active) setUser(null);
    });
    return () => { active = false; };
  }, [isAuthenticated]);

  async function logout() {
    const refresh = localStorage.getItem("refresh") || sessionStorage.getItem("refresh");
    if (refresh) {
      try { await django.post("/api/auth/logout/", { refresh }); } catch {}
    }
    localStorage.clear();
    sessionStorage.clear();
    navigate("/login");
  }

  return (
    <div className={`app-shell min-h-screen ${isAuthPage ? "auth-shell bg-[#030305]" : "bg-[#0b0d0b]"}`}>
      {!isAuthPage && <nav className="app-nav">
        <Link to="/" className="brand-lockup"><span className="brand-mark" aria-hidden="true">P</span><span>PaySecure</span></Link>
        <div className="nav-links">
          {isAuthenticated ? (
            <>
              <NavLink to="/" end className={({isActive}) => `nav-link${isActive ? " is-active" : ""}`}>Overview</NavLink>
              <NavLink to="/cards" className={({isActive}) => `nav-link${isActive ? " is-active" : ""}`}>Cards</NavLink>
              <NavLink to="/payment" className={({isActive}) => `nav-link${isActive ? " is-active" : ""}`}>Payment</NavLink>
              <NavLink to="/transactions" className={({isActive}) => `nav-link${isActive ? " is-active" : ""}`}>Activity</NavLink>
              {user?.is_staff && <NavLink to="/admin-dashboard" className={({isActive}) => `nav-link${isActive ? " is-active" : ""}`}>Admin</NavLink>}
              <span className="nav-user">{user?.username || "Account"}</span>
              <button onClick={logout} className="nav-logout" aria-label="Log out" title="Log out">↗</button>
            </>
          ) : (
            <><NavLink className="nav-link" to="/login">Sign in</NavLink><NavLink className="nav-cta" to="/register">Create account</NavLink></>
          )}
        </div>
      </nav>}
      <main className={isAuthPage ? "max-w-none p-0" : "workspace"}>{children}</main>
    </div>
  );
}

function Protected({ children }) {
  return localStorage.getItem("access") || sessionStorage.getItem("access") ? children : <Navigate to="/login" replace />;
}

function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({username:"", password:""});
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [resetNotice, setResetNotice] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const r = await django.post("/api/auth/login/", form);
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      sessionStorage.removeItem("access");
      sessionStorage.removeItem("refresh");
      const tokenStorage = rememberMe ? localStorage : sessionStorage;
      tokenStorage.setItem("access", r.data.access);
      tokenStorage.setItem("refresh", r.data.refresh);
      navigate("/");
    } catch (err) { setError(JSON.stringify(err.response?.data || "Login failed")); }
  }

  return <section className="login-scene relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12 text-white sm:px-6">
    <div className="relative z-10 flex w-full max-w-md flex-col items-center">
      <header className="mb-10 text-center">
        <p className="text-4xl font-light leading-tight sm:text-5xl">PaySecure</p>
        <p className="mt-1 text-xs font-semibold uppercase tracking-[0.2em] text-amber-400 sm:text-sm">Secure payments</p>
      </header>
      <div className="w-full rounded-lg border border-white/15 bg-black/55 p-6 shadow-2xl shadow-black/60 backdrop-blur-xl sm:p-8">
        <div className="mb-6 flex items-start gap-4">
          <span aria-hidden="true" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md border border-amber-200/40 bg-white/[0.06] text-lg font-semibold text-amber-300">P</span>
          <div>
            <p className="text-xl font-semibold">Welcome <span className="text-amber-300">Back</span></p>
            <p className="mt-1 text-xs leading-5 text-white/55">Sign in to your PaySecure account.</p>
          </div>
        </div>
        {error && <div role="alert" className="mb-5 rounded-md border border-red-300/30 bg-red-950/50 p-3 text-sm text-red-100">{error}</div>}
        <form onSubmit={submit} className="space-y-4">
          <label htmlFor="login-username" className="block text-xs font-medium text-white/75">Username</label>
          <input id="login-username" autoComplete="username" required className="-mt-2 w-full rounded-md border border-white/10 bg-white/[0.06] px-3.5 py-3 text-sm text-white outline-none placeholder:text-white/35 focus:border-amber-300/70 focus:ring-2 focus:ring-amber-300/15" placeholder="Enter your username" value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/>
          <div>
            <label htmlFor="login-password" className="block text-xs font-medium text-white/75">Password</label>
            <div className="relative mt-2">
              <input id="login-password" autoComplete="current-password" required className="w-full rounded-md border border-white/10 bg-white/[0.06] px-3.5 py-3 pr-16 text-sm text-white outline-none placeholder:text-white/35 focus:border-amber-300/70 focus:ring-2 focus:ring-amber-300/15" placeholder="Enter your password" type={showPassword ? "text" : "password"} value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>
              <button type="button" onClick={()=>setShowPassword(!showPassword)} className="absolute inset-y-0 right-3 text-xs font-medium text-white/60 hover:text-white" aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? "Hide" : "Show"}</button>
            </div>
          </div>
          <div className="flex items-center justify-between gap-3 pt-1 text-xs">
            <label className="flex cursor-pointer items-center gap-2 text-white/70"><input type="checkbox" checked={rememberMe} onChange={e=>setRememberMe(e.target.checked)} className="h-3.5 w-3.5 accent-amber-300"/>Remember me</label>
            <button type="button" onClick={()=>setResetNotice(true)} className="text-white/60 underline decoration-white/25 underline-offset-4 hover:text-amber-200">Forgot password?</button>
          </div>
          {resetNotice && <p role="status" className="text-xs leading-5 text-amber-100/80">Password reset is not enabled for this demo. Please contact your administrator.</p>}
          <button className="w-full rounded-md bg-[#f5df35] px-4 py-3 text-sm font-semibold text-[#1d1800] shadow-lg shadow-yellow-300/10 transition hover:bg-[#ffe94e] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-yellow-200">Sign in <span aria-hidden="true" className="ml-1">→</span></button>
        </form>
        <p className="mt-5 border-t border-white/10 pt-4 text-center text-xs text-white/60">New to PaySecure? <Link to="/register" className="font-semibold text-amber-200 hover:text-yellow-100">Create an account</Link></p>
      </div>
    </div>
  </section>
}

function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({username:"",email:"",password:"",password2:""});
  const [error, setError] = useState("");
  const [showPasswords, setShowPasswords] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (form.password !== form.password2) {
      setError("Passwords do not match.");
      return;
    }
    try {
      await django.post("/api/auth/register/", form);
      navigate("/login");
    } catch (err) { setError(JSON.stringify(err.response?.data || "Registration failed")); }
  }

  return <section className="login-scene relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10 text-white sm:px-6">
    <div className="relative z-10 flex w-full max-w-md flex-col items-center">
      <header className="mb-8 text-center">
        <p className="text-4xl font-light leading-tight sm:text-5xl">PaySecure</p>
        <p className="mt-1 text-xs font-semibold uppercase tracking-[0.2em] text-amber-400 sm:text-sm">Secure payments</p>
      </header>
      <div className="w-full rounded-lg border border-white/15 bg-black/55 p-6 shadow-2xl shadow-black/60 backdrop-blur-xl sm:p-8">
        <div className="mb-6 flex items-start gap-4">
          <span aria-hidden="true" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md border border-amber-200/40 bg-white/[0.06] text-lg font-semibold text-amber-300">P</span>
          <div>
            <p className="text-xl font-semibold">Create <span className="text-amber-300">Account</span></p>
            <p className="mt-1 text-xs leading-5 text-white/55">Join PaySecure to manage your cards and payments.</p>
          </div>
        </div>
        {error && <div role="alert" className="mb-5 rounded-md border border-red-300/30 bg-red-950/50 p-3 text-sm text-red-100">{error}</div>}
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label htmlFor="register-username" className="block text-xs font-medium text-white/75">Username</label>
            <input id="register-username" autoComplete="username" required className="mt-2 w-full rounded-md border border-white/10 bg-white/[0.06] px-3.5 py-3 text-sm text-white outline-none placeholder:text-white/35 focus:border-amber-300/70 focus:ring-2 focus:ring-amber-300/15" placeholder="Choose a username" value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/>
          </div>
          <div>
            <label htmlFor="register-email" className="block text-xs font-medium text-white/75">Email address</label>
            <input id="register-email" type="email" autoComplete="email" required className="mt-2 w-full rounded-md border border-white/10 bg-white/[0.06] px-3.5 py-3 text-sm text-white outline-none placeholder:text-white/35 focus:border-amber-300/70 focus:ring-2 focus:ring-amber-300/15" placeholder="name@example.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="register-password" className="block text-xs font-medium text-white/75">Password</label>
              <div className="relative mt-2">
                <input id="register-password" autoComplete="new-password" required className="w-full rounded-md border border-white/10 bg-white/[0.06] px-3 py-3 pr-14 text-sm text-white outline-none placeholder:text-white/35 focus:border-amber-300/70 focus:ring-2 focus:ring-amber-300/15" placeholder="Create password" type={showPasswords ? "text" : "password"} value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>
                <button type="button" onClick={()=>setShowPasswords(!showPasswords)} className="absolute inset-y-0 right-2 text-xs font-medium text-white/60 hover:text-white" aria-label={showPasswords ? "Hide passwords" : "Show passwords"}>{showPasswords ? "Hide" : "Show"}</button>
              </div>
            </div>
            <div>
              <label htmlFor="register-password-confirm" className="block text-xs font-medium text-white/75">Confirm password</label>
              <input id="register-password-confirm" autoComplete="new-password" required className="mt-2 w-full rounded-md border border-white/10 bg-white/[0.06] px-3 py-3 text-sm text-white outline-none placeholder:text-white/35 focus:border-amber-300/70 focus:ring-2 focus:ring-amber-300/15" placeholder="Repeat password" type={showPasswords ? "text" : "password"} value={form.password2} onChange={e=>setForm({...form,password2:e.target.value})}/>
            </div>
          </div>
          <button className="w-full rounded-md bg-[#f5df35] px-4 py-3 text-sm font-semibold text-[#1d1800] shadow-lg shadow-yellow-300/10 transition hover:bg-[#ffe94e] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-yellow-200">Create account <span aria-hidden="true" className="ml-1">→</span></button>
        </form>
        <p className="mt-5 border-t border-white/10 pt-4 text-center text-xs text-white/60">Already have an account? <Link to="/login" className="font-semibold text-amber-200 hover:text-yellow-100">Sign in</Link></p>
      </div>
    </div>
  </section>
}

function Dashboard() {
  const [user, setUser] = useState(null);
  const [cards, setCards] = useState([]);
  const [tx, setTx] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    Promise.all([
      django.get("/api/auth/me/"),
      django.get("/api/cards/"),
      django.get("/api/transactions/")
    ]).then(([userResponse, cardResponse, transactionResponse]) => {
      if (!active) return;
      setUser(userResponse.data);
      setCards(cardResponse.data);
      setTx(transactionResponse.data);
    }).catch((requestError) => {
      if (active) setError(requestError.response?.data?.detail || "We couldn't load your dashboard. Check your connection and try again.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [retryCount]);

  const successfulTransactions = tx.filter(transaction => transaction.status === "SUCCESS");
  const failedTransactions = tx.filter(transaction => transaction.status === "FAILED");
  const pendingTransactions = tx.filter(transaction => transaction.status === "PENDING");
  const successfulVolume = successfulTransactions.reduce((total, transaction) => total + Number(transaction.amount), 0);
  const successRate = tx.length ? Math.round((successfulTransactions.length / tx.length) * 100) : 0;
  const money = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const activityDays = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(today);
    date.setDate(today.getDate() - (6 - index));
    const dayTransactions = tx.filter(transaction => new Date(transaction.created_at).toDateString() === date.toDateString());
    return {
      date,
      label: date.toLocaleDateString("en-IN", { weekday: "short" }),
      count: dayTransactions.length,
      successful: dayTransactions.filter(transaction => transaction.status === "SUCCESS").length,
      failed: dayTransactions.filter(transaction => transaction.status === "FAILED").length,
      pending: dayTransactions.filter(transaction => transaction.status === "PENDING").length,
    };
  });
  const peakActivity = Math.max(1, ...activityDays.map(day => day.count));
  const recentTransactions = tx.slice(0, 5);

  if (loading) return <div className="mx-auto max-w-7xl py-16 text-center text-sm text-slate-500" role="status">Loading your overview…</div>;
  if (error) return <div className="mx-auto max-w-7xl py-16 text-center"><p role="alert" className="text-sm text-rose-700">{error}</p><button onClick={() => setRetryCount(count => count + 1)} className="mt-4 rounded-md bg-[#111311] px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700">Try again</button></div>;

  return <div className="dashboard-page">
    <header className="page-heading dashboard-heading">
      <div>
        <p className="eyebrow">YOUR MONEY, AT A GLANCE</p>
        <h1>Good to see you, <span>{user?.username}</span></h1>
        <p className="page-subtitle">A calm, clear view of your payment activity.</p>
      </div>
      <div className="heading-actions">
        <Link to="/cards" className="button-secondary">Manage cards</Link>
        <Link to="/payment" className="button-primary">Make a payment <span aria-hidden="true">↗</span></Link>
      </div>
    </header>

    <section aria-label="Payment statistics" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <Stat label="Successful volume" value={money.format(successfulVolume)} note={`${successfulTransactions.length} settled payment${successfulTransactions.length === 1 ? "" : "s"}`} marker="₹" markerClass="bg-amber-100 text-amber-900"/>
      <Stat label="Transactions" value={tx.length} note={`${pendingTransactions.length} pending`} marker="↗" markerClass="bg-slate-100 text-slate-800"/>
      <Stat label="Success rate" value={`${successRate}%`} note={`${failedTransactions.length} failed`} marker="%" markerClass="bg-emerald-100 text-emerald-800"/>
      <Stat label="Saved cards" value={cards.length} note="Card numbers stay masked" marker="••" markerClass="bg-stone-100 text-stone-700"/>
    </section>

    <section className="grid gap-4 lg:grid-cols-[minmax(0,1.65fr)_minmax(280px,0.8fr)]">
      <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold">Transaction activity</h2>
            <p className="mt-1 text-xs text-slate-500">Daily payment attempts over the last seven days</p>
          </div>
          <span className="rounded-full border border-slate-200 px-2.5 py-1 text-[11px] font-medium text-slate-500">7 days</span>
        </div>
        <div className="mt-6 flex h-44 items-end gap-2 sm:gap-4" role="img" aria-label="Stacked bar chart of successful, failed, and pending transactions over the last seven days">
          {activityDays.map(day => {
            const height = day.count ? Math.max((day.count / peakActivity) * 100, 8) : 3;
            return <div key={day.date.toISOString()} className="flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-2" title={`${day.label}: ${day.count} transaction${day.count === 1 ? "" : "s"}`}>
              <span className="text-[11px] tabular-nums text-slate-500">{day.count || ""}</span>
              <div className="flex w-full max-w-12 items-end overflow-hidden rounded-t-sm bg-slate-100" style={{ height: `${height}%` }}>
                {day.successful > 0 && <span className="w-full bg-amber-300" style={{ height: `${(day.successful / day.count) * 100}%` }} />}
                {day.failed > 0 && <span className="w-full bg-rose-400" style={{ height: `${(day.failed / day.count) * 100}%` }} />}
                {day.pending > 0 && <span className="w-full bg-slate-400" style={{ height: `${(day.pending / day.count) * 100}%` }} />}
              </div>
              <span className="text-[11px] text-slate-500">{day.label}</span>
            </div>;
          })}
        </div>
        <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
          <span className="flex items-center gap-2"><i className="h-2.5 w-2.5 rounded-sm bg-amber-300"/>Successful</span>
          <span className="flex items-center gap-2"><i className="h-2.5 w-2.5 rounded-sm bg-rose-400"/>Failed</span>
          <span className="flex items-center gap-2"><i className="h-2.5 w-2.5 rounded-sm bg-slate-400"/>Pending</span>
        </div>
      </article>

      <article className="rounded-lg border border-slate-200 bg-[#111311] p-5 text-white shadow-sm sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div><h2 className="text-base font-semibold">Payment health</h2><p className="mt-1 text-xs text-white/55">Across all your transactions</p></div>
          <span className="rounded-md bg-white/10 px-2 py-1 text-xs text-amber-200">{successRate}%</span>
        </div>
        <div className="mt-7 h-2 overflow-hidden rounded-full bg-white/10" aria-label={`${successRate}% success rate`}>
          <div className="h-full rounded-full bg-[#f5df35] transition-all" style={{ width: `${successRate}%` }}/>
        </div>
        <div className="mt-6 space-y-4">
          <StatusCount label="Successful" value={successfulTransactions.length} color="bg-amber-300"/>
          <StatusCount label="Failed" value={failedTransactions.length} color="bg-rose-400"/>
          <StatusCount label="Pending" value={pendingTransactions.length} color="bg-slate-400"/>
        </div>
        <p className="mt-7 border-t border-white/10 pt-4 text-xs leading-5 text-white/50">Payments are simulated. No real payment gateway is used.</p>
      </article>
    </section>

    <section className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.85fr)]">
      <article className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-5 py-4 sm:px-6">
          <div><h2 className="text-base font-semibold">Recent transactions</h2><p className="mt-1 text-xs text-slate-500">Your latest payment activity</p></div>
          <Link to="/transactions" className="shrink-0 text-xs font-semibold text-emerald-800 hover:text-emerald-950">View history <span aria-hidden="true">→</span></Link>
        </div>
        {recentTransactions.length ? <div className="divide-y divide-slate-100">
          {recentTransactions.map(transaction => <div key={transaction.id} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-5 py-4 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:px-6">
            <div className="min-w-0"><p className="truncate text-sm font-medium text-slate-900">{transaction.reference}</p><p className="mt-1 text-xs text-slate-500">{new Date(transaction.created_at).toLocaleString()}</p></div>
            <StatusBadge status={transaction.status}/>
            <p className="col-start-2 row-start-1 text-right text-sm font-semibold tabular-nums sm:col-start-3">{money.format(Number(transaction.amount))}</p>
          </div>)}
        </div> : <div className="px-6 py-10 text-center"><p className="text-sm font-medium">No transactions yet</p><p className="mt-1 text-xs text-slate-500">Your payment activity will appear here.</p></div>}
      </article>

      <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex items-center justify-between gap-3">
          <div><h2 className="text-base font-semibold">Saved cards</h2><p className="mt-1 text-xs text-slate-500">{cards.length} card{cards.length === 1 ? "" : "s"} on file</p></div>
          <Link to="/cards" aria-label="Manage saved cards" className="text-xs font-semibold text-emerald-800 hover:text-emerald-950">Manage</Link>
        </div>
        {cards.length ? <div className="mt-5 space-y-3">
          {cards.slice(0, 3).map(card => <div key={card.id} className="flex items-center justify-between gap-3 rounded-md border border-slate-200 px-3.5 py-3">
            <div className="min-w-0"><p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{card.card_type} card</p><p className="mt-1 truncate font-mono text-sm tracking-normal">{card.masked_card_number}</p></div>
            <p className="shrink-0 text-xs text-slate-500">{String(card.expiry_month).padStart(2, "0")}/{card.expiry_year}</p>
          </div>)}
          {cards.length > 3 && <p className="text-xs text-slate-500">+{cards.length - 3} more cards</p>}
        </div> : <div className="mt-5 rounded-md border border-dashed border-slate-300 px-4 py-6 text-center"><p className="text-sm text-slate-600">No cards saved</p><Link to="/cards" className="mt-2 inline-block text-xs font-semibold text-emerald-800">Add a card <span aria-hidden="true">→</span></Link></div>}
      </article>
    </section>
  </div>;
}

function Stat({label, value, note, marker, markerClass}) {
  return <article className="min-h-32 rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
    <div className="flex items-center justify-between gap-3"><p className="text-xs font-medium text-slate-500">{label}</p><span aria-hidden="true" className={`flex h-8 min-w-8 items-center justify-center rounded-md px-1 text-xs font-semibold ${markerClass}`}>{marker}</span></div>
    <p className="mt-4 truncate text-2xl font-semibold tabular-nums tracking-normal text-slate-950">{value}</p>
    <p className="mt-1 truncate text-xs text-slate-500">{note}</p>
  </article>;
}

function StatusCount({label, value, color}) {
  return <div className="flex items-center justify-between text-sm"><span className="flex items-center gap-2 text-white/70"><i className={`h-2 w-2 rounded-full ${color}`}/>{label}</span><span className="font-medium tabular-nums">{value}</span></div>;
}

function StatusBadge({status}) {
  const styles = {
    SUCCESS: "bg-emerald-50 text-emerald-800",
    FAILED: "bg-rose-50 text-rose-700",
    PENDING: "bg-slate-100 text-slate-700",
  };
  return <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${styles[status] || styles.PENDING}`}>{status}</span>;
}

function Cards() {
  const [cards,setCards]=useState([]); const [error,setError]=useState("");
  const [form,setForm]=useState({card_type:"CREDIT",card_holder_name:"",expiry_month:12,expiry_year:2030,card_number:"",cvv:""});
  const previewLast4 = form.card_number.replace(/\D/g, "").slice(-4) || "0000";
  async function load(){ const r=await django.get("/api/cards/"); setCards(r.data); }
  useEffect(()=>{load()},[]);
  async function submit(e){e.preventDefault();setError("");try{await django.post("/api/cards/",form);setForm({...form,card_number:"",cvv:""});load();}catch(err){setError(JSON.stringify(err.response?.data||"Failed"));}}
  async function remove(id){await django.delete(`/api/cards/${id}/`);load();}
  return <div className="page-shell cards-page">
    <header className="page-heading">
      <div><p className="eyebrow">PAYMENT METHODS</p><h1>Your cards</h1><p className="page-subtitle">Keep your payment methods together and ready to use.</p></div>
      <span className="page-count">{cards.length} saved</span>
    </header>
    <div className="cards-layout">
    <section className="surface-panel add-card-panel">
      <div className="panel-heading"><div><p className="eyebrow">NEW METHOD</p><h2>Add a card</h2></div><span className="panel-index">01</span></div>
      <div className="card-preview" aria-label={`${form.card_type.toLowerCase()} card preview`}>
        <div className="card-preview-top"><span>PAYSECURE</span><span className="card-chip" aria-hidden="true" /></div>
        <p className="preview-number">•••• &nbsp; •••• &nbsp; •••• &nbsp; {previewLast4}</p>
        <div className="card-preview-bottom"><span>{form.card_holder_name || "CARDHOLDER NAME"}</span><span>{String(form.expiry_month).padStart(2, "0")}/{String(form.expiry_year).slice(-2)}</span></div>
        <span className="preview-type">{form.card_type}</span>
      </div>
      {error && <p className="bg-red-100 p-2 rounded mb-3 text-red-700">{error}</p>}
      <form onSubmit={submit} className="form-stack">
        <label className="field-label">Card type<select className="field-control" value={form.card_type} onChange={e=>setForm({...form,card_type:e.target.value})}><option>CREDIT</option><option>DEBIT</option></select></label>
        <label className="field-label">Name on card<input className="field-control" autoComplete="cc-name" placeholder="e.g. Alex Morgan" value={form.card_holder_name} onChange={e=>setForm({...form,card_holder_name:e.target.value})}/></label>
        <label className="field-label">Card number<input className="field-control" inputMode="numeric" autoComplete="cc-number" placeholder="0000 0000 0000 0000" value={form.card_number} onChange={e=>setForm({...form,card_number:e.target.value})}/></label>
        <div className="field-row">
          <label className="field-label">Expiry month<input className="field-control" type="number" min="1" max="12" autoComplete="cc-exp-month" placeholder="MM" value={form.expiry_month} onChange={e=>setForm({...form,expiry_month:e.target.value})}/></label>
          <label className="field-label">Expiry year<input className="field-control" type="number" min="2026" autoComplete="cc-exp-year" placeholder="YYYY" value={form.expiry_year} onChange={e=>setForm({...form,expiry_year:e.target.value})}/></label>
          <label className="field-label">Security code<input className="field-control" inputMode="numeric" autoComplete="cc-csc" placeholder="CVV" maxLength="4" value={form.cvv} onChange={e=>setForm({...form,cvv:e.target.value})}/></label>
        </div>
        <button className="button-primary form-submit">Save card <span aria-hidden="true">↗</span></button>
      </form>
      <p className="privacy-note"><span aria-hidden="true">◈</span> Card number and security code are never stored.</p>
    </section>
    <section className="saved-card-section">
      <div className="panel-heading"><div><p className="eyebrow">IN YOUR WALLET</p><h2>Saved cards</h2></div><span className="panel-index">{String(cards.length).padStart(2, "0")}</span></div>
      <div className="saved-card-list">{cards.map(c=><article key={c.id} className="saved-card-item"><div className="saved-card-icon" aria-hidden="true">▤</div><div className="saved-card-info"><span className="card-kind">{c.card_type} CARD</span><strong>{c.masked_card_number}</strong><small>{c.card_holder_name} · {String(c.expiry_month).padStart(2, "0")}/{c.expiry_year}</small></div><button onClick={()=>remove(c.id)} className="icon-delete" aria-label={`Delete card ending ${c.last4}`} title="Delete card">×</button></article>)}</div>
      {!cards.length && <div className="empty-state"><span className="empty-mark" aria-hidden="true">▤</span><h3>Your wallet is ready</h3><p>Your saved payment methods will appear here.</p></div>}
    </section>
    </div>
  </div>
}

function Payment() {
  const [cards,setCards]=useState([]); const [cardId,setCardId]=useState(""); const [amount,setAmount]=useState(""); const [result,setResult]=useState(null); const [error,setError]=useState("");
  useEffect(()=>{django.get("/api/cards/").then(r=>{setCards(r.data);if(r.data[0])setCardId(r.data[0].id)})},[]);
  async function submit(e){e.preventDefault();setError("");setResult(null);try{const me=await django.get("/api/auth/me/");const token=localStorage.getItem("access")||sessionStorage.getItem("access");const r=await fastapi.post("/payments/",{user_id:me.data.id,card_id:Number(cardId),amount:amount,currency:"INR"},{headers:{Authorization:`Bearer ${token}`}});setResult(r.data)}catch(err){setError(JSON.stringify(err.response?.data||"Payment failed"));}}
  const selectedCard = cards.find(card => String(card.id) === String(cardId));
  return <div className="page-shell payment-page">
    <header className="page-heading"><div><p className="eyebrow">SECURE CHECKOUT</p><h1>Make a payment</h1><p className="page-subtitle">A simple, secure way to move money.</p></div><span className="secure-label"><span aria-hidden="true">◆</span> Protected payment</span></header>
    <div className="payment-layout">
      <section className="surface-panel payment-form-panel">
        <div className="panel-heading"><div><p className="eyebrow">PAYMENT DETAILS</p><h2>Where should we send it?</h2></div><span className="panel-index">01</span></div>
        {error&&<div role="alert" className="form-alert">{error}</div>}
        {result&&<div role="status" className={`payment-result ${result.status === "SUCCESS" ? "is-success" : "is-failed"}`}><span className="result-symbol" aria-hidden="true">{result.status === "SUCCESS" ? "✓" : "!"}</span><div><strong>{result.status === "SUCCESS" ? "Payment complete" : "Payment not completed"}</strong><p>{result.message}</p><small>Reference {result.reference}</small></div></div>}
        <form onSubmit={submit} className="form-stack payment-form">
          <label className="field-label">Pay with<select className="field-control" value={cardId} onChange={e=>setCardId(e.target.value)} required>{cards.map(c=><option key={c.id} value={c.id}>{c.card_type} · {c.masked_card_number}</option>)}</select></label>
          <label className="field-label">Amount<input className="field-control amount-control" type="number" step="0.01" min="0.01" placeholder="0.00" value={amount} onChange={e=>setAmount(e.target.value)} required/><span className="input-currency">INR</span></label>
          <div className="payment-summary"><span>Payment method</span><strong>{selectedCard ? `${selectedCard.card_type} ending ${selectedCard.last4}` : "No card selected"}</strong><span>Processing</span><strong>Instant</strong></div>
          <button disabled={!cards.length} className="button-primary form-submit pay-button">Pay securely <span aria-hidden="true">↗</span></button>
        </form>
        {!cards.length && <div className="empty-inline">No cards saved yet. <Link to="/cards">Add a card</Link> to continue.</div>}
      </section>
      <aside className="payment-aside">
        <div className="checkout-card"><span className="checkout-overline">TOTAL DUE</span><p className="checkout-amount"><span>₹</span>{amount ? Number(amount).toLocaleString("en-IN", {minimumFractionDigits: 2, maximumFractionDigits: 2}) : "0.00"}</p><div className="checkout-rule"/><div className="checkout-method"><span className="mini-card-icon" aria-hidden="true">▤</span><div><small>PAYING WITH</small><strong>{selectedCard ? `•••• ${selectedCard.last4}` : "Select a card"}</strong></div></div><div className="checkout-stamp">PS <span>PAYSECURE</span></div></div>
        <div className="payment-note"><span className="note-icon" aria-hidden="true">◈</span><div><strong>Encrypted & protected</strong><p>Card details stay private. This demo simulates payment processing and does not contact a real gateway.</p></div></div>
      </aside>
    </div>
  </div>
}

function Transactions() {
  const [tx,setTx]=useState([]);
  const [filters,setFilters]=useState({status:"",from_date:"",to_date:"",min_amount:"",max_amount:""});
  async function load(){
    const params=Object.fromEntries(Object.entries(filters).filter(([,value])=>value!==""));
    const r=await django.get("/api/transactions/",{params});setTx(r.data);
  }
  useEffect(()=>{load()},[filters]);
  function updateFilter(event){setFilters({...filters,[event.target.name]:event.target.value});}
  const money = new Intl.NumberFormat("en-IN", {style:"currency",currency:"INR",maximumFractionDigits:2});
  return <div className="page-shell transactions-page">
    <header className="page-heading"><div><p className="eyebrow">YOUR PAYMENT RECORD</p><h1>Activity</h1><p className="page-subtitle">Every payment, clearly accounted for.</p></div><div className="activity-total"><strong>{tx.length}</strong><span>transactions shown</span></div></header>
    <section className="filter-panel" aria-label="Filter transactions">
      <div className="filter-heading"><span className="filter-icon" aria-hidden="true">⌕</span><span>Filter activity</span></div>
      <div className="filter-controls">
        <label className="filter-field"><span>Status</span><select aria-label="Filter by status" name="status" value={filters.status} onChange={updateFilter}><option value="">All statuses</option><option>SUCCESS</option><option>FAILED</option><option>PENDING</option></select></label>
        <label className="filter-field"><span>From</span><input aria-label="From date" name="from_date" type="date" value={filters.from_date} onChange={updateFilter}/></label>
        <label className="filter-field"><span>To</span><input aria-label="To date" name="to_date" type="date" value={filters.to_date} onChange={updateFilter}/></label>
        <label className="filter-field"><span>Minimum</span><input aria-label="Minimum amount" name="min_amount" type="number" min="0" step="0.01" placeholder="₹ 0.00" value={filters.min_amount} onChange={updateFilter}/></label>
        <label className="filter-field"><span>Maximum</span><input aria-label="Maximum amount" name="max_amount" type="number" min="0" step="0.01" placeholder="₹ 0.00" value={filters.max_amount} onChange={updateFilter}/></label>
      </div>
    </section>
    <section className="transactions-panel" aria-label="Transaction history">
      <div className="table-scroll"><table className="transactions-table"><thead><tr><th>Reference</th><th>Amount</th><th>Status</th><th>Payment card</th><th>Date & time</th></tr></thead><tbody>{tx.map(x=><tr key={x.id}><td><span className="reference-cell">{x.reference}</span></td><td className="amount-cell">{money.format(Number(x.amount))}</td><td><StatusBadge status={x.status}/></td><td>{x.card_mask || "—"}</td><td>{new Date(x.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>
      {!tx.length&&<div className="empty-state table-empty"><span className="empty-mark" aria-hidden="true">↗</span><h3>No matching activity</h3><p>Try adjusting the filters or make your first payment.</p></div>}
      <footer className="table-footer"><span>Showing {tx.length} transaction{tx.length === 1 ? "" : "s"}</span><span>Updated just now</span></footer>
    </section>
  </div>
}

function AdminDashboard() {
  const [data,setData]=useState(null);
  useEffect(()=>{django.get("/api/admin/summary/").then(r=>setData(r.data))},[]);
  if(!data)return <div>Loading...</div>;
  return <div><h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1><div className="grid md:grid-cols-4 gap-4">{Object.entries({Transactions:data.total_transactions,Successful:data.successful,Failed:data.failed,Pending:data.pending}).map(([label,value])=><Stat key={label} label={label} value={value} note="All time" marker={label === "Transactions" ? "↗" : label === "Successful" ? "✓" : label === "Failed" ? "!" : "…"} markerClass={label === "Successful" ? "bg-emerald-100 text-emerald-800" : label === "Failed" ? "bg-rose-50 text-rose-700" : "bg-amber-100 text-amber-900"}/>)}</div><div className="bg-white p-6 rounded-2xl shadow mt-6"><h2 className="font-bold">Total Amount</h2><div className="text-3xl mt-2">₹{data.total_amount}</div><a className="inline-block mt-4 text-cyan-700" href={`${import.meta.env.VITE_DJANGO_URL||"http://localhost:8000"}/admin/`}>Open Django Admin</a></div><section className="bg-white p-6 rounded-2xl shadow mt-6"><h2 className="font-bold">Today&apos;s Payments <span className="font-normal text-slate-500">{data.daily.date}</span></h2><dl className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">{[["Payments",data.daily.total_transactions],["Successful",data.daily.successful],["Failed",data.daily.failed],["Pending",data.daily.pending],["Amount",`₹${data.daily.total_amount}`]].map(([label,value])=><div key={label}><dt className="text-slate-500">{label}</dt><dd className="text-xl font-bold mt-1">{value}</dd></div>)}</dl></section></div>;
}

export default function App() {
  return <Layout><Routes>
    <Route path="/login" element={<Login/>}/>
    <Route path="/register" element={<Register/>}/>
    <Route path="/" element={<Protected><Dashboard/></Protected>}/>
    <Route path="/cards" element={<Protected><Cards/></Protected>}/>
    <Route path="/payment" element={<Protected><Payment/></Protected>}/>
    <Route path="/transactions" element={<Protected><Transactions/></Protected>}/>
    <Route path="/admin-dashboard" element={<Protected><AdminDashboard/></Protected>}/>
  </Routes></Layout>
}
