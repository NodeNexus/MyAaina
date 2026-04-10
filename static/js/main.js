// Global State
let charts = {};
window.userObj = null;

document.addEventListener('DOMContentLoaded', () => {
  // Init Profile if passed down
  if (typeof userProfileInfo !== 'undefined' && userProfileInfo) {
    window.userObj = userProfileInfo;
    populateProfileForm(userProfileInfo);
    document.getElementById('nav-profile-area').textContent = `👋 Hi, ${userProfileInfo.name.split(' ')[0]}`;
  }
  
  // Attach Slider listener
  document.getElementById('deals-budget-slider').addEventListener('mouseup', () => {
    fetchDeals();
  });
  document.getElementById('deals-budget-slider').addEventListener('touchend', () => {
    fetchDeals();
  });

  // Init Explore
  fetchTrending();
  fetchDeals();
});

// ── NAVIGATION & TABBING ──
function showSection(sectionId) {
  document.querySelectorAll('.section').forEach(sec => {
    sec.classList.remove('active');
    sec.style.animation = 'none';
  });
  
  const activeSec = document.getElementById(sectionId);
  activeSec.classList.add('active');
  // Trigger reflow
  void activeSec.offsetWidth;
  activeSec.style.animation = 'fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards';

  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById(`nav-${sectionId}`);
  if(btn) btn.classList.add('active');

  // Lazy loading hooks
  if(sectionId === 'history') loadHistory();
  if(sectionId === 'wishlist') loadWishlist();
}

function switchTab(tabId) {
  document.querySelectorAll('.explore-tabs .tab-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById(`tab-${tabId}`).classList.add('active');

  document.querySelectorAll('.explore-panel').forEach(p => p.classList.add('hidden'));
  document.getElementById(`explore-${tabId}-panel`).classList.remove('hidden');
}

// ── PROFILE ──
function populateProfileForm(profile) {
  const fields = ['name','age','gender','body_type','skin_tone','size','budget_min','budget_max'];
  fields.forEach(f => {
    if(document.getElementById(f) && profile[f]) {
      document.getElementById(f).value = profile[f];
    }
  });
  
  if (profile.interests) {
    document.querySelectorAll('.check-item input[type="checkbox"]').forEach(cb => {
      cb.checked = profile.interests.includes(cb.value);
    });
  }
}

async function saveProfile(event) {
  event.preventDefault();
  const btn = document.getElementById('save-profile-btn');
  const orgTxt = btn.innerHTML;
  btn.innerHTML = 'Saving... ⏳';
  btn.disabled = true;

  const interests = Array.from(document.querySelectorAll('.check-item input:checked')).map(c => c.value);
  const data = {
    name: document.getElementById('name').value,
    age: document.getElementById('age').value,
    gender: document.getElementById('gender').value,
    body_type: document.getElementById('body_type').value,
    skin_tone: document.getElementById('skin_tone').value,
    size: document.getElementById('size').value,
    budget_min: document.getElementById('budget_min').value,
    budget_max: document.getElementById('budget_max').value,
    interests
  };

  try {
    const res = await fetch('/api/save-profile', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    const d = await res.json();
    const status = document.getElementById('profile-status');
    status.classList.remove('hidden', 'error', 'success');
    
    if (d.success) {
      status.classList.add('success');
      status.innerHTML = `✅ ${d.message}`;
      window.userObj = data;
      document.getElementById('nav-profile-area').textContent = `👋 Hi, ${data.name.split(' ')[0]}`;
      showToast('Profile Saved!', 'success');
      setTimeout(() => showSection('recommend'), 1200);
    } else {
      status.classList.add('error');
      status.innerHTML = `❌ ${d.message}`;
    }
  } catch(e) {
    console.error(e);
  } finally {
    btn.innerHTML = orgTxt;
    btn.disabled = false;
  }
}

// ── EXPLORE (SEARCH, TRENDING, DEALS) ──
async function doSearch() {
  const q = document.getElementById('search-input').value.trim();
  if(!q) return;
  switchTab('search');
  document.getElementById('search-no-results').classList.add('hidden');
  document.getElementById('search-results-grid').innerHTML = '<p>Searching...</p>';

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const d = await res.json();
    if (d.success && d.results.length > 0) {
      document.getElementById('search-results-grid').innerHTML = generateCardGrid(d.results, false);
    } else {
      document.getElementById('search-results-grid').innerHTML = '';
      document.getElementById('search-no-results').classList.remove('hidden');
    }
  } catch(e) { console.error(e); }
}

async function fetchTrending() {
  try {
    const res = await fetch('/api/trending');
    const d = await res.json();
    if(d.success) document.getElementById('trending-grid').innerHTML = generateCardGrid(d.results, false);
  } catch(e) {}
}

function updateDealsBudget(val) {
  document.getElementById('deals-budget-label').textContent = `₹${val}`;
}

async function fetchDeals() {
  const b = document.getElementById('deals-budget-slider').value;
  try {
    const res = await fetch(`/api/deals?budget=${b}`);
    const d = await res.json();
    if(d.success) document.getElementById('deals-grid').innerHTML = generateCardGrid(d.results, false);
  } catch(e) {}
}

// ── RECOMMEND ──
async function getRecommendations() {
  const occasion = document.getElementById('occasion').value;
  const sortBy = document.getElementById('sort_by').value;

  if(!occasion) {
    showToast('Please select an occasion.', 'error');
    return;
  }
  
  if(!window.userObj) {
    showToast('Please complete your profile first!', 'error');
    showSection('home');
    return;
  }

  const btn = document.getElementById('find-btn');
  const orgTxt = btn.innerHTML;
  btn.innerHTML = 'Searching AI... ⏳';
  btn.disabled = true;

  try {
    const res = await fetch('/api/recommend', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ occasion, sort_by: sortBy })
    });
    const d = await res.json();
    
    const sec = document.getElementById('results-section');
    const none = document.getElementById('no-results');
    const chrt = document.getElementById('charts-section');

    if(d.success) {
      if(d.results.length === 0) {
        sec.classList.add('hidden'); chrt.classList.add('hidden'); none.classList.remove('hidden');
      } else {
        none.classList.add('hidden'); sec.classList.remove('hidden'); chrt.classList.remove('hidden');
        document.getElementById('results-title').textContent = `✨ ${d.results.length} Matches for ${d.user}'s ${occasion}`;
        document.getElementById('results-grid').innerHTML = generateCardGrid(d.results, true);
        renderDecisionCharts(d.price_chart, d.quality_chart, d.delivery_chart);
        // Scroll to results seamlessly
        setTimeout(()=> chrt.scrollIntoView({behavior:'smooth'}), 100);
      }
    } else {
      showToast(d.message, 'error');
    }
  } catch(e) { console.error(e); } finally {
    btn.innerHTML = orgTxt;
    btn.disabled = false;
  }
}

function renderDecisionCharts(pData, qData, dData) {
  if(charts.pc) charts.pc.destroy();
  if(charts.qc) charts.qc.destroy();
  if(charts.dc) charts.dc.destroy();

  const getCtx = id => document.getElementById(id).getContext('2d');
  const sharedOpt = { responsive: true, plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#aaa' } }, x: { ticks: { color: '#aaa' } } } };

  charts.pc = new Chart(getCtx('priceChart'), {
    type: 'bar',
    data: { labels: Object.keys(pData), datasets: [{ data: Object.values(pData), backgroundColor: 'rgba(0, 212, 255, 0.6)', borderColor: '#00d4ff', borderWidth: 1, borderRadius: 8 }] },
    options: sharedOpt
  });

  charts.qc = new Chart(getCtx('qualityChart'), {
    type: 'line',
    data: { labels: Object.keys(qData), datasets: [{ data: Object.values(qData), borderColor: '#ff7bff', backgroundColor: 'rgba(255, 123, 255, 0.2)', borderWidth: 3, pointBackgroundColor: '#fff', fill: true, tension: 0.4 }] },
    options: { ...sharedOpt, scales: { ...sharedOpt.scales, y: { ...sharedOpt.scales.y, min: 2, max: 5 } } }
  });

  charts.dc = new Chart(getCtx('deliveryChart'), {
    type: 'bar',
    data: { labels: Object.keys(dData), datasets: [{ data: Object.values(dData), backgroundColor: 'rgba(80, 250, 123, 0.6)', borderColor: '#50fa7b', borderWidth: 1, borderRadius: 8 }] },
    options: sharedOpt
  });
}

// ── UTILS & HTML GEN ──
function getImgSrc(item) {
  const kw = item.image_keyword ? item.image_keyword.replace(/\s/g, ',') : 'indian,clothing';
  // Standard Unsplash source is dead, so using picsum with stable seeds based on ID
  // It gives deterministic stunning abstract photography. We overlay text so it feels premium.
  return `https://picsum.photos/seed/${item.id * 1024}/500/700`; 
}

function renderStars(rating) {
  const f = Math.floor(rating), h = rating % 1 >= 0.5 ? 1 : 0, e = 5 - f - h;
  return '⭐'.repeat(f) + (h ? '✨' : '') + '☆'.repeat(e);
}

function generateCardGrid(items, showScore = false) {
  // Store items in global for modal reference
  window.catalogData = window.catalogData || {};
  items.forEach(i => window.catalogData[i.id] = i);

  return items.map((item, idx) => `
    <div class="product-card" style="animation: fadeInUp 0.4s ease forwards; animation-delay: ${idx * 0.05}s; opacity:0;">
      
      <button class="wishlist-btn ${item.in_wishlist?'active':''}" onclick="toggleWishlist(${item.id}, this)">
        ${item.in_wishlist?'❤️':'🤍'}
      </button>

      <div class="img-container" onclick="openModal(${item.id})">
        <img src="${getImgSrc(item)}" class="product-img" loading="lazy" alt="${item.name}"/>
        <span class="platform-badge">${item.platform}</span>
      </div>

      <div class="product-name" title="${item.name}">${item.name}</div>
      <div class="product-cat">${item.category} · ${item.color}</div>

      <div class="product-meta">
        <div class="meta-row">
          <span class="meta-label">Price</span>
          <span class="meta-value price-value">₹${item.price.toLocaleString('en-IN')}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">Rating</span>
          <span class="meta-value" style="color:#ffb86c;">${item.quality_rating} ★</span>
        </div>
      </div>

      <button class="btn-buy" id="buy-btn-${item.id}" onclick="logPurchase(${item.id})">
        🛍️ Buy / Add to Wardrobe
      </button>
    </div>
  `).join('');
}

// ── ACTIONS ──
async function toggleWishlist(id, btnElement) {
  try {
    const res = await fetch('/api/wishlist/toggle', {
      method: 'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({item_id: id})
    });
    const d = await res.json();
    if(d.success) {
      showToast(d.message, d.added ? 'success' : '');
      if(d.added) {
        btnElement.classList.add('active');
        btnElement.innerHTML = '❤️';
      } else {
        btnElement.classList.remove('active');
        btnElement.innerHTML = '🤍';
        // If we are in wishlist view, reload
        if(document.getElementById('wishlist').classList.contains('active')) loadWishlist();
      }
    }
  } catch(e) {}
}

async function logPurchase(id) {
  try {
    const res = await fetch('/api/log-purchase', {
      method: 'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({item_id: id})
    });
    const d = await res.json();
    if(d.success) {
      showToast('Logged to Wardrobe! 👗', 'success');
      const b = document.getElementById(`buy-btn-${id}`);
      if(b) {
        b.innerHTML = '✅ Owned';
        b.style.background = 'var(--accent)';
        b.style.color = '#000';
        b.style.borderColor = 'var(--accent)';
        b.disabled = true;
      }
    }
  } catch(e){}
}

// ── WISHLIST VIEW ──
async function loadWishlist() {
  document.getElementById('wishlist-grid').innerHTML = '';
  try {
    const res = await fetch('/api/wishlist');
    const d = await res.json();
    if(d.success) {
      if(d.items.length===0){
        document.getElementById('no-wishlist').classList.remove('hidden');
        document.getElementById('wishlist-grid').classList.add('hidden');
      } else {
        document.getElementById('no-wishlist').classList.add('hidden');
        document.getElementById('wishlist-grid').classList.remove('hidden');
        document.getElementById('wishlist-grid').innerHTML = generateCardGrid(d.items);
      }
    }
  } catch(e){}
}

// ── HISTORY VIEW ──
async function loadHistory() {
  try {
    const res = await fetch('/api/history');
    const d = await res.json();

    const none = document.getElementById('no-history');
    const grid = document.getElementById('history-grid');
    const chartsRow = document.getElementById('history-charts-row');
    const kpiRow = document.getElementById('kpi-row');

    if(!d.items || d.items.length === 0) {
      none.classList.remove('hidden');
      grid.innerHTML = '';
      chartsRow.classList.add('hidden');
      kpiRow.classList.add('hidden');
      document.getElementById('wardrobe-label').classList.add('hidden');
      return;
    }

    none.classList.add('hidden');
    chartsRow.classList.remove('hidden');
    kpiRow.classList.remove('hidden');
    document.getElementById('wardrobe-label').classList.remove('hidden');
    document.getElementById('wardrobe-label').innerHTML = `All Past Purchases (${d.total_items})`;

    // Update KPIs
    document.getElementById('kpi-total-items').innerText = d.total_items;
    document.getElementById('kpi-total-spend').innerText = `₹${d.total_spend.toLocaleString('en-IN')}`;
    
    const avgQ = d.items.reduce((s,i)=> s+parseFloat(i.quality_rating), 0)/d.items.length;
    document.getElementById('kpi-avg-quality').innerText = avgQ.toFixed(1);

    const tops = Object.entries(d.platform_spend).sort((a,b)=>b[1]-a[1]);
    document.getElementById('kpi-fav-platform').innerText = tops.length ? tops[0][0] : '—';

    // Render Grid
    grid.innerHTML = d.items.map((item, idx) => `
      <div class="product-card" style="animation-delay:${idx*0.05}s">
        <div class="img-container" onclick="openModal(${item.id})">
          <img src="${getImgSrc(item)}" class="product-img" loading="lazy" />
          <span class="platform-badge" style="background:var(--accent); color:#000;">Purchased</span>
        </div>
        <div class="product-name">${item.name}</div>
        <div class="meta-row mt-2" style="background: rgba(80,250,123,0.1); border: 1px solid rgba(80,250,123,0.2); padding: 10px; border-radius:8px;">
          <span class="meta-label" style="color:var(--accent)">Paid</span>
          <span class="meta-value price-value">₹${item.price.toLocaleString('en-IN')}</span>
        </div>
      </div>
    `).join('');

    renderHistoryCharts(d.stats, d.platform_spend);

  } catch(e) { console.error(e); }
}

function renderHistoryCharts(stats, platformStats) {
  if(charts.hc) charts.hc.destroy();
  if(charts.psc) charts.psc.destroy();
  
  const ctxHC = document.getElementById('historyChart').getContext('2d');
  const ctxPSC = document.getElementById('platformSpendChart').getContext('2d');
  const colors = ['#ff7bff', '#00d4ff', '#50fa7b', '#f1fa8c', '#ff5555', '#bd93f9', '#ffb86c'];

  charts.hc = new Chart(ctxHC, {
    type: 'doughnut',
    data: { labels: Object.keys(stats), datasets: [{ data: Object.values(stats), backgroundColor: colors, borderWidth: 0 }] },
    options: { responsive: true, plugins: { legend: { position: 'right', labels:{color:'#fff'} } }, cutout: '75%' }
  });

  charts.psc = new Chart(ctxPSC, {
    type: 'pie',
    data: { labels: Object.keys(platformStats), datasets: [{ data: Object.values(platformStats), backgroundColor: colors.slice().reverse(), borderWidth: 0 }] },
    options: { responsive: true, plugins: { legend: { position: 'right', labels:{color:'#fff'} } } }
  });
}

// ── MODAL ──
function openModal(itemId) {
  const item = window.catalogData[itemId];
  if(!item) return;

  const content = `
    <div class="modal-body">
      <div class="modal-img-col">
        <img src="${getImgSrc(item)}" class="modal-img" />
        <button class="wishlist-btn ${item.in_wishlist?'active':''}" style="width:50px;height:50px;font-size:1.5rem;" onclick="toggleWishlist(${item.id}, this); event.stopPropagation();">
          ${item.in_wishlist?'❤️':'🤍'}
        </button>
      </div>
      <div class="modal-info-col">
        <div class="modal-platform">via ${item.platform}</div>
        <h2 class="modal-title">${item.name}</h2>
        <div class="modal-desc">${item.description || 'A beautiful traditional piece for your wardrobe.'}</div>
        
        <div class="modal-metrics">
          <div class="metric">
            <span class="metric-label">Price</span>
            <span class="metric-val price">₹${item.price.toLocaleString('en-IN')}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Quality Score</span>
            <span class="metric-val">${item.quality_rating} / 5.0</span>
          </div>
          <div class="metric">
            <span class="metric-label">Delivery Est.</span>
            <span class="metric-val">${item.delivery_days} Days</span>
          </div>
          <div class="metric">
            <span class="metric-label">Size Availability</span>
            <span class="metric-val">${item.size}</span>
          </div>
        </div>

        <button class="btn-primary" style="margin-top:0;" onclick="logPurchase(${item.id}); closeModal(event);">
          Buy Now &amp; Log Purchase
        </button>
      </div>
    </div>
  `;
  document.getElementById('modal-content').innerHTML = content;
  document.getElementById('product-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden'; // stop background scroll
}

function closeModal(e) {
  if (e && e.target !== document.getElementById('product-modal') && !e.target.closest('.modal-close')) {
    // Only close if clicking overlay or close btn
    if(!e.target.classList.contains('modal-overlay')) return;
  }
  document.getElementById('product-modal').classList.add('hidden');
  document.body.style.overflow = '';
}

// ── TOAST ──
function showToast(msg, type='success') {
  const toast = document.getElementById('toast');
  toast.innerText = msg;
  toast.className = 'toast ' + (type === 'error' ? 'toast-error' : '');
  toast.classList.remove('hidden');
  
  setTimeout(() => toast.classList.add('hidden'), 3500);
}
