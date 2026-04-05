import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import '../component.css'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Area, AreaChart
} from 'recharts'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.1
    }
  }
}

const cardVariants = {
  hidden: { opacity: 0, y: 30, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 15
    }
  }
}

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="chart-tooltip">
        <p className="tooltip-label">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="tooltip-value" style={{ color: entry.color }}>
            {entry.name}: <span>{entry.value}</span>
          </p>
        ))}
      </div>
    )
  }
  return null
}

function AnalysisCharts({ analysis }) {
  if (!analysis) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="analysis-empty"
      >
        <motion.div
          className="empty-glow"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.6, 0.3]
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.span
          className="empty-icon"
          animate={{
            y: [0, -10, 0],
            rotateY: [0, 360]
          }}
          transition={{
            y: { duration: 2, repeat: Infinity, ease: "easeInOut" },
            rotateY: { duration: 4, repeat: Infinity, ease: "linear" }
          }}
        >
          📊
        </motion.span>
        <h3>Analysis Not Available</h3>
        <p>Run orchestration to generate analysis data</p>
      </motion.div>
    )
  }

  const chartColors = {
    primary: '#dc2626',
    primaryLight: '#ef4444',
    secondary: '#f87171',
    gradient: ['#dc2626', '#7f1d1d'],
    positive: '#22c55e',
    negative: '#ef4444',
    grid: 'rgba(220, 38, 38, 0.1)',
    axis: '#71717a',
    text: '#a1a1aa'
  }

  const charts = [
    {
      id: 'publication',
      title: 'Publication Trend',
      icon: '📈',
      data: analysis.publication_trend,
      render: (data) => (
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="publicationGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={chartColors.primary} stopOpacity={0.4} />
                <stop offset="100%" stopColor={chartColors.primary} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
            <XAxis 
              dataKey="year" 
              stroke={chartColors.axis}
              tick={{ fill: chartColors.text, fontSize: 12 }}
              axisLine={{ stroke: chartColors.grid }}
            />
            <YAxis 
              stroke={chartColors.axis}
              tick={{ fill: chartColors.text, fontSize: 12 }}
              axisLine={{ stroke: chartColors.grid }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="count"
              stroke={chartColors.primary}
              strokeWidth={3}
              fill="url(#publicationGradient)"
              dot={{ fill: chartColors.primary, strokeWidth: 2, r: 4, stroke: '#0a0a0a' }}
              activeDot={{ r: 6, stroke: chartColors.primaryLight, strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )
    },
    {
      id: 'authors',
      title: 'Top Authors',
      icon: '👥',
      data: analysis.top_authors,
      render: (data) => (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={data.slice(0, 10)} layout="vertical" barGap={8}>
            <defs>
              <linearGradient id="authorGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor={chartColors.gradient[1]} />
                <stop offset="100%" stopColor={chartColors.primary} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} horizontal={false} />
            <XAxis 
              type="number" 
              stroke={chartColors.axis}
              tick={{ fill: chartColors.text, fontSize: 12 }}
              axisLine={{ stroke: chartColors.grid }}
            />
            <YAxis 
              type="category" 
              dataKey="name" 
              width={130} 
              stroke={chartColors.axis}
              tick={{ fill: chartColors.text, fontSize: 11 }}
              axisLine={{ stroke: chartColors.grid }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="count" 
              fill="url(#authorGradient)"
              radius={[0, 6, 6, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )
    },
    {
      id: 'keywords',
      title: 'Keyword Frequency',
      icon: '🏷️',
      subtitle: 'Top 20 Keywords',
      data: analysis.keyword_frequency,
      render: (data) => (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.slice(0, 20)}>
            <defs>
              <linearGradient id="keywordGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={chartColors.primary} />
                <stop offset="100%" stopColor={chartColors.gradient[1]} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} vertical={false} />
            <XAxis 
              dataKey="word" 
              stroke={chartColors.axis}
              tick={{ fill: chartColors.text, fontSize: 10 }}
              angle={-45}
              textAnchor="end"
              height={80}
              axisLine={{ stroke: chartColors.grid }}
            />
            <YAxis 
              stroke={chartColors.axis}
              tick={{ fill: chartColors.text, fontSize: 12 }}
              axisLine={{ stroke: chartColors.grid }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="count" 
              fill="url(#keywordGradient)"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )
    },
    {
      id: 'citations',
      title: 'Citation Distribution',
      icon: '📚',
      data: analysis.citation_distribution,
      render: (data) => (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <defs>
              <linearGradient id="citationGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={chartColors.secondary} />
                <stop offset="100%" stopColor={chartColors.gradient[1]} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} vertical={false} />
            <XAxis 
              dataKey="bucket" 
              stroke={chartColors.axis}
              tick={{ fill: chartColors.text, fontSize: 12 }}
              axisLine={{ stroke: chartColors.grid }}
            />
            <YAxis 
              stroke={chartColors.axis}
              tick={{ fill: chartColors.text, fontSize: 12 }}
              axisLine={{ stroke: chartColors.grid }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="count" 
              fill="url(#citationGradient)"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )
    },
    {
      id: 'emerging',
      title: 'Emerging Topics',
      icon: '🚀',
      data: analysis.emerging_topics,
      render: (data) => (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <defs>
              <linearGradient id="positiveGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22c55e" />
                <stop offset="100%" stopColor="#166534" />
              </linearGradient>
              <linearGradient id="negativeGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ef4444" />
                <stop offset="100%" stopColor="#7f1d1d" />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} vertical={false} />
            <XAxis 
              dataKey="word" 
              stroke={chartColors.axis}
              tick={{ fill: chartColors.text, fontSize: 10 }}
              angle={-45}
              textAnchor="end"
              height={80}
              axisLine={{ stroke: chartColors.grid }}
            />
            <YAxis 
              stroke={chartColors.axis}
              tick={{ fill: chartColors.text, fontSize: 12 }}
              axisLine={{ stroke: chartColors.grid }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="delta"
              radius={[4, 4, 0, 0]}
              fill={chartColors.positive}
            >
              {data.map((entry, index) => (
                <rect 
                  key={index} 
                  fill={entry.delta >= 0 ? 'url(#positiveGradient)' : 'url(#negativeGradient)'} 
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )
    }
  ]

  return (
    <motion.div
      className="analysis-container"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {charts.map((chart, index) => (
        <motion.div
          key={chart.id}
          className="chart-card"
          variants={cardVariants}
          whileHover={{ 
            scale: 1.01,
            y: -4,
            transition: { type: "spring", stiffness: 300 }
          }}
        >
          <motion.div 
            className="chart-card-glow"
            animate={{
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{
              duration: 3 + index * 0.5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          
          <div className="chart-header">
            <div className="chart-title-wrapper">
              <motion.span 
                className="chart-icon"
                whileHover={{ scale: 1.2, rotate: 10 }}
              >
                {chart.icon}
              </motion.span>
              <div>
                <h3 className="chart-title">{chart.title}</h3>
                {chart.subtitle && (
                  <span className="chart-subtitle">{chart.subtitle}</span>
                )}
              </div>
            </div>
            {chart.data && chart.data.length > 0 && (
              <motion.div 
                className="chart-badge"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 500, delay: 0.3 + index * 0.1 }}
              >
                {chart.data.length} items
              </motion.div>
            )}
          </div>

          <div className="chart-content">
            {chart.data && chart.data.length > 0 ? (
              chart.render(chart.data)
            ) : (
              <div className="chart-no-data">
                <span className="no-data-icon">📭</span>
                <p>No data available</p>
              </div>
            )}
          </div>
        </motion.div>
      ))}
    </motion.div>
  )
}

export default AnalysisCharts
