const API_BASE = "http://localhost:5000";

const CITY_CENTERS = {
  'Delhi': [28.6139, 77.2090],
  'Mumbai': [19.0760, 72.8777],
  'Nagpur': [21.1458, 79.0882]
};

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
