import { useState, useEffect } from 'react'
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine,
    AreaChart, Area
} from 'recharts'
import Select from '../components/Select'
import { getDiseases, getStates, getData } from '../api/client'
import './Dashboard.css'

const API_BASE = 'http://localhost:5001'

const DISEASE_META = {
    covid: { icon: '', label: 'COVID-19', color: '#667eea' },
    dengue: { icon: '', label: 'Dengue', color: '#f5576c' },
    malaria: { icon: '', label: 'Malaria', color: '#4facfe' },
    idsp: { icon: '', label: 'IDSP', color: '#38ef7d' },
}

const MODEL_META = {
    arima: { label: 'ARIMA', color: '#f5576c' },
    sarima: { label: 'SARIMA', color: '#4facfe' },
    linear: { label: 'Linear Regression', color: '#f9ca24' },
}

function fmtDate(d) {
    if (!d) return ''
    try {
        const dt = new Date(d)
        const q = Math.ceil((dt.getMonth() + 1) / 3)
        return `Q${q} ${dt.getFullYear()}`
    } catch { return String(d) }
}

function fmtN(n) {
    if (n === null || n === undefined || isNaN(n)) return '—'
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
    return Number(n).toLocaleString('en-IN')
}

const TOOLTIP_STYLE = { background: '#1a1f2e', border: '1px solid #2d3561', borderRadius: 8, fontSize: 13 }

export default function Dashboard() {
    const [selectedDisease, setSelectedDisease] = useState('')
    const [selectedState, setSelectedState] = useState('')
    const [diseases, setDiseases] = useState([])
    const [states, setStates] = useState([])
    const [caseData, setCaseData] = useState([])
    const [forecastData, setForecastData] = useState(null)
    const [comparisonData, setComparisonData] = useState([])
    const [loadingDiseases, setLoadingDiseases] = useState(true)
    const [loadingStates, setLoadingStates] = useState(false)
    const [loadingData, setLoadingData] = useState(false)
    const [loadingForecast, setLoadingForecast] = useState(false)
    const [error, setError] = useState(null)

    // Load diseases on mount
    useEffect(() => {
        getDiseases()
            .then(setDiseases)
            .catch(e => setError(e.message))
            .finally(() => setLoadingDiseases(false))
    }, [])

    // Load states + comparison when disease changes
    useEffect(() => {
        if (!selectedDisease) {
            setStates([]); setSelectedState(''); setCaseData([])
            setForecastData(null); setComparisonData([])
            return
        }
        setLoadingStates(true)
        getStates(selectedDisease)
            .then(s => { setStates(s); setSelectedState('') })
            .catch(e => setError(e.message))
            .finally(() => setLoadingStates(false))

        fetch(`${API_BASE}/api/comparison?disease_key=${selectedDisease}&top=10`)
            .then(r => r.json())
            .then(d => setComparisonData(Array.isArray(d.data) ? d.data : []))
            .catch(() => { })
    }, [selectedDisease])

    // Load data + forecast when state changes
    useEffect(() => {
        if (!selectedDisease || !selectedState) {
            setCaseData([]); setForecastData(null); return
        }
        setLoadingData(true)
        setLoadingForecast(true)
        getData(selectedDisease, selectedState)
            .then(d => setCaseData(Array.isArray(d) ? d : []))
            .catch(e => setError(e.message))
            .finally(() => setLoadingData(false))

        fetch(`${API_BASE}/api/forecast?disease_key=${selectedDisease}&state=${encodeURIComponent(selectedState)}&steps=4`)
            .then(r => r.json())
            .then(d => setForecastData(d))
            .catch(() => { })
            .finally(() => setLoadingForecast(false))
    }, [selectedDisease, selectedState])

    const meta = DISEASE_META[selectedDisease] || { icon: '', label: selectedDisease, color: '#667eea' }
    const sortedData = [...caseData].sort((a, b) => new Date(a.time_index) - new Date(b.time_index))
    const totalCases = sortedData.reduce((s, r) => s + (Number(r.cases) || 0), 0)
    const totalDeaths = sortedData.reduce((s, r) => s + (Number(r.deaths) || 0), 0)
    const cfr = totalCases > 0 ? ((totalDeaths / totalCases) * 100).toFixed(2) : '—'
    const latestRow = sortedData[sortedData.length - 1]

    // Trend chart data
    const trendData = sortedData.map(r => ({
        date: fmtDate(r.time_index),
        cases: Number(r.cases) || 0,
        deaths: Number(r.deaths) || 0,
    }))

    // Forecast chart data — full history
    let forecastChart = []
    // Zoomed forecast chart — last 6 historical quarters + 4 future
    let zoomedForecastChart = []
    const models = forecastData?.models || {}
    if (forecastData && !forecastData.error) {
        const allHist = (forecastData.historical || []).map(h => ({
            date: fmtDate(h.date), actual: h.actual
        }))
        const futureDates = forecastData.future_dates || []
        const futureRows = futureDates.map((d, i) => ({
            date: fmtDate(d),
            arima: models.arima?.forecast?.[i] ?? null,
            sarima: models.sarima?.forecast?.[i] ?? null,
            linear: models.linear?.forecast?.[i] ?? null,
        }))
        forecastChart = [...allHist, ...futureRows]
        // Zoomed: take only last 6 quarters of history + all future
        const recentHist = allHist.slice(-6)
        zoomedForecastChart = [...recentHist, ...futureRows]
    }

    const lastHistDate = forecastData?.historical?.slice(-1)?.[0]?.date
        ? fmtDate(forecastData.historical.slice(-1)[0].date)
        : null

    return (
        <div className="dashboard">

            {/* ── Hero ── */}
            <header className="dashboard-header">
                <div className="container">
                    <div className="hero-top">
                        <div className="hero-left">
                            <div className="project-kicker">NTCC Final Year Project • 2024–25</div>
                            <h1 className="hero-title">
                                Data-Driven Computational Approaches<br />
                                for <span className="gradient-text">Forecasting Infectious Diseases</span>
                            </h1>
                            <p className="hero-subtitle">
                                Multi-disease surveillance platform using ARIMA, SARIMA &amp; ML models on India&apos;s epidemiological data
                            </p>
                            <div className="hero-pills">
                                {['COVID-19', 'Dengue', 'Malaria', 'IDSP'].map(p => <span key={p} className="pill">{p}</span>)}
                                {['ARIMA', 'SARIMA', 'Linear Regression'].map(p => <span key={p} className="pill pill-model">{p}</span>)}
                            </div>
                        </div>
                        <div className="hero-right">
                            <div className="hero-stat-box">
                                {[['4', 'Diseases'], ['3', 'ML Models'], ['36+', 'States'], ['5yr', 'Data Range']].map(([n, l]) => (
                                    <div key={l} className="hstat">
                                        <div className="hstat-n">{n}</div>
                                        <div className="hstat-l">{l}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="dashboard-main">
                <div className="container">

                    {error && (
                        <div className="error-banner fade-in">
                            <span>{error}</span>
                            <button className="error-dismiss" onClick={() => setError(null)}>✕</button>
                        </div>
                    )}

                    {/* ── Selection ── */}
                    <section className="selection-panel glass fade-in">
                        <h2 className="panel-title">Explore Disease Data</h2>
                        <p className="panel-description">Select a disease and state to view historical trends and ML forecasts</p>
                        <div className="selection-grid">
                            <Select id="disease-select" label="Disease" value={selectedDisease}
                                onChange={setSelectedDisease} options={diseases}
                                placeholder="Select a disease" loading={loadingDiseases} disabled={loadingDiseases} />
                            <Select id="state-select" label="State / UT" value={selectedState}
                                onChange={setSelectedState} options={states}
                                placeholder={selectedDisease ? 'Select a state' : 'Choose disease first'}
                                loading={loadingStates} disabled={!selectedDisease || loadingStates} />
                        </div>
                    </section>

                    {/* ── State Comparison Bar Chart — hide when state selected ── */}
                    {selectedDisease && !selectedState && comparisonData.length > 0 && (
                        <section className="chart-section glass fade-in">
                            <h2 className="section-heading">{meta.icon} Top States — {meta.label}</h2>
                            <p className="section-desc">Total reported cases by state across all available years. Ranked in descending order.</p>
                            <div style={{ height: 420 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart
                                        key={`chart-${selectedDisease}`}
                                        data={comparisonData}
                                        layout="vertical"
                                        margin={{ left: 20, right: 60, top: 20, bottom: 5 }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                                        <XAxis type="number" tick={{ fill: '#8898aa', fontSize: 11 }} tickFormatter={fmtN} domain={[0, 'auto']} hide={false} />
                                        <YAxis type="category" dataKey="state" tick={{ fill: '#cdd5df', fontSize: 11 }} width={130} />
                                        <Tooltip
                                            contentStyle={TOOLTIP_STYLE}
                                            cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                            formatter={(v) => [Number(v).toLocaleString('en-IN'), 'Total Cases']}
                                        />
                                        <Bar
                                            dataKey="total_cases"
                                            fill={meta.color || '#667eea'}
                                            name="Total Cases"
                                            barSize={24}
                                            minPointSize={10}
                                            isAnimationActive={true}
                                        />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </section>
                    )}

                    {/* ── Stats + Trend Chart ── */}
                    {selectedState && !loadingData && caseData.length > 0 && (
                        <>
                            <div className="stats-grid fade-in">
                                {[
                                    { label: 'Total Cases', value: fmtN(totalCases), color: meta.color, sub: 'All periods combined' },
                                    { label: 'Total Deaths', value: fmtN(totalDeaths), color: '#fc466b', sub: 'Reported mortality' },
                                    { label: 'Case Fatality Rate', value: `${cfr}%`, color: '#f9ca24', sub: 'Deaths per 100 cases' },
                                    { label: 'Latest Period', value: fmtDate(latestRow?.time_index), color: '#38ef7d', sub: `${fmtN(latestRow?.cases)} cases` },
                                ].map(s => (
                                    <div key={s.label} className="stat-card glass">
                                        <div className="stat-label">{s.label}</div>
                                        <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
                                        <div className="stat-sub">{s.sub}</div>
                                    </div>
                                ))}
                            </div>

                            <section className="chart-section glass fade-in">
                                <h2 className="section-heading">Quarterly Trend — {selectedState}</h2>
                                <p className="section-desc">Cases (area) and deaths (line) plotted quarterly. Peaks represent outbreak waves.</p>
                                <div style={{ height: 300 }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={trendData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                                            <defs>
                                                <linearGradient id="caseGrad" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor={meta.color} stopOpacity={0.4} />
                                                    <stop offset="95%" stopColor={meta.color} stopOpacity={0.02} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                            <XAxis dataKey="date" tick={{ fill: '#8898aa', fontSize: 10 }} />
                                            <YAxis tickFormatter={fmtN} tick={{ fill: '#8898aa', fontSize: 10 }} />
                                            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n) => [Number(v).toLocaleString('en-IN'), n]} />
                                            <Legend />
                                            <Area type="monotone" dataKey="cases" stroke={meta.color} strokeWidth={2}
                                                fill="url(#caseGrad)" name="Cases" dot={false} />
                                            <Line type="monotone" dataKey="deaths" stroke="#fc466b" strokeWidth={1.5}
                                                name="Deaths" dot={false} />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            </section>
                        </>
                    )}

                    {loadingData && (
                        <div className="loading-inline glass fade-in">
                            <div className="spinner" />
                            <span>Loading data for {selectedState}…</span>
                        </div>
                    )}

                    {/* ── Forecast section ── */}
                    {selectedState && (
                        <section className="chart-section glass fade-in">
                            <h2 className="section-heading">ML Forecast — Next 4 Quarters</h2>
                            <p className="section-desc">
                                Three models trained on historical data and projected 4 quarters beyond the last recorded quarter.
                            </p>

                            {/* How to read box */}
                            <div className="how-to-read">
                                <div className="htr-title">How to read this chart</div>
                                <div className="htr-grid">
                                    <div className="htr-item">
                                        <span className="htr-dot" style={{ background: '#fff' }} />
                                        <div><strong>White line = Actual data</strong><br />Real reported cases up to the last available quarter.</div>
                                    </div>
                                    <div className="htr-item">
                                        <span className="htr-dot" style={{ background: '#f5576c' }} />
                                        <div><strong>Red dashed = ARIMA prediction</strong><br />Captures overall trend direction (declining / rising).</div>
                                    </div>
                                    <div className="htr-item">
                                        <span className="htr-dot" style={{ background: '#4facfe' }} />
                                        <div><strong>Blue dashed = SARIMA prediction</strong><br />Detects seasonal waves (e.g. monsoon spikes). May predict a resurgence if seasonal patterns existed historically.</div>
                                    </div>
                                    <div className="htr-item">
                                        <span className="htr-dot" style={{ background: '#f9ca24' }} />
                                        <div><strong>Yellow dashed = Linear Regression</strong><br />Baseline straight-line trend. Simple but interpretable.</div>
                                    </div>
                                </div>
                                <div className="htr-insight">
                                    <strong>Key insight:</strong> When models disagree, it means the disease pattern is complex.
                                    SARIMA predicting a spike while ARIMA stays low often indicates a historical seasonal pattern
                                    that may or may not repeat — this divergence itself is a valuable finding.
                                </div>
                            </div>

                            {loadingForecast && (
                                <div className="loading-inline">
                                    <div className="spinner" />
                                    <span>Running ARIMA &amp; SARIMA models…</span>
                                </div>
                            )}

                            {!loadingForecast && forecastData && !forecastData.error && zoomedForecastChart.length > 0 && (
                                <>
                                    {/* ── Zoomed Forecast Chart (main) ── */}
                                    <div className="chart-label">Forecast Window — Last 6 Quarters + Next 4 Predicted</div>
                                    <div style={{ height: 320 }}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={zoomedForecastChart} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                <XAxis dataKey="date" tick={{ fill: '#8898aa', fontSize: 11 }} />
                                                <YAxis tickFormatter={fmtN} tick={{ fill: '#8898aa', fontSize: 11 }} />
                                                <Tooltip contentStyle={TOOLTIP_STYLE}
                                                    formatter={(v, n) => [v != null ? Number(v).toLocaleString('en-IN') : '—', n]} />
                                                <Legend wrapperStyle={{ paddingTop: 12 }} />
                                                {lastHistDate && (
                                                    <ReferenceLine x={lastHistDate} stroke="rgba(255,255,255,0.35)"
                                                        strokeDasharray="6 3"
                                                        label={{ value: 'Forecast starts', fill: '#a5b4fc', fontSize: 11, position: 'insideTopLeft' }} />
                                                )}
                                                <Line type="monotone" dataKey="actual" stroke="#ffffff" strokeWidth={3}
                                                    name="Actual" dot={{ r: 4, fill: '#fff' }} connectNulls={false} />
                                                <Line type="monotone" dataKey="arima" stroke={MODEL_META.arima.color}
                                                    strokeWidth={2.5} strokeDasharray="8 3" dot={{ r: 5, fill: MODEL_META.arima.color }}
                                                    name="ARIMA" connectNulls activeDot={{ r: 7 }} />
                                                <Line type="monotone" dataKey="sarima" stroke={MODEL_META.sarima.color}
                                                    strokeWidth={2.5} strokeDasharray="8 3" dot={{ r: 5, fill: MODEL_META.sarima.color }}
                                                    name="SARIMA" connectNulls activeDot={{ r: 7 }} />
                                                <Line type="monotone" dataKey="linear" stroke={MODEL_META.linear.color}
                                                    strokeWidth={2} strokeDasharray="4 4" dot={{ r: 4, fill: MODEL_META.linear.color }}
                                                    name="Linear Regression" connectNulls activeDot={{ r: 6 }} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>

                                    {/* ── Full History Context Chart ── */}
                                    <div className="chart-label" style={{ marginTop: 28 }}>Full Historical Trend — All Quarters</div>
                                    <div style={{ height: 220 }}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={forecastChart} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                                                <XAxis dataKey="date" tick={{ fill: '#8898aa', fontSize: 9 }} interval="preserveStartEnd" />
                                                <YAxis tickFormatter={fmtN} tick={{ fill: '#8898aa', fontSize: 9 }} />
                                                <Tooltip contentStyle={TOOLTIP_STYLE}
                                                    formatter={(v, n) => [v != null ? Number(v).toLocaleString('en-IN') : '—', n]} />
                                                {lastHistDate && (
                                                    <ReferenceLine x={lastHistDate} stroke="rgba(255,255,255,0.2)" strokeDasharray="6 3" />
                                                )}
                                                <Line type="monotone" dataKey="actual" stroke={meta.color} strokeWidth={2}
                                                    name="Actual" dot={false} connectNulls={false} />
                                                <Line type="monotone" dataKey="arima" stroke={MODEL_META.arima.color}
                                                    strokeWidth={1.5} dot={{ r: 3 }} name="ARIMA" connectNulls />
                                                <Line type="monotone" dataKey="sarima" stroke={MODEL_META.sarima.color}
                                                    strokeWidth={1.5} dot={{ r: 3 }} name="SARIMA" connectNulls />
                                                <Line type="monotone" dataKey="linear" stroke={MODEL_META.linear.color}
                                                    strokeWidth={1} dot={false} name="Linear" connectNulls />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>

                                    {/* Model info cards */}
                                    <div className="model-cards-grid">
                                        {Object.entries(models)
                                            .filter(([, v]) => !v.error)
                                            .map(([k, v]) => (
                                                <div key={k} className="model-card"
                                                    style={{ borderTop: `3px solid ${MODEL_META[k]?.color}` }}>
                                                    <div className="model-card-header">
                                                        <span className="model-badge"
                                                            style={{ background: MODEL_META[k]?.color }}>
                                                            {MODEL_META[k]?.label}
                                                        </span>
                                                        <span className="model-aic">
                                                            {v.aic ? `AIC ${v.aic}` : v.r2 != null ? `R² ${v.r2}` : ''}
                                                        </span>
                                                    </div>
                                                    <div className="model-metrics">
                                                        <div><span>RMSE</span><strong>{Number(v.rmse).toLocaleString()}</strong></div>
                                                        <div><span>MAE</span><strong>{Number(v.mae).toLocaleString()}</strong></div>
                                                    </div>
                                                    <p className="model-description">{v.description}</p>
                                                </div>
                                            ))}
                                    </div>

                                    {/* Forecast table */}
                                    <div className="table-wrapper" style={{ marginTop: 24 }}>
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Model</th>
                                                    <th>Order</th>
                                                    {(forecastData.future_dates || []).map(d => (
                                                        <th key={d}>{fmtDate(d)}</th>
                                                    ))}
                                                    <th>RMSE ↓</th>
                                                    <th>MAE ↓</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {Object.entries(models)
                                                    .filter(([, v]) => !v.error)
                                                    .map(([k, v]) => (
                                                        <tr key={k}>
                                                            <td>
                                                                <span className="model-badge-sm"
                                                                    style={{ background: MODEL_META[k]?.color }}>
                                                                    {MODEL_META[k]?.label}
                                                                </span>
                                                            </td>
                                                            <td style={{ color: '#8898aa', fontSize: '0.8rem' }}>
                                                                {k === 'arima' ? 'ARIMA(2,1,2)' : k === 'sarima' ? 'SARIMA(1,1,1)(1,1,0,4)' : 'OLS'}
                                                            </td>
                                                            {(v.forecast || []).map((f, i) => (
                                                                <td key={i} className="num-cell">
                                                                    {fmtN(Math.round(f))}
                                                                </td>
                                                            ))}
                                                            <td className="num-cell">{Number(v.rmse).toLocaleString()}</td>
                                                            <td className="num-cell">{Number(v.mae).toLocaleString()}</td>
                                                        </tr>
                                                    ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </>
                            )}

                            {!loadingForecast && forecastData?.error && (
                                <div className="error-banner">⚠️ {forecastData.error}</div>
                            )}
                        </section>
                    )}

                    {/* ── Methodology ── */}
                    <section className="methodology-section glass fade-in">
                        <h2 className="section-heading">Methodology</h2>
                        <div className="method-grid">
                            {[
                                {
                                    icon: '', title: 'ARIMA',
                                    desc: 'Auto-Regressive Integrated Moving Average. Captures non-seasonal temporal patterns using past values and errors. Fitted with order (2,1,2).',
                                    formula: 'y_t = φ₁y_{t-1} + θ₁ε_{t-1} + ε_t',
                                    color: MODEL_META.arima.color,
                                },
                                {
                                    icon: '', title: 'SARIMA',
                                    desc: 'Seasonal ARIMA with period=4 (quarterly). Models recurring monsoon-driven peaks in vector-borne diseases like Dengue & Malaria.',
                                    formula: 'SARIMA(1,1,1)(1,1,0)₄',
                                    color: MODEL_META.sarima.color,
                                },
                                {
                                    icon: '', title: 'Linear Regression',
                                    desc: 'Baseline OLS model capturing the overall trend direction. Used to benchmark and quantify improvement from ARIMA/SARIMA.',
                                    formula: 'ŷ = β₀ + β₁t',
                                    color: MODEL_META.linear.color,
                                },
                                {
                                    icon: '', title: 'Model Evaluation',
                                    desc: 'Models ranked by RMSE, MAE, and AIC. Lower values indicate better in-sample fit and predictive accuracy.',
                                    formula: 'RMSE = √(Σ(ŷ−y)² / n)',
                                    color: '#a5b4fc',
                                },
                            ].map(m => (
                                <div key={m.title} className="method-card">
                                    <div className="method-icon">{m.icon}</div>
                                    <h3 style={{ color: m.color }}>{m.title}</h3>
                                    <p>{m.desc}</p>
                                    <div className="method-formula">{m.formula}</div>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* ── Welcome ── */}
                    {!selectedDisease && !loadingDiseases && (
                        <section className="empty-state glass fade-in">
                            <div className="empty-icon"></div>
                            <h3>Select a Disease to Begin</h3>
                            <p>Choose COVID-19, Dengue, Malaria, or IDSP to explore historical trends and run ML forecasting.</p>
                        </section>
                    )}
                </div>
            </main>

            <footer className="dashboard-footer">
                <div className="container footer-inner">
                    <p>India Multi-Disease Epidemiology Framework • {new Date().getFullYear()}</p>
                    <p>Data: MoHFW · NCVBDC · NCDC &nbsp;|&nbsp; Models: ARIMA · SARIMA · Linear Regression</p>
                </div>
            </footer>
        </div>
    )
}
