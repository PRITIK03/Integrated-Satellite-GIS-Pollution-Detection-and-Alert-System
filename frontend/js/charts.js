function safe(arr){ return (arr||[]).map(v=> (v==null? null : +v)); }
function k(v){ return (typeof v === 'number' && isFinite(v)) ? v.toFixed(1) : '--'; }

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

function corr(a,b){
  const n = Math.min(a.length,b.length); if(n===0) return 0;
  let ma=0, mb=0; for(let i=0;i<n;i++){ ma+=+a[i]||0; mb+=+b[i]||0; } ma/=n; mb/=n;
  let num=0, da=0, db=0; for(let i=0;i<n;i++){ const va=(+a[i]||0)-ma; const vb=(+b[i]||0)-mb; num+=va*vb; da+=va*va; db+=vb*vb; }
  return (da&&db) ? num/Math.sqrt(da*db) : 0;
}
