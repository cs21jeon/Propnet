/*
 * PropMap 로그인 UI + 비로그인 gating
 *
 * - 헤더(side-panel)에 로그인 버튼 / 프로필 마운트
 * - propnet.kr 도메인 쿠키(propnet_uid)로 로그인 상태 감지
 *   (propnet_token 은 HttpOnly — JS 접근 불가)
 * - 보호된 액션(매물 상세/상담/전화) 실행 전 로그인 gating 모달
 * - inapp=1 (Proppedia WebView) 에서는 로그아웃 메뉴 숨김
 *
 * 외부 사용 API:
 *   window.PropMapAuth.isLoggedIn()
 *   window.PropMapAuth.showGate(reason?)          // 로그인 유도 모달
 *   window.PropMapAuth.requireLogin(fn, reason?)  // 로그인된 경우에만 fn 실행
 *   window.PropMapAuth.refresh()                  // 재로그인 후 뱃지 재렌더
 */
(function () {
    'use strict';

    // ===== 설정 =====
    // /register/ 는 Gmail OAuth 통합 진입점 (기존 유저 로그인 + 신규 가입 자동 분기)
    var LOGIN_URL = '/register/';
    // 로그아웃은 서버 구현에 따라 달라질 수 있음. 실패해도 페이지만 리로드되도록 처리.
    // 서버 확인: /propsheet/auth/logout (GET 302) 가 유효
    var LOGOUT_URL_CANDIDATES = ['/propsheet/auth/logout'];
    // 서버 확인 우선순위:
    //  1) /api/auth/session-sync (propnet_token 쿠키 기반, name 포함)
    //  2) /api/auth/me / /app/api/auth/me (Bearer 토큰 필요 — 폴백)
    var ME_ENDPOINTS = ['/app/api/auth/session-sync', '/app/api/auth/me'];

    var isInApp = (function () {
        try { return new URLSearchParams(location.search).get('inapp') === '1'; }
        catch (e) { return false; }
    })();

    var state = {
        loggedIn: false,
        user: null,
        initialized: false
    };

    // ===== 쿠키/상태 =====
    function getPropnetUid() {
        var m = document.cookie.match(/(?:^|;\s*)propnet_uid=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : null;
    }

    function fetchMe() {
        var idx = 0;
        function tryNext() {
            if (idx >= ME_ENDPOINTS.length) return Promise.resolve(null);
            var url = ME_ENDPOINTS[idx++];
            return fetch(url, { credentials: 'include' })
                .then(function (r) {
                    if (!r.ok) throw new Error('status ' + r.status);
                    return r.json();
                })
                .then(function (data) {
                    // /api/auth/me 응답 구조: { success: true, user: {id, email, name, role, agent_id, ...} }
                    if (!data || data.success === false) return tryNext();
                    var u = data.user || data;  // 혹시 다른 엔드포인트가 flat로 오는 경우 대비
                    if (!u || (!u.id && !u.email)) return tryNext();
                    return {
                        id: u.id || u.user_id || u.propnet_uid || null,
                        display_name: u.name || u.display_name || u.full_name || null,
                        email: u.email || null,
                        role: u.role || null
                    };
                })
                .catch(function () { return tryNext(); });
        }
        return tryNext();
    }

    function checkAuthStatus() {
        var uid = getPropnetUid();
        if (!uid) {
            state.loggedIn = false;
            state.user = null;
            return Promise.resolve(false);
        }
        state.loggedIn = true;
        return fetchMe().then(function (info) {
            state.user = info || { id: uid, display_name: null };
            return true;
        });
    }

    // ===== URL =====
    function currentReturnUrl() {
        return location.pathname + location.search + location.hash;
    }
    function loginHref() {
        return LOGIN_URL + '?next=' + encodeURIComponent(currentReturnUrl());
    }

    // ===== 렌더 =====
    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function renderAuthButton() {
        var mount = document.getElementById('propmapAuthMount');
        if (!mount) return;

        if (state.loggedIn) {
            var name = ((state.user && state.user.display_name) || '').trim();
            var email = ((state.user && state.user.email) || '').trim();
            // 이니셜: 한글 이름이면 성(첫 글자), 영문이면 첫 글자 대문자, 둘 다 없으면 이메일 앞글자.
            var initialSource = name || email || 'U';
            var initial = initialSource.charAt(0).toUpperCase();

            var menuItems = '';
            if (name || email) {
                menuItems += '<div class="auth-menu-name">' + escapeHtml(name || email) + '</div>';
            }
            menuItems += '<a href="/propsheet/" class="auth-menu-item">내 서비스</a>';
            menuItems += '<a href="/billing/" class="auth-menu-item">요금제</a>';
            if (!isInApp) {
                menuItems += '<button type="button" class="auth-menu-item auth-menu-logout" id="propmapLogoutBtn">로그아웃</button>';
            }

            mount.innerHTML =
                '<button type="button" id="propmapAuthBtn" class="auth-profile-btn" title="' + escapeHtml(name || email || '로그인됨') + '">' +
                    '<span class="auth-avatar">' + escapeHtml(initial) + '</span>' +
                '</button>' +
                '<div id="propmapAuthMenu" class="auth-menu" hidden>' + menuItems + '</div>';

            var btn = document.getElementById('propmapAuthBtn');
            var menu = document.getElementById('propmapAuthMenu');
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                menu.hidden = !menu.hidden;
            });
            document.addEventListener('click', function (e) {
                if (!menu.contains(e.target) && e.target !== btn && !btn.contains(e.target)) {
                    menu.hidden = true;
                }
            });
            var logoutBtn = document.getElementById('propmapLogoutBtn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', function () { doLogout(); });
            }
        } else {
            mount.innerHTML =
                '<a href="' + escapeHtml(loginHref()) + '" class="auth-login-btn" id="propmapAuthBtn">' +
                    '<span class="material-symbols-outlined auth-login-icon">login</span>' +
                    '<span class="auth-login-label">로그인</span>' +
                '</a>';
        }
    }

    function doLogout() {
        // 서버 로그아웃 엔드포인트 중 하나로 이동. 실패해도 페이지 리로드로 쿠키 갱신.
        var next = encodeURIComponent(location.pathname);
        for (var i = 0; i < LOGOUT_URL_CANDIDATES.length; i++) {
            // 가장 보수적인 방식: 첫 후보로 리다이렉트 (서버가 404면 수동 새로고침으로 복구).
            window.location.href = LOGOUT_URL_CANDIDATES[i] + '?next=' + next;
            return;
        }
    }

    // ===== Gating 모달 =====
    var DEFAULT_GATE_MSG = '매물 정보 열람은 propnet 로그인 후 이용해 주세요.\n로그인하면 AI 매물 추천 1회를 무료로 드립니다.';

    function ensureGateModal() {
        if (document.getElementById('propmapAuthGateOverlay')) return;
        var overlay = document.createElement('div');
        overlay.id = 'propmapAuthGateOverlay';
        overlay.className = 'auth-gate-overlay';
        overlay.innerHTML =
            '<div class="auth-gate-modal" role="dialog" aria-modal="true" aria-labelledby="propmapAuthGateTitle">' +
                '<button type="button" class="auth-gate-close" aria-label="닫기">&#10005;</button>' +
                '<div class="auth-gate-icon"><span class="material-symbols-outlined">lock</span></div>' +
                '<h3 id="propmapAuthGateTitle" class="auth-gate-title">로그인이 필요해요</h3>' +
                '<p class="auth-gate-msg" id="propmapAuthGateMsg"></p>' +
                '<a href="#" class="auth-gate-primary" id="propmapAuthGateLogin">' +
                    '<span class="material-symbols-outlined auth-login-icon">login</span>' +
                    '<span>Google로 로그인</span>' +
                '</a>' +
                '<button type="button" class="auth-gate-secondary" id="propmapAuthGateCancel">다음에 할게요</button>' +
            '</div>';
        document.body.appendChild(overlay);

        overlay.querySelector('.auth-gate-close').addEventListener('click', hideGate);
        overlay.querySelector('#propmapAuthGateCancel').addEventListener('click', hideGate);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) hideGate();
        });
    }

    function showGate(reason) {
        // 이미 로그인된 상태라면 모달 띄우지 말고 바로 반환
        if (state.loggedIn) return false;
        ensureGateModal();
        var overlay = document.getElementById('propmapAuthGateOverlay');
        var msg = document.getElementById('propmapAuthGateMsg');
        var login = document.getElementById('propmapAuthGateLogin');
        msg.textContent = reason || DEFAULT_GATE_MSG;
        login.href = loginHref();
        overlay.classList.add('active');
        return true;
    }
    function hideGate() {
        var overlay = document.getElementById('propmapAuthGateOverlay');
        if (overlay) overlay.classList.remove('active');
    }

    function requireLogin(fn, reason) {
        if (state.loggedIn) {
            try { fn(); } catch (e) { console.error(e); }
            return true;
        }
        showGate(reason);
        return false;
    }

    // ===== 공개 API =====
    window.PropMapAuth = {
        isLoggedIn: function () { return state.loggedIn; },
        getUser: function () { return state.user; },
        isInApp: function () { return isInApp; },
        showGate: showGate,
        hideGate: hideGate,
        requireLogin: requireLogin,
        refresh: function () {
            return checkAuthStatus().then(renderAuthButton);
        },
        loginHref: loginHref
    };

    // ===== 초기화 =====
    function init() {
        if (state.initialized) return;
        state.initialized = true;
        checkAuthStatus().then(function () {
            renderAuthButton();
            document.dispatchEvent(new CustomEvent('propmap:auth-ready', {
                detail: { loggedIn: state.loggedIn, user: state.user }
            }));
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
