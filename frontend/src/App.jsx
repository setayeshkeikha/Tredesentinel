import { useState } from 'react'
import Heartbeat from './components/Heartbeat.jsx'
import TickLog from './components/TickLog.jsx'
import BacktestPanel from './components/BacktestPanel.jsx'
import BotsPanel from './components/BotsPanel.jsx'
import PortfolioBadge from './components/PortfolioBadge.jsx'
import LoginPanel from './components/LoginPanel.jsx'
import { useLiveFeed } from './hooks/useLiveFeed.js'
import { useAuth } from './hooks/useAuth.jsx'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: '▦' },
  { id: 'backtest', label: 'Backtest', icon: '◈' },
  { id: 'live', label: 'Live Monitor', icon: '◉' },
  { id: 'bots', label: 'Trading Bots', icon: '⚡' },
]

export default function App() {
  const { isAuthenticated, logout } = useAuth()
  const [tab, setTab] = useState('dashboard')

  const {
    connected,
    ticks,
    halted,
    authFailed,
  } = useLiveFeed({ enabled: isAuthenticated })

  if (!isAuthenticated) {
    return <LoginPanel />
  }

  const latestTick = ticks[ticks.length - 1]

  return (
    <div className="app-shell">

      {/* Sidebar */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-mark">
            TS
          </div>

          <div>
            <div className="brand-name">TradeSentinel</div>
            <div className="brand-subtitle">Trading Intelligence</div>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-label">Workspace</div>

          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => setTab(item.id)}
              className={`nav-item ${tab === item.id ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>

              {item.id === 'live' && connected && (
                <span className="nav-live-dot" />
              )}
            </button>
          ))}
        </div>

        <div className="sidebar-bottom">

          <div className="system-card">
            <div className="system-header">
              <span>System status</span>
              <span className={`status-dot ${connected ? 'online' : 'offline'}`} />
            </div>

            <div className="system-status">
              {connected ? 'All systems operational' : 'Reconnecting...'}
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

      {/* Main area */}
      <div className="main-area">

        {/* Topbar */}
        <header className="topbar">

          <div>
            <div className="breadcrumb">
              TradeSentinel / {NAV_ITEMS.find(x => x.id === tab)?.label}
            </div>

            <h1>
              {tab === 'dashboard' && 'Trading Dashboard'}
              {tab === 'backtest' && 'Strategy Backtest'}
              {tab === 'live' && 'Live Monitor'}
              {tab === 'bots' && 'Trading Bots'}
            </h1>
          </div>

          <div className="topbar-right">

            <div className="market-indicator">
              <span className="status-dot online" />
              <span>API Connected</span>
            </div>

            <PortfolioBadge />

            <div className="avatar">
              TS
            </div>

          </div>

        </header>

        {authFailed && (
          <div className="alert alert-danger">
            ⚠ Live feed session expired — please log out and back in.
          </div>
        )}

        {halted && (
          <div className="alert alert-warning">
            ⚠ {halted}
          </div>
        )}

        {/* Content */}
        <main className="content">

          {tab === 'dashboard' && (
            <Dashboard
              ticks={ticks}
              connected={connected}
              latestTick={latestTick}
              onNavigate={setTab}
            />
          )}

          {tab === 'backtest' && <BacktestPanel />}

          {tab === 'live' && (
            <TickLog ticks={ticks} />
          )}

          {tab === 'bots' && (
            <BotsPanel />
          )}

        </main>

      </div>
    </div>
  )
}


function Dashboard({
  ticks,
  connected,
  latestTick,
  onNavigate,
}) {

  const portfolioValue =
    latestTick?.portfolio_value ?? 10000

  const tickCount = ticks.length

  return (
    <div className="dashboard">

      {/* Hero */}
      <section className="dashboard-hero">

        <div>
          <div className="eyebrow">
            PORTFOLIO OVERVIEW
          </div>

          <div className="hero-value">
            ${portfolioValue.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>

          <div className="hero-change positive">
            <span>↑</span>
            Paper trading environment
          </div>
        </div>

        <div className="hero-actions">

          <button
            onClick={() => onNavigate('backtest')}
            className="primary-button"
          >
            Run Backtest
          </button>

          <button
            onClick={() => onNavigate('bots')}
            className="secondary-button"
          >
            Manage Bots
          </button>

        </div>

      </section>


      {/* Metrics */}
      <section className="metrics-grid">

        <MetricCard
          label="Total Equity"
          value={`$${portfolioValue.toLocaleString()}`}
          change="+0.00%"
          positive
        />

        <MetricCard
          label="Active Signals"
          value={tickCount}
          change={connected ? 'LIVE' : 'OFFLINE'}
          positive={connected}
        />

        <MetricCard
          label="Trading Mode"
          value="PAPER"
          change="SAFE MODE"
        />

        <MetricCard
          label="System Status"
          value={connected ? 'ONLINE' : 'OFFLINE'}
          change={connected ? 'Operational' : 'Reconnecting'}
          positive={connected}
        />

      </section>


      {/* Main grid */}
      <section className="dashboard-grid">

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
              {connected ? 'LIVE' : 'PAUSED'}
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
                <div className="empty-icon">⌁</div>
                <div>Waiting for trading activity</div>
                <span>
                  Start a bot to populate the live portfolio stream.
                </span>
              </div>
            )}

          </div>

        </div>


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
              onClick={() => onNavigate('live')}
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
              .map((tick, index) => (

                <div
                  key={index}
                  className="activity-item"
                >

                  <div className={`signal-icon ${tick.signal}`}>
                    {tick.signal === 'buy'
                      ? '↑'
                      : tick.signal === 'sell'
                        ? '↓'
                        : '•'}
                  </div>

                  <div className="activity-main">

                    <div className="activity-symbol">
                      {tick.symbol}
                    </div>

                    <div className="activity-reason">
                      {tick.reason || 'Strategy signal'}
                    </div>

                  </div>

                  <div className="activity-price">
                    {tick.price?.toLocaleString(undefined, {
                      maximumFractionDigits: 2,
                    })}
                  </div>

                </div>

              ))}

          </div>

        </div>

      </section>


      {/* Bottom cards */}
      <section className="bottom-grid">

        <QuickAction
          icon="◈"
          title="Strategy Backtest"
          description="Test RSI, MACD and other strategies against historical data."
          button="Open Backtest"
          onClick={() => onNavigate('backtest')}
        />

        <QuickAction
          icon="⚡"
          title="Trading Bots"
          description="Create, start, pause and monitor automated trading bots."
          button="Manage Bots"
          onClick={() => onNavigate('bots')}
        />

        <QuickAction
          icon="◉"
          title="Live Monitor"
          description="Watch strategy signals and trading activity in real time."
          button="Open Monitor"
          onClick={() => onNavigate('live')}
        />

      </section>

    </div>
  )
}


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

      <div className={`metric-change ${positive ? 'positive' : ''}`}>
        {change}
      </div>

    </div>
  )
}


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
