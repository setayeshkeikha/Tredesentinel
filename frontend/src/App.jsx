import { useState } from 'react'
import Heartbeat from './components/Heartbeat.jsx'
import TickLog from './components/TickLog.jsx'
import BacktestPanel from './components/BacktestPanel.jsx'
import { useLiveFeed } from './hooks/useLiveFeed.js'

const API_URL =
  import.meta.env.VITE_API_BASE_URL ||
  'https://tredesentinel7.onrender.com'

const NAV_ITEMS = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: '▦',
  },
  {
    id: 'backtest',
    label: 'Backtest',
    icon: '◈',
  },
  {
    id: 'live',
    label: 'Live Monitor',
    icon: '◉',
  },
]

export default function App() {
  const [authenticated, setAuthenticated] = useState(
    Boolean(localStorage.getItem('access_token'))
  )

  const [tab, setTab] = useState('dashboard')

  // login / register
  const [authMode, setAuthMode] = useState('login')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [authError, setAuthError] = useState('')
  const [authSuccess, setAuthSuccess] = useState('')

  const [loggingIn, setLoggingIn] = useState(false)
  const [registering, setRegistering] = useState(false)

  const {
    connected,
    ticks,
    halted,
  } = useLiveFeed()

  /*
   * =========================
   * LOGIN
   * =========================
   */

  async function login(event) {
    event.preventDefault()

    setAuthError('')
    setAuthSuccess('')
    setLoggingIn(true)

    try {
      const body = new URLSearchParams()

      body.append('username', email)
      body.append('password', password)

      const response = await fetch(
        `${API_URL}/api/v1/auth/login`,
        {
          method: 'POST',
          headers: {
            'Content-Type':
              'application/x-www-form-urlencoded',
          },
          body,
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail ||
            'Incorrect email or password'
        )
      }

      localStorage.setItem(
        'access_token',
        data.access_token
      )

      if (data.refresh_token) {
        localStorage.setItem(
          'refresh_token',
          data.refresh_token
        )
      }

      setAuthenticated(true)
      setPassword('')
      setAuthError('')
      setAuthSuccess('')
      setTab('dashboard')
    } catch (error) {
      setAuthError(
        error.message ||
          'Unable to sign in'
      )
    } finally {
      setLoggingIn(false)
    }
  }

  /*
   * =========================
   * REGISTER
   * =========================
   */

  async function register(event) {
    event.preventDefault()

    setAuthError('')
    setAuthSuccess('')
    setRegistering(true)

    try {
      const response = await fetch(
        `${API_URL}/api/v1/auth/register`,
        {
          method: 'POST',
          headers: {
            'Content-Type':
              'application/json',
          },
          body: JSON.stringify({
            email,
            password,
          }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        let message =
          'Registration failed'

        if (typeof data.detail === 'string') {
          message = data.detail
        }

        throw new Error(message)
      }

      /*
       * Registration succeeded.
       * Switch back to Login.
       */

      setAuthMode('login')
      setAuthSuccess(
        'Account created successfully. You can now sign in.'
      )

      setPassword('')
      setAuthError('')
    } catch (error) {
      setAuthError(
        error.message ||
          'Registration failed'
      )
    } finally {
      setRegistering(false)
    }
  }

  /*
   * =========================
   * LOGOUT
   * =========================
   */

  async function logout() {
    const token =
      localStorage.getItem(
        'access_token'
      )

    try {
      if (token) {
        await fetch(
          `${API_URL}/api/v1/auth/logout`,
          {
            method: 'POST',
            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        )
      }
    } catch {
      // Ignore logout network errors
    }

    localStorage.removeItem(
      'access_token'
    )

    localStorage.removeItem(
      'refresh_token'
    )

    setAuthenticated(false)
    setAuthMode('login')
    setEmail('')
    setPassword('')
    setAuthError('')
    setAuthSuccess('')
    setTab('dashboard')
  }

  /*
   * =========================
   * AUTH SCREEN
   * =========================
   */

  if (!authenticated) {
    return (
      <LoginScreen
        mode={authMode}
        email={email}
        password={password}
        setEmail={setEmail}
        setPassword={setPassword}
        onSubmit={
          authMode === 'login'
            ? login
            : register
        }
        error={authError}
        success={authSuccess}
        loading={
          authMode === 'login'
            ? loggingIn
            : registering
        }
        onSwitchMode={() => {
          setAuthMode(
            authMode === 'login'
              ? 'register'
              : 'login'
          )

          setAuthError('')
          setAuthSuccess('')
        }}
      />
    )
  }

  const latestTick =
    ticks[ticks.length - 1]

  return (
    <div className="app-shell">

      {/* =========================
          SIDEBAR
      ========================= */}

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">
            TS
          </div>

          <div>
            <div className="brand-name">
              TradeSentinel
            </div>

            <div className="brand-subtitle">
              Trading Intelligence
            </div>
          </div>

        </div>

        <div className="sidebar-section">

          <div className="sidebar-label">
            Workspace
          </div>

          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() =>
                setTab(item.id)
              }
              className={`nav-item ${
                tab === item.id
                  ? 'active'
                  : ''
              }`}
            >

              <span className="nav-icon">
                {item.icon}
              </span>

              <span>
                {item.label}
              </span>

              {item.id === 'live' &&
                connected && (
                  <span className="nav-live-dot" />
                )}

            </button>
          ))}

        </div>

        <div className="sidebar-bottom">

          <div className="system-card">

            <div className="system-header">

              <span>
                System status
              </span>

              <span
                className={`status-dot ${
                  connected
                    ? 'online'
                    : 'offline'
                }`}
              />

            </div>

            <div className="system-status">
              {connected
                ? 'All systems operational'
                : 'Live feed offline'}
            </div>

            <div className="system-mode">
              PAPER TRADING
            </div>

          </div>

          <button
            onClick={logout}
            className="logout-button"
          >
            <span>↪</span>
            Sign out
          </button>

        </div>

      </aside>

      {/* =========================
          MAIN AREA
      ========================= */}

      <div className="main-area">

        {/* TOPBAR */}

        <header className="topbar">

          <div>

            <div className="breadcrumb">
              TradeSentinel /{' '}
              {
                NAV_ITEMS.find(
                  (x) =>
                    x.id === tab
                )?.label
              }
            </div>

            <h1>

              {tab === 'dashboard' &&
                'Trading Dashboard'}

              {tab === 'backtest' &&
                'Strategy Backtest'}

              {tab === 'live' &&
                'Live Monitor'}

            </h1>

          </div>

          <div className="topbar-right">

            <div className="market-indicator">

              <span
                className={`status-dot ${
                  connected
                    ? 'online'
                    : 'offline'
                }`}
              />

              <span>
                {connected
                  ? 'API Connected'
                  : 'API Offline'}
              </span>

            </div>

            <div className="portfolio-badge">

              <span>
                Portfolio
              </span>

              <strong>

                $
                {(
                  latestTick
                    ?.portfolio_value ??
                  10000
                ).toLocaleString(
                  undefined,
                  {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  }
                )}

              </strong>

            </div>

            <div className="avatar">
              TS
            </div>

          </div>

        </header>

        {halted && (
          <div className="alert alert-warning">
            ⚠ {halted}
          </div>
        )}

        {/* =========================
            CONTENT
        ========================= */}

        <main className="content">

          {tab === 'dashboard' && (
            <Dashboard
              ticks={ticks}
              connected={connected}
              latestTick={latestTick}
              onNavigate={setTab}
            />
          )}

          {tab === 'backtest' && (
            <BacktestPanel />
          )}

          {tab === 'live' && (
            <div className="panel live-panel">

              <div className="panel-header">

                <div>

                  <div className="panel-title">
                    Live Trading Activity
                  </div>

                  <div className="panel-subtitle">
                    Real-time strategy signals
                  </div>

                </div>

                <div className="chart-badge">
                  {connected
                    ? 'LIVE'
                    : 'OFFLINE'}
                </div>

              </div>

              <TickLog
                ticks={ticks}
              />

            </div>
          )}

        </main>

      </div>

    </div>
  )
}


/*
 * =====================================================
 * LOGIN / REGISTER SCREEN
 * =====================================================
 */

function LoginScreen({
  mode,
  email,
  password,
  setEmail,
  setPassword,
  onSubmit,
  error,
  success,
  loading,
  onSwitchMode,
}) {
  const isLogin =
    mode === 'login'

  return (
    <div className="login-page">

      <div className="login-background" />

      <div className="login-card">

        {/* LOGO */}

        <div className="login-logo">
          TS
        </div>

        <h1>
          TradeSentinel
        </h1>

        <p>
          Trading Intelligence Platform
        </p>

        {/* TITLE */}

        <div className="auth-heading">

          {isLogin
            ? 'Welcome back'
            : 'Create your account'}

        </div>

        <div className="auth-description">

          {isLogin
            ? 'Sign in to access your trading dashboard.'
            : 'Create an account to start using TradeSentinel.'}

        </div>

        {/* ERROR */}

        {error && (
          <div className="login-message">

            <span>
              ⚠
            </span>

            <span>
              {error}
            </span>

          </div>
        )}

        {/* SUCCESS */}

        {success && (
          <div className="login-message success">

            <span>
              ✓
            </span>

            <span>
              {success}
            </span>

          </div>
        )}

        {/* FORM */}

        <form onSubmit={onSubmit}>

          <label>
            Email
          </label>

          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) =>
              setEmail(
                event.target.value
              )
            }
            required
            autoComplete="email"
          />

          <label>
            Password
          </label>

          <input
            type="password"
            placeholder="Your password"
            value={password}
            onChange={(event) =>
              setPassword(
                event.target.value
              )
            }
            required
            minLength={6}
            autoComplete={
              isLogin
                ? 'current-password'
                : 'new-password'
            }
          />

          <button
            type="submit"
            disabled={loading}
            className="login-button"
          >

            {loading
              ? isLogin
                ? 'Signing in...'
                : 'Creating account...'
              : isLogin
                ? 'Sign in'
                : 'Create account'}

          </button>

        </form>

        {/* SWITCH */}

        <div className="auth-switch">

          <span>

            {isLogin
              ? "Don't have an account?"
              : 'Already have an account?'}

          </span>

          <button
            type="button"
            onClick={onSwitchMode}
            className="auth-switch-button"
          >

            {isLogin
              ? 'Create account'
              : 'Sign in'}

          </button>

        </div>

        <div className="login-footer">
          PAPER TRADING ENVIRONMENT
        </div>

      </div>

    </div>
  )
}


/*
 * =====================================================
 * DASHBOARD
 * =====================================================
 */

function Dashboard({
  ticks,
  connected,
  latestTick,
  onNavigate,
}) {
  const portfolioValue =
    latestTick
      ?.portfolio_value ??
    10000

  const tickCount =
    ticks.length

  return (
    <div className="dashboard">

      {/* HERO */}

      <section className="dashboard-hero">

        <div>

          <div className="eyebrow">
            PORTFOLIO OVERVIEW
          </div>

          <div className="hero-value">

            $
            {portfolioValue.toLocaleString(
              undefined,
              {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              }
            )}

          </div>

          <div className="hero-change positive">

            <span>
              ↑
            </span>

            Paper trading environment

          </div>

        </div>

        <div className="hero-actions">

          <button
            onClick={() =>
              onNavigate('backtest')
            }
            className="primary-button"
          >
            Run Backtest
          </button>

          <button
            onClick={() =>
              onNavigate('live')
            }
            className="secondary-button"
          >
            Live Monitor
          </button>

        </div>

      </section>

      {/* METRICS */}

      <section className="metrics-grid">

        <MetricCard
          label="Total Equity"
          value={`$${portfolioValue.toLocaleString()}`}
          change="+0.00%"
          positive
        />

        <MetricCard
          label="Live Signals"
          value={tickCount}
          change={
            connected
              ? 'LIVE'
              : 'OFFLINE'
          }
          positive={connected}
        />

        <MetricCard
          label="Trading Mode"
          value="PAPER"
          change="SAFE MODE"
        />

        <MetricCard
          label="System Status"
          value={
            connected
              ? 'ONLINE'
              : 'OFFLINE'
          }
          change={
            connected
              ? 'Operational'
              : 'Reconnecting'
          }
          positive={connected}
        />

      </section>

      {/* DASHBOARD GRID */}

      <section className="dashboard-grid">

        {/* CHART */}

        <div className="panel chart-panel">

          <div className="panel-header">

            <div>

              <div className="panel-title">
                Portfolio Activity
              </div>

              <div className="panel-subtitle">
                Real-time portfolio monitoring
              </div>

            </div>

            <div className="chart-badge">

              {connected
                ? 'LIVE'
                : 'PAUSED'}

            </div>

          </div>

          <div className="dashboard-chart">

            {ticks.length > 1 ? (

              <Heartbeat
                ticks={ticks}
                connected={connected}
              />

            ) : (

              <div className="empty-chart">

                <div className="empty-icon">
                  ⌁
                </div>

                <div>
                  Waiting for trading activity
                </div>

                <span>
                  Live portfolio signals
                  will appear here.
                </span>

              </div>

            )}

          </div>

        </div>

        {/* RECENT SIGNALS */}

        <div className="panel activity-panel">

          <div className="panel-header">

            <div>

              <div className="panel-title">
                Recent Signals
              </div>

              <div className="panel-subtitle">
                Latest strategy decisions
              </div>

            </div>

            <button
              className="text-button"
              onClick={() =>
                onNavigate('live')
              }
            >
              View all →
            </button>

          </div>

          <div className="activity-list">

            {ticks.length === 0 && (
              <div className="empty-state">
                No signals yet
              </div>
            )}

            {[...ticks]
              .reverse()
              .slice(0, 5)
              .map(
                (
                  tick,
                  index
                ) => (

                  <div
                    key={index}
                    className="activity-item"
                  >

                    <div
                      className={`signal-icon ${
                        tick.signal ||
                        'neutral'
                      }`}
                    >

                      {tick.signal ===
                      'buy'
                        ? '↑'
                        : tick.signal ===
                            'sell'
                          ? '↓'
                          : '•'}

                    </div>

                    <div className="activity-main">

                      <div className="activity-symbol">
                        {tick.symbol ||
                          'Market'}
                      </div>

                      <div className="activity-reason">
                        {tick.reason ||
                          'Strategy signal'}
                      </div>

                    </div>

                    <div className="activity-price">

                      {tick.price
                        ? tick.price.toLocaleString(
                            undefined,
                            {
                              maximumFractionDigits: 2,
                            }
                          )
                        : '—'}

                    </div>

                  </div>

                )
              )}

          </div>

        </div>

      </section>

      {/* QUICK ACTIONS */}

      <section className="bottom-grid">

        <QuickAction
          icon="◈"
          title="Strategy Backtest"
          description="Test your trading strategies against historical or demo market data."
          button="Open Backtest"
          onClick={() =>
            onNavigate('backtest')
          }
        />

        <QuickAction
          icon="◉"
          title="Live Monitor"
          description="Watch strategy signals and portfolio activity in real time."
          button="Open Monitor"
          onClick={() =>
            onNavigate('live')
          }
        />

        <QuickAction
          icon="⚙"
          title="Trading Environment"
          description="Currently running in paper trading mode for safe testing."
          button="Paper Mode"
          onClick={() => {}}
        />

      </section>

    </div>
  )
}


/*
 * =====================================================
 * METRIC CARD
 * =====================================================
 */

function MetricCard({
  label,
  value,
  change,
  positive,
}) {
  return (
    <div className="metric-card">

      <div className="metric-label">
        {label}
      </div>

      <div className="metric-value">
        {value}
      </div>

      <div
        className={`metric-change ${
          positive
            ? 'positive'
            : ''
        }`}
      >
        {change}
      </div>

    </div>
  )
}


/*
 * =====================================================
 * QUICK ACTION
 * =====================================================
 */

function QuickAction({
  icon,
  title,
  description,
  button,
  onClick,
}) {
  return (
    <div className="quick-card">

      <div className="quick-icon">
        {icon}
      </div>

      <div className="quick-title">
        {title}
      </div>

      <div className="quick-description">
        {description}
      </div>

      <button
        onClick={onClick}
        className="quick-button"
      >
        {button} →
      </button>

    </div>
  )
             }
