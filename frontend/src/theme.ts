import { createTheme } from '@mui/material/styles';

export const TIER_COLORS = {
  traditional: '#8D6E63',
  lantern:     '#FDD835',
  shs:         '#FB8C00',
  minigrid:    '#26A69A',
  grid:        '#42A5F5',
} as const;

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary:   { main: '#FFB74D' },
    secondary: { main: '#4DD0E1' },
    background: { default: '#0B1220', paper: '#141C2E' },
    text: { primary: '#E8EAF2', secondary: '#94A3B8' },
    divider: '#1E2740',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", system-ui, sans-serif',
    h4: { fontWeight: 700, letterSpacing: '-0.02em' },
    h6: { fontWeight: 700, letterSpacing: '-0.01em' },
    overline: { letterSpacing: 1.5, fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    Paper: { styleOverrides: { root: { backgroundImage: 'none' } } },
  },
});