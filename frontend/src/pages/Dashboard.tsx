import { IndiaMap } from '../components/IndiaMap';
import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  AppBar,
  Box,
  Button,
  Chip,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Toolbar,
  Typography,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import SaveIcon from '@mui/icons-material/Save';
import PublicIcon from '@mui/icons-material/Public';

import { useSimStore } from '../store/useSimStore';
import { LeverSlider } from '../components/LeverSlider';
import { KpiCards } from '../components/KpiCards';
import { EnergyStackChart } from '../components/EnergyStackChart';

export function Dashboard() {
  const {
    country,
    setCountry,
    countries,
    initCountries,
    years,
    setYears,
    trendWindow,
    setTrendWindow,
    policyAdjustments,
    setPolicyAdjustment,
    selectedYear,
    setSelectedYear,
    history,
    runSim,
    running,
    error,
    baselineYear,
    scenarios,
    saveScenario,
    loadScenario,
    deleteScenario,
  } = useSimStore();

  const [scenarioName, setScenarioName] = useState('');

  useEffect(() => {
    void initCountries();
    void runSim();
  }, [initCountries, runSim]);

  const current = history.find((row) => row.year === selectedYear);
  const firstYear = history[0]?.year;
  const lastYear = history.at(-1)?.year;

  const selectedCountry = useMemo(
    () => countries.find((item) => item.code === country),
    [countries, country],
  );

  const canSave = history.length > 0 && !running && !error;

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          bgcolor: 'background.paper',
          borderBottom: '1px solid #1E2740',
        }}
      >
        <Toolbar sx={{ gap: 2, flexWrap: 'wrap', py: 1 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            ? Energy Access Dynamics Simulator
          </Typography>

          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <PublicIcon color="primary" />
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel id="country-label">Country</InputLabel>
              <Select
                labelId="country-label"
                label="Country"
                value={country}
                disabled={countries.length === 0}
                onChange={(event) => setCountry(event.target.value)}
              >
                {countries.map((item) => (
                  <MenuItem key={item.code} value={item.code}>
                    {item.name} ({item.code})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </Toolbar>
      </AppBar>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', lg: '340px minmax(0, 1fr)' },
          gap: 3,
          p: { xs: 2, md: 3 },
          alignItems: 'start',
        }}
      >
        <Paper sx={{ p: 3, border: '1px solid #1E2740' }}>
          <Typography variant="overline" color="text.secondary">
            Simulation configuration
          </Typography>

          <Typography variant="h6" sx={{ mt: 0.5 }}>
            {selectedCountry?.name ?? country}
          </Typography>

          {selectedCountry && (
            <Stack spacing={0.5} sx={{ mt: 1, mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Latest electricity access:{' '}
                {selectedCountry.access == null
                  ? 'Not available'
                  : `${selectedCountry.access.toFixed(1)}%`}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Latest clean cooking access:{' '}
                {selectedCountry.cleanCookingAccess == null
                  ? 'Not available'
                  : `${selectedCountry.cleanCookingAccess.toFixed(1)}%`}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Baseline year: {selectedCountry.baselineYear}
              </Typography>
            </Stack>
          )}

          <Divider sx={{ my: 2 }} />

          <Typography variant="overline" color="text.secondary">
            Model settings
          </Typography>

          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Projection horizon (years)"
              type="number"
              size="small"
              value={years}
              slotProps={{ htmlInput: { min: 1, max: 100 } }}
              onChange={(event) => {
                const value = Number(event.target.value);
                if (Number.isFinite(value)) {
                  setYears(Math.min(100, Math.max(1, value)));
                }
              }}
            />

            <TextField
              label="Historical trend window (years)"
              type="number"
              size="small"
              value={trendWindow}
              slotProps={{ htmlInput: { min: 2, max: 30 } }}
              onChange={(event) => {
                const value = Number(event.target.value);
                if (Number.isFinite(value)) {
                  setTrendWindow(Math.min(30, Math.max(2, value)));
                }
              }}
            />
          </Stack>

          <Divider sx={{ my: 2 }} />

          <Typography variant="overline" color="text.secondary">
            Scenario assumptions
          </Typography>

          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: 'block', mt: 0.5, mb: 2 }}
          >
            Annual adjustment to the historical trend, in percentage points.
            These are hypothetical scenario inputs, not causal estimates.
          </Typography>

          <Stack spacing={2.5}>
            <LeverSlider
              label="National electricity access"
              value={policyAdjustments.elec_access_total ?? 0}
              color="#42A5F5"
              onChange={(value) =>
                setPolicyAdjustment('elec_access_total', value)
              }
            />

            <LeverSlider
              label="Rural electricity access"
              value={policyAdjustments.elec_access_rural ?? 0}
              color="#4DD0E1"
              onChange={(value) =>
                setPolicyAdjustment('elec_access_rural', value)
              }
            />

            <LeverSlider
              label="Urban electricity access"
              value={policyAdjustments.elec_access_urban ?? 0}
              color="#FFB74D"
              onChange={(value) =>
                setPolicyAdjustment('elec_access_urban', value)
              }
            />

            <LeverSlider
              label="Clean cooking access"
              value={policyAdjustments.clean_cooking_access ?? 0}
              color="#66BB6A"
              onChange={(value) =>
                setPolicyAdjustment('clean_cooking_access', value)
              }
            />
          </Stack>

          <Button
            fullWidth
            variant="contained"
            startIcon={<PlayArrowIcon />}
            onClick={() => void runSim()}
            disabled={running}
            sx={{ mt: 3, fontWeight: 700, color: '#0B1220' }}
          >
            {running ? 'Simulatingâ€¦' : 'Run simulation'}
          </Button>

          <Divider sx={{ my: 3 }} />

          <Typography variant="overline" color="text.secondary">
            Saved scenarios
          </Typography>

          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
            <TextField
              size="small"
              fullWidth
              placeholder="Scenario name"
              value={scenarioName}
              onChange={(event) => setScenarioName(event.target.value)}
            />
            <Button
              variant="outlined"
              startIcon={<SaveIcon />}
              disabled={!canSave || !scenarioName.trim()}
              onClick={() => {
                saveScenario(scenarioName.trim());
                setScenarioName('');
              }}
            >
              Save
            </Button>
          </Stack>

          <Stack spacing={1} sx={{ mt: 2 }}>
            {scenarios.map((scenario) => (
              <Paper
                key={scenario.id}
                sx={{
                  p: 1.5,
                  bgcolor: '#0B1220',
                  border: '1px solid #1E2740',
                }}
              >
                <Stack
                  direction="row"
                  spacing={1}
                  sx={{ alignItems: "center", flexWrap: "wrap" }}
                >
                  <Box sx={{ flex: 1, minWidth: 100 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {scenario.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {scenario.country} Â· {scenario.years} years
                    </Typography>
                  </Box>
                  <Button size="small" onClick={() => loadScenario(scenario.id)}>
                    Load
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    onClick={() => deleteScenario(scenario.id)}
                  >
                    Delete
                  </Button>
                </Stack>
              </Paper>
            ))}

            {scenarios.length === 0 && (
              <Typography variant="caption" color="text.secondary">
                No saved scenarios yet.
              </Typography>
            )}
          </Stack>
        </Paper>

        <Stack spacing={3} sx={{ minWidth: 0 }}>
          {error && <Alert severity="error">{error}</Alert>}

          {baselineYear !== null && (
            <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
              <Chip label={`Baseline: ${baselineYear}`} size="small" />
              <Chip
                label={`Projection: ${years} years`}
                size="small"
                color="info"
                variant="outlined"
              />
              <Chip
                label={`Trend window: ${trendWindow} years`}
                size="small"
                variant="outlined"
              />
            </Stack>
          )}

          <KpiCards
            year={selectedYear ?? baselineYear ?? 0}
            current={current}
          />

          <Paper sx={{ p: 2, border: '1px solid #1E2740' }}>
            <Stack
              direction="row"
              spacing={1}
              sx={{
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: 1,
                mb: 1,
              }}
            >
              <Box>
                <Typography variant="h6">
                  Access trends over time
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Solid lines: historical observations Â· Dashed lines: projections
                </Typography>
              </Box>
              {current && (
                <Chip
                  size="small"
                  label={current.kind === 'historical' ? 'Historical year' : 'Projected year'}
                  color={current.kind === 'historical' ? 'default' : 'info'}
                />
              )}
            </Stack>

            <Box sx={{ height: { xs: 390, md: 460 } }}>
              {history.length > 0 ? (
                <EnergyStackChart
                  history={history}
                  year={selectedYear ?? baselineYear ?? 0}
                />
              ) : (
                <Stack
                  sx={{
                    height: '100%',
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Typography color="text.secondary">
                    {running
                      ? 'Loading simulationâ€¦'
                      : 'Run a simulation to view results.'}
                  </Typography>
                </Stack>
              )}
            </Box>
          </Paper>
                    <Paper
            sx={{
              height: 460,
              overflow: 'hidden',
              border: '1px solid #1E2740',
            }}
          >
            <Stack spacing={1} sx={{ p: 2 }}>
              <Typography variant="h6">Geographic context</Typography>
              <Typography variant="caption" color="text.secondary">
                National-level indicators are available. State-level
                projections are not currently supported by the underlying data.
              </Typography>
            </Stack>
            <Box sx={{ height: 370 }}>
              <IndiaMap />
            </Box>
          </Paper>
          {history.length > 0 &&
            firstYear !== undefined &&
            lastYear !== undefined && (
              <Paper sx={{ p: 3, border: '1px solid #1E2740' }}>
                <Stack
                  direction="row"
                  spacing={2}
                  sx={{
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <Typography variant="overline" color="text.secondary">
                    Selected year
                  </Typography>
                  <Typography
                    variant="h6"
                    color="primary.main"
                    sx={{ fontVariantNumeric: 'tabular-nums' }}
                  >
                    {selectedYear ?? baselineYear}
                  </Typography>
                </Stack>

                <input
                  type="range"
                  min={firstYear}
                  max={lastYear}
                  value={selectedYear ?? baselineYear ?? firstYear}
                  onChange={(event) =>
                    setSelectedYear(Number(event.target.value))
                  }
                  style={{
                    width: '100%',
                    marginTop: 16,
                    accentColor: '#FFB74D',
                  }}
                />

                <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                  <Typography variant="caption" color="text.secondary">
                    {firstYear}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {lastYear}
                  </Typography>
                </Stack>
              </Paper>
            )}

          <Alert severity="info" variant="outlined">
            Projections extrapolate historical trends and apply the scenario
            adjustments entered above. They are exploratory scenarios, not
            validated forecasts or estimates of causal policy impact.
          </Alert>
        </Stack>
      </Box>
    </Box>
  );
}
