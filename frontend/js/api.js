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
