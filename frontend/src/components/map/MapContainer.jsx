import { MapContainer as LeafletMap, TileLayer } from 'react-leaflet'
import LocationMarkers from './LocationMarkers'
import RoutePolylines from './RoutePolylines'

const BANGALORE_CENTER = [12.9716, 77.5946]
const DEFAULT_ZOOM = 12

export default function MapContainer({ mapData, viewMode }) {
  const center = mapData?.center
    ? [mapData.center.lat, mapData.center.lon]
    : BANGALORE_CENTER

  return (
    <LeafletMap
      center={center}
      zoom={DEFAULT_ZOOM}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {mapData && (
        <>
          <LocationMarkers
            pickupPoints={mapData.pickupPoints}
            dropoffPoints={mapData.dropoffPoints}
            vehicleStarts={mapData.vehicleStarts}
            viewMode={viewMode}
          />

          {viewMode === 'optimized' && mapData.routes && (
            <RoutePolylines routes={mapData.routes} />
          )}
        </>
      )}
    </LeafletMap>
  )
}
