document.addEventListener('DOMContentLoaded', function() {
    // 샘플 데이터
    const users = [
        {"id": 1, "username": "sales1", "role": "sales", "name": "김영업", "password": "1234"},
        {"id": 2, "username": "sales2", "role": "sales", "name": "이세일즈", "password": "1234"},
        {"id": 3, "username": "manager1", "role": "manager", "name": "박관리", "password": "1234"}
    ];
    
    const followups = [
        {"id": 1, "userId": 1, "customerName": "홍길동", "company": "ABC회사", "status": "active", "priority": "high", "createdAt": "2025-06-10"},
        {"id": 2, "userId": 1, "customerName": "김고객", "company": "XYZ그룹", "status": "active", "priority": "medium", "createdAt": "2025-06-12"},
        {"id": 3, "userId": 2, "customerName": "이클라이언트", "company": "DEF기업", "status": "completed", "priority": "low", "createdAt": "2025-06-08"}
    ];
    
    const schedules = [
        {"id": 1, "userId": 1, "followupId": 1, "visitDate": "2025-06-20", "visitTime": "14:00", "location": "ABC회사 본사", "status": "scheduled"},
        {"id": 2, "userId": 1, "followupId": 2, "visitDate": "2025-06-22", "visitTime": "10:00", "location": "XYZ그룹 강남지점", "status": "scheduled"}
    ];
    
    const histories = [
        {"id": 1, "followupId": 1, "userId": 1, "actionType": "call", "content": "초기 상담 진행. 제품 관심도 높음", "createdAt": "2025-06-10T09:30:00"},
        {"id": 2, "followupId": 1, "userId": 1, "actionType": "email", "content": "제품 카탈로그 및 견적서 발송", "createdAt": "2025-06-11T16:20:00"}
    ];
    
    const researches = [
        {"id": 1, "scheduleId": 1, "userId": 1, "customerInfo": "IT 솔루션 전문 기업, 직원 50명", "marketAnalysis": "경쟁사 대비 가격 경쟁력 있음", "notes": "의사결정권자는 CTO, 예산 승인 6월말 예정"}
    ];
    
    // 애플리케이션 상태
    let state = {
        currentUser: null,
        currentTab: 'dashboard',
        currentMonth: new Date(),
        currentFollowupId: null,
        currentScheduleId: null,
        nextId: {
            followup: 4,
            schedule: 3,
            history: 3,
            research: 2
        },
        data: {
            users: [...users],
            followups: [...followups],
            schedules: [...schedules],
            histories: [...histories],
            researches: [...researches]
        }
    };
    
    // 로그인 폼 이벤트 리스너
    document.getElementById('loginForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        const user = state.data.users.find(u => u.username === username && u.password === password);
        
        if (user) {
            state.currentUser = user;
            showMainApp();
        } else {
            alert('잘못된 사용자명 또는 비밀번호입니다.');
        }
    });
    
    // 로그아웃 버튼 이벤트 리스너
    document.getElementById('logoutBtn').addEventListener('click', function() {
        state.currentUser = null;
        showLoginPage();
    });
    
    // 네비게이션 탭 이벤트 리스너 (이벤트 위임)
    document.getElementById('navTabs').addEventListener('click', function(e) {
        if (e.target.classList.contains('nav-tab')) {
            switchTab(e.target.dataset.tab);
        }
    });
    
    // 팔로우업 추가 버튼
    document.getElementById('addFollowupBtn').addEventListener('click', function() {
        openFollowupModal();
    });
    
    // 일정 추가 버튼
    document.getElementById('addScheduleBtn').addEventListener('click', function() {
        openScheduleModal();
    });
    
    // 팔로우업 폼 제출
    document.getElementById('followupForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveFollowup();
    });
    
    // 일정 폼 제출
    document.getElementById('scheduleForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSchedule();
    });
    
    // 히스토리 폼 제출
    document.getElementById('historyForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveHistory();
    });
    
    // 사전조사 폼 제출
    document.getElementById('researchForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveResearch();
    });
    
    // 달력 이전 월 버튼
    document.getElementById('prevMonth').addEventListener('click', function() {
        state.currentMonth.setMonth(state.currentMonth.getMonth() - 1);
        renderCalendar();
    });
    
    // 달력 다음 월 버튼
    document.getElementById('nextMonth').addEventListener('click', function() {
        state.currentMonth.setMonth(state.currentMonth.getMonth() + 1);
        renderCalendar();
    });
    
    // 관리자 필터 변경
    document.getElementById('salesPersonFilter').addEventListener('change', function() {
        renderTeamReport();
    });
    
    // 모달 닫기 버튼
    document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
        btn.addEventListener('click', closeModal);
    });
    
    // 모달 배경 클릭 시 닫기
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    });
    
    // 초기 화면 표시
    showLoginPage();
    
    // 함수 정의
    function showLoginPage() {
        document.getElementById('loginPage').classList.remove('hidden');
        document.getElementById('mainApp').classList.add('hidden');
        document.getElementById('loginForm').reset();
    }
    
    function showMainApp() {
        document.getElementById('loginPage').classList.add('hidden');
        document.getElementById('mainApp').classList.remove('hidden');
        
        // 사용자 정보 표시
        document.getElementById('userInfo').textContent = `${state.currentUser.name} (${state.currentUser.role === 'sales' ? '영업사원' : '관리자'})`;
        
        // 역할별 UI 설정
        document.body.className = state.currentUser.role;
        
        setupNavigation();
        switchTab('dashboard');
    }
    
    function setupNavigation() {
        const navTabs = document.getElementById('navTabs');
        const tabs = [
            { id: 'dashboard', label: '대시보드', roles: ['sales', 'manager'] },
            { id: 'followup', label: '팔로우업', roles: ['sales', 'manager'] },
            { id: 'schedule', label: '일정', roles: ['sales', 'manager'] },
            { id: 'report', label: '팀 보고서', roles: ['manager'] }
        ];
        
        navTabs.innerHTML = tabs
            .filter(tab => tab.roles.includes(state.currentUser.role))
            .map(tab => `<button class="nav-tab" data-tab="${tab.id}">${tab.label}</button>`)
            .join('');
    }
    
    function switchTab(tabId) {
        state.currentTab = tabId;
        
        // 탭 활성화
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.tab === tabId) {
                tab.classList.add('active');
            }
        });
        
        // 콘텐츠 표시
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        document.getElementById(`${tabId}Tab`).classList.remove('hidden');
        
        // 탭별 렌더링
        switch (tabId) {
            case 'dashboard':
                renderDashboard();
                break;
            case 'followup':
                renderFollowups();
                break;
            case 'schedule':
                renderSchedules();
                break;
            case 'report':
                renderTeamReport();
                break;
        }
    }
    
    function renderDashboard() {
        const userFollowups = getUserFollowups();
        const userSchedules = getUserSchedules();
        
        // 통계 업데이트
        document.getElementById('totalFollowups').textContent = userFollowups.length;
        document.getElementById('activeFollowups').textContent = userFollowups.filter(f => f.status === 'active').length;
        document.getElementById('upcomingVisits').textContent = userSchedules.filter(s => s.status === 'scheduled').length;
        
        // 최근 활동 렌더링
        renderRecentActivities();
    }
    
    function renderRecentActivities() {
        const container = document.getElementById('recentActivities');
        const userHistories = state.data.histories
            .filter(h => h.userId === state.currentUser.id)
            .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
            .slice(0, 5);
        
        if (userHistories.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>최근 활동이 없습니다.</p></div>';
            return;
        }
        
        container.innerHTML = userHistories.map(history => {
            const followup = state.data.followups.find(f => f.id === history.followupId);
            const actionTypeLabels = {
                call: '전화', email: '이메일', meeting: '미팅', visit: '방문', other: '기타'
            };
            
            return `
                <div class="activity-item">
                    <div class="activity-item__header">
                        <h5 class="activity-item__title">${followup ? followup.customerName : '알 수 없음'} - ${actionTypeLabels[history.actionType]}</h5>
                        <span class="activity-item__time">${formatDateTime(history.createdAt)}</span>
                    </div>
                    <p class="activity-item__content">${history.content}</p>
                </div>
            `;
        }).join('');
    }
    
    function renderFollowups() {
        const container = document.getElementById('followupList');
        const userFollowups = getUserFollowups();
        
        if (userFollowups.length === 0) {
            container.innerHTML = '<div class="empty-state"><h4>팔로우업이 없습니다</h4><p>새로운 팔로우업을 추가해보세요.</p></div>';
            return;
        }
        
        container.innerHTML = userFollowups.map(followup => {
            const histories = state.data.histories.filter(h => h.followupId === followup.id);
            
            return `
                <div class="followup-item">
                    <div class="followup-item__header">
                        <div class="followup-item__info">
                            <h4>${followup.customerName}</h4>
                            <p>${followup.company}</p>
                        </div>
                        <div class="followup-item__meta">
                            <span class="status priority-${followup.priority}">${getPriorityLabel(followup.priority)}</span>
                            <span class="status status-${followup.status}">${getStatusLabel(followup.status)}</span>
                        </div>
                    </div>
                    <div class="followup-item__actions">
                        ${state.currentUser.role === 'sales' ? `
                            <button class="btn btn--sm btn--primary" onclick="openHistoryModal(${followup.id})">활동 추가</button>
                            <button class="btn btn--sm btn--secondary" onclick="editFollowup(${followup.id})">수정</button>
                            <button class="btn btn--sm btn--outline" onclick="deleteFollowup(${followup.id})">삭제</button>
                        ` : ''}
                    </div>
                    ${histories.length > 0 ? `
                        <div class="followup-item__history">
                            <h5>활동 히스토리</h5>
                            <div class="history-list">
                                ${histories.map(history => `
                                    <div class="history-item">
                                        <div class="history-item__header">
                                            <span class="history-item__type">${getActionTypeLabel(history.actionType)}</span>
                                            <span class="history-item__time">${formatDateTime(history.createdAt)}</span>
                                        </div>
                                        <p class="history-item__content">${history.content}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }
    
    function renderSchedules() {
        renderCalendar();
        renderScheduleList();
    }
    
    function renderCalendar() {
        const calendar = document.getElementById('calendar');
        const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
        const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
        
        document.getElementById('currentMonth').textContent = 
            `${state.currentMonth.getFullYear()}년 ${monthNames[state.currentMonth.getMonth()]}`;
        
        const firstDay = new Date(state.currentMonth.getFullYear(), state.currentMonth.getMonth(), 1);
        const lastDay = new Date(state.currentMonth.getFullYear(), state.currentMonth.getMonth() + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());
        
        const userSchedules = getUserSchedules();
        const today = new Date();
        
        let html = '';
        
        // 요일 헤더
        weekdays.forEach(day => {
            html += `<div class="calendar-weekday">${day}</div>`;
        });
        
        // 날짜 셀
        const current = new Date(startDate);
        for (let i = 0; i < 42; i++) {
            const dateStr = current.toISOString().split('T')[0];
            const hasEvent = userSchedules.some(s => s.visitDate === dateStr);
            const isToday = current.toDateString() === today.toDateString();
            const isCurrentMonth = current.getMonth() === state.currentMonth.getMonth();
            
            let classes = ['calendar-day'];
            if (hasEvent) classes.push('has-event');
            if (isToday) classes.push('today');
            if (!isCurrentMonth) classes.push('other-month');
            
            html += `<div class="${classes.join(' ')}">${current.getDate()}</div>`;
            current.setDate(current.getDate() + 1);
        }
        
        calendar.innerHTML = html;
    }
    
    function renderScheduleList() {
        const container = document.getElementById('scheduleList');
        const userSchedules = getUserSchedules()
            .filter(s => s.status === 'scheduled')
            .sort((a, b) => new Date(a.visitDate) - new Date(b.visitDate));
        
        if (userSchedules.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>예정된 방문이 없습니다.</p></div>';
            return;
        }
        
        container.innerHTML = userSchedules.map(schedule => {
            const followup = state.data.followups.find(f => f.id === schedule.followupId);
            const research = state.data.researches.find(r => r.scheduleId === schedule.id);
            
            return `
                <div class="schedule-item">
                    <div class="schedule-item__header">
                        <h4 class="schedule-item__title">${followup ? followup.customerName : '알 수 없음'}</h4>
                        <span class="status status-${schedule.status}">${getScheduleStatusLabel(schedule.status)}</span>
                    </div>
                    <div class="schedule-item__details">
                        <div><strong>회사:</strong> ${followup ? followup.company : '-'}</div>
                        <div><strong>날짜:</strong> ${formatDate(schedule.visitDate)}</div>
                        <div><strong>시간:</strong> ${schedule.visitTime}</div>
                        <div><strong>장소:</strong> ${schedule.location}</div>
                    </div>
                    ${state.currentUser.role === 'sales' ? `
                        <div class="schedule-item__actions">
                            ${!research ? `<button class="btn btn--sm btn--primary" onclick="openResearchModal(${schedule.id})">사전조사</button>` : ''}
                            <button class="btn btn--sm btn--secondary" onclick="editSchedule(${schedule.id})">수정</button>
                            <button class="btn btn--sm btn--outline" onclick="deleteSchedule(${schedule.id})">삭제</button>
                        </div>
                    ` : ''}
                    ${research ? `
                        <div class="schedule-item__research">
                            <h5>사전조사 내용</h5>
                            <div><strong>고객 정보:</strong> ${research.customerInfo}</div>
                            <div><strong>시장 분석:</strong> ${research.marketAnalysis}</div>
                            ${research.notes ? `<div><strong>추가 메모:</strong> ${research.notes}</div>` : ''}
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }
    
    function renderTeamReport() {
        if (state.currentUser.role !== 'manager') return;
        
        const salesFilter = document.getElementById('salesPersonFilter');
        const selectedUserId = salesFilter.value ? parseInt(salesFilter.value) : null;
        
        // 영업사원 필터 옵션 업데이트
        const salesUsers = state.data.users.filter(u => u.role === 'sales');
        salesFilter.innerHTML = '<option value="">전체 영업사원</option>' +
            salesUsers.map(user => `<option value="${user.id}">${user.name}</option>`).join('');
        
        // 통계 계산
        const followups = selectedUserId ? 
            state.data.followups.filter(f => f.userId === selectedUserId) : 
            state.data.followups;
        
        const schedules = selectedUserId ?
            state.data.schedules.filter(s => s.userId === selectedUserId) :
            state.data.schedules;
        
        document.getElementById('teamTotalFollowups').textContent = followups.length;
        document.getElementById('teamActiveFollowups').textContent = followups.filter(f => f.status === 'active').length;
        document.getElementById('teamScheduledVisits').textContent = schedules.filter(s => s.status === 'scheduled').length;
        
        // 팀 활동 렌더링
        renderTeamActivities(selectedUserId);
    }
    
    function renderTeamActivities(userId = null) {
        const container = document.getElementById('teamActivities');
        const histories = userId ?
            state.data.histories.filter(h => h.userId === userId) :
            state.data.histories;
        
        const sortedHistories = histories
            .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
            .slice(0, 10);
        
        if (sortedHistories.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>활동이 없습니다.</p></div>';
            return;
        }
        
        container.innerHTML = sortedHistories.map(history => {
            const user = state.data.users.find(u => u.id === history.userId);
            const followup = state.data.followups.find(f => f.id === history.followupId);
            
            return `
                <div class="activity-item">
                    <div class="activity-item__header">
                        <h5 class="activity-item__title">${user ? user.name : '알 수 없음'} - ${followup ? followup.customerName : '알 수 없음'}</h5>
                        <span class="activity-item__time">${formatDateTime(history.createdAt)}</span>
                    </div>
                    <p class="activity-item__content">${getActionTypeLabel(history.actionType)}: ${history.content}</p>
                </div>
            `;
        }).join('');
    }
    
    // 모달 관련 함수들
    function openFollowupModal(followupId = null) {
        const modal = document.getElementById('followupModal');
        const form = document.getElementById('followupForm');
        const title = document.getElementById('followupModalTitle');
        
        if (followupId) {
            const followup = state.data.followups.find(f => f.id === followupId);
            title.textContent = '팔로우업 수정';
            document.getElementById('customerName').value = followup.customerName;
            document.getElementById('companyName').value = followup.company;
            document.getElementById('priority').value = followup.priority;
            document.getElementById('status').value = followup.status;
            state.currentFollowupId = followupId;
        } else {
            title.textContent = '새 팔로우업';
            form.reset();
            state.currentFollowupId = null;
        }
        
        modal.style.display = 'block';
    }
    
    function openScheduleModal(scheduleId = null) {
        const modal = document.getElementById('scheduleModal');
        const form = document.getElementById('scheduleForm');
        const title = document.getElementById('scheduleModalTitle');
        const followupSelect = document.getElementById('scheduleFollowup');
        
        // 팔로우업 옵션 설정
        const userFollowups = getUserFollowups();
        followupSelect.innerHTML = userFollowups.map(f => 
            `<option value="${f.id}">${f.customerName} (${f.company})</option>`
        ).join('');
        
        if (scheduleId) {
            const schedule = state.data.schedules.find(s => s.id === scheduleId);
            title.textContent = '일정 수정';
            document.getElementById('scheduleFollowup').value = schedule.followupId;
            document.getElementById('visitDate').value = schedule.visitDate;
            document.getElementById('visitTime').value = schedule.visitTime;
            document.getElementById('visitLocation').value = schedule.location;
            state.currentScheduleId = scheduleId;
        } else {
            title.textContent = '새 일정';
            form.reset();
            state.currentScheduleId = null;
        }
        
        modal.style.display = 'block';
    }
    
    function openHistoryModal(followupId) {
        const modal = document.getElementById('historyModal');
        const form = document.getElementById('historyForm');
        
        state.currentFollowupId = followupId;
        form.reset();
        modal.style.display = 'block';
    }
    
    function openResearchModal(scheduleId) {
        const modal = document.getElementById('researchModal');
        const form = document.getElementById('researchForm');
        
        state.currentScheduleId = scheduleId;
        form.reset();
        modal.style.display = 'block';
    }
    
    function closeModal() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
        state.currentFollowupId = null;
        state.currentScheduleId = null;
    }
    
    // CRUD 관련 함수들
    function saveFollowup() {
        const customerName = document.getElementById('customerName').value;
        const companyName = document.getElementById('companyName').value;
        const priority = document.getElementById('priority').value;
        const status = document.getElementById('status').value;
        
        if (state.currentFollowupId) {
            // 수정
            const index = state.data.followups.findIndex(f => f.id === state.currentFollowupId);
            state.data.followups[index] = {
                ...state.data.followups[index],
                customerName,
                company: companyName,
                priority,
                status
            };
        } else {
            // 추가
            state.data.followups.push({
                id: state.nextId.followup++,
                userId: state.currentUser.id,
                customerName,
                company: companyName,
                status,
                priority,
                createdAt: new Date().toISOString().split('T')[0]
            });
        }
        
        closeModal();
        renderFollowups();
        if (state.currentTab === 'dashboard') {
            renderDashboard();
        }
    }
    
    function saveSchedule() {
        const followupId = parseInt(document.getElementById('scheduleFollowup').value);
        const visitDate = document.getElementById('visitDate').value;
        const visitTime = document.getElementById('visitTime').value;
        const location = document.getElementById('visitLocation').value;
        
        if (state.currentScheduleId) {
            // 수정
            const index = state.data.schedules.findIndex(s => s.id === state.currentScheduleId);
            state.data.schedules[index] = {
                ...state.data.schedules[index],
                followupId,
                visitDate,
                visitTime,
                location
            };
        } else {
            // 추가
            state.data.schedules.push({
                id: state.nextId.schedule++,
                userId: state.currentUser.id,
                followupId,
                visitDate,
                visitTime,
                location,
                status: 'scheduled'
            });
        }
        
        closeModal();
        renderSchedules();
        if (state.currentTab === 'dashboard') {
            renderDashboard();
        }
    }
    
    function saveHistory() {
        const actionType = document.getElementById('actionType').value;
        const content = document.getElementById('historyContent').value;
        
        state.data.histories.push({
            id: state.nextId.history++,
            followupId: state.currentFollowupId,
            userId: state.currentUser.id,
            actionType,
            content,
            createdAt: new Date().toISOString()
        });
        
        closeModal();
        renderFollowups();
        if (state.currentTab === 'dashboard') {
            renderDashboard();
        }
    }
    
    function saveResearch() {
        const customerInfo = document.getElementById('customerInfo').value;
        const marketAnalysis = document.getElementById('marketAnalysis').value;
        const notes = document.getElementById('researchNotes').value;
        
        state.data.researches.push({
            id: state.nextId.research++,
            scheduleId: state.currentScheduleId,
            userId: state.currentUser.id,
            customerInfo,
            marketAnalysis,
            notes
        });
        
        closeModal();
        renderSchedules();
    }
    
    function editFollowup(id) {
        openFollowupModal(id);
    }
    
    function deleteFollowup(id) {
        if (confirm('정말 이 팔로우업을 삭제하시겠습니까?')) {
            state.data.followups = state.data.followups.filter(f => f.id !== id);
            renderFollowups();
            if (state.currentTab === 'dashboard') {
                renderDashboard();
            }
        }
    }
    
    function editSchedule(id) {
        openScheduleModal(id);
    }
    
    function deleteSchedule(id) {
        if (confirm('정말 이 일정을 삭제하시겠습니까?')) {
            state.data.schedules = state.data.schedules.filter(s => s.id !== id);
            renderSchedules();
            if (state.currentTab === 'dashboard') {
                renderDashboard();
            }
        }
    }
    
    // 유틸리티 함수들
    function getUserFollowups() {
        if (state.currentUser.role === 'manager') {
            return state.data.followups;
        }
        return state.data.followups.filter(f => f.userId === state.currentUser.id);
    }
    
    function getUserSchedules() {
        if (state.currentUser.role === 'manager') {
            return state.data.schedules;
        }
        return state.data.schedules.filter(s => s.userId === state.currentUser.id);
    }
    
    function getPriorityLabel(priority) {
        const labels = { high: '높음', medium: '보통', low: '낮음' };
        return labels[priority] || priority;
    }
    
    function getStatusLabel(status) {
        const labels = { active: '진행중', completed: '완료', pending: '대기중' };
        return labels[status] || status;
    }
    
    function getScheduleStatusLabel(status) {
        const labels = { scheduled: '예정', completed: '완료', cancelled: '취소' };
        return labels[status] || status;
    }
    
    function getActionTypeLabel(actionType) {
        const labels = { call: '전화', email: '이메일', meeting: '미팅', visit: '방문', other: '기타' };
        return labels[actionType] || actionType;
    }
    
    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('ko-KR');
    }
    
    function formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        return date.toLocaleString('ko-KR');
    }
    
    // 전역 함수 정의 (HTML에서 onclick 이벤트 처리용)
    window.openHistoryModal = openHistoryModal;
    window.openResearchModal = openResearchModal;
    window.editFollowup = editFollowup;
    window.deleteFollowup = deleteFollowup;
    window.editSchedule = editSchedule;
    window.deleteSchedule = deleteSchedule;
});