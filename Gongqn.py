# -*- coding: utf-8 -*-
"""Gongqn 실시간 방송 후원 시스템 (Replit 최적화 버전)
- 프레임워크: Flask
- 인증 방식: 브라우저 쿠키 인증 (새로고침 문제 완벽 해결)
- 관리자 접속 주소: /admin_gongqn
"""

from flask import Flask, request, render_template_string, jsonify, redirect, url_for, make_response
import sqlite3
from datetime import datetime
import threading
import time
import json
import os
import sys
import logging

try:
    import websocket
except ImportError:
    print("⚠️ 'websocket-client' 라이브러리가 필요합니다.")
    print("👉 Replit 쉘(Shell) 탭에서 'pip install websocket-client'를 입력하세요.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("GongqnDonation")

app = Flask(__name__)

# ==========================================
# ⚙️ 시스템 설정 
# ==========================================
# Replit은 파일이 영구 보존되므로 현재 폴더에 바로 생성
DB_NAME = "donations_secure.db"

# 🛑 Pushbullet 토큰을 여기에 직접 넣으세요 (리플릿 Secrets 기능을 써도 됩니다)
PUSHBULLET_API_KEY = os.environ.get("PUSHBULLET_API_KEY", "o.P9LtMvpDoNgYXOLogbiPsuIvZc95P2nY")

# 관리자 페이지 비밀번호
ADMIN_PASSWORD = "zizer731!!"

# ==========================================
# 🗄️ 데이터베이스 모델
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount INTEGER NOT NULL,
            message TEXT,
            status TEXT DEFAULT '대기중',
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("💾 데이터베이스 초기화 완료.")

# ==========================================
# 🎨 프론트엔드 HTML / CSS / JS 템플릿
# ==========================================

# 1. 메인 홈페이지 (Gongqn 방송 후원)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gongqn 방송 후원하기</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Pretendard:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Pretendard', sans-serif; background: radial-gradient(circle at 50% 50%, #151528 0%, #080811 100%); min-height: 100vh; color: #ffffff; overflow-x: hidden; }
        .neon-text { font-family: 'Orbitron', sans-serif; text-shadow: 0 0 10px rgba(0, 255, 204, 0.8), 0 0 20px rgba(0, 255, 204, 0.4); }
        .neon-border { box-shadow: 0 0 15px rgba(0, 255, 204, 0.2); border: 1px solid rgba(0, 255, 204, 0.3); background: rgba(30, 30, 50, 0.6); backdrop-filter: blur(10px); }
        .fade-in { animation: fadeIn 0.8s ease-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        #toast {
            visibility: hidden; min-width: 280px; background-color: #00ffcc; color: #080811; text-align: center; border-radius: 8px; padding: 14px; position: fixed; z-index: 50; left: 50%; bottom: 30px; transform: translateX(-50%); font-weight: bold; box-shadow: 0 5px 20px rgba(0, 255, 204, 0.5); transition: visibility 0s, opacity 0.3s ease-in-out; opacity: 0;
        }
        #toast.show { visibility: visible; opacity: 1; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 mt-4 md:mt-10">

        <div class="lg:col-span-5 flex flex-col gap-6 fade-in">
            <div class="text-center md:text-left mb-2">
                <h1 class="text-3xl md:text-4xl font-extrabold tracking-tight neon-text mb-2">GONGQN LIVE</h1>
                <p class="text-gray-400 text-sm md:text-base">Gongqn 채널에 후원하고 소중한 메시지를 남겨보세요!</p>
            </div>

            <div onclick="copyAccount()" class="neon-border rounded-2xl p-6 cursor-pointer hover:scale-[1.02] transition-all duration-300 relative group overflow-hidden">
                <div class="absolute -right-10 -top-10 w-32 h-32 bg-cyan-500 opacity-10 rounded-full group-hover:scale-150 transition-all duration-500"></div>
                <div class="flex justify-between items-start mb-3">
                    <span class="text-xs bg-cyan-500/20 text-cyan-400 px-3 py-1 rounded-full font-bold">계좌번호 터치 시 자동 복사</span>
                    <svg class="w-5 h-5 text-cyan-400 group-hover:animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
                </div>
                <p class="text-gray-400 text-xs mb-1">입금 은행</p>
                <h3 class="text-xl font-bold mb-2">🏦 토스뱅크 (Toss Bank)</h3>
                <div class="text-2xl font-black text-cyan-400 tracking-wider font-mono select-all">1001-5289-9617</div>
                <p class="text-gray-500 text-xs mt-2">예금주: ㄱㅇㅈ | 기부 신청 후 이 계좌로 입금해주세요!</p>
            </div>

            <div class="neon-border rounded-2xl p-6 md:p-8">
                <h2 class="text-xl font-bold mb-6 text-cyan-400 border-b border-cyan-500/20 pb-2">✏️ 후원 정보 입력</h2>
                <form action="/ready" method="POST" class="space-y-5" onsubmit="return validateForm()">
                    <div>
                        <label class="block text-gray-400 text-xs mb-2">예금주명 (송금하시는 실명)</label>
                        <input type="text" name="name" id="donor_name" required class="w-full bg-[#1b1b30] border border-gray-700 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 rounded-lg p-3 text-white placeholder-gray-500 transition outline-none" placeholder="실제 돈을 보내시는 성함을 입력하세요.">
                    </div>
                    <div>
                        <label class="block text-gray-400 text-xs mb-2">후원 금액 (원)</label>
                        <input type="number" name="amount" id="donor_amount" required min="100" class="w-full bg-[#1b1b30] border border-gray-700 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 rounded-lg p-3 text-white placeholder-gray-500 transition outline-none font-mono" placeholder="최소 100원 이상 입력">
                    </div>
                    <div>
                        <label class="block text-gray-400 text-xs mb-2">응원 메시지</label>
                        <textarea name="message" id="donor_message" required rows="3" maxlength="150" class="w-full bg-[#1b1b30] border border-gray-700 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 rounded-lg p-3 text-white placeholder-gray-500 transition outline-none resize-none" placeholder="방송 화면에 띄울 응원 메시지를 작성해보세요! (최대 150자)"></textarea>
                    </div>
                    <button type="submit" class="w-full bg-gradient-to-r from-cyan-400 to-blue-500 text-gray-900 font-extrabold py-4 px-6 rounded-lg hover:from-cyan-300 hover:to-blue-400 hover:shadow-[0_0_20px_rgba(0,255,204,0.4)] transition-all duration-300 transform active:scale-95">다음 단계 (계좌 전송 및 대기) 🚀</button>
                </form>
            </div>
        </div>

        <div class="lg:col-span-7 flex flex-col gap-8 fade-in" style="animation-delay: 0.3s;">
            <div class="neon-border rounded-2xl p-6 md:p-8 flex-1">
                <div class="flex justify-between items-center mb-6 border-b border-cyan-500/20 pb-3">
                    <h2 class="text-xl font-bold text-yellow-400 flex items-center gap-2"><span>🏆 명예의 전당 (역대 기부왕)</span></h2>
                    <span class="text-xs text-gray-400">실시간 누적 집계</span>
                </div>
                <div class="space-y-4">
                    {% for rank in rankings %}
                    <div class="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition duration-300 border border-white/5">
                        <div class="flex items-center gap-4">
                            <div class="w-8 h-8 rounded-full flex items-center justify-center font-black text-sm {% if loop.index == 1 %} bg-yellow-400 text-gray-900 shadow-[0_0_10px_rgba(250,204,21,0.5)] {% elif loop.index == 2 %} bg-slate-300 text-gray-900 {% elif loop.index == 3 %} bg-amber-600 text-white {% else %} bg-gray-700 text-gray-300 {% endif %}">{{ loop.index }}</div>
                            <span class="font-bold text-base md:text-lg">{{ rank['name'] }}</span>
                        </div>
                        <div class="text-right">
                            <span class="text-cyan-400 font-extrabold font-mono text-base md:text-lg">{{ "{:,}".format(rank['total_amount']) }}</span><span class="text-xs text-gray-400 ml-1">원</span>
                        </div>
                    </div>
                    {% else %}
                    <div class="text-center py-10 text-gray-500">아직 명예의 전당에 등록된 후원자가 없습니다.<br>첫 기부왕의 주인공이 되어보세요! 🎉</div>
                    {% endfor %}
                </div>
            </div>

            <div class="neon-border rounded-2xl p-6 md:p-8 flex-1">
                <div class="flex justify-between items-center mb-6 border-b border-cyan-500/20 pb-3">
                    <h2 class="text-xl font-bold text-cyan-400 flex items-center gap-2"><span class="animate-pulse">💬 실시간 후원 한마디</span></h2>
                    <span class="text-xs text-gray-400">최신 5개 내역</span>
                </div>
                <div class="space-y-4">
                    {% for feed in recent_feeds %}
                    <div class="p-4 rounded-xl bg-[#1b1b30]/60 border-l-4 border-cyan-400">
                        <div class="flex justify-between items-center mb-1">
                            <span class="font-bold text-cyan-300 text-sm">{{ feed['name'] }} 님</span>
                            <span class="text-xs text-gray-500">{{ feed['timestamp'].split(' ')[1] }}</span>
                        </div>
                        <p class="text-white text-sm my-1 break-all">{{ feed['message'] }}</p>
                        <div class="text-right text-xs font-mono text-yellow-400/80 font-bold">후원금액: {{ "{:,}".format(feed['amount']) }}원</div>
                    </div>
                    {% else %}
                    <div class="text-center py-10 text-gray-500">아직 활성화된 후원 메시지가 없습니다.<br>따뜻한 한마디를 방송 화면에 띄워보세요! 😊</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    <div id="toast">📋 계좌번호가 복사되었습니다! 편리하게 송금하세요.</div>
    <script>
        function copyAccount() {
            const accountText = "토스뱅크 1001-5289-9617";
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(accountText).then(() => showToast()).catch(err => fallbackCopy(accountText));
            } else { fallbackCopy(accountText); }
        }
        function fallbackCopy(text) {
            const textArea = document.createElement("textarea");
            textArea.value = text; textArea.style.position = "fixed";
            document.body.appendChild(textArea); textArea.focus(); textArea.select();
            try { document.execCommand('copy'); showToast(); } catch (err) { alert("계좌 복사에 실패했습니다. 직접 입력해주세요: " + text); }
            document.body.removeChild(textArea);
        }
        function showToast() {
            const toast = document.getElementById("toast");
            toast.className = "show"; setTimeout(() => { toast.className = toast.className.replace("show", ""); }, 2500);
        }
        function validateForm() {
            const name = document.getElementById("donor_name").value.trim();
            const amount = parseInt(document.getElementById("donor_amount").value);
            const message = document.getElementById("donor_message").value.trim();
            if (name.length < 1) { alert("보내시는 분의 성함을 정확히 적어주세요!"); return false; }
            if (isNaN(amount) || amount < 100) { alert("최소 후원 금액은 100원 이상입니다!"); return false; }
            if (message.length < 1) { alert("응원 메시지를 남겨주세요!"); return false; }
            return true;
        }
    </script>
</body>
</html>
"""

# 2. 입금 대기 및 완료 애니메이션 화면
PAYMENT_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>입금 확인 대기중...</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Pretendard:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Pretendard', sans-serif; background: #0b0b16; color: #ffffff; min-height: 100vh; display: flex; justify-content: center; align-items: center; overflow: hidden; position: relative; }
        .glass-box { background: rgba(25, 25, 45, 0.8); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 15px 35px rgba(0,0,0,0.4); }
        .neon-glow { box-shadow: 0 0 25px rgba(0, 255, 204, 0.3); border: 1px solid rgba(0, 255, 204, 0.5); }
        .spinner { border: 4px solid rgba(255, 255, 255, 0.1); width: 70px; height: 70px; border-radius: 50%; border-left-color: #00ffcc; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #celebration-overlay { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(10, 10, 25, 0.95); z-index: 100; justify-content: center; align-items: center; flex-direction: column; }
        #confetti-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 101; }
    </style>
</head>
<body>
    <div class="glass-box rounded-2xl p-8 max-w-md w-full mx-4 text-center relative z-10">
        <div class="flex justify-center mb-6"><div class="spinner"></div></div>
        <h1 class="text-2xl font-black text-yellow-400 mb-2">⏳ 실시간 입금 대기 중</h1>
        <p class="text-gray-300 text-sm mb-6"><span class="font-bold text-cyan-300">{{ name }}</span>님, 입금 대기 시스템이 작동하고 있습니다.</p>
        <div class="bg-[#1b1b30] rounded-xl p-5 mb-6 text-left border border-white/5 space-y-3">
            <div class="flex justify-between items-center text-xs text-gray-400"><span>보내실 은행</span><span class="font-bold text-white">토스뱅크 (예금주: ㄱㅇㅈ)</span></div>
            <div class="flex justify-between items-center text-xs text-gray-400"><span>계좌 번호</span><span class="font-bold text-cyan-400 font-mono text-sm select-all">1001-5289-9617</span></div>
            <hr class="border-white/5">
            <div class="flex justify-between items-center"><span class="text-sm text-gray-300 font-bold">정확한 송금액</span><span class="text-xl font-extrabold text-yellow-400 font-mono">{{ "{:,}".format(amount) }} 원</span></div>
        </div>
        <div class="text-xs text-rose-400 leading-relaxed font-semibold bg-rose-500/10 p-3 rounded-lg border border-rose-500/20">
            ⚠️ 반드시 입력하신 [예금주명: {{ name }}]과 [정확한 금액: {{ amount }}원]을 일치시켜 이체하셔야 1초 만에 자동 확인 처리됩니다!
        </div>
        <button onclick="location.href='/'" class="mt-6 text-sm text-gray-400 hover:text-white transition duration-200">← 정보 재입력 및 메인으로</button>
    </div>

    <div id="celebration-overlay">
        <canvas id="confetti-canvas"></canvas>
        <div class="text-center p-8 max-w-lg relative z-[102] space-y-6">
            <div class="neon-glow bg-[#101026] p-8 md:p-12 rounded-3xl transform scale-95">
                <div class="w-20 h-20 bg-cyan-500/20 text-cyan-400 rounded-full flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(0,255,204,0.3)]">
                    <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
                </div>
                <h2 class="text-3xl md:text-4xl font-black text-cyan-400 tracking-tight mb-2">🎉 입금 확인 완료!</h2>
                <p class="text-gray-300 text-lg mb-6"><span class="font-bold text-yellow-300">{{ name }}</span>님의 기부가 성공적으로 승인되었습니다.</p>
                <div class="bg-cyan-500/10 rounded-2xl p-4 border border-cyan-500/20 mb-6">
                    <p class="text-xs text-gray-400 mb-1">보내주신 소중한 후원금</p>
                    <span class="text-2xl font-black text-white font-mono">{{ "{:,}".format(amount) }}원</span>
                </div>
                <p class="text-xs text-cyan-400/80 animate-pulse font-bold">5초 후 메인으로 돌아갑니다...</p>
            </div>
        </div>
    </div>
    <script>
        const donationId = "{{ donation_id }}";
        function checkDonationStatus() {
            fetch(`/api/status/${donationId}`)
                .then(r => r.json())
                .then(data => { if (data.status === '완료') { triggerCelebration(); } else { setTimeout(checkDonationStatus, 2000); } })
                .catch(err => setTimeout(checkDonationStatus, 3000));
        }
        function triggerCelebration() {
            document.getElementById("celebration-overlay").style.display = "flex";
            startConfetti();
            setTimeout(() => { window.location.href = "/"; }, 5000);
        }
        function startConfetti() {
            const canvas = document.getElementById("confetti-canvas");
            const ctx = canvas.getContext("2d");
            canvas.width = window.innerWidth; canvas.height = window.innerHeight;
            const colors = ["#00ffcc", "#ff007f", "#ffcc00", "#3b82f6", "#10b981", "#ffffff"];
            const particles = [];
            class Particle {
                constructor() {
                    this.x = Math.random() * canvas.width; this.y = Math.random() * canvas.height - canvas.height;
                    this.size = Math.random() * 8 + 6; this.color = colors[Math.floor(Math.random() * colors.length)];
                    this.speedX = Math.random() * 3 - 1.5; this.speedY = Math.random() * 4 + 4;
                    this.rotation = Math.random() * 360; this.rotationSpeed = Math.random() * 4 - 2;
                }
                update() { this.x += this.speedX; this.y += this.speedY; this.rotation += this.rotationSpeed; if (this.y > canvas.height) { this.y = -20; this.x = Math.random() * canvas.width; } }
                draw() { ctx.save(); ctx.translate(this.x, this.y); ctx.rotate((this.rotation * Math.PI) / 180); ctx.fillStyle = this.color; ctx.fillRect(-this.size/2, -this.size/2, this.size, this.size); ctx.restore(); }
            }
            for (let i = 0; i < 150; i++) particles.push(new Particle());
            function animate() { ctx.clearRect(0, 0, canvas.width, canvas.height); particles.forEach(p => { p.update(); p.draw(); }); requestAnimationFrame(animate); }
            animate();
            window.addEventListener('resize', () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; });
        }
        window.onload = checkDonationStatus;
    </script>
</body>
</html>
"""

# 3. Gongqn 전용 대시보드 (새로고침 문제 해결 및 자동 갱신 적용)
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gongqn 관리자 관제 패널</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Pretendard:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Pretendard', sans-serif; background-color: #0b0b16; color: #ffffff; min-height: 100vh; }
        .admin-glow { border: 1px solid rgba(239, 68, 68, 0.3); box-shadow: 0 0 20px rgba(239, 68, 68, 0.1); background: rgba(30, 20, 30, 0.6); backdrop-filter: blur(10px); }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto">
        <div class="flex flex-col md:flex-row justify-between items-center mb-8 border-b border-red-500/20 pb-4">
            <div class="text-center md:text-left mb-4 md:mb-0">
                <h1 class="text-3xl font-black text-red-500 font-mono tracking-wider flex items-center gap-3 justify-center md:justify-start">
                    <span>👑 GONGQN ADMIN CONSOLE</span>
                </h1>
                <p class="text-gray-400 text-xs mt-1">실시간 데이터 스트리밍 감지 및 원격 제어 (10초마다 자동 갱신 중...)</p>
            </div>
            <div class="flex gap-4">
                <button onclick="location.reload()" class="bg-gray-800 text-gray-300 font-bold py-2 px-4 rounded-lg hover:bg-gray-700 hover:text-white transition">🔄 수동 새로고침</button>
                <a href="/" class="bg-red-900/50 text-red-300 font-bold py-2 px-4 rounded-lg border border-red-500/30 hover:bg-red-800 transition">← 사이트로 가기</a>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="admin-glow rounded-xl p-6 flex flex-col justify-between">
                <span class="text-xs text-gray-400 font-bold uppercase tracking-wider">💰 누적 승인 금액</span>
                <div class="flex items-baseline gap-1 mt-2">
                    <span class="text-3xl font-extrabold text-cyan-400 font-mono">{{ "{:,}".format(stats['total_success_amount']) }}</span>
                    <span class="text-xs text-gray-400">원</span>
                </div>
            </div>
            <div class="admin-glow rounded-xl p-6 flex flex-col justify-between">
                <span class="text-xs text-gray-400 font-bold uppercase tracking-wider">📊 완료 / 전체 건수</span>
                <div class="flex items-baseline gap-1 mt-2">
                    <span class="text-3xl font-extrabold text-yellow-400 font-mono">{{ stats['success_count'] }}</span>
                    <span class="text-lg text-gray-500">/</span>
                    <span class="text-xl font-bold text-gray-400 font-mono">{{ stats['total_count'] }}</span>
                    <span class="text-xs text-gray-400 ml-1">건</span>
                </div>
            </div>
            <div class="admin-glow rounded-xl p-6 flex flex-col justify-between">
                <span class="text-xs text-gray-400 font-bold uppercase tracking-wider">⏳ 실시간 입금 확인 대기중</span>
                <div class="flex items-baseline gap-1 mt-2">
                    <span class="text-3xl font-extrabold text-rose-500 font-mono">{{ stats['pending_count'] }}</span>
                    <span class="text-xs text-gray-400">건</span>
                </div>
            </div>
        </div>

        <div class="admin-glow rounded-2xl overflow-hidden">
            <div class="p-6 border-b border-red-500/10 flex justify-between items-center">
                <h2 class="text-lg font-bold text-red-400">🗂️ 실시간 수동 컨트롤 타워</h2>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-red-500/5 text-gray-400 text-xs border-b border-red-500/10">
                            <th class="p-4 text-center">ID</th>
                            <th class="p-4">시간</th>
                            <th class="p-4">신청자명</th>
                            <th class="p-4">신청액</th>
                            <th class="p-4">메시지</th>
                            <th class="p-4 text-center">상태</th>
                            <th class="p-4 text-center">제어</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-white/5 text-sm">
                        {% for d in donations %}
                        <tr id="row-{{ d['id'] }}" class="hover:bg-white/5 transition duration-150">
                            <td class="p-4 text-center text-gray-500 font-mono">{{ d['id'] }}</td>
                            <td class="p-4 text-gray-400 text-xs">{{ d['timestamp'] }}</td>
                            <td class="p-4 font-bold text-white">{{ d['name'] }}</td>
                            <td class="p-4 font-mono text-cyan-400 font-extrabold">{{ "{:,}".format(d['amount']) }} 원</td>
                            <td class="p-4 text-gray-300">{{ d['message'] }}</td>
                            <td class="p-4 text-center">
                                {% if d['status'] == '완료' %}
                                <span class="bg-cyan-500/20 text-cyan-400 py-1 px-3 rounded-full text-xs font-black">승인완료</span>
                                {% else %}
                                <span class="bg-yellow-500/20 text-yellow-400 py-1 px-3 rounded-full text-xs font-black">대기중</span>
                                {% endif %}
                            </td>
                            <td class="p-4 text-center">
                                <div class="flex justify-center gap-2">
                                    {% if d['status'] == '대기중' %}
                                    <button onclick="approveDonation({{ d['id'] }})" class="bg-cyan-500 text-gray-900 font-bold px-3 py-1 rounded text-xs hover:bg-cyan-400 transition">승인</button>
                                    {% endif %}
                                    <button onclick="deleteDonation({{ d['id'] }})" class="bg-rose-600 text-white font-bold px-3 py-1 rounded text-xs hover:bg-rose-500 transition">삭제</button>
                                </div>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="7" class="text-center py-20 text-gray-500 font-semibold">기록이 없습니다.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // 새로고침 방해 없이 10초마다 자동 갱신
        setInterval(() => {
            window.location.reload();
        }, 10000);

        function approveDonation(id) {
            if (!confirm("해당 내역을 수동으로 승인하시겠습니까?")) return;
            fetch(`/api/admin/approve/${id}`, { method: "POST" })
            .then(res => res.json())
            .then(data => { if (data.status === "success") location.reload(); })
            .catch(err => alert("네트워크 오류"));
        }

        function deleteDonation(id) {
            if (!confirm("완전히 영구 삭제하시겠습니까?")) return;
            fetch(`/api/admin/delete/${id}`, { method: "POST" })
            .then(res => res.json())
            .then(data => { if (data.status === "success") location.reload(); })
            .catch(err => alert("네트워크 오류"));
        }
    </script>
</body>
</html>
"""

# 4. 로그인 폼
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>관리자 콘솔 인증</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body { background: #080811; color: #fff; display: flex; align-items: center; justify-content: center; min-height: 100vh; } .glow { border: 1px solid rgba(239, 68, 68, 0.4); box-shadow: 0 0 25px rgba(239, 68, 68, 0.2); }</style>
</head>
<body class="p-4">
    <div class="glow bg-[#151528] rounded-2xl p-8 max-w-sm w-full">
        <div class="text-center mb-6">
            <span class="text-4xl">🔑</span>
            <h1 class="text-xl font-black mt-2 text-red-500 font-mono tracking-wider">GONGQN ADMIN</h1>
            <p class="text-gray-400 text-xs mt-1">시스템 관리를 위한 보안 패널</p>
        </div>
        <form action="/admin_gongqn" method="POST" class="space-y-4">
            <input type="password" name="password" required class="w-full bg-[#20203a] border border-gray-700 focus:border-red-500 rounded-lg p-3 text-center outline-none transition" placeholder="비밀번호 입력">
            <button type="submit" class="w-full bg-rose-600 hover:bg-rose-500 text-white font-extrabold py-3 px-4 rounded-lg transition-colors">로그인 🛰️</button>
        </form>
        {% if error %}<p class="text-red-400 text-xs text-center mt-3 font-semibold">❌ 패스워드가 잘못되었습니다!</p>{% endif %}
    </div>
</body>
</html>
"""

# ==========================================
# 🛰️ 라우팅 및 뷰 로직
# ==========================================

@app.route('/')
def home():
    conn = get_db_connection()
    rankings = conn.execute("SELECT name, SUM(amount) as total_amount FROM donations WHERE status='완료' GROUP BY name ORDER BY total_amount DESC LIMIT 5").fetchall()
    recent_feeds = conn.execute("SELECT name, amount, message, timestamp FROM donations WHERE status='완료' ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    return render_template_string(INDEX_HTML, rankings=rankings, recent_feeds=recent_feeds)

@app.route('/ready', methods=['POST'])
def ready():
    name = request.form.get('name', '').strip()
    amount_str = request.form.get('amount', '0')
    message = request.form.get('message', '').strip()
    try: amount = int(amount_str)
    except ValueError: amount = 0
    if not name or amount < 100 or not message: return redirect('/')

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO donations (name, amount, message, status, timestamp) VALUES (?, ?, ?, '대기중', ?)", (name, amount, message, timestamp))
    donation_id = c.lastrowid
    conn.commit()
    conn.close()
    return render_template_string(PAYMENT_HTML, donation_id=donation_id, name=name, amount=amount)

@app.route('/api/status/<int:donation_id>')
def api_status(donation_id):
    conn = get_db_connection()
    row = conn.execute("SELECT status FROM donations WHERE id=?", (donation_id,)).fetchone()
    conn.close()
    if row: return jsonify({"status": row['status']})
    return jsonify({"status": "error"}), 404

# 쿠키 기반 인증을 사용하여 무한 새로고침 문제 해결
@app.route('/admin_gongqn', methods=['GET', 'POST'])
def admin():
    # POST로 로그인 시도 시
    if request.method == 'POST':
        if request.form.get('password', '') == ADMIN_PASSWORD:
            resp = make_response(redirect(url_for('admin')))
            resp.set_cookie('admin_auth', 'gongqn_logged_in', max_age=3600)
            return resp
        return render_template_string(LOGIN_HTML, error=True)

    # GET 요청 (일반 접속 및 새로고침)
    if request.cookies.get('admin_auth') == 'gongqn_logged_in':
        conn = get_db_connection()
        donations = conn.execute("SELECT * FROM donations ORDER BY id DESC").fetchall()
        stats = {}
        total_success = conn.execute("SELECT SUM(amount) FROM donations WHERE status='완료'").fetchone()[0]
        stats['total_success_amount'] = total_success if total_success else 0
        stats['total_count'] = conn.execute("SELECT COUNT(*) FROM donations").fetchone()[0]
        stats['success_count'] = conn.execute("SELECT COUNT(*) FROM donations WHERE status='완료'").fetchone()[0]
        stats['pending_count'] = conn.execute("SELECT COUNT(*) FROM donations WHERE status='대기중'").fetchone()[0]
        conn.close()
        return render_template_string(ADMIN_HTML, donations=donations, stats=stats)

    return render_template_string(LOGIN_HTML, error=False)

# API 인증 검사 헬퍼
def is_admin():
    return request.cookies.get('admin_auth') == 'gongqn_logged_in'

@app.route('/api/admin/approve/<int:donation_id>', methods=['POST'])
def api_admin_approve(donation_id):
    if not is_admin(): return jsonify({"status": "fail"}), 403
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE donations SET status='완료' WHERE id=?", (donation_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/admin/delete/<int:donation_id>', methods=['POST'])
def api_admin_delete(donation_id):
    if not is_admin(): return jsonify({"status": "fail"}), 403
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM donations WHERE id=?", (donation_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

# ==========================================
# 🤖 웹소켓 봇 
# ==========================================

def update_db_on_payment(full_text):
    conn = get_db_connection()
    c = conn.cursor()
    pending = c.execute("SELECT id, name, amount FROM donations WHERE status='대기중'").fetchall()

    for row in pending:
        sanitized_text = full_text.replace(',', '')
        if row['name'] in sanitized_text and str(row['amount']) in sanitized_text:
            logger.info(f"🎯 [매칭 성공] 이름: {row['name']}, 금액: {row['amount']}원")
            c.execute("UPDATE donations SET status='완료' WHERE id=?", (row['id'],))
            conn.commit()
    conn.close()

def on_message(ws, message):
    try:
        data = json.loads(message)
        if data.get("type") == "push" and data.get("push", {}).get("type") == "mirror":
            push = data["push"]
            full_text = f"{push.get('title', '')} {push.get('body', '')}"
            if "toss" in push.get("package_name", "").lower() or "토스" in full_text:
                if "입금" in full_text or "원" in full_text:
                    logger.info(f"💰 [알림 수신] {full_text}")
                    update_db_on_payment(full_text)
    except Exception as e:
        pass

def on_error(ws, error): logger.error(f"❌ [에러] {error}")
def on_close(ws, close_status_code, close_msg): time.sleep(5); start_pushbullet_ws()
def on_open(ws): logger.info("🟢 스마트폰 연동 완료!")

def start_pushbullet_ws():
    if not PUSHBULLET_API_KEY or "여기에" in PUSHBULLET_API_KEY: return
    try:
        ws = websocket.WebSocketApp(f"wss://stream.pushbullet.com/websocket/{PUSHBULLET_API_KEY}",
                                    on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.run_forever()
    except: time.sleep(10); start_pushbullet_ws()

def run_bot_thread(): start_pushbullet_ws()

if __name__ == '__main__':
    init_db()
    threading.Thread(target=run_bot_thread, daemon=True).start()

    # Replit 환경에 맞춰 기본 포트 8080 사용 (보통 0.0.0.0 바인딩)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
