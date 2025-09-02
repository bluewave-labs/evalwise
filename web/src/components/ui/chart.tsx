"use client"

import React from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler,
} from 'chart.js'
import { Bar, Pie, Line, Doughnut } from 'react-chartjs-2'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler
)

interface ChartProps {
  data: any
  options?: any
  type: 'bar' | 'pie' | 'line' | 'doughnut'
  className?: string
}

export function Chart({ data, options = {}, type, className }: ChartProps) {
  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
    ...options,
  }

  const chartComponents = {
    bar: Bar,
    pie: Pie,
    line: Line,
    doughnut: Doughnut,
  }

  const ChartComponent = chartComponents[type]

  return (
    <div className={className}>
      <ChartComponent data={data} options={defaultOptions} />
    </div>
  )
}

// Specific chart components for easier usage
export function BarChart({ data, options, className }: Omit<ChartProps, 'type'>) {
  return <Chart data={data} options={options} type="bar" className={className} />
}

export function PieChart({ data, options, className }: Omit<ChartProps, 'type'>) {
  return <Chart data={data} options={options} type="pie" className={className} />
}

export function LineChart({ data, options, className }: Omit<ChartProps, 'type'>) {
  return <Chart data={data} options={options} type="line" className={className} />
}

export function DoughnutChart({ data, options, className }: Omit<ChartProps, 'type'>) {
  return <Chart data={data} options={options} type="doughnut" className={className} />
}