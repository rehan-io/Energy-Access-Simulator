// frontend/src/pages/Dashboard.tsx
import { useEffect, useMemo, useState } from 'react';
import {
  AppBar, Toolbar, Typography, Box, Paper, Stack, Button, Chip,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import SaveIcon from '@mui/icons-material/Save';
import { useSimStore } from '../store/useSimStore';
import { LeverSlider } from '../components/LeverSlider';
import { KpiCards } from '../components/KpiCards';
import { EnergyStackChart } from '../components/EnergyStackChart';
import { DeltaChart } from '../components/DeltaChart';
import { IndiaMap } from '../components/IndiaMap';
import { INDIA_STATES } from '../data/indiaStates';

const scrollbarSx = {
  '&::-webkit-scrollbar': { width: 8 },
  '&::-webkit-scrollbar-thumb': { backgroundColor: '#2A3550', borderRadius: 4 },
  '&::-webkit-scrollbar-track': { backgroundColor: 'transparent' },
};

export function Dashboard() {
  const {
    country, initialStocks,
    levers, setLever, year, setYear,
    history, referenceHistory,
    runSim, running,
    scenarios, saveScenario, loadScenario, deleteScenario,
    source, lastError,
  } = useSimStore();

  const [scenarioName, setScenarioName] = useState('');
  const current = history[Math.min(year - 2026, history.length - 1)];
  const reference = referenceHistory?.[country] ?? [];

  // Fire the backend once on mount so the badge + chart reflect real data immediately
  useEffect(() => {
    runSim();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <AppBar
        position="static"
        elevation={0}
        sx={{
          flexShrink: 0,
          bgcolor: 'background.paper',
          borderBottom: '1px solid #1E2740',
        }}
      >
        <Toolbar>
          <Typography variant="h6">⚡ Energy Access Dynamics Simulator</Typography>
          <Box sx={{ flex: 1 }} />
          <Chip
            label={source === 'backend' ? '● live backend' : source === 'local' ? '● local fallback' : '…'}
            size="small"
            title={lastError ?? 'Simulation source'}
            sx={{
              bgcolor: source === 'backend' ? '#1B3D2F' : '#3D2A1B',
              color:   source === 'backend' ? '#4ADE80' : '#FBBF24',
              mr: 1,
            }}
          />
          <Chip
            label={`${country} · 2026–2075`}
            size="small"
            sx={{ bgcolor: '#1E2740', color: '#94A3B8' }}
          />
        </Toolbar>
      </AppBar>

      <Box
        sx={{
          display: 'flex',
          flex: 1,
          minHeight: 0,
          overflow: 'hidden',
          p: 3,
          gap: 3,
        }}
      >
        {/* ── LEFT: levers + scenarios, independently scrollable ── */}
        <Paper
          sx={{
            width: 320,
            flexShrink: 0,
            p: 3,
            overflowY: 'auto',
            border: '1px solid #1E2740',
            ...scrollbarSx,
          }}
        >
          <Typography variant="overline" color="text.secondary">
            Year 0 Baseline ({country})
          </Typography>
          <Paper sx={{
            p: 1.5, mt: 1, mb: 3,
            bgcolor: '#0B1220', border: '1px solid #1E2740', borderRadius: 2,
          }}>
            <Stack spacing={0.5}>
              <Typography variant="caption" sx={{ color: '#42A5F5' }}>
                Grid: <b>{initialStocks?.grid ?? '—'}%</b> · SHS:{' '}
                <b>{initialStocks?.shs ?? '—'}%</b>
              </Typography>
              <Typography variant="caption" sx={{ color: '#8D6E63' }}>
                Traditional: <b>{initialStocks?.traditional ?? '—'}%</b> · Lantern:{' '}
                <b>{initialStocks?.lantern ?? '—'}%</b>
              </Typography>
            </Stack>
          </Paper>

          <Typography variant="overline" color="text.secondary">Policy Levers</Typography>
          <Stack spacing={3} sx={{ mt: 2 }}>
            <LeverSlider label="Subsidy" value={levers.subsidy} color="#FFB74D"
              onChange={(v) => setLever('subsidy', v)} description="Reduces upfront SHS cost" />
            <LeverSlider label="Carbon Tax" value={levers.carbonTax} color="#EF5350"
              onChange={(v) => setLever('carbonTax', v)} description="Raises kerosene / diesel price" />
            <LeverSlider label="Off-Grid Deployment" value={levers.offGrid} color="#26A69A"
              onChange={(v) => setLever('offGrid', v)} description="Solar companies reach" />
            <LeverSlider label="Grid Extension" value={levers.gridExt} color="#42A5F5"
              onChange={(v) => setLever('gridExt', v)} description="National grid build rate" />
          </Stack>

          <Button
            fullWidth variant="contained" startIcon={<PlayArrowIcon />}
            onClick={runSim} disabled={running}
            sx={{ mt: 3, fontWeight: 700, color: '#0B1220', '&:hover': { bgcolor: '#FFC978' } }}
          >
            {running ? 'Simulating…' : 'Run Simulation'}
          </Button>

          <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mt: 4 }}>
            Scenarios
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
            <input
              placeholder="Name" value={scenarioName}
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
                sx={{
                  p: 1.5, bgcolor: '#0B1220', border: '1px solid #1E2740',
                  display: 'flex', alignItems: 'center', gap: 1,
                }}>
                <Typography variant="body2" sx={{ flex: 1 }}>
                  {s.name} ({s.country})
                </Typography>
                <Button size="small" onClick={() => loadScenario(s.id)}>Load</Button>
                <Button size="small" color="error" onClick={() => deleteScenario(s.id)}>×</Button>
              </Paper>
            ))}
          </Stack>
        </Paper>

        {/* ── RIGHT: KPIs + charts + slider + map, independently scrollable ── */}
        <Stack
          spacing={3}
          sx={{
            flex: 1,
            minWidth: 0,
            overflowY: 'auto',
            pr: 1,
            pb: 1,
            ...scrollbarSx,
          }}
        >
          <KpiCards
            year={year}
            access={current.shs + current.minigrid + current.grid}
            traditional={current.traditional}
            gridCoverage={current.grid}
          />

          {/* Energy ladder (with value bar on top) */}
          <Paper
            sx={{
              p: 2,
              height: 470,
              display: 'flex',
              flexDirection: 'column',
              flexShrink: 0,
              border: '1px solid #1E2740',
            }}
          >
            <EnergyStackChart history={history} year={year} />
          </Paper>

          {/* Year slider */}
          <Paper sx={{ p: 2, flexShrink: 0, border: '1px solid #1E2740' }}>
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
              <Typography variant="overline" color="text.secondary">Year</Typography>
              <input
                type="range" min={2026} max={2075} value={year}
                onChange={(e) => setYear(+e.target.value)}
                style={{ flex: 1, accentColor: '#FFB74D' }}
              />
              <Typography
                variant="h6"
                sx={{ fontWeight: 700, color: 'primary.main', minWidth: 60, textAlign: 'right' }}
              >
                {year}
              </Typography>
            </Stack>
          </Paper>

          {/* Δ vs. default policy — only renders once the reference run has landed */}
          {reference.length > 0 && (
            <Paper
              sx={{
                p: 2,
                height: 400,
                display: 'flex',
                flexDirection: 'column',
                flexShrink: 0,
                border: '1px solid #1E2740',
              }}
            >
              <DeltaChart current={history} reference={reference} />
            </Paper>
          )}

          {/* Map */}
          <Paper
            sx={{
              height: 520,
              flexShrink: 0,
              overflow: 'hidden',
              border: '1px solid #1E2740',
            }}
          >
            {country === 'IND' ? (
              <IndiaMap states={INDIA_STATES} year={year} accessByState={accessByState} />
            ) : (
              <Box sx={{
                height: '100%', display: 'flex', alignItems: 'center',
                justifyContent: 'center', p: 4, textAlign: 'center',
              }}>
                <Box>
                  <Typography variant="h6" color="text.secondary">
                    Subnational Geo Data for {country}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1, maxWidth: 450 }}>
                    State-level granularity is currently mapped for India (IND). National energy
                    ladder dynamics above are actively simulating for {country}.
                  </Typography>
                </Box>
              </Box>
            )}
          </Paper>
        </Stack>
      </Box>
    </Box>
  );
}