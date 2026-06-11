import { CITY_CENTERS } from './js/config.js';

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
