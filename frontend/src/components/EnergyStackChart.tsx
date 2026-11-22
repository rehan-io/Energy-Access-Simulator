import ReactECharts from 'echarts-for-react';
import { Box, Stack, Typography } from '@mui/material';
import type { YearSnapshot } from '../types';
import { TIER_COLORS } from '../theme';

interface Props {
  history: YearSnapshot[];
  year: number;
}

const SERIES = [
  { key: 'traditional', name: 'Traditional' },
  { key: 'lantern',     name: 'Lanterns'    },
  { key: 'shs',         name: 'SHS'         },
  { key: 'minigrid',    name: 'Mini-Grids'  },
  { key: 'grid',        name: 'National Grid' },
] as const;

export function EnergyStackChart({ history, year }: Props) {
  const years = history.map((h) => h.year);

  const idx = Math.max(0, Math.min(year - 2026, history.length - 1));
  const current = history[idx];
  const final   = history[history.length - 1];

  const series = SERIES.map(({ key, name }, i) => ({
    name,
    type: 'line',
    stack: 'total',
    smooth: true,
    showSymbol: false,
    lineStyle: { width: 0 },
    areaStyle: { opacity: 0.9 },
    emphasis: { focus: 'series' },
    itemStyle: { color: TIER_COLORS[key] },
    data: history.map((h) => h[key]),
    ...(i === 0 && {
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#E8EAF2', type: 'dashed', width: 1, opacity: 0.5 },
        data: [{ xAxis: year }],
        label: { show: false },
      },
    }),
  }));

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      {/* ── Values bar (numbers on top of the graph) ── */}
      <Stack
        direction="row"
        spacing={2}
        sx={{
          px: 1,
          py: 1,
          flexWrap: 'wrap',
          rowGap: 0.5,
          borderBottom: '1px solid #1E2740',
          mb: 0.5,
        }}
      >
        {SERIES.map(({ key, name }) => {
          const cur = current[key];
          const fin = final[key];
          const delta = fin - cur;
          const up = delta >= 0.05;
          const down = delta <= -0.05;
          return (
            <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
              <Box
                sx={{
                  width: 10, height: 10, borderRadius: 0.5,
                  bgcolor: TIER_COLORS[key], flexShrink: 0,
                }}
              />
              <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                {name}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: TIER_COLORS[key],
                  fontWeight: 700,
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {cur.toFixed(1)}%
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: up ? '#4ADE80' : down ? '#EF5350' : '#94A3B8',
                  fontSize: 10,
                  fontWeight: 600,
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {up ? '↑' : down ? '↓' : '·'} {Math.abs(delta).toFixed(1)} by {years[years.length - 1]}
              </Typography>
            </Box>
          );
        })}
      </Stack>

      {/* ── Chart ── */}
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <ReactECharts
          notMerge={false}
          style={{ height: '100%', width: '100%' }}
          option={{
            animation: true,
            animationDuration: 800,
            animationDurationUpdate: 0,
            animationEasing: 'cubicOut',
            grid: { left: 50, right: 24, top: 16, bottom: 48 },
            tooltip: {
              trigger: 'axis',
              backgroundColor: '#141C2E',
              borderColor: '#2A3550',
              textStyle: { color: '#E8EAF2' },
              valueFormatter: (v: number) => `${(v as number).toFixed(1)}%`,
            },
            legend: { bottom: 0, textStyle: { color: '#94A3B8' }, icon: 'roundRect' },
            xAxis: {
              type: 'category',
              data: years,
              boundaryGap: false,
              axisLine: { lineStyle: { color: '#2A3550' } },
              axisLabel: { color: '#94A3B8' },
            },
            yAxis: {
              type: 'value',
              max: 100,
              axisLabel: { color: '#94A3B8', formatter: '{value}%' },
              splitLine: { lineStyle: { color: '#1E2740' } },
            },
            series,
          }}
        />
      </Box>
    </Box>
  );
}