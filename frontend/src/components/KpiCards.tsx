import { Card, CardContent, Stack, Typography } from '@mui/material';

interface Props {
  year: number;
  access: number;
  traditional: number;
  gridCoverage: number;
}

export function KpiCards({ year, access, traditional, gridCoverage }: Props) {
  const items = [
    { label: 'Total Access',      value: `${access.toFixed(1)}%`,       color: '#42A5F5', sub: `projected ${year}` },
    { label: 'Grid Coverage',     value: `${gridCoverage.toFixed(1)}%`, color: '#4DD0E1', sub: 'utility-scale' },
    { label: 'On Traditional',    value: `${traditional.toFixed(1)}%`,  color: '#8D6E63', sub: 'kerosene / biomass' },
  ];
  return (
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
      {items.map((it) => (
        <Card key={it.label} sx={{ flex: 1, border: '1px solid #1E2740' }}>
          <CardContent>
            <Typography variant="caption" sx={{ color: 'text.secondary', textTransform: 'uppercase', letterSpacing: 1 }}>
              {it.label}
            </Typography>
            <Typography variant="h4" sx={{ color: it.color, mt: 0.5, fontVariantNumeric: 'tabular-nums' }}>
              {it.value}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>{it.sub}</Typography>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
}