import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

interface Props {
  scoreRequirement: number
  scoreSecurity: number
  scoreQuality: number
  scorePerformance: number
}

export default function RadarChart({
  scoreRequirement,
  scoreSecurity,
  scoreQuality,
  scorePerformance,
}: Props) {
  const data = [
    { dimension: 'Requirement', score: scoreRequirement, fullMark: 100 },
    { dimension: 'Security', score: scoreSecurity, fullMark: 100 },
    { dimension: 'Quality', score: scoreQuality, fullMark: 100 },
    { dimension: 'Performance', score: scorePerformance, fullMark: 100 },
  ]

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RechartsRadarChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fontSize: 13, fill: '#374151', fontWeight: 500 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fontSize: 10, fill: '#9ca3af' }}
        />
        <Radar
          name="Score"
          dataKey="score"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.2}
          strokeWidth={2}
        />
        <Tooltip
          formatter={(value: number) => [`${value}/100`, 'Score']}
          contentStyle={{
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            fontSize: '13px',
          }}
        />
      </RechartsRadarChart>
    </ResponsiveContainer>
  )
}
