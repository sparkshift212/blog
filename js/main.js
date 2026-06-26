document.addEventListener('DOMContentLoaded', () => {
  
  // Newsletter Form
  const newsletterForm = document.getElementById('newsletter-form');
  if (newsletterForm) {
    newsletterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      alert('Thanks for joining the Cozy Club! Check your email for your first free pattern.');
      newsletterForm.reset();
    });
  }

  // Mobile Menu Toggle (Simple alert for now, can be expanded)
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
      const navLinks = document.querySelector('.nav-links');
      if (navLinks.style.display === 'flex') {
        navLinks.style.display = 'none';
      } else {
        navLinks.style.display = 'flex';
        navLinks.style.flexDirection = 'column';
        navLinks.style.position = 'absolute';
        navLinks.style.top = '100%';
        navLinks.style.left = '0';
        navLinks.style.width = '100%';
        navLinks.style.background = 'rgba(252, 249, 242, 0.95)';
        navLinks.style.padding = '20px';
        navLinks.style.boxShadow = '0 8px 24px rgba(74, 60, 49, 0.1)';
      }
    });
  }

  // Add to Cart Buttons
  const addToCartBtns = document.querySelectorAll('.add-to-cart-btn');
  addToCartBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const title = btn.getAttribute('data-title') || 'Pattern';
      alert(`Added ${title} to your cart!`);
    });
  });

  // Contact Form
  const contactForm = document.getElementById('contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      alert('Thanks for reaching out! We will get back to you soon.');
      contactForm.reset();
    });
  }
});
