// Orationes App Core Engine

(function () {
  'use strict';

  let currentPrayerId = null;
  let currentLang = 'pt';
  let currentFontSize = parseInt(localStorage.getItem('orationes_font_size') || '15', 10);
  let userTheme = localStorage.getItem('orationes_theme') || 'auto'; // 'auto', 'light', 'dark'

  // Initialize theme
  applyTheme(userTheme);

  // Initialize font size
  applyFontSize(currentFontSize);

  // Listen to system theme changes if set to auto
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (userTheme === 'auto') {
      applyTheme('auto');
    }
  });

  // Listen to hash changes (SPA Router)
  window.addEventListener('hashchange', handleRoute);
  window.addEventListener('DOMContentLoaded', () => {
    handleRoute();
  });

  function handleRoute() {
    const hash = window.location.hash.replace('#', '').trim();
    if (hash && window.ORATIONES_DATA && window.ORATIONES_DATA[hash]) {
      loadPrayer(hash);
    } else {
      showHome();
    }
  }

  function showHome() {
    currentPrayerId = null;
    document.getElementById('homeView').style.display = 'block';
    document.getElementById('prayerView').style.display = 'none';
    document.getElementById('navBrand').textContent = 'Orationes';
    document.getElementById('navBrand').href = '#';
    document.getElementById('langSelect').style.display = 'none';
    document.title = 'Orationes & Officium Divinum';
  }

  function loadPrayer(prayerId) {
    currentPrayerId = prayerId;
    const data = window.ORATIONES_DATA[prayerId];
    if (!data) return;

    document.getElementById('homeView').style.display = 'none';
    document.getElementById('prayerView').style.display = 'block';
    document.getElementById('navBrand').innerHTML = `← ${data.title.la}`;
    document.getElementById('navBrand').href = '#';

    // Populate language selector for this specific prayer
    const langSelect = document.getElementById('langSelect');
    langSelect.innerHTML = '';
    langSelect.style.display = 'inline-block';

    // Add available vernacular languages
    if (data.availableLangs && data.availableLangs.length > 0) {
      data.availableLangs.forEach(lang => {
        const opt = document.createElement('option');
        opt.value = lang.code;
        opt.textContent = lang.label;
        if (lang.code === currentLang) opt.selected = true;
        langSelect.appendChild(opt);
      });
    }

    // Add Latin Only option
    const latOpt = document.createElement('option');
    latOpt.value = 'none';
    latOpt.textContent = 'Latim';
    if (currentLang === 'none') latOpt.selected = true;
    langSelect.appendChild(latOpt);

    // If current selected lang is not in this prayer's available langs, fallback to first available or 'pt'
    if (currentLang !== 'none' && !data.availableLangs.some(l => l.code === currentLang)) {
      currentLang = data.availableLangs[0] ? data.availableLangs[0].code : 'none';
      langSelect.value = currentLang;
    }

    renderPrayerView(data);
  }

  function renderPrayerView(data) {
    const isSingle = currentLang === 'none';
    document.body.classList.toggle('single-col', isSingle);

    // Titles
    const titleVern = !isSingle && data.title[currentLang] ? ` • ${data.title[currentLang]}` : '';
    document.getElementById('prayerTitle').textContent = `${data.title.la}${titleVern}`;
    document.title = `${data.title.la} • Orationes`;

    const subVern = !isSingle && data.subtitle && data.subtitle[currentLang] ? ` / ${data.subtitle[currentLang]}` : '';
    document.getElementById('prayerSubtitle').textContent = data.subtitle ? `${data.subtitle.la}${subVern}` : '';

    const body = document.getElementById('prayerBody');
    let html = '';

    for (const item of data.items) {
      if (item.type === 'section_header') {
        const titlePt = !isSingle && item.title[currentLang] ? ` • ${item.title[currentLang]}` : '';
        const sub = item.sub ? `<div class="rubric" style="text-align:center; margin-bottom: 2px;">${item.sub}</div>` : '';
        html += `
          <tr>
            <td colspan="${isSingle ? 1 : 2}" style="padding: 14px 2px 4px 2px; border-bottom: none;">
              <h2 class="section-title">${item.title.la}${titlePt}</h2>
              ${sub}
            </td>
          </tr>
        `;
      } else if (item.type === 'psalm_title') {
        html += `
          <tr>
            <td colspan="${isSingle ? 1 : 2}" style="padding: 8px 2px 2px 2px; border-bottom: none;">
              <h3 class="psalm-title">${item.title}</h3>
            </td>
          </tr>
        `;
      } else if (item.type === 'rubric') {
        const textPt = !isSingle && item.text[currentLang] ? `<div style="margin-top: 2px; opacity: 0.9;">${item.text[currentLang]}</div>` : '';
        html += `
          <tr>
            <td colspan="${isSingle ? 1 : 2}" style="text-align:center; padding: 6px 4px;" class="rubric">
              <div>${item.text.la}</div>
              ${textPt}
            </td>
          </tr>
        `;
      } else if (item.type === 'dialogue') {
        html += `
          <tr>
            <td class="col-lat"><span class="v-sym">℣.</span> ${item.v.la}</td>
            <td class="col-vern"><span class="v-sym">℣.</span> ${item.v[currentLang] || ''}</td>
          </tr>
          <tr>
            <td class="col-lat"><span class="r-sym">℟.</span> ${item.r.la}</td>
            <td class="col-vern"><span class="r-sym">℟.</span> ${item.r[currentLang] || ''}</td>
          </tr>
        `;
      } else if (item.type === 'prayer' || item.type === 'prayer_ref') {
        const italic = item.type === 'prayer_ref' ? 'font-style: italic;' : '';
        html += `
          <tr>
            <td class="col-lat" style="${italic}">${item.text.la}</td>
            <td class="col-vern" style="${italic}">${item.text[currentLang] || ''}</td>
          </tr>
        `;
      } else if (item.type === 'hymn_stanza') {
        html += `
          <tr>
            <td class="col-lat" style="padding-bottom: 8px;">${item.text.la}</td>
            <td class="col-vern" style="padding-bottom: 8px;">${item.text[currentLang] || ''}</td>
          </tr>
        `;
      } else if (item.type === 'oratio') {
        html += `
          <tr>
            <td class="col-lat">
              <strong>${item.label.la}</strong><br>
              ${item.text.la}<br>
              <span class="r-sym">${item.amen.la}</span>
            </td>
            <td class="col-vern">
              <strong>${item.label[currentLang] || ''}</strong><br>
              ${item.text[currentLang] || ''}<br>
              <span class="r-sym">${item.amen[currentLang] || ''}</span>
            </td>
          </tr>
        `;
      } else if (item.type === 'psalm_verse') {
        const numSpan = item.num ? `<span class="v-num">${item.num}</span> ` : '';
        html += `
          <tr>
            <td class="col-lat">${numSpan}${item.text.la}</td>
            <td class="col-vern">${numSpan}${item.text[currentLang] || ''}</td>
          </tr>
        `;
      }
    }

    body.innerHTML = html;

    // Render prayer specific source/footer
    const footer = document.getElementById('prayerFooter');
    if (footer) {
      if (data.sources && data.sources.length > 0) {
        const srcLinks = data.sources.map(s => {
          if (s.url) {
            return `<a href="${s.url}" target="_blank" rel="noopener" style="color: var(--rubric-color); text-decoration: none;">${s.name}</a>`;
          }
          return s.name;
        }).join(', ');
        footer.innerHTML = `<p>Fonte: ${srcLinks}</p>`;
        footer.style.display = 'block';
      } else {
        footer.innerHTML = '';
        footer.style.display = 'none';
      }
    }
  }

  // Language Change
  window.changeLanguage = function (lang) {
    currentLang = lang;
    if (currentPrayerId && window.ORATIONES_DATA[currentPrayerId]) {
      renderPrayerView(window.ORATIONES_DATA[currentPrayerId]);
    }
  };

  // Font Size Adjustments
  window.adjustFont = function (delta) {
    currentFontSize = Math.max(12, Math.min(24, currentFontSize + delta));
    applyFontSize(currentFontSize);
    localStorage.setItem('orationes_font_size', currentFontSize);
  };

  function applyFontSize(size) {
    document.documentElement.style.setProperty('--font-size', size + 'px');
  }

  // Theme Management (3-state cycle: auto -> dark -> light -> auto)
  window.toggleTheme = function () {
    if (userTheme === 'auto') {
      userTheme = 'dark';
    } else if (userTheme === 'dark') {
      userTheme = 'light';
    } else {
      userTheme = 'auto';
    }

    applyTheme(userTheme);
    if (userTheme === 'auto') {
      localStorage.removeItem('orationes_theme');
    } else {
      localStorage.setItem('orationes_theme', userTheme);
    }
  };

  function applyTheme(theme) {
    const html = document.documentElement;
    const btn = document.getElementById('themeBtn');

    if (theme === 'auto') {
      html.removeAttribute('data-theme');
      if (btn) {
        btn.textContent = '🌓';
        btn.title = 'Tema: Automático (seguindo o dispositivo)';
      }
    } else if (theme === 'dark') {
      html.setAttribute('data-theme', 'dark');
      if (btn) {
        btn.textContent = '🌙';
        btn.title = 'Tema: Escuro';
      }
    } else {
      html.setAttribute('data-theme', 'light');
      if (btn) {
        btn.textContent = '☀️';
        btn.title = 'Tema: Claro';
      }
    }
  }

})();
