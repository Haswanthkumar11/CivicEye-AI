import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { MapPin, Navigation, Compass, AlertCircle } from 'lucide-react';

interface LocationPickerProps {
  latitude?: number;
  longitude?: number;
  address?: string;
  onChange: (loc: { latitude: number; longitude: number; address?: string }) => void;
}

export const LocationPicker: React.FC<LocationPickerProps> = ({
  latitude = 17.3850,
  longitude = 78.4867,
  address = '',
  onChange,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

  const [currentLat, setCurrentLat] = useState<number>(latitude);
  const [currentLng, setCurrentLng] = useState<number>(longitude);
  const [currentAddr, setCurrentAddr] = useState<string>(address);
  const [isLocating, setIsLocating] = useState<boolean>(false);
  const [geoError, setGeoError] = useState<string | null>(null);

  // Custom SVG icon for the map marker
  const customIcon = L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="
        background: #2563eb;
        color: white;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
      ">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
  });

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current).setView([currentLat, currentLng], 14);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      const marker = L.marker([currentLat, currentLng], {
        icon: customIcon,
        draggable: true,
      }).addTo(map);

      marker.on('dragend', () => {
        const position = marker.getLatLng();
        handlePositionChange(position.lat, position.lng);
      });

      map.on('click', (e: L.LeafletMouseEvent) => {
        marker.setLatLng(e.latlng);
        handlePositionChange(e.latlng.lat, e.latlng.lng);
      });

      mapInstanceRef.current = map;
      markerRef.current = marker;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  const reverseGeocode = async (lat: number, lng: number) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`,
        { headers: { 'User-Agent': 'CivicEye-AI-Grievance-Platform' } }
      );
      if (response.ok) {
        const data = await response.json();
        if (data.display_name) {
          setCurrentAddr(data.display_name);
          onChange({ latitude: lat, longitude: lng, address: data.display_name });
          return;
        }
      }
    } catch {
      // Fallback if nominatim has CORS or network rate limit
    }
    const fallbackAddr = `Civic Zone (${lat.toFixed(5)}, ${lng.toFixed(5)})`;
    setCurrentAddr(fallbackAddr);
    onChange({ latitude: lat, longitude: lng, address: fallbackAddr });
  };

  const handlePositionChange = (lat: number, lng: number) => {
    setCurrentLat(lat);
    setCurrentLng(lng);
    reverseGeocode(lat, lng);
  };

  const handleUseGPS = () => {
    if (!navigator.geolocation) {
      setGeoError('GPS Geolocation is not supported by your browser.');
      return;
    }
    setIsLocating(true);
    setGeoError(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        setCurrentLat(lat);
        setCurrentLng(lng);

        if (mapInstanceRef.current && markerRef.current) {
          mapInstanceRef.current.setView([lat, lng], 16);
          markerRef.current.setLatLng([lat, lng]);
        }
        reverseGeocode(lat, lng);
        setIsLocating(false);
      },
      (err) => {
        setIsLocating(false);
        setGeoError(`Could not acquire GPS: ${err.message}. Please click on the map to set location.`);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-semibold text-slate-200">
            Geographic Location & Incident Coordinates
          </span>
        </div>

        <button
          type="button"
          onClick={handleUseGPS}
          disabled={isLocating}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 text-xs font-medium transition-colors disabled:opacity-50"
        >
          <Navigation className={`w-3.5 h-3.5 ${isLocating ? 'animate-spin' : ''}`} />
          <span>{isLocating ? 'Detecting GPS...' : 'Use My Current Location'}</span>
        </button>
      </div>

      {geoError && (
        <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{geoError}</span>
        </div>
      )}

      {/* Interactive Map Box */}
      <div className="relative rounded-xl overflow-hidden border border-slate-800 shadow-inner">
        <div ref={mapContainerRef} className="h-64 sm:h-72 w-full z-0" />
        <div className="absolute bottom-2 left-2 z-10 px-2.5 py-1 rounded-md bg-slate-900/90 backdrop-blur-sm border border-slate-800 text-[11px] text-slate-300 font-mono shadow">
          Lat: {currentLat.toFixed(5)}, Lng: {currentLng.toFixed(5)}
        </div>
      </div>

      {/* Address display / manual edit */}
      <div className="space-y-1">
        <label className="text-[11px] text-slate-400 font-medium">
          Identified Landmark / Street Address:
        </label>
        <div className="relative">
          <Compass className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={currentAddr}
            onChange={(e) => {
              setCurrentAddr(e.target.value);
              onChange({ latitude: currentLat, longitude: currentLng, address: e.target.value });
            }}
            placeholder="e.g. Near Community Center, Road No 12, Ward 5"
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>
    </div>
  );
};
