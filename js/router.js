// ========================================
// SIMPLE SPA ROUTER
// ========================================

class Router {
  constructor() {
    this.routes = {};
    this.currentRoute = '/';

    window.addEventListener('hashchange', () => this.navigate());
    window.addEventListener('DOMContentLoaded', () => this.navigate());
  }

  route(path, handler) {
    this.routes[path] = handler;
  }

  navigate() {
    const hash = window.location.hash.slice(1) || '/';
    this.currentRoute = hash;

    // Hide all pages
    document.querySelectorAll('[data-page]').forEach(page => {
      page.style.display = 'none';
    });

    // Show requested page
    if (this.routes[hash]) {
      const pageId = this.routes[hash];
      const page = document.getElementById(pageId);
      if (page) {
        page.style.display = 'block';
      }
    }
  }

  go(path) {
    window.location.hash = path;
  }
}

const router = new Router();

// ========================================
// ROUTE DEFINITIONS
// ========================================

router.route('/', 'homePage');
router.route('/login', 'loginPage');
router.route('/register', 'registerPage');
router.route('/saved', 'savedProductsPage');
router.route('/profile', 'profilePage');
router.route('/alerts', 'alertsPage');
