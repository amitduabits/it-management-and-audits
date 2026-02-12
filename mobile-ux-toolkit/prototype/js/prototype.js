/* ============================================================
   PROTOTYPE.JS — Mobile UX Prototyping Toolkit
   Screen Transitions, Interactions & Prototype Behaviors
   ============================================================ */

(function () {
  'use strict';

  /* ────────────────────────────────────────────────────────────
     1. NAVIGATION & SCREEN TRANSITIONS
     ──────────────────────────────────────────────────────────── */

  const PrototypeNav = {
    init() {
      this.bindNavLinks();
      this.setActiveNavItem();
      this.initBackButtons();
    },

    bindNavLinks() {
      document.querySelectorAll('.bottom-nav__item').forEach(item => {
        item.addEventListener('click', function (e) {
          document.querySelectorAll('.bottom-nav__item').forEach(el => {
            el.classList.remove('bottom-nav__item--active');
          });
          this.classList.add('bottom-nav__item--active');
        });
      });
    },

    setActiveNavItem() {
      const currentPage = window.location.pathname.split('/').pop().replace('.html', '');
      document.querySelectorAll('.bottom-nav__item').forEach(item => {
        const href = item.getAttribute('href') || '';
        const itemPage = href.split('/').pop().replace('.html', '');
        if (itemPage === currentPage) {
          item.classList.add('bottom-nav__item--active');
        }
      });
    },

    initBackButtons() {
      document.querySelectorAll('.app-header__back').forEach(btn => {
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          const target = this.getAttribute('data-back') || this.getAttribute('href');
          if (target) {
            ScreenTransition.navigateTo(target, 'slide-right');
          } else {
            window.history.back();
          }
        });
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     2. SCREEN TRANSITION MANAGER
     ──────────────────────────────────────────────────────────── */

  const ScreenTransition = {
    isTransitioning: false,

    navigateTo(url, direction = 'slide-left') {
      if (this.isTransitioning) return;
      this.isTransitioning = true;

      const screen = document.querySelector('.screen');
      if (!screen) {
        window.location.href = url;
        return;
      }

      const animClass = direction === 'slide-right'
        ? 'screen-exit-right'
        : 'screen-exit-left';

      screen.style.transition = 'transform 300ms ease-in-out, opacity 300ms ease-in-out';
      screen.style.transform = direction === 'slide-right'
        ? 'translateX(30px)'
        : 'translateX(-30px)';
      screen.style.opacity = '0';

      setTimeout(() => {
        window.location.href = url;
      }, 200);
    }
  };


  /* ────────────────────────────────────────────────────────────
     3. BUTTON INTERACTIONS
     ──────────────────────────────────────────────────────────── */

  const ButtonEffects = {
    init() {
      document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', this.createRipple);
      });
    },

    createRipple(e) {
      const btn = e.currentTarget;
      const existing = btn.querySelector('.ripple');
      if (existing) existing.remove();

      const ripple = document.createElement('span');
      ripple.classList.add('ripple');

      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
      ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';

      btn.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    }
  };


  /* ────────────────────────────────────────────────────────────
     4. PIN INPUT
     ──────────────────────────────────────────────────────────── */

  const PinInput = {
    init() {
      const pinGroups = document.querySelectorAll('.pin-input-group');
      pinGroups.forEach(group => {
        const inputs = group.querySelectorAll('.pin-input');
        inputs.forEach((input, index) => {
          input.addEventListener('input', function () {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 1);
            if (this.value && index < inputs.length - 1) {
              inputs[index + 1].focus();
            }
            this.classList.toggle('pin-input--filled', this.value !== '');

            // Check if all filled
            const allFilled = Array.from(inputs).every(inp => inp.value);
            if (allFilled) {
              group.dispatchEvent(new CustomEvent('pin-complete', {
                detail: { pin: Array.from(inputs).map(i => i.value).join('') }
              }));
            }
          });

          input.addEventListener('keydown', function (e) {
            if (e.key === 'Backspace' && !this.value && index > 0) {
              inputs[index - 1].focus();
              inputs[index - 1].value = '';
              inputs[index - 1].classList.remove('pin-input--filled');
            }
          });

          input.addEventListener('focus', function () {
            this.select();
          });
        });
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     5. TAB SWITCHING
     ──────────────────────────────────────────────────────────── */

  const Tabs = {
    init() {
      // Standard tabs
      document.querySelectorAll('.tabs').forEach(tabGroup => {
        const tabs = tabGroup.querySelectorAll('.tab');
        tabs.forEach(tab => {
          tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('tab--active'));
            tab.classList.add('tab--active');

            const targetId = tab.getAttribute('data-tab');
            if (targetId) {
              this.showTabContent(tabGroup, targetId);
            }
          });
        });
      });

      // Pill tabs
      document.querySelectorAll('.pill-tabs').forEach(tabGroup => {
        const pills = tabGroup.querySelectorAll('.pill-tab');
        pills.forEach(pill => {
          pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('pill-tab--active'));
            pill.classList.add('pill-tab--active');

            const targetId = pill.getAttribute('data-tab');
            if (targetId) {
              this.showTabContent(tabGroup, targetId);
            }
          });
        });
      });
    },

    showTabContent(tabGroup, targetId) {
      const container = tabGroup.closest('[data-tab-container]') || tabGroup.parentElement;
      container.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('tab-panel--active');
        panel.style.display = 'none';
      });

      const target = document.getElementById(targetId);
      if (target) {
        target.classList.add('tab-panel--active');
        target.style.display = '';
        target.style.animation = 'fadeIn 250ms ease-out';
      }
    }
  };


  /* ────────────────────────────────────────────────────────────
     6. BOTTOM SHEET
     ──────────────────────────────────────────────────────────── */

  const BottomSheet = {
    init() {
      document.querySelectorAll('[data-sheet-trigger]').forEach(trigger => {
        trigger.addEventListener('click', () => {
          const sheetId = trigger.getAttribute('data-sheet-trigger');
          this.open(sheetId);
        });
      });

      document.querySelectorAll('[data-sheet-close]').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
          const sheet = closeBtn.closest('.bottom-sheet');
          if (sheet) this.close(sheet.id);
        });
      });

      // Close on overlay click
      document.querySelectorAll('.overlay').forEach(overlay => {
        overlay.addEventListener('click', () => {
          const sheetId = overlay.getAttribute('data-overlay-for');
          if (sheetId) this.close(sheetId);
        });
      });
    },

    open(sheetId) {
      const sheet = document.getElementById(sheetId);
      const overlay = document.querySelector(`[data-overlay-for="${sheetId}"]`) ||
                      document.querySelector('.overlay');
      if (sheet) {
        sheet.classList.add('bottom-sheet--active');
        if (overlay) overlay.classList.add('overlay--active');
        document.body.style.overflow = 'hidden';
      }
    },

    close(sheetId) {
      const sheet = document.getElementById(sheetId);
      const overlay = document.querySelector(`[data-overlay-for="${sheetId}"]`) ||
                      document.querySelector('.overlay');
      if (sheet) {
        sheet.classList.remove('bottom-sheet--active');
        if (overlay) overlay.classList.remove('overlay--active');
        document.body.style.overflow = '';
      }
    }
  };


  /* ────────────────────────────────────────────────────────────
     7. TOAST NOTIFICATIONS
     ──────────────────────────────────────────────────────────── */

  const Toast = {
    container: null,

    init() {
      this.container = document.querySelector('.toast-container');
      if (!this.container) {
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
      }
    },

    show(message, type = 'default', duration = 3000) {
      const toast = document.createElement('div');
      toast.className = `toast toast--${type}`;

      const icons = {
        success: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        error: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        default: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
      };

      toast.innerHTML = `
        <span class="toast__icon">${icons[type] || icons.default}</span>
        <span class="toast__message">${message}</span>
        <button class="toast__close" aria-label="Dismiss">&times;</button>
      `;

      toast.querySelector('.toast__close').addEventListener('click', () => {
        toast.style.animation = 'fadeIn 200ms ease reverse forwards';
        setTimeout(() => toast.remove(), 200);
      });

      this.container.appendChild(toast);

      if (duration > 0) {
        setTimeout(() => {
          if (toast.parentNode) {
            toast.style.animation = 'fadeIn 200ms ease reverse forwards';
            setTimeout(() => toast.remove(), 200);
          }
        }, duration);
      }
    }
  };


  /* ────────────────────────────────────────────────────────────
     8. TOGGLE SWITCHES
     ──────────────────────────────────────────────────────────── */

  const Toggles = {
    init() {
      document.querySelectorAll('.toggle__input').forEach(input => {
        input.addEventListener('change', function () {
          const label = this.closest('.toggle');
          if (label) {
            label.dispatchEvent(new CustomEvent('toggle-change', {
              detail: { checked: this.checked }
            }));
          }
        });
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     9. FILTER CHIPS
     ──────────────────────────────────────────────────────────── */

  const FilterChips = {
    init() {
      document.querySelectorAll('.filter-row').forEach(row => {
        const chips = row.querySelectorAll('.filter-chip');
        chips.forEach(chip => {
          chip.addEventListener('click', () => {
            if (chip.getAttribute('data-filter-multi') !== 'true') {
              chips.forEach(c => c.classList.remove('filter-chip--active'));
            }
            chip.classList.toggle('filter-chip--active');

            const activeFilters = Array.from(row.querySelectorAll('.filter-chip--active'))
              .map(c => c.getAttribute('data-filter') || c.textContent.trim());

            row.dispatchEvent(new CustomEvent('filter-change', {
              detail: { filters: activeFilters }
            }));
          });
        });
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     10. AMOUNT FORMATTER
     ──────────────────────────────────────────────────────────── */

  const AmountFormatter = {
    init() {
      document.querySelectorAll('[data-amount-input]').forEach(input => {
        input.addEventListener('input', function () {
          let value = this.value.replace(/[^0-9.]/g, '');
          const parts = value.split('.');
          if (parts.length > 2) {
            value = parts[0] + '.' + parts.slice(1).join('');
          }
          if (parts[1] && parts[1].length > 2) {
            value = parts[0] + '.' + parts[1].slice(0, 2);
          }
          this.value = value;
        });

        input.addEventListener('blur', function () {
          if (this.value && !isNaN(parseFloat(this.value))) {
            const num = parseFloat(this.value);
            this.setAttribute('data-raw-value', num);
          }
        });
      });
    },

    format(amount, currency = '$') {
      const num = parseFloat(amount);
      if (isNaN(num)) return currency + '0.00';
      return currency + num.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     11. SEARCH FUNCTIONALITY
     ──────────────────────────────────────────────────────────── */

  const Search = {
    init() {
      document.querySelectorAll('.search-bar__input').forEach(input => {
        let debounceTimer;
        input.addEventListener('input', function () {
          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(() => {
            const query = this.value.trim().toLowerCase();
            const container = this.closest('[data-search-container]') ||
                              this.closest('.screen-content');
            if (container) {
              Search.filterItems(container, query);
            }
          }, 200);
        });
      });
    },

    filterItems(container, query) {
      const items = container.querySelectorAll('[data-search-text]');
      let visibleCount = 0;

      items.forEach(item => {
        const text = (item.getAttribute('data-search-text') || item.textContent).toLowerCase();
        const match = !query || text.includes(query);
        item.style.display = match ? '' : 'none';
        if (match) visibleCount++;
      });

      // Show/hide empty state
      const emptyState = container.querySelector('.empty-state');
      if (emptyState) {
        emptyState.style.display = (visibleCount === 0 && query) ? 'flex' : 'none';
      }
    }
  };


  /* ────────────────────────────────────────────────────────────
     12. ONBOARDING CAROUSEL
     ──────────────────────────────────────────────────────────── */

  const Onboarding = {
    currentSlide: 0,
    totalSlides: 0,

    init() {
      const carousel = document.querySelector('.onboarding-carousel');
      if (!carousel) return;

      const slides = carousel.querySelectorAll('.onboarding-slide');
      this.totalSlides = slides.length;
      if (this.totalSlides === 0) return;

      const nextBtn = document.querySelector('[data-onboarding-next]');
      const skipBtn = document.querySelector('[data-onboarding-skip]');
      const dots = document.querySelectorAll('.step-dot');

      if (nextBtn) {
        nextBtn.addEventListener('click', () => this.next(slides, dots, nextBtn));
      }
      if (skipBtn) {
        skipBtn.addEventListener('click', () => this.complete());
      }

      this.showSlide(slides, dots, 0);
    },

    showSlide(slides, dots, index) {
      slides.forEach((slide, i) => {
        slide.style.display = i === index ? 'flex' : 'none';
        if (i === index) {
          slide.style.animation = 'fadeInUp 400ms ease-out';
        }
      });

      dots.forEach((dot, i) => {
        dot.classList.toggle('step-dot--active', i === index);
        dot.classList.toggle('step-dot--completed', i < index);
      });
    },

    next(slides, dots, btn) {
      this.currentSlide++;
      if (this.currentSlide >= this.totalSlides) {
        this.complete();
        return;
      }
      this.showSlide(slides, dots, this.currentSlide);

      if (this.currentSlide === this.totalSlides - 1) {
        btn.textContent = 'Get Started';
      }
    },

    complete() {
      const loginUrl = 'login.html';
      ScreenTransition.navigateTo(loginUrl, 'slide-left');
    }
  };


  /* ────────────────────────────────────────────────────────────
     13. LOADING STATE SIMULATION
     ──────────────────────────────────────────────────────────── */

  const LoadingState = {
    showButton(btn) {
      btn.classList.add('btn--loading');
      btn.setAttribute('aria-busy', 'true');
      btn.setAttribute('data-original-text', btn.textContent);
      btn.textContent = '';
    },

    hideButton(btn) {
      btn.classList.remove('btn--loading');
      btn.setAttribute('aria-busy', 'false');
      btn.textContent = btn.getAttribute('data-original-text') || '';
    },

    simulateAction(btn, callback, duration = 1500) {
      this.showButton(btn);
      setTimeout(() => {
        this.hideButton(btn);
        if (callback) callback();
      }, duration);
    }
  };


  /* ────────────────────────────────────────────────────────────
     14. PULL TO REFRESH (Simulation)
     ──────────────────────────────────────────────────────────── */

  const PullToRefresh = {
    init() {
      const refreshable = document.querySelector('[data-pull-refresh]');
      if (!refreshable) return;

      let startY = 0;
      let pulling = false;

      refreshable.addEventListener('touchstart', (e) => {
        if (refreshable.scrollTop === 0) {
          startY = e.touches[0].clientY;
          pulling = true;
        }
      }, { passive: true });

      refreshable.addEventListener('touchmove', (e) => {
        if (!pulling) return;
        const currentY = e.touches[0].clientY;
        const diff = currentY - startY;

        if (diff > 0 && diff < 100) {
          refreshable.style.transform = `translateY(${diff * 0.4}px)`;
        }
      }, { passive: true });

      refreshable.addEventListener('touchend', () => {
        if (!pulling) return;
        pulling = false;
        refreshable.style.transition = 'transform 300ms ease';
        refreshable.style.transform = 'translateY(0)';
        setTimeout(() => {
          refreshable.style.transition = '';
        }, 300);
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     15. CARD FREEZE/UNFREEZE TOGGLE
     ──────────────────────────────────────────────────────────── */

  const CardManager = {
    init() {
      document.querySelectorAll('[data-card-freeze]').forEach(btn => {
        btn.addEventListener('click', function () {
          const cardEl = document.querySelector('[data-card-id="' + this.getAttribute('data-card-freeze') + '"]');
          if (!cardEl) return;

          const isFrozen = cardEl.classList.toggle('bank-card--frozen');
          this.textContent = isFrozen ? 'Unfreeze' : 'Freeze';

          if (isFrozen) {
            cardEl.style.filter = 'grayscale(1) brightness(0.7)';
            Toast.show('Card has been frozen', 'success');
          } else {
            cardEl.style.filter = '';
            Toast.show('Card has been unfrozen', 'success');
          }
        });
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     16. BIOMETRIC AUTH SIMULATION
     ──────────────────────────────────────────────────────────── */

  const BiometricAuth = {
    init() {
      const biometricBtn = document.querySelector('[data-biometric-trigger]');
      if (!biometricBtn) return;

      biometricBtn.addEventListener('click', () => {
        this.simulate();
      });
    },

    simulate() {
      const overlay = document.createElement('div');
      overlay.className = 'biometric-overlay';
      overlay.style.cssText = `
        position: fixed; inset: 0; background: rgba(0,0,0,0.8);
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; z-index: 100; color: white;
        animation: fadeIn 200ms ease;
      `;
      overlay.innerHTML = `
        <div style="width:80px;height:80px;border:3px solid rgba(255,255,255,0.3);border-radius:50%;
                    display:flex;align-items:center;justify-content:center;margin-bottom:24px;">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 10V14M18.5 4.35A9.96 9.96 0 0 1 22 12c0 5.52-4.48 10-10 10S2 17.52 2 12c0-2.74 1.1-5.22 2.88-7.02"/>
            <path d="M12 2a10 10 0 0 1 6.5 2.35"/>
            <path d="M8.65 3.35A9.96 9.96 0 0 1 12 2"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </div>
        <p style="font-size:18px;font-weight:600;margin-bottom:8px;">Touch Sensor</p>
        <p style="font-size:14px;opacity:0.7;">Verify your identity</p>
      `;
      document.body.appendChild(overlay);

      overlay.addEventListener('click', () => {
        overlay.querySelector('div').style.borderColor = '#10b981';
        overlay.querySelector('p').textContent = 'Verified';
        setTimeout(() => {
          overlay.style.animation = 'fadeIn 200ms ease reverse forwards';
          setTimeout(() => {
            overlay.remove();
            window.location.href = 'dashboard.html';
          }, 200);
        }, 800);
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     17. STAGGER ANIMATION ON SCROLL
     ──────────────────────────────────────────────────────────── */

  const ScrollAnimations = {
    init() {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-fade-in-up');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1 });

      document.querySelectorAll('[data-animate-on-scroll]').forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     18. FORM VALIDATION (Prototype)
     ──────────────────────────────────────────────────────────── */

  const FormValidation = {
    init() {
      document.querySelectorAll('[data-validate]').forEach(form => {
        form.addEventListener('submit', (e) => {
          e.preventDefault();
          const inputs = form.querySelectorAll('[required]');
          let isValid = true;

          inputs.forEach(input => {
            const group = input.closest('.form-group');
            const error = group ? group.querySelector('.form-error') : null;

            if (!input.value.trim()) {
              isValid = false;
              input.classList.add('form-input--error');
              if (error) error.style.display = 'flex';
            } else {
              input.classList.remove('form-input--error');
              if (error) error.style.display = 'none';
            }
          });

          if (isValid) {
            const submitBtn = form.querySelector('[type="submit"]');
            if (submitBtn) {
              LoadingState.simulateAction(submitBtn, () => {
                Toast.show('Action completed successfully', 'success');
              });
            }
          }
        });
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     19. AMOUNT ENTRY KEYPAD (for transfer screen)
     ──────────────────────────────────────────────────────────── */

  const AmountKeypad = {
    init() {
      const display = document.querySelector('[data-amount-display]');
      const keys = document.querySelectorAll('[data-key]');
      if (!display || keys.length === 0) return;

      let value = '';

      keys.forEach(key => {
        key.addEventListener('click', () => {
          const keyVal = key.getAttribute('data-key');

          if (keyVal === 'delete') {
            value = value.slice(0, -1);
          } else if (keyVal === '.') {
            if (!value.includes('.')) value += '.';
          } else {
            if (value.includes('.') && value.split('.')[1].length >= 2) return;
            if (value.length >= 10) return;
            value += keyVal;
          }

          display.textContent = value ? '$' + (value || '0') : '$0';
          display.classList.toggle('text-secondary', !value);
        });
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     20. NOTIFICATION MARK AS READ
     ──────────────────────────────────────────────────────────── */

  const NotificationManager = {
    init() {
      document.querySelectorAll('.notification-item--unread').forEach(item => {
        item.addEventListener('click', function () {
          this.classList.remove('notification-item--unread');
          const dot = this.querySelector('.notification-item__dot');
          if (dot) dot.style.display = 'none';

          // Update badge count
          const badge = document.querySelector('.bottom-nav__badge');
          if (badge) {
            let count = parseInt(badge.textContent) - 1;
            if (count <= 0) {
              badge.style.display = 'none';
            } else {
              badge.textContent = count;
            }
          }
        });
      });
    }
  };


  /* ────────────────────────────────────────────────────────────
     21. STATUS BAR CLOCK
     ──────────────────────────────────────────────────────────── */

  const StatusBar = {
    init() {
      const timeEl = document.querySelector('.status-bar__time');
      if (!timeEl) return;

      const update = () => {
        const now = new Date();
        timeEl.textContent = now.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });
      };

      update();
      setInterval(update, 60000);
    }
  };


  /* ────────────────────────────────────────────────────────────
     INITIALIZATION
     ──────────────────────────────────────────────────────────── */

  document.addEventListener('DOMContentLoaded', () => {
    PrototypeNav.init();
    ButtonEffects.init();
    PinInput.init();
    Tabs.init();
    BottomSheet.init();
    Toast.init();
    Toggles.init();
    FilterChips.init();
    AmountFormatter.init();
    Search.init();
    Onboarding.init();
    PullToRefresh.init();
    CardManager.init();
    BiometricAuth.init();
    ScrollAnimations.init();
    FormValidation.init();
    AmountKeypad.init();
    NotificationManager.init();
    StatusBar.init();

    // Entrance animation for screen
    const screen = document.querySelector('.screen');
    if (screen) {
      screen.style.animation = 'fadeIn 300ms ease-out';
    }
  });

  // Expose Toast and LoadingState globally for inline usage
  window.PrototypeKit = {
    Toast,
    LoadingState,
    ScreenTransition,
    BottomSheet,
    AmountFormatter
  };

})();
