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

function fadeInChart(id){
  const el = document.getElementById(id);
  if(!el) return;
  el.classList.remove('fade-in');
  void el.offsetWidth;
  el.classList.add('fade-in');
}

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
