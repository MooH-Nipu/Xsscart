/* XssCart — main.js */

// ── Hint accordion ─────────────────────────────────────────────
document.querySelectorAll('.hint-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const body = btn.nextElementSibling;
    const open = btn.classList.toggle('open');
    body.style.display = open ? 'block' : 'none';
    btn.textContent = (open ? '▼ ' : '▶ ') + btn.dataset.label;
  });
});

// ── Typing effect on auth logo ─────────────────────────────────
(function typingEffect() {
  const el = document.querySelector('[data-typing]');
  if (!el) return;
  const text = el.dataset.typing;
  el.textContent = '';
  el.classList.add('cursor');
  let i = 0;
  const iv = setInterval(() => {
    el.textContent += text[i++];
    if (i >= text.length) clearInterval(iv);
  }, 80);
})();

// ── Animate XP bar ────────────────────────────────────────────
(function xpAnim() {
  const fill = document.querySelector('.xp-bar__fill');
  if (!fill) return;
  const target = fill.dataset.pct || '0';
  fill.style.width = '0%';
  setTimeout(() => { fill.style.width = target + '%'; }, 200);
})();

// ── Level card hover sound effect (visual feedback) ───────────
document.querySelectorAll('.level-card').forEach(card => {
  card.addEventListener('mouseenter', () => {
    card.style.borderColor = card.dataset.color || 'var(--green)';
  });
  card.addEventListener('mouseleave', () => {
    card.style.borderColor = '';
  });
});

// ── Alert auto-hide ────────────────────────────────────────────
document.querySelectorAll('.alert[data-autohide]').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity 0.5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  }, 4000);
});

// ── Payload char counter ───────────────────────────────────────
const payloadInput = document.querySelector('.payload-input');
if (payloadInput) {
  const counter = document.querySelector('#payload-counter');
  payloadInput.addEventListener('input', () => {
    if (counter) counter.textContent = payloadInput.value.length + ' chars';
  });
}
