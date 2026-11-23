import ReactECharts from 'echarts-for-react';
import type { AccessIndicator, YearSnapshot } from '../types';

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
        data: history.map((row) => row.kind === 'historical' ? row[key] : null),
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
              : null
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
