// ========================================
// SAVED PRODUCTS - Mock Data
// ========================================

const SAVED_PRODUCTS = [
  {
    id: 'sp1',
    name: 'Nike Air Zoom Pegasus 40',
    brand: 'Nike',
    category: 'Running',
    image: 'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?q=80&w=600&auto=format&fit=crop',
    originalPrice: 149.99,
    currentPrice: 99.99,
    stock: 12,
    deliveryDays: '2-3',
    rating: 4.5,
    reviews: 328,
    specs: {
      'Peso': '311g',
      'Material': 'Mesh + Sintético',
      'Suela': 'Goma Espuma Zoom',
      'Talla': 'Unisex',
      'Peso Máximo': '100kg',
      'Tecnología': 'Zoom Air'
    }
  },
  {
    id: 'sp2',
    name: 'Adidas Ultraboost Light',
    brand: 'Adidas',
    category: 'Running',
    image: 'https://images.unsplash.com/photo-1587563871167-1ee9c731aefb?q=80&w=600&auto=format&fit=crop',
    originalPrice: 220.00,
    currentPrice: 159.99,
    stock: 5,
    deliveryDays: '3-4',
    rating: 4.8,
    reviews: 512,
    specs: {
      'Peso': '294g',
      'Material': 'Knit Primeknit',
      'Suela': 'Boost',
      'Amortiguación': 'Alta',
      'Versatilidad': 'Running/Casual',
      'Tecnología': 'Boost + Stretchweb'
    }
  },
  {
    id: 'sp3',
    name: 'Puma Velocity Nitro 2',
    brand: 'Puma',
    category: 'Running',
    image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=600&auto=format&fit=crop',
    originalPrice: 135.00,
    currentPrice: 89.99,
    stock: 0,
    deliveryDays: '5-7',
    rating: 4.2,
    reviews: 156,
    specs: {
      'Peso': '305g',
      'Material': 'Synthé tico',
      'Suela': 'Nitro Foam',
      'Grip': 'Excelente',
      'Uso': 'Terreno Mixto',
      'Tecnología': 'Nitro Foam'
    }
  },
  {
    id: 'sp4',
    name: 'Nike Sportswear Tech Fleece',
    brand: 'Nike',
    category: 'Apparel',
    image: 'https://images.unsplash.com/photo-1556906781-9a412961c28c?q=80&w=600&auto=format&fit=crop',
    originalPrice: 149.99,
    currentPrice: 124.99,
    stock: 25,
    deliveryDays: '1-2',
    rating: 4.6,
    reviews: 892,
    specs: {
      'Material': 'Algodón + Poliéster',
      'Clima': 'Templado',
      'Capucha': 'Sí',
      'Bolsillos': '2 laterales',
      'Cierre': 'Completo',
      'Cuidado': 'Lavar 30°C'
    }
  },
  {
    id: 'sp5',
    name: 'Asics Novablast 3',
    brand: 'Asics',
    category: 'Running',
    image: 'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?q=80&w=600&auto=format&fit=crop',
    originalPrice: 180.00,
    currentPrice: 129.99,
    stock: 8,
    deliveryDays: '2-3',
    rating: 4.7,
    reviews: 445,
    specs: {
      'Peso': '289g',
      'Amortiguación': 'Gel + FF Blast',
      'Responsividad': 'Alta',
      'Para': 'Corredores Neutros',
      'Durabilidad': 'Excelente',
      'Tecnología': 'Gel + FlyteFoam Propel'
    }
  },
  {
    id: 'sp6',
    name: 'New Balance Fresh Foam 1080',
    brand: 'New Balance',
    category: 'Running',
    image: 'https://images.unsplash.com/photo-1539185441755-769473a23570?q=80&w=600&auto=format&fit=crop',
    originalPrice: 220.00,
    currentPrice: 169.99,
    stock: 15,
    deliveryDays: '2-3',
    rating: 4.4,
    reviews: 267,
    specs: {
      'Peso': '310g',
      'Espuma': 'Fresh Foam X',
      'Suavidad': 'Máxima',
      'Estabilidad': 'Neutral',
      'Uso': 'Largas Distancias',
      'Acolchado': 'Premium'
    }
  }
];

// ========================================
// SAVED PRODUCTS PAGE FUNCTIONALITY
// ========================================

let savedProductsState = {
  all: [...SAVED_PRODUCTS],
  filtered: [...SAVED_PRODUCTS],
  currentModalProduct: null,
  filters: {
    category: '',
    priceMin: 0,
    priceMax: Infinity,
    brands: [],
    rating: 0,
    inStockOnly: false
  },
  sortBy: 'newest'
};

function initSavedProductsPage() {
  // Load from localStorage
  loadSavedProducts();

  // Setup event listeners
  setupSavedProductsFilters();
  setupSavedProductsSort();
  setupSavedModalListeners();

  // Initial render
  renderSavedProducts();
}

function setupSavedProductsFilters() {
  // Category filter
  const categoryFilter = document.getElementById('savedCategoryFilter');
  categoryFilter?.addEventListener('change', (e) => {
    savedProductsState.filters.category = e.target.value;
    applyFilters();
  });

  // Price filters
  const priceMin = document.getElementById('savedPriceMin');
  const priceMax = document.getElementById('savedPriceMax');

  priceMin?.addEventListener('change', (e) => {
    savedProductsState.filters.priceMin = e.target.value ? parseFloat(e.target.value) : 0;
    applyFilters();
  });

  priceMax?.addEventListener('change', (e) => {
    savedProductsState.filters.priceMax = e.target.value ? parseFloat(e.target.value) : Infinity;
    applyFilters();
  });

  // Rating filter
  const ratingFilter = document.getElementById('savedRatingFilter');
  ratingFilter?.addEventListener('change', (e) => {
    savedProductsState.filters.rating = parseFloat(e.target.value);
    applyFilters();
  });

  // Stock filter
  const stockFilter = document.getElementById('savedStockFilter');
  stockFilter?.addEventListener('change', (e) => {
    savedProductsState.filters.inStockOnly = e.target.checked;
    applyFilters();
  });

  // Reset button
  const resetBtn = document.getElementById('savedResetFiltersBtn');
  resetBtn?.addEventListener('click', () => {
    categoryFilter.value = '';
    priceMin.value = '';
    priceMax.value = '';
    ratingFilter.value = '0';
    stockFilter.checked = false;

    savedProductsState.filters = {
      category: '',
      priceMin: 0,
      priceMax: Infinity,
      brands: [],
      rating: 0,
      inStockOnly: false
    };

    applyFilters();
  });

  // Populate brand checkboxes
  populateBrandFilters();
}

function populateBrandFilters() {
  const brands = [...new Set(savedProductsState.all.map(p => p.brand))];
  const brandFiltersContainer = document.getElementById('savedBrandFilters');

  if (!brandFiltersContainer) return;

  brandFiltersContainer.innerHTML = brands.map(brand => `
    <label class="filter-checkbox-item">
      <input type="checkbox" value="${brand}" class="brand-checkbox">
      <label style="margin: 0; cursor: pointer;">${brand}</label>
    </label>
  `).join('');

  document.querySelectorAll('.brand-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      savedProductsState.filters.brands = Array.from(
        document.querySelectorAll('.brand-checkbox:checked')
      ).map(c => c.value);
      applyFilters();
    });
  });
}

function setupSavedProductsSort() {
  const sortBy = document.getElementById('savedSortBy');
  sortBy?.addEventListener('change', (e) => {
    savedProductsState.sortBy = e.target.value;
    renderSavedProducts();
  });
}

function setupSavedModalListeners() {
  const modal = document.getElementById('savedProductModal');
  const closeBtn = document.getElementById('closeSavedModal');

  closeBtn?.addEventListener('click', () => {
    modal.style.display = 'none';
  });

  modal?.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.style.display = 'none';
    }
  });

  // Modal action buttons
  document.getElementById('savedModalAddCart')?.addEventListener('click', () => {
    alert(`✅ ${savedProductsState.currentModalProduct.name} agregado al carrito`);
  });

  document.getElementById('savedModalShare')?.addEventListener('click', () => {
    const product = savedProductsState.currentModalProduct;
    const text = `Mira este producto: ${product.name} por ${product.currentPrice}€`;
    if (navigator.share) {
      navigator.share({ title: 'SportsScraper', text });
    } else {
      alert('Producto: ' + product.name + '\nPrecio: €' + product.currentPrice);
    }
  });

  document.getElementById('savedModalRemove')?.addEventListener('click', () => {
    const product = savedProductsState.currentModalProduct;
    removeSavedProduct(product.id);
    modal.style.display = 'none';
    renderSavedProducts();
  });
}

function applyFilters() {
  let filtered = savedProductsState.all.filter(product => {
    const categoryMatch = !savedProductsState.filters.category ||
                         product.category === savedProductsState.filters.category;

    const priceMatch = product.currentPrice >= savedProductsState.filters.priceMin &&
                      product.currentPrice <= savedProductsState.filters.priceMax;

    const brandMatch = savedProductsState.filters.brands.length === 0 ||
                      savedProductsState.filters.brands.includes(product.brand);

    const ratingMatch = product.rating >= savedProductsState.filters.rating;

    const stockMatch = !savedProductsState.filters.inStockOnly || product.stock > 0;

    return categoryMatch && priceMatch && brandMatch && ratingMatch && stockMatch;
  });

  savedProductsState.filtered = filtered;
  renderSavedProducts();
}

function renderSavedProducts() {
  const grid = document.getElementById('savedProductsGrid');
  const empty = document.getElementById('savedProductsEmpty');
  const count = document.getElementById('savedProductsCount');

  if (!grid) return;

  // Sort
  let sorted = [...savedProductsState.filtered];
  switch(savedProductsState.sortBy) {
    case 'price-low':
      sorted.sort((a, b) => a.currentPrice - b.currentPrice);
      break;
    case 'price-high':
      sorted.sort((a, b) => b.currentPrice - a.currentPrice);
      break;
    case 'rating':
      sorted.sort((a, b) => b.rating - a.rating);
      break;
    default: // newest
      break;
  }

  // Render
  if (sorted.length === 0) {
    grid.innerHTML = '';
    empty.style.display = 'flex';
    count.textContent = '0 productos guardados';
    return;
  }

  empty.style.display = 'none';
  count.textContent = `${sorted.length} producto${sorted.length !== 1 ? 's' : ''} guardado${sorted.length !== 1 ? 's' : ''}`;

  grid.innerHTML = sorted.map(product => {
    const discount = Math.round(((product.originalPrice - product.currentPrice) / product.originalPrice) * 100);
    const inStock = product.stock > 0;

    return `
      <div class="saved-product-card" data-product-id="${product.id}">
        <div class="saved-product-image-wrapper">
          <img src="${product.image}" alt="${product.name}" class="saved-product-image" referrerPolicy="no-referrer">
          ${discount > 0 ? `<span class="saved-product-discount-badge">-${discount}%</span>` : ''}
        </div>

        <div class="saved-product-header">
          <h3>${product.name}</h3>
          <span class="saved-product-brand">${product.brand}</span>
        </div>

        <p class="saved-product-category">${product.category}</p>

        <div class="saved-product-rating">
          <span>${'★'.repeat(Math.floor(product.rating))}${'☆'.repeat(5 - Math.floor(product.rating))}</span>
          <span>(${product.reviews})</span>
        </div>

        <div class="saved-product-pricing">
          <span class="saved-product-original">€${product.originalPrice.toFixed(2)}</span>
          <span class="saved-product-current">€${product.currentPrice.toFixed(2)}</span>
        </div>

        <div class="saved-product-stock ${inStock ? 'in-stock' : 'out-stock'}">
          ${inStock ? `✓ En stock (${product.stock})` : '✕ Sin stock'}
        </div>

        <div class="saved-product-footer">
          <button class="saved-product-btn btn-view-details" data-product-id="${product.id}">
            <i class="material-icons">visibility</i> VER DETALLES
          </button>
          <button class="saved-product-btn btn-add-cart" data-product-id="${product.id}">
            <i class="material-icons">shopping_cart</i> CARRITO
          </button>
          <button class="saved-product-btn btn-remove" data-product-id="${product.id}">
            <i class="material-icons">delete</i> ELIMINAR
          </button>
        </div>
      </div>
    `;
  }).join('');

  // Add event listeners
  document.querySelectorAll('.btn-view-details').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const productId = btn.dataset.productId;
      openSavedProductModal(productId);
    });
  });

  document.querySelectorAll('.btn-add-cart').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const productId = btn.dataset.productId;
      const product = savedProductsState.all.find(p => p.id === productId);
      alert(`✅ ${product.name} agregado al carrito`);
    });
  });

  document.querySelectorAll('.btn-remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const productId = btn.dataset.productId;
      if (confirm('¿Eliminar este producto guardado?')) {
        removeSavedProduct(productId);
        renderSavedProducts();
      }
    });
  });

  // Card click
  document.querySelectorAll('.saved-product-card').forEach(card => {
    card.addEventListener('click', () => {
      const productId = card.dataset.productId;
      openSavedProductModal(productId);
    });
  });
}

function openSavedProductModal(productId) {
  const product = savedProductsState.all.find(p => p.id === productId);
  if (!product) return;

  savedProductsState.currentModalProduct = product;

  // Populate modal
  document.getElementById('savedModalProductName').textContent = product.name;
  document.getElementById('savedModalProductImage').src = product.image;
  document.getElementById('savedModalBrand').textContent = product.brand;
  document.getElementById('savedModalCategory').textContent = product.category;
  document.getElementById('savedModalOriginalPrice').textContent = `€${product.originalPrice.toFixed(2)}`;
  document.getElementById('savedModalCurrentPrice').textContent = `€${product.currentPrice.toFixed(2)}`;

  const discount = Math.round(((product.originalPrice - product.currentPrice) / product.originalPrice) * 100);
  document.getElementById('savedModalDiscount').textContent = `-${discount}%`;

  document.getElementById('savedModalStock').textContent = product.stock > 0 ?
    `${product.stock} unidades` : 'Sin stock';
  document.getElementById('savedModalDelivery').textContent = `${product.deliveryDays} días`;

  document.getElementById('savedModalRating').textContent = '★'.repeat(Math.floor(product.rating)) +
                                                           '☆'.repeat(5 - Math.floor(product.rating));
  document.getElementById('savedModalReviews').textContent = `(${product.reviews} reseñas)`;

  // Specs
  const specsTable = document.getElementById('savedModalSpecs');
  specsTable.innerHTML = Object.entries(product.specs).map(([key, value]) => `
    <tr>
      <td>${key}</td>
      <td>${value}</td>
    </tr>
  `).join('');

  document.getElementById('savedProductModal').style.display = 'flex';
}

function removeSavedProduct(productId) {
  savedProductsState.all = savedProductsState.all.filter(p => p.id !== productId);
  saveSavedProducts();
  applyFilters();
}

function loadSavedProducts() {
  const saved = localStorage.getItem('savedProducts');
  if (saved) {
    try {
      savedProductsState.all = JSON.parse(saved);
      savedProductsState.filtered = [...savedProductsState.all];
    } catch (e) {
      console.error('Error loading saved products');
    }
  }
}

function saveSavedProducts() {
  localStorage.setItem('savedProducts', JSON.stringify(savedProductsState.all));
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('savedProductsPage')) {
    initSavedProductsPage();
  }
});
