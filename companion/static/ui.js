// Gemeinsame UI-Helfer: Meldungen (Toast), Bestaetigungsdialog, Fehlerbehandlung.
import { ApiError } from './api.js';
import { T, S, esc } from './i18n.js';

const TOAST_MS = 3500;
const TOAST_ERROR_MS = 7000;

// Kante .toast; its life line shrinks over --life, so the timer and the line agree.
export function toast(html, kind) {
  const host = document.getElementById('toasts');
  const ms = kind === 'error' ? TOAST_ERROR_MS : TOAST_MS;
  const el = document.createElement('div');
  el.className = 'toast';
  if (kind) el.dataset.kind = kind;
  el.innerHTML = `<span>${html}</span><span class="toast-life" style="--life:${ms}ms" aria-hidden="true"></span>`;
  host.appendChild(el);
  setTimeout(() => el.remove(), ms);
}

// Fuehrt einen API-Aufruf aus und zeigt Fehler verstaendlich an. Gibt bei Erfolg das
// Ergebnis zurueck, bei Fehler null.
export async function guard(fn, onLocked) {
  try {
    return await fn();
  } catch (e) {
    if (e instanceof ApiError) {
      if (e.status === 409 && e.data.busy) toast(T('err_busy'), 'error');
      else if (e.status === 409) { toast(T('err_locked'), 'error'); if (onLocked) onLocked(); }
      else toast(T('err_generic', e.message), 'error');
    } else {
      toast(T('err_generic', e && e.message), 'error');
    }
    return null;
  }
}

// Bestaetigungsdialog im Stil des Designsystems. Liefert true/false.
export function dialog({ title, body, facts, notes, confirm, cancel = 'cancel', danger }) {
  return new Promise((resolve) => {
    const host = document.getElementById('dialog-host');
    const wrap = document.createElement('div');
    wrap.className = 'scrim is-fixed';
    const factsHtml = facts && facts.length
      ? `<div class="dialog-facts">${facts.map((f) => `<div class="fact"${f.color ? ` data-k="${f.color}"` : ''}><b>${esc(f.value)}</b><span>${T(f.label)}</span></div>`).join('')}</div>`
      : '';
    const notesHtml = (notes || []).map((n) => `<div class="callout callout-warn">${n}</div>`).join('');
    wrap.innerHTML = `<div class="dialog" role="dialog" aria-modal="true" aria-labelledby="dlg-h">
      <h3 id="dlg-h">${T(title)}</h3><p>${T(body)}</p>${factsHtml}${notesHtml}
      <div class="dialog-actions"><button type="button" class="btn btn-outline" data-x="no">${T(cancel)}</button>
      <button type="button" class="btn btn-accent" data-x="yes">${T(confirm)}</button></div></div>`;
    const done = (v) => { document.removeEventListener('keydown', onKey, true); wrap.remove(); resolve(v); };
    const onKey = (e) => { if (e.key === 'Escape') { e.stopPropagation(); done(false); } };
    wrap.addEventListener('click', (e) => {
      const x = e.target.closest('[data-x]');
      if (x) done(x.dataset.x === 'yes');
      else if (e.target === wrap) done(false);
    });
    document.addEventListener('keydown', onKey, true);
    host.appendChild(wrap);
    wrap.querySelector('[data-x="yes"]').focus();
  });
}

// Kante's live value: the number counts to the new value and a cyan strip fades behind it.
// Falls back to plain text when shrippen.js is not there (no script, tests).
export function live(el, text) {
  if (window.Kante) window.Kante.tick(el, text);
  else el.textContent = text;
}

// Kante's fresh line: a 2px line runs once along the bottom edge of a surface with new data.
export function fresh(el) {
  if (window.Kante && el) window.Kante.fresh(el);
}

export const attrText = (key, ...a) => esc(S(key, ...a));
