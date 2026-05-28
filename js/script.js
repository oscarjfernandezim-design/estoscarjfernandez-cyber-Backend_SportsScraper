const STORES = [
  { id: 's1', name: 'Zalando', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Zalando_logo.svg/2560px-Zalando_logo.svg.png' },
  { id: 's2', name: 'ASOS', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Asos_logo.svg/2560px-Asos_logo.svg.png' },
  { id: 's3', name: 'Adidas Official', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Adidas_Logo.svg/2560px-Adidas_Logo.svg.png' },
  { id: 's4', name: 'Nike Store', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Logo_NIKE.svg/1200px-Logo_NIKE.svg.png' },
  { id: 's5', name: 'Decathlon', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Decathlon_Logo.svg/2560px-Decathlon_Logo.svg.png' },
];

let apiLimit = 1000;
let apiOffset = 0;
let PRODUCTS = [];
// If page is opened from file://, backend isn't same-origin — fallback to localhost server
const API_BASE = (location.protocol === 'file:') ? 'http://127.0.0.1:3000' : '';

async function fetchProductsFromApi(limit = 100, offset = 0) {
  try {
    const res = await fetch(`${API_BASE}/api/products/?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}`, { cache: 'no-store' });
    if (!res.ok) throw new Error('no api');
    const list = await res.json();
    if (!Array.isArray(list)) throw new Error('bad');

    console.log('[script] fetchProductsFromApi: received', list.length, 'items');

    // Map backend products to frontend product shape used in script.js
    PRODUCTS = list.map(p => ({
      id: p.id,
      name: p.product_name,
      brand: p.brand,
      category: p.category || 'General',
      image: p.image_url || 'https://via.placeholder.com/600x600?text=SportsScraper',
      description: p.product_name,
      basePrice: p.latest_price ? parseFloat(p.latest_price) : 0,
      priceHistory: []
    }));
    window.PRODUCTS = PRODUCTS;

    console.log('[script] PRODUCTS mapped, length=', PRODUCTS.length);

    // Clear OFFERS since we don't have per-store offers yet
    OFFERS = [];
    window.OFFERS = OFFERS;
    // Update statistics numbers
    document.getElementById('stat-products').textContent = new Intl.NumberFormat('es-ES').format(PRODUCTS.length);
    return true;
  } catch (e) {
    // API not available or failed — continue using local mocks
    console.warn('[script] fetchProductsFromApi failed:', e);
    return false;
  }
}

// Simulado de ofertas de tiendas para cada producto (en un caso real, esto vendría de una API o base de datos)
let OFFERS = [
  { id: 'o1', productId: 'p1', storeId: 's1', price: 124.99, currency: 'EUR', url: 'https://www.zalando.es/nike-zapatillas-running/', stock: true, lastUpdated: new Date().toISOString() },
  { id: 'o2', productId: 'p1', storeId: 's2', price: 119.50, currency: 'EUR', url: 'https://www.asos.com/nike-running-shoes/', stock: true, lastUpdated: new Date().toISOString() },
  { id: 'o3', productId: 'p1', storeId: 's4', price: 129.99, currency: 'EUR', url: 'https://www.nike.com/es/zapatillas-running-hombre/', stock: true, lastUpdated: new Date().toISOString() },
  { id: 'o4', productId: 'p2', storeId: 's1', price: 185.00, currency: 'EUR', url: 'https://www.zalando.es/adidas-ultraboost/', stock: true, lastUpdated: new Date().toISOString() },
  { id: 'o5', productId: 'p2', storeId: 's3', price: 190.00, currency: 'EUR', url: 'https://www.adidas.es/zapatillas-ultraboost/', stock: true, lastUpdated: new Date().toISOString() },
  { id: 'o6', productId: 'p2', storeId: 's5', price: 179.99, currency: 'EUR', url: 'https://www.decathlon.es/adidas-zapatillas-running/', stock: false, lastUpdated: new Date().toISOString() },
  { id: 'o7', productId: 'p3', storeId: 's1', price: 105.00, currency: 'EUR', url: 'https://www.zalando.es/puma-zapatillas/', stock: true, lastUpdated: new Date().toISOString() },
  { id: 'o8', productId: 'p3', storeId: 's2', price: 110.00, currency: 'EUR', url: 'https://www.asos.com/puma-shoes/', stock: true, lastUpdated: new Date().toISOString() },
];
window.OFFERS = OFFERS;

let currentSearch = '';
let currentSort = 'featured';
let currentCategory = '';
let currentMaxPrice = Infinity;

// ========================================
// INITIALIZATION
// ========================================

// Trigger scraping on first load if products are empty
async function triggerScrapingIfNeeded() {
  if (PRODUCTS.length === 0) {
    console.log('[script] No products found, triggering scraper...');
    try {
      const res = await fetch(`${API_BASE}/api/scraper/run`, { 
        method: 'POST',
        cache: 'no-store'
      });
      if (res.ok) {
        const data = await res.json();
        console.log('[script] Scraper finished:', data);
        // Reload products
        await fetchProductsFromApi();
      }
    } catch (e) {
      console.warn('[script] Scraper trigger failed:', e);
    }
  }
}

function init() {
  if (typeof loadAndRender === 'function') {
    loadAndRender();
  } else {
    renderProducts(PRODUCTS);
  }
  setupSearchListeners();
  setupSortAndFilterListeners();
  updateStatistics();
  setupModalListeners();
  initializeAlerts();
  setupAlertListeners();
}

// ========================================
// STATISTICS UPDATE
// ========================================
function updateStatistics() {
  const totalProducts = PRODUCTS.length;
  const totalStores = STORES.length;
  const totalOffers = OFFERS.length;

  document.getElementById('stat-products').textContent = new Intl.NumberFormat('es-ES').format(totalProducts);
  document.getElementById('stat-stores').textContent = new Intl.NumberFormat('es-ES').format(totalStores);
  document.getElementById('stat-offers').textContent = new Intl.NumberFormat('es-ES').format(totalOffers);
}

// ========================================
// SEARCH FUNCTIONALITY (CU1)
// ========================================
function setupSearchListeners() {
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.querySelector('.search-btn');

  // Search on input (with debounce)
  let searchTimeout;
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    clearTimeout(searchTimeout);

    // Show suggestions while typing
    if (query.length > 0) {
      showSuggestions(query);
      searchTimeout = setTimeout(() => {
        performSearch(query);
      }, 300);
    } else {
      hideSuggestions();
      performSearch('');
    }
  });

  // Search on button click
  searchBtn.addEventListener('click', () => {
    hideSuggestions();
    performSearch(searchInput.value);
  });

  // Search on Enter key
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      hideSuggestions();
      performSearch(searchInput.value);
    }
  });

  // Close suggestions when clicking outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-bar-wrapper')) {
      hideSuggestions();
    }
  });
}

// ========================================
// SORT AND FILTER FUNCTIONALITY
// ========================================
function setupSortAndFilterListeners() {
  // Populate categories dropdown
  const categoriesDropdown = document.getElementById('categoriesDropdown');
  const categories = ['TODOS', ...new Set(PRODUCTS.map(p => p.category))];
  categoriesDropdown.innerHTML = categories.map(cat =>
    `<div class="dropdown-item" data-category="${cat === 'TODOS' ? '' : cat}">${cat}</div>`
  ).join('');

  // Category filter
  categoriesDropdown.querySelectorAll('.dropdown-item').forEach(item => {
    item.addEventListener('click', () => {
      currentCategory = item.dataset.category;
      applyFilterAndSort();
      updateResetButton();
      // Uncheck checkbox to close dropdown
      document.getElementById('categoriesToggle').checked = false;
    });
  });

  // Sort dropdown items
  const sortDropdown = document.getElementById('sortDropdown');
  sortDropdown.querySelectorAll('.dropdown-item').forEach(item => {
    item.addEventListener('click', () => {
      currentSort = item.dataset.sort;
      applyFilterAndSort();
      // Uncheck checkbox to close dropdown
      document.getElementById('sortToggle').checked = false;
    });
  });

  // Price filter
  const priceFilter = document.getElementById('priceFilter');
  priceFilter.addEventListener('change', (e) => {
    currentMaxPrice = e.target.value ? parseFloat(e.target.value) : Infinity;
    applyFilterAndSort();
    updateResetButton();
  });

  // Reset filters button
  const resetBtn = document.getElementById('resetFiltersBtn');
  resetBtn.addEventListener('click', () => {
    currentCategory = '';
    currentMaxPrice = Infinity;
    currentSort = 'featured';
    currentSearch = '';

    document.getElementById('searchInput').value = '';
    document.getElementById('priceFilter').value = '';
    document.getElementById('categoriesToggle').checked = false;
    document.getElementById('sortToggle').checked = false;

    applyFilterAndSort();
    updateResetButton();
  });
}

function updateResetButton() {
  const resetBtn = document.getElementById('resetFiltersBtn');
  const hasFilters = currentCategory || currentMaxPrice !== Infinity || currentSearch;
  resetBtn.style.display = hasFilters ? 'flex' : 'none';
}

function applyFilterAndSort() {
  let filtered = PRODUCTS.filter(product => {
    // Filter by search
    const matchesSearch = !currentSearch ||
      product.name.toLowerCase().includes(currentSearch) ||
      product.brand.toLowerCase().includes(currentSearch) ||
      product.category.toLowerCase().includes(currentSearch);

    // Filter by category
    const matchesCategory = !currentCategory || product.category === currentCategory;

    // Filter by price
    const bestOffer = OFFERS.filter(o => o.productId === product.id).sort((a, b) => a.price - b.price)[0];
    const price = bestOffer ? bestOffer.price : product.basePrice;
    const matchesPrice = price <= currentMaxPrice;

    return matchesSearch && matchesCategory && matchesPrice;
  });

  // Apply sorting
  switch(currentSort) {
    case 'price-low':
      filtered.sort((a, b) => {
        const aOffer = OFFERS.filter(o => o.productId === a.id).sort((x, y) => x.price - y.price)[0];
        const bOffer = OFFERS.filter(o => o.productId === b.id).sort((x, y) => x.price - y.price)[0];
        const aPrice = aOffer ? aOffer.price : a.basePrice;
        const bPrice = bOffer ? bOffer.price : b.basePrice;
        return aPrice - bPrice;
      });
      break;
    case 'price-high':
      filtered.sort((a, b) => {
        const aOffer = OFFERS.filter(o => o.productId === a.id).sort((x, y) => x.price - y.price)[0];
        const bOffer = OFFERS.filter(o => o.productId === b.id).sort((x, y) => x.price - y.price)[0];
        const aPrice = aOffer ? aOffer.price : a.basePrice;
        const bPrice = bOffer ? bOffer.price : b.basePrice;
        return bPrice - aPrice;
      });
      break;
    case 'newest':
      // Reverse order for newest
      filtered.reverse();
      break;
    case 'featured':
    default:
      // Keep original order for featured
      break;
  }

  renderProducts(filtered);
}

function showSuggestions(query) {
  const lowerQuery = query.toLowerCase();

  // Filter products by name, brand, or category
  const matches = PRODUCTS.filter(product => {
    const name = product.name.toLowerCase();
    const brand = product.brand.toLowerCase();
    const category = product.category.toLowerCase();

    return name.includes(lowerQuery) ||
           brand.includes(lowerQuery) ||
           category.includes(lowerQuery);
  }).slice(0, 8); // Show max 8 suggestions

  const suggestionsEl = document.getElementById('search-suggestions');
  const suggestionsContent = suggestionsEl.querySelector('.suggestions-content');

  if (matches.length > 0) {
    suggestionsContent.innerHTML = matches.map(product => `
      <div class="suggestion-item" data-product-id="${product.id}">
        <div style="font-weight: bold;">${product.name}</div>
        <div style="color: #666; font-size: 0.75rem;">${product.brand} • ${product.category}</div>
      </div>
    `).join('');

    // Add click handlers
    suggestionsContent.querySelectorAll('.suggestion-item').forEach(item => {
      item.addEventListener('click', () => {
        const productId = item.dataset.productId;
        const product = PRODUCTS.find(p => p.id === productId);
        document.getElementById('searchInput').value = product.name;
        hideSuggestions();
        performSearch(product.name);
      });
    });

    suggestionsEl.classList.add('active');
  } else {
    suggestionsContent.innerHTML = `
      <div class="suggestion-count">
        No se encontraron coincidencias para "${query}"
      </div>
    `;
    suggestionsEl.classList.add('active');
  }
}

function hideSuggestions() {
  const suggestionsEl = document.getElementById('search-suggestions');
  suggestionsEl.classList.remove('active');
}

function performSearch(query) {
  currentSearch = query.trim().toLowerCase();

  if (!currentSearch) {
    // Show all products if search is empty
    applyFilterAndSort();
    hideSearchStatus();
    hideEmptyState();
    return;
  }

  applyFilterAndSort();
}

function showSearchStatus(text) {
  const statusEl = document.getElementById('search-status');
  const statusText = document.getElementById('search-status-text');
  statusText.textContent = text;
  statusEl.style.display = 'block';
}

function hideSearchStatus() {
  const statusEl = document.getElementById('search-status');
  statusEl.style.display = 'none';
}

function showEmptyState() {
  const emptyState = document.getElementById('empty-state');
  const productGrid = document.getElementById('product-grid');
  productGrid.style.display = 'none';
  emptyState.style.display = 'flex';
}

function hideEmptyState() {
  const emptyState = document.getElementById('empty-state');
  const productGrid = document.getElementById('product-grid');
  emptyState.style.display = 'none';
  productGrid.style.display = 'grid';
}

// ========================================
// PRODUCT RENDERING
// ========================================
function renderProducts(productsToRender) {
  const grid = document.getElementById('product-grid');
  grid.innerHTML = '';

  productsToRender.forEach((product, index) => {
    const card = document.createElement('div');
    card.className = 'brutal-card';
    card.style.animationDelay = `${index * 0.05}s`;
    card.addEventListener('click', () => {
      openPriceModal(product.id);
    });

    const bestOffer = OFFERS.filter(o => o.productId === product.id).sort((a, b) => a.price - b.price)[0];
    const priceDisplay = bestOffer ? `${bestOffer.price} ${bestOffer.currency}` : `${product.basePrice} EUR`;

    // Calcular descuento aproximado
    let discountBadge = '';
    if (bestOffer && bestOffer.price < product.basePrice * 0.9) {
      const discount = Math.round(((product.basePrice - bestOffer.price) / product.basePrice) * 100);
      discountBadge = `<span class="card-badge">-${discount}% OFF</span>`;
    }

    card.innerHTML = `
      ${discountBadge}
      <img src="${product.image}" alt="${product.name}" referrerPolicy="no-referrer">
      <div class="neon-badge">${product.brand}</div>
      <h3>${product.name}</h3>
      <p>${product.category}</p>
      <div class="brutal-card-footer">
        <span class="brutal-card-price">${priceDisplay}</span>
        <button class="brutal-card-btn" aria-label="Comparar precios" title="Comparar precios">
          <i class="material-icons" style="font-size: 1rem;">arrow_forward</i>
        </button>
      </div>
    `;
    grid.appendChild(card);
  });

  // Show/hide empty state
  if (productsToRender.length === 0) {
    showEmptyState();
  } else {
    hideEmptyState();
  }
}

// ========================================
// PRICE COMPARISON MODAL (CU2)
// ========================================
function openPriceModal(productId) {
  const product = PRODUCTS.find(p => p.id === productId);
  if (!product) return;

  // Actualizar encabezado
  document.getElementById('modalProductName').textContent = product.name;
  document.getElementById('modalProductImage').src = product.image;
  document.getElementById('modalProductDescription').textContent = product.description;

  // Badge de precio mínimo histórico
  const allOffers = OFFERS.filter(o => o.productId === productId);
  const lowestPrice = allOffers.length > 0
    ? Math.min(...allOffers.map(o => o.price))
    : product.basePrice;

  const badge = document.getElementById('modalLowestPrice');
  if (lowestPrice < 120) {
    badge.textContent = '¡PRECIO MÍNIMO HISTÓRICO!';
    badge.style.display = 'inline-block';
  } else {
    badge.style.display = 'none';
  }

  // Renderizar detalles del producto
  renderProductDetails(product);

  // Renderizar ofertas
  renderOffers(productId);

  // Renderizar histórico de precios
  // Try API first
  try {
    fetch(`${API_BASE}/api/products/${productId}/prices`).then(r => {
      if (!r.ok) {
        renderPriceHistory(productId);
        return;
      }
      r.json().then(payload => {
        const history = payload.history || [];
        renderPriceHistoryFromApi(history);
      }).catch(() => renderPriceHistory(productId));
    }).catch(() => renderPriceHistory(productId));
    // Also try to fetch offers (product_url will be provided by backend)
    try {
      fetch(`${API_BASE}/api/products/${productId}/offers`).then(r => {
        if (!r.ok) {
          // fallback to local/offers rendering
          renderOffers(productId);
          return;
        }
        r.json().then(payload => {
          const offers = payload.offers || [];
          renderOffersFromApi(offers);
        }).catch(() => renderOffers(productId));
      }).catch(() => renderOffers(productId));
    } catch (e) {
      renderOffers(productId);
    }
  } catch (e) {
    renderPriceHistory(productId);
  }

  // Renderizar alertas de precio (CU3)
  renderAlertForm(productId);
  renderActiveAlerts(productId);
  checkPriceAlerts(productId);

  // Abrir modal
  document.getElementById('priceModal').style.display = 'flex';
}

function renderProductDetails(product) {
  const detailsContainer = document.getElementById('productDetailsContent');
  detailsContainer.innerHTML = '';

  const details = [
    { label: 'MARCA', value: product.brand },
    { label: 'CATEGORÍA', value: product.category },
    { label: 'PRECIO BASE', value: `${new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(product.basePrice)}` },
  ];

  details.forEach(detail => {
    const item = document.createElement('div');
    item.className = 'detail-item';
    item.innerHTML = `
      <span class="detail-label">${detail.label}</span>
      <span class="detail-value">${detail.value}</span>
    `;
    detailsContainer.appendChild(item);
  });
}

function closePriceModal() {
  document.getElementById('priceModal').style.display = 'none';
  document.getElementById('offersContainer').innerHTML = '';
  if (priceModal) {
    priceModal.destroy();
    priceModal = null;
  }
}

let priceModal = null;

function renderOffers(productId) {
  const offers = OFFERS.filter(o => o.productId === productId)
    .sort((a, b) => a.price - b.price); // Ordenamiento CU2

  const container = document.getElementById('offersContainer');
  container.innerHTML = '';

  if (offers.length === 0) {
    container.innerHTML = '<p style="text-align: center; color: #999;">No hay ofertas disponibles para este producto</p>';
    return;
  }

  offers.forEach(offer => {
    const store = STORES.find(s => s.id === offer.storeId);
    const stockText = offer.stock ? 'En Stock' : 'Sin Stock';
    const updatedText = formatDate(offer.lastUpdated);

    const row = document.createElement('div');
    row.className = 'offer-row';
    row.innerHTML = `
      <img src="${store.logo}" alt="${store.name}" class="offer-logo" referrerPolicy="no-referrer">
      <div class="offer-info">
        <span class="offer-store">${store.name}</span>
        <span class="offer-price">${new Intl.NumberFormat('es-ES', { style: 'currency', currency: offer.currency }).format(offer.price)}</span>
        <span class="offer-stock">${stockText}</span>
        <span class="offer-updated">Actualizado: ${updatedText}</span>
      </div>
      <button class="compare-btn" data-url="${offer.url}">
        COMPARAR PRECIOS
      </button>
    `;

    row.querySelector('.compare-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      const url = e.target.getAttribute('data-url');
      if (url && url !== '#') {
        window.open(url, '_blank');
      }
    });

    container.appendChild(row);
  });
}

// Render offers returned by API (array of {store_name, price, product_url, scraped_at})
function renderOffersFromApi(offers) {
  const container = document.getElementById('offersContainer');
  container.innerHTML = '';
  if (!offers || offers.length === 0) {
    container.innerHTML = '<p style="text-align: center; color: #999;">No hay ofertas disponibles para este producto</p>';
    return;
  }

  offers.sort((a, b) => parseFloat(a.price) - parseFloat(b.price));
  offers.forEach(offer => {
    const row = document.createElement('div');
    row.className = 'offer-row';
    const updatedText = formatDate(offer.scraped_at);
    row.innerHTML = `
      <div class="offer-info">
        <span class="offer-store">${offer.store_name}</span>
        <span class="offer-price">${new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(parseFloat(offer.price))}</span>
        <span class="offer-updated">Actualizado: ${updatedText}</span>
      </div>
      <button class="compare-btn" data-url="${offer.product_url}">IR A TIENDA</button>
    `;
    row.querySelector('.compare-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      const url = e.currentTarget.getAttribute('data-url');
      if (url && url !== '#') window.open(url, '_blank');
    });
    container.appendChild(row);
  });
}

function renderPriceHistory(productId) {
  const product = PRODUCTS.find(p => p.id === productId);
  const historyContainer = document.getElementById('modalPriceHistory');

  if (!product || !product.priceHistory || product.priceHistory.length === 0) {
    historyContainer.style.display = 'none';
    return;
  }

  historyContainer.style.display = 'block';

  // Destruir gráfica anterior si existe
  if (priceModal) {
    priceModal.destroy();
  }

  const labels = product.priceHistory.map(h => h.date);
  const data = product.priceHistory.map(h => h.price);

  const ctx = document.getElementById('modalPriceChart').getContext('2d');
  priceModal = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: `Precio (${OFFERS.find(o => o.productId === productId)?.currency || 'EUR'})`,
        data: data,
        borderColor: '#00FF00',
        backgroundColor: 'rgba(0, 255, 0, 0.1)',
        borderWidth: 3,
        pointBackgroundColor: '#000',
        pointBorderColor: '#00FF00',
        pointBorderWidth: 2,
        pointRadius: 5,
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: false,
          grid: { color: '#ddd' }
        },
        x: {
          grid: { display: false }
        }
      },
      plugins: { legend: { display: true } }
    }
  });
}

function formatDate(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'ahora';
  if (diffMins < 60) return `hace ${diffMins} min`;
  if (diffHours < 24) return `hace ${diffHours} h`;
  if (diffDays < 30) return `hace ${diffDays} d`;

  return date.toLocaleDateString('es-ES');
}

function setupModalListeners() {
  // Cerrar modal por botón X
  document.getElementById('closeModal').addEventListener('click', closePriceModal);

  // Cerrar modal por tecla ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('priceModal').style.display !== 'none') {
      closePriceModal();
    }
  });

  // Cerrar modal por click en overlay
  document.getElementById('priceModal').addEventListener('click', (e) => {
    if (e.target.id === 'priceModal') {
      closePriceModal();
    }
  });
}
function setupAuthListeners() {
  // LOGIN FORM
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value;
      const password = document.getElementById('loginPassword').value;

      const result = await loginUser(email, password);
      if (result.success) {
        updateUserMenu();
        router.go('/');
        alert('¡Bienvenido ' + (result.user.name || result.user.full_name || 'Usuario') + '!');
      } else {
        alert('Error: ' + result.error);
      }
      loginForm.reset();
    });
  }

  // REGISTER FORM
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('registerName').value;
      const email = document.getElementById('registerEmail').value;
      const password = document.getElementById('registerPassword').value;
      const passwordConfirm = document.getElementById('registerPasswordConfirm').value;

      if (password !== passwordConfirm) {
        alert('Las contraseñas no coinciden');
        return;
      }

      const result = await registerUser(email, password, name);
      if (result.success) {
        alert('¡Cuenta creada! Ahora puedes iniciar sesión');
        router.go('/login');
      } else {
        alert('Error: ' + result.error);
      }
      registerForm.reset();
    });
  }

  // LOGIN BUTTON IN HEADER
  const loginBtn = document.querySelector('.button-login');
  if (loginBtn) {
    loginBtn.addEventListener('click', () => {
      router.go('/login');
    });
  }
}

function updateUserMenu() {
  const userMenu = document.getElementById('userMenu');
  const mobileUserMenu = document.getElementById('mobileUserMenu');
  const user = getCurrentUser();

  // Clear both menus
  userMenu.innerHTML = '';
  if (mobileUserMenu) mobileUserMenu.innerHTML = '';

  if (user && isLoggedIn()) {
    // Desktop user menu
    userMenu.innerHTML = `
      <img src="${user.avatar}" alt="avatar" class="user-avatar">
      <span class="user-username">${user.name}</span>
      <div class="user-dropdown">
        <button class="brutal-btn" style="padding: 0.5rem 1rem; font-size: 0.75rem;">CUENTA ▼</button>
        <div class="user-dropdown-menu">
          <a href="#/saved">MIS PRODUCTOS GUARDADOS</a>
          <a href="#/profile">MI PERFIL</a>
          <a href="#/alerts">MIS ALERTAS</a>
          <button id="logoutHeaderBtn">CERRAR SESIÓN</button>
        </div>
      </div>
    `;

    // Mobile user menu
    if (mobileUserMenu) {
      mobileUserMenu.innerHTML = `
        <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem; border-bottom: 2px solid #ddd;">
          <img src="${user.avatar}" alt="avatar" style="width: 50px; height: 50px; border-radius: 50%; border: 2px solid var(--neon-green);">
          <div>
            <p style="margin: 0; font-weight: 900; font-size: 0.9rem;">${user.name}</p>
            <p style="margin: 0; font-family: 'JetBrains Mono'; font-size: 0.75rem; color: #999;">${user.email}</p>
          </div>
        </div>
        <a href="#/saved" class="mobile-menu-item">
          <i class="material-icons">bookmark</i> MIS PRODUCTOS GUARDADOS
        </a>
        <a href="#/profile" class="mobile-menu-item">
          <i class="material-icons">person</i> MI PERFIL
        </a>
        <a href="#/alerts" class="mobile-menu-item">
          <i class="material-icons">notifications</i> MIS ALERTAS
        </a>
        <button id="mobileLogoutBtn" class="mobile-menu-item mobile-logout">
          <i class="material-icons">logout</i> CERRAR SESIÓN
        </button>
      `;
    }

    // Setup desktop dropdown
    const dropdownBtn = userMenu.querySelector('.brutal-btn');
    const dropdownMenu = userMenu.querySelector('.user-dropdown-menu');

    dropdownBtn.addEventListener('click', () => {
      dropdownMenu.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
      if (!userMenu.contains(e.target)) {
        dropdownMenu.classList.remove('active');
      }
    });

    // Setup logout button (both desktop and mobile)
    const logoutBtn = document.getElementById('logoutHeaderBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        logoutUser();
        updateUserMenu();
        router.go('/');
        alert('Sesión cerrada');
      });
    }

    const mobileLogoutBtn = document.getElementById('mobileLogoutBtn');
    if (mobileLogoutBtn) {
      mobileLogoutBtn.addEventListener('click', () => {
        logoutUser();
        updateUserMenu();
        router.go('/');
        alert('Sesión cerrada');
        // Cerrar menú móvil basado en checkbox
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        if (mobileMenuToggle) mobileMenuToggle.checked = false;
        document.body.style.overflow = 'auto';
      });
    }
  } else {
    // Desktop login button
    userMenu.innerHTML = `<button class="brutal-btn button-login">LOGIN</button>`;
    const newLoginBtn = userMenu.querySelector('.button-login');
    newLoginBtn.addEventListener('click', () => {
      router.go('/login');
    });

    // Mobile login button
    if (mobileUserMenu) {
      mobileUserMenu.innerHTML = `
        <button class="mobile-menu-item" id="mobileLoginBtn">
          <i class="material-icons">login</i> INICIAR SESIÓN
        </button>
        <button class="mobile-menu-item" id="mobileRegisterBtn">
          <i class="material-icons">app_registration</i> REGISTRARSE
        </button>
      `;

      const mobileLoginBtn = document.getElementById('mobileLoginBtn');
      const mobileRegisterBtn = document.getElementById('mobileRegisterBtn');

      mobileLoginBtn.addEventListener('click', () => {
        router.go('/login');
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        if (mobileMenuToggle) mobileMenuToggle.checked = false;
        document.body.style.overflow = 'auto';
      });

      mobileRegisterBtn.addEventListener('click', () => {
        router.go('/register');
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        if (mobileMenuToggle) mobileMenuToggle.checked = false;
        document.body.style.overflow = 'auto';
      });
    }
    // Guard: if button didn't appear (DOM/CSS issue), create a minimal login link in header
    setTimeout(() => {
      if (!userMenu.querySelector('.button-login')) {
        const fallback = document.createElement('a');
        fallback.textContent = 'LOGIN';
        fallback.href = '#/login';
        fallback.className = 'brutal-btn button-login';
        userMenu.appendChild(fallback);
      }
    }, 200);
  }
}

function setupProfileListeners() {
  const profilePage = document.getElementById('profilePage');
  if (!profilePage) return;

  const user = getCurrentUser();
  if (!user) {
    router.go('/login');
    return;
  }

  // Display user info
  document.getElementById('profileAvatar').src = user.avatar;
  document.getElementById('profileName').textContent = user.name;
  document.getElementById('profileEmail').textContent = user.email;
  document.getElementById('profileMemberSince').textContent =
    'Miembro desde: ' + new Date(user.createdAt).toLocaleDateString('es-ES');

  // Display stats
  const alerts = getAlerts();
  const userAlerts = alerts.filter(a => a.productId); // Simplified count
  document.getElementById('alertsCount').textContent = userAlerts.length;

  const searchHistory = JSON.parse(localStorage.getItem('sportsscraper_search_history')) || [];
  document.getElementById('recentSearches').textContent = searchHistory.length;

  // Profile action buttons
  document.getElementById('editProfileBtn').addEventListener('click', () => {
    const newName = prompt('Nuevo nombre:', user.name);
    if (newName && newName.trim()) {
      updateUserProfile(newName, user.email);
      alert('Perfil actualizado');
      document.getElementById('profileName').textContent = newName;
    }
  });

  document.getElementById('changePasswordBtn').addEventListener('click', async () => {
    const oldPassword = prompt('Contraseña actual:');
    if (!oldPassword) return;

    const newPassword = prompt('Nueva contraseña (mín. 6 caracteres):');
    if (!newPassword || newPassword.length < 6) {
      alert('Contraseña inválida');
      return;
    }

    const result = await changePassword(oldPassword, newPassword);
    if (result.success) {
      alert('Contraseña cambiada exitosamente');
    } else {
      alert('Error: ' + result.error);
    }
  });

  document.getElementById('logoutBtn').addEventListener('click', () => {
    logoutUser();
    updateUserMenu();
    router.go('/');
    alert('Sesión cerrada');
  });
}

function setupAlertsPageListeners() {
  const alertsPage = document.getElementById('alertsPage');
  if (!alertsPage) return;

  const user = getCurrentUser();
  if (!user) {
    router.go('/login');
    return;
  }

  renderAlertsPage();

  const filterSelect = document.getElementById('alertFilter');
  if (filterSelect) {
    filterSelect.addEventListener('change', () => {
      renderAlertsPage();
    });
  }
}

function renderAlertsPage() {
  const alerts = getAlerts();
  const filterValue = document.getElementById('alertFilter')?.value || '';

  let filtered = alerts;
  if (filterValue === 'active') {
    filtered = alerts.filter(a => a.enabled);
  } else if (filterValue === 'inactive') {
    filtered = alerts.filter(a => !a.enabled);
  }

  const alertsList = document.getElementById('alertsList');
  const emptyState = document.getElementById('emptyAlertsState');

  if (filtered.length === 0) {
    alertsList.style.display = 'none';
    emptyState.style.display = 'flex';
    return;
  }

  alertsList.style.display = 'flex';
  emptyState.style.display = 'none';

  alertsList.innerHTML = filtered.map(alert => {
    const product = PRODUCTS.find(p => p.id === alert.productId);
    if (!product) return '';

    return `
      <div class="alert-card">
        <div class="alert-product">
          <img src="${product.image}" alt="${product.name}">
          <div class="alert-info">
            <h3>${product.name}</h3>
            <p>Objetivo: €${alert.targetPrice} | Estado: ${alert.enabled ? 'ACTIVA' : 'INACTIVA'}</p>
          </div>
        </div>
        <div class="alert-actions">
          <button class="alert-btn" data-alert-id="${alert.id}" data-action="toggle">
            ${alert.enabled ? 'DESACTIVAR' : 'ACTIVAR'}
          </button>
          <button class="alert-btn delete" data-alert-id="${alert.id}" data-action="delete">ELIMINAR</button>
        </div>
      </div>
    `;
  }).join('');

  // Add event listeners for delete/toggle buttons
  alertsList.querySelectorAll('.alert-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const alertId = btn.dataset.alertId;
      const action = btn.dataset.action;

      if (action === 'delete') {
        if (confirm('¿Eliminar esta alerta?')) {
          deleteAlert(alertId);
          renderAlertsPage();
        }
      } else if (action === 'toggle') {
        toggleAlertActive(alertId);
        renderAlertsPage();
      }
    });
  });
}

// ========================================
// INITIALIZE ROUTING AND AUTH
// ========================================

// Setup routers
document.addEventListener('DOMContentLoaded', async () => {
  // If backend API is available, fetch products to replace local mocks
  const hasProducts = await fetchProductsFromApi().catch(() => false);
  
  // If no products, trigger scraping
  if (!hasProducts || PRODUCTS.length === 0) {
    await triggerScrapingIfNeeded();
  }
  
  init();
  setupAuthListeners();
  updateUserMenu();

  // Setup page-specific listeners when router navigates
  const observer = new MutationObserver(() => {
    const visiblePage = document.querySelector('[data-page]:not([style*="display: none"])');
    if (visiblePage) {
      const pageId = visiblePage.id;
      if (pageId === 'profilePage') {
        setupProfileListeners();
      } else if (pageId === 'alertsPage') {
        setupAlertsPageListeners();
      } else if (pageId === 'savedProductsPage') {
        initSavedProductsPage();
      }
    }
  });

  observer.observe(document.body, {
    subtree: true,
    attributes: true,
    attributeFilter: ['style']
  });

  // Initial navigation
  router.navigate();
});


// (fetchProductsFromApi implementation is defined earlier in the file)

// Render price history from API payload
function renderPriceHistoryFromApi(history) {
  const historyContainer = document.getElementById('modalPriceHistory');
  if (!history || history.length === 0) {
    historyContainer.style.display = 'none';
    return;
  }
  historyContainer.style.display = 'block';

  if (priceModal) {
    priceModal.destroy();
  }

  const labels = history.map(h => new Date(h.scraped_at).toLocaleString());
  const data = history.map(h => parseFloat(h.price));

  const ctx = document.getElementById('modalPriceChart').getContext('2d');
  priceModal = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Precio',
        data: data,
        borderColor: '#00FF00',
        backgroundColor: 'rgba(0,255,0,0.08)',
        tension: 0.1
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
}

// PRICE ALERTS (CU3)
// ========================================
let currentProductId = null;
let editingAlertId = null;

function initializeAlerts() {
  // Cargar alertas al iniciar
  const alerts = getAlerts();
  if (alerts.length > 0) {
    document.getElementById('bellButton')?.classList.add('active');
  }
}

function getAlerts() {
  // Prefer backend alerts API; fallback to localStorage
  try {
    // synchronous fallback: return stored immediately, but refresh in background
    const stored = localStorage.getItem('sportsscraper_alerts');
    const fallback = stored ? JSON.parse(stored) : [];
    fetch(`${API_BASE}/api/alerts`).then(r => r.ok ? r.json().then(data => {
      try { localStorage.setItem('sportsscraper_alerts', JSON.stringify(data)); } catch(e){}
    }) : null).catch(() => {});
    return fallback;
  } catch (e) {
    return [];
  }
}

function saveAlertsToStorage(alerts) {
  try {
    localStorage.setItem('sportsscraper_alerts', JSON.stringify(alerts));
  } catch (e) {
    console.error('Error guardando alertas:', e);
  }
}

function getProductAlerts(productId) {
  const alerts = getAlerts();
  return alerts.filter(a => a.productId === productId && a.enabled);
}

async function saveAlert(productId, targetPrice, stores, alertIdToEdit = null) {
  if (!productId || !targetPrice || Number(targetPrice) <= 0) {
    alert('Por favor ingresa un precio válido');
    return false;
  }

  // Normalize product id to integer when possible
  let pid = Number(productId);
  if (Number.isNaN(pid)) {
    // try to find in PRODUCTS list by matching id or name
    const found = (window.PRODUCTS || []).find(p => String(p.id) === String(productId) || p.name === productId);
    if (found && found.id) pid = Number(found.id);
  }

  if (Number.isNaN(pid) || !Number.isFinite(pid)) {
    showPriceNotification('No se pudo identificar el producto para la alerta', 'error');
    return false;
  }

  try {
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('sportsscraper_token');
    if (token) headers['Authorization'] = 'Bearer ' + token;

    const res = await fetch(`${API_BASE}/api/alerts/`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ product_id: pid, target_price: parseFloat(targetPrice), stores })
    });

    if (res.status === 401) {
      showPriceNotification('Debes iniciar sesión para crear alertas', 'error');
      // redirect to login after short delay
      setTimeout(() => router.go('/login'), 600);
      return false;
    }

    if (!res.ok) {
      let payload = {};
      try { payload = await res.json(); } catch (_) {}
      showPriceNotification(payload.error || 'Error guardando alerta', 'error');
      return false;
    }

    const data = await res.json();
    // store into local as cache (most recent first)
    const alerts = getAlerts();
    alerts.unshift(data);
    saveAlertsToStorage(alerts);
    showPriceNotification('¡Alerta guardada exitosamente!', 'success');
    renderActiveAlerts(pid);
    updateBellIcon();
    return true;
  } catch (e) {
    console.error('saveAlert error', e);
    showPriceNotification('Error guardando alerta (conexión)', 'error');
    return false;
  }
}

function deleteAlert(alertId) {
  if (!confirm('¿Estás seguro de que deseas eliminar esta alerta?')) return;
  // Try backend delete
  try {
    const token = localStorage.getItem('sportsscraper_token');
    const headers = token ? { 'Authorization': 'Bearer ' + token } : {};
    fetch(`${API_BASE}/api/alerts/${alertId}`, { method: 'DELETE', headers }).then(r => {
      if (r.ok) {
        const alerts = getAlerts().filter(a => String(a.id) !== String(alertId));
        saveAlertsToStorage(alerts);
        renderActiveAlerts(currentProductId);
        updateBellIcon();
        showPriceNotification('Alerta eliminada', 'success');
      } else {
        showPriceNotification('Error al eliminar alerta', 'error');
      }
    }).catch(() => showPriceNotification('Error al eliminar alerta', 'error'));
  } catch (e) {
    showPriceNotification('Error al eliminar alerta', 'error');
  }
}

function toggleAlertActive(alertId) {
  try {
    const alerts = getAlerts();
    const alert = alerts.find(a => String(a.id) === String(alertId));
    if (!alert) return;
    const newState = !alert.enabled;
    const token = localStorage.getItem('sportsscraper_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    fetch(`${API_BASE}/api/alerts/${alertId}/toggle`, { method: 'PUT', headers, body: JSON.stringify({ enabled: newState }) })
      .then(async r => {
        if (r.status === 401) {
          showPriceNotification('Debes iniciar sesión para modificar alertas', 'error');
          setTimeout(() => router.go('/login'), 600);
          return;
        }
        if (r.ok) {
          alert.enabled = newState;
          saveAlertsToStorage(alerts);
          renderActiveAlerts(currentProductId);
          updateBellIcon();
        } else {
          let payload = {};
          try { payload = await r.json(); } catch (_) {}
          showPriceNotification(payload.error || 'No se pudo actualizar la alerta', 'error');
        }
      }).catch(() => showPriceNotification('Error de conexión al actualizar alerta', 'error'));
  } catch (e) {}
}

function editAlert(alertId) {
  const alerts = getAlerts();
  const alert = alerts.find(a => a.id === alertId);
  if (!alert) return;

  editingAlertId = alertId;
  document.getElementById('targetPrice').value = alert.targetPrice;

  // Des-seleccionar todos los checkboxes
  document.querySelectorAll('.store-checkbox input').forEach(cb => cb.checked = false);

  // Seleccionar los checkboxes del alerta
  if (alert.stores.length > 0) {
    alert.stores.forEach(storeId => {
      const checkbox = document.querySelector(`input[value="${storeId}"]`);
      if (checkbox) checkbox.checked = true;
    });
  }

  document.getElementById('toggleAlertForm').click();
  document.getElementById('targetPrice').focus();
}

function renderAlertForm(productId) {
  currentProductId = productId;
  const form = document.getElementById('alertForm');
  const toggleBtn = document.getElementById('toggleAlertForm');

  // Renderizar checkboxes de tiendas
  const storesContainer = document.getElementById('storeCheckboxes');
  storesContainer.innerHTML = '';
  STORES.forEach(store => {
    const label = document.createElement('label');
    label.className = 'store-checkbox';
    label.innerHTML = `
      <input type="checkbox" value="${store.id}">
      <span>${store.name}</span>
    `;
    storesContainer.appendChild(label);
  });

  // Event handlers unicos por apertura de modal
  toggleBtn.onclick = () => {
    const isVisible = form.style.display !== 'none';
    form.style.display = isVisible ? 'none' : 'flex';
    toggleBtn.style.transform = isVisible ? 'rotate(0deg)' : 'rotate(180deg)';
  };

  document.getElementById('cancelAlert').onclick = () => {
    form.style.display = 'none';
    editingAlertId = null;
    document.getElementById('targetPrice').value = '';
    document.querySelectorAll('.store-checkbox input').forEach(cb => cb.checked = false);
    toggleBtn.style.transform = 'rotate(0deg)';
  };

  form.onsubmit = async (e) => {
    e.preventDefault();
    const targetPrice = document.getElementById('targetPrice').value;
    const selectedStores = Array.from(document.querySelectorAll('.store-checkbox input:checked'))
      .map(cb => cb.value);

    const ok = await saveAlert(productId, targetPrice, selectedStores, editingAlertId);
    if (ok) {
      form.reset();
      form.style.display = 'none';
      toggleBtn.style.transform = 'rotate(0deg)';
      editingAlertId = null;
      renderActiveAlerts(productId);
      updateBellIcon();
    }
  };
}

function renderActiveAlerts(productId) {
  const alerts = getProductAlerts(productId);
  const container = document.getElementById('activeAlerts');
  const list = document.getElementById('modalAlertsList');

  if (alerts.length === 0) {
    container.style.display = 'none';
    return;
  }

  container.style.display = 'block';
  list.innerHTML = '';

  alerts.forEach(alert => {
    const storeNames = alert.stores.length > 0
      ? STORES.filter(s => alert.stores.includes(s.id)).map(s => s.name).join(', ')
      : 'Todas las tiendas';

    const item = document.createElement('div');
    item.className = 'alert-item';
    item.innerHTML = `
      <div class="alert-item-info">
        <strong>Precio objetivo:</strong> €${alert.targetPrice.toFixed(2)}<br>
        <strong>Tiendas:</strong> ${storeNames}
      </div>
      <div class="alert-item-actions">
        <button class="alert-btn" onclick="editAlert('${alert.id}')">EDITAR</button>
        <button class="alert-btn" onclick="toggleAlertActive('${alert.id}')">${alert.enabled ? 'DESACTIVAR' : 'ACTIVAR'}</button>
        <button class="alert-btn delete" onclick="deleteAlert('${alert.id}')">ELIMINAR</button>
      </div>
    `;
    list.appendChild(item);
  });
}

function updateBellIcon() {
  const allAlerts = getAlerts();
  const activeAlerts = allAlerts.filter(a => a.enabled);
  const bellIcon = document.getElementById('bellButton');

  if (activeAlerts.length > 0) {
    bellIcon.classList.add('active');
    bellIcon.setAttribute('data-count', activeAlerts.length);
  } else {
    bellIcon.classList.remove('active');
    bellIcon.setAttribute('data-count', '');
  }
}

function checkPriceAlerts(productId) {
  const alerts = getProductAlerts(productId);
  const offers = OFFERS.filter(o => o.productId === productId);

  if (offers.length === 0) return;

  const lowestPrice = Math.min(...offers.map(o => o.price));

  alerts.forEach(alert => {
    if (lowestPrice <= alert.targetPrice && !alert.triggered) {
      const storeName = alert.stores.length > 0
        ? STORES.filter(s => alert.stores.includes(s.id)).map(s => s.name).join(', ')
        : 'algunas tiendas';

      showPriceNotification(
        `¡Alerta! El precio bajó a €${lowestPrice.toFixed(2)} en ${storeName}`,
        'alert'
      );

      // Marcar alerta como disparada
      const allAlerts = getAlerts();
      const idx = allAlerts.findIndex(a => a.id === alert.id);
      if (idx !== -1) {
        allAlerts[idx].triggered = true;
        saveAlertsToStorage(allAlerts);
      }
    }
  });
}

function showPriceNotification(message, type = 'success') {
  const notification = document.getElementById('priceAlertNotification');
  const messageEl = document.getElementById('notificationMessage');
  const closeBtn = document.getElementById('closeNotification');

  messageEl.textContent = message;
  notification.className = 'price-alert-notification';
  if (type === 'alert') {
    notification.classList.add('warning');
  }

  notification.style.display = 'flex';

  closeBtn.addEventListener('click', () => {
    notification.style.display = 'none';
  }, { once: true });

  setTimeout(() => {
    if (notification.style.display !== 'none') {
      notification.style.display = 'none';
    }
  }, 5000);
}

function setupAlertListeners() {
  const bellButton = document.getElementById('bellButton');

  bellButton.addEventListener('click', () => {
    const form = document.getElementById('alertForm');
    const isVisible = form.style.display !== 'none';
    form.style.display = isVisible ? 'none' : 'flex';
    document.getElementById('toggleAlertForm').style.transform = isVisible ? 'rotate(0deg)' : 'rotate(180deg)';
  });
}
