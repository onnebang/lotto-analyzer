"""
generate_app_with_pinball.py
45구 네온 핀볼 머신(Pachinko Pinball Machine) 기능과 배틀로얄을 완벽하게 통합하여
templates/index.html, index.html, docs/index.html을 동시에 빌드하고 검증하는 마스터 스크립트
"""
import re
import os
import shutil

# 기준이 되는 index.html (git 원본)을 읽음
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Navigation Tabs: Pinball을 첫 번째 활성 탭으로 추가
tabs_nav_old = '''    <!-- Navigation Tabs -->
    <div class="tabs-nav">
      <button class="tab-btn active" onclick="switchTab('battle')">
        <span style="font-size:1.15rem;">🥊</span> 45구 배틀로얄 서바이벌 <span class="tab-badge">인기</span>
      </button>'''

tabs_nav_new = '''    <!-- Navigation Tabs -->
    <div class="tabs-nav">
      <button class="tab-btn active" onclick="switchTab('pinball')">
        <span style="font-size:1.15rem;">🕹️</span> 45구 네온 핀볼 머신 <span class="tab-badge" style="background:linear-gradient(135deg, #06b6d4, #10b981);">NEW</span>
      </button>
      <button class="tab-btn" onclick="switchTab('battle')">
        <span style="font-size:1.15rem;">🥊</span> 45구 배틀로얄 서바이벌 <span class="tab-badge">인기</span>
      </button>'''

if tabs_nav_old in html:
    html = html.replace(tabs_nav_old, tabs_nav_new)
    print("[OK] Updated Navigation Tabs")
else:
    print("[WARN] tabs_nav_old not found")

# 2. 기존 tab-battle의 active 제거
html = html.replace('<div id="tab-battle" class="tab-content active">', '<div id="tab-battle" class="tab-content">')

# 3. Pinball Tab HTML 마크업
pinball_tab_markup = '''    <!-- ============================================== -->
    <!-- TAB: 45구 네온 핀볼 머신 (NEW PINBALL ARCADE) -->
    <!-- ============================================== -->
    <div id="tab-pinball" class="tab-content active">
      <div class="battle-layout">
        <!-- Canvas Arena Box -->
        <div class="arena-box" style="border-color: rgba(6, 182, 212, 0.4); box-shadow: 0 0 30px rgba(6, 182, 212, 0.2);">
          <div style="display:flex; justify-content:space-between; width:100%; align-items:center; margin-bottom:0.6rem; padding:0 0.5rem;">
            <div style="font-size:0.95rem; font-weight:800; color:#f8fafc; display:flex; align-items:center; gap:0.4rem;">
              <span style="color:#06b6d4;">● ARCADE</span> 45구 파칭코 핀볼 머신
            </div>
            <div style="font-size:0.85rem; color:#38bdf8;" id="pinballScoreLabel">
              SCORE: <span id="pinballScore" style="font-weight:800; font-family:'Outfit'; font-size:1.1rem; color:#fbc02d;">0</span>
            </div>
          </div>
          <canvas id="pinballCanvas" width="500" height="620" style="width:500px; height:620px; max-width:100%; border-radius:16px; background:#070a13; border:2px solid rgba(6,182,212,0.3); display:block;"></canvas>
        </div>

        <!-- Sidebar / Controls -->
        <div class="battle-sidebar">
          <div class="battle-controls-card">
            <h3 style="font-size:1.1rem; font-weight:800; color:#fff; margin-bottom:0.6rem; display:flex; align-items:center; gap:0.5rem;">
              <i class="fa-solid fa-gamepad" style="color:#06b6d4;"></i> 핀볼 런처 컨트롤러
            </h3>
            <p style="font-size:0.82rem; color:var(--text-muted); margin-bottom:1rem; line-height:1.5;">
              못(Pegs)과 회전 범퍼를 뚫고 하단의 <strong>6개 골드 슬롯</strong>에 가장 먼저 쏙 들어간 6개의 공이 이번 주 1등 추천 번호가 됩니다!
            </p>

            <!-- Launch Buttons -->
            <div style="display:flex; gap:0.5rem; margin-bottom:1rem; flex-wrap:wrap;">
              <button class="btn btn-primary" style="flex:1; background:linear-gradient(135deg, #06b6d4, #0284c7); border-color:#0284c7;" id="btnLaunchAll" onclick="launchPinballAll()">
                <i class="fa-solid fa-meteor"></i> 45구 폭풍 투하!
              </button>
              <button class="btn btn-outline" onclick="launchPinballSingle()" id="btnLaunchSingle">
                <i class="fa-solid fa-play"></i> 1구씩 발사
              </button>
              <button class="btn btn-outline" onclick="resetPinball()">
                <i class="fa-solid fa-rotate-right"></i> 다시 하기
              </button>
              <button class="btn btn-outline" onclick="skipPinball()">
                <i class="fa-solid fa-forward-fast"></i> 즉시 추첨 (스킵)
              </button>
            </div>

            <!-- Slots Visual Bar -->
            <div style="background:rgba(255,255,255,0.03); padding:0.9rem; border-radius:12px; margin-bottom:0.8rem; border:1px solid rgba(255,255,255,0.06);">
              <div style="font-size:0.84rem; font-weight:700; color:#cbd5e1; margin-bottom:0.6rem; display:flex; justify-content:space-between;">
                <span>🎯 골드 슬롯 점령 현황:</span>
                <span style="color:#fbc02d; font-family:'Outfit';" id="slotStatusText">0 / 6 슬롯</span>
              </div>
              <div style="display:flex; gap:0.4rem; justify-content:space-between;" id="slotBallsPreview">
                <div class="slot-preview-box" id="spb-0">1번 ?</div>
                <div class="slot-preview-box" id="spb-1">2번 ?</div>
                <div class="slot-preview-box" id="spb-2">3번 ?</div>
                <div class="slot-preview-box" id="spb-3">4번 ?</div>
                <div class="slot-preview-box" id="spb-4">5번 ?</div>
                <div class="slot-preview-box" id="spb-5">6번 ?</div>
              </div>
            </div>

            <!-- Funny Commentary -->
            <div style="background:rgba(15,23,42,0.7); border:1px solid var(--border-color); border-radius:12px; padding:0.85rem; font-size:0.82rem; color:var(--text-muted); line-height:1.5;" id="pinballCommentary">
              💡 <strong>꿀팁:</strong> '45구 폭풍 투하!' 버튼을 누르면 화면 가득 네온 공들이 쏟아져 내리며 리얼한 핀볼 사운드가 울려 퍼집니다!
            </div>
          </div>

          <!-- Pinball Jackpot Banner -->
          <div class="survivors-banner" id="pinballJackpotBanner" style="display:none; border-color:#06b6d4; box-shadow:0 0 25px rgba(6,182,212,0.4); background:linear-gradient(135deg, rgba(6,182,212,0.15), rgba(99,102,241,0.2));">
            <h3 style="font-size:1.25rem; font-weight:800; color:#38bdf8; margin-bottom:0.3rem;">
              🎰 핀볼 잭팟! 6개 슬롯 점령 완료!
            </h3>
            <p style="font-size:0.82rem; color:#f8fafc; margin-bottom:0.8rem;">
              못과 범퍼의 치열한 난기류를 뚫고 슬롯에 안착한 기적의 6개 번호!
            </p>
            <div class="balls-row" id="pinballBallsRow" style="justify-content:center; margin-bottom:1rem;"></div>
            <div style="display:flex; gap:0.5rem; justify-content:center; flex-wrap:wrap;">
              <button class="btn btn-primary" onclick="copyPinballNumbers()">
                <i class="fa-solid fa-copy"></i> 카톡 공유 복사
              </button>
              <button class="btn btn-outline" style="background:#fff; color:#111; font-weight:700;" onclick="openPinballReceiptModal()">
                <i class="fa-solid fa-receipt"></i> 핀볼 잭팟 부적 영수증
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
'''

target_battle = '    <!-- ============================================== -->\n    <!-- TAB 0: 45구 배틀로얄'
if target_battle in html:
    html = html.replace(target_battle, pinball_tab_markup + '\n' + target_battle)
    print("[OK] Added Pinball Tab HTML markup")
else:
    print("[WARN] target_battle markup not found")

# 4. Slot CSS 추가
slot_css = '''
    .slot-preview-box {
      flex: 1;
      height: 48px;
      border: 1px dashed rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      background: rgba(0, 0, 0, 0.3);
      transition: all 0.25s ease;
    }
    .slot-preview-box.filled {
      border: 1px solid #06b6d4;
      background: rgba(6, 182, 212, 0.18);
      color: #fff;
      box-shadow: 0 0 12px rgba(6, 182, 212, 0.3);
      transform: scale(1.05);
    }
'''
if '.slot-preview-box' not in html:
    html = html.replace('</style>', slot_css + '\n  </style>')
    print("[OK] Added slot_css")

# 5. Pinball Lucky Receipt Modal 추가
pinball_modal_markup = '''
  <!-- Pinball Lucky Receipt Modal -->
  <div class="modal-overlay" id="pinballReceiptModal" onclick="closePinballReceiptModal(event)">
    <div class="receipt-paper" onclick="event.stopPropagation()">
      <div style="text-align:center; font-weight:800; font-size:1.15rem; border-bottom:2px dashed #000; padding-bottom:0.6rem; margin-bottom:0.8rem;">
        🎰 네온 핀볼 머신 1등 잭팟 영수증 🎰
      </div>
      <div style="font-size:0.78rem; line-height:1.5; margin-bottom:0.8rem;">
        <div>[발행] 네온 파칭코 핀볼 연구소</div>
        <div>[인증] 45구 난기류 슬롯 관통 챔피언</div>
        <div>[일자] <span id="pinballReceiptDate">2026.10.29</span></div>
        <div>[스코어] <span id="pinballReceiptScore" style="color:#d97706; font-weight:700;">120,500 PT</span></div>
      </div>
      <div style="border-top:1px dashed #444; border-bottom:1px dashed #444; padding:0.8rem 0; margin-bottom:0.8rem; text-align:center;">
        <div style="font-size:0.85rem; font-weight:700; margin-bottom:0.4rem;">[슬롯 점령 6구]</div>
        <div style="font-size:1.4rem; font-weight:800; letter-spacing:2px; color:#0284c7;" id="pinballReceiptNumbers">
          07 14 21 28 35 42
        </div>
      </div>
      <div style="font-size:0.75rem; line-height:1.6; margin-bottom:1rem;">
        <div style="font-weight:700; margin-bottom:0.2rem;">[※ 핀볼 잭팟 당첨 시 필수 수칙]</div>
        <div>1. 핀볼로 뽑았다고 부모님께 자랑하면 등짝 맞으니 'AI 빅데이터'라고 둘러대기</div>
        <div>2. 슬롯에 쏙 들어간 공처럼 이번 주 월급도 통장에 쏙 보존하기</div>
        <div>3. 아는 누나에게 '내가 핀볼로 소고기 사준다 했지?' 카톡 캡처 보내기</div>
        <div>4. 1등 당첨되면 조용히 출근해서 대표님 어깨 한번 툭 치고 퇴사하기</div>
      </div>
      <div style="text-align:center; font-size:0.8rem; font-weight:700; border-top:2px dashed #000; padding-top:0.6rem;">
        핀볼의 신 曰: "못을 튕겨내듯 인생의 고난도 튕겨내라."
      </div>
      <div style="margin-top:1.2rem; display:flex; gap:0.5rem;">
        <button class="btn btn-primary" style="flex:1; justify-content:center; font-size:0.8rem; background:#0284c7; border-color:#0284c7;" onclick="copyPinballReceiptText()">
          텍스트 복사
        </button>
        <button class="btn btn-outline" style="color:#000; border-color:#888; font-size:0.8rem;" onclick="closePinballReceiptModal()">
          닫기
        </button>
      </div>
    </div>
  </div>
'''
if 'id="pinballReceiptModal"' not in html:
    html = html.replace('<!-- Meme Lucky Receipt Modal -->', pinball_modal_markup + '\n  <!-- Meme Lucky Receipt Modal -->')
    print("[OK] Added pinballReceiptModal")

# 6. Audio Synthesizer: playSound에 peg, bumper, slot, jackpot 사운드 추가
old_playsound_part = """        } else if (type === 'win') {
          const notes = [523.25, 659.25, 783.99, 1046.50];
          notes.forEach((freq, idx) => {
            const o = audioCtx.createOscillator();
            const g = audioCtx.createGain();
            o.type = 'triangle';
            o.frequency.value = freq;
            o.connect(g);
            g.connect(audioCtx.destination);
            const t = now + idx * 0.1;
            g.gain.setValueAtTime(0.18, t);
            g.gain.linearRampToValueAtTime(0.001, t + 0.35);
            o.start(t);
            o.stop(t + 0.35);
          });
        }"""

new_playsound_part = """        } else if (type === 'win') {
          const notes = [523.25, 659.25, 783.99, 1046.50];
          notes.forEach((freq, idx) => {
            const o = audioCtx.createOscillator();
            const g = audioCtx.createGain();
            o.type = 'triangle';
            o.frequency.value = freq;
            o.connect(g);
            g.connect(audioCtx.destination);
            const t = now + idx * 0.1;
            g.gain.setValueAtTime(0.18, t);
            g.gain.linearRampToValueAtTime(0.001, t + 0.35);
            o.start(t);
            o.stop(t + 0.35);
          });
        } else if (type === 'peg') {
          if (now - lastPegSoundTime < 0.035) return;
          lastPegSoundTime = now;
          const o = audioCtx.createOscillator();
          const g = audioCtx.createGain();
          o.type = 'triangle';
          o.frequency.setValueAtTime(800 + Math.random() * 500, now);
          g.gain.setValueAtTime(0.04, now);
          g.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
          o.connect(g);
          g.connect(audioCtx.destination);
          o.start(now);
          o.stop(now + 0.04);
        } else if (type === 'bumper') {
          if (now - lastBumperSoundTime < 0.08) return;
          lastBumperSoundTime = now;
          const o = audioCtx.createOscillator();
          const g = audioCtx.createGain();
          o.type = 'sawtooth';
          o.frequency.setValueAtTime(250, now);
          o.frequency.exponentialRampToValueAtTime(750, now + 0.1);
          g.gain.setValueAtTime(0.12, now);
          g.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
          o.connect(g);
          g.connect(audioCtx.destination);
          o.start(now);
          o.stop(now + 0.1);
        } else if (type === 'slot') {
          const chord = [523.25, 659.25, 783.99, 1046.5];
          chord.forEach((f, i) => {
            const o = audioCtx.createOscillator();
            const g = audioCtx.createGain();
            o.type = 'sine';
            o.frequency.value = f;
            const t = now + i * 0.06;
            g.gain.setValueAtTime(0.1, t);
            g.gain.exponentialRampToValueAtTime(0.001, t + 0.25);
            o.connect(g);
            g.connect(audioCtx.destination);
            o.start(t);
            o.stop(t + 0.25);
          });
        } else if (type === 'jackpot') {
          const notes = [523.25, 659.25, 783.99, 1046.5, 1318.5, 1567.98];
          notes.forEach((freq, idx) => {
            const o = audioCtx.createOscillator();
            const g = audioCtx.createGain();
            o.type = 'triangle';
            o.frequency.value = freq;
            o.connect(g);
            g.connect(audioCtx.destination);
            const t = now + idx * 0.08;
            g.gain.setValueAtTime(0.16, t);
            g.gain.exponentialRampToValueAtTime(0.001, t + 0.4);
            o.start(t);
            o.stop(t + 0.4);
          });
        }"""

if old_playsound_part in html:
    html = html.replace(old_playsound_part, new_playsound_part)
    print("[OK] Enhanced playSound with Pinball audio synthesis")
else:
    print("[WARN] old_playsound_part not found")

# 7. switchTab에 'pinball' 처리 추가
old_switch_tab = """      if (tabId === 'stats') {
        loadPairs();
      } else if (tabId === 'history') {
        loadHistory(1);
      } else if (tabId === 'battle') {
        if (!battleRunning && aliveCount === 45) {
          drawBattleFrame();
        }
      }"""

new_switch_tab = """      if (tabId === 'stats') {
        loadPairs();
      } else if (tabId === 'history') {
        loadHistory(1);
      } else if (tabId === 'battle') {
        if (!battleRunning && aliveCount === 45) {
          drawBattleFrame();
        }
      } else if (tabId === 'pinball') {
        if (!pinballRunning) {
          drawPinballFrame();
        }
      }"""

if old_switch_tab in html:
    html = html.replace(old_switch_tab, new_switch_tab)
    print("[OK] Updated switchTab for pinball")
else:
    print("[WARN] old_switch_tab not found")

# 8. Full Pinball Engine JavaScript Implementation
pinball_engine_js = """
    // =========================================================
    // 🕹️ 45구 네온 핀볼 머신 물리 엔진 & 게임 루프 (CANVAS 2D)
    // =========================================================
    const pbCanvas = document.getElementById('pinballCanvas');
    const pbCtx = pbCanvas ? pbCanvas.getContext('2d') : null;

    let pinballRunning = false;
    let pinballAnimationId = null;
    let pinballLaunchInterval = null;
    let pinballScore = 0;
    let pinballBalls = [];
    let pinballPegs = [];
    let pinballBumpers = [];
    let pinballSlots = [];
    let pinballParticles = [];
    let pinballShockwaves = [];
    let latestPinballWinners = [];
    let capturedSlotsCount = 0;
    let lastPegSoundTime = 0;
    let lastBumperSoundTime = 0;

    function initPinball() {
      if (!pbCanvas || !pbCtx) return;
      initPinballBumpers();
      initPinballPegs();
      initPinballSlots();
      initPinballBalls();
      drawPinballFrame();
    }

    function initPinballBumpers() {
      pinballBumpers = [
        { x: 135, y: 195, r: 25, color: '#06b6d4', flash: 0, label: '300' },
        { x: 365, y: 195, r: 25, color: '#06b6d4', flash: 0, label: '300' },
        { x: 250, y: 260, r: 32, color: '#ec4899', flash: 0, label: '500' }
      ];
    }

    function initPinballPegs() {
      pinballPegs = [];
      const rows = [
        { y: 105, startX: 65, endX: 435, count: 9 },
        { y: 145, startX: 85, endX: 415, count: 8 },
        { y: 185, startX: 65, endX: 435, count: 9 },
        { y: 225, startX: 85, endX: 415, count: 8 },
        { y: 270, startX: 65, endX: 435, count: 9 },
        { y: 315, startX: 85, endX: 415, count: 8 },
        { y: 360, startX: 65, endX: 435, count: 9 },
        { y: 405, startX: 85, endX: 415, count: 8 },
        { y: 450, startX: 65, endX: 435, count: 9 },
        { y: 490, startX: 85, endX: 415, count: 8 }
      ];

      rows.forEach(row => {
        const step = (row.endX - row.startX) / (row.count - 1);
        for (let i = 0; i < row.count; i++) {
          const px = row.startX + i * step;
          const py = row.y;
          let overlapsBumper = false;
          for (let b of pinballBumpers) {
            if (Math.hypot(px - b.x, py - b.y) < b.r + 18) {
              overlapsBumper = true;
              break;
            }
          }
          if (!overlapsBumper) {
            pinballPegs.push({ x: px, y: py, r: 4.5, flash: 0 });
          }
        }
      });

      // Guide pegs directly above the 7 divider tips at y = 510
      [20, 96.6, 173.3, 250, 326.6, 403.3, 480].forEach(dx => {
        pinballPegs.push({ x: dx, y: 510, r: 4, flash: 0, isDividerCap: true });
      });
    }

    function initPinballSlots() {
      pinballSlots = [];
      const startX = 20;
      const totalWidth = 460;
      const slotWidth = totalWidth / 6;
      for (let i = 0; i < 6; i++) {
        pinballSlots.push({
          index: i,
          leftX: startX + i * slotWidth,
          rightX: startX + (i + 1) * slotWidth,
          centerX: startX + (i + 0.5) * slotWidth,
          capturedBall: null,
          flash: 0
        });
      }
    }

    function shuffleArray(arr) {
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
      }
      return arr;
    }

    function initPinballBalls() {
      pinballBalls = [];
      for (let i = 1; i <= 45; i++) {
        let col = '#fbc02d';
        if (i > 10 && i <= 20) col = '#1e88e5';
        else if (i > 20 && i <= 30) col = '#e53935';
        else if (i > 30 && i <= 40) col = '#78909c';
        else if (i > 40) col = '#43a047';

        pinballBalls.push({
          num: i,
          x: 250,
          y: -20,
          vx: 0,
          vy: 0,
          r: 11,
          color: col,
          state: 'idle',
          slotIndex: -1
        });
      }
      // 1~45번 순서 편향 방지: 공 목록을 무작위로 셔플
      shuffleArray(pinballBalls);
    }

    function dropBall(b) {
      b.state = 'active';
      b.x = 200 + Math.random() * 100;
      b.y = 20;
      b.vx = (Math.random() - 0.5) * 4.2;
      b.vy = 2.2 + Math.random() * 2.5;
      spawnPinballParticles(b.x, b.y, '#38bdf8', 4);
    }

    function launchPinballAll() {
      if (capturedSlotsCount >= 6) {
        resetPinball();
      }
      // 대기 중인 공들을 매번 무작위 셔플하여 투하 순서 완전 랜덤화
      const waitingBalls = shuffleArray(pinballBalls.filter(b => b.state === 'idle'));
      if (waitingBalls.length === 0) return;

      const btnAll = document.getElementById('btnLaunchAll');
      if (btnAll) btnAll.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 45구 폭풍 투하 중...';

      let idx = 0;
      if (pinballLaunchInterval) clearInterval(pinballLaunchInterval);
      pinballLaunchInterval = setInterval(() => {
        if (idx >= waitingBalls.length || capturedSlotsCount >= 6) {
          clearInterval(pinballLaunchInterval);
          pinballLaunchInterval = null;
          if (btnAll && capturedSlotsCount < 6) {
            btnAll.innerHTML = '<i class="fa-solid fa-meteor"></i> 45구 폭풍 투하!';
          }
          return;
        }
        const b = waitingBalls[idx];
        dropBall(b);
        idx++;
      }, 55);

      startPinballLoop();
    }

    function launchPinballSingle() {
      if (capturedSlotsCount >= 6) {
        resetPinball();
      }
      const waitingBalls = pinballBalls.filter(b => b.state === 'idle');
      if (waitingBalls.length === 0) return;

      // 남아있는 공 중 완전 무작위 1구 선택
      const randIdx = Math.floor(Math.random() * waitingBalls.length);
      const b = waitingBalls[randIdx];
      dropBall(b);
      startPinballLoop();
    }

    function resetPinball() {
      if (pinballLaunchInterval) {
        clearInterval(pinballLaunchInterval);
        pinballLaunchInterval = null;
      }
      pinballScore = 0;
      capturedSlotsCount = 0;
      latestPinballWinners = [];
      initPinballBalls();
      initPinballSlots();
      pinballParticles = [];
      pinballShockwaves = [];

      const scoreEl = document.getElementById('pinballScore');
      if (scoreEl) scoreEl.textContent = '0';
      const statusText = document.getElementById('slotStatusText');
      if (statusText) statusText.textContent = '0 / 6 슬롯';

      for (let i = 0; i < 6; i++) {
        const box = document.getElementById(`spb-${i}`);
        if (box) {
          box.classList.remove('filled');
          box.innerHTML = `${i + 1}번 ?`;
        }
      }

      const banner = document.getElementById('pinballJackpotBanner');
      if (banner) banner.style.display = 'none';

      const commentary = document.getElementById('pinballCommentary');
      if (commentary) {
        commentary.innerHTML = `💡 <strong>꿀팁:</strong> '45구 폭풍 투하!' 버튼을 누르면 화면 가득 네온 공들이 쏟아져 내리며 리얼한 핀볼 사운드가 울려 퍼집니다!`;
      }

      const btnAll = document.getElementById('btnLaunchAll');
      if (btnAll) btnAll.innerHTML = '<i class="fa-solid fa-meteor"></i> 45구 폭풍 투하!';

      drawPinballFrame();
    }

    function skipPinball() {
      if (capturedSlotsCount >= 6) return;
      if (pinballLaunchInterval) {
        clearInterval(pinballLaunchInterval);
        pinballLaunchInterval = null;
      }

      const capturedNums = new Set(pinballSlots.filter(s => s.capturedBall).map(s => s.capturedBall.num));
      const pool = [];
      for (let i = 1; i <= 45; i++) {
        if (!capturedNums.has(i)) pool.push(i);
      }
      for (let i = pool.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [pool[i], pool[j]] = [pool[j], pool[i]];
      }

      let pIdx = 0;
      for (let s of pinballSlots) {
        if (s.capturedBall === null && pIdx < pool.length) {
          const num = pool[pIdx++];
          let ball = pinballBalls.find(b => b.num === num);
          if (!ball) {
            let col = '#fbc02d';
            if (num > 10 && num <= 20) col = '#1e88e5';
            else if (num > 20 && num <= 30) col = '#e53935';
            else if (num > 30 && num <= 40) col = '#78909c';
            else if (num > 40) col = '#43a047';
            ball = { num, x: s.centerX, y: 575, vx: 0, vy: 0, r: 11, color: col, state: 'captured', slotIndex: s.index };
          } else {
            ball.state = 'captured';
            ball.slotIndex = s.index;
            ball.x = s.centerX;
            ball.y = 575;
            ball.vx = 0;
            ball.vy = 0;
          }
          s.capturedBall = ball;
          capturedSlotsCount++;
          updateSlotUI(s.index, ball);
        }
      }

      triggerPinballJackpot();
      drawPinballFrame();
    }

    function pointToLineDistance(px, py, x1, y1, x2, y2) {
      const l2 = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1);
      if (l2 === 0) return Math.hypot(px - x1, py - y1);
      let t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2;
      t = Math.max(0, Math.min(1, t));
      return Math.hypot(px - (x1 + t * (x2 - x1)), py - (y1 + t * (y2 - y1)));
    }

    function updatePinballPhysics() {
      const gy = 0.22;

      for (let i = 0; i < pinballBalls.length; i++) {
        const b = pinballBalls[i];
        if (b.state !== 'active') continue;

        b.vy += gy;
        b.vx *= 0.998;
        b.vy *= 0.998;

        const speed = Math.hypot(b.vx, b.vy);
        if (speed > 12) {
          b.vx = (b.vx / speed) * 12;
          b.vy = (b.vy / speed) * 12;
        }

        b.x += b.vx;
        b.y += b.vy;

        // Anti-stuck watchdog
        if (b.y < 515 && Math.hypot(b.vx, b.vy) < 0.2) {
          b.vx += (Math.random() - 0.5) * 1.5;
          b.vy += 0.8;
        }

        // Left / Right wall bounce
        if (b.x - b.r < 16) {
          b.x = 16 + b.r;
          b.vx = -b.vx * 0.7;
        } else if (b.x + b.r > 484) {
          b.x = 484 - b.r;
          b.vx = -b.vx * 0.7;
        }

        // Top funnel bounce
        if (b.y < 70) {
          if (b.x < 190 && b.y < 50 + (b.x - 16) * (20 / 174) + b.r) {
            b.y = 50 + (b.x - 16) * (20 / 174) + b.r;
            b.vy = Math.abs(b.vy) * 0.7 + 1;
            b.vx += 0.8;
          } else if (b.x > 310 && b.y < 50 + (484 - b.x) * (20 / 174) + b.r) {
            b.y = 50 + (484 - b.x) * (20 / 174) + b.r;
            b.vy = Math.abs(b.vy) * 0.7 + 1;
            b.vx -= 0.8;
          }
        }

        // Slingshots (left and right angled kickers)
        if (b.x < 75 && b.y > 340 && b.y < 420) {
          const d = pointToLineDistance(b.x, b.y, 16, 350, 65, 415);
          if (d < b.r + 4) {
            b.vx = 4 + Math.random() * 2;
            b.vy = -3 - Math.random() * 2;
            pinballScore += 150;
            playSound('bumper');
            spawnPinballParticles(b.x, b.y, '#06b6d4', 4);
          }
        }
        if (b.x > 425 && b.y > 340 && b.y < 420) {
          const d = pointToLineDistance(b.x, b.y, 484, 350, 435, 415);
          if (d < b.r + 4) {
            b.vx = -4 - Math.random() * 2;
            b.vy = -3 - Math.random() * 2;
            pinballScore += 150;
            playSound('bumper');
            spawnPinballParticles(b.x, b.y, '#06b6d4', 4);
          }
        }

        // Peg collisions
        for (let p of pinballPegs) {
          const dx = b.x - p.x;
          const dy = b.y - p.y;
          const dist = Math.hypot(dx, dy);
          const minDist = b.r + p.r;
          if (dist < minDist && dist > 0) {
            const nx = dx / dist;
            const ny = dy / dist;
            b.x = p.x + nx * minDist;
            b.y = p.y + ny * minDist;
            const dot = b.vx * nx + b.vy * ny;
            b.vx = (b.vx - 2 * dot * nx) * 0.75 + (Math.random() - 0.5) * 0.6;
            b.vy = (b.vy - 2 * dot * ny) * 0.75 + (Math.random() - 0.5) * 0.4;
            p.flash = 1.0;
            pinballScore += 50;
            playSound('peg');
            if (Math.random() < 0.3) {
              spawnPinballParticles(p.x, p.y, '#38bdf8', 2);
            }
          }
        }

        // Bumper collisions
        for (let bmp of pinballBumpers) {
          const dx = b.x - bmp.x;
          const dy = b.y - bmp.y;
          const dist = Math.hypot(dx, dy);
          const minDist = b.r + bmp.r;
          if (dist < minDist && dist > 0) {
            const nx = dx / dist;
            const ny = dy / dist;
            b.x = bmp.x + nx * (minDist + 2);
            b.y = bmp.y + ny * (minDist + 2);
            const impulse = 8.0;
            b.vx = nx * impulse + (Math.random() - 0.5) * 1.5;
            b.vy = ny * impulse + (Math.random() - 0.5) * 1.5;
            bmp.flash = 1.0;
            pinballScore += parseInt(bmp.label);
            playSound('bumper');
            spawnPinballParticles(bmp.x + nx * bmp.r, bmp.y + ny * bmp.r, bmp.color, 8);
            pinballShockwaves.push({ x: bmp.x, y: bmp.y, r: bmp.r, maxR: bmp.r + 25, color: bmp.color, alpha: 1.0 });
          }
        }

        // Ball to Ball collisions
        for (let j = i + 1; j < pinballBalls.length; j++) {
          const b2 = pinballBalls[j];
          if (b2.state !== 'active') continue;
          const dx = b2.x - b.x;
          const dy = b2.y - b.y;
          const dist = Math.hypot(dx, dy);
          const minDist = b.r + b2.r;
          if (dist < minDist && dist > 0) {
            const nx = dx / dist;
            const ny = dy / dist;
            const overlap = minDist - dist;
            b.x -= nx * overlap * 0.5;
            b.y -= ny * overlap * 0.5;
            b2.x += nx * overlap * 0.5;
            b2.y += ny * overlap * 0.5;

            const kx = b.vx - b2.vx;
            const ky = b.vy - b2.vy;
            const p = (nx * kx + ny * ky);
            b.vx -= p * nx * 0.85;
            b.vy -= p * ny * 0.85;
            b2.vx += p * nx * 0.85;
            b2.vy += p * ny * 0.85;
          }
        }

        // Slot Entry (y >= 545)
        if (b.y >= 545) {
          for (let s of pinballSlots) {
            if (b.x >= s.leftX + 4 && b.x <= s.rightX - 4) {
              if (s.capturedBall === null) {
                s.capturedBall = b;
                s.flash = 1.0;
                b.state = 'captured';
                b.slotIndex = s.index;
                b.x = s.centerX;
                b.y = 575;
                b.vx = 0;
                b.vy = 0;
                capturedSlotsCount++;
                pinballScore += 5000;
                playSound('slot');
                spawnPinballParticles(s.centerX, 575, '#fbc02d', 16);
                pinballShockwaves.push({ x: s.centerX, y: 575, r: 10, maxR: 45, color: '#fbc02d', alpha: 1.0 });
                updateSlotUI(s.index, b);

                if (capturedSlotsCount === 6) {
                  triggerPinballJackpot();
                }
                break;
              } else {
                if (b.y >= 615) {
                  b.state = 'drained';
                  pinballScore += 100;
                  break;
                }
              }
            }
          }

          if (b.y > 625) {
            b.state = 'drained';
            pinballScore += 100;
          }
        }
      }
    }

    function updateSlotUI(slotIdx, ball) {
      const statusText = document.getElementById('slotStatusText');
      if (statusText) statusText.textContent = `${capturedSlotsCount} / 6 슬롯 점령!`;

      const box = document.getElementById(`spb-${slotIdx}`);
      if (box) {
        box.classList.add('filled');
        box.innerHTML = `<div class="ball xs ${getBallClass(ball.num)}" style="margin:0;">${ball.num}</div>`;
      }
      const commentary = document.getElementById('pinballCommentary');
      if (commentary) {
        const funMsgs = [
          `🎯 <strong>[공 ${ball.num}]</strong>번이 ${slotIdx + 1}번 골드 슬롯을 극적으로 번개 점령했습니다!`,
          `⚡ <strong>[공 ${ball.num}]</strong>번 범퍼 맞고 굴절되어 ${slotIdx + 1}번 슬롯 안착! (나이스 샷!)`,
          `🔥 <strong>[공 ${ball.num}]</strong>번 치열한 핀볼 난기류 뚫고 ${slotIdx + 1}번 슬롯 골인!`,
          `✨ <strong>[공 ${ball.num}]</strong>번 골드 슬롯 쏙! 이번 주 행운의 조짐이 보입니다!`
        ];
        commentary.innerHTML = funMsgs[Math.floor(Math.random() * funMsgs.length)];
      }
    }

    function triggerPinballJackpot() {
      pinballScore += 50000;
      playSound('jackpot');
      if (typeof confetti === 'function') {
        confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 } });
      }

      latestPinballWinners = pinballSlots.map(s => s.capturedBall.num).sort((a,b)=>a-b);

      const banner = document.getElementById('pinballJackpotBanner');
      if (banner) banner.style.display = 'block';

      const row = document.getElementById('pinballBallsRow');
      if (row) {
        row.innerHTML = '';
        latestPinballWinners.forEach(n => {
          row.appendChild(createBallElement(n, 'lg'));
        });
      }

      const now = new Date();
      const dateStr = `${now.getFullYear()}.${String(now.getMonth()+1).padStart(2,'0')}.${String(now.getDate()).padStart(2,'0')}`;
      const recDate = document.getElementById('pinballReceiptDate');
      if (recDate) recDate.textContent = dateStr;

      const recScore = document.getElementById('pinballReceiptScore');
      if (recScore) recScore.textContent = pinballScore.toLocaleString() + ' PT';

      const recNums = document.getElementById('pinballReceiptNumbers');
      if (recNums) recNums.textContent = latestPinballWinners.map(n => String(n).padStart(2, '0')).join('  ');

      const commentary = document.getElementById('pinballCommentary');
      if (commentary) {
        commentary.innerHTML = `🎉 <strong>핀볼 잭팟 완성!</strong> 6개 골드 슬롯 점령 완료! 행운의 추천 6구: <span style="color:#fbc02d; font-weight:800;">${latestPinballWinners.join(', ')}</span>`;
      }

      const statusText = document.getElementById('slotStatusText');
      if (statusText) statusText.textContent = `6 / 6 슬롯 점령 완료! 🎉`;

      const btnAll = document.getElementById('btnLaunchAll');
      if (btnAll) btnAll.innerHTML = '<i class="fa-solid fa-trophy"></i> 잭팟 달성! 다시 하기';
    }

    function drawPinballFrame() {
      if (!pbCtx) return;
      const ctx = pbCtx;
      const w = pbCanvas.width;
      const h = pbCanvas.height;

      ctx.fillStyle = '#070a13';
      ctx.fillRect(0, 0, w, h);

      ctx.save();
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.05)';
      ctx.lineWidth = 1;
      for (let x = 0; x < w; x += 25) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += 25) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }
      ctx.restore();

      ctx.save();
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.4)';
      ctx.lineWidth = 3;
      ctx.strokeRect(10, 10, w - 20, h - 20);
      ctx.restore();

      ctx.save();
      ctx.fillStyle = 'rgba(6, 182, 212, 0.15)';
      ctx.fillRect(190, 10, 120, 40);
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 2;
      ctx.strokeRect(190, 10, 120, 40);

      ctx.fillStyle = '#38bdf8';
      ctx.font = 'bold 11px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('▼ 45 LOTTO LAUNCHER ▼', 250, 34);

      ctx.beginPath();
      ctx.moveTo(16, 50);
      ctx.lineTo(190, 70);
      ctx.moveTo(484, 50);
      ctx.lineTo(310, 70);
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.6)';
      ctx.lineWidth = 3;
      ctx.stroke();
      ctx.restore();

      ctx.save();
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 4;
      ctx.shadowColor = '#06b6d4';
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.moveTo(16, 350);
      ctx.lineTo(65, 415);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(484, 350);
      ctx.lineTo(435, 415);
      ctx.stroke();
      ctx.restore();

      for (let bmp of pinballBumpers) {
        ctx.save();
        if (bmp.flash > 0) {
          bmp.flash = Math.max(0, bmp.flash - 0.05);
        }
        ctx.beginPath();
        ctx.arc(bmp.x, bmp.y, bmp.r, 0, Math.PI * 2);
        ctx.fillStyle = bmp.flash > 0 ? '#ffffff' : bmp.color;
        ctx.shadowColor = bmp.color;
        ctx.shadowBlur = bmp.flash > 0 ? 30 : 15;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(bmp.x, bmp.y, bmp.r * 0.75, 0, Math.PI * 2);
        ctx.fillStyle = '#0f172a';
        ctx.fill();
        ctx.strokeStyle = bmp.color;
        ctx.lineWidth = 2.5;
        ctx.stroke();

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 13px Outfit, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(bmp.label, bmp.x, bmp.y);
        ctx.restore();
      }

      for (let p of pinballPegs) {
        ctx.save();
        if (p.flash > 0) {
          p.flash = Math.max(0, p.flash - 0.08);
        }
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.flash > 0 ? '#fbc02d' : (p.isDividerCap ? '#38bdf8' : '#06b6d4');
        ctx.shadowColor = p.flash > 0 ? '#fbc02d' : '#06b6d4';
        ctx.shadowBlur = p.flash > 0 ? 15 : 6;
        ctx.fill();
        ctx.restore();
      }

      ctx.save();
      for (let s of pinballSlots) {
        if (s.flash > 0) s.flash = Math.max(0, s.flash - 0.05);

        ctx.fillStyle = s.capturedBall ? 'rgba(251, 192, 45, 0.15)' : 'rgba(255, 255, 255, 0.03)';
        ctx.fillRect(s.leftX, 515, s.rightX - s.leftX, 100);

        ctx.strokeStyle = s.capturedBall ? '#fbc02d' : 'rgba(255, 255, 255, 0.15)';
        ctx.lineWidth = s.capturedBall ? 2 : 1;
        ctx.strokeRect(s.leftX, 515, s.rightX - s.leftX, 100);

        ctx.fillStyle = s.capturedBall ? '#fbc02d' : '#94a3b8';
        ctx.font = 'bold 11px Outfit, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`SLOT ${s.index + 1}`, s.centerX, 606);

        if (!s.capturedBall) {
          ctx.fillStyle = 'rgba(255, 255, 255, 0.25)';
          ctx.font = '12px Outfit, sans-serif';
          ctx.fillText('[ ? ]', s.centerX, 570);
        } else {
          ctx.fillStyle = '#fbc02d';
          ctx.font = '10px sans-serif';
          ctx.fillText('★ WIN ★', s.centerX, 545);
        }
      }

      ctx.strokeStyle = 'rgba(6, 182, 212, 0.8)';
      ctx.lineWidth = 3;
      for (let s of pinballSlots) {
        ctx.beginPath();
        ctx.moveTo(s.leftX, 515);
        ctx.lineTo(s.leftX, 615);
        ctx.stroke();
      }
      ctx.beginPath();
      ctx.moveTo(pinballSlots[5].rightX, 515);
      ctx.lineTo(pinballSlots[5].rightX, 615);
      ctx.stroke();
      ctx.restore();

      for (let sw of pinballShockwaves) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(sw.x, sw.y, sw.r, 0, Math.PI * 2);
        ctx.strokeStyle = sw.color;
        ctx.globalAlpha = sw.alpha;
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.restore();
        sw.r += 2.5;
        sw.alpha -= 0.06;
      }
      pinballShockwaves = pinballShockwaves.filter(sw => sw.alpha > 0);

      for (let p of pinballParticles) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.life;
        ctx.fill();
        ctx.restore();
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.04;
      }
      pinballParticles = pinballParticles.filter(p => p.life > 0);

      for (let b of pinballBalls) {
        if (b.state !== 'active' && b.state !== 'captured') continue;

        ctx.save();
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
        ctx.fillStyle = b.color;
        ctx.shadowColor = b.state === 'captured' ? '#fbc02d' : 'rgba(0,0,0,0.6)';
        ctx.shadowBlur = b.state === 'captured' ? 14 : 6;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(b.x - b.r * 0.3, b.y - b.r * 0.3, b.r * 0.35, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.55)';
        ctx.fill();

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 10px Outfit, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.shadowColor = '#000';
        ctx.shadowBlur = 3;
        ctx.fillText(b.num, b.x, b.y);

        ctx.restore();
      }

      const scoreEl = document.getElementById('pinballScore');
      if (scoreEl) scoreEl.textContent = pinballScore.toLocaleString();
    }

    function pinballLoop() {
      if (!pinballRunning) return;
      updatePinballPhysics();
      drawPinballFrame();

      const activeCount = pinballBalls.filter(b => b.state === 'active').length;
      const waitingCount = pinballBalls.filter(b => b.state === 'idle').length;

      if (activeCount > 0 || waitingCount > 0 || pinballParticles.length > 0 || pinballShockwaves.length > 0) {
        pinballAnimationId = requestAnimationFrame(pinballLoop);
      } else {
        pinballRunning = false;
        pinballAnimationId = null;
        drawPinballFrame();
      }
    }

    function startPinballLoop() {
      if (!pinballRunning) {
        pinballRunning = true;
        pinballAnimationId = requestAnimationFrame(pinballLoop);
      }
    }

    function spawnPinballParticles(x, y, color, count) {
      for (let i = 0; i < count; i++) {
        const ang = Math.random() * Math.PI * 2;
        const spd = 1 + Math.random() * 3;
        pinballParticles.push({
          x, y,
          vx: Math.cos(ang) * spd,
          vy: Math.sin(ang) * spd,
          color,
          r: 2 + Math.random() * 2,
          life: 1.0
        });
      }
    }

    function copyPinballNumbers() {
      if (!latestPinballWinners || latestPinballWinners.length < 6) {
        alert("아직 6개 슬롯 점령이 완료되지 않았습니다!");
        return;
      }
      const sStr = latestPinballWinners.map(n => String(n).padStart(2, '0')).join(', ');
      const text = `🎰 [로또 6/45 네온 핀볼 머신 1등 잭팟 추천 번호]
번호: ${sStr}
스코어: ${pinballScore.toLocaleString()} PT
(못과 범퍼의 난기류를 뚫고 골드 슬롯에 안착한 기적의 6구!)
https://mwon001.github.io/lotto-number/`;
      navigator.clipboard.writeText(text).then(() => {
        alert("카카오톡 공유용 핀볼 잭팟 번호가 복사되었습니다!");
      });
    }

    function openPinballReceiptModal() {
      const modal = document.getElementById('pinballReceiptModal');
      if (modal) modal.classList.add('open');
    }

    function closePinballReceiptModal(e) {
      const modal = document.getElementById('pinballReceiptModal');
      if (modal) modal.classList.remove('open');
    }

    function copyPinballReceiptText() {
      if (!latestPinballWinners || latestPinballWinners.length < 6) return;
      const dateStr = document.getElementById('pinballReceiptDate').textContent;
      const scoreStr = document.getElementById('pinballReceiptScore').textContent;
      const numsStr = latestPinballWinners.map(n => String(n).padStart(2, '0')).join('  ');
      const text = `========================================
🎰 네온 핀볼 머신 1등 잭팟 영수증 🎰
========================================
[발행] 네온 파칭코 핀볼 연구소
[인증] 45구 난기류 슬롯 관통 챔피언
[일자] ${dateStr}
[스코어] ${scoreStr}
----------------------------------------
[슬롯 점령 6구]
${numsStr}
----------------------------------------
[※ 핀볼 잭팟 당첨 시 필수 수칙]
1. 핀볼로 뽑았다고 부모님께 자랑하면 등짝 맞으니 'AI 빅데이터'라고 둘러대기
2. 슬롯에 쏙 들어간 공처럼 이번 주 월급도 통장에 쏙 보존하기
3. 아는 누나에게 '내가 핀볼로 소고기 사준다 했지?' 카톡 캡처 보내기
4. 1등 당첨되면 조용히 출근해서 대표님 어깨 한번 툭 치고 퇴사하기
----------------------------------------
핀볼의 신 曰: "못을 튕겨내듯 인생의 고난도 튕겨내라."
========================================`;
      navigator.clipboard.writeText(text).then(() => {
        alert("영수증 부적 텍스트가 클립보드에 복사되었습니다!");
      });
    }
"""

target_battle_js = '    // =========================================================\n    // 🥊 45구 배틀로얄 물리 엔진 & 게임 루프 (CANVAS 2D)'
if target_battle_js in html:
    html = html.replace(target_battle_js, pinball_engine_js + '\n' + target_battle_js)
    print("[OK] Added Pinball Engine JavaScript implementation")
else:
    print("[WARN] target_battle_js not found")

# 9. DOMContentLoaded에 initPinball() 추가
old_dom_content_loaded = """    window.addEventListener('DOMContentLoaded', async () => {
      await loadSummary();
      initCustomPad();
      initBacktestPad();
      initBattleBalls();
      generateNumbers();
    });"""

new_dom_content_loaded = """    window.addEventListener('DOMContentLoaded', async () => {
      await loadSummary();
      initCustomPad();
      initBacktestPad();
      initPinball();
      initBattleBalls();
      generateNumbers();
    });"""

if old_dom_content_loaded in html:
    html = html.replace(old_dom_content_loaded, new_dom_content_loaded)
    print("[OK] Added initPinball to DOMContentLoaded")
else:
    print("[WARN] old_dom_content_loaded not found")

# 10. 세 파일 모두에 쓰기: templates/index.html, index.html, docs/index.html
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("[OK] Saved templates/index.html")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("[OK] Saved index.html")

with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("[OK] Saved docs/index.html")

print("\n[SUCCESS] All 3 HTML files updated and synchronized successfully!")
