import { Box, Slider, Stack, Typography } from '@mui/material';

interface Props {
  label: string;
  value: number;
  onChange: (value: number) => void;
  color?: string;
  description?: string;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
}

export function LeverSlider({
  label,
  value,
  onChange,
  color = '#FFB74D',
  description,
  min = 0,
  max = 100,
  step = 1,
  unit = '%',
}: Props) {
  const formattedValue = `${Math.round(value)}${unit}`;

  return (
    <Box>
      <Stack
        direction="row"
        sx={{ justifyContent: 'space-between', alignItems: 'baseline' }}
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
          {label}
        </Typography>
        <Typography
          variant="subtitle2"
          sx={{ color, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}
        >
          {formattedValue}
        </Typography>
      </Stack>

      <Slider
        value={value}
        onChange={(_, nextValue) => onChange(nextValue as number)}
        min={min}
        max={max}
        step={step}
        sx={{
          color,
          '& .MuiSlider-thumb': { width: 16, height: 16 },
          '& .MuiSlider-rail': { opacity: 0.15 },
        }}
      />

      {description && (
        <Typography
          variant="caption"
          sx={{ color: 'text.secondary', display: 'block', mt: -0.5 }}
        >
          {description}
        </Typography>
      )}
    </Box>
  );
}