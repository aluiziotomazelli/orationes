import { describe, it, expect, beforeEach } from 'vitest';
import { JSDOM } from 'jsdom';
import fs from 'fs';
import path from 'path';

const htmlPath = path.resolve(__dirname, '../index.html');
const angelusJsPath = path.resolve(__dirname, '../data/prayers/angelus.js');
const completoriumJsPath = path.resolve(__dirname, '../data/prayers/completorium.js');
const appJsPath = path.resolve(__dirname, '../app.js');

function createTestEnvironment(initialHash = '') {
  const html = fs.readFileSync(htmlPath, 'utf-8');
  const dom = new JSDOM(html, {
    runScripts: 'dangerously',
    url: `http://localhost/#${initialHash}`
  });

  const { window } = dom;

  // Mock matchMedia for JSDOM
  window.matchMedia = window.matchMedia || function(query) {
    return {
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false
    };
  };

  // Execute prayer data scripts in window context
  window.eval(fs.readFileSync(angelusJsPath, 'utf-8'));
  window.eval(fs.readFileSync(completoriumJsPath, 'utf-8'));
  window.eval(fs.readFileSync(appJsPath, 'utf-8'));

  // Trigger DOMContentLoaded
  window.document.dispatchEvent(new window.Event('DOMContentLoaded'));

  return { dom, window, document: window.document };
}

describe('Orationes App Engine (app.js)', () => {

  describe('Home View & Initialization', () => {
    it('should display home view and hide prayer view by default', () => {
      const { document } = createTestEnvironment();
      const homeView = document.getElementById('homeView');
      const prayerView = document.getElementById('prayerView');
      const navBrand = document.getElementById('navBrand');

      expect(homeView.style.display).toBe('block');
      expect(prayerView.style.display).toBe('none');
      expect(navBrand.textContent).toBe('Orationes');
    });
  });

  describe('Font Sizing', () => {
    it('should adjust font size up and down within limits (12px - 24px)', () => {
      const { window, document } = createTestEnvironment();

      // Default is 15px
      expect(document.documentElement.style.getPropertyValue('--font-size')).toBe('15px');

      // Increase font
      window.adjustFont(1);
      expect(document.documentElement.style.getPropertyValue('--font-size')).toBe('16px');
      expect(window.localStorage.getItem('orationes_font_size')).toBe('16');

      // Try decreasing below minimum (12px)
      window.adjustFont(-10);
      expect(document.documentElement.style.getPropertyValue('--font-size')).toBe('12px');

      // Try increasing above maximum (24px)
      window.adjustFont(50);
      expect(document.documentElement.style.getPropertyValue('--font-size')).toBe('24px');
    });
  });

  describe('Theme 3-State Cycle', () => {
    it('should cycle through Auto -> Dark -> Light -> Auto', () => {
      const { window, document } = createTestEnvironment();
      const themeBtn = document.getElementById('themeBtn');

      // Initial state: auto
      expect(document.documentElement.getAttribute('data-theme')).toBeNull();
      expect(themeBtn.textContent).toBe('🌓');

      // 1. Auto -> Dark
      window.toggleTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
      expect(themeBtn.textContent).toBe('🌙');
      expect(window.localStorage.getItem('orationes_theme')).toBe('dark');

      // 2. Dark -> Light
      window.toggleTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBe('light');
      expect(themeBtn.textContent).toBe('☀️');
      expect(window.localStorage.getItem('orationes_theme')).toBe('light');

      // 3. Light -> Auto
      window.toggleTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBeNull();
      expect(themeBtn.textContent).toBe('🌓');
      expect(window.localStorage.getItem('orationes_theme')).toBeNull();
    });
  });

  describe('Routing & Prayer Rendering', () => {
    it('should load and render Angelus correctly', () => {
      const { window, document } = createTestEnvironment('angelus');

      const homeView = document.getElementById('homeView');
      const prayerView = document.getElementById('prayerView');
      const prayerTitle = document.getElementById('prayerTitle');
      const prayerFooter = document.getElementById('prayerFooter');
      const prayerBody = document.getElementById('prayerBody');

      expect(homeView.style.display).toBe('none');
      expect(prayerView.style.display).toBe('block');
      expect(prayerTitle.textContent).toContain('Angelus Dómini');
      expect(prayerFooter.innerHTML).toContain('Breviarium Romanum');
      expect(prayerBody.querySelectorAll('tr').length).toBeGreaterThan(0);
    });

    it('should load and render Completorium correctly', () => {
      const { window, document } = createTestEnvironment('completorium');

      const prayerTitle = document.getElementById('prayerTitle');
      const prayerFooter = document.getElementById('prayerFooter');

      expect(prayerTitle.textContent).toContain('Ad Completorium');
      expect(prayerFooter.innerHTML).toContain('Divinum Officium');
    });

    it('should toggle single-column Latin mode when language is set to none', () => {
      const { window, document } = createTestEnvironment('angelus');

      expect(document.body.classList.contains('single-col')).toBe(false);

      window.changeLanguage('none');
      expect(document.body.classList.contains('single-col')).toBe(true);

      window.changeLanguage('pt');
      expect(document.body.classList.contains('single-col')).toBe(false);
    });
  });

});
