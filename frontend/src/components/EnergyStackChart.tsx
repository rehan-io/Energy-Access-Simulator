import ReactECharts from 'echarts-for-react';
import { TIER_COLORS } from '../theme';
import type { AccessIndicator, EnergyTierKey, YearSnapshot } from '../types';

interface Props {
  history: YearSnapshot[];
  year: number;
}

const INDICATORS: {
  key: AccessIndicator;
  name: string;
  color: string;
}[] = [
  { key: 'elec_access_total', name: 'National electricity access', color: '#42A5F5' },
  { key: 'elec_access_rural', name: 'Rural electricity access', color: '#4DD0E1' },
  { key: 'elec_access_urban', name: 'Urban electricity access', color: '#FFB74D' },
  { key: 'clean_cooking_access', name: 'Clean cooking access', color: '#66BB6A' },
];

const TIER_SERIES: {
  key: EnergyTierKey;
  name: string;
  color: string;
}[] = [
  { key: 'grid', name: 'National Grid (Tier 4–5)', color: TIER_COLORS.grid },
  { key: 'minigrid', name: 'Mini-Grids (Tier 3–4)', color: TIER_COLORS.minigrid },
  { key: 'shs', name: 'Solar Home Systems (Tier 1–2)', color: TIER_COLORS.shs },
  { key: 'lantern', name: 'Solar Lanterns (Tier 1)', color: TIER_COLORS.lantern },
  { key: 'traditional', name: 'Traditional Fuels (Tier 0)', color: TIER_COLORS.traditional },
];

export function EnergyStackChart({ history, year }: Props) {
  const years = history.map((row) => row.year);
  const baselineYear = history.filter((row) => row.kind === 'historical').at(-1)?.year;

  const series = INDICATORS.flatMap(({ key, name, color }) => {
    const baselineValue = history.find((row) => row.year === baselineYear)?.[key];

    return [
      {
        name: `${name} · historical`,
        type: 'line',
        showSymbol: false,
        connectNulls: false,
        lineStyle: { width: 2, type: 'solid' },
        itemStyle: { color },
        data: history.map((row) => (row.kind === 'historical' ? row[key] : null)),
      },
      {
        name: `${name} · projected`,
        type: 'line',
        showSymbol: false,
        connectNulls: false,
        lineStyle: { width: 2, type: 'dashed' },
        itemStyle: { color },
        data: history.map((row) =>
          row.kind === 'projected'
            ? row[key]
            : row.year === baselineYear
              ? baselineValue
              : null,
        ),
      },
    ];
  });

  return (
    <ReactECharts
      notMerge
      style={{ height: '100%', width: '100%' }}
      option={{
        backgroundColor: 'transparent',
        grid: { left: 58, right: 24, top: 32, bottom: 100 },
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#141C2E',
          borderColor: '#2A3550',
          textStyle: { color: '#E8EAF2' },
          valueFormatter: (value: number | null) =>
            value == null ? 'Not available' : `${value.toFixed(1)}%`,
        },
        legend: {
          bottom: 4,
          type: 'scroll',
          textStyle: { color: '#94A3B8' },
        },
        xAxis: {
          type: 'category',
          data: years,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#2A3550' } },
          axisLabel: { color: '#94A3B8' },
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: { color: '#94A3B8', formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#1E2740' } },
        },
        series: [
          ...series,
          {
            name: 'Selected year',
            type: 'line',
            data: [],
            markLine: {
              silent: true,
              symbol: 'none',
              lineStyle: {
                color: '#E8EAF2',
                type: 'dashed',
                width: 1,
                opacity: 0.6,
              },
              data: [{ xAxis: year }],
              label: { show: false },
            },
          },
        ],
      }}
    />
  );
}

export function TierStackChart({ history, year }: Props) {
  const tierRows = history.filter(
    (row) => row.grid != null && row.traditional != null,
  );
  const years = tierRows.map((row) => row.year);
  const hasSelectedYear = years.includes(year);

  const series = TIER_SERIES.map(({ key, name, color }) => ({
    name,
    type: 'line',
    stack: 'ladder',
    showSymbol: false,
    smooth: true,
    lineStyle: { width: 1.5, color },
    itemStyle: { color },
    areaStyle: { opacity: 0.78, color },
    emphasis: { focus: 'series' },
    data: tierRows.map((row) => row[key] ?? 0),
  }));

  return (
    <ReactECharts
      notMerge
      style={{ height: '100%', width: '100%' }}
      option={{
        backgroundColor: 'transparent',
        grid: { left: 58, right: 24, top: 28, bottom: 72 },
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#141C2E',
          borderColor: '#2A3550',
          textStyle: { color: '#E8EAF2' },
          valueFormatter: (value: number | null) =>
            value == null ? 'Not available' : `${value.toFixed(1)}%`,
        },
        legend: {
          bottom: 4,
          type: 'scroll',
          textStyle: { color: '#94A3B8' },
        },
        xAxis: {
          type: 'category',
          data: years,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#2A3550' } },
          axisLabel: { color: '#94A3B8' },
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: { color: '#94A3B8', formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#1E2740' } },
        },
        series: [
          ...series,
          ...(hasSelectedYear
            ? [
                {
                  name: 'Selected year',
                  type: 'line',
                  data: [],
                  markLine: {
                    silent: true,
                    symbol: 'none',
                    lineStyle: {
                      color: '#E8EAF2',
                      type: 'dashed',
                      width: 1,
                      opacity: 0.7,
                    },
                    data: [{ xAxis: year }],
                    label: { show: false },
                  },
                },
              ]
            : []),
        ],
      }}
    />
  );
}