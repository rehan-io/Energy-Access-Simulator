import ReactECharts from 'echarts-for-react';
import type { YearSnapshot } from '../types';
import { TIER_COLORS } from '../theme';

interface Props {
  history: YearSnapshot[];
  year: number;
}

const SERIES = [
  { key: 'traditional', name: 'Traditional Fuels' },
  { key: 'lantern',     name: 'Solar Lanterns' },
  { key: 'shs',         name: 'Solar Home Systems' },
  { key: 'minigrid',    name: 'Mini-Grids' },
  { key: 'grid',        name: 'National Grid' },
] as const;

export function EnergyStackChart({ history, year }: Props) {
  const years = history.map((h) => h.year);

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
    <ReactECharts
      notMerge
      style={{ height: '100%', width: '100%' }}
      option={{
        grid: { left: 50, right: 24, top: 24, bottom: 48 },
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
  );
}