import { Fragment } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import type { StateData } from '../types';
import 'leaflet/dist/leaflet.css';
import './IndiaMap.css';

interface Props {
  states: StateData[];
  year: number;
  accessByState: Record<string, number>;
}

/** Linearly interpolate between two hex colors. t ∈ [0, 1]. */
function lerpColor(a: string, b: string, t: number): string {
  const ah = parseInt(a.slice(1), 16);
  const bh = parseInt(b.slice(1), 16);
  const ar = (ah >> 16) & 0xff, ag = (ah >> 8) & 0xff, ab = ah & 0xff;
  const br = (bh >> 16) & 0xff, bg = (bh >> 8) & 0xff, bb = bh & 0xff;
  const rr = Math.round(ar + (br - ar) * t);
  const rg = Math.round(ag + (bg - ag) * t);
  const rb = Math.round(ab + (bb - ab) * t);
  return `#${((rr << 16) | (rg << 8) | rb).toString(16).padStart(6, '0')}`;
}

/**
 * Brown (traditional fuels) → orange (SHS) → blue (national grid).
 * Matches the tier colors on the chart so the map and chart speak the same
 * visual language.
 */
function colorForAccess(access: number): string {
  const a = Math.max(0, Math.min(100, access));
  if (a < 50) return lerpColor('#8D6E63', '#FB8C00', a / 50);
  return lerpColor('#FB8C00', '#42A5F5', (a - 50) / 50);
}

export function IndiaMap({ states, year, accessByState }: Props) {
  return (
    <MapContainer
      center={[22.5, 79]}
      zoom={4.4}
      scrollWheelZoom
      style={{ height: '100%', width: '100%', background: '#0B1220' }}
    >
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        attribution="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"
        maxZoom={16}
      />

      {states.map((s) => {
        const access = accessByState[s.id] ?? s.initialAccess;
        const color = colorForAccess(access);

        // Radius grows with population AND with access progress.
        // A state at 100% access is ~67% bigger than at 0% — visibly
        // "swelling" as electrification spreads over the years.
        const baseRadius = 5 + Math.sqrt(s.population);
        const accessBoost = 0.75 + (access / 100) * 0.5;
        const radius = baseRadius * accessBoost;

        // Stagger the halo pulse deterministically per state so they
        // don't all breathe in sync (looks more organic).
        const delayClass = `hal-delay-${(s.id.charCodeAt(0) + s.id.charCodeAt(1)) % 6}`;

        return (
          <Fragment key={s.id}>
            {/* Layer 1 — soft outer halo (largest, faintest) */}
            <CircleMarker
              center={[s.lat, s.lng]}
              radius={radius * 1.9}
              pathOptions={{
                stroke: false,
                fillColor: color,
                fillOpacity: 0.08,
                className: `state-halo ${delayClass}`,
              }}
            />

            {/* Layer 2 — mid ring for depth */}
            <CircleMarker
              center={[s.lat, s.lng]}
              radius={radius * 1.35}
              pathOptions={{
                stroke: false,
                fillColor: color,
                fillOpacity: 0.2,
              }}
            />

            {/* Layer 3 — solid core with white rim */}
            <CircleMarker
              center={[s.lat, s.lng]}
              radius={radius}
              pathOptions={{
                stroke: true,
                color: '#ffffff',
                weight: 1.2,
                opacity: 0.55,
                fillColor: color,
                fillOpacity: 0.85,
                className: 'state-core',
              }}
            >
              <Tooltip
                direction="top"
                opacity={1}
                className="state-tooltip"
                offset={[0, -4]}
              >
                <div style={{ fontWeight: 700, marginBottom: 4 }}>{s.name}</div>
                <div style={{ color: '#94A3B8' }}>
                  Access {year}:{' '}
                  <span style={{ color, fontWeight: 700 }}>
                    {access.toFixed(0)}%
                  </span>
                </div>
                <div style={{ color: '#94A3B8' }}>
                  Population: {s.population}M
                </div>
              </Tooltip>
            </CircleMarker>
          </Fragment>
        );
      })}
    </MapContainer>
  );
}