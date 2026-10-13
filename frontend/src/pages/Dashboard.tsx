import { useMemo, useState } from 'react';
import {
  AppBar, Toolbar, Typography, Box, Paper, Stack, Button, Chip,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import SaveIcon from '@mui/icons-material/Save';
import { useSimStore } from '../store/useSimStore';
import { LeverSlider } from '../components/LeverSlider';
import { KpiCards } from '../components/KpiCards';
import { EnergyStackChart } from '../components/EnergyStackChart';
import { IndiaMap } from '../components/IndiaMap';
import { INDIA_STATES } from '../data/indiaStates';

export function Dashboard() {
  const {
    levers, setLever, year, setYear,
    history, runSim, running,
    scenarios, saveScenario, loadScenario, deleteScenario,
  } = useSimStore();

  const [scenarioName, setScenarioName] = useState('');
  const current = history[Math.min(year - 2026, history.length - 1)];

  const accessByState = useMemo(() => {
    const nationalAccess = current.shs + current.minigrid + current.grid;
    const progress = Math.min(1, (nationalAccess / 100) * (1 + levers.subsidy / 200));
    const map: Record<string, number> = {};
    INDIA_STATES.forEach((s) => {
      const gap = Math.max(0, 100 - s.initialAccess);
      map[s.id] = Math.min(100, s.initialAccess + gap * progress * 0.7);
    });
    return map;
  }, [current, levers.subsidy]);

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="sticky" elevation={0}
        sx={{ bgcolor: 'background.paper', borderBottom: '1px solid #1E2740' }}>
        <Toolbar>
          <Typography variant="h6">⚡ Energy Access Dynamics Simulator</Typography>
          <Box sx={{ flex: 1 }} />
          <Chip label="India · 2026–2050" size="small"
            sx={{ bgcolor: '#1E2740', color: '#94A3B8' }} />
        </Toolbar>
      </AppBar>

      <Box sx={{ display: 'flex', p: 3, gap: 3, alignItems: 'flex-start' }}>
        {/* ── Controls ── */}
        <Paper sx={{ width: 320, p: 3, flexShrink: 0, border: '1px solid #1E2740' }}>
          <Typography variant="overline" color="text.secondary">Policy Levers</Typography>
          <Stack spacing={3} sx={{ mt: 2 }}>
            <LeverSlider label="Subsidy"             value={levers.subsidy}   color="#FFB74D"
              onChange={(v) => setLever('subsidy', v)}   description="Reduces upfront SHS cost" />
            <LeverSlider label="Carbon Tax"          value={levers.carbonTax} color="#EF5350"
              onChange={(v) => setLever('carbonTax', v)} description="Raises kerosene / diesel price" />
            <LeverSlider label="Off-Grid Deployment" value={levers.offGrid}   color="#26A69A"
              onChange={(v) => setLever('offGrid', v)}   description="Solar companies reach" />
            <LeverSlider label="Grid Extension"      value={levers.gridExt}   color="#42A5F5"
              onChange={(v) => setLever('gridExt', v)}   description="National grid build rate" />
          </Stack>

          <Button
            fullWidth variant="contained" startIcon={<PlayArrowIcon />}
            onClick={runSim} disabled={running}
            sx={{ mt: 3, fontWeight: 700, color: '#0B1220',
                  '&:hover': { bgcolor: '#FFC978' } }}
          >
            {running ? 'Simulating…' : 'Run Simulation'}
          </Button>

          <Typography variant="overline" color="text.secondary"
            sx={{ display: 'block', mt: 4 }}>Scenarios</Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
            <input
              placeholder="Name"
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              style={{
                flex: 1, background: '#0B1220', border: '1px solid #1E2740',
                color: '#E8EAF2', padding: '8px 10px', borderRadius: 8, outline: 'none',
              }}
            />
            <Button variant="outlined" startIcon={<SaveIcon />}
              onClick={() => { if (scenarioName) { saveScenario(scenarioName); setScenarioName(''); } }}
              sx={{ color: 'secondary.main', borderColor: 'secondary.main' }}
            >Save</Button>
          </Stack>
          <Stack spacing={1} sx={{ mt: 2 }}>
            {scenarios.map((s) => (
              <Paper key={s.id}
                sx={{ p: 1.5, bgcolor: '#0B1220', border: '1px solid #1E2740',
                      display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" sx={{ flex: 1 }}>{s.name}</Typography>
                <Button size="small" onClick={() => loadScenario(s.id)}>Load</Button>
                <Button size="small" color="error" onClick={() => deleteScenario(s.id)}>×</Button>
              </Paper>
            ))}
          </Stack>
        </Paper>

        {/* ── Visuals ── */}
        <Stack spacing={3} sx={{ flex: 1, minWidth: 0 }}>
          <KpiCards
            year={year}
            access={current.shs + current.minigrid + current.grid}
            traditional={current.traditional}
            gridCoverage={current.grid}
          />

          <Paper sx={{ p: 2, height: 420, border: '1px solid #1E2740' }}>
            <EnergyStackChart history={history} year={year} />
          </Paper>

          <Paper sx={{ p: 2, border: '1px solid #1E2740' }}>
            <Stack direction="row" spacing={2} alignItems="center">
              <Typography variant="overline" color="text.secondary">Year</Typography>
              <input
                type="range" min={2026} max={2050} value={year}
                onChange={(e) => setYear(+e.target.value)}
                style={{ flex: 1, accentColor: '#FFB74D' }}
              />
              <Typography variant="h6"
                sx={{ fontWeight: 700, color: 'primary.main', minWidth: 60, textAlign: 'right' }}>
                {year}
              </Typography>
            </Stack>
          </Paper>

          <Paper sx={{ height: 520, overflow: 'hidden', border: '1px solid #1E2740' }}>
            <IndiaMap states={INDIA_STATES} year={year} accessByState={accessByState} />
          </Paper>
        </Stack>
      </Box>
    </Box>
  );
}