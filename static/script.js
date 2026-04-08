// ===== PAGE DETECTION =====
const isLoginPage = document.getElementById('loginForm') !== null;
const isChatPage  = document.getElementById('chatMessages') !== null;

// ===== SESSION REASON MESSAGE =====
(function() {
  const params = new URLSearchParams(window.location.search);
  const reason = params.get('reason');
  const msgEl  = document.getElementById('sessionMsg');
  if (msgEl && reason === 'timeout') {
    msgEl.textContent = '⏱️ Your session expired after 15 minutes of inactivity. Please sign in again.';
    msgEl.classList.remove('hidden');
  } else if (msgEl && reason === 'refresh') {
    msgEl.textContent = '🔄 You were logged out after too many page refreshes. Please sign in again.';
    msgEl.classList.remove('hidden');
  }
})();

// ===== AUTH TAB TOGGLE =====
window.showTab = function(tab) {
  document.getElementById('userLoginSection').classList.toggle('hidden', tab !== 'user');
  document.getElementById('adminLoginSection').classList.toggle('hidden', tab !== 'admin');
  document.getElementById('tabUser').classList.toggle('active',  tab === 'user');
  document.getElementById('tabAdmin').classList.toggle('active', tab === 'admin');
};

// ===== SETUP PAGE (admin tab) =====
const isSetupPage = document.getElementById('gateForm') !== null;
if (isSetupPage) {
  document.getElementById('gateForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const password = document.getElementById('masterPass').value.trim();
    const errEl    = document.getElementById('gateError');
    const res  = await fetch('/setup', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
    const data = await res.json();
    if (data.success) {
      window._master = password;
      document.getElementById('adminGate').classList.add('hidden');
      document.getElementById('adminCards').classList.remove('hidden');
      renderAdminCards();
    } else {
      errEl.classList.remove('hidden');
    }
  });
}

function renderAdminCards() {
  const grid = document.getElementById('credGrid');
  const users = [
    { username:'deo_cse', password:'cse123',   role:'DEO',   dept:'CSE', cls:'deo',   icon:'👨‍💻' },
    { username:'hod_cse', password:'hod123',   role:'HOD',   dept:'CSE', cls:'hod',   icon:'👩‍🏫' },
    { username:'admin',   password:'admin123', role:'Admin', dept:'ALL', cls:'admin', icon:'🛡️' },
  ];
  grid.innerHTML = '';
  users.forEach(u => {
    const card = document.createElement('div');
    card.className = 'admin-cred-card';
    card.innerHTML = `
      <div class="admin-cred-header ${u.cls}">${u.icon} ${u.role}</div>
      <div class="admin-cred-body">
        <div class="admin-cred-row"><span>Username</span><strong>${u.username}</strong></div>
        <div class="admin-cred-row"><span>Password</span><strong>${u.password}</strong></div>
        <div class="admin-cred-row"><span>Department</span><strong>${u.dept}</strong></div>
        <button class="btn-genqr" onclick="generateQR('${u.username}', this)">🔐 Generate QR Code</button>
        <div class="qr-result hidden" id="qr-${u.username}">
          <p class="qr-label">Scan with Google Authenticator</p>
          <img id="qrimg-${u.username}" src="" alt="QR"/>
          <p class="scan-note">📱 Open Authenticator → + → Other account → Scan</p>
        </div>
      </div>`;
    grid.appendChild(card);
  });
}

async function generateQR(username, btn) {
  btn.textContent = 'Generating...';
  btn.disabled    = true;
  const res  = await fetch('/setup/qr', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, master: window._master })
  });
  const data = await res.json();
  if (data.success) {
    document.getElementById(`qr-${username}`).classList.remove('hidden');
    document.getElementById(`qrimg-${username}`).src = `data:image/png;base64,${data.qr_code}`;
    btn.textContent = '✅ QR Generated';
  } else {
    btn.textContent = '❌ Failed'; btn.disabled = false;
  }
}

// ===== LOGIN LOGIC =====
if (isLoginPage) {
  const loginForm  = document.getElementById('loginForm');
  const loginError = document.getElementById('loginError');

  loginForm.addEventListener('submit', async function (e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const dept     = document.getElementById('department').value;
    const otp      = document.getElementById('otp').value.trim();

    const btn = document.getElementById('loginBtn');
    const btnText = btn.innerHTML;
    btn.innerHTML = '<span>Verifying...</span><span>⏳</span>';
    btn.disabled = true;

    console.log('Login attempt:', { username, dept, otp });

    try {
      const res  = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, department: dept, otp })
      });
      
      console.log('Response status:', res.status);
      const data = await res.json();
      console.log('Response data:', data);

      if (data.success) {
        btn.innerHTML = '<span>Success!</span><span>✅</span>';
        console.log('Login successful, redirecting...');
        setTimeout(() => {
          window.location.href = '/chat';
        }, 500);
      } else {
        loginError.textContent = data.message || 'Login failed.';
        loginError.classList.remove('hidden');
        btn.innerHTML = btnText;
        btn.disabled = false;
        console.error('Login failed:', data.message);
      }
    } catch (error) {
      console.error('Login error:', error);
      loginError.textContent = 'Network error. Please try again.';
      loginError.classList.remove('hidden');
      btn.innerHTML = btnText;
      btn.disabled = false;
    }
  });
}

// ===== REGISTER LOGIC =====
const isRegisterPage = document.getElementById('registerForm') !== null;
if (isRegisterPage) {
  document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('reg_username').value.trim();
    const password = document.getElementById('reg_password').value.trim();
    const role     = document.getElementById('reg_role').value;
    const dept     = document.getElementById('reg_dept').value;
    const errEl    = document.getElementById('regError');

    const res  = await fetch('/admin/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, role, dept })
    });
    const data = await res.json();

    if (data.success) {
      document.getElementById('qrUsername').textContent = data.username;
      document.getElementById('qrImage').src = `data:image/png;base64,${data.qr_code}`;
      document.getElementById('formSection').classList.add('hidden');
      document.getElementById('qrSection').classList.remove('hidden');
    } else {
      errEl.textContent = data.message;
      errEl.classList.remove('hidden');
    }
  });
}

function resetForm() {
  document.getElementById('registerForm').reset();
  document.getElementById('regError').classList.add('hidden');
  document.getElementById('formSection').classList.remove('hidden');
  document.getElementById('qrSection').classList.add('hidden');
}

// ===== CHAT LOGIC =====
if (isChatPage) {

  const chatMessages = document.getElementById('chatMessages');
  const chatInput    = document.getElementById('chatInput');
  const sendBtn      = document.getElementById('sendBtn');
  const exportBar    = document.getElementById('exportBar');
  const logoutBtn    = document.getElementById('logoutBtn');

  let lastReportData = null;

  // ===== SESSION COUNTDOWN TIMER =====
  (function() {
    const TIMEOUT_MS = 15 * 60 * 1000;
    const timerEl = document.getElementById('sessionTimer');
    let deadline = Date.now() + TIMEOUT_MS;
    let lastActivityUpdate = 0;

    // Fetch actual last_active from server ONCE on page load
    fetch('/api/me').then(r => r.json()).then(data => {
      if (data.last_active) {
        const serverTime = new Date(data.last_active + 'Z').getTime();
        deadline = serverTime + TIMEOUT_MS;
      }
    }).catch(() => {});

    // Reset deadline on user activity (but throttle server updates to every 30 seconds)
    function onActivity() {
      const now = Date.now();
      deadline = now + TIMEOUT_MS;
      
      // Only update server every 30 seconds to avoid constant API calls
      if (now - lastActivityUpdate > 30000) {
        lastActivityUpdate = now;
        fetch('/api/report', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: '__keepalive__', semester: '', batch: '' })
        }).catch(() => {});
      }
    }

    ['click', 'keydown'].forEach(evt =>
      document.addEventListener(evt, onActivity, { passive: true, once: false })
    );

    setInterval(() => {
      const remaining = deadline - Date.now();
      if (remaining <= 0) {
        window.location.href = '/logout';
        return;
      }
      const mins = Math.floor(remaining / 60000);
      const secs = Math.floor((remaining % 60000) / 1000);
      if (timerEl) {
        timerEl.textContent = `⏱ ${mins}:${secs.toString().padStart(2, '0')}`;
        timerEl.style.color = remaining < 2 * 60 * 1000 ? '#ff5252' : '#ef9a9a';
      }
    }, 1000);
  })();

  // ===== LOGOUT =====
  logoutBtn.addEventListener('click', () => { window.location.href = '/logout'; });

  // Show admin link if admin role
  fetch('/api/me').then(r => r.json()).then(data => { 
    if (data && data.role === 'Admin') {
      const el = document.getElementById('adminLink');
      if (el) el.style.display = 'block';
    }
  }).catch(()=>{});

  // ===== QUICK BUTTONS =====
  document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      chatInput.value = btn.dataset.query;
      sendMessage();
    });
  });

  // ===== SEND ON ENTER =====
  chatInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });
  sendBtn.addEventListener('click', sendMessage);

  // ===== SEND MESSAGE =====
  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage('user', text);
    chatInput.value = '';
    showTyping();

    const sem   = document.getElementById('filterSemester').value;
    const batch = document.getElementById('filterBatch').value;

    try {
      const res  = await fetch('/api/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, semester: sem, batch })
      });
      const data = await res.json();
      removeTyping();

      if (data.success) {
        if (!data.message && data.report_type === 'general') {
          // empty keepalive — ignore
        } else if (data.report_type === 'general' || data.report_type === 'empty') {
          appendBotResponse(data.message || "I'm here to help!");
        } else if (data.report_type === 'average_marks' && data.averages) {
          const a = data.averages;
          const html = `<strong>📊 Average Marks — ${a.semester} (${a.count} students)</strong>
            <table class="report-table" style="margin-top:10px;">
              <thead><tr><th>Metric</th><th>Average</th><th>Status</th></tr></thead>
              <tbody>
                <tr><td>Internal Marks</td><td>${a.internal} / 50</td><td>${a.internal>=30?badge(a.internal+'/50','green'):badge(a.internal+'/50','red')}</td></tr>
                <tr><td>External Marks</td><td>${a.external} / 100</td><td>${a.external>=40?badge(a.external+'/100','green'):badge(a.external+'/100','red')}</td></tr>
                <tr><td>CGPA</td><td>${a.cgpa} / 10</td><td>${a.cgpa>=7?badge(a.cgpa,'green'):a.cgpa>=5.5?badge(a.cgpa,'yellow'):badge(a.cgpa,'red')}</td></tr>
                <tr><td>Attendance</td><td>${a.attendance}%</td><td>${a.attendance>=75?badge(a.attendance+'%','green'):badge(a.attendance+'%','red')}</td></tr>
              </tbody>
            </table>`;
          lastReportData = { type: 'average_marks', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'student_lookup' && data.data) {
          const s = data.data;
          const subj = s.subjects || {};
          let html = `<strong>🎓 Student Profile — ${s.roll}</strong>
            <table class="report-table" style="margin-top:10px;"><tbody>
              <tr><td><strong>Name</strong></td><td>${s.name}</td><td><strong>Section</strong></td><td>${badge(s.section,'green')}</td></tr>
              <tr><td><strong>Department</strong></td><td>${s.department}</td><td><strong>Semester</strong></td><td>${s.semester}</td></tr>
              <tr><td><strong>Batch</strong></td><td>${s.batch}</td><td><strong>CGPA</strong></td><td>${badge(s.cgpa, s.cgpa>=8?'green':s.cgpa>=6?'yellow':'red')}</td></tr>
              <tr><td><strong>Overall Attendance</strong></td><td colspan="3">${s.attendance>=75?badge(s.attendance+'%','green'):badge(s.attendance+'%','red')}</td></tr>
              <tr><td><strong>Backlogs</strong></td><td colspan="3">${s.backlogs>0?badge(s.backlogs+' subject(s)','red'):badge('None','green')}</td></tr>
            </tbody></table><br/><strong>📚 Subject-wise Details</strong>`;
          html += buildTable(['Subject','Attendance','Internal (/50)','External (/100)','Status'],
            ['CN','SE','ADS','PDC'].map(sub => {
              const d = subj[sub] || {};
              return [`<strong>${sub}</strong>`,
                d.attendance>=75?badge(d.attendance+'%','green'):badge(d.attendance+'%','red'),
                d.internal>=30?badge(d.internal+'/50','green'):badge(d.internal+'/50','red'),
                d.external>=40?badge(d.external+'/100','green'):badge(d.external+'/100','red'),
                d.external>=40&&d.internal>=20?badge('Pass','green'):badge('Fail','red')];
            }));
          lastReportData = { type: 'student_lookup', students: [s] };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'section_lookup' && data.data) {
          let html = `<strong>📋 ${data.section} — ${data.data.length} Students</strong>`;
          html += buildTable(['Roll No','Name','Attendance','CGPA','CN','SE','ADS','PDC'],
            data.data.map(s => {
              const sub = s.subjects || {};
              return [s.roll, s.name,
                s.attendance>=75?badge(s.attendance+'%','green'):badge(s.attendance+'%','red'),
                badge(s.cgpa, s.cgpa>=8?'green':s.cgpa>=6?'yellow':'red'),
                badge((sub.CN||{}).attendance+'%',(sub.CN||{}).attendance>=75?'green':'red'),
                badge((sub.SE||{}).attendance+'%',(sub.SE||{}).attendance>=75?'green':'red'),
                badge((sub.ADS||{}).attendance+'%',(sub.ADS||{}).attendance>=75?'green':'red'),
                badge((sub.PDC||{}).attendance+'%',(sub.PDC||{}).attendance>=75?'green':'red')];
            }));
          lastReportData = { type: 'section_lookup', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'subject_performance' && data.data) {
          let html = `<strong>📚 Subject Performance Analysis (CN / SE / ADS / PDC)</strong>`;
          html += buildTable(['Subject','Students','Avg Internal','Avg External','Avg Attendance','Pass Rate','Low Attend'],
            data.data.map(r => [`<strong>${r.subject}</strong>`, r.count,
              r.avg_internal>=30?badge(r.avg_internal+'/50','green'):badge(r.avg_internal+'/50','red'),
              r.avg_external>=40?badge(r.avg_external+'/100','green'):badge(r.avg_external+'/100','red'),
              r.avg_attend>=75?badge(r.avg_attend+'%','green'):badge(r.avg_attend+'%','red'),
              r.pass_rate>=75?badge(r.pass_rate+'%','green'):badge(r.pass_rate+'%','red'),
              badge(r.low_attend,'red')]));
          lastReportData = { type: 'subject_performance', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'cgpa_distribution' && data.data) {
          let html = `<strong>🏆 CGPA Distribution by Department</strong>`;
          html += buildTable(['Department','Students','Avg CGPA','≥8 (Excellent)','6–8 (Good)','<6 (Poor)'],
            data.data.map(r => [r.department, r.count,
              badge(r.avg_cgpa, r.avg_cgpa>=7?'green':r.avg_cgpa>=5.5?'yellow':'red'),
              badge(r.above_8,'green'), badge(r.above_6,'yellow'), badge(r.below_6,'red')]));
          lastReportData = { type: 'cgpa_distribution', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'section_attendance' && data.data) {
          let html = `<strong>📋 Section-wise Attendance</strong>`;
          html += buildTable(['Section','Total Students','Avg Attendance','≥75% (OK)','<75% (Low)'],
            data.data.map(r => [r.section, r.total,
              r.avg_attend>=75?badge(r.avg_attend+'%','green'):badge(r.avg_attend+'%','red'),
              badge(r.above_75,'green'), badge(r.below_75,'red')]));
          lastReportData = { type: 'section_attendance', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'subject_attendance' && data.data) {
          let html = `<strong>📋 Subject-wise Attendance (CN / SE / ADS / PDC)</strong>`;
          html += buildTable(['Subject','Students','Avg Attendance','≥75% (OK)','<75% (Low)'],
            data.data.map(r => [`<strong>${r.subject}</strong>`, r.count,
              r.avg_attend>=75?badge(r.avg_attend+'%','green'):badge(r.avg_attend+'%','red'),
              badge(r.above_75,'green'), badge(r.below_75,'red')]));
          lastReportData = { type: 'subject_attendance', students: data.students || data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'subject_section_attendance' && data.data) {
          const sm = data.summary;
          const title = `${data.subject} Attendance — ${data.section}`;
          let html = `<strong>📊 ${title}</strong>
            <table class="report-table" style="margin-top:10px;">
              <thead><tr><th>Metric</th><th>Value</th><th>Status</th></tr></thead>
              <tbody>
                <tr><td>Total Students</td><td>${sm.count}</td><td></td></tr>
                <tr><td>Avg Attendance</td><td>${sm.avg_att}%</td><td>${sm.avg_att>=75?badge(sm.avg_att+'%','green'):badge(sm.avg_att+'%','red')}</td></tr>
                <tr><td>Avg Internal</td><td>${sm.avg_int}/50</td><td>${sm.avg_int>=30?badge(sm.avg_int+'/50','green'):badge(sm.avg_int+'/50','red')}</td></tr>
                <tr><td>Avg External</td><td>${sm.avg_ext}/100</td><td>${sm.avg_ext>=40?badge(sm.avg_ext+'/100','green'):badge(sm.avg_ext+'/100','red')}</td></tr>
                <tr><td>≥75% Attendance</td><td>${sm.above_75} students</td><td>${badge(sm.above_75,'green')}</td></tr>
                <tr><td>&lt;75% Attendance</td><td>${sm.below_75} students</td><td>${badge(sm.below_75,'red')}</td></tr>
              </tbody>
            </table><br/><strong>📋 Student-wise ${data.subject} Details</strong>`;
          html += buildTable(['Roll No','Name','Section','Attendance','Internal','External'],
            data.data.map(r => [r.roll, r.name, badge(r.section,'green'),
              r.attendance>=75?badge(r.attendance+'%','green'):badge(r.attendance+'%','red'),
              r.internal>=30?badge(r.internal+'/50','green'):badge(r.internal+'/50','red'),
              r.external>=40?badge(r.external+'/100','green'):badge(r.external+'/100','red')]));
          lastReportData = { type: 'subject_section_attendance', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'subject_filter' && data.data) {
          const qualifierLabels = { low: '⚠️ Low / Weak', high: '🌟 Top / Excellent', average: '📊 Average' };
          const qualifierLabel  = qualifierLabels[data.qualifier] || data.qualifier;
          const scope  = data.section !== 'All' ? ` — ${data.section}` : '';
          const focus  = data.focus || 'all';

          let headers, rows;
          if (focus === 'attendance') {
            // Only show attendance column
            headers = ['Roll No', 'Name', 'Section', `${data.subject} Attendance`, 'Status'];
            rows = data.data.map(r => [
              r.roll, r.name, badge(r.section, 'green'),
              r.attendance >= 75 ? badge(r.attendance + '%', 'green') : badge(r.attendance + '%', 'red'),
              r.attendance >= 75 ? badge('OK', 'green') : badge('Low', 'red'),
            ]);
          } else if (focus === 'marks') {
            // Only show marks columns
            headers = ['Roll No', 'Name', 'Section', 'Internal (/50)', 'External (/100)', 'Result'];
            rows = data.data.map(r => {
              const pass = r.external >= 40 && r.internal >= 20;
              return [
                r.roll, r.name, badge(r.section, 'green'),
                r.internal >= 30 ? badge(r.internal + '/50', 'green') : badge(r.internal + '/50', 'red'),
                r.external >= 40 ? badge(r.external + '/100', 'green') : badge(r.external + '/100', 'red'),
                pass ? badge('Pass', 'green') : badge('Fail', 'red'),
              ];
            });
          } else {
            // Show all columns
            headers = ['Roll No', 'Name', 'Section', 'Attendance', 'Internal (/50)', 'External (/100)', 'Status'];
            rows = data.data.map(r => {
              const pass   = r.external >= 40 && r.internal >= 20;
              const attOk  = r.attendance >= 75;
              return [
                r.roll, r.name, badge(r.section, 'green'),
                attOk ? badge(r.attendance + '%', 'green') : badge(r.attendance + '%', 'red'),
                r.internal >= 30 ? badge(r.internal + '/50', 'green') : badge(r.internal + '/50', 'red'),
                r.external >= 40 ? badge(r.external + '/100', 'green') : badge(r.external + '/100', 'red'),
                pass && attOk ? badge('OK', 'green') : !pass ? badge('Fail', 'red') : badge('Low Att', 'yellow'),
              ];
            });
          }

          let html = `<strong>${qualifierLabel} Students in ${data.subject}${scope} — ${data.count} found</strong>`;
          html += buildTable(headers, rows);
          lastReportData = { type: 'subject_filter', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'department_attendance' && data.data) {
          let html = `<strong>🏫 Department-wise Attendance Analysis</strong>`;
          html += buildTable(['Department','Students','Avg Attendance','≥85%','<75%'],
            data.data.map(r => [r.department, r.count,
              r.avg_attend>=75?badge(r.avg_attend+'%','green'):badge(r.avg_attend+'%','red'),
              badge(r.above_85,'green'), badge(r.below_75,'red')]));
          lastReportData = { type: 'department_attendance', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'section_toppers' && data.data) {
          const scope = data.subject ? ` — ${data.subject}` : ' — by CGPA';
          let html = `<strong>🏆 Top Students in ${data.section}${scope}</strong>`;
          if (data.subject) {
            html += buildTable(['Rank','Roll No','Name','Section','External (/100)','Internal (/50)','Attendance'],
              data.data.map(r => [badge(r.rank,'green'), r.roll, r.name, badge(r.section,'green'),
                r.external>=40?badge(r.external+'/100','green'):badge(r.external+'/100','red'),
                r.internal>=30?badge(r.internal+'/50','green'):badge(r.internal+'/50','red'),
                r.attendance>=75?badge(r.attendance+'%','green'):badge(r.attendance+'%','red')]));
          } else {
            html += buildTable(['Rank','Roll No','Name','Section','CGPA','Attendance'],
              data.data.map(r => [badge(r.rank,'green'), r.roll, r.name, badge(r.section,'green'),
                badge(r.cgpa, r.cgpa>=8?'green':r.cgpa>=6?'yellow':'red'),
                r.attendance>=75?badge(r.attendance+'%','green'):badge(r.attendance+'%','red')]));
          }
          lastReportData = { type: 'section_toppers', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'section_backlogs' && data.data) {
          let html = `<strong>⚠️ Students with >${data.threshold} Backlogs in ${data.section} (${data.count} found)</strong>`;
          html += buildTable(['Roll No','Name','Section','CGPA','Attendance','Backlogs'],
            data.data.map(s => [s.roll, s.name, badge(s.section,'green'),
              badge(s.cgpa, s.cgpa>=6?'yellow':'red'),
              s.attendance>=75?badge(s.attendance+'%','green'):badge(s.attendance+'%','red'),
              badge(s.backlogs,'red')]));
          lastReportData = { type: 'section_backlogs', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'section_performance') {
          let html = `<strong>📊 Performance Report — ${data.section} (${data.count} students)</strong>
            <table class="report-table" style="margin-top:10px;">
              <thead><tr><th>Metric</th><th>Value</th><th>Status</th></tr></thead>
              <tbody>
                <tr><td>Avg CGPA</td><td>${data.avg_cgpa}</td><td>${badge(data.avg_cgpa, data.avg_cgpa>=7?'green':data.avg_cgpa>=5.5?'yellow':'red')}</td></tr>
                <tr><td>Avg Attendance</td><td>${data.avg_attendance}%</td><td>${data.avg_attendance>=75?badge(data.avg_attendance+'%','green'):badge(data.avg_attendance+'%','red')}</td></tr>
              </tbody>
            </table><br/><strong>📚 Subject-wise Breakdown</strong>`;
          html += buildTable(['Subject','Avg External','Avg Internal','Avg Attendance','Pass Rate','Low Attend'],
            data.subjects.map(r => [
              `<strong>${r.subject}</strong>`,
              r.avg_external>=40?badge(r.avg_external+'/100','green'):badge(r.avg_external+'/100','red'),
              r.avg_internal>=30?badge(r.avg_internal+'/50','green'):badge(r.avg_internal+'/50','red'),
              r.avg_attend>=75?badge(r.avg_attend+'%','green'):badge(r.avg_attend+'%','red'),
              r.pass_rate>=75?badge(r.pass_rate+'%','green'):badge(r.pass_rate+'%','red'),
              badge(r.low_attend,'red')]));
          lastReportData = { type: 'section_performance', students: data.data || [] };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'section_cgpa_filter' && data.data) {
          const dir = data.direction === 'above' ? '≥' : '<';
          let html = `<strong>🎓 Students with CGPA ${dir}${data.threshold} in ${data.section} (${data.count} found)</strong>`;
          html += buildTable(['Roll No','Name','Section','CGPA','Attendance','Backlogs'],
            data.data.map(s => [s.roll, s.name, badge(s.section,'green'),
              badge(s.cgpa, s.cgpa>=8?'green':s.cgpa>=6?'yellow':'red'),
              s.attendance>=75?badge(s.attendance+'%','green'):badge(s.attendance+'%','red'),
              s.backlogs>0?badge(s.backlogs,'red'):badge('None','green')]));
          lastReportData = { type: 'section_cgpa_filter', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'compare_sections') {
          const s1 = data.sec1, s2 = data.sec2;
          const subj = data.subject ? ` — ${data.subject}` : '';
          let html = `<strong>⚖️ Section Comparison${subj}: ${s1.section} vs ${s2.section}</strong>`;
          if (data.subject) {
            html += buildTable(['Metric', s1.section, s2.section],
              [['Students', s1.count, s2.count],
               ['Avg External', s1.avg_external+'/100', s2.avg_external+'/100'],
               ['Avg Internal', s1.avg_internal+'/50', s2.avg_internal+'/50'],
               ['Avg Attendance', s1.avg_attend+'%', s2.avg_attend+'%'],
               ['Pass Rate', s1.pass_rate+'%', s2.pass_rate+'%']]);
          } else {
            html += buildTable(['Metric', s1.section, s2.section],
              [['Students', s1.count, s2.count],
               ['Avg CGPA', s1.avg_cgpa, s2.avg_cgpa],
               ['Avg Attendance', s1.avg_attend+'%', s2.avg_attend+'%'],
               ['Avg External', s1.avg_external+'/100', s2.avg_external+'/100']]);
          }
          lastReportData = { type: 'compare_sections', students: [s1, s2] };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'subject_failure_rate' && data.data) {
          let html = `<strong>📉 Subject Failure Rate Analysis</strong>`;
          html += buildTable(['Subject','Total','Failures','Fail Rate','Avg External','Avg Internal'],
            data.data.map(r => [`<strong>${r.subject}</strong>`, r.count,
              badge(r.fail_count,'red'),
              r.fail_rate>30?badge(r.fail_rate+'%','red'):r.fail_rate>15?badge(r.fail_rate+'%','yellow'):badge(r.fail_rate+'%','green'),
              r.avg_external>=40?badge(r.avg_external+'/100','green'):badge(r.avg_external+'/100','red'),
              r.avg_internal>=30?badge(r.avg_internal+'/50','green'):badge(r.avg_internal+'/50','red')]));
          lastReportData = { type: 'subject_failure_rate', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'marks_distribution' && data.data) {
          const b = data.buckets;
          let html = `<strong>📊 Marks Distribution — ${data.subject} in ${data.section} (${data.count} students)</strong>
            <table class="report-table" style="margin-top:10px;">
              <thead><tr><th>Range</th><th>Count</th><th>Bar</th></tr></thead><tbody>`;
          Object.entries(b).forEach(([range, cnt]) => {
            const pct = data.count > 0 ? Math.round(cnt/data.count*100) : 0;
            const color = range.startsWith('0') ? 'red' : range.startsWith('4') ? 'yellow' : 'green';
            html += `<tr><td>${range}</td><td>${badge(cnt, color)}</td><td><div style="background:${color==='green'?'#4caf50':color==='yellow'?'#ff9800':'#f44336'};height:12px;width:${pct*2}px;border-radius:4px;display:inline-block"></div> ${pct}%</td></tr>`;
          });
          html += `</tbody></table><br/><strong>📋 Student Details</strong>`;
          html += buildTable(['Roll No','Name','Section','External (/100)','Internal (/50)','Attendance'],
            data.data.map(r => [r.roll, r.name, badge(r.section,'green'),
              r.external>=40?badge(r.external+'/100','green'):badge(r.external+'/100','red'),
              r.internal>=30?badge(r.internal+'/50','green'):badge(r.internal+'/50','red'),
              r.attendance>=75?badge(r.attendance+'%','green'):badge(r.attendance+'%','red')]));
          lastReportData = { type: 'marks_distribution', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'subject_trend' && data.data) {
          let html = `<strong>📈 ${data.subject} Performance Trend Across Sections</strong>`;
          html += buildTable(['Section','Students','Avg External','Avg Attendance','Pass Rate'],
            data.data.map(r => [badge(r.section,'green'), r.count,
              r.avg_external>=40?badge(r.avg_external+'/100','green'):badge(r.avg_external+'/100','red'),
              r.avg_attend>=75?badge(r.avg_attend+'%','green'):badge(r.avg_attend+'%','red'),
              r.pass_rate>=75?badge(r.pass_rate+'%','green'):badge(r.pass_rate+'%','red')]));
          lastReportData = { type: 'subject_trend', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'perfect_attendance' && data.data) {
          let html = `<strong>✅ Students with Perfect Attendance (${data.count} found)</strong>`;
          html += buildTable(['Roll No','Name','Section','Attendance','CGPA'],
            data.data.map(s => [s.roll, s.name, badge(s.section,'green'),
              badge(s.attendance+'%','green'),
              badge(s.cgpa, s.cgpa>=8?'green':s.cgpa>=6?'yellow':'red')]));
          lastReportData = { type: 'perfect_attendance', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'section_stats' && data.data) {
          let html = `<strong>📋 Section Statistics (${data.data.length} sections)</strong>`;
          html += buildTable(['Section','Students','Avg CGPA','Avg Attendance','≥75% Att','<75% Att'],
            data.data.map(r => [badge(r.section,'green'), r.count,
              badge(r.avg_cgpa, r.avg_cgpa>=7?'green':r.avg_cgpa>=5.5?'yellow':'red'),
              r.avg_attend>=75?badge(r.avg_attend+'%','green'):badge(r.avg_attend+'%','red'),
              badge(r.above_75,'green'), badge(r.below_75,'red')]));
          lastReportData = { type: 'section_stats', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'dept_summary') {
          let html = `<strong>🏫 Department Summary (${data.count} students)</strong>
            <table class="report-table" style="margin-top:10px;">
              <thead><tr><th>Metric</th><th>Value</th><th>Status</th></tr></thead>
              <tbody>
                <tr><td>Avg CGPA</td><td>${data.avg_cgpa}</td><td>${badge(data.avg_cgpa, data.avg_cgpa>=7?'green':data.avg_cgpa>=5.5?'yellow':'red')}</td></tr>
                <tr><td>Avg Attendance</td><td>${data.avg_attend}%</td><td>${data.avg_attend>=75?badge(data.avg_attend+'%','green'):badge(data.avg_attend+'%','red')}</td></tr>
                <tr><td>Avg Internal</td><td>${data.avg_internal}/50</td><td>${data.avg_internal>=30?badge(data.avg_internal+'/50','green'):badge(data.avg_internal+'/50','red')}</td></tr>
                <tr><td>Avg External</td><td>${data.avg_external}/100</td><td>${data.avg_external>=40?badge(data.avg_external+'/100','green'):badge(data.avg_external+'/100','red')}</td></tr>
              </tbody>
            </table><br/><strong>📚 Subject-wise Summary</strong>`;
          html += buildTable(['Subject','Avg External','Avg Attendance','Pass Rate'],
            (data.subjects||[]).map(r => [`<strong>${r.subject}</strong>`,
              r.avg_external>=40?badge(r.avg_external+'/100','green'):badge(r.avg_external+'/100','red'),
              r.avg_attend>=75?badge(r.avg_attend+'%','green'):badge(r.avg_attend+'%','red'),
              r.pass_rate>=75?badge(r.pass_rate+'%','green'):badge(r.pass_rate+'%','red')]));
          lastReportData = { type: 'dept_summary', students: data.subjects || [] };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'predict_backlog' && data.data) {
          const scope = data.section !== 'All' ? ` in ${data.section}` : '';
          const subj  = data.subject ? ` (${data.subject})` : '';
          let html = `<strong>🔮 Backlog Risk Prediction${subj}${scope} — ${data.count} at risk</strong>`;
          if (data.subject) {
            html += buildTable(['Roll No','Name','Section','Attendance','Internal','External','Risk'],
              data.data.map(r => [r.roll, r.name, badge(r.section,'green'),
                r.attendance>=75?badge(r.attendance+'%','green'):badge(r.attendance+'%','red'),
                r.internal>=30?badge(r.internal+'/50','green'):badge(r.internal+'/50','red'),
                r.external>=40?badge(r.external+'/100','green'):badge(r.external+'/100','red'),
                badge('⚠️ Risk '+r.risk_score+'/3','red')]));
          } else {
            html += buildTable(['Roll No','Name','Section','CGPA','Attendance','Backlogs','Risk'],
              data.data.map(r => [r.roll, r.name, badge(r.section,'green'),
                badge(r.cgpa, r.cgpa>=6?'yellow':'red'),
                r.attendance>=75?badge(r.attendance+'%','green'):badge(r.attendance+'%','red'),
                r.backlogs>0?badge(r.backlogs,'red'):badge('0','green'),
                badge('⚠️ Risk '+r.risk_score+'/3','red')]));
          }
          lastReportData = { type: 'predict_backlog', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'cgpa_threshold' && data.data) {
          const dirSym = {'below':'<','at most':'≤','above':'>','at least':'≥'}[data.direction] || data.direction;
          let html = `<strong>🎓 Students with CGPA ${dirSym} ${data.threshold} (${data.count} found)</strong>`;
          html += buildTable(['Roll No','Name','Section','CGPA','Attendance','Backlogs'],
            data.data.map(s => [s.roll, s.name, badge(s.section,'green'),
              badge(s.cgpa, s.cgpa>=8?'green':s.cgpa>=6?'yellow':'red'),
              s.attendance>=75?badge(s.attendance+'%','green'):badge(s.attendance+'%','red'),
              s.backlogs>0?badge(s.backlogs,'red'):badge('None','green')]));
          lastReportData = { type: 'cgpa_threshold', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'internal_filter' && data.data) {
          const subjectLabel = data.subject ? `${data.subject} ` : '';
          const dirSym = {'below':'<','at most':'≤','above':'>','at least':'≥'}[data.direction] || data.direction;
          let html = `<strong>📝 Students Scoring ${dirSym}${data.threshold} in ${subjectLabel}Internals (${data.count} found)</strong>`;
          if (data.subject) {
            // Subject-specific: show internal, external, attendance
            html += buildTable(['Roll No','Name','Section','Internal (/50)','External (/100)','Attendance'],
              data.data.map(r => [r.roll, r.name, badge(r.section,'green'),
                r.internal>=30?badge(r.internal+'/50','green'):badge(r.internal+'/50','red'),
                (r.external !== undefined) ? (r.external>=40?badge(r.external+'/100','green'):badge(r.external+'/100','red')) : '—',
                r.attendance>=75?badge(r.attendance+'%','green'):badge(r.attendance+'%','red')]));
          } else {
            // No subject: show internal, attendance, cgpa
            html += buildTable(['Roll No','Name','Section','Internal (/50)','Attendance','CGPA'],
              data.data.map(r => [r.roll, r.name, badge(r.section,'green'),
                r.internal>=30?badge(r.internal+'/50','green'):badge(r.internal+'/50','red'),
                r.attendance>=75?badge(r.attendance+'%','green'):badge(r.attendance+'%','red'),
                badge(r.cgpa, r.cgpa>=8?'green':r.cgpa>=6?'yellow':'red')]));
          }
          lastReportData = { type: 'internal_filter', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.report_type === 'external_filter' && data.data) {
          const subjectLabel = data.subject ? `${data.subject} ` : '';
          const dirSym = {'below':'<','at most':'≤','above':'>','at least':'≥'}[data.direction] || data.direction;
          let html = `<strong>📝 Students Scoring ${dirSym}${data.threshold} in ${subjectLabel}Externals (${data.count} found)</strong>`;
          if (data.subject) {
            html += buildTable(['Roll No','Name','Section','External (/100)','Internal (/50)','Attendance'],
              data.data.map(r => [r.roll, r.name, badge(r.section,'green'),
                r.external>=40?badge(r.external+'/100','green'):badge(r.external+'/100','red'),
                (r.internal !== undefined) ? (r.internal>=30?badge(r.internal+'/50','green'):badge(r.internal+'/50','red')) : '—',
                r.attendance>=75?badge(r.attendance+'%','green'):badge(r.attendance+'%','red')]));
          } else {
            html += buildTable(['Roll No','Name','Section','External (/100)','Internal (/50)','Attendance','CGPA'],
              data.data.map(r => [r.roll, r.name, badge(r.section,'green'),
                r.external>=40?badge(r.external+'/100','green'):badge(r.external+'/100','red'),
                r.internal>=30?badge(r.internal+'/50','green'):badge(r.internal+'/50','red'),
                r.attendance>=75?badge(r.attendance+'%','green'):badge(r.attendance+'%','red'),
                badge(r.cgpa, r.cgpa>=8?'green':r.cgpa>=6?'yellow':'red')]));
          }
          lastReportData = { type: 'external_filter', students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(html);
        } else if (data.data) {
          lastReportData = { type: data.report_type, students: data.data };
          exportBar.style.display = 'flex';
          appendBotResponse(buildReportHTML(data.report_type, data.data));
        } else {
          appendBotResponse("Sorry, I couldn't fetch the report. Try again.");
        }
      } else {
        appendBotResponse(`I didn't understand that. Try asking about attendance, marks, backlogs, CGPA, or toppers.`);
      }
    } catch (err) {
      removeTyping();
      console.error('Chat error:', err);
      appendBotResponse('Error connecting to server. Make sure Flask is running.');
    }
  }

  // ===== APPEND USER MESSAGE =====
  function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `message ${role === 'user' ? 'user-message' : 'bot-message'}`;
    div.innerHTML = `
      <span class="avatar">${role === 'user' ? '👤' : '<img src="/static/images/bot-icon.svg" alt="Bot" style="width: 32px; height: 32px;">'}</span>
      <div class="bubble">${text}</div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // ===== APPEND BOT RESPONSE (HTML) =====
  function appendBotResponse(html) {
    const div = document.createElement('div');
    div.className = 'message bot-message';
    div.innerHTML = `<span class="avatar"><img src="/static/images/bot-icon.svg" alt="Bot" style="width: 32px; height: 32px;"></span><div class="bubble">${html}</div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // ===== TYPING INDICATOR =====
  function showTyping() {
    const div = document.createElement('div');
    div.className = 'message bot-message typing';
    div.id = 'typingIndicator';
    div.innerHTML = `<span class="avatar"><img src="/static/images/bot-icon.svg" alt="Bot" style="width: 32px; height: 32px;"></span><div class="bubble">Generating report...</div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  function removeTyping() {
    const t = document.getElementById('typingIndicator');
    if (t) t.remove();
  }

  // ===== BUILD REPORT HTML FROM API DATA =====
  function buildReportHTML(type, students) {
    if (!students || students.length === 0)
      return `No data found for this report with the current filters.`;

    const titles = {
      attendance: '📋 Attendance Report',
      low_attendance: '⚠️ Low Attendance Students',
      internal_marks: '📝 Internal Marks Report',
      external_marks: '📝 External Marks Report',
      semester_result: '📊 Semester Result Summary',
      backlogs: '⚠️ Backlog Report',
      repeated_subjects: '🔁 Repeated Subjects Report',
      pending_completions: '⏳ Pending Course Completions',
      cgpa: '🏆 CGPA Report',
      toppers: '🥇 Academic Toppers',
      rankings: '📈 Student Rankings',
      risk: '🚨 Academic Risk Students',
      top_performers: '⭐ Top Performers',
    };

    let html = `<strong>${titles[type] || 'Report'}</strong><br/>`;

    if (type === 'attendance' || type === 'low_attendance') {
      const rows = students.map(s => [s.roll, s.name, s.semester, s.batch, s.attendance >= 75 ? badge(s.attendance + '%', 'green') : badge(s.attendance + '%', 'red')]);
      html += buildTable(['Roll No', 'Name', 'Semester', 'Batch', 'Attendance'], rows);
    } else if (type === 'internal_marks') {
      const rows = students.map(s => [s.roll, s.name, s.semester, s.internal >= 30 ? badge(s.internal + '/50', 'green') : badge(s.internal + '/50', 'red')]);
      html += buildTable(['Roll No', 'Name', 'Semester', 'Internal Marks'], rows);
    } else if (type === 'external_marks') {
      const rows = students.map(s => [s.roll, s.name, s.semester, s.external >= 40 ? badge(s.external + '/100', 'green') : badge(s.external + '/100', 'red')]);
      html += buildTable(['Roll No', 'Name', 'Semester', 'External Marks'], rows);
    } else if (type === 'semester_result') {
      const rows = students.map(s => [s.roll, s.name, s.semester, s.cgpa, s.backlogs === 0 ? badge('PASS', 'green') : badge('BACKLOG', 'red')]);
      html += buildTable(['Roll No', 'Name', 'Semester', 'CGPA', 'Result'], rows);
    } else if (type === 'backlogs' || type === 'repeated_subjects') {
      const rows = students.map(s => [s.roll, s.name, s.semester, s.batch,
        badge(s.backlogs + ' subject(s)', 'red'),
        s.cgpa < 5 ? badge('Critical', 'red') : badge('Monitor', 'yellow')]);
      html += buildTable(['Roll No', 'Name', 'Semester', 'Batch', 'Backlogs', 'Status'], rows);
    } else if (type === 'pending_completions') {
      const rows = students.map(s => [s.roll, s.name, s.semester, s.batch,
        badge(s.backlogs + ' pending', 'red'),
        badge(s.attendance + '%', s.attendance >= 75 ? 'yellow' : 'red')]);
      html += buildTable(['Roll No', 'Name', 'Semester', 'Batch', 'Pending Courses', 'Attendance'], rows);
    } else if (type === 'toppers' || type === 'rankings') {
      const rows = students.map((s, i) => [i + 1, s.roll, s.name, s.semester, badge(s.cgpa, 'green')]);
      html += buildTable(['Rank', 'Roll No', 'Name', 'Semester', 'CGPA'], rows);
    } else if (type === 'risk') {
      const rows = students.map(s => {
        const risks = [];
        if (s.cgpa < 6)        risks.push(badge('Low CGPA', 'red'));
        if (s.backlogs >= 2)   risks.push(badge('Backlogs', 'red'));
        if (s.attendance < 65) risks.push(badge('Low Attendance', 'yellow'));
        return [s.roll, s.name, s.semester, s.cgpa, s.attendance + '%', risks.join(' ')];
      });
      html += buildTable(['Roll No', 'Name', 'Sem', 'CGPA', 'Attendance', 'Risk Flags'], rows);
    } else if (type === 'cgpa') {
      const rows = students.map((s, i) => [i + 1, s.roll, s.name, s.semester,
        badge(s.cgpa, s.cgpa >= 8 ? 'green' : s.cgpa >= 6 ? 'yellow' : 'red'),
        s.backlogs > 0 ? badge(s.backlogs + ' backlog(s)', 'red') : badge('Clear', 'green')]);
      html += buildTable(['#', 'Roll No', 'Name', 'Semester', 'CGPA', 'Backlogs'], rows);
    } else if (type === 'top_performers') {
      const rows = students.map(s => [s.roll, s.name, s.semester, badge(s.cgpa, 'green'), badge(s.attendance + '%', 'green')]);
      html += buildTable(['Roll No', 'Name', 'Semester', 'CGPA', 'Attendance'], rows);
    } else {
      const rows = students.map(s => [s.roll, s.name, s.semester, s.cgpa]);
      html += buildTable(['Roll No', 'Name', 'Semester', 'CGPA'], rows);
    }
    return html;
  }

  // ===== EXPORT =====
  async function doExport(fmt) {
    if (!lastReportData || !lastReportData.students) return;

    // For summary reports (arrays of objects, not student arrays), export as-is
    // For student arrays, export directly
    const exportData = lastReportData.students;

    if (fmt === 'pdf') {
      exportPDF(lastReportData.type, exportData);
      return;
    }

    const res = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: exportData, format: fmt, report_type: lastReportData.type })
    });
    if (res.ok) {
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href = url; a.download = `${lastReportData.type}.${fmt === 'excel' ? 'xlsx' : fmt}`;
      a.click(); URL.revokeObjectURL(url);
    }
  }

  function exportPDF(reportType, data) {
    if (!data || data.length === 0) return;
    const keys = Object.keys(data[0]);
    let html = `<html><head><style>
      body{font-family:Arial,sans-serif;padding:20px;}
      h2{color:#1a237e;margin-bottom:16px;}
      table{width:100%;border-collapse:collapse;font-size:12px;}
      th{background:#1a237e;color:#fff;padding:8px;text-align:left;}
      td{padding:6px 8px;border-bottom:1px solid #eee;}
      tr:nth-child(even) td{background:#f5f6fa;}
    </style></head><body>
    <h2>${reportType.replace(/_/g,' ').toUpperCase()} REPORT</h2>
    <p style="font-size:11px;color:#888;margin-bottom:12px;">Generated: ${new Date().toLocaleString()}</p>
    <table><thead><tr>${keys.map(k=>`<th>${k}</th>`).join('')}</tr></thead><tbody>
    ${data.map(row=>`<tr>${keys.map(k=>`<td>${row[k]??''}</td>`).join('')}</tr>`).join('')}
    </tbody></table></body></html>`;
    const win = window.open('', '_blank');
    win.document.write(html);
    win.document.close();
    win.print();
  }

  document.getElementById('exportCSV').addEventListener('click',   () => doExport('csv'));
  document.getElementById('exportExcel').addEventListener('click', () => doExport('excel'));
  document.getElementById('exportPDF').addEventListener('click',   () => doExport('pdf'));

  // ===== HELPERS =====
  function buildTable(headers, rows) {
    let html = `<table class="report-table"><thead><tr>`;
    headers.forEach(h => html += `<th>${h}</th>`);
    html += `</tr></thead><tbody>`;
    rows.forEach(r => { html += `<tr>`; r.forEach(cell => html += `<td>${cell}</td>`); html += `</tr>`; });
    html += `</tbody></table>`;
    return html;
  }

  function badge(val, type) {
    return `<span class="badge badge-${type}">${val}</span>`;
  }
}

// ===== DATA MANAGEMENT PAGE =====
const isDataPage = document.querySelector('.data-content') !== null;

if (isDataPage) {
  // Load students will be called after function is defined

  // ===== SESSION COUNTDOWN TIMER FOR DATA PAGE =====
  (function() {
    const TIMEOUT_MS = 15 * 60 * 1000;
    const timerEl = document.getElementById('sessionTimer');
    if (!timerEl) return; // Exit if timer element doesn't exist
    
    let deadline = Date.now() + TIMEOUT_MS;
    let lastActivityUpdate = 0;

    // Fetch actual last_active from server ONCE on page load
    fetch('/api/me').then(r => r.json()).then(data => {
      if (data.last_active) {
        const serverTime = new Date(data.last_active + 'Z').getTime();
        deadline = serverTime + TIMEOUT_MS;
      }
    }).catch(() => {});

    // Reset deadline on user activity (but throttle server updates to every 30 seconds)
    function onActivity() {
      const now = Date.now();
      deadline = now + TIMEOUT_MS;
      
      // Only update server every 30 seconds to avoid constant API calls
      if (now - lastActivityUpdate > 30000) {
        lastActivityUpdate = now;
        fetch('/data/students?search=').catch(() => {}); // Keepalive request
      }
    }

    ['click', 'keydown', 'scroll'].forEach(evt =>
      document.addEventListener(evt, onActivity, { passive: true, once: false })
    );

    setInterval(() => {
      const remaining = deadline - Date.now();
      if (remaining <= 0) {
        window.location.href = '/logout';
        return;
      }
      const mins = Math.floor(remaining / 60000);
      const secs = Math.floor((remaining % 60000) / 1000);
      if (timerEl) {
        timerEl.textContent = `⏱ ${mins}:${secs.toString().padStart(2, '0')}`;
        timerEl.style.color = remaining < 2 * 60 * 1000 ? '#ff5252' : '#c5cae9';
      }
    }, 1000);
  })();

  // Auto-calculate semester from joining year
  window.autoCalcSemester = function() {
    const year = parseInt(document.getElementById('f_joining_year').value);
    if (!year) return;

    const now        = new Date();
    const currYear   = now.getFullYear();
    const currMonth  = now.getMonth() + 1; // 1-12
    const yearsIn    = currYear - year;
    // Each academic year has 2 semesters. July-Dec = odd sem, Jan-June = even sem
    const semOffset  = currMonth >= 7 ? 1 : 0;
    let sem          = (yearsIn * 2) + semOffset;
    sem              = Math.min(Math.max(sem, 1), 8);

    const batchEnd   = year + 4;
    document.getElementById('f_sem').value   = sem;
    document.getElementById('f_batch').value = `${year}-${batchEnd.toString().slice(-2)}`;
  };

  // Auto-calculate CGPA from internal + external
  window.autoCalcCGPA = function() {
    const internal = parseFloat(document.getElementById('f_internal').value) || 0;
    const external = parseFloat(document.getElementById('f_external').value) || 0;
    if (!internal && !external) return;

    // Normalize: internal/50 * 40% + external/100 * 60% → scale to 10
    const score = ((internal / 50) * 40 + (external / 100) * 60);
    const cgpa  = Math.min((score / 10).toFixed(1), 10);
    document.getElementById('f_cgpa').value = cgpa;

    const badge = document.getElementById('cgpaBadge');
    if (cgpa >= 8.5)      { badge.textContent = '🌟 Excellent'; badge.style.color = '#2e7d32'; }
    else if (cgpa >= 7)   { badge.textContent = '✅ Good';      badge.style.color = '#1565c0'; }
    else if (cgpa >= 5.5) { badge.textContent = '⚠️ Average';  badge.style.color = '#f57f17'; }
    else                  { badge.textContent = '❌ Poor';      badge.style.color = '#c62828'; }
  };

  // Attendance badge
  window.updateAttendanceBadge = function() {
    const val   = parseInt(document.getElementById('f_attendance').value) || 0;
    const badge = document.getElementById('attendanceBadge');
    if (val >= 85)      { badge.textContent = '✅ Good Standing';    badge.style.color = '#2e7d32'; }
    else if (val >= 75) { badge.textContent = '⚠️ Borderline';      badge.style.color = '#f57f17'; }
    else                { badge.textContent = '❌ Low — Defaulter';  badge.style.color = '#c62828'; }
  };

  // Tab switching
  window.switchTab = function(tab) {
    ['manual','upload','view'].forEach(t => {
      document.getElementById(`tab${t.charAt(0).toUpperCase()+t.slice(1)}Content`).classList.add('hidden');
      document.getElementById(`tab${t.charAt(0).toUpperCase()+t.slice(1)}`).classList.remove('active');
    });
    document.getElementById(`tab${tab.charAt(0).toUpperCase()+tab.slice(1)}Content`).classList.remove('hidden');
    document.getElementById(`tab${tab.charAt(0).toUpperCase()+tab.slice(1)}`).classList.add('active');
    if (tab === 'view') loadStudents();
  };

  // Submit form
  const studentForm = document.getElementById('studentForm');
  if (studentForm) {
    studentForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const editRoll = document.getElementById('editRoll').value;
    const payload  = {
      roll:       document.getElementById('f_roll').value.trim(),
      name:       document.getElementById('f_name').value.trim(),
      department: document.getElementById('f_dept').value,
      section:    document.getElementById('f_section').value,
      semester:   document.getElementById('f_sem').value,
      batch:      document.getElementById('f_batch').value.trim(),
      cgpa:       document.getElementById('f_cgpa').value,
      attendance: document.getElementById('f_attendance').value,
      backlogs:   document.getElementById('f_backlogs').value,
      internal:   document.getElementById('f_internal').value,
      external:   document.getElementById('f_external').value,
      cn_att:  document.getElementById('f_cn_att').value,
      cn_int:  document.getElementById('f_cn_int').value,
      cn_ext:  document.getElementById('f_cn_ext').value,
      se_att:  document.getElementById('f_se_att').value,
      se_int:  document.getElementById('f_se_int').value,
      se_ext:  document.getElementById('f_se_ext').value,
      ads_att: document.getElementById('f_ads_att').value,
      ads_int: document.getElementById('f_ads_int').value,
      ads_ext: document.getElementById('f_ads_ext').value,
      pdc_att: document.getElementById('f_pdc_att').value,
      pdc_int: document.getElementById('f_pdc_int').value,
      pdc_ext: document.getElementById('f_pdc_ext').value,
    };
    const url = editRoll ? '/data/update' : '/data/add';
    if (editRoll) payload.roll = editRoll;

    const res  = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    const msg  = document.getElementById('formMsg');
    msg.textContent = data.message;
    msg.classList.remove('hidden');
    msg.style.color = data.success ? '#2e7d32' : '#e53935';

    if (data.success) {
      resetForm();
      setTimeout(() => msg.classList.add('hidden'), 3000);
    }
    });
  }

  // Search
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      loadStudents(this.value);
    });
  }
}

// Load students table
window.loadStudents = async function(search = '') {
  const res  = await fetch(`/data/students?search=${encodeURIComponent(search)}`);
  const data = await res.json();
  const container = document.getElementById('studentsTable');
  const msg       = document.getElementById('tableMsg');

  if (!data.data || data.data.length === 0) {
    container.innerHTML = '';
    msg.textContent = 'No students found.';
    return;
  }
  msg.textContent = '';

  // Helper function to create badges
  const badge = (value, type) => `<span class="badge-${type}">${value}</span>`;
  const attendanceBadge = (val) => val >= 75 ? badge(val + '%', 'success') : badge(val + '%', 'danger');
  const cgpaBadge = (val) => val >= 8 ? badge(val, 'success') : val >= 6 ? badge(val, 'warning') : badge(val, 'danger');
  const backlogBadge = (val) => val > 0 ? badge(val, 'danger') : badge('0', 'success');

  let html = `<table class="data-table">
    <thead><tr>
      <th>Roll</th><th>Name</th><th>Sec</th><th>Dept</th><th>Sem</th><th>Batch</th>
      <th>CGPA</th><th>Attend</th><th>Backlogs</th><th>Int</th><th>Ext</th><th>Actions</th>
    </tr></thead><tbody>`;

  data.data.forEach(s => {
    const canEdit = !window._userRole || window._userRole !== 'HOD';
    html += `<tr>
      <td>${s.roll}</td>
      <td>${s.name}</td>
      <td>${s.section||''}</td>
      <td>${s.department}</td>
      <td>${s.semester}</td>
      <td>${s.batch}</td>
      <td>${cgpaBadge(s.cgpa)}</td>
      <td>${attendanceBadge(s.attendance)}</td>
      <td>${backlogBadge(s.backlogs)}</td>
      <td>${s.internal}/50</td>
      <td>${s.external}/100</td>
      <td>${canEdit ? `
        <button class="btn-edit"   onclick='editStudent(${JSON.stringify(s)})'>✏️</button>
        <button class="btn-delete" onclick="deleteStudent('${s.roll}')">🗑️</button>
      ` : '<span style="color:#aaa;font-size:11px;">View</span>'}
      </td>
    </tr>`;
  });
  html += '</tbody></table>';
  container.innerHTML = html;
};

// Initialize: Load students on page load if on data page
if (isDataPage) {
  window.loadStudents();
}

// Edit student — fill form
window.editStudent = function(s) {
  switchTab('manual');
  document.getElementById('formTitle').textContent = '✏️ Edit Student';
  document.getElementById('editRoll').value      = s.roll;
  document.getElementById('f_roll').value        = s.roll;
  document.getElementById('f_roll').disabled     = true;
  document.getElementById('f_name').value        = s.name;
  document.getElementById('f_dept').value        = s.department;
  document.getElementById('f_section').value     = s.section || 'SEC-1';
  document.getElementById('f_sem').value         = s.semester;
  document.getElementById('f_batch').value       = s.batch;
  document.getElementById('f_cgpa').value        = s.cgpa;
  document.getElementById('f_attendance').value  = s.attendance;
  document.getElementById('f_backlogs').value    = s.backlogs;
  document.getElementById('f_internal').value    = s.internal;
  document.getElementById('f_external').value    = s.external;
  // Fill per-subject fields if available
  const sub = s.subjects || {};
  ['cn','se','ads','pdc'].forEach(k => {
    const d = sub[k.toUpperCase()] || {};
    const el_att = document.getElementById(`f_${k}_att`);
    const el_int = document.getElementById(`f_${k}_int`);
    const el_ext = document.getElementById(`f_${k}_ext`);
    if (el_att) el_att.value = d.attendance ?? '';
    if (el_int) el_int.value = d.internal   ?? '';
    if (el_ext) el_ext.value = d.external   ?? '';
  });
  document.getElementById('submitBtn').textContent = '💾 Update Student';
};

// Delete student
window.deleteStudent = async function(roll) {
  if (!confirm(`Delete student ${roll}?`)) return;
  const res  = await fetch('/data/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ roll })
  });
  const data = await res.json();
  if (data.success) loadStudents();
};

// Reset form
window.resetForm = function() {
  document.getElementById('studentForm').reset();
  document.getElementById('editRoll').value        = '';
  document.getElementById('f_roll').disabled       = false;
  document.getElementById('f_sem').value           = '';
  document.getElementById('f_batch').value         = '';
  document.getElementById('f_cgpa').value          = '';
  document.getElementById('cgpaBadge').textContent      = '';
  document.getElementById('attendanceBadge').textContent = '';
  document.getElementById('formTitle').textContent = '➕ Add New Student';
  document.getElementById('submitBtn').textContent = '➕ Add Student';
};

// File upload
let selectedFile = null;
window.handleFileSelect = function(input) {
  selectedFile = input.files[0];
  if (!selectedFile) return;
  document.getElementById('fileName').textContent = `📄 ${selectedFile.name} (${(selectedFile.size/1024).toFixed(1)} KB)`;
  document.getElementById('fileInfo').classList.remove('hidden');
};

window.clearFile = function() {
  selectedFile = null;
  document.getElementById('fileInput').value = '';
  document.getElementById('fileInfo').classList.add('hidden');
  document.getElementById('uploadMsg').classList.add('hidden');
};

window.uploadFile = async function() {
  if (!selectedFile) return;
  const formData = new FormData();
  formData.append('file', selectedFile);

  const msgEl = document.getElementById('uploadMsg');
  msgEl.textContent = '⏳ Uploading...';
  msgEl.style.background = '#e8eaf6';
  msgEl.style.color = '#1a237e';
  msgEl.classList.remove('hidden');

  try {
    const res = await fetch('/data/upload', { 
      method: 'POST', 
      body: formData,
      credentials: 'same-origin'
    });

    // If redirected to login, session expired
    if (res.redirected || res.url.includes('/login')) {
      msgEl.textContent = '❌ Session expired. Please login again.';
      msgEl.style.background = '#ffebee';
      msgEl.style.color = '#c62828';
      setTimeout(() => window.location.href = '/login', 2000);
      return;
    }

    // Check content type — if not JSON, something went wrong
    const contentType = res.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      const text = await res.text();
      console.error('[UPLOAD] Non-JSON response:', text.substring(0, 200));
      msgEl.textContent = '❌ Server error. Check Flask console for details.';
      msgEl.style.background = '#ffebee';
      msgEl.style.color = '#c62828';
      return;
    }

    const data = await res.json();
    msgEl.textContent      = data.message;
    msgEl.style.background = data.success ? '#e8f5e9' : '#ffebee';
    msgEl.style.color      = data.success ? '#2e7d32' : '#c62828';

    if (data.success) {
      clearFile();
      setTimeout(() => switchTab('view'), 1200);
    }
  } catch (err) {
    console.error('[UPLOAD] Fetch error:', err);
    msgEl.textContent = '❌ Upload failed: ' + err.message;
    msgEl.style.background = '#ffebee';
    msgEl.style.color = '#c62828';
  }
};

// Drag and drop
if (isDataPage) {
  const zone = document.getElementById('uploadZone');
  if (zone) {
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.style.borderColor = '#3949ab'; });
    zone.addEventListener('dragleave', () => { zone.style.borderColor = '#c5cae9'; });
    zone.addEventListener('drop', e => {
      e.preventDefault();
      zone.style.borderColor = '#c5cae9';
      const file = e.dataTransfer.files[0];
      if (file) {
        selectedFile = file;
        document.getElementById('fileName').textContent = `📄 ${file.name}`;
        document.getElementById('fileInfo').classList.remove('hidden');
      }
    });
  }
}
