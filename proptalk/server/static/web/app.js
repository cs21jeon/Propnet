/**
 * Proptalk Web App - Alpine.js + socket.io
 * PC 브라우저에서 앱과 동일한 기능 제공
 */

// ── PWA: 서비스 워커 등록 ──
// sw.js는 /proptalk/web/sw.js 경로로 서빙 (web_app.py에서 Service-Worker-Allowed 헤더 포함)
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/proptalk/web/sw.js', { scope: '/proptalk/web/' })
        .then(() => console.log('[PWA] Service Worker registered'))
        .catch(err => console.warn('[PWA] SW registration failed:', err));
}

// ── PWA: 설치 프롬프트 캡처 ──
let _deferredInstallPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    _deferredInstallPrompt = e;
});

function ProptalkApp() {
    return {
        // ── Auth ──
        token: null,
        refreshToken: null,
        user: null,

        // ── PWA ──
        installPrompt: null,

        // ── Rooms ──
        rooms: [],
        filteredRooms: [],
        roomSearch: '',
        currentRoom: null,

        // ── Messages ──
        messages: [],
        inputText: '',
        loadingMore: false,
        hasMore: true,
        oldestMsgId: null,

        // ── Members ──
        members: [],

        // ── WebSocket ──
        socket: null,
        typingText: '',
        _typingTimeout: null,
        _typingUsers: {},

        // ── UI state ──
        showDetail: false,
        showSummaries: false,
        showSearch: false,
        showCreateRoom: false,
        showJoinRoom: false,
        showSettings: false,
        searchQuery: '',
        searchResultIds: [],     // [fix #3] 검색 결과 메시지 ID 목록
        searchResultIndex: -1,   // [fix #3] 현재 선택된 검색 결과 인덱스
        summarySearchQuery: '',
        summarySearchTotal: -1,

        // ── Room forms ──
        newRoomName: '',
        joinCode: '',

        // ── Reply ──
        replyTo: null,   // { id, content, user_name, type }

        // ── Drag & Drop ──
        isDragging: false,

        // ── Uploads ──
        uploads: [],

        // ── Clipboard Paste ──
        pastePreview: null,
        _pasteFile: null,

        // ── Read Status ──
        _readStatus: {},  // user_id -> last_read_message_id
        _memberCount: 0,

        // ── Recording ──
        isRecording: false,
        recordingTime: '00:00',
        _mediaRecorder: null,
        _audioChunks: [],
        _recordingStart: null,
        _recordingTimer: null,

        // ── Summaries ──
        summaries: [],

        // ── Expand state (Map-based for x-for compatibility) ──
        _expandedMsgs: {},

        // ── Dark mode ──
        darkMode: false,

        // ── Toasts ──
        toasts: [],

        // ── Message menu ──
        msgMenu: { show: false, x: 0, y: 0, msg: null },
        deleteConfirm: { show: false, msg: null, text: '' },

        // ── Computed ──
        get isRoomAdmin() {
            if (!this.currentRoom || !this.user) return false;
            const me = this.members.find(m => m.user_id === this.user.id);
            return me?.role === 'admin';
        },

        // ============================================================
        // Init
        // ============================================================
        init() {
            this.token = localStorage.getItem('proptalk_token');
            this.refreshToken = localStorage.getItem('proptalk_refresh_token');
            const userJson = localStorage.getItem('proptalk_user');
            if (userJson) {
                try { this.user = JSON.parse(userJson); } catch(e) {}
            }

            if (!this.token) {
                window.location.href = '/proptalk/web/login';
                return;
            }

            // PWA 설치 프롬프트
            this.installPrompt = _deferredInstallPrompt;
            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                this.installPrompt = e;
            });

            // Dark mode 로드
            this.darkMode = localStorage.getItem('proptalk_dark') === 'true';
            if (this.darkMode) document.body.classList.add('dark');

            this.loadUser();
            this.loadRooms();
            this.connectSocket();

            // [fix #4] Enter 키로 메시지 전송 - addEventListener 방식
            this.$nextTick(() => {
                const textarea = this.$refs.chatInput;
                if (textarea) {
                    textarea.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.altKey) {
                            e.preventDefault();
                            this.sendMessage();
                        }
                    });
                }
            });
        },

        // ============================================================
        // API helpers
        // ============================================================
        async api(path, opts = {}) {
            const url = API_BASE + path;
            const headers = {
                'Authorization': 'Bearer ' + this.token,
                ...(opts.headers || {}),
            };
            if (!(opts.body instanceof FormData)) {
                headers['Content-Type'] = 'application/json';
            }
            const res = await fetch(url, { ...opts, headers });

            if (res.status === 401) {
                const refreshed = await this.tryRefresh();
                if (refreshed) {
                    headers['Authorization'] = 'Bearer ' + this.token;
                    return fetch(url, { ...opts, headers });
                }
                this.logout();
                return null;
            }
            return res;
        },

        async tryRefresh() {
            if (!this.refreshToken) return false;
            try {
                const res = await fetch(API_BASE + '/api/auth/refresh', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: this.refreshToken }),
                });
                if (res.ok) {
                    const data = await res.json();
                    this.token = data.access_token || data.token;
                    if (data.refresh_token) this.refreshToken = data.refresh_token;
                    localStorage.setItem('proptalk_token', this.token);
                    if (this.refreshToken) localStorage.setItem('proptalk_refresh_token', this.refreshToken);
                    return true;
                }
            } catch(e) {}
            return false;
        },

        // ============================================================
        // Auth
        // ============================================================
        async loadUser() {
            const res = await this.api('/api/auth/me');
            if (res?.ok) {
                const data = await res.json();
                this.user = data.user || data;
                localStorage.setItem('proptalk_user', JSON.stringify(this.user));
            }
        },

        logout() {
            localStorage.removeItem('proptalk_token');
            localStorage.removeItem('proptalk_refresh_token');
            localStorage.removeItem('proptalk_user');
            if (this.socket) this.socket.disconnect();
            window.location.href = '/proptalk/web/login';
        },

        async installApp() {
            if (!this.installPrompt) return;
            this.installPrompt.prompt();
            const result = await this.installPrompt.userChoice;
            if (result.outcome === 'accepted') {
                this.toast('앱이 설치되었습니다!', 'success');
                this.installPrompt = null;
            }
        },

        // ============================================================
        // Rooms
        // ============================================================
        async loadRooms() {
            const res = await this.api('/api/rooms');
            if (res?.ok) {
                const data = await res.json();
                this.rooms = (data.rooms || data || []).map(r => this._enrichRoom(r));
                this.filterRooms();
            }
        },

        _enrichRoom(room) {
            room._lastMsg = '';
            room._timeStr = '';
            if (room.last_message) {
                const lm = room.last_message;
                room._lastMsg = lm.type === 'audio' ? '🎤 음성 메시지' : (lm.content || '').substring(0, 50);
                room._timeStr = this.formatTimeShort(lm.created_at);
            }
            return room;
        },

        filterRooms() {
            const q = this.roomSearch.toLowerCase();
            this.filteredRooms = q
                ? this.rooms.filter(r => r.name.toLowerCase().includes(q))
                : [...this.rooms];
        },

        async selectRoom(room) {
            if (this.currentRoom?.id === room.id) return;

            // Leave previous room
            if (this.currentRoom && this.socket) {
                this.socket.emit('leave_room', { room_id: this.currentRoom.id });
            }

            this.currentRoom = room;
            this.messages = [];
            this.hasMore = true;
            this.oldestMsgId = null;
            this.showSearch = false;
            this.searchQuery = '';
            this.searchResultIds = [];
            this.searchResultIndex = -1;
            this.showSummaries = false;
            this.summaries = [];
            this.summarySearchQuery = '';
            this.summarySearchTotal = -1;

            await this.loadMessages();
            this.loadMembers();
            this.loadReadStatus(room.id);

            // Join room via WebSocket
            if (this.socket) {
                this.socket.emit('join_room', { token: this.token, room_id: room.id });
            }

            // Mark as read
            this.markRead(room.id);

            this.$nextTick(() => this.scrollToBottom());
        },

        async createRoom() {
            if (!this.newRoomName.trim()) return;
            const res = await this.api('/api/rooms', {
                method: 'POST',
                body: JSON.stringify({ name: this.newRoomName.trim() }),
            });
            if (res?.ok) {
                const data = await res.json();
                const room = this._enrichRoom(data.room || data);
                this.rooms.unshift(room);
                this.filterRooms();
                this.showCreateRoom = false;
                this.newRoomName = '';
                this.selectRoom(room);
                this.toast('방이 생성되었습니다', 'success');
            } else {
                this.toast('방 생성 실패', 'error');
            }
        },

        async joinRoom() {
            if (!this.joinCode.trim()) return;
            const res = await this.api('/api/rooms/join', {
                method: 'POST',
                body: JSON.stringify({ invite_code: this.joinCode.trim() }),
            });
            if (res?.ok) {
                const data = await res.json();
                this.showJoinRoom = false;
                this.joinCode = '';
                await this.loadRooms();
                const room = this.rooms.find(r => r.id === (data.room?.id || data.room_id));
                if (room) this.selectRoom(room);
                this.toast('방에 참가했습니다', 'success');
            } else {
                const err = await res?.json().catch(() => ({}));
                this.toast(err.error || '참가 실패', 'error');
            }
        },

        async renameRoom() {
            const name = prompt('새 방 이름:', this.currentRoom.name);
            if (!name || name === this.currentRoom.name) return;
            const res = await this.api(`/api/rooms/${this.currentRoom.id}`, {
                method: 'PATCH',
                body: JSON.stringify({ name }),
            });
            if (res?.ok) {
                this.currentRoom.name = name;
                const r = this.rooms.find(r => r.id === this.currentRoom.id);
                if (r) r.name = name;
                this.toast('방 이름이 변경되었습니다', 'success');
            }
        },

        async deleteRoom() {
            if (!confirm('정말 이 방을 삭제하시겠습니까?')) return;
            const res = await this.api(`/api/rooms/${this.currentRoom.id}`, { method: 'DELETE' });
            if (res?.ok) {
                this.rooms = this.rooms.filter(r => r.id !== this.currentRoom.id);
                this.filterRooms();
                this.currentRoom = null;
                this.messages = [];
                this.members = [];
                this.toast('방이 삭제되었습니다', 'success');
            }
        },

        copyInviteCode() {
            navigator.clipboard.writeText(this.currentRoom.invite_code);
            this.toast('초대코드가 복사되었습니다', 'success');
        },

        // ============================================================
        // Panel Toggle (안정적 토글 - 상호 배타적)
        // ============================================================
        toggleSearch() {
            if (this.showSearch) {
                this.closeSearch();
            } else {
                this.showSearch = true;
                this.showDetail = false;
                this.showSummaries = false;
                this.showSettings = false;
                this.$nextTick(() => this.$refs.searchInput?.focus());
            }
        },

        toggleSummaries() {
            const next = !this.showSummaries;
            this.showSummaries = next;
            this.showDetail = false;
            this.showSettings = false;
            if (next) this.loadSummaries();
        },

        toggleDetail() {
            const next = !this.showDetail;
            this.showDetail = next;
            this.showSummaries = false;
            this.showSettings = false;
            if (next) this.loadMembers();
        },

        // ============================================================
        // Messages
        // ============================================================
        async loadMessages(before) {
            if (!this.currentRoom) return;
            let url = `/api/rooms/${this.currentRoom.id}/messages?limit=50`;
            if (before) url += `&before_id=${before}`;

            const res = await this.api(url);
            if (res?.ok) {
                const data = await res.json();
                const msgs = (data.messages || data || []).map(m => this._enrichMessage(m)).reverse();

                if (before) {
                    this.messages = [...msgs, ...this.messages];
                } else {
                    this.messages = msgs;
                }

                this.hasMore = msgs.length >= 50;
                if (msgs.length > 0) {
                    this.oldestMsgId = msgs[0].id;
                }

                this._markDateSeparators();
            }
        },

        _enrichMessage(msg) {
            // 모든 메시지에 기본 필드 설정 (Alpine 반응형 보장)
            const defaults = {
                _userName: msg.user_name || msg.user?.name || '알 수 없음',
                _avatar: msg.user_avatar || msg.user?.avatar_url || '',
                _showDate: false,
                _dateStr: '',
                _expanded: false,
                _audioExpanded: false,
                _audioPlaying: false,
                _audioLoading: false,
                _audioLoaded: false,
                // file 필드 기본값 (반응형 위해 항상 존재해야 함)
                file_id: msg.file_id || null,
                file_name: msg.file_name || null,
                file_type: msg.file_type || null,
                file_size: msg.file_size || 0,
                file_drive_url: msg.file_drive_url || null,
                file_status: msg.file_status || 'completed',
                file_thumbnail_path: msg.file_thumbnail_path || null,
            };
            msg = Object.assign(defaults, msg);

            // API가 flat 구조로 반환: audio_id, audio_status, audio_filename 등
            // -> 템플릿이 사용하는 nested msg.audio 객체로 변환
            if (msg.audio_id && !msg.audio) {
                const filename = msg.audio_filename
                    || (msg.content || '').replace(/^🎙️\s*/, '').trim()
                    || '녹음';
                msg.audio = {
                    id: msg.audio_id,
                    status: msg.audio_status || 'completed',
                    original_filename: filename,
                    duration_seconds: msg.duration_seconds || null,
                    transcript_text: msg.transcript_text || null,
                    transcript_summary: msg.transcript_summary || null,
                    drive_url: msg.drive_url || null,
                };
            }

            // file 타입: content에서 파일명 추출
            if (msg.type === 'file' && !msg.file_name) {
                msg.file_name = (msg.content || '').replace(/^[^\s]*\s*/, '').split(' (')[0] || '파일';
            }

            // replies에서 파일정보(system) 추출
            msg._fileInfo = null;
            if (msg.replies && Array.isArray(msg.replies)) {
                const sysReply = msg.replies.find(r => r.type === 'system' && r.content && r.content.startsWith('파일정보'));
                if (sysReply) {
                    msg._fileInfo = sysReply.content.split('\n')
                        .filter(l => l.trim() && l.trim() !== '파일정보')
                        .map(l => l.trim());
                }
            }

            return msg;
        },

        _markDateSeparators() {
            let lastDate = null;
            for (const msg of this.messages) {
                const d = msg.created_at ? msg.created_at.substring(0, 10) : null;
                if (d && d !== lastDate) {
                    msg._showDate = true;
                    msg._dateStr = this.formatDate(msg.created_at);
                    lastDate = d;
                } else {
                    msg._showDate = false;
                }
            }
        },

        async sendMessage() {
            const text = this.inputText.trim();
            if (!text || !this.currentRoom) return;

            const parentId = this.replyTo?.id || null;
            this.inputText = '';
            this.replyTo = null;
            this.$nextTick(() => {
                if (this.$refs.chatInput) {
                    this.$refs.chatInput.style.height = 'auto';
                }
            });

            const body = { content: text };
            if (parentId) body.parent_id = parentId;

            const res = await this.api(`/api/rooms/${this.currentRoom.id}/messages`, {
                method: 'POST',
                body: JSON.stringify(body),
            });
            if (!res?.ok) {
                this.toast('메시지 전송 실패', 'error');
                this.inputText = text;
            }
        },

        // [fix #3 + #4] 검색 후 결과 메시지로 스크롤 + 토스트 중복 제거
        async searchMessages() {
            if (!this.searchQuery.trim() || !this.currentRoom) return;

            // 검색 결과 초기화
            this.searchResultIds = [];
            this.searchResultIndex = -1;

            const res = await this.api(`/api/rooms/${this.currentRoom.id}/messages/search?q=${encodeURIComponent(this.searchQuery)}`);
            if (res?.ok) {
                const data = await res.json();
                const results = (data.messages || data || []).map(m => this._enrichMessage(m));
                this.messages = results;
                this._markDateSeparators();

                // 검색 결과 ID 목록 저장
                this.searchResultIds = results.map(m => m.id);

                const count = results.length;
                this.toast(`${count}개 결과를 찾았습니다`, 'info');

                // 첫 번째 결과로 스크롤
                if (count > 0) {
                    this.searchResultIndex = 0;
                    this.$nextTick(() => this.scrollToSearchResult(0));
                }
            }
        },

        // [fix #3] 검색 결과 간 이동
        scrollToSearchResult(index) {
            if (index < 0 || index >= this.searchResultIds.length) return;
            this.searchResultIndex = index;
            const msgId = this.searchResultIds[index];
            const el = document.getElementById('msg-' + msgId);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                el.classList.add('search-highlight');
                setTimeout(() => el.classList.remove('search-highlight'), 2000);
            }
        },

        nextSearchResult() {
            if (this.searchResultIds.length === 0) return;
            const next = (this.searchResultIndex + 1) % this.searchResultIds.length;
            this.scrollToSearchResult(next);
        },

        prevSearchResult() {
            if (this.searchResultIds.length === 0) return;
            const prev = (this.searchResultIndex - 1 + this.searchResultIds.length) % this.searchResultIds.length;
            this.scrollToSearchResult(prev);
        },

        // [fix #3] 검색 닫기 시 원래 메시지 다시 로드
        async closeSearch() {
            this.showSearch = false;
            this.searchQuery = '';
            this.searchResultIds = [];
            this.searchResultIndex = -1;
            // 검색 결과 상태에서 전체 메시지로 복원
            if (this.currentRoom) {
                this.messages = [];
                this.hasMore = true;
                this.oldestMsgId = null;
                await this.loadMessages();
                this.$nextTick(() => this.scrollToBottom());
            }
        },

        handleScroll(e) {
            if (e.target.scrollTop < 50 && this.hasMore && !this.loadingMore) {
                this.loadMore();
            }
        },

        async loadMore() {
            if (!this.oldestMsgId || this.loadingMore) return;
            this.loadingMore = true;
            const container = this.$refs.messagesContainer;
            const oldHeight = container.scrollHeight;
            await this.loadMessages(this.oldestMsgId);
            this.$nextTick(() => {
                container.scrollTop = container.scrollHeight - oldHeight;
                this.loadingMore = false;
            });
        },

        scrollToBottom() {
            const c = this.$refs.messagesContainer;
            if (c) c.scrollTop = c.scrollHeight;
        },

        // ============================================================
        // Members
        // ============================================================
        async loadMembers() {
            if (!this.currentRoom) return;
            const res = await this.api(`/api/rooms/${this.currentRoom.id}/members`);
            if (res?.ok) {
                const data = await res.json();
                this.members = data.members || data || [];
            }
        },

        // ============================================================
        // WebSocket
        // ============================================================
        connectSocket() {
            const wsUrl = window.location.origin;
            this.socket = io(wsUrl, {
                path: '/voiceroom/socket.io/',
                auth: { token: this.token },
                transports: ['websocket'],
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionAttempts: 10,
            });

            this.socket.on('connect', () => {
                console.log('[WS] Connected');
                // Rejoin current room
                if (this.currentRoom) {
                    this.socket.emit('join_room', { token: this.token, room_id: this.currentRoom.id });
                }
            });

            this.socket.on('disconnect', () => console.log('[WS] Disconnected'));
            this.socket.on('connect_error', (err) => console.error('[WS] Error:', err.message));

            // New message
            this.socket.on('new_message', (data) => {
                const msg = this._enrichMessage(data.message || data);
                if (msg.room_id === this.currentRoom?.id) {
                    // parent_id가 있고 text가 아닌 메시지(transcript, system)는
                    // 부모 메시지의 replies 배열에 추가 (앱과 동일한 동작)
                    if (msg.parent_id && msg.type !== 'text') {
                        const parentIdx = this.messages.findIndex(m => m.id === msg.parent_id);
                        if (parentIdx >= 0) {
                            const parent = this.messages[parentIdx];
                            if (!parent.replies) parent.replies = [];
                            parent.replies.push(msg);
                            // audio 메시지의 transcript 댓글이면 요약 정보도 업데이트
                            if (msg.type === 'transcript' && parent.audio) {
                                parent.audio.transcript_summary = msg.content;
                            }
                            // Alpine 반응형 트리거
                            this.messages[parentIdx] = { ...parent };
                        }
                        // replies에 추가했으므로 독립 메시지로는 추가하지 않음
                    } else {
                        this.messages.push(msg);
                    }
                    this._markDateSeparators();
                    this.$nextTick(() => this.scrollToBottom());
                    // Mark as read since user is viewing this room
                    this.markRead(this.currentRoom.id);
                }
                // Update room list
                this._updateRoomLastMessage(msg);
            });

            // Audio status
            this.socket.on('audio_status', (data) => {
                const audioId = data.audio_id;
                const status = data.status;
                for (const msg of this.messages) {
                    if (msg.audio?.id === audioId || msg.audio_id === audioId) {
                        if (!msg.audio) msg.audio = { id: audioId };
                        msg.audio.status = status;
                        if (data.transcript_summary) msg.audio.transcript_summary = data.transcript_summary;
                        if (data.transcript_text) msg.audio.transcript_text = data.transcript_text;
                        // flat 필드도 업데이트
                        msg.audio_status = status;
                        break;
                    }
                }
            });

            // File status
            this.socket.on('file_status', (data) => {
                for (const msg of this.messages) {
                    if (msg.id === data.message_id) {
                        msg.file_status = data.status;
                        if (data.drive_url) msg.file_drive_url = data.drive_url;
                        break;
                    }
                }
            });

            // Typing
            this.socket.on('user_typing', (data) => {
                if (data.is_typing) {
                    this._typingUsers[data.user_name] = Date.now();
                } else {
                    delete this._typingUsers[data.user_name];
                }
                this._updateTypingText();
            });

            // User joined
            this.socket.on('user_joined', (data) => {
                // Could refresh members
            });

            // Read update
            this.socket.on('read_update', (data) => {
                // 현재 방이면 읽음 상태 실시간 업데이트
                if (data.room_id === this.currentRoom?.id) {
                    this._readStatus[data.user_id] = data.last_read_message_id;
                }
                // Reload rooms to refresh unread counts
                this.loadRooms();
            });

            // 메시지 삭제
            this.socket.on('message_deleted', (data) => {
                if (data.room_id === this.currentRoom?.id) {
                    const ids = new Set(data.deleted_ids || [data.message_id]);
                    this.messages = this.messages.filter(m => !ids.has(m.id));
                }
            });

            // 리액션 업데이트
            this.socket.on('reaction_updated', (data) => {
                if (data.room_id === this.currentRoom?.id) {
                    const msg = this.messages.find(m => m.id === data.message_id);
                    if (msg) msg.reactions = data.reactions;
                }
            });
        },

        _updateRoomLastMessage(msg) {
            const room = this.rooms.find(r => r.id === msg.room_id);
            if (room) {
                room._lastMsg = msg.type === 'audio' ? '🎤 음성 메시지' : (msg.content || '').substring(0, 50);
                room._timeStr = this.formatTimeShort(msg.created_at);
                // Move to top
                this.rooms = [room, ...this.rooms.filter(r => r.id !== room.id)];
                this.filterRooms();
            }
        },

        async loadReadStatus(roomId) {
            const res = await this.api(`/api/rooms/${roomId}/read-status`);
            if (res?.ok) {
                const data = await res.json();
                const status = data.read_status || [];
                this._memberCount = status.length;
                this._readStatus = {};
                for (const s of status) {
                    this._readStatus[s.user_id] = s.last_read_message_id;
                }
            }
        },

        getUnreadCount(msg) {
            if (!msg.id || msg.id < 0 || this._memberCount <= 1) return 0;
            let readCount = 0;
            for (const uid in this._readStatus) {
                if (this._readStatus[uid] >= msg.id) readCount++;
            }
            const unread = this._memberCount - readCount;
            return unread > 0 ? unread : 0;
        },

        async markRead(roomId) {
            if (!this.token) return;
            // WebSocket으로 실시간 전파
            if (this.socket) {
                this.socket.emit('mark_read', { token: this.token, room_id: roomId });
            }
            // REST API 백업 (DB 업데이트 보장)
            try {
                await fetch(`/voiceroom/api/rooms/${roomId}/mark-read`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json',
                    },
                    body: '{}',
                });
            } catch (e) {
                console.warn('[markRead] REST fallback failed:', e);
            }
            // Update local unread count
            const room = this.rooms.find(r => r.id === roomId);
            if (room) {
                room.unread_count = 0;
                this.filterRooms();
            }
        },

        sendTyping() {
            if (!this.currentRoom || !this.socket || !this.user) return;
            this.socket.emit('typing', {
                room_id: this.currentRoom.id,
                user_name: this.user.name,
                is_typing: true,
            });
            clearTimeout(this._typingTimeout);
            this._typingTimeout = setTimeout(() => {
                this.socket.emit('typing', {
                    room_id: this.currentRoom.id,
                    user_name: this.user.name,
                    is_typing: false,
                });
            }, 2000);
        },

        _updateTypingText() {
            const now = Date.now();
            const names = Object.entries(this._typingUsers)
                .filter(([_, t]) => now - t < 3000)
                .map(([n]) => n);
            if (names.length === 0) this.typingText = '';
            else if (names.length === 1) this.typingText = `${names[0]}님이 입력 중...`;
            else this.typingText = `${names.length}명이 입력 중...`;
        },

        // ============================================================
        // File Upload (Drag & Drop + File picker)
        // ============================================================
        handleDrop(e) {
            this.isDragging = false;
            if (!this.currentRoom) {
                this.toast('먼저 채팅방을 선택하세요', 'error');
                return;
            }
            const files = e.dataTransfer?.files;
            if (files?.length) this.uploadFiles(files);
        },

        handlePaste(e) {
            if (!this.currentRoom) return;
            const items = e.clipboardData?.items;
            if (!items) return;

            for (const item of items) {
                if (item.type.startsWith('image/')) {
                    e.preventDefault();
                    const file = item.getAsFile();
                    if (!file) return;

                    // 미리보기 생성
                    const reader = new FileReader();
                    reader.onload = (ev) => {
                        this.pastePreview = ev.target.result;
                        this._pasteFile = file;
                    };
                    reader.readAsDataURL(file);
                    return;
                }
            }
        },

        cancelPaste() {
            this.pastePreview = null;
            this._pasteFile = null;
        },

        sendPastedImage() {
            if (!this._pasteFile || !this.currentRoom) return;
            // 파일명 생성: clipboard_YYYYMMDD_HHmmss.png
            const now = new Date();
            const ts = now.getFullYear().toString() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            const ext = this._pasteFile.type.split('/')[1] || 'png';
            const named = new File([this._pasteFile], `clipboard_${ts}.${ext}`, { type: this._pasteFile.type });

            this.uploadFile(named);
            this.pastePreview = null;
            this._pasteFile = null;
        },

        handleFileSelect(e) {
            const files = e.target.files;
            if (files?.length) this.uploadFiles(files);
            e.target.value = '';
        },

        async uploadFiles(files) {
            for (const file of files) {
                this.uploadFile(file);
            }
        },

        async uploadFile(file) {
            const ext = file.name.split('.').pop().toLowerCase();
            const audioExts = ['mp3', 'wav', 'ogg', 'm4a', 'flac', 'webm', 'mp4', 'aac'];
            const isAudio = audioExts.includes(ext);

            const idx = this.uploads.length;
            this.uploads.push({ name: file.name, progress: 0 });

            const formData = new FormData();
            const endpoint = isAudio
                ? `/api/rooms/${this.currentRoom.id}/audio`
                : `/api/rooms/${this.currentRoom.id}/files`;

            // 서버 routes_messages.py는 'file' 키를 사용
            formData.append('file', file);

            try {
                await new Promise((resolve, reject) => {
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', API_BASE + endpoint);
                    xhr.setRequestHeader('Authorization', 'Bearer ' + this.token);

                    xhr.upload.onprogress = (e) => {
                        if (e.lengthComputable) {
                            this.uploads[idx].progress = Math.round((e.loaded / e.total) * 100);
                        }
                    };

                    xhr.onload = () => {
                        if (xhr.status >= 200 && xhr.status < 300) {
                            resolve();
                        } else {
                            reject(new Error(xhr.statusText));
                        }
                    };
                    xhr.onerror = () => reject(new Error('네트워크 오류'));
                    xhr.send(formData);
                });

                this.toast(`${file.name} 업로드 완료`, 'success');
            } catch (err) {
                this.toast(`${file.name} 업로드 실패: ${err.message}`, 'error');
            }

            // Remove from upload list after brief delay
            setTimeout(() => {
                this.uploads = this.uploads.filter((_, i) => i !== idx);
            }, 1500);
        },

        // ============================================================
        // Audio Recording (MediaRecorder API)
        // ============================================================
        async startRecording() {
            if (!this.currentRoom) {
                this.toast('먼저 채팅방을 선택하세요', 'error');
                return;
            }

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this._audioChunks = [];
                this._mediaRecorder = new MediaRecorder(stream, {
                    mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                        ? 'audio/webm;codecs=opus' : 'audio/webm'
                });

                this._mediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) this._audioChunks.push(e.data);
                };

                this._mediaRecorder.onstop = () => {
                    stream.getTracks().forEach(t => t.stop());
                };

                this._mediaRecorder.start(1000); // chunk every 1s
                this.isRecording = true;
                this._recordingStart = Date.now();
                this._recordingTimer = setInterval(() => {
                    const elapsed = Math.floor((Date.now() - this._recordingStart) / 1000);
                    const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
                    const s = String(elapsed % 60).padStart(2, '0');
                    this.recordingTime = `${m}:${s}`;
                }, 200);

            } catch (err) {
                this.toast('마이크 접근 권한이 필요합니다', 'error');
            }
        },

        async stopRecording() {
            if (!this._mediaRecorder) return;

            return new Promise((resolve) => {
                this._mediaRecorder.onstop = () => {
                    // Stop all tracks
                    if (this._mediaRecorder.stream) {
                        this._mediaRecorder.stream.getTracks().forEach(t => t.stop());
                    }

                    const blob = new Blob(this._audioChunks, { type: 'audio/webm' });
                    const now = new Date();
                    const filename = `recording_${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}_${String(now.getHours()).padStart(2,'0')}${String(now.getMinutes()).padStart(2,'0')}${String(now.getSeconds()).padStart(2,'0')}.webm`;
                    const file = new File([blob], filename, { type: 'audio/webm' });

                    this._cleanup();
                    this.uploadFile(file);
                    resolve();
                };

                this._mediaRecorder.stop();
            });
        },

        cancelRecording() {
            if (this._mediaRecorder) {
                this._mediaRecorder.stream?.getTracks().forEach(t => t.stop());
                this._mediaRecorder.stop();
            }
            this._cleanup();
        },

        _cleanup() {
            clearInterval(this._recordingTimer);
            this.isRecording = false;
            this.recordingTime = '00:00';
            this._mediaRecorder = null;
            this._audioChunks = [];
        },

        // ============================================================
        // Summaries  [fix #1] - 올바른 응답 필드 매핑
        // ============================================================
        async loadSummaries(query) {
            if (!this.currentRoom) return;
            let url = `/api/audio/summaries?room_id=${this.currentRoom.id}&per_page=50`;
            if (query) url += `&q=${encodeURIComponent(query)}`;
            const res = await this.api(url);
            if (res?.ok) {
                const data = await res.json();
                this.summaries = data.audio_files || data.summaries || data.items || [];
                this.summarySearchTotal = query ? (data.total ?? this.summaries.length) : -1;
                // 빈 배열이면 메시지에서 audio가 있는 것들을 fallback으로 표시
                if (!query && this.summaries.length === 0) {
                    this.summaries = this.messages
                        .filter(m => m.audio && m.audio.transcript_summary)
                        .map(m => ({
                            id: m.audio.id,
                            original_filename: m.audio.original_filename,
                            transcript_summary: m.audio.transcript_summary,
                            created_at: m.created_at,
                            duration_seconds: m.audio.duration_seconds,
                        }));
                }
            }
        },

        async searchSummaries() {
            const q = this.summarySearchQuery.trim();
            if (!q) return;
            await this.loadSummaries(q);
        },

        async clearSummarySearch() {
            this.summarySearchQuery = '';
            this.summarySearchTotal = -1;
            await this.loadSummaries();
        },

        // ============================================================
        // Audio: fetch as blob for playback [fix #2 + #6]
        // ============================================================
        async playAudioBtn(msg) {
            if (!msg.audio?.id) return;
            const el = document.getElementById('audio-el-' + msg.id);
            if (!el) return;

            // Already loaded - toggle play/pause
            if (msg._audioLoaded && el.src && el.src.startsWith('blob:')) {
                if (el.paused) {
                    el.play();
                } else {
                    el.pause();
                }
                return;
            }

            // Fetch audio as blob via server proxy
            msg._audioLoading = true;
            try {
                const res = await this.api(`/api/audio/${msg.audio.id}/download`);
                if (res?.ok) {
                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);
                    el.src = url;
                    el.load();
                    msg._audioLoaded = true;
                    await el.play();
                } else if (res?.status === 404) {
                    this.toast('파일이 만료되었습니다', 'error');
                } else {
                    this.toast('오디오 재생 실패', 'error');
                }
            } catch (e) {
                this.toast('오디오 로드 실패: ' + e.message, 'error');
            } finally {
                msg._audioLoading = false;
            }
        },

        async playAudio(audioId, el) {
            // Legacy fallback - kept for compatibility
            if (!audioId || !el) return;
            if (el.src && el.src.startsWith('blob:')) return;
            el.pause();
            try {
                const res = await this.api(`/api/audio/${audioId}/download`);
                if (res?.ok) {
                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);
                    el.src = url;
                    await el.load();
                    el.play();
                } else if (res?.status === 404) {
                    this.toast('파일이 만료되었습니다', 'error');
                } else {
                    this.toast('오디오 재생 실패', 'error');
                }
            } catch (e) {
                this.toast('오디오 로드 실패: ' + e.message, 'error');
            }
        },


        // [fix #6] 파일 다운로드 - fetch + blob 방식
        async downloadAudio(audioId, filename) {
            try {
                const res = await this.api(`/api/audio/${audioId}/download`);
                if (res?.ok) {
                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename || 'audio';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                } else {
                    this.toast('다운로드 실패', 'error');
                }
            } catch (e) {
                this.toast('다운로드 실패: ' + e.message, 'error');
            }
        },

        async downloadSummaryPdf(audioId, filename) {
            try {
                const res = await this.api(`/api/audio/${audioId}/summary-pdf`);
                if (res?.ok) {
                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    const base = (filename || 'audio').replace(/\.[^.]+$/, '');
                    a.download = base + '_요약.pdf';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                } else {
                    const err = await res.json().catch(() => null);
                    this.toast(err?.error || '요약 PDF 다운로드 실패', 'error');
                }
            } catch (e) {
                this.toast('요약 PDF 다운로드 실패: ' + e.message, 'error');
            }
        },

        // ============================================================
        // Keyboard shortcuts
        // ============================================================
        handleGlobalKeydown(e) {
            // Ctrl+N: new room
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                this.showCreateRoom = true;
            }
            // Ctrl+F: search
            if (e.ctrlKey && e.key === 'f' && this.currentRoom) {
                e.preventDefault();
                this.toggleSearch();
            }
            // Ctrl+R: record
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                if (this.isRecording) this.stopRecording();
                else this.startRecording();
            }
            // Escape: close panels/modals
            if (e.key === 'Escape') {
                if (this.showCreateRoom) this.showCreateRoom = false;
                else if (this.showJoinRoom) this.showJoinRoom = false;
                else if (this.showSearch) this.closeSearch();
                else if (this.showSettings) this.showSettings = false;
                else if (this.showDetail) this.showDetail = false;
                else if (this.showSummaries) this.showSummaries = false;
                else if (this.isRecording) this.cancelRecording();
            }
        },

        // ============================================================
        // ============================================================
        // Image fullscreen viewer
        // ============================================================
        openImageFullscreen(msg) {
            const driveUrl = msg.file_drive_url;
            const thumbnailUrl = msg.file_thumbnail_path
                ? (API_BASE + '/api/files/' + msg.file_id + '/thumbnail')
                : null;
            const fullUrl = msg.file_id
                ? (API_BASE + '/api/files/' + msg.file_id + '/download?token=' + this.token + '&inline=1')
                : driveUrl;
            if (!fullUrl) return;

            // Create overlay
            const overlay = document.createElement('div');
            overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.95);z-index:10000;display:flex;align-items:center;justify-content:center;cursor:pointer;';
            overlay.onclick = () => overlay.remove();

            // Close button
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '&times;';
            closeBtn.style.cssText = 'position:absolute;top:16px;right:16px;background:none;border:none;color:white;font-size:32px;cursor:pointer;z-index:10001;';
            overlay.appendChild(closeBtn);

            // Filename
            if (msg.file_name) {
                const nameEl = document.createElement('div');
                nameEl.textContent = msg.file_name;
                nameEl.style.cssText = 'position:absolute;top:20px;left:20px;color:white;font-size:14px;z-index:10001;';
                overlay.appendChild(nameEl);
            }

            const img = document.createElement('img');
            img.src = fullUrl;
            img.style.cssText = 'max-width:90vw;max-height:90vh;object-fit:contain;';
            img.onclick = (e) => e.stopPropagation();
            img.onerror = () => {
                img.style.display = 'none';
                const expiredEl = document.createElement('div');
                expiredEl.style.cssText = 'text-align:center;color:white;';
                expiredEl.innerHTML = '<div style="font-size:48px;margin-bottom:16px;">🖼️</div>'
                    + '<div style="color:#aaa;margin-bottom:16px;">보관 기간이 만료되었습니다</div>'
                    + (driveUrl ? '<a href="' + driveUrl + '" target="_blank" rel="noopener" '
                        + 'style="color:#4fc3f7;text-decoration:underline;" '
                        + 'onclick="event.stopPropagation();">Google Drive에서 확인</a>' : '');
                overlay.appendChild(expiredEl);
            };
            overlay.appendChild(img);

            document.body.appendChild(overlay);

            // ESC to close
            const escHandler = (e) => { if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', escHandler); } };
            document.addEventListener('keydown', escHandler);
        },

        // Formatting helpers
        // ============================================================
        formatTime(ts) {
            if (!ts) return '';
            const d = new Date(ts);
            return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
        },

        formatTimeShort(ts) {
            if (!ts) return '';
            const d = new Date(ts);
            const now = new Date();
            const diff = now - d;
            if (diff < 86400000 && d.getDate() === now.getDate()) {
                return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
            }
            if (diff < 172800000) return '어제';
            return `${d.getMonth()+1}/${d.getDate()}`;
        },

        formatDate(ts) {
            if (!ts) return '';
            const d = new Date(ts);
            return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' });
        },

        formatDuration(seconds) {
            if (!seconds) return '';
            const m = Math.floor(seconds / 60);
            const s = Math.round(seconds % 60);
            return `${m}:${String(s).padStart(2, '0')}`;
        },

        audioStatusText(status) {
            const map = {
                'uploading': '업로드 중...',
                'transcribing': '음성 인식 중...',
                'summarizing': '요약 생성 중...',
                'completed': '완료',
                'failed': '실패',
            };
            return map[status] || status;
        },

        renderContent(text) {
            if (!text) return '';
            // XSS protection
            let html = text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            // Basic markdown: bold, italic, inline code
            html = html
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>')
                .replace(/`(.+?)`/g, '<code style="background:#f0f0f0;padding:1px 4px;border-radius:3px;font-size:0.9em;">$1</code>');
            // Horizontal rule
            html = html.replace(/^---$/gm, '<hr style="border:none;border-top:1px solid #e0e0e0;margin:8px 0;">');
            // URLs → clickable links
            html = html.replace(
                /(https?:\/\/[^\s<>"']+)/g,
                '<a href="$1" target="_blank" rel="noopener" style="color:inherit;text-decoration:underline;">$1</a>'
            );
            // Line breaks
            html = html.replace(/\n/g, '<br>');
            return html;
        },

        autoResize(el) {
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 120) + 'px';
        },

        // ============================================================
        // Expand/collapse (Map-based for x-for + template x-if)
        // ============================================================
        toggleExpand(msgId) {
            const copy = { ...this._expandedMsgs };
            copy[msgId] = !copy[msgId];
            this._expandedMsgs = copy;
        },

        isExpanded(msgId) {
            return !!this._expandedMsgs[msgId];
        },

        // ============================================================
        // Dark mode
        // ============================================================
        toggleDark() {
            this.darkMode = !this.darkMode;
            document.body.classList.toggle('dark', this.darkMode);
            localStorage.setItem('proptalk_dark', this.darkMode);
        },

        // ============================================================
        // Toast notifications  [fix #4] - 이전 토스트 자동 제거
        // ============================================================
        toast(message, type = 'info') {
            // 같은 타입의 기존 토스트 제거 (중복 방지)
            this.toasts = this.toasts.filter(x => x.type !== type);
            const t = { message, type, id: Date.now() };
            this.toasts.push(t);
            setTimeout(() => {
                this.toasts = this.toasts.filter(x => x.id !== t.id);
            }, 3000);
        },

        // ============================================================
        // Message context menu + delete + reactions
        // ============================================================
        showMsgMenu(event, msg) {
            // 위치 계산 (화면 밖으로 나가지 않도록)
            const x = Math.min(event.clientX, window.innerWidth - 200);
            const y = Math.min(event.clientY, window.innerHeight - 250);
            this.msgMenu = { show: true, x, y, msg };
        },

        isRoomAdmin() {
            if (!this.currentRoom || !this.members || !this.user) return false;
            const me = this.members.find(m => m.id === this.user.id);
            return me?.role === 'admin';
        },

        replyToMsg(msg) {
            if (msg) {
                const preview = msg.type === 'audio'
                    ? (msg.audio?.original_filename || '음성 메시지')
                    : (msg.content || '').substring(0, 50);
                this.replyTo = {
                    id: msg.id,
                    content: preview,
                    user_name: msg._userName || msg.user_name || '알 수 없음',
                    type: msg.type,
                };
                this.$nextTick(() => this.$refs.chatInput?.focus());
            }
        },

        cancelReply() {
            this.replyTo = null;
        },

        copyMsgContent(msg) {
            if (!msg) return;
            let text = msg.content || '';
            // 음성 메시지면 요약도 포함
            if (msg.type === 'audio' && msg.audio?.transcript_summary) {
                text += '\n\n' + msg.audio.transcript_summary;
            }
            navigator.clipboard.writeText(text).then(() => {
                this.toast('복사되었습니다', 'info');
            });
        },

        confirmDeleteMsg(msg) {
            if (!msg) return;
            let text = '이 메시지를 삭제하시겠습니까?';
            if (msg.type === 'audio') text += '\nGoogle Drive 파일과 기록도 함께 삭제됩니다.';
            else if (msg.type === 'file') text += '\nGoogle Drive 파일도 함께 삭제됩니다.';
            this.deleteConfirm = { show: true, msg, text };
        },

        async executeDeleteMsg() {
            const msg = this.deleteConfirm.msg;
            this.deleteConfirm.show = false;
            if (!msg) return;
            try {
                const res = await this.api(`/api/messages/${msg.id}`, { method: 'DELETE' });
                if (res?.ok) {
                    const data = await res.json();
                    const ids = new Set(data.deleted_ids || [msg.id]);
                    this.messages = this.messages.filter(m => !ids.has(m.id));
                    this.toast('메시지가 삭제되었습니다', 'info');
                } else {
                    const err = await res?.json().catch(() => ({}));
                    this.toast(err.error || '삭제 실패', 'error');
                }
            } catch (e) {
                this.toast('삭제 실패: ' + e.message, 'error');
            }
        },

        async toggleReaction(messageId, emoji) {
            if (!messageId || !emoji) return;
            try {
                const res = await this.api(`/api/messages/${messageId}/reactions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ emoji }),
                });
                if (res?.ok) {
                    const data = await res.json();
                    const msg = this.messages.find(m => m.id === messageId);
                    if (msg) msg.reactions = data.reactions;
                }
            } catch (e) {
                console.error('[Reaction]', e);
            }
        },

        groupReactions(reactions) {
            if (!reactions || !reactions.length) return [];
            const groups = {};
            for (const r of reactions) {
                if (!groups[r.emoji]) {
                    groups[r.emoji] = { emoji: r.emoji, count: 0, mine: false, users: [] };
                }
                groups[r.emoji].count++;
                groups[r.emoji].users.push(r.user_name);
                if (r.user_id === this.user?.id) groups[r.emoji].mine = true;
            }
            return Object.values(groups);
        },
    };
}
