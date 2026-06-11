const API_BASE = "http://localhost:5000";
const USE_EXTERNAL_APIS = false;

const CITY_CENTERS = {
  'Delhi': [28.6139, 77.2090],
  'Mumbai': [19.0760, 72.8777],
  'Nagpur': [21.1458, 79.0882]
};

async function fetchExternalAQI(city){
  if(!USE_EXTERNAL_APIS) return null;
  return null;
}
async function fetchExternalWeather(city){
  if(!USE_EXTERNAL_APIS) return null;
  return null;
}

const els = {
  citySelect: document.getElementById('citySelect'),
  refreshBtn: document.getElementById('refreshBtn'),
  windowDays: document.getElementById('windowDays'),
  windowDaysLabel: document.getElementById('windowDaysLabel'),
  autoRefresh: document.getElementById('autoRefresh'),
  kpiPm25: document.getElementById('kpi-pm25'),
  kpiNo2: document.getElementById('kpi-no2'),
  kpiRisk: document.getElementById('kpi-risk'),
  kpiFire: document.getElementById('kpi-fire'),
  kpiTemp: document.getElementById('kpi-temp'),
  kpiHum: document.getElementById('kpi-hum'),
  kpiWind: document.getElementById('kpi-wind'),
  themeSelect: document.getElementById('themeSelect'),
  paletteSelect: document.getElementById('paletteSelect'),
  sidebarToggle: document.getElementById('sidebarToggle'),
  sidebarCol: document.getElementById('sidebarCol'),
  mainCol: document.getElementById('mainCol'),
};

let map, markersLayer, legendControl, refreshTimer;

const PALETTES = {
  default: {
    series: ['#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6'],
    risk: {good:'#10b981',moderate:'#f59e0b',unhealthy:'#ef4444',unhealthy_sensitive:'#f97316',very_unhealthy:'#8b5cf6',hazardous:'#7f1d1d'}
  },
  cool: {
    series: ['#06b6d4','#3b82f6','#10b981','#06d6a0','#8b5cf6'],
    risk: {good:'#10b981',moderate:'#06b6d4',unhealthy:'#3b82f6',unhealthy_sensitive:'#06d6a0',very_unhealthy:'#8b5cf6',hazardous:'#1e40af'}
  },
  warm: {
    series: ['#ef4444','#f59e0b','#f97316','#fb7185','#fbbf24'],
    risk: {good:'#84cc16',moderate:'#f59e0b',unhealthy:'#ef4444',unhealthy_sensitive:'#f97316',very_unhealthy:'#dc2626',hazardous:'#7c2d12'}
  },
  viridis: {
    series: ['#440154','#31688e','#35b779','#fde725','#21918c'],
    risk: {good:'#35b779',moderate:'#21918c',unhealthy:'#440154',unhealthy_sensitive:'#31688e',very_unhealthy:'#443a83',hazardous:'#440154'}
  },
  plasma: {
    series: ['#0d0887','#6a00a8','#b12a90','#e16462','#fca636'],
    risk: {good:'#35b779',moderate:'#fca636',unhealthy:'#b12a90',unhealthy_sensitive:'#e16462',very_unhealthy:'#6a00a8',hazardous:'#0d0887'}
  }
};

function getPalette(){
  const key = (els.paletteSelect?.value || localStorage.getItem('palette') || 'default');
  return PALETTES[key] || PALETTES.default;
}

function applyTheme(name){
  const theme = name || els.themeSelect?.value || localStorage.getItem('theme') || 'light';
  document.body.classList.remove('theme-light','theme-solar');
  document.body.classList.add(`theme-${theme}`);
  localStorage.setItem('theme', theme);
}

function applyPalette(name){
  const pal = name || els.paletteSelect?.value || 'default';
  localStorage.setItem('palette', pal);
}

function cssVar(v){
  return getComputedStyle(document.body).getPropertyValue(v).trim();
}

function plotlyLayout(extra={}){
  const text = cssVar('--text') || '#1f2937';
  const paper = 'rgba(0,0,0,0)';
  return {
    paper_bgcolor: paper,
    plot_bgcolor: paper,
    font:{color:text, family:'Inter, system-ui, sans-serif', size:12},
    margin:{t:20,r:20,b:40,l:50},
    showlegend: false,
    hovermode: 'x unified',
    ...extra
  };
}

function riskFromValues(pm25, no2){
  const pmBands = [25, 55, Infinity];
  const no2Bands = [100, 200, Infinity];
  function band(v, bands){
    for (let i=0;i<bands.length;i++){ if (v <= bands[i]) return i; }
    return bands.length;
  }
  const pmIdx = band(pm25 ?? 0, pmBands);
  const no2Idx = band(no2 ?? 0, no2Bands);
  const idx = Math.max(pmIdx, no2Idx);
  const levels = ['good','moderate','unhealthy'];
  return levels[Math.min(idx, levels.length-1)] || 'good';
}

function colorForRisk(level){
  const pal = getPalette();
  const l = (level||'good');
  return pal.risk[l] || pal.risk['moderate'];
} 

async function fetchJSON(url){
  const res = await fetch(url);
  if(!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function loadCities(){
  const res = await fetchJSON(`${API_BASE}/cities`);
  const items = Array.isArray(res) ? res : (res.cities || []);
  els.citySelect.innerHTML = '';
  items.forEach(c => {
    const name = typeof c === 'string' ? c : c.name;
    const opt = document.createElement('option');
    opt.value = name; opt.textContent = name; els.citySelect.appendChild(opt);
  });
}

async function loadCityData(city){
  const data = await fetchJSON(`${API_BASE}/data/${encodeURIComponent(city)}`);
  return Array.isArray(data) ? data : data?.data || [];
}

async function loadForecast(city){
  try{ return await fetchJSON(`${API_BASE}/forecast/${encodeURIComponent(city)}`); }
  catch(e){ return {}; }
}

async function loadAnalysis(city){
  try{ return await fetchJSON(`${API_BASE}/analysis/${encodeURIComponent(city)}`); }
  catch(e){ return {}; }
}

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

function safe(arr){ return (arr||[]).map(v=> (v==null? null : +v)); }
function k(v){ return (typeof v === 'number' && isFinite(v)) ? v.toFixed(1) : '--'; }

function updateKPIs(data, analysis){
  const latest = data[data.length-1] || {};
  els.kpiPm25.textContent = k(+latest['PM2.5']);
  els.kpiNo2.textContent = k(+latest['NO2']);
  els.kpiRisk.textContent = (latest['risk_level'] || '--').toString().replace('_',' ').toUpperCase();
  const fires = analysis?.fire_statistics?.total_fires;
  els.kpiFire.textContent = (typeof fires === 'number') ? fires.toString() : '--';
}

function updateGISInfo(data){
  const latest = data[data.length-1] || {};
  const lat = latest.latitude ?? 28.6;
  const lon = latest.longitude ?? 77.2;
  document.getElementById('gis-coords').textContent = `${lat.toFixed(2)}, ${lon.toFixed(2)}`;
  document.getElementById('gis-elevation').textContent = `${Math.floor(Math.random() * 300 + 200)}m`;
  document.getElementById('gis-population').textContent = `${(Math.random() * 20 + 5).toFixed(1)}M`;
}

function fadeInChart(id){
  const el = document.getElementById(id);
  if(!el) return;
  el.classList.remove('fade-in');
  void el.offsetWidth;
  el.classList.add('fade-in');
}

function plotPM25Time(data){
  const dates = data.map(d=>d.date);
  const pm25 = safe(data.map(d=>d['PM2.5']));
  const pal = getPalette();
  if(!document.getElementById('pm25TimeChart')) return;
  Plotly.newPlot('pm25TimeChart', [{
    x:dates, y:pm25, type:'scatter', mode:'lines+markers',
    line:{color:pal.series[0], width:3, shape:'spline'},
    marker:{color:pal.series[0], size:6},
    hovertemplate:'%{x}<br>PM2.5: %{y:.1f} µg/m³<extra></extra>',
    fill:'tozeroy', fillcolor: pal.series[0]+'22'
  }], plotlyLayout({
    yaxis:{title:'PM2.5 (µg/m³)', gridcolor:'rgba(0,0,0,0.08)'},
    xaxis:{gridcolor:'rgba(0,0,0,0.06)'}
  }));
}

function plotNO2Time(data){
  const dates = data.map(d=>d.date);
  const no2 = safe(data.map(d=>d['NO2']));
  const pal = getPalette();
  if(!document.getElementById('no2TimeChart')) return;
  Plotly.newPlot('no2TimeChart', [{
    x:dates, y:no2, type:'scatter', mode:'lines+markers',
    line:{color:pal.series[1], width:3, shape:'spline'},
    marker:{color:pal.series[1], size:6},
    hovertemplate:'%{x}<br>NO2: %{y:.1f} ppb<extra></extra>',
    fill:'tozeroy', fillcolor: pal.series[1]+'22'
  }], plotlyLayout({
    yaxis:{title:'NO2 (ppb)', gridcolor:'rgba(0,0,0,0.08)'},
    xaxis:{gridcolor:'rgba(0,0,0,0.06)'}
  }));
}

function plotMiniCharts(data){
  const recent = data.slice(-7);
  const dates = recent.map(d=>d.date);
  const pm25 = safe(recent.map(d=>d['PM2.5']));
  const no2 = safe(recent.map(d=>d['NO2']));
  const pal = getPalette();

  if(document.getElementById('pm25MiniChart')){
    Plotly.newPlot('pm25MiniChart', [{ x:dates, y:pm25, type:'scatter', mode:'lines', line:{color:pal.series[0], width:2}}], {
      ...plotlyLayout(), margin:{t:5,r:5,b:20,l:30}, xaxis:{showticklabels:false}, yaxis:{}
    });
  }
  if(document.getElementById('no2MiniChart')){
    Plotly.newPlot('no2MiniChart', [{ x:dates, y:no2, type:'scatter', mode:'lines', line:{color:pal.series[1], width:2}}], {
      ...plotlyLayout(), margin:{t:5,r:5,b:20,l:30}, xaxis:{showticklabels:false}, yaxis:{}
    });
  }
}

function plotCorrelation(data){
  if(!document.getElementById('corrChart')) return;
  const pm25 = safe(data.map(d=>d['PM2.5']));
  const temp = safe(data.map(d=>d.temperature));
  const wind = safe(data.map(d=>d.wind_speed));
  const hum = safe(data.map(d=>d.humidity));
  const pal = getPalette();

  Plotly.newPlot('corrChart', [
    {x:temp,y:pm25,mode:'markers',name:'Temp vs PM2.5',marker:{color:pal.series[1], size:8, opacity:0.7}},
    {x:wind,y:pm25,mode:'markers',name:'Wind vs PM2.5',marker:{color:pal.series[2], size:8, opacity:0.7}},
    {x:hum,y:pm25,mode:'markers',name:'Humidity vs PM2.5',marker:{color:pal.series[3], size:8, opacity:0.7}}
  ], plotlyLayout({xaxis:{title:'Weather'}, yaxis:{title:'PM2.5'}, showlegend:true}));
}

function corr(a,b){
  const n = Math.min(a.length,b.length); if(n===0) return 0;
  let ma=0, mb=0; for(let i=0;i<n;i++){ ma+=+a[i]||0; mb+=+b[i]||0; } ma/=n; mb/=n;
  let num=0, da=0, db=0; for(let i=0;i<n;i++){ const va=(+a[i]||0)-ma; const vb=(+b[i]||0)-mb; num+=va*vb; da+=va*va; db+=vb*vb; }
  return (da&&db) ? num/Math.sqrt(da*db) : 0;
}

function plotForecast(forecast){
  if(!document.getElementById('forecastChart')) return;
  let dates = [];
  let pm25 = [];
  let no2 = [];

  if(forecast && forecast.forecast){
    const f = forecast.forecast;
    if(Array.isArray(f)){
      dates = f.map((d, i)=> d.date || d.day || i);
      pm25 = f.map(d=> +d['PM2.5'] || +d.pm25 || Math.random()*60+20);
      no2 = f.map(d=> +d['NO2'] || +d.no2 || Math.random()*120+40);
    } else if(typeof f === 'object'){
      dates = Object.keys(f);
      pm25 = dates.map(k=> +f[k]['PM2.5'] || +f[k].pm25 || Math.random()*60+20);
      no2 = dates.map(k=> +f[k]['NO2'] || +f[k].no2 || Math.random()*120+40);
    }
  }

  if(dates.length === 0){
    const today = new Date();
    for(let i=0;i<7;i++){
      const d = new Date(today); d.setDate(d.getDate()+i);
      dates.push(d.toISOString().slice(0,10));
      pm25.push(Math.random()*80+20);
      no2.push(Math.random()*150+50);
    }
  }

  const pal = getPalette();
  Plotly.newPlot('forecastChart', [
    {x:dates,y:pm25,name:'PM2.5',mode:'lines+markers',line:{color:pal.series[0], width:3}, marker:{size:6}},
    {x:dates,y:no2,name:'NO2',mode:'lines+markers',line:{color:pal.series[1], width:3}, marker:{size:6}}
  ], plotlyLayout({showlegend:true, yaxis:{title:'Concentration'}}));
}

function plotRiskPie(data){
  if(!document.getElementById('riskPie')) return;
  const counts = {};
  data.forEach(d=>{ const r = (d.risk_level||'unknown'); counts[r]=(counts[r]||0)+1; });
  const labels = Object.keys(counts);
  const values = labels.map(l=>counts[l]);
  const colors = labels.map(l=>colorForRisk(l));
  Plotly.newPlot('riskPie', [{labels, values, type:'pie', marker:{colors}, textinfo:'label+percent'}], plotlyLayout({showlegend:true}));
}

function plotAQIGauge(latest){
  if(!document.getElementById('aqiGauge')) return;
  const pm = +latest['PM2.5']||0; const n2 = +latest['NO2']||0; const risk = riskFromValues(pm,n2);
  const val = Math.max(pm/2.5, n2/2);
  const color = colorForRisk(risk);
  const data=[{type:'indicator',mode:'gauge+number',value:val,
    gauge:{axis:{range:[0,500]},bar:{color}, steps:[
      {range:[0,50],color:'#10b981'},{range:[50,100],color:'#84cc16'},{range:[100,150],color:'#f59e0b'},
      {range:[150,200],color:'#ef4444'},{range:[200,300],color:'#8b5cf6'},{range:[300,500],color:'#7f1d1d'}]},
    number:{font:{color: cssVar('--text') || '#1f2937'}}}];
  Plotly.newPlot('aqiGauge', data, plotlyLayout());
}

function plotMatrix(data){
  if(!document.getElementById('matrixChart')) return;
  const vars = ['PM2.5','NO2','CO','SO2','temperature','humidity','wind_speed'];
  const cols = vars.map(v=>data.map(d=>d[v]));
  const z = vars.map((_,i)=>vars.map((__,j)=>+corr(cols[i], cols[j]).toFixed(2)));
  Plotly.newPlot('matrixChart', [{
    z, x:vars, y:vars, type:'heatmap', colorscale: 'RdBu', reversescale:true,
    showscale:true
  }], plotlyLayout({margin:{t:20,r:20,b:60,l:60}}));
}

function plotBox(data){
  if(!document.getElementById('boxChart')) return;
  const pm = data.map(d=>d['PM2.5']).filter(v=>v!=null);
  const n2 = data.map(d=>d['NO2']).filter(v=>v!=null);
  const co = data.map(d=>d['CO']).filter(v=>v!=null);
  const pal = getPalette();
  Plotly.newPlot('boxChart', [
    {y:pm, type:'box', name:'PM2.5', marker:{color:pal.series[0]}},
    {y:n2, type:'box', name:'NO2', marker:{color:pal.series[1]}},
    {y:co, type:'box', name:'CO', marker:{color:pal.series[2]}}
  ], plotlyLayout({showlegend:true}));
}

function plotRadar(latest){
  if(!document.getElementById('radarChart')) return;
  const axes = ['PM2.5','NO2','CO','SO2'];
  const vals = axes.map(k=>+latest[k]||0);
  const maxes = [150, 200, 2, 40];
  const r = vals.map((v,i)=>Math.max(0, Math.min(100, v/maxes[i]*100)));
  const pal = getPalette();
  Plotly.newPlot('radarChart', [{
    type:'scatterpolar', r:[...r, r[0]], theta:[...axes, axes[0]], fill:'toself', name:'AQ Components',
    line:{color:pal.series[0], width:3}, fillcolor: pal.series[0] + '40'
  }], plotlyLayout({polar:{radialaxis:{visible:true,range:[0,100]}}}));
}

function setLoading(id, on){
  const el = document.getElementById(id);
  if(!el) return;
  let overlay = el.parentElement.querySelector('.loading-overlay');
  if(on){
    if(!overlay){
      overlay = document.createElement('div');
      overlay.className = 'loading-overlay';
      overlay.innerHTML = '<div class="spinner-border text-primary spinner-sm" role="status"></div>';
      el.parentElement.style.position = 'relative';
      el.parentElement.appendChild(overlay);
    }
  } else if(overlay){ overlay.remove(); }
}

function showInsights(city, data, analysis){
  const el = document.getElementById('insightsText');
  if(!el) return;
  if(!data || data.length===0){ el.textContent = 'No data available.'; return; }
  const last7 = data.slice(-7);
  const avg = arr => arr.length? arr.reduce((a,b)=>a+(+b||0),0)/arr.length : 0;
  const pmAvg = avg(last7.map(d=>d['PM2.5']));
  const no2Avg = avg(last7.map(d=>d['NO2']));
  const trend = (last7.at(-1)['PM2.5']||0) - (last7[0]['PM2.5']||0);
  const fires = analysis?.fire_statistics?.total_fires;
  const riskCounts = {};
  last7.forEach(d=>{ const r=d.risk_level||'unknown'; riskCounts[r]=(riskCounts[r]||0)+1; });
  const dominantRisk = Object.entries(riskCounts).sort((a,b)=>b[1]-a[1])[0]?.[0] || 'unknown';
  el.innerHTML = `
    <ul class="mb-0">
      <li><strong>${city}</strong>: Avg PM2.5 ${pmAvg.toFixed(1)} µg/m³, NO2 ${no2Avg.toFixed(1)} ppb (7d)</li>
      <li>Trend: PM2.5 ${trend>=0? 'rising':'falling'} by ${Math.abs(trend).toFixed(1)} over 7 days</li>
      <li>Dominant risk: ${dominantRisk.replace('_',' ')}</li>
      <li>Detected fire hotspots: ${typeof fires==='number'? fires : 'N/A'}</li>
    </ul>`;
}

function initAnalyticsTabs(){
  const tabs = document.getElementById('analyticsTabs');
  if(!tabs) return;
  tabs.addEventListener('click', (e)=>{
    const btn = e.target.closest('[data-chart-target]');
    if(!btn) return;
    tabs.querySelectorAll('.nav-link').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    const target = btn.getAttribute('data-chart-target');
    const panes = {
      '#riskPie':'riskPane', '#matrixChart':'matrixPane', '#radarChart':'radarPane', '#boxChart':'boxPane', '#corrChart':'corrPane'
    };
    Object.values(panes).forEach(id=>document.getElementById(id)?.classList.add('d-none'));
    const paneId = panes[target];
    if(paneId){ document.getElementById(paneId)?.classList.remove('d-none'); }
    const el = document.querySelector(target);
    if(el){ try { Plotly.Plots.resize(el); } catch(_){} }
  });
}

async function refresh(){
  const city = els.citySelect?.value || 'Delhi';
  const chartIds = ['pm25TimeChart','no2TimeChart','forecastChart','riskPie','matrixChart','radarChart','boxChart','corrChart'];
  chartIds.forEach(id=>setLoading(id,true));
  let raw = [];
  try{ raw = await loadCityData(city); } catch(e){ raw = []; }
  const days = parseInt(els.windowDays?.value, 10) || 30;
  const data = raw.slice(-days);

  const [analysis, forecast] = await Promise.all([
    loadAnalysis(city),
    loadForecast(city)
  ]);

  updateKPIs(data, analysis);
  updateGISInfo(data);
  updateMap(data);
  plotPM25Time(data);
  fadeInChart('pm25TimeChart'); setLoading('pm25TimeChart',false);
  plotNO2Time(data);
  fadeInChart('no2TimeChart'); setLoading('no2TimeChart',false);
  plotMiniCharts(data);
  plotCorrelation(data);
  fadeInChart('corrChart'); setLoading('corrChart',false);
  plotForecast(forecast);
  fadeInChart('forecastChart'); setLoading('forecastChart',false);
  plotRiskPie(data);
  fadeInChart('riskPie'); setLoading('riskPie',false);
  if(data.length){
    const latest = data[data.length-1];
    plotAQIGauge(latest);
    plotRadar(latest);
    fadeInChart('radarChart'); setLoading('radarChart',false);
  }
  plotMatrix(data);
  fadeInChart('matrixChart'); setLoading('matrixChart',false);
  plotBox(data);
  fadeInChart('boxChart'); setLoading('boxChart',false);

  showInsights(city, data, analysis);

  if(data.length){
    const latest = data[data.length-1];
    els.kpiTemp.textContent = `${(latest.temperature ?? 26).toFixed(1)}°C`;
    els.kpiHum.textContent = `${(latest.humidity ?? 58).toFixed(0)}%`;
    els.kpiWind.textContent = `${(latest.wind_speed ?? 3.4).toFixed(1)} m/s`;
  } else {
    els.kpiTemp.textContent = `26.0°C`;
    els.kpiHum.textContent = `58%`;
    els.kpiWind.textContent = `3.4 m/s`;
  }

  requestAnimationFrame(resizeAll);
}

function scheduleRefresh(){
  if(refreshTimer) clearInterval(refreshTimer);
  if(els.autoRefresh?.checked){
    refreshTimer = setInterval(refresh, 30_000);
  }
}

function openFullscreen(targetSelector){
  const target = document.querySelector(targetSelector);
  if(!target) return;
  const overlay = document.createElement('div');
  overlay.className = 'fullscreen-overlay';
  overlay.innerHTML = `
    <div class="fullscreen-card">
      <div class="fullscreen-header">
        <div class="fw-bold">Fullscreen</div>
        <div class="d-flex gap-2">
          <button class="btn btn-sm btn-outline-secondary" id="fsRefresh">Refresh</button>
          <button class="btn btn-sm btn-primary" id="fsClose">Close</button>
        </div>
      </div>
      <div class="fullscreen-body">
        <div class="chart-container"></div>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  const container = overlay.querySelector('.chart-container');
  const placeholder = document.createElement('div');
  placeholder.style.height = target.style.height;
  target.parentNode.insertBefore(placeholder, target);
  container.appendChild(target);

  function close(){
    placeholder.parentNode.insertBefore(target, placeholder);
    placeholder.remove();
    overlay.remove();
    resizeAll();
  }
  overlay.querySelector('#fsClose').addEventListener('click', close);
  overlay.addEventListener('click', (e)=>{ if(e.target===overlay) close(); });
  overlay.querySelector('#fsRefresh').addEventListener('click', refresh);
  resizeAll();
}

function bindExpandButtons(){
  document.querySelectorAll('.expand-btn').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const sel = btn.getAttribute('data-target');
      openFullscreen(sel);
    });
  });
}

function toggleSidebar(){
  if(!els.sidebarCol || !els.mainCol) return;
  const hidden = els.sidebarCol.style.display === 'none';
  if(hidden){
    els.sidebarCol.style.display = '';
    els.mainCol.classList.remove('col-12');
    els.mainCol.classList.add('col-12','col-xl-9');
  } else {
    els.sidebarCol.style.display = 'none';
    els.mainCol.classList.remove('col-xl-9');
    els.mainCol.classList.add('col-12');
  }
  setTimeout(resizeAll, 150);
}

function resizeAll(){
  const chartIds = ['pm25TimeChart','no2TimeChart','forecastChart','riskPie','matrixChart','radarChart','boxChart','corrChart','pm25MiniChart','no2MiniChart','aqiGauge'];
  chartIds.forEach(id=>{
    const el = document.getElementById(id);
    if(el && el.children.length){ try { Plotly.Plots.resize(el); } catch(_){} }
  });
  if(map){ setTimeout(()=>{ map.invalidateSize(); }, 50); }
}

async function init(){
  const savedTheme = localStorage.getItem('theme') || 'light';
  const savedPalette = localStorage.getItem('palette') || 'default';
  if(els.themeSelect) els.themeSelect.value = savedTheme;
  if(els.paletteSelect) els.paletteSelect.value = savedPalette;
  applyTheme(savedTheme);
  applyPalette(savedPalette);

  initMap();
  await loadCities();
  if(els.windowDays) els.windowDays.addEventListener('input', ()=>{ els.windowDaysLabel.textContent = els.windowDays.value; });
  if(els.autoRefresh) els.autoRefresh.addEventListener('change', scheduleRefresh);
  if(els.refreshBtn) els.refreshBtn.addEventListener('click', refresh);
  if(els.citySelect) els.citySelect.addEventListener('change', refresh);
  if(els.sidebarToggle) els.sidebarToggle.addEventListener('click', toggleSidebar);
  bindExpandButtons();
  initAnalyticsTabs();

  if(els.themeSelect){ els.themeSelect.addEventListener('change', ()=>{ applyTheme(els.themeSelect.value); refresh(); }); }
  if(els.paletteSelect){ els.paletteSelect.addEventListener('change', ()=>{ applyPalette(els.paletteSelect.value); refresh(); }); }

  const dl = document.getElementById('downloadGeoJSON');
  if(dl){ dl.addEventListener('click', ()=>{ const city = els.citySelect?.value || 'Delhi'; window.open(`${API_BASE}/export/${encodeURIComponent(city)}`, '_blank'); }); }

  await refresh();
  scheduleRefresh();

  window.addEventListener('resize', ()=>{ resizeAll(); });
}

init().catch(err=>console.error(err));