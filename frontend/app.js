import { API_BASE, CITY_CENTERS, applyTheme, applyPalette, colorForRisk, getPalette, plotlyLayout, riskFromValues, cssVar } from './js/config.js';
import { loadCities, loadCityData, loadForecast, loadAnalysis } from './js/api.js';
import { initMap, updateMap } from './js/map.js';
import { setLoading, fadeInChart, updateKPIs, updateGISInfo, showInsights, initAnalyticsTabs, resizeAll, scheduleRefresh, openFullscreen, bindExpandButtons, toggleSidebar } from './js/ui.js';
import { plotPM25Time, plotNO2Time, plotMiniCharts, plotCorrelation, plotForecast, plotRiskPie, plotAQIGauge, plotMatrix, plotBox, plotRadar, corr } from './js/charts.js';

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
