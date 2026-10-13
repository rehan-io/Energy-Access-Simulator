import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import type { StateData } from '../types';
import 'leaflet/dist/leaflet.css';

interface Props {
  states: StateData[];
  year: number;
  accessByState: Record<string, number>;
}

function colorForAccess(a: number) {
  if (a > 90) return '#42A5F5';
  if (a > 70) return '#26A69A';
  if (a > 40) return '#FB8C00';
  if (a > 20) return '#FDD835';
  return '#8D6E63';
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
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; OpenStreetMap &copy; CARTO'
      />
      {states.map((s) => {
        const access = accessByState[s.id] ?? s.initialAccess;
        const color = colorForAccess(access);
        return (
          <CircleMarker
            key={s.id}
            center={[s.lat, s.lng]}
            radius={Math.sqrt(s.population) * 2.2}
            pathOptions={{ color, fillColor: color, fillOpacity: 0.55, weight: 1.5 }}
          >
            <Tooltip direction="top">
              <div style={{ fontWeight: 600 }}>{s.name}</div>
              <div>Access ({year}): {access.toFixed(0)}%</div>
              <div>Pop: {s.population}M</div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}