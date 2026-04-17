/**
 * Week 5 Phase G-2 — 통합 검색 자동완성 컴포넌트.
 *
 * 사용 예:
 *   <div id="unified-search"></div>
 *   <script src="/propmap/js/unified-search.js"></script>
 *   <script>
 *     const ui = new UnifiedSearch({
 *       mountEl: document.getElementById('unified-search'),
 *       placeholder: '지번 · 도로명 · 건물명 검색',
 *       onSelect: (item) => {
 *         // item.type: 'complex' | 'jibun' | 'road' | 'coord'
 *       },
 *       endpoint: '/api/search/unified',  // 기본값
 *       debounceMs: 250,
 *       minChars: 2,
 *     });
 *   </script>
 *
 * 의존성: 없음 (바닐라 JS).
 */
(function () {
  'use strict';

  const DEFAULTS = {
    endpoint: '/api/search/unified',
    placeholder: '지번 · 도로명 · 건물명으로 검색',
    debounceMs: 250,
    minChars: 2,
    limit: 10,
  };

  function createEl(tag, props = {}) {
    const el = document.createElement(tag);
    Object.entries(props).forEach(([k, v]) => {
      if (k === 'className') el.className = v;
      else if (k === 'style') Object.assign(el.style, v);
      else if (k === 'onClick') el.addEventListener('click', v);
      else if (k === 'textContent') el.textContent = v;
      else el.setAttribute(k, v);
    });
    return el;
  }

  class UnifiedSearch {
    constructor(opts) {
      this.opts = Object.assign({}, DEFAULTS, opts || {});
      if (!this.opts.mountEl) {
        throw new Error('UnifiedSearch: mountEl required');
      }
      this.onSelect = this.opts.onSelect || (() => {});
      this.results = [];
      this.activeIdx = -1;
      this.debounceTimer = null;
      this.lastQuery = '';
      this.injectStyles();
      this.render();
    }

    injectStyles() {
      if (document.getElementById('unified-search-style')) return;
      const css = `
.unified-search { position: relative; width: 100%; max-width: 480px; font-family: inherit; }
.unified-search-input {
  width: 100%; box-sizing: border-box;
  padding: 10px 36px 10px 14px;
  font-size: 15px; border: 1px solid #d1d5db;
  border-radius: 10px; outline: none;
  background: #fff;
  transition: border-color 0.15s ease;
}
.unified-search-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }
.unified-search-clear {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; color: #9ca3af;
  font-size: 18px; padding: 2px 6px; display: none;
}
.unified-search-clear.visible { display: block; }
.unified-search-dropdown {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  max-height: 420px; overflow-y: auto; z-index: 10000;
  display: none;
}
.unified-search-dropdown.visible { display: block; }
.unified-search-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 12px; cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.1s ease;
}
.unified-search-item:last-child { border-bottom: none; }
.unified-search-item:hover,
.unified-search-item.active { background: #f0f9ff; }
.unified-search-icon { font-size: 20px; line-height: 1.2; flex-shrink: 0; }
.unified-search-text { flex: 1; min-width: 0; }
.unified-search-label {
  font-weight: 600; color: #111827; font-size: 14px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.unified-search-sublabel {
  color: #6b7280; font-size: 12px; margin-top: 2px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.unified-search-empty, .unified-search-loading {
  padding: 14px; text-align: center; color: #9ca3af; font-size: 13px;
}
.unified-search-footer {
  padding: 6px 12px; font-size: 11px; color: #9ca3af;
  text-align: right; border-top: 1px solid #f3f4f6;
}
      `.trim();
      const style = document.createElement('style');
      style.id = 'unified-search-style';
      style.textContent = css;
      document.head.appendChild(style);
    }

    render() {
      const wrap = createEl('div', { className: 'unified-search' });
      const input = createEl('input', {
        className: 'unified-search-input',
        type: 'text',
        placeholder: this.opts.placeholder,
        autocomplete: 'off',
        spellcheck: 'false',
      });
      const clearBtn = createEl('button', {
        className: 'unified-search-clear',
        type: 'button',
        'aria-label': '지우기',
      });
      clearBtn.innerHTML = '&times;';
      const dropdown = createEl('div', { className: 'unified-search-dropdown' });

      wrap.appendChild(input);
      wrap.appendChild(clearBtn);
      wrap.appendChild(dropdown);
      this.opts.mountEl.appendChild(wrap);

      this.inputEl = input;
      this.clearEl = clearBtn;
      this.dropdownEl = dropdown;

      input.addEventListener('input', () => this.onInput());
      input.addEventListener('keydown', (e) => this.onKeyDown(e));
      input.addEventListener('focus', () => {
        if (this.results.length) this.showDropdown();
      });
      document.addEventListener('click', (e) => {
        if (!wrap.contains(e.target)) this.hideDropdown();
      });

      clearBtn.addEventListener('click', () => {
        input.value = '';
        this.lastQuery = '';
        this.results = [];
        this.activeIdx = -1;
        this.hideDropdown();
        this.clearEl.classList.remove('visible');
        input.focus();
      });
    }

    onInput() {
      const q = this.inputEl.value.trim();
      this.clearEl.classList.toggle('visible', q.length > 0);

      if (q.length < this.opts.minChars) {
        this.results = [];
        this.hideDropdown();
        return;
      }
      if (q === this.lastQuery) return;
      this.lastQuery = q;

      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => this.fetchResults(q), this.opts.debounceMs);
    }

    async fetchResults(q) {
      this.showLoading();
      try {
        const url = `${this.opts.endpoint}?q=${encodeURIComponent(q)}&limit=${this.opts.limit}`;
        const resp = await fetch(url, { credentials: 'same-origin' });
        const data = await resp.json();
        if (this.lastQuery !== q) return; // 이미 다른 쿼리가 진행 중
        if (!data.success) {
          this.showEmpty('검색 실패: ' + (data.error || '알 수 없는 오류'));
          return;
        }
        this.results = data.results || [];
        this.activeIdx = -1;
        this.renderResults(data);
      } catch (e) {
        console.warn('[UnifiedSearch]', e);
        this.showEmpty('네트워크 오류');
      }
    }

    renderResults(data) {
      const dd = this.dropdownEl;
      dd.innerHTML = '';
      if (!this.results.length) {
        this.showEmpty('검색 결과가 없습니다');
        return;
      }
      this.results.forEach((r, idx) => {
        const item = createEl('div', {
          className: 'unified-search-item',
          'data-idx': idx,
        });
        item.innerHTML = `
          <span class="unified-search-icon">${r.icon || '•'}</span>
          <span class="unified-search-text">
            <div class="unified-search-label">${escapeHtml(r.label || '')}</div>
            <div class="unified-search-sublabel">${escapeHtml(r.sublabel || '')}</div>
          </span>
        `;
        item.addEventListener('mouseenter', () => this.setActive(idx));
        item.addEventListener('click', () => this.selectItem(idx));
        dd.appendChild(item);
      });
      // 푸터에 응답 시간 표시
      if (typeof data.elapsed_ms === 'number') {
        const footer = createEl('div', {
          className: 'unified-search-footer',
          textContent: `${this.results.length}건 · ${data.elapsed_ms}ms · ${data.detected_type}`,
        });
        dd.appendChild(footer);
      }
      this.showDropdown();
    }

    setActive(idx) {
      this.activeIdx = idx;
      const items = this.dropdownEl.querySelectorAll('.unified-search-item');
      items.forEach((el, i) => el.classList.toggle('active', i === idx));
    }

    selectItem(idx) {
      const r = this.results[idx];
      if (!r) return;
      this.inputEl.value = r.label;
      this.lastQuery = r.label;
      this.hideDropdown();
      try {
        this.onSelect(r);
      } catch (e) {
        console.error('[UnifiedSearch.onSelect]', e);
      }
    }

    onKeyDown(e) {
      if (!this.dropdownEl.classList.contains('visible')) return;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        const next = Math.min(this.activeIdx + 1, this.results.length - 1);
        this.setActive(next);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        const prev = Math.max(this.activeIdx - 1, 0);
        this.setActive(prev);
      } else if (e.key === 'Enter') {
        if (this.activeIdx >= 0) {
          e.preventDefault();
          this.selectItem(this.activeIdx);
        } else if (this.results.length > 0) {
          e.preventDefault();
          this.selectItem(0);
        }
      } else if (e.key === 'Escape') {
        this.hideDropdown();
      }
    }

    showLoading() {
      this.dropdownEl.innerHTML = '<div class="unified-search-loading">검색 중...</div>';
      this.showDropdown();
    }

    showEmpty(msg) {
      this.dropdownEl.innerHTML = `<div class="unified-search-empty">${escapeHtml(msg)}</div>`;
      this.showDropdown();
    }

    showDropdown() {
      this.dropdownEl.classList.add('visible');
    }

    hideDropdown() {
      this.dropdownEl.classList.remove('visible');
    }

    setValue(v) {
      this.inputEl.value = v;
    }
  }

  function escapeHtml(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // 전역 노출
  window.UnifiedSearch = UnifiedSearch;
})();
