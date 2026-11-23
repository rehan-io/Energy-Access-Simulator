import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  AppBar,
  Box,
  Button,
  Chip,
  Divider,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  TextField,
  Toolbar,
  Typography,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import SaveIcon from '@mui/icons-material/Save';
import PublicIcon from '@mui/icons-material/Public';

import { useSimStore } from '../store/useSimStore';
import { LeverSlider } from '../components/LeverSlider';
import { KpiCards } from '../components/KpiCards';
import { EnergyStackChart, TierStackChart } from '../components/EnergyStackChart';
import { IndiaMap } from '../components/IndiaMap';

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
    policyLevers,
    setPolicyLever,
    setRecycleTaxRevenue,
    resetPolicyLevers,
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
            ⚡ Energy Access Dynamics Simulator
          </Typography>

          <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
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
          gridTemplateColumns: { xs: '1fr', lg: '360px minmax(0, 1fr)' },
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

          <Stack
            direction="row"
            sx={{ justifyContent: 'space-between', alignItems: 'center' }}
          >
            <Typography variant="overline" color="text.secondary">
              Policy levers
            </Typography>
            <Button
              size="small"
              startIcon={<RestartAltIcon />}
              onClick={resetPolicyLevers}
              sx={{ textTransform: 'none' }}
            >
              Reset
            </Button>
          </Stack>

          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: 'block', mt: 0.5, mb: 2 }}
          >
            Adjust structural policy dials (0–100%). Effects propagate through
            empirical demand elasticities, Wright&apos;s Law learning, grid
            remoteness penalties, and clean-cooking fuel stacking.
          </Typography>

          <Stack spacing={2.5}>
            <LeverSlider
              label="Subsidy Percentage"
              value={policyLevers.subsidy}
              color="#FFB74D"
              description="Reduces upfront capital costs for grid connections, off-grid solar, and clean cooking."
              onChange={(value) => setPolicyLever('subsidy', value)}
            />

            <LeverSlider
              label="Carbon Tax"
              value={policyLevers.carbon_tax}
              color="#EF5350"
              description="Raises traditional fuel prices (kerosene, diesel, LPG) to incentivize switching."
              onChange={(value) => setPolicyLever('carbon_tax', value)}
            />

            <LeverSlider
              label="Off-Grid Deployment Rate"
              value={policyLevers.off_grid}
              color="#26A69A"
              description="Speed at which solar home system and mini-grid providers reach rural areas."
              onChange={(value) => setPolicyLever('off_grid', value)}
            />

            <LeverSlider
              label="Grid Extension Speed"
              value={policyLevers.grid_ext}
              color="#42A5F5"
              description="Annual rate at which the national utility extends transmission and distribution lines."
              onChange={(value) => setPolicyLever('grid_ext', value)}
            />
          </Stack>

          <Box
            sx={{
              mt: 2.5,
              p: 1.5,
              borderRadius: 1.5,
              bgcolor: '#0B1220',
              border: '1px solid #1E2740',
            }}
          >
            <FormControlLabel
              control={
                <Switch
                  checked={policyLevers.recycle_tax_revenue}
                  onChange={(event) =>
                    setRecycleTaxRevenue(event.target.checked)
                  }
                  color="secondary"
                />
              }
              label={
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  Recycle carbon-tax revenue
                </Typography>
              }
            />
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: 'block', mt: 0.5 }}
            >
              Shields low-income households from LPG price increases; disabling
              this without subsidies causes biomass backfire.
            </Typography>
          </Box>

          <Button
            fullWidth
            variant="contained"
            startIcon={<PlayArrowIcon />}
            onClick={() => void runSim()}
            disabled={running}
            sx={{ mt: 3, fontWeight: 700, color: '#0B1220' }}
          >
            {running ? 'Simulating…' : 'Run simulation'}
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
                  sx={{ alignItems: 'center', flexWrap: 'wrap' }}
                >
                  <Box sx={{ flex: 1, minWidth: 100 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {scenario.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {scenario.country} · {scenario.years} years · Sub{' '}
                      {scenario.policyLevers.subsidy}% / Tax{' '}
                      {scenario.policyLevers.carbon_tax}%
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
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
              <Chip label={`Baseline: ${baselineYear}`} size="small" />
              <Chip
                label={`Projection: ${years} years`}
                size="small"
                color="info"
                variant="outlined"
              />
              <Chip
                label="Coupled Bass-Logistic & 5-Tier Engine"
                size="small"
                color="secondary"
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
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 1,
                mb: 1,
              }}
            >
              <Box>
                <Typography variant="h6">
                  Access trends over time
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Solid lines: World Bank historical · Dashed lines: coupled
                  bounded projections
                </Typography>
              </Box>
              {current && (
                <Chip
                  size="small"
                  label={
                    current.kind === 'historical'
                      ? 'Historical year'
                      : 'Projected year'
                  }
                  color={current.kind === 'historical' ? 'default' : 'info'}
                />
              )}
            </Stack>

            <Box sx={{ height: { xs: 380, md: 430 } }}>
              {history.length > 0 ? (
                <EnergyStackChart
                  history={history}
                  year={selectedYear ?? baselineYear ?? 0}
                />
              ) : (
                <Stack
                  sx={{
                    height: '100%',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Typography color="text.secondary">
                    {running
                      ? 'Loading simulation…'
                      : 'Run a simulation to view results.'}
                  </Typography>
                </Stack>
              )}
            </Box>
          </Paper>

          <Paper sx={{ p: 2, border: '1px solid #1E2740' }}>
            <Stack
              direction="row"
              spacing={1}
              sx={{
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 1,
                mb: 1,
              }}
            >
              <Box>
                <Typography variant="h6">
                  Five-tier energy ladder composition
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Synchronized stock shares summing to 100% (Grid, Mini-Grid,
                  SHS, Lantern, Traditional)
                </Typography>
              </Box>
              {current?.grid != null && (
                <Chip
                  size="small"
                  label={`Grid ${current.grid.toFixed(1)}% · Off-grid ${(
                    (current.minigrid ?? 0) +
                    (current.shs ?? 0) +
                    (current.lantern ?? 0)
                  ).toFixed(1)}%`}
                  variant="outlined"
                />
              )}
            </Stack>

            <Box sx={{ height: { xs: 340, md: 380 } }}>
              {history.some((row) => row.grid != null) ? (
                <TierStackChart
                  history={history}
                  year={selectedYear ?? baselineYear ?? 0}
                />
              ) : (
                <Stack
                  sx={{
                    height: '100%',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Typography color="text.secondary">
                    {running
                      ? 'Loading energy ladder stocks…'
                      : 'Run a simulation to view tier transitions.'}
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
                    alignItems: 'center',
                    justifyContent: 'space-between',
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

                <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
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
            Projections use a bounded Coupled Bass-Logistic and Five-Tier
            Stock-and-Flow model calibrated to World Bank baselines, empirical
            price elasticities, Wright&apos;s Law learning, and rural
            urbanization trends.
          </Alert>
        </Stack>
      </Box>
    </Box>
  );
}