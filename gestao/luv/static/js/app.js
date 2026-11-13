// Utilitários pequenos compartilhados pelas telas.
const Luv = {
  numero(txt) {
    if (txt == null) return NaN;
    let t = String(txt).trim().replace(/R\$|\s/g, '');
    if (!t) return NaN;
    if (t.includes(',')) t = t.replace(/\./g, '').replace(',', '.');
    else if ((t.match(/\./g) || []).length > 1) t = t.replace(/\./g, '');
    else if (/^\-?[1-9]\d*\.\d{3}$/.test(t)) t = t.replace('.', '');
    return parseFloat(t);
  },
  centavos(txt) {
    const n = Luv.numero(txt);
    return isNaN(n) ? NaN : Math.round(n * 100);
  },
  brl(c) {
    const v = (c || 0) / 100;
    const s = Math.abs(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return (v < -0.004 ? '−' : '') + 'R$ ' + s;
  },
  paraTexto(c) {
    return ((c || 0) / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },
  qtd(v, u) {
    if (u === 'g' && Math.abs(v) >= 1000) return (v / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 2 }) + ' kg';
    if (u === 'ml' && Math.abs(v) >= 1000) return (v / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 2 }) + ' L';
    return v.toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' ' + u;
  },
};

// Avisos somem sozinhos.
document.querySelectorAll('.toast').forEach((t, i) => {
  setTimeout(() => { t.classList.add('some'); setTimeout(() => t.remove(), 400); }, 3800 + i * 400);
});

// Confirmação antes de ações destrutivas.
document.addEventListener('submit', e => {
  const msg = e.target.dataset.confirmar;
  if (msg && !confirm(msg)) e.preventDefault();
});

// Diálogos: <button data-abrir="id-do-dialog">, campos preenchidos por data-set-*.
document.addEventListener('click', e => {
  const b = e.target.closest('[data-abrir]');
  if (b) {
    const d = document.getElementById(b.dataset.abrir);
    if (!d) return;
    if (b.dataset.acao) d.querySelector('form').action = b.dataset.acao;
    for (const [k, v] of Object.entries(b.dataset)) {
      if (!k.startsWith('set')) continue;
      const nome = k.slice(3).replace(/^./, c => c.toLowerCase());
      d.querySelectorAll(`[data-campo="${nome}"]`).forEach(el => {
        if ('value' in el && el.tagName !== 'SPAN') el.value = v; else el.textContent = v;
      });
    }
    d.showModal();
  }
  if (e.target.closest('[data-fechar]')) e.target.closest('dialog').close();
  const t = e.target.closest('[data-toggle]');
  if (t) {
    t.classList.toggle('aberto');
    document.querySelectorAll(`[data-grupo="${t.dataset.toggle}"]`).forEach(r => r.classList.toggle('hidden'));
  }
});
document.querySelectorAll('dialog').forEach(d => d.addEventListener('click', e => { if (e.target === d) d.close(); }));
