import { Box, Slider, Typography, Stack } from '@mui/material';

interface Props {
  label: string;
  value: number;
  onChange: (v: number) => void;
  color?: string;
  description?: string;
}

export function LeverSlider({ label, value, onChange, color = '#FFB74D', description }: Props) {
  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="baseline">
        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>{label}</Typography>
        <Typography variant="subtitle1" sx={{ color, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
          {value}%
        </Typography>
      </Stack>
      <Slider
        value={value}
        onChange={(_, v) => onChange(v as number)}
        min={0}
        max={100}
        sx={{ color, '& .MuiSlider-thumb': { width: 16, height: 16 }, '& .MuiSlider-rail': { opacity: 0.15 } }}
      />
      {description && (
        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: -0.5 }}>
          {description}
        </Typography>
      )}
    </Box>
  );
}