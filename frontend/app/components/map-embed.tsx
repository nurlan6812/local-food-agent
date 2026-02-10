'use client';

import { useEffect, useRef, useState } from 'react';
import { MapPin, X, ExternalLink } from 'lucide-react';

declare global {
  interface Window {
    kakao: any;
  }
}

interface MapEmbedProps {
  url: string;
}

interface PlaceInfo {
  lat: number;
  lng: number;
  name: string;
  address?: string;
  phone?: string;
  category?: string;
  kakaoUrl?: string;
}

// URL에서 좌표 추출 (여러 좌표 지원)
function parseCoordinates(url: string): PlaceInfo[] {
  const places: PlaceInfo[] = [];

  // 새 형식: lat1,lng1,name1|address1|phone1|category1|kakaoUrl1;lat2,lng2,...
  if (url.includes(';') || !url.startsWith('http')) {
    const parts = url.split(';');
    for (const part of parts) {
      const [lat, lng, ...infoParts] = part.split(',');
      if (lat && lng) {
        const infoStr = infoParts.join(',');
        const [name, address, phone, category, kakaoUrl] = infoStr.split('|');
        places.push({
          lat: parseFloat(lat),
          lng: parseFloat(lng),
          name: name || '식당',
          address: address || undefined,
          phone: phone || undefined,
          category: category || undefined,
          kakaoUrl: kakaoUrl || undefined,
        });
      }
    }
    return places;
  }

  // 기존 Google Maps URL 형식
  const googleMatch = url.match(/[?&]q=([-\d.]+),([-\d.]+)/);
  if (googleMatch) {
    places.push({
      lat: parseFloat(googleMatch[1]),
      lng: parseFloat(googleMatch[2]),
      name: '위치',
    });
  }

  return places;
}

// 마커 색상
const MARKER_COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1'];

// 마커 요소 생성 (DOM API 사용)
function createMarkerElement(index: number, color: string, isSelected: boolean): HTMLDivElement {
  const wrapper = document.createElement('div');
  const marker = document.createElement('div');

  Object.assign(marker.style, {
    backgroundColor: color,
    color: 'white',
    width: isSelected ? '38px' : '32px',
    height: isSelected ? '38px' : '32px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: isSelected ? '16px' : '14px',
    border: isSelected ? '4px solid white' : '3px solid white',
    boxShadow: isSelected ? '0 4px 12px rgba(0,0,0,0.4)' : '0 2px 8px rgba(0,0,0,0.3)',
    cursor: 'pointer',
    transition: 'all 0.2s',
    transform: isSelected ? 'scale(1.1)' : 'scale(1)',
  });
  marker.textContent = String(index + 1);

  wrapper.appendChild(marker);
  return wrapper;
}

export function MapEmbed({ url }: MapEmbedProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlace, setSelectedPlace] = useState<PlaceInfo | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const markersRef = useRef<{ overlay: any; element: HTMLDivElement }[]>([]);
  const mapInstanceRef = useRef<any>(null);

  const places = parseCoordinates(url);

  useEffect(() => {
    if (places.length === 0) {
      // 좌표가 없으면 조용히 아무것도 표시하지 않음
      return;
    }

    // 카카오맵 SDK 로드 확인
    if (!window.kakao || !window.kakao.maps) {
      setError('카카오맵 SDK가 로드되지 않았습니다');
      return;
    }

    // 카카오맵 로드
    window.kakao.maps.load(() => {
      if (!mapRef.current) return;

      try {
        // 첫 번째 좌표를 중심으로 설정
        const centerPosition = new window.kakao.maps.LatLng(places[0].lat, places[0].lng);

        const map = new window.kakao.maps.Map(mapRef.current, {
          center: centerPosition,
          level: 4,
        });
        mapInstanceRef.current = map;

        // 모든 마커의 bounds 계산용
        const bounds = new window.kakao.maps.LatLngBounds();
        markersRef.current = [];

        // 마커 클릭 핸들러 (재사용 가능하도록 분리)
        const handleMarkerClick = (clickedIndex: number) => {
          const clickedPlace = places[clickedIndex];
          const clickedPosition = new window.kakao.maps.LatLng(clickedPlace.lat, clickedPlace.lng);

          // 지도 이동
          map.panTo(clickedPosition);

          // 선택 상태 업데이트
          setSelectedPlace(clickedPlace);
          setSelectedIndex(clickedIndex);

          // 모든 마커 스타일 업데이트
          markersRef.current.forEach((m, i) => {
            const newMarker = createMarkerElement(i, MARKER_COLORS[i % MARKER_COLORS.length], i === clickedIndex);
            m.element.replaceWith(newMarker);
            m.element = newMarker;

            // 새 마커에도 클릭 이벤트 추가 (같은 핸들러 사용)
            newMarker.onclick = () => handleMarkerClick(i);
          });
        };

        // 여러 마커 추가
        places.forEach((place, index) => {
          const position = new window.kakao.maps.LatLng(place.lat, place.lng);
          bounds.extend(position);

          const color = MARKER_COLORS[index % MARKER_COLORS.length];
          const markerContent = createMarkerElement(index, color, false);

          const customOverlay = new window.kakao.maps.CustomOverlay({
            position: position,
            content: markerContent,
            yAnchor: 1,
          });
          customOverlay.setMap(map);

          markersRef.current.push({ overlay: customOverlay, element: markerContent });

          // 마커 클릭 이벤트
          markerContent.onclick = () => handleMarkerClick(index);
        });

        // 지도 클릭 시 선택 해제
        window.kakao.maps.event.addListener(map, 'click', () => {
          setSelectedPlace(null);
          setSelectedIndex(null);
        });

        // 지도 컨트롤 추가
        const zoomControl = new window.kakao.maps.ZoomControl();
        map.addControl(zoomControl, window.kakao.maps.ControlPosition.RIGHT);

        setIsLoaded(true);

        // 컨테이너 크기 변경 후 지도 재렌더링 및 bounds 조정
        setTimeout(() => {
          map.relayout();
          if (places.length > 1) {
            // 모든 마커가 보이도록 bounds 설정
            map.setBounds(bounds);
            // 한 단계 축소해서 여유 공간 확보
            setTimeout(() => {
              const currentLevel = map.getLevel();
              map.setLevel(currentLevel + 1);
            }, 50);
          } else {
            map.setCenter(centerPosition);
            map.setLevel(3); // 단일 마커일 때 적절한 줌 레벨
          }
        }, 100);
      } catch (e) {
        setError('지도를 로드하는 중 오류가 발생했습니다');
        console.error('Kakao Map Error:', e);
      }
    });
  }, [url]);

  // 선택 해제 함수
  const handleClose = () => {
    setSelectedPlace(null);
    setSelectedIndex(null);
  };

  if (error) {
    return (
      <div className="rounded-lg overflow-hidden border border-border bg-card">
        <div className="flex items-center gap-2 px-3 py-2 bg-muted/50 border-b border-border">
          <MapPin className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium text-foreground">위치 정보</span>
        </div>
        <div className="p-4 text-center text-muted-foreground text-sm">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg overflow-hidden border border-border bg-card">
      <div className="flex items-center gap-2 px-3 py-2 bg-muted/50 border-b border-border">
        <MapPin className="h-4 w-4 text-primary" />
        <span className="text-sm font-medium text-foreground">위치 정보</span>
      </div>

      {/* 지도 영역 */}
      <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
        <div
          ref={mapRef}
          className="absolute inset-0 w-full h-full"
          style={{ display: isLoaded ? 'block' : 'none' }}
        />
        {!isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-muted">
            <div className="text-sm text-muted-foreground">지도 로딩 중...</div>
          </div>
        )}

        {/* 선택된 장소 정보 패널 (지도 하단에 오버레이) */}
        {selectedPlace && selectedIndex !== null && (
          <div className="absolute bottom-0 left-0 right-0 z-50 bg-white dark:bg-gray-800 border-t border-border shadow-lg animate-in slide-in-from-bottom-4 duration-200">
            <div className="p-4">
              {/* 헤더 */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
                    style={{ backgroundColor: MARKER_COLORS[selectedIndex % MARKER_COLORS.length] }}
                  >
                    {selectedIndex + 1}
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground text-base">{selectedPlace.name}</h3>
                    {selectedPlace.category && (
                      <span className="text-xs text-muted-foreground">{selectedPlace.category}</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={handleClose}
                  className="p-1 hover:bg-muted rounded-full transition-colors"
                >
                  <X className="h-5 w-5 text-muted-foreground" />
                </button>
              </div>

              {/* 정보 */}
              <div className="mt-3 space-y-1 text-sm">
                {selectedPlace.address && (
                  <p className="text-muted-foreground">\ud83d\udccd {selectedPlace.address}</p>
                )}
                {selectedPlace.phone && (
                  <p className="text-muted-foreground">\ud83d\udcde {selectedPlace.phone}</p>
                )}
              </div>

              {/* 카카오맵 링크 */}
              {selectedPlace.kakaoUrl && (
                <a
                  href={selectedPlace.kakaoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 flex items-center justify-center gap-2 w-full py-2.5 bg-[#FEE500] hover:bg-[#F5D800] text-[#3C1E1E] rounded-lg font-medium text-sm transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                  카카오맵에서 보기
                </a>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
