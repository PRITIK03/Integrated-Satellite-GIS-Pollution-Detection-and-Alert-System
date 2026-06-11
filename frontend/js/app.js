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
