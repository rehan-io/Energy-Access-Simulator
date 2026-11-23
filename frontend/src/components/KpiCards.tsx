import { Box, Card, CardContent, Typography } from '@mui/material';
import type { YearSnapshot } from '../types';

interface Props {
  year: number;
  current: YearSnapshot | undefined;
}

export function KpiCards({ year, current }: Props) {
  const format = (value: number | null | undefined) =>
    value == null ? 'Not available' : `${value.toFixed(1)}%`;

  const items = [
    { label: 'Electricity access', value: format(current?.elec_access_total), color: '#42A5F5', description: 'National population' },
    { label: 'Rural electricity access', value: format(current?.elec_access_rural), color: '#4DD0E1', description: 'Rural population' },
    { label: 'Urban electricity access', value: format(current?.elec_access_urban), color: '#FFB74D', description: 'Urban population' },
    { label: 'Clean cooking access', value: format(current?.clean_cooking_access), color: '#66BB6A', description: 'Separate access indicator' },
  ];

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: '1fr',
          sm: 'repeat(2, minmax(0, 1fr))',
          xl: 'repeat(4, minmax(0, 1fr))',
        },
        gap: 2,
      }}
    >
      {items.map((item) => (
        <Card key={item.label} sx={{ minWidth: 0, border: '1px solid #1E2740' }}>
          <CardContent>
            <Typography
              variant="caption"
              sx={{ color: 'text.secondary', textTransform: 'uppercase', letterSpacing: 1 }}
            >
              {item.label}
            </Typography>
            <Typography
              variant="h4"
              sx={{
                color: item.color,
                mt: 0.5,
                fontVariantNumeric: 'tabular-nums',
                fontSize: { xs: '1.8rem', md: '2rem' },
              }}
            >
              {item.value}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {item.description} · {year}
            </Typography>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
}
