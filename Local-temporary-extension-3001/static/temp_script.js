
        const API_BASE = '';  // same origin
        let currentWorkers = [];
        let currentTasks = [];
        let selectedTaskId = null;

        // ── Toast Notifications ──
        function showToast(message, type = 'success') {
            const container = document.getElementById('toastContainer');
            const el = document.createElement('div');
            el.className = `toast-msg ${type}`;
            el.textContent = message;
            container.appendChild(el);
            setTimeout(() => el.remove(), 4000);
        }

        // ── Helpers ──
        function escapeHtml(unsafe) {
            if (!unsafe) return "";
            return unsafe.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }

        // ── Fetch Workers ──
        async function fetchWorkers() {
            try {
                const res = await fetch(`${API_BASE}/workers`);
                currentWorkers = await res.json();
                renderWorkers();
                updateStats();
            } catch (e) {
                document.getElementById('serverDot').className = 'status-dot';
                document.getElementById('serverDot').style.background = 'var(--accent-red)';
            }
        }

        // ── Fetch Tasks ──
        async function fetchTasks() {
            try {
                const res = await fetch(`${API_BASE}/tasks`);
                currentTasks = await res.json();
                renderTasks();
            } catch (e) {
                console.error('Failed to fetch tasks:', e);
            }
        }

        // ── Fetch Results ──
        let currentPage = 1;
        const limitPerPage = 15;
        let totalPages = 1;

        async function fetchResults() {
            try {
                const res = await fetch(`${API_BASE}/results?page=${currentPage}&limit=${limitPerPage}`);
                const data = await res.json();
                renderResults(data.data);
                updatePagination(data.total);
            } catch (e) {
                console.error('Failed to fetch results:', e);
            }
        }

        function changePage(delta) {
            currentPage += delta;
            if (currentPage < 1) currentPage = 1;
            if (currentPage > totalPages) currentPage = totalPages;
            fetchResults();
        }

        function updatePagination(totalItems) {
            totalPages = Math.ceil(totalItems / limitPerPage) || 1;

            document.getElementById('paginationControls').style.display = totalItems > 0 ? 'flex' : 'none';
            document.getElementById('currentPageDisplay').textContent = currentPage;
            document.getElementById('totalPagesDisplay').textContent = totalPages;

            document.getElementById('btnPrevPage').disabled = (currentPage === 1);
            document.getElementById('btnNextPage').disabled = (currentPage === totalPages);

            document.getElementById('btnPrevPage').style.opacity = (currentPage === 1) ? '0.5' : '1';
            document.getElementById('btnPrevPage').style.cursor = (currentPage === 1) ? 'not-allowed' : 'pointer';

            document.getElementById('btnNextPage').style.opacity = (currentPage === totalPages) ? '0.5' : '1';
            document.getElementById('btnNextPage').style.cursor = (currentPage === totalPages) ? 'not-allowed' : 'pointer';
        }

        // ── Render Workers Table ──
        function renderWorkers() {
            const container = document.getElementById('workersContainer');

            if (currentWorkers.length === 0) {
                container.innerHTML = `
                <div class="empty-state">
                    <div class="emoji">📡</div>
                    <p>Chưa có Worker nào kết nối.<br>Hãy cài Extension và mở Chrome.</p>
                </div>`;
                return;
            }

            let html = `
            <table class="table-dark-custom">
                <thead>
                    <tr>
                        <th>Worker ID</th>
                        <th>Trạng thái</th>
                        <th>Task đang chạy</th>
                        <th>Lần ping cuối</th>
                        <th>Kết nối lúc</th>
                        <th>Hành động</th>
                    </tr>
                </thead>
                <tbody>`;

            for (const w of currentWorkers) {
                html += `
                <tr>
                    <td><span class="worker-id-text">${w.worker_id.substring(0, 8)}…</span></td>
                    <td><span class="badge-state badge-${w.state}">${w.state}</span></td>
                    <td>${w.task_running || '—'}</td>
                    <td>${w.last_ping}</td>
                    <td>${w.connected_at}</td>
                    <td>
                        <button class="btn-delete" onclick="deleteWorker('${w.worker_id}')">
                            ✕ Xóa
                        </button>
                    </td>
                </tr>`;
            }

            html += `</tbody></table>`;
            container.innerHTML = html;
        }

        // ── Render Tasks ──
        let currentTaskTab = 'sample';

        function switchTaskTab(tab) {
            currentTaskTab = tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.currentTarget.classList.add('active');
            renderTasks();

            const geminiSec = document.getElementById('geminiSection');
            if (geminiSec) {
                geminiSec.style.display = (tab === 'executable') ? 'block' : 'none';
            }
        }

        function renderTasks() {
            const container = document.getElementById('tasksContainer');
            const tasksToShow = currentTasks.filter(t => t.category === currentTaskTab);

            if (tasksToShow.length === 0) {
                container.innerHTML = '<div class="empty-state">Không có task nào trong mục này</div>';
                return;
            }

            let html = '';
            for (const t of tasksToShow) {
                const hasIdleWorker = currentWorkers.some(w => w.state === 'IDLE');
                html += `
                <div class="task-item">
                    <div>
                        <div class="task-name">${t.name}</div>
                        <div class="task-meta">ID: ${t.task_id} · ${t.steps_count} bước</div>
                    </div>
                    <button class="btn-assign"
                        ${!hasIdleWorker ? 'disabled title="Không có Worker IDLE"' : ''}
                        onclick="openAssignModal('${t.task_id}', '${t.name.replace(/'/g, "\\'")}')">
                        📤 Assign
                    </button>
                </div>`;
            }
            container.innerHTML = html;
        }

        // ── Render Results ──
        function renderResults(results) {
            const container = document.getElementById('resultsContainer');
            if (results.length === 0) {
                container.innerHTML = `
                <div class="empty-state">
                    <div class="emoji">📭</div>
                    <p>Chưa có kết quả nào được ghi nhận.</p>
                </div>`;
                return;
            }

            let html = `
            <table class="table-dark-custom">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Thời gian</th>
                        <th>Task / Worker</th>
                        <th>Trạng thái</th>
                        <th>Chi tiết</th>
                        <th>Hành động</th>
                    </tr>
                </thead>
                <tbody>`;

            for (const r of results) {
                const statusColor = r.status === 'completed' ? 'var(--accent-green)' : 'var(--accent-red)';
                const statusIcon = r.status === 'completed' ? '✅' : '❌';
                const shortData = r.result_data ? (r.result_data.length > 80 ? r.result_data.substring(0, 80) + '...' : r.result_data) : null;
                const safeData = escapeHtml(r.result_data);

                const details = r.status === 'completed' ?
                    (shortData ? `<span style="font-family: monospace; font-size: 0.8rem; color: #a5b4fc; cursor: pointer; text-decoration: underline;" onclick="openResultModal(this.getAttribute('data-result'))" data-result="${safeData}" title="Nhấn để xem chi tiết">${escapeHtml(shortData)}</span>` : 'Không có chi tiết') :
                    `<span style="color:var(--accent-red)">${escapeHtml(r.error_message) || 'Lỗi không xác định'}</span>`;

                html += `
                <tr>
                    <td style="color:var(--text-secondary)">#${r.id}</td>
                    <td>${r.created_at}</td>
                    <td>
                        <div><strong>${r.task_id}</strong></div>
                        <div class="worker-id-text">${r.worker_id.substring(0, 8)}…</div>
                    </td>
                    <td>
                        <span style="color:${statusColor}; font-weight:600;">
                            ${statusIcon} ${r.status.toUpperCase()}
                        </span>
                    </td>
                    <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${details}
                    </td>
                    <td style="white-space: nowrap;">
                        ${r.task_id === 'gemini_gen_image' ?
                        `<button class="btn-primary" style="padding: 0.2rem 0.6rem; font-size: 0.75rem; margin-right: 4px; background: var(--accent-blue);" onclick="event.stopPropagation(); downloadImage(this.getAttribute('data-result'), ${r.id})" data-result="${safeData}" ${r.status !== 'completed' ? 'disabled' : ''} title="Tải ảnh dạng hình ảnh">
                            📥 Tải Ảnh
                        </button>` :
                        `<button class="btn-primary" style="padding: 0.2rem 0.6rem; font-size: 0.75rem; margin-right: 4px;" onclick="event.stopPropagation(); exportCSV(this.getAttribute('data-result'), ${r.id})" data-result="${safeData}" ${r.status !== 'completed' ? 'disabled' : ''} title="Xuất dữ liệu Scrape thành CSV">
                            📥 CSV
                        </button>`}
                        <button class="btn-delete" style="padding: 0.2rem 0.6rem; font-size: 0.75rem;" onclick="event.stopPropagation(); deleteResult(${r.id})" title="Xóa kết quả này">
                            ✕ Xóa
                        </button>
                    </td>
                </tr>`;
            }
            html += `</tbody></table>`;
            container.innerHTML = html;
        }

        // ── Delete Result ──
        async function deleteResult(id) {
            if (!confirm('Bạn có chắc chắn muốn xóa kết quả này?')) return;
            try {
                const res = await fetch(`${API_BASE}/results/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    showToast(`🗑️ Đã xóa kết quả #${id}`, 'success');
                    fetchResults();
                } else {
                    const data = await res.json();
                    showToast(`❌ Xóa thất bại: ${data.detail || 'Lỗi không xác định'}`, 'error');
                }
            } catch (e) {
                showToast(`❌ Lỗi kết nối khi xóa: ${e.message}`, 'error');
            }
        }

        // ── Export CSV ──
        function exportCSV(jsonString, id) {
            if (!jsonString) return;
            try {
                const parsed = JSON.parse(jsonString);

                let dataToExport = null;
                if (Array.isArray(parsed)) {
                    // Find scrape results
                    const reversed = [...parsed].reverse();
                    for (const step of reversed) {
                        if (step.data && Array.isArray(step.data) && step.data.length > 0) {
                            dataToExport = step.data;
                            break;
                        } else if (step.data && typeof step.data === 'object' && !Array.isArray(step.data)) {
                            dataToExport = [step.data];
                            break;
                        }
                    }
                    if (!dataToExport) dataToExport = parsed;
                } else if (typeof parsed === 'object') {
                    dataToExport = [parsed];
                } else {
                    dataToExport = [{ value: parsed }];
                }

                if (!Array.isArray(dataToExport) || dataToExport.length === 0) {
                    showToast('Không có dữ liệu bảng hợp lệ để xuất CSV', 'warning');
                    return;
                }

                const headers = Array.from(new Set(dataToExport.flatMap(obj => Object.keys(obj || {}))));
                if (headers.length === 0) return;

                const csvRows = [];
                csvRows.push(headers.join(','));

                for (const row of dataToExport) {
                    const values = headers.map(header => {
                        const val = row[header];
                        const strVal = val === null || val === undefined ? '' : typeof val === 'object' ? JSON.stringify(val) : String(val);
                        return '"' + strVal.replace(/"/g, '""') + '"';
                    });
                    csvRows.push(values.join(','));
                }

                const csvContent = "\uFEFF" + csvRows.join('\n'); // UTF-8 BOM
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.setAttribute("href", url);
                link.setAttribute("download", `result_${id}.csv`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);

                showToast(`📥 Đã tải xuống CSV #${id}`, 'success');
            } catch (e) {
                console.error(e);
                showToast(`❌ Lỗi cấu trúc JSON: ${e.message}`, 'error');
            }
        }

        // ── Download Image ──
        function downloadImage(jsonString, id) {
            if (!jsonString) return;
            try {
                const parsed = JSON.parse(jsonString);

                let urls = [];
                if (Array.isArray(parsed)) {
                    urls = parsed.flatMap(item => {
                        if (typeof item === 'string') return [item];
                        if (item && item.data && Array.isArray(item.data)) {
                            return item.data.filter(u => typeof u === 'string');
                        }
                        if (item && item.urls) return item.urls;
                        return [];
                    });
                } else if (typeof parsed === 'string') {
                    urls = [parsed];
                } else if (parsed && parsed.urls) {
                    urls = parsed.urls;
                }

                if (urls.length === 0) {
                    showToast('Không tìm thấy ảnh để tải!', 'warning');
                    return;
                }

                urls.forEach((url, idx) => {
                    const link = document.createElement('a');
                    link.href = url;
                    const extension = url.includes('.png') ? '.png' : '.webp';
                    const filename = url.split('/').pop() || ('image_' + id + '_' + idx + extension);
                    link.download = filename;
                    link.target = '_blank';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                });
                showToast('📥 Đã tải ' + urls.length + ' ảnh', 'success');
            } catch (e) {
                console.error(e);
                showToast('❌ Lỗi phân tích dữ liệu ảnh: ' + e.message, 'error');
            }
        }

        // ── Update Stats ──
        function updateStats() {
            const total = currentWorkers.length;
            const idle = currentWorkers.filter(w => w.state === 'IDLE').length;
            const busy = currentWorkers.filter(w => w.state === 'BUSY').length;
            const errHung = currentWorkers.filter(w => w.state === 'ERROR' || w.state === 'HUNG').length;

            document.getElementById('statTotal').textContent = total;
            document.getElementById('statIdle').textContent = idle;
            document.getElementById('statBusy').textContent = busy;
            document.getElementById('statError').textContent = errHung;

            document.getElementById('serverDot').className = 'status-dot online';
            document.getElementById('serverDot').style.background = '';
        }

        // ── Assign Modal ──
        function openAssignModal(taskId, taskName) {
            selectedTaskId = taskId;
            document.getElementById('modalTaskName').textContent = taskName;

            const list = document.getElementById('modalWorkerList');
            list.innerHTML = '';
            document.getElementById('selectAllWorkers').checked = false;

            const idleWorkers = currentWorkers.filter(w => w.state === 'IDLE');
            if (idleWorkers.length === 0) {
                list.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.85rem;">Không có Worker nào đang IDLE</div>';
            } else {
                for (const w of idleWorkers) {
                    const label = document.createElement('label');
                    label.style.cssText = 'display: block; margin-bottom: 0.3rem; cursor: pointer; font-size: 0.85rem;';
                    label.innerHTML = `<input type="checkbox" class="worker-checkbox" value="${w.worker_id}"> ${w.worker_id.substring(0, 8)}… (IDLE)`;
                    list.appendChild(label);
                }
            }

            document.getElementById('assignModal').classList.add('active');
        }

        function toggleAllWorkers() {
            const checked = document.getElementById('selectAllWorkers').checked;
            const checkboxes = document.querySelectorAll('.worker-checkbox');
            checkboxes.forEach(cb => cb.checked = checked);
        }

        function closeAssignModal() {
            document.getElementById('assignModal').classList.remove('active');
            selectedTaskId = null;
        }

        async function confirmAssign() {
            const checkboxes = document.querySelectorAll('.worker-checkbox:checked');
            const workerIds = Array.from(checkboxes).map(cb => cb.value);

            if (workerIds.length === 0) {
                showToast('Vui lòng chọn ít nhất 1 Worker!', 'error');
                return;
            }

            try {
                const res = await fetch(`${API_BASE}/assign_task`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_id: selectedTaskId, worker_ids: workerIds })
                });

                const data = await res.json();
                if (res.ok) {
                    const num = data.assigned_to ? data.assigned_to.length : 0;
                    showToast(`✅ Đã giao task "${selectedTaskId}" cho ${num} Worker`, 'success');
                    if (data.errors && data.errors.length > 0) {
                        showToast(`⚠️ Có ${data.errors.length} lỗi khi giao việc`, 'error');
                    }
                    closeAssignModal();
                    fetchWorkers();
                    loadGallery(); // refresh
                } else {
                    showToast(`❌ ${data.detail || 'Lỗi không xác định'}`, 'error');
                }
            } catch (e) {
                showToast(`❌ Lỗi kết nối: ${e.message}`, 'error');
            }
        }

        // ── Delete Worker ──
        async function deleteWorker(workerId) {
            if (!confirm(`Xóa Worker [${workerId.substring(0, 8)}…] khỏi danh sách?`)) return;

            try {
                const res = await fetch(`${API_BASE}/workers/${workerId}`, { method: 'DELETE' });
                const data = await res.json();
                if (res.ok) {
                    showToast(`🗑️ Đã xóa Worker [${workerId.substring(0, 8)}…]`, 'success');
                    fetchWorkers();
                    loadGallery();
                } else {
                    showToast(`❌ ${data.detail}`, 'error');
                }
            } catch (e) {
                showToast(`❌ Lỗi: ${e.message}`, 'error');
            }
        }

        // ── Click outside modal to close ──
        document.getElementById('assignModal').addEventListener('click', function (e) {
            if (e.target === this) closeAssignModal();
        });

        // ── Result Modal ──
        function openResultModal(dataString) {
            let content = dataString;
            try {
                const parsed = JSON.parse(dataString);

                // Xử lý làm mịn giao diện hiển thị cho evaluate_script (ví dụ mảng YouTube)
                let displayObj = parsed;
                if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].data) {
                    try {
                        displayObj = parsed.map(p => ({
                            ...p,
                            data: JSON.parse(p.data) // Thử parse chuỗi json bên trong 'data'
                        }));
                    } catch (e) { }
                }

                content = JSON.stringify(displayObj, null, 2);
            } catch (e) { }

            document.getElementById('modalResultContent').textContent = content;
            document.getElementById('resultModal').classList.add('active');
        }

        function closeResultModal() {
            document.getElementById('resultModal').classList.remove('active');
        }

        document.getElementById('resultModal').addEventListener('click', function (e) {
            if (e.target === this) closeResultModal();
        });


        // ── Gemini Image Gen ─────────────────────────────────────
        function openGeminiAssignModal() {
            const prompt = document.getElementById('geminiPrompt').value.trim();
            if (!prompt) {
                showToast('❌ Vui lòng nhập prompt trước khi giao việc!', 'error');
                document.getElementById('geminiPrompt').focus();
                return;
            }
            document.getElementById('modalGeminiPromptText').textContent = prompt;
            refreshGeminiWorkerList();
            document.getElementById('geminiAssignModal').classList.add('active');
        }

        function closeGeminiAssignModal() {
            document.getElementById('geminiAssignModal').classList.remove('active');
        }

        document.getElementById('geminiAssignModal').addEventListener('click', function (e) {
            if (e.target === this) closeGeminiAssignModal();
        });

        function refreshGeminiWorkerList() {
            const list = document.getElementById('geminiWorkerList');
            if (!list) return;

            // Only refresh if modal is open to avoid unnecessary DOM updates in background
            const modal = document.getElementById('geminiAssignModal');
            if (!modal || !modal.classList.contains('active')) return;

            const checkedBoxes = Array.from(document.querySelectorAll('.gemini-worker-checkbox:checked')).map(cb => cb.value);

            list.innerHTML = '';
            
            const idleWorkers = (currentWorkers || []).filter(w => w.state === 'IDLE');
            if (idleWorkers.length === 0) {
                list.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.85rem;">Không có Worker nào đang IDLE</div>';
                const sa = document.getElementById('geminiSelectAllWorkers');
                if (sa) sa.checked = false;
            } else {
                for (const w of idleWorkers) {
                    const label = document.createElement('label');
                    label.style.cssText = 'display: block; margin-bottom: 0.3rem; cursor: pointer; font-size: 0.85rem;';
                    const isChecked = checkedBoxes.includes(w.worker_id) ? 'checked' : '';
                    label.innerHTML = `<input type="checkbox" class="gemini-worker-checkbox" value="${w.worker_id}" ${isChecked}> ${w.worker_id.substring(0, 8)}… (IDLE)`;
                    list.appendChild(label);
                }
            }
        }

        function toggleAllGeminiWorkers() {
            const checked = document.getElementById('geminiSelectAllWorkers').checked;
            const checkboxes = document.querySelectorAll('.gemini-worker-checkbox');
            checkboxes.forEach(cb => cb.checked = checked);
        }

        async function genImg() {
            const prompt = document.getElementById('geminiPrompt').value.trim();
            const checkboxes = document.querySelectorAll('.gemini-worker-checkbox:checked');
            const workerIds = Array.from(checkboxes).map(cb => cb.value);

            if (!prompt) return showToast('❌ Nhập prompt trước!', 'error');
            if (workerIds.length === 0) return showToast('❌ Chọn ít nhất 1 worker IDLE!', 'error');

            try {
                const res = await fetch(`${API_BASE}/gen-img`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, worker_ids: workerIds })
                });
                const data = await res.json();
                if (res.ok) {
                    const num = data.assigned_to ? data.assigned_to.length : 0;
                    showToast(`🎨 Đã dispatch! Đang tạo ảnh trên ${num} worker...`, 'success');
                    if (data.errors && data.errors.length > 0) {
                        showToast(`⚠️ Có ${data.errors.length} lỗi khi giao việc`, 'error');
                    }
                    document.getElementById('geminiPrompt').value = '';
                    closeGeminiAssignModal();
                    setTimeout(loadGallery, 15000); // tải lại sau 15s
                } else {
                    showToast(`❌ ${data.detail || 'Lỗi dispatch'}`, 'error');
                }
            } catch (e) { showToast(`❌ Lỗi: ${e.message}`, 'error'); }
        }

        let geminiCurrentPage = 1;
        const geminiLimitPerPage = 12;
        let geminiTotalPages = 1;

        async function loadGallery() {
            try {
                const res = await fetch(`${API_BASE}/gen-img/results?page=${geminiCurrentPage}&limit=${geminiLimitPerPage}`);
                const data = await res.json();
                renderGallery(data.data || []);
                updateGeminiPagination(data.total || 0);
            } catch (e) { console.error('loadGallery error:', e); }
        }

        function changeGeminiPage(delta) {
            geminiCurrentPage += delta;
            if (geminiCurrentPage < 1) geminiCurrentPage = 1;
            if (geminiCurrentPage > geminiTotalPages) geminiCurrentPage = geminiTotalPages;
            loadGallery();
        }

        function updateGeminiPagination(totalItems) {
            geminiTotalPages = Math.ceil(totalItems / geminiLimitPerPage) || 1;

            const controls = document.getElementById('geminiPaginationControls');
            if (controls) controls.style.display = totalItems > 0 ? 'flex' : 'none';

            const curDisp = document.getElementById('geminiCurrentPageDisplay');
            if (curDisp) curDisp.textContent = geminiCurrentPage;

            const totDisp = document.getElementById('geminiTotalPagesDisplay');
            if (totDisp) totDisp.textContent = geminiTotalPages;

            const prevBtn = document.getElementById('geminiBtnPrevPage');
            const nextBtn = document.getElementById('geminiBtnNextPage');
            if (prevBtn) {
                prevBtn.disabled = (geminiCurrentPage === 1);
                prevBtn.style.opacity = (geminiCurrentPage === 1) ? '0.5' : '1';
                prevBtn.style.cursor = (geminiCurrentPage === 1) ? 'not-allowed' : 'pointer';
            }
            if (nextBtn) {
                nextBtn.disabled = (geminiCurrentPage === geminiTotalPages);
                nextBtn.style.opacity = (geminiCurrentPage === geminiTotalPages) ? '0.5' : '1';
                nextBtn.style.cursor = (geminiCurrentPage === geminiTotalPages) ? 'not-allowed' : 'pointer';
            }
        }

        function triggerDownload(url, filename, event) {
            if (event) event.stopPropagation();
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        function renderGallery(items) {
            const g = document.getElementById('geminiGallery');
            const empty = document.getElementById('geminiGalleryEmpty');
            if (!items.length) { g.innerHTML = ''; empty.style.display = 'block'; return; }
            empty.style.display = 'none';
            g.innerHTML = items.map(item => {
                if ((item.status === 'success' || item.status === 'completed') && item.image_urls && item.image_urls.length) {
                    return item.image_urls.map(url => {
                        const filename = url.split('/').pop() || 'image';
                        return `
                    <div class="gemini-item">
                        <img src="${url}" alt="${item.prompt}" onerror="this.style.display='none'">
                        <div class="gemini-overlay">
                            <div class="gemini-filename" title="${filename}">${filename}</div>
                            <button class="gemini-download-btn" onclick="triggerDownload('${url}', '${filename}', event)">⬇ Tải xuống</button>
                        </div>
                    </div>`;
                    }).join('');
                }
                return `<div style="border-radius:8px; border:1px solid var(--border-color); background:var(--bg-dark); padding:0.6rem; font-size:0.8rem; color:#e74c3c;">❌ ${item.prompt}<br><span style="color:var(--text-muted)">${item.error_message || 'Lỗi không xác định'}</span></div>`;
            }).join('');
        }

        // Cập nhật worker list cho Gemini khi fetchWorkers chạy
        const _origRenderWorkers = typeof renderWorkers === 'function' ? renderWorkers : null;
        
        // ── Navigation ──
        function switchView(viewName) {
            document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
            document.getElementById(`nav-${viewName}`).classList.add('active');
            
            document.getElementById('dashboardView').style.display = viewName === 'dashboard' ? 'block' : 'none';
            document.getElementById('builderView').style.display = viewName === 'builder' ? 'block' : 'none';
            
            if(viewName === 'builder') {
                renderCustomTasksTable();
            }
        }

        // ── Builder Logic ──
        let builderSteps = [];
        
        function addBuilderStep() {
            const action = document.getElementById('builderActionSelect').value;
            const newStep = { action: action };
            
            if(action === 'goto') { newStep.url = ''; }
            if(action === 'wait_for_selector') { newStep.selector = ''; newStep.timeout = 10000; }
            if(action === 'wait') { newStep.time = 1000; }
            if(action === 'random_delay') { newStep.min = 1000; newStep.max = 3000; }
            if(action === 'click') { newStep.selector = ''; }
            if(action === 'click_text') { newStep.text = ''; }
            if(action === 'type') { newStep.selector = ''; newStep.text = ''; }
            if(action === 'scroll') { newStep.direction = 'down'; newStep.pixels = 500; }
            if(action === 'evaluate_script' || action === 'extract_data') { newStep.script = ''; }
            
            builderSteps.push(newStep);
            renderBuilderSteps();
        }

        function removeBuilderStep(index) {
            builderSteps.splice(index, 1);
            renderBuilderSteps();
        }

        function moveBuilderStep(index, dir) {
            if(index + dir < 0 || index + dir >= builderSteps.length) return;
            const temp = builderSteps[index];
            builderSteps[index] = builderSteps[index + dir];
            builderSteps[index + dir] = temp;
            renderBuilderSteps();
        }

        function renderBuilderSteps() {
            const container = document.getElementById('builderStepsContainer');
            if(builderSteps.length === 0) {
                container.innerHTML = '<div style="color:var(--text-secondary); font-size:0.85rem;">Chưa có bước nào.</div>';
                return;
            }
            
            let html = '';
            builderSteps.forEach((step, idx) => {
                html += `<div class="builder-step">
                    <div class="builder-step-header">
                        <span>Bước ${idx + 1}: <span style="color:var(--accent-blue);">${step.action.toUpperCase()}</span></span>
                        <div class="builder-step-actions">
                            <button class="btn-cancel" style="padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="moveBuilderStep(${idx}, -1)">▲</button>
                            <button class="btn-cancel" style="padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="moveBuilderStep(${idx}, 1)">▼</button>
                            <button class="btn-delete" style="padding:0.2rem 0.5rem; font-size:0.75rem; border:none; background:transparent; color:var(--accent-red);" onclick="removeBuilderStep(${idx})">✕</button>
                        </div>
                    </div>
                    <div class="builder-step-form">`;
                
                Object.keys(step).forEach(key => {
                    if(key === 'action') return;
                    html += `
                        <label style="font-size:0.8rem; color:var(--text-secondary);">${key}</label>
                        ${key === 'script' 
                            ? `<textarea class="step-input" onchange="builderSteps[${idx}]['${key}'] = this.value" rows="3" style="font-family:monospace;">${escapeHtml(step[key])}</textarea>`
                            : `<input type="${typeof step[key]==='number'?'number':'text'}" class="step-input" value="${escapeHtml(step[key])}" onchange="builderSteps[${idx}]['${key}'] = ${typeof step[key]==='number' ? 'Number(this.value)' : 'this.value'}">`}
                    `;
                });
                
                html += `</div></div>`;
            });
            container.innerHTML = html;
        }

        async function saveCustomTask() {
            const taskId = document.getElementById('builderTaskId').value.trim();
            const taskName = document.getElementById('builderTaskName').value.trim();
            
            if(!taskId || !taskName) return showToast('Vui lòng nhập Task ID và Tên Kịch Bản', 'error');
            if(builderSteps.length === 0) return showToast('Kịch bản cần có ít nhất 1 bước', 'error');
            
            const payload = {
                task_id: taskId,
                name: taskName,
                steps: builderSteps
            };
            
            try {
                const res = await fetch(`${API_BASE}/tasks`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if(res.ok) {
                    showToast('✅ Lưu thành công!', 'success');
                    fetchTasks();
                    setTimeout(renderCustomTasksTable, 300);
                } else {
                    showToast('❌ Lỗi: ' + data.detail, 'error');
                }
            } catch(e) {
                showToast('❌ Lỗi lưu: ' + e.message, 'error');
            }
        }
        
        function renderCustomTasksTable() {
            const container = document.getElementById('customTasksContainer');
            const customTasks = currentTasks.filter(t => t.category === 'custom');
            
            if (customTasks.length === 0) {
                container.innerHTML = '<div class="empty-state" style="padding:1rem;">Không có kịch bản custom nào</div>';
                return;
            }

            let html = `
            <table class="table-dark-custom">
                <thead>
                    <tr>
                        <th>Task ID</th>
                        <th>Tên (Name)</th>
                        <th>Số Bước</th>
                        <th>Hành động</th>
                    </tr>
                </thead>
                <tbody>`;

            for (const t of customTasks) {
                html += `
                <tr>
                    <td><span class="worker-id-text">${t.task_id}</span></td>
                    <td>${t.name}</td>
                    <td>${t.steps_count} steps</td>
                    <td>
                        <button class="btn-cancel" style="padding: 0.2rem 0.6rem; font-size: 0.75rem; color: var(--text-primary); margin-right: 4px;" onclick="editCustomTask('${t.task_id}')">
                            ✏️ Sửa
                        </button>
                        <button class="btn-delete" style="padding: 0.2rem 0.6rem; font-size: 0.75rem;" onclick="deleteCustomTask('${t.task_id}')">
                            ✕ Xóa
                        </button>
                    </td>
                </tr>`;
            }
            html += `</tbody></table>`;
            container.innerHTML = html;
        }

        async function deleteCustomTask(taskId) {
            if(!confirm(`Xóa kịch bản ${taskId}?`)) return;
            try {
                const res = await fetch(`${API_BASE}/tasks/${taskId}`, { method: 'DELETE' });
                if(res.ok) {
                    showToast('🗑️ Đã xóa', 'success');
                    fetchTasks();
                    setTimeout(renderCustomTasksTable, 300);
                }
            } catch(e) { showToast('❌ Lỗi xoá', 'error'); }
        }

        async function editCustomTask(taskId) {
            try {
                const res = await fetch(`${API_BASE}/tasks/${taskId}`);
                if (!res.ok) throw new Error("Không thể tải kịch bản");
                const data = await res.json();
                
                document.getElementById('builderTaskId').value = data.task_id;
                document.getElementById('builderTaskName').value = data.name;
                builderSteps = data.steps || [];
                renderBuilderSteps();
                window.scrollTo({ top: 0, behavior: 'smooth' });
                showToast(`Đang sửa kịch bản ${taskId}`, 'success');
            } catch (e) {
                showToast(`❌ Lỗi: ${e.message}`, 'error');
            }
        }

        // Initialize Builder steps
        renderBuilderSteps();

        // ── Init & Auto-refresh ──
        fetchWorkers();
        loadGallery();
        fetchTasks();
        fetchResults();
        setInterval(() => {
            fetchWorkers();
            refreshGeminiWorkerList();
            loadGallery();
            fetchTasks();
            fetchResults();
        }, 3000);
    
