
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export function IndiaMap() {
  return (
    <MapContainer
      center={[22.5, 79]}
      zoom={4.4}
      scrollWheelZoom
      style={{
        height: '100%',
        width: '100%',
        background: '#0B1220',
      }}
    >
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        attribution="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"
        maxZoom={16}
      />
    </MapContainer>
  );
}
