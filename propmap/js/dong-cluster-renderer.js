** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
/*
 * dong-cluster-renderer.js — Week 3
 *
 * PropMap 3곳(propmap/map.html, propmap/index.html, frontend/public/propmap/index.html)
 * 공통 동 단위 마커 렌더러.
 *
 * 사용법:
 *   var renderer = DongClusterRenderer.init({
 *     map: window._kakaoMap,
 *     properties: () => window._currentProperties,  // 현재 매물 배열 getter
 *     apiUrl: '/propsheet/api/propsheet/map/dong-coords',
 *     zoomThreshold: 3,          // kakao level <=3 (줌 인)에서 활성화. 기본 3.
 *     onDongClick: (dong, matched) => { ... },
 *   });
 *
 *   renderer.refresh();    // 외부에서 매물 변경 후 강제 갱신
 *   renderer.enable();     // 기능 활성화
 *   renderer.disable();    // OFF + 마커 제거
 *
 * 주의:
 *   - Kakao Map level은 "작을수록 확대"됨. 문서 요구 "줌>=15"는 카카오 level 기준 level<=3 에 대응.
 *   - /map/dong-coords API는 ENABLE_DONG_CLUSTERING=true 일 때만 응답 (503 차단).
 *   - 동별 마커는 동 매물 수를 카운트하여 표시하며, 매물 0건인 동은 회색 윤곽으로 렌더링.
 */
(function (global) {
  'use strict';

  var DEFAULT_API = '/propsheet/api/propsheet/map/dong-coords';
  var DEFAULT_ZOOM_THRESHOLD = 3; // 카카오 level 기준

  function DongClusterRenderer(opts) {
    this.map = opts.map;
    this.propertiesGetter = typeof opts.properties === 'function'
      ? opts.properties
      : function () { return []; };
    this.apiUrl = opts.apiUrl || DEFAULT_API;
    this.zoomThreshold = (typeof opts.zoomThreshold === 'number') ? opts.zoomThreshold : DEFAULT_ZOOM_THRESHOLD;
    this.onDongClick = opts.onDongClick || null;
    this.clusterPopupFn = opts.createClusterPopup || null; // 기존 createClusterPopup 재사용

    this._enabled = true;
    this._dongCache = {}; // pnu → dongs[]
    this._dongMarkers = []; // 현재 렌더링된 동 마커
    this._pendingPnus = {}; // 중복 요청 방지
    this._listenersAttached = false;

    this._attachListeners();
  }

  DongClusterRenderer.prototype._attachListeners = function () {
    if (this._listenersAttached || !this.map || !global.kakao) return;
    var self = this;
    kakao.maps.event.addListener(this.map, 'zoom_changed', function () {
      self._onZoomChanged();
    });
    kakao.maps.event.addListener(this.map, 'idle', function () {
      // idle에서는 이미 준 줌이어도 캐시된 데이터로 재렌더링
      self._onZoomChanged();
    });
    this._listenersAttached = true;
  };

  DongClusterRenderer.prototype._onZoomChanged = function () {
    if (!this._enabled) return;
    var level = this.map.getLevel();
    if (level > this.zoomThreshold) {
      // 줌 아웃 → 동 마커 제거 (기존 클러스터 로직이 담당)
      this._clearDongMarkers();
      return;
    }
    // 줌 인 → 현재 매물에서 유니크 지번/PNU 추출 → fetch → 렌더링
    this._renderForCurrentBounds();
  };

  DongClusterRenderer.prototype._renderForCurrentBounds = function () {
    var props = (this.propertiesGetter() || []).filter(function (p) {
      return p && p.lat && (p.lon || p.lng);
    });
    if (!props.length) {
      this._clearDongMarkers();
      return;
    }

    // 지도 bounds 내에서만 처리 (성능)
    var bounds = this.map.getBounds();
    var sw = bounds.getSouthWest(), ne = bounds.getNorthEast();
    var inBounds = props.filter(function (p) {
      var la = +p.lat, lo = +(p.lon || p.lng);
      return la >= sw.getLat() && la <= ne.getLat() &&
             lo >= sw.getLng() && lo <= ne.getLng();
    });

    // 유니크 key 우선순위: pnu → 지번주소 → (lat,lon) 격자(약 100m 단위).
    // map-data API 응답에 pnu/주소가 없는 레거시 매물도 lat/lon 기반으로 동 클러스터링 가능하도록.
    var groups = {}; // key → {key, pnu, address, items: [], lat, lon}
    inBounds.forEach(function (p) {
      var la = +p.lat, lo = +(p.lon || p.lng);
      var key = p.pnu || p['지번주소'] || p.jibun_address || p.jibun;
      if (!key) {
        if (!isFinite(la) || !isFinite(lo)) return;
        // 소수점 3자리 ≈ 111m / (경도 100m 내외) 격자
        key = 'grid:' + la.toFixed(3) + ',' + lo.toFixed(3);
      }
      if (!groups[key]) {
        // key가 19자리 숫자(PNU 형식)일 때만 pnu로 간주. "grid:xxx,yyy"도 19자가 될 수 있어 숫자 체크 필수.
        var isRealPnu = (typeof key === 'string' && key.length === 19 && /^\d{19}$/.test(key));
        groups[key] = {
          key: key,
          pnu: isRealPnu ? key : (p.pnu || null),
          address: p['지번주소'] || p.jibun_address || p.jibun || null,
          items: [],
          lat: la,
          lon: lo,
        };
      }
      groups[key].items.push(p);
    });

    var self = this;
    Object.keys(groups).forEach(function (key) {
      var g = groups[key];
      self._ensureDongData(g).then(function (dongs) {
        self._renderDongsForGroup(g, dongs);
      }).catch(function (err) {
        console.warn('[dong-cluster] fetch 실패:', key, err);
      });
    });
  };

  DongClusterRenderer.prototype._ensureDongData = function (g) {
    var cacheKey = g.pnu || g.address || g.key || ('geo:' + g.lat + ',' + g.lon);
    if (this._dongCache[cacheKey]) {
      return Promise.resolve(this._dongCache[cacheKey]);
    }
    if (this._pendingPnus[cacheKey]) {
      return this._pendingPnus[cacheKey];
    }
    var params = new URLSearchParams();
    if (g.pnu) params.set('pnu', g.pnu);
    else if (g.lat && g.lon) {
      params.set('lat', g.lat);
      params.set('lon', g.lon);
    }
    if (g.address) params.set('address', g.address);

    var self = this;
    var p = fetch(this.apiUrl + '?' + params.toString(), { credentials: 'same-origin' })
      .then(function (r) {
        if (r.status === 503) { // 기능 플래그 off
          return { success: false, disabled: true };
        }
        return r.json();
      })
      .then(function (body) {
        if (!body || !body.success) {
          self._dongCache[cacheKey] = [];
          return [];
        }
        self._dongCache[cacheKey] = body.dongs || [];
        return body.dongs || [];
      })
      .finally(function () {
        delete self._pendingPnus[cacheKey];
      });
    this._pendingPnus[cacheKey] = p;
    return p;
  };

  // Week 4: 매물 동 값 정규화. "동 없음", "없음", "-" 등은 빈 문자열로 취급.
  function _normalizeDong(raw) {
    var v = (raw == null ? '' : String(raw)).trim();
    if (!v) return '';
    // 전각/반각 공백만 있는 경우
    if (!v.replace(/\s/g, '')) return '';
    // 흔한 "없음" 표현
    var lower = v.toLowerCase();
    if (v === '동 없음' || v === '없음' || v === '-' || v === 'n/a' || lower === 'none' || lower === 'null') return '';
    return v;
  }

  // Week 4: 동명 매칭 규칙 — 정확 일치 → 숫자 부분 일치.
  // 예: 매물 "101" vs 캐시 "101동", 매물 "제101동" vs 캐시 "101동" 모두 매칭.
  function _dongMatches(propDong, cacheDong) {
    var a = _normalizeDong(propDong);
    var b = _normalizeDong(cacheDong);
    if (!a || !b) return false;
    if (a === b) return true;
    // 숫자만 추출해 비교 (맨 뒤 숫자 기준)
    var na = (a.match(/\d+/g) || []);
    var nb = (b.match(/\d+/g) || []);
    if (na.length && nb.length && na[na.length - 1] === nb[nb.length - 1]) {
      return true;
    }
    return false;
  }

  DongClusterRenderer.prototype._renderDongsForGroup = function (g, dongs) {
    if (!dongs || !dongs.length) return;

    // Week 4: 단지 내 동이 1개뿐이면 동 입력 없는 매물도 그 동에 매칭.
    var singleDongNm = (dongs.length === 1) ? _normalizeDong(dongs[0].dong_nm || dongs[0].bld_nm || '') : '';

    // Week 4: 각 캐시 동 이름을 키로, 매물을 부분매칭 규칙으로 할당.
    // — 정확 일치 > 숫자 일치 > 단일 동 단지의 empty 매물.
    var countByDong = {};
    dongs.forEach(function (d) {
      var name = (d.dong_nm || d.bld_nm || '').trim();
      if (name) countByDong[name] = 0;
    });
    g.items.forEach(function (p) {
      var dn = _normalizeDong(p.dong || p['동']);
      // 단일 동 단지의 동 미입력 매물
      if (!dn) {
        if (singleDongNm) {
          countByDong[singleDongNm] = (countByDong[singleDongNm] || 0) + 1;
        }
        return;
      }
      // 캐시 동 리스트에서 매칭되는 첫 번째 이름 찾기
      var hitName = null;
      for (var i = 0; i < dongs.length; i++) {
        var cacheName = (dongs[i].dong_nm || dongs[i].bld_nm || '').trim();
        if (!cacheName) continue;
        if (_dongMatches(dn, cacheName)) {
          hitName = cacheName;
          break;
        }
      }
      if (hitName) {
        countByDong[hitName] = (countByDong[hitName] || 0) + 1;
      }
    });

    var self = this;
    dongs.forEach(function (d) {
      var dongNm = (d.dong_nm || d.bld_nm || '').trim();
      if (!dongNm || !d.lat || !d.lon) return;
      var count = countByDong[dongNm] || 0;

      var el = self._createDongMarkerEl(dongNm, count);
      var pos = new kakao.maps.LatLng(d.lat, d.lon);
      var overlay = new kakao.maps.CustomOverlay({
        map: self.map,
        position: pos,
        content: el,
        yAnchor: 0.5,
        xAnchor: 0.5,
      });

      (function (dongObj, cnt) {
        el.addEventListener('click', function (ev) {
          ev.stopPropagation();
          var matched = g.items.filter(function (p) {
            var dn = _normalizeDong(p.dong || p['동']);
            if (!dn && singleDongNm && _normalizeDong(dongNm) === singleDongNm) return true;
            return _dongMatches(dn, dongNm);
          });
          if (self.onDongClick) {
            self.onDongClick(dongObj, matched, pos);
          } else if (cnt > 0 && typeof self.clusterPopupFn === 'function') {
            // 기존 createClusterPopup 재사용
            var groupForPopup = matched.map(function (p) {
              return {
                lat: +p.lat, lon: +(p.lon || p.lng),
                agent: p.agent_slug || p.agent || '',
                price: p.price || p.display_price || '',
                id: p.id || p.record_id,
                raw: p,
              };
            });
            self.clusterPopupFn(groupForPopup, pos);
          } else if (cnt === 0) {
            // 매물 없는 동 — 간단 알림
            console.log('[dong-cluster] 매물 없는 동: ' + dongNm);
          }
        });
      })(d, count);

      self._dongMarkers.push(overlay);
    });
  };

  DongClusterRenderer.prototype._createDongMarkerEl = function (dongNm, count) {
    var el = document.createElement('div');
    el.className = 'dong-marker' + (count === 0 ? ' dong-empty' : '');
    el.style.cssText = [
      'display:inline-flex',
      'flex-direction:column',
      'align-items:center',
      'justify-content:center',
      'min-width:48px',
      'padding:4px 8px',
      'border-radius:12px',
      'font-size:11px',
      'font-weight:700',
      'line-height:1.2',
      'cursor:pointer',
      'box-shadow:0 2px 6px rgba(0,0,0,0.2)',
      'user-select:none',
      count > 0
        ? 'background:#1D4ED8;color:#fff;border:1px solid #1e3a8a;'
        : 'background:transparent;color:#64748b;border:1.5px dashed #94a3b8;opacity:0.45;',
    ].join(';');
    el.setAttribute('data-dong', dongNm);
    el.setAttribute('title', count > 0 ? dongNm + ' — 매물 ' + count + '건' : dongNm + ' — 매물 없음');
    el.innerHTML =
      '<span style="font-size:10px;opacity:0.9;">' + _escape(dongNm) + '</span>' +
      (count > 0 ? '<span style="font-size:13px;">' + count + '</span>' : '');
    return el;
  };

  DongClusterRenderer.prototype._clearDongMarkers = function () {
    this._dongMarkers.forEach(function (m) {
      try { m.setMap(null); } catch (e) {}
    });
    this._dongMarkers = [];
  };

  DongClusterRenderer.prototype.refresh = function () {
    this._clearDongMarkers();
    this._onZoomChanged();
  };

  DongClusterRenderer.prototype.enable = function () {
    this._enabled = true;
    this._onZoomChanged();
  };

  DongClusterRenderer.prototype.disable = function () {
    this._enabled = false;
    this._clearDongMarkers();
  };

  function _escape(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // Public API
  global.DongClusterRenderer = {
    init: function (opts) {
      return new DongClusterRenderer(opts);
    },
    _Class: DongClusterRenderer, // 테스트용
  };
})(typeof window !== 'undefined' ? window : this);
