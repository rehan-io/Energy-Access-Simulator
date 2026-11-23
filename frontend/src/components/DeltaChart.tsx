import ReactECharts from 'echarts-for-react';
import { Box, Typography, Stack } from '@mui/material';
import type { YearSnapshot } from '../types';
import { TIER_COLORS } from '../theme';

interface Props {
  current: YearSnapshot[];
  reference: YearSnapshot[];
}

const SERIES = [
  { key: 'traditional', name: 'Traditional' },
  { key: 'lantern',     name: 'Lanterns'    },
  { key: 'shs',         name: 'SHS'         },
  { key: 'minigrid',    name: 'Mini-Grids'  },
  { key: 'grid',        name: 'National Grid' },
] as const;

export function DeltaChart({ current, reference }: Props) {
  const years = current.map((c) => c.year);
  const refByYear = new Map(reference.map((r) => [r.year, r]));

  // Find the single biggest |delta| across all tiers/years → headline stat
  let maxAbs = 0;
  let headline = { tier: '', year: 0, delta: 0 };
  for (const s of SERIES) {
    for (const row of current) {
      const r = refByYear.get(row.year);
      if (!r) continue;
      const d = row[s.key] - r[s.key];
      if (Math.abs(d) > maxAbs) {
        maxAbs = Math.abs(d);
        headline = { tier: s.name, year: row.year, delta: d };
      }
    }
  }

  const series = SERIES.map(({ key, name }) => ({
    name,
    type: 'line',
    smooth: true,
    showSymbol: false,
    lineStyle: { width: 2.5 },
    itemStyle: { color: TIER_COLORS[key] },
    emphasis: { focus: 'series', lineStyle: { width: 4 } },
    data: current.map((c) => {
      const r = refByYear.get(c.year);
      return r ? +(c[key] - r[key]).toFixed(2) : 0;
    }),
  }));

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="baseline"
        sx={{ px: 1, pb: 0.75, borderBottom: '1px solid #1E2740' }}
      >
        <Typography variant="caption" sx={{ color: '#94A3B8', fontWeight: 600, letterSpacing: 0.5 }}>
          Δ vs. default policy · Subsidy 20 · Tax 10 · Off-Grid 30 · Grid 30
        </Typography>
        {maxAbs > 0.5 && (
          <Typography variant="caption" sx={{
            color: headline.delta > 0 ? '#4ADE80' : '#EF5350',
            fontWeight: 700,
            fontVariantNumeric: 'tabular-nums',
          }}>
            Max impact: {headline.tier} {headline.delta > 0 ? '+' : ''}{headline.delta.toFixed(1)} pp @ {headline.year}
          </Typography>
        )}
      </Stack>

      <Box sx={{ flex: 1, minHeight: 0 }}>
        <ReactECharts
          notMerge={false}
          style={{ height: '100%', width: '100%' }}
          option={{
            animation: true,
            animationDuration: 300,
            animationDurationUpdate: 0,
            animationEasing: 'cubicOut',
            grid: { left: 56, right: 24, top: 16, bottom: 42 },
            tooltip: {
              trigger: 'axis',
              backgroundColor: '#141C2E',
              borderColor: '#2A3550',
              textStyle: { color: '#E8EAF2' },
              valueFormatter: (v: number) =>
                `${(v as number) > 0 ? '+' : ''}${(v as number).toFixed(2)} pp`,
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
              name: 'Δ pp',
              nameTextStyle: { color: '#94A3B8', fontSize: 10 },
              axisLabel: {
                color: '#94A3B8',
                formatter: (v: number) => `${v > 0 ? '+' : ''}${v}`,
              },
              splitLine: {
                lineStyle: {
                  color: (v: any) => (v.value === 0 ? '#E8EAF2' : '#1E2740'),
                  type: (v: any) => (v.value === 0 ? 'solid' : 'dashed'),
                  opacity: (v: any) => (v.value === 0 ? 0.55 : 1),
                  width: (v: any) => (v.value === 0 ? 1.5 : 1),
                },
              },
            },
            series,
          }}
        />
      </Box>
    </Box>
  );
}