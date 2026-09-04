import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

/**
 * Renders a backtest equity curve using TradingView's lightweight-charts —
 * the same visual language a trader already reads candles in, so the
 * result feels native to the subject rather than borrowed from generic
 * dashboard chart libraries.
 */
export default function EquityChart({ equityCurve }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const seriesRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: '#12161C' },
        textColor: '#6B7280',
        fontFamily: '"JetBrains Mono", monospace',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#1A1F27' },
        horzLines: { color: '#1A1F27' },
      },
      rightPriceScale: { borderColor: '#232830' },
      timeScale: { borderColor: '#232830', timeVisible: true },
      crosshair: { mode: 0 },
      height: containerRef.current.clientHeight,
      width: containerRef.current.clientWidth,
    })

    const series = chart.addAreaSeries({
      lineColor: '#00D9A3',
      topColor: 'rgba(0, 217, 163, 0.25)',
      bottomColor: 'rgba(0, 217, 163, 0.0)',
      lineWidth: 1.5,
      priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
    })

    chartRef.current = chart
    seriesRef.current = series

    const handleResize = () => {
      if (!containerRef.current) return
      chart.applyOptions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
      })
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [])

  useEffect(() => {
    if (!seriesRef.current || !equityCurve?.length) return
    const data = equityCurve.map((pt) => ({
      time: Math.floor(new Date(pt.t).getTime() / 1000),
      value: pt.equity,
    }))
    // lightweight-charts requires strictly ascending unique timestamps
    const deduped = data.filter((d, i) => i === 0 || d.time > data[i - 1].time)
    seriesRef.current.setData(deduped)
    chartRef.current?.timeScale().fitContent()
  }, [equityCurve])

  return <div ref={containerRef} className="h-full w-full" />
}
