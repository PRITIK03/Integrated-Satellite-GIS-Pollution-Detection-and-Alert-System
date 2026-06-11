function initMap(){
  map = L.map('map').setView(CITY_CENTERS['Delhi'] || [28.6, 77.2], 9);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
  markersLayer = L.layerGroup().addTo(map);

  legendControl = L.control({position:'bottomright'});
  legendControl.onAdd = function(){
    const div = L.DomUtil.create('div','legend');
    const levels = ['good','moderate','unhealthy_sensitive','unhealthy','very_unhealthy','hazardous'];
    div.innerHTML = '<strong>Risk</strong><br>' + levels.map(l=>{
      return `<span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${colorForRisk(l)};margin-right:6px"></span>${l.replace('_',' ')}`;
    }).join('<br>');
    return div;
  };
  legendControl.addTo(map);
}

function jitteredPoints(lat, lon, n=24, radiusKm=15){
  const pts=[];
  for(let i=0;i<n;i++){
    const r = radiusKm * (0.3 + Math.random()*0.7);
    const t = Math.random()*Math.PI*2;
    const dx = (r/111) * Math.cos(t);
    const dy = (r/(111*Math.cos(lat*Math.PI/180))) * Math.sin(t);
    pts.push([lat+dy, lon+dx]);
  }
  return pts;
}

function updateMap(data){
  markersLayer.clearLayers();
  if(!data || data.length === 0) return;

  const latest = data[data.length-1];
  const city = els.citySelect?.value || 'Delhi';
  const preset = CITY_CENTERS[city];
  const baseLat = latest.latitude ?? preset?.[0] ?? 28.6139;
  const baseLon = latest.longitude ?? preset?.[1] ?? 77.2090;

  const points = jitteredPoints(baseLat, baseLon, 36, 18);

  points.forEach(([lat, lon])=>{
    const pm = (latest['PM2.5'] ?? 0) * (0.8 + Math.random()*0.6);
    const n2 = (latest['NO2'] ?? 0) * (0.8 + Math.random()*0.6);
    const risk = riskFromValues(pm, n2);
    const color = colorForRisk(risk);

    const circle = L.circleMarker([lat, lon], {
      radius: 6 + Math.random()*6,
      color,
      weight: 1.5,
      fillColor: color,
      fillOpacity: 0.55
    }).bindPopup(`PM2.5: ${pm.toFixed(1)}<br/>NO2: ${n2.toFixed(1)}<br/>Risk: ${risk.replace('_',' ')}`);
    circle.addTo(markersLayer);
  });

  if(map){ map.flyTo([baseLat, baseLon], 9, {animate:true, duration:0.8}); }
}
