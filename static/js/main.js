(() => {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.main-nav');
  if (toggle && nav) toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('nav-open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Tutup navigasi' : 'Buka navigasi');
  });
  document.querySelectorAll('.flash-close').forEach(btn => btn.addEventListener('click', () => btn.closest('.flash')?.remove()));
})();
