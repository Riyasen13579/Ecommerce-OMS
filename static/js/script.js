document.addEventListener('DOMContentLoaded', () => {

  // ── Dark mode ──────────────────────────────────────────
  const toggle = document.getElementById('dark-toggle');
  const body = document.body;
  if (localStorage.getItem('darkMode') === 'on') {
    body.classList.add('dark-mode');
    if (toggle) toggle.textContent = '☀️';
  }
  if (toggle) {
    toggle.addEventListener('click', () => {
      body.classList.toggle('dark-mode');
      const isDark = body.classList.contains('dark-mode');
      localStorage.setItem('darkMode', isDark ? 'on' : 'off');
      toggle.textContent = isDark ? '☀️' : '🌙';
    });
  }

  // ── Auto-dismiss alerts ────────────────────────────────
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      try { bootstrap.Alert.getOrCreateInstance(alert).close(); } catch(e) {}
    }, 4000);
  });

  // ── Quantity input guard ───────────────────────────────
  document.querySelectorAll('input[name="quantity"]').forEach(input => {
    input.addEventListener('change', function () {
      if (parseInt(this.value) < 1) this.value = 1;
    });
  });

  // ── Broken image fallback ──────────────────────────────
  document.querySelectorAll('.product-img, .pop-card-img, .blog-card-img').forEach(img => {
    if (img.tagName === 'IMG') {
      img.onerror = function() {
        this.src = 'https://placehold.co/400x400/f2ede6/888?text=No+Image';
        this.onerror = null;
      };
    }
  });

});

// ── Sidebar drawer ─────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const menuBtn = document.getElementById('menuBtn');
  if (!sidebar) return;
  const isOpen = sidebar.classList.contains('open');
  sidebar.classList.toggle('open', !isOpen);
  overlay.classList.toggle('open', !isOpen);
  document.body.style.overflow = isOpen ? '' : 'hidden';
  // Animate hamburger to X
  if (menuBtn) {
    const spans = menuBtn.querySelectorAll('span');
    if (!isOpen) {
      spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
      spans[1].style.opacity = '0';
      spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
    } else {
      spans[0].style.transform = '';
      spans[1].style.opacity = '';
      spans[2].style.transform = '';
    }
  }
}

// ── Admin login toggle ─────────────────────────────────
function toggleAdmin(e) {
  e.preventDefault();
  const box = document.getElementById('admin-login-box');
  if (box) box.style.display = box.style.display === 'none' ? 'block' : 'none';
}
