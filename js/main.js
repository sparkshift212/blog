document.addEventListener('DOMContentLoaded', () => {
  
  // Newsletter Form
  window.handleSubscribe = function(event, form) {
    if (event) event.preventDefault();
    const modal = document.getElementById('subscribe-modal-overlay');
    if (modal) {
      modal.classList.add('active');
    }
    if (form) form.reset();
  };

  const newsletterForm = document.getElementById('newsletter-form');
  if (newsletterForm) {
    newsletterForm.addEventListener('submit', (e) => {
      window.handleSubscribe(e, newsletterForm);
    });
  }

  // Inject Global Components (Search Modal, Back to Top, Mobile Drawer)
  injectGlobalComponents();

  // Mobile Menu Logic
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const mobileDrawer = document.getElementById('mobile-drawer');
  const drawerOverlay = document.getElementById('drawer-overlay');
  const drawerClose = document.getElementById('drawer-close');

  if (mobileMenuBtn && mobileDrawer) {
    mobileMenuBtn.addEventListener('click', () => {
      mobileDrawer.classList.add('active');
      drawerOverlay.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
    
    const closeDrawer = () => {
      mobileDrawer.classList.remove('active');
      drawerOverlay.classList.remove('active');
      document.body.style.overflow = '';
    };

    drawerClose.addEventListener('click', closeDrawer);
    drawerOverlay.addEventListener('click', closeDrawer);
  }

  // Search Modal Logic
  const searchBtn = document.querySelector('button[aria-label="Search"]');
  const searchModal = document.getElementById('search-modal-overlay');
  if (searchBtn && searchModal) {
    searchBtn.addEventListener('click', () => {
      searchModal.classList.add('active');
      document.getElementById('global-search-input').focus();
    });

    searchModal.addEventListener('click', (e) => {
      if (e.target === searchModal || e.target.classList.contains('search-modal-close')) {
        searchModal.classList.remove('active');
      }
    });
  }

  // Back to Top Logic
  const backToTop = document.getElementById('back-to-top');
  if (backToTop) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 300) {
        backToTop.classList.add('visible');
      } else {
        backToTop.classList.remove('visible');
      }
    });

    backToTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // Dark Mode Toggle
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    // Check local storage
    if (localStorage.getItem('theme') === 'dark') {
      document.body.setAttribute('data-theme', 'dark');
      themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }
    
    themeToggle.addEventListener('click', () => {
      if (document.body.getAttribute('data-theme') === 'dark') {
        document.body.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
      } else {
        document.body.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
      }
    });
  }
  // Handle Search Filtering on Blog/Shop pages
  const urlParams = new URLSearchParams(window.location.search);
  const searchQuery = urlParams.get('search');
  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    const searchableItems = document.querySelectorAll('.blog-card, .post-card, .shop-item, .pattern-card');
    if (searchableItems.length > 0) {
      let resultsFound = 0;
      searchableItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(query)) {
          item.style.display = '';
          resultsFound++;
        } else {
          item.style.display = 'none';
        }
      });
      
      const heroTitle = document.querySelector('.hero-title, .page-title');
      if (heroTitle) {
        heroTitle.textContent = `Search Results for "${searchQuery}"`;
      }
    }
  }

});

function injectGlobalComponents() {
  // 1. Back to Top Button
  const btn = document.createElement('button');
  btn.id = 'back-to-top';
  btn.className = 'back-to-top';
  btn.innerHTML = '<i class="fas fa-arrow-up"></i>';
  document.body.appendChild(btn);

  // 2. Search Modal
  const searchHtml = `
    <div class="search-modal-overlay" id="search-modal-overlay">
      <div class="search-modal">
        <button class="search-modal-close"><i class="fas fa-times"></i></button>
        <h3 style="margin-bottom: 1rem;">Search Patterns & Products</h3>
        <form action="blog.html" method="GET">
          <input type="text" name="search" id="global-search-input" placeholder="e.g. Axolotl, Crochet Hook..." required>
          <button type="submit" class="btn btn-primary"><i class="fas fa-search"></i></button>
        </form>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', searchHtml);

  // 3. Mobile Drawer
  // Extract nav links from desktop nav to populate mobile drawer
  const navLinks = Array.from(document.querySelectorAll('.nav-list > li > a')).map(a => `<a href="${a.href}">${a.textContent}</a>`).join('');
  const drawerHtml = `
    <div class="mobile-drawer-overlay" id="drawer-overlay"></div>
    <div class="mobile-drawer" id="mobile-drawer">
      <button class="drawer-close" id="drawer-close"><i class="fas fa-times"></i></button>
      <div class="mobile-drawer-nav">
        ${navLinks}
        <a href="shop.html" style="color:var(--color-terracotta);"><i class="fas fa-shopping-bag"></i> Shop</a>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', drawerHtml);

  // 4. Subscribe Modal
  const subscribeHtml = `
    <div class="search-modal-overlay" id="subscribe-modal-overlay">
      <div class="search-modal" style="text-align: center; max-width: 450px; padding: var(--space-6) var(--space-4);">
        <button class="search-modal-close" onclick="document.getElementById('subscribe-modal-overlay').classList.remove('active')"><i class="fas fa-times"></i></button>
        <div style="font-size: 3rem; color: var(--color-terracotta); margin-bottom: 15px;">
          <i class="fas fa-heart"></i>
        </div>
        <h3 style="margin-bottom: 10px; font-family: var(--font-display); font-size: 1.8rem; color: var(--color-sage-dark);">Thank You!</h3>
        <p style="color: var(--text-muted); font-size: 1.1rem; line-height: 1.5;">
          You've successfully subscribed. Check your email for your free pattern!
        </p>
        <button class="btn btn-primary" style="margin-top: 20px; width: 100%;" onclick="document.getElementById('subscribe-modal-overlay').classList.remove('active')">Continue Browsing</button>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', subscribeHtml);
}
