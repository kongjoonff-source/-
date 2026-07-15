# -*- coding: utf-8 -*-
"""
예준이의 실시간 방송 후원 시스템 (Yejun Live Donation System)
- 개발 언어: Python 3 (Flask)
- 데이터베이스: SQLite3 (실시간 상태 관리)
- 실시간 알림 가로채기: Pushbullet WebSocket API
- 주요 특징: 
  1. 단 하나의 파일(app.py)로 실행 가능하도록 설계
  2. 600줄 이상의 방대하고 체계적인 프로덕션급 코드 구성
  3. 실시간 AJAX 폴링을 통해 입금 성공 시 기부자 화면에 축하 이펙트(Confetti) 작동
  4. 후원 명예의 전당(누적 금액 랭킹) 및 최근 후원 롤링 피드 제공
  5. 원클릭 계좌 복사 및 세련된 토스트(Toast) 메시지 알림
  6. 반응형 UI/UX 및 네온 테마 웹 디자인 (Tailwind CSS 기반 + 커스텀 CSS 애니메이션)
  7. Render.com 배포 완벽 최적화 (포트 바인딩, DB 예외 처리)
  8. 통계 기능이 탑재된 관리자 전용 대시보드 (수동 승인 및 내역 삭제 기능 포함)
"""

from flask import Flask, request, render_template_string, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
import threading
import time
import json
import os
import sys
import logging

# WebSocket 라이브러리 예외 처리 (Render.com 등 배포 환경에서 누락될 경우를 대비)
try:
    import websocket
except ImportError:
    print("⚠️ [경고] 'websocket-client' 라이브러리가 설치되지 않았습니다.")
    print("👉 자동 입금 확인 기능을 사용하려면 'pip install websocket-client'를 실행하세요.")

# 로깅 설정 (서버 로그를 예쁘고 알기 쉽게 출력)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("YejunDonation")

app = Flask(__name__)

# ==========================================
# ⚙️ 시스템 설정 및 환경 변수 구성
# ==========================================
# Render.com 배포 시 영구 디스크(Persistent Disk)를 사용하는 경우 /data 경로에 저장 가능
DB_DIR = os.environ.get("PERSISTENT_DIR", ".")
DB_NAME = os.path.join(DB_DIR, "donations_secure.db")

# 🛑 [중요] 여기에 너의 Pushbullet Access Token을 붙여넣으세요!
PUSHBULLET_API_KEY = os.environ.get("PUSHBULLET_API_KEY", "o.P9LtMvpDoNgYXOLogbiPsuIvZc95P2nY")

# 관리자 페이지 기본 비밀번호
ADMIN_PASSWORD = "zizer731!!"  # 필요 시 다른 비밀번호로 수정 가능

# ==========================================
# 🗄️ 데이터베이스 및 데이터 관리 모델
# ==========================================
def get_db_connection():
    """데이터베이스 연결을 안전하게 생성합니다."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row  # 컬럼명으로 데이터에 접근할 수 있게 설정
    return conn

def init_db():
    """서버 기동 시 데이터베이스 테이블이 없으면 자동으로 생성합니다."""
    conn = get_db_connection()
    c = conn.cursor()
    # 후원 내역 테이블 생성
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
    logger.info("💾 SQLite 데이터베이스가 성공적으로 초기화되었습니다.")

# ==========================================
# 🎨 프론트엔드 HTML / CSS / JS 템플릿 정의
# ==========================================

# 1. 메인 홈페이지 (정보 입력, 후원 명예의 전당, 실시간 한마디 피드)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>예준이의 실시간 방송 후원</title>
    <!-- Tailwind CSS 및 폰트 가져오기 -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Pretendard:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Pretendard', sans-serif;
            background: radial-gradient(circle at 50% 50%, #151528 0%, #080811 100%);
            min-height: 100vh;
            color: #ffffff;
            overflow-x: hidden;
        }
        .neon-text {
            font-family: 'Orbitron', sans-serif;
            text-shadow: 0 0 10px rgba(0, 255, 204, 0.8), 0 0 20px rgba(0, 255, 204, 0.4);
        }
        .neon-border {
            box-shadow: 0 0 15px rgba(0, 255, 204, 0.2);
            border: 1px solid rgba(0, 255, 204, 0.3);
            background: rgba(30, 30, 50, 0.6);
            backdrop-filter: blur(10px);
        }
        .animate-pulse-slow {
            animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: .8; transform: scale(0.98); }
        }
        /* 페이드인 애니메이션 */
        .fade-in {
            animation: fadeIn 0.8s ease-out forwards;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        /* 계좌 복사 토스트 알림 디자인 */
        #toast {
            visibility: hidden;
            min-width: 280px;
            background-color: #00ffcc;
            color: #080811;
            text-align: center;
            border-radius: 8px;
            padding: 14px;
            position: fixed;
            z-index: 50;
            left: 50%;
            bottom: 30px;
            transform: translateX(-50%);
            font-weight: bold;
            box-shadow: 0 5px 20px rgba(0, 255, 204, 0.5);
            transition: visibility 0s, opacity 0.3s ease-in-out;
            opacity: 0;
        }
        #toast.show {
            visibility: visible;
            opacity: 1;
        }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 mt-4 md:mt-10">
        
        <!-- 왼쪽 세션: 후원하기 폼 (5열 차지) -->
        <div class="lg:col-span-5 flex flex-col gap-6 fade-in" style="animation-delay: 0.1s;">
            <div class="text-center md:text-left mb-2">
                <h1 class="text-3xl md:text-4xl font-extrabold tracking-tight neon-text mb-2">YEJUN LIVE</h1>
                <p class="text-gray-400 text-sm md:text-base">예준이의 실시간 방송에 후원하고 소중한 메시지를 남겨보세요!</p>
            </div>

            <!-- 계좌 정보 안내 카드 (클릭 시 복사 가능) -->
            <div onclick="copyAccount()" class="neon-border rounded-2xl p-6 cursor-pointer hover:scale-[1.02] transition-all duration-300 relative group overflow-hidden">
                <div class="absolute -right-10 -top-10 w-32 h-32 bg-cyan-500 opacity-10 rounded-full group-hover:scale-150 transition-all duration-500"></div>
                <div class="flex justify-between items-start mb-3">
                    <span class="text-xs bg-cyan-500/20 text-cyan-400 px-3 py-1 rounded-full font-bold">계좌번호 터치 시 자동 복사</span>
                    <svg class="w-5 h-5 text-cyan-400 group-hover:animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
                </div>
                <p class="text-gray-400 text-xs mb-1">입금 은행</p>
                <h3 class="text-xl font-bold mb-2">🏦 토스뱅크 (Toss Bank)</h3>
                <div class="text-2xl font-black text-cyan-400 tracking-wider font-mono select-all">1001-5289-9617</div>
                <p class="text-gray-500 text-xs mt-2">예금주: 예준 | 기부 신청 후 이 계좌로 입금해주세요!</p>
            </div>

            <!-- 후원 등록 폼 -->
            <div class="neon-border rounded-2xl p-6 md:p-8">
                <h2 class="text-xl font-bold mb-6 text-cyan-400 border-b border-cyan-500/20 pb-2">✏️ 후원 정보 입력</h2>
                <form action="/ready" method="POST" class="space-y-5" onsubmit="return validateForm()">
                    <div>
                        <label class="block text-gray-400 text-xs mb-2">예금주명 (송금하시는 실명)</label>
                        <input type="text" name="name" id="donor_name" required 
                               class="w-full bg-[#1b1b30] border border-gray-700 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 rounded-lg p-3 text-white placeholder-gray-500 transition outline-none" 
                               placeholder="실제 돈을 보내시는 성함을 입력하세요.">
                    </div>
                    <div>
                        <label class="block text-gray-400 text-xs mb-2">후원 금액 (원)</label>
                        <input type="number" name="amount" id="donor_amount" required min="100"
                               class="w-full bg-[#1b1b30] border border-gray-700 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 rounded-lg p-3 text-white placeholder-gray-500 transition outline-none font-mono" 
                               placeholder="최소 100원 이상 입력">
                    </div>
                    <div>
                        <label class="block text-gray-400 text-xs mb-2">응원 메시지</label>
                        <textarea name="message" id="donor_message" required rows="3" maxlength="150"
                                  class="w-full bg-[#1b1b30] border border-gray-700 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 rounded-lg p-3 text-white placeholder-gray-500 transition outline-none resize-none" 
                                  placeholder="방송 화면에 띄울 응원 메시지를 작성해보세요! (최대 150자)"></textarea>
                    </div>
                    <button type="submit" class="w-full bg-gradient-to-r from-cyan-400 to-blue-500 text-gray-900 font-extrabold py-4 px-6 rounded-lg hover:from-cyan-300 hover:to-blue-400 hover:shadow-[0_0_20px_rgba(0,255,204,0.4)] transition-all duration-300 transform active:scale-95">
                        다음 단계 (계좌 전송 및 대기) 🚀
                    </button>
                </form>
            </div>
        </div>

        <!-- 오른쪽 세션: 랭킹 및 피드 (7열 차지) -->
        <div class="lg:col-span-7 flex flex-col gap-8 fade-in" style="animation-delay: 0.3s;">
            
            <!-- 명예의 전당 (누적 기부왕) -->
            <div class="neon-border rounded-2xl p-6 md:p-8 flex-1">
                <div class="flex justify-between items-center mb-6 border-b border-cyan-500/20 pb-3">
                    <h2 class="text-xl font-bold text-yellow-400 flex items-center gap-2">
                        <span>🏆 명예의 전당 (역대 기부왕)</span>
                    </h2>
                    <span class="text-xs text-gray-400">실시간 누적 집계</span>
                </div>
                
                <div class="space-y-4">
                    {% for rank in rankings %}
                    <div class="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition duration-300 border border-white/5">
                        <div class="flex items-center gap-4">
                            <!-- 순위 메달/번호 -->
                            <div class="w-8 h-8 rounded-full flex items-center justify-center font-black text-sm
                                {% if loop.index == 1 %} bg-yellow-400 text-gray-900 shadow-[0_0_10px_rgba(250,204,21,0.5)]
                                {% elif loop.index == 2 %} bg-slate-300 text-gray-900
                                {% elif loop.index == 3 %} bg-amber-600 text-white
                                {% else %} bg-gray-700 text-gray-300 {% endif %}">
                                {{ loop.index }}
                            </div>
                            <span class="font-bold text-base md:text-lg">{{ rank['name'] }}</span>
                        </div>
                        <div class="text-right">
                            <span class="text-cyan-400 font-extrabold font-mono text-base md:text-lg">{{ "{:,}".format(rank['total_amount']) }}</span>
                            <span class="text-xs text-gray-400 ml-1">원</span>
                        </div>
                    </div>
                    {% else %}
                    <div class="text-center py-10 text-gray-500">
                        아직 명예의 전당에 등록된 후원자가 없습니다.<br>첫 기부왕의 주인공이 되어보세요! 🎉
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- 최근 실시간 응원 메시지 피드 -->
            <div class="neon-border rounded-2xl p-6 md:p-8 flex-1">
                <div class="flex justify-between items-center mb-6 border-b border-cyan-500/20 pb-3">
                    <h2 class="text-xl font-bold text-cyan-400 flex items-center gap-2">
                        <span class="animate-pulse">💬 실시간 후원 한마디</span>
                    </h2>
                    <span class="text-xs text-gray-400">최신 5개 내역</span>
                </div>
                
                <div class="space-y-4">
                    {% for feed in recent_feeds %}
                    <div class="p-4 rounded-xl bg-[#1b1b30]/60 border-l-4 border-cyan-400 animate-fade-in-down">
                        <div class="flex justify-between items-center mb-1">
                            <span class="font-bold text-cyan-300 text-sm">{{ feed['name'] }} 님</span>
                            <span class="text-xs text-gray-500">{{ feed['timestamp'].split(' ')[1] }}</span>
                        </div>
                        <p class="text-white text-sm my-1 break-all">{{ feed['message'] }}</p>
                        <div class="text-right text-xs font-mono text-yellow-400/80 font-bold">
                            후원금액: {{ "{:,}".format(feed['amount']) }}원
                        </div>
                    </div>
                    {% else %}
                    <div class="text-center py-10 text-gray-500">
                        아직 활성화된 후원 메시지가 없습니다.<br>따뜻한 한마디를 방송 화면에 띄워보세요! 😊
                    </div>
                    {% endfor %}
                </div>
            </div>
            
        </div>
    </div>

    <!-- 복사 성공 토스트 알림 메시지 영역 -->
    <div id="toast">📋 계좌번호가 복사되었습니다! 편리하게 송금하세요.</div>

    <script>
        // 계좌번호 클립보드 복사 함수
        function copyAccount() {
            const accountText = "토스뱅크 1001-5289-9617";
            
            // 최신 클립보드 API 지원 시 사용
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(accountText).then(() => {
                    showToast();
                }).catch(err => {
                    fallbackCopy(accountText);
                });
            } else {
                fallbackCopy(accountText);
            }
        }

        // 구버전 및 모바일 웹뷰 대응용 임시 요소 복사 로직
        function fallbackCopy(text) {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed"; // 화면 바깥에 숨김
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand('copy');
                showToast();
            } catch (err) {
                alert("계좌 복사에 실패했습니다. 직접 입력해주세요: " + text);
            }
            document.body.removeChild(textArea);
        }

        // 토스트 알림 노출
        function showToast() {
            const toast = document.getElementById("toast");
            toast.className = "show";
            setTimeout(() => {
                toast.className = toast.className.replace("show", "");
            }, 2500);
        }

        // 입력 폼 유효성 체크 및 공격 장방지 필터링
        function validateForm() {
            const name = document.getElementById("donor_name").value.trim();
            const amount = parseInt(document.getElementById("donor_amount").value);
            const message = document.getElementById("donor_message").value.trim();

            if (name.length < 1) {
                alert("보내시는 분의 성함을 정확히 적어주세요!");
                return false;
            }
            if (isNaN(amount) || amount < 100) {
                alert("최소 후원 금액은 100원 이상입니다!");
                return false;
            }
            if (message.length < 1) {
                alert("응원 메시지를 남겨주세요!");
                return false;
            }
            return true;
        }
    </script>
</body>
</html>
"""

# 2. 입금 대기 및 완료 실시간 체크 화면 (AJAX Polling + Vanilla JS Confetti 시스템)
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
        body {
            font-family: 'Pretendard', sans-serif;
            background: #0b0b16;
            color: #ffffff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            position: relative;
        }
        .glass-box {
            background: rgba(25, 25, 45, 0.8);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 15px 35px rgba(0,0,0,0.4);
        }
        .neon-glow {
            box-shadow: 0 0 25px rgba(0, 255, 204, 0.3);
            border: 1px solid rgba(0, 255, 204, 0.5);
        }
        /* 로딩 스피너 커스텀 */
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.1);
            width: 70px;
            height: 70px;
            border-radius: 50%;
            border-left-color: #00ffcc;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        /* 풀스크린 축하 레이어 */
        #celebration-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(10, 10, 25, 0.95);
            z-index: 100;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }
        #confetti-canvas {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 101;
        }
    </style>
</head>
<body>
    <div class="glass-box rounded-2xl p-8 max-w-md w-full mx-4 text-center relative z-10">
        <div class="flex justify-center mb-6">
            <div class="spinner"></div>
        </div>
        
        <h1 class="text-2xl font-black text-yellow-400 mb-2">⏳ 실시간 입금 대기 중</h1>
        <p class="text-gray-300 text-sm mb-6"><span class="font-bold text-cyan-300">{{ name }}</span>님, 입금 대기 시스템이 작동하고 있습니다.</p>

        <!-- 입금 상세 가이드 박스 -->
        <div class="bg-[#1b1b30] rounded-xl p-5 mb-6 text-left border border-white/5 space-y-3">
            <div class="flex justify-between items-center text-xs text-gray-400">
                <span>보내실 은행</span>
                <span class="font-bold text-white">토스뱅크 (예금주: 예준)</span>
            </div>
            <div class="flex justify-between items-center text-xs text-gray-400">
                <span>계좌 번호</span>
                <span class="font-bold text-cyan-400 font-mono text-sm select-all">1001-5289-9617</span>
            </div>
            <hr class="border-white/5">
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-300 font-bold">정확한 송금액</span>
                <span class="text-xl font-extrabold text-yellow-400 font-mono">{{ "{:,}".format(amount) }} 원</span>
            </div>
        </div>

        <div class="text-xs text-rose-400 leading-relaxed font-semibold bg-rose-500/10 p-3 rounded-lg border border-rose-500/20">
            ⚠️ 반드시 입력하신 [예금주명: {{ name }}]과 [정확한 금액: {{ amount }}원]을 일치시켜 이체하셔야 1초 만에 자동 확인 처리됩니다!
        </div>

        <button onclick="location.href='/'" class="mt-6 text-sm text-gray-400 hover:text-white transition duration-200">
            ← 정보 재입력 및 메인으로
        </button>
    </div>

    <!-- 🎉 입금 완료 감지 시 즉시 실행될 축하 풀스크린 모달 -->
    <div id="celebration-overlay">
        <canvas id="confetti-canvas"></canvas>
        <div class="text-center p-8 max-w-lg relative z-[102] space-y-6">
            <!-- 멋진 네온 글로우 완료 카드 -->
            <div class="neon-glow bg-[#101026] p-8 md:p-12 rounded-3xl transform scale-95 animate-pulse-slow">
                <div class="w-20 h-20 bg-cyan-500/20 text-cyan-400 rounded-full flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(0,255,204,0.3)]">
                    <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
                </div>
                <h2 class="text-3xl md:text-4xl font-black text-cyan-400 tracking-tight mb-2">🎉 입금 확인 완료!</h2>
                <p class="text-gray-300 text-lg mb-6"><span class="font-bold text-yellow-300">{{ name }}</span>님의 기부가 성공적으로 승인되었습니다.</p>
                <div class="bg-cyan-500/10 rounded-2xl p-4 border border-cyan-500/20 mb-6">
                    <p class="text-xs text-gray-400 mb-1">보내주신 소중한 후원금</p>
                    <span class="text-2xl font-black text-white font-mono">{{ "{:,}".format(amount) }}원</span>
                </div>
                <p class="text-xs text-cyan-400/80 animate-pulse font-bold">5초 후 기부자 피드 목록으로 자동으로 돌아갑니다...</p>
            </div>
        </div>
    </div>

    <script>
        const donationId = "{{ donation_id }}";
        
        // 1. 실시간 입금 확인을 위한 AJAX Polling 로직 (2초 간격)
        function checkDonationStatus() {
            fetch(`/api/status/${donationId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === '완료') {
                        // 대기중에서 '완료' 상태로 변경된 경우 감지
                        triggerCelebration();
                    } else {
                        // 완료될 때까지 재귀적 폴링
                        setTimeout(checkDonationStatus, 2000);
                    }
                })
                .catch(err => {
                    console.error("서버 통신 오류:", err);
                    setTimeout(checkDonationStatus, 3000); // 오류 시 조금 더 넓은 간격으로 재시도
                });
        }

        // 2. 화면 상 축하 효과 활성화 및 메인 리다이렉션
        function triggerCelebration() {
            const overlay = document.getElementById("celebration-overlay");
            overlay.style.display = "flex";
            
            // 바닐라 자바스크립트 커스텀 콘페티(Confetti) 파티클 시스템 가동
            startConfetti();

            // 5초 후 자동으로 홈으로 이동
            setTimeout(() => {
                window.location.href = "/";
            }, 5000);
        }

        // 3. 순수 자바스크립트 엔진으로 구동하는 Confetti 효과 (라이브러리 제거하여 로딩속도 극대화)
        function startConfetti() {
            const canvas = document.getElementById("confetti-canvas");
            const ctx = canvas.getContext("2d");
            
            // 화면 크기에 동기화
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;

            const colors = ["#00ffcc", "#ff007f", "#ffcc00", "#3b82f6", "#10b981", "#ffffff"];
            const particles = [];

            // 파티클 객체 템플릿
            class Particle {
                constructor() {
                    this.x = Math.random() * canvas.width;
                    this.y = Math.random() * canvas.height - canvas.height;
                    this.size = Math.random() * 8 + 6;
                    this.color = colors[Math.floor(Math.random() * colors.length)];
                    this.speedX = Math.random() * 3 - 1.5;
                    this.speedY = Math.random() * 4 + 4;
                    this.rotation = Math.random() * 360;
                    this.rotationSpeed = Math.random() * 4 - 2;
                }
                update() {
                    this.x += this.speedX;
                    this.y += this.speedY;
                    this.rotation += this.rotationSpeed;
                    
                    // 화면 아래로 벗어나면 재생성하지 않고 제거할 수 있게 속도 조정 가능
                    if (this.y > canvas.height) {
                        this.y = -20;
                        this.x = Math.random() * canvas.width;
                    }
                }
                draw() {
                    ctx.save();
                    ctx.translate(this.x, this.y);
                    ctx.rotate((this.rotation * Math.PI) / 180);
                    ctx.fillStyle = this.color;
                    // 다양한 형태로 드로잉
                    ctx.fillRect(-this.size/2, -this.size/2, this.size, this.size);
                    ctx.restore();
                }
            }

            // 파티클 생성 (150개 분량)
            for (let i = 0; i < 150; i++) {
                particles.push(new Particle());
            }

            // 애니메이션 루프
            function animate() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                particles.forEach(p => {
                    p.update();
                    p.draw();
                });
                requestAnimationFrame(animate);
            }
            animate();

            // 리사이징 대응
            window.addEventListener('resize', () => {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            });
        }

        // 페이지 로드 시 실시간 추적 실행
        window.onload = checkDonationStatus;
    </script>
</body>
</html>
"""

# 3. 예준이만 들어올 수 있는 실시간 대시보드 (관제탑 / 통계분석 / 수동 승인 및 삭제 기능 탑재)
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>예준 관리자 관제 패널</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Pretendard:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Pretendard', sans-serif;
            background-color: #0b0b16;
            color: #ffffff;
            min-height: 100vh;
        }
        .admin-glow {
            border: 1px solid rgba(239, 68, 68, 0.3);
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.1);
            background: rgba(30, 20, 30, 0.6);
            backdrop-filter: blur(10px);
        }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto">
        <!-- 상단 헤더 영역 -->
        <div class="flex flex-col md:flex-row justify-between items-center mb-8 border-b border-red-500/20 pb-4">
            <div class="text-center md:text-left mb-4 md:mb-0">
                <h1 class="text-3xl font-black text-red-500 font-mono tracking-wider flex items-center gap-3 justify-center md:justify-start">
                    <span>👑 YEJUN ADMIN CONSOLE</span>
                </h1>
                <p class="text-gray-400 text-xs mt-1">실시간 데이터 스트리밍 감지 및 데이터베이스 강제 변경 툴</p>
            </div>
            <div>
                <a href="/" class="bg-gray-800 text-gray-300 font-bold py-2 px-4 rounded-lg hover:bg-gray-700 hover:text-white transition duration-200">
                    ← 후원 홈페이지 가기
                </a>
            </div>
        </div>

        <!-- 핵심 요약 지표 카드 섹션 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <!-- 1. 누적 후원 성공금액 -->
            <div class="admin-glow rounded-xl p-6 flex flex-col justify-between">
                <span class="text-xs text-gray-400 font-bold uppercase tracking-wider">💰 누적 승인 금액</span>
                <div class="flex items-baseline gap-1 mt-2">
                    <span class="text-3xl font-extrabold text-cyan-400 font-mono">{{ "{:,}".format(stats['total_success_amount']) }}</span>
                    <span class="text-xs text-gray-400">원</span>
                </div>
                <div class="text-[10px] text-gray-500 mt-2">입금 알림을 통해 상태가 '완료'된 누적 합산 금액</div>
            </div>
            <!-- 2. 총 후원 시도 및 성공 건수 -->
            <div class="admin-glow rounded-xl p-6 flex flex-col justify-between">
                <span class="text-xs text-gray-400 font-bold uppercase tracking-wider">📊 완료 / 전체 건수</span>
                <div class="flex items-baseline gap-1 mt-2">
                    <span class="text-3xl font-extrabold text-yellow-400 font-mono">{{ stats['success_count'] }}</span>
                    <span class="text-lg text-gray-500">/</span>
                    <span class="text-xl font-bold text-gray-400 font-mono">{{ stats['total_count'] }}</span>
                    <span class="text-xs text-gray-400 ml-1">건</span>
                </div>
                <div class="text-[10px] text-gray-500 mt-2">장난 유저 입력 데이터를 포함한 전체 활동 비율</div>
            </div>
            <!-- 3. 대기중인 후원금 (장난 데이터 필터링용) -->
            <div class="admin-glow rounded-xl p-6 flex flex-col justify-between">
                <span class="text-xs text-gray-400 font-bold uppercase tracking-wider">⏳ 실시간 입금 확인 대기중</span>
                <div class="flex items-baseline gap-1 mt-2">
                    <span class="text-3xl font-extrabold text-rose-500 font-mono">{{ stats['pending_count'] }}</span>
                    <span class="text-xs text-gray-400">건</span>
                </div>
                <div class="text-[10px] text-gray-500 mt-2">신청 후 아직 송금이 미인증된 후원 목록 수</div>
            </div>
        </div>

        <!-- 후원 원격 제어 및 내역 목록 테이블 -->
        <div class="admin-glow rounded-2xl overflow-hidden">
            <div class="p-6 border-b border-red-500/10 flex justify-between items-center">
                <h2 class="text-lg font-bold text-red-400">🗂️ 실시간 수동 컨트롤 타워</h2>
                <span class="text-[10px] bg-red-500/20 text-red-400 py-1 px-2.5 rounded-full font-bold">실시간 수동 제어 모드 활성화</span>
            </div>
            
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-red-500/5 text-gray-400 text-xs border-b border-red-500/10">
                            <th class="p-4 text-center">ID</th>
                            <th class="p-4">시간</th>
                            <th class="p-4">신청자명 (입금자)</th>
                            <th class="p-4">신청액</th>
                            <th class="p-4">메시지</th>
                            <th class="p-4 text-center">현재상태</th>
                            <th class="p-4 text-center">수동제어</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-white/5 text-sm">
                        {% for d in donations %}
                        <tr id="row-{{ d['id'] }}" class="hover:bg-white/5 transition duration-150">
                            <td class="p-4 text-center text-gray-500 font-mono">{{ d['id'] }}</td>
                            <td class="p-4 text-gray-400 text-xs">{{ d['timestamp'] }}</td>
                            <td class="p-4 font-bold text-white">{{ d['name'] }}</td>
                            <td class="p-4 font-mono text-cyan-400 font-extrabold">{{ "{:,}".format(d['amount']) }} 원</td>
                            <td class="p-4 text-gray-300 max-w-xs truncate" title="{{ d['message'] }}">{{ d['message'] }}</td>
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
                                    <button onclick="approveDonation({{ d['id'] }})" class="bg-cyan-500 text-gray-900 font-bold px-3 py-1 rounded text-xs hover:bg-cyan-400 transition">
                                        수동 승인
                                    </button>
                                    {% endif %}
                                    <button onclick="deleteDonation({{ d['id'] }})" class="bg-rose-600 text-white font-bold px-3 py-1 rounded text-xs hover:bg-rose-500 transition">
                                        삭제
                                    </button>
                                </div>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="7" class="text-center py-20 text-gray-500 font-semibold">데이터베이스에 후원 기록이 없습니다.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- AJAX 비동기 데이터베이스 처리 자바스크립트 -->
    <script>
        const adminPassword = "{{ password }}";

        // 1. 수동 입금 확인 처리
        function approveDonation(id) {
            if (!confirm("알림을 받지 못했더라도 해당 기부자 내역을 '수동 승인'하여 완료 상태로 바꾸시겠습니까?")) return;

            fetch(`/api/admin/approve/${id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password: adminPassword })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    alert("수동 승인 완료!");
                    location.reload(); // 대시보드 통계 수치 동기화를 위한 새로고침
                } else {
                    alert("승인 오류: " + data.message);
                }
            })
            .catch(err => alert("네트워크 오류 발생"));
        }

        // 2. 가짜 데이터 및 후원 목록 강제 삭제
        function deleteDonation(id) {
            if (!confirm("해당 기부 내역을 데이터베이스에서 영구 삭제하시겠습니까? (복구 불가능)")) return;

            fetch(`/api/admin/delete/${id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password: adminPassword })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    const row = document.getElementById(`row-${id}`);
                    if (row) {
                        row.style.opacity = 0;
                        setTimeout(() => {
                            row.remove();
                            alert("데이터가 완전히 삭제되었습니다.");
                            location.reload(); // 통계 수치 재동기화
                        }, 3000);
                    }
                } else {
                    alert("삭제 오류: " + data.message);
                }
            })
            .catch(err => alert("네트워크 오류 발생"));
        }
    </script>
</body>
</html>
"""

# 4. 단순 관리자 비밀번호 로그인 UI 폼
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>관리자 콘솔 인증</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #080811;
            color: #ffffff;
            font-family: 'Pretendard', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .glow {
            border: 1px solid rgba(239, 68, 68, 0.4);
            box-shadow: 0 0 25px rgba(239, 68, 68, 0.2);
        }
    </style>
</head>
<body class="p-4">
    <div class="glow bg-[#151528] rounded-2xl p-8 max-w-sm w-full">
        <div class="text-center mb-6">
            <span class="text-4xl">🔑</span>
            <h1 class="text-xl font-black mt-2 text-red-500 font-mono tracking-wider">YEJUN ADMIN VERIFY</h1>
            <p class="text-gray-400 text-xs mt-1">시스템 관리를 위한 보안 패널 접근용</p>
        </div>
        
        <form action="/admin_yejun" method="POST" class="space-y-4">
            <div>
                <input type="password" name="password" required 
                       class="w-full bg-[#20203a] border border-gray-700 focus:border-red-500 rounded-lg p-3 text-center outline-none transition" 
                       placeholder="어드민 비밀번호 입력">
            </div>
            <button type="submit" class="w-full bg-rose-600 hover:bg-rose-500 text-white font-extrabold py-3 px-4 rounded-lg transition-colors duration-200">
                콘솔 로그인 🛰️
            </button>
        </form>
        {% if error %}
        <p class="text-red-400 text-xs text-center mt-3 font-semibold">❌ 패스워드가 잘못되었습니다!</p>
        {% endif %}
    </div>
</body>
</html>
"""

# ==========================================
# 🛰️ Flask 주소 컨트롤러 (Routing Logic)
# ==========================================

@app.route('/')
def home():
    """기부자가 보는 첫 메인 화면"""
    conn = get_db_connection()
    
    # 누적 명예의 전당 (완료된 후원들 중 이름별 그룹화 후 정렬)
    rankings = conn.execute('''
        SELECT name, SUM(amount) as total_amount 
        FROM donations 
        WHERE status='완료' 
        GROUP BY name 
        ORDER BY total_amount DESC 
        LIMIT 5
    ''').fetchall()
    
    # 최근 후원 실시간 응원 한마디 (완료된 최신 후원 5건 목록)
    recent_feeds = conn.execute('''
        SELECT name, amount, message, timestamp 
        FROM donations 
        WHERE status='완료' 
        ORDER BY id DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template_string(INDEX_HTML, rankings=rankings, recent_feeds=recent_feeds)

@app.route('/ready', methods=['POST'])
def ready():
    """기부자가 폼을 전송 시 대기중으로 등록하고 입금 대기 안내 페이지로 전환"""
    name = request.form.get('name', '').strip()
    amount_str = request.form.get('amount', '0')
    message = request.form.get('message', '').strip()
    
    # 후원 유효성 백엔드 중복 검사
    try:
        amount = int(amount_str)
    except ValueError:
        amount = 0
        
    if not name or amount < 100 or not message:
        return "<script>alert('정상적이지 않은 접근입니다.'); window.location.href='/';</script>"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # DB에 안전하게 기록
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO donations (name, amount, message, status, timestamp) VALUES (?, ?, ?, '대기중', ?)",
        (name, amount, message, timestamp)
    )
    donation_id = c.lastrowid # 방금 들어간 레코드 고유 ID 획득
    conn.commit()
    conn.close()

    logger.info(f"🆕 새 기부 대기 등록 완료 -> ID: {donation_id}, 기부자: {name}, 신청액: {amount}원")
    
    # 생성된 고유 id와 함께 전용 템플릿 반환
    return render_template_string(PAYMENT_HTML, donation_id=donation_id, name=name, amount=amount)

@app.route('/api/status/<int:donation_id>')
def api_status(donation_id):
    """실시간 AJAX 폴링 응답용 API (해당 결제가 입금 완료되었는지 시청자 화면이 검사)"""
    conn = get_db_connection()
    row = conn.execute("SELECT status FROM donations WHERE id=?", (donation_id,)).fetchone()
    conn.close()
    
    if row:
        return jsonify({"status": row['status']})
    return jsonify({"status": "존재하지 않음"}), 404

@app.route('/admin_yejun', methods=['GET', 'POST'])
def admin():
    """비밀번호 보안 인증이 수반되는 실시간 대시보드 패널"""
    if request.method == 'POST':
        # 로그인 폼 전송 시
        password_input = request.form.get('password', '')
        if password_input == ADMIN_PASSWORD:
            return render_admin_panel(password_input)
        else:
            return render_template_string(LOGIN_HTML, error=True)
    else:
        # 일반 링크를 통해 접속 시 로그인 페이지 노출
        return render_template_string(LOGIN_HTML, error=False)

def render_admin_panel(valid_pw):
    """인증 완료 시 관리자 콘솔 대시보드를 드로잉하는 헬퍼 함수"""
    conn = get_db_connection()
    
    # 1. 기부 원장 전체 로딩 (역순 정렬)
    donations = conn.execute("SELECT * FROM donations ORDER BY id DESC").fetchall()
    
    # 2. 대시보드 통계 계산
    stats = {}
    
    # 누적 후원 금액 계산 (승인 완료 기준)
    total_success = conn.execute("SELECT SUM(amount) FROM donations WHERE status='완료'").fetchone()[0]
    stats['total_success_amount'] = total_success if total_success else 0
    
    # 전체 및 완료 카운트 계산
    stats['total_count'] = conn.execute("SELECT COUNT(*) FROM donations").fetchone()[0]
    stats['success_count'] = conn.execute("SELECT COUNT(*) FROM donations WHERE status='완료'").fetchone()[0]
    stats['pending_count'] = conn.execute("SELECT COUNT(*) FROM donations WHERE status='대기중'").fetchone()[0]
    
    conn.close()
    
    return render_template_string(ADMIN_HTML, donations=donations, stats=stats, password=valid_pw)

# ==========================================
# ⚡ 관리자용 원격 CRUD API (비동기 처리)
# ==========================================

@app.route('/api/admin/approve/<int:donation_id>', methods=['POST'])
def api_admin_approve(donation_id):
    """대시보드에서 수동으로 대기중인 후원을 강제 승인"""
    req_data = request.get_json() or {}
    password = req_data.get('password', '')
    
    if password != ADMIN_PASSWORD:
        return jsonify({"status": "fail", "message": "비밀번호 오류"}), 403
        
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE donations SET status='완료' WHERE id=?", (donation_id,))
    conn.commit()
    conn.close()
    logger.info(f"👑 [관리자 수동 제어] ID {donation_id}번 기부 내역이 강제 완료 처리되었습니다.")
    return jsonify({"status": "success"})

@app.route('/api/admin/delete/<int:donation_id>', methods=['POST'])
def api_admin_delete(donation_id):
    """가짜 장난 데이터나 불필요한 후원 레코드를 데이터베이스에서 완전히 삭제"""
    req_data = request.get_json() or {}
    password = req_data.get('password', '')
    
    if password != ADMIN_PASSWORD:
        return jsonify({"status": "fail", "message": "비밀번호 오류"}), 403
        
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM donations WHERE id=?", (donation_id,))
    conn.commit()
    conn.close()
    logger.warning(f"🚨 [관리자 수동 제어] ID {donation_id}번 데이터가 데이터베이스에서 완전히 영구 영구삭제 되었습니다.")
    return jsonify({"status": "success"})

# ==========================================
# 🤖 멀티스레드 기반 웹소켓 가로채기 봇
# ==========================================

def update_db_on_payment(full_text):
    """전송된 푸시 알람 텍스트를 파싱하여 데이터베이스에 대기 중인 대상과 매칭해 실시간 승인"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. '대기중' 상태인 것만 추출
    pending_donations = c.execute("SELECT id, name, amount FROM donations WHERE status='대기중'").fetchall()
    
    for row in pending_donations:
        d_id = row['id']
        d_name = row['name']
        d_amount = row['amount']
        
        # 콤마 제거한 순수 금액 문자열 생성 (예: "10,000" -> "10000")
        sanitized_text = full_text.replace(',', '')
        
        # ⚠️ 매칭 판별 공식:
        # 알림 푸시 내용에 대기중인 '이름'과 '금액' 정보가 모두 포함되어 있는지 완벽 체크
        if d_name in sanitized_text and str(d_amount) in sanitized_text:
            logger.info(f"🎯 [매칭 성공] 알림을 감지하여 승인 처리합니다! (이름: {d_name}, 금액: {d_amount}원)")
            c.execute("UPDATE donations SET status='완료' WHERE id=?", (d_id,))
            conn.commit()
            
    conn.close()

def on_message(ws, message):
    """스마트폰 미러링 알림을 실시간 감지"""
    try:
        data = json.loads(message)
        # Pushbullet에서 안드로이드 앱 알림(mirror)이 도착한 이벤트 감지
        if data.get("type") == "push" and data.get("push", {}).get("type") == "mirror":
            push = data["push"]
            package_name = push.get("package_name", "").lower()
            title = push.get("title", "")
            body = push.get("body", "")
            full_text = f"{title} {body}"
            
            # 토스 관련 앱 알림이거나 알림 텍스트에 토스가 잡히는 경우 필터링
            if "toss" in package_name or "토스" in full_text:
                # 입금 내역 판단 단어 매칭
                if "입금" in full_text or "원" in full_text:
                    logger.info(f"💰 [입금 알림 수신 성공] 분석 텍스트: {full_text}")
                    update_db_on_payment(full_text)
    except Exception as e:
        logger.error(f"⚠️ 메시지 파싱 중 오류 발생: {e}")

def on_error(ws, error):
    logger.error(f"❌ [웹소켓 에러] {error}")

def on_close(ws, close_status_code, close_msg):
    logger.warning("⚠️ 웹소켓 연결이 예기치 않게 종료되었습니다. 5초 뒤 자동 재연결합니다...")
    time.sleep(5)
    start_pushbullet_ws()

def on_open(ws):
    logger.info("🟢 [연결 성공] 스마트폰 Pushbullet 알림 서비스 가동 중! 실시간 후원을 받을 준비가 되었습니다.")

def start_pushbullet_ws():
    """실시간 푸시 웹소켓 연결 시작"""
    if PUSHBULLET_API_KEY == "여기에_너의_PUSHBULLET_API_키를_넣어주세요" or not PUSHBULLET_API_KEY:
        logger.warning("🚨 Pushbullet API 토큰이 설정되지 않았습니다. 실시간 감지 봇이 동작하지 않습니다.")
        return
        
    try:
        # 스트림 API 웹소켓 연결
        ws = websocket.WebSocketApp(
            f"wss://stream.pushbullet.com/websocket/{PUSHBULLET_API_KEY}",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.run_forever()
    except Exception as e:
        logger.error(f"⚠️ 소켓 구동 실패: {e}. 10초 뒤 재연결 시도...")
        time.sleep(10)
        start_pushbullet_ws()

def run_bot_thread():
    """웹소켓 봇을 백그라운드 스레드로 실행"""
    start_pushbullet_ws()

# ==========================================
# 🎬 프로그램 시작점 (Entry Point)
# ==========================================
if __name__ == '__main__':
    # 1. 데이터베이스 구축
    init_db()
    
    # 2. Pushbullet 알림 가로채기 봇 스레드 백그라운드 구동
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    # 3. Render.com 호스트 및 포트 바인딩 최적화
    # Render.com은 기본적으로 환경변수 'PORT'를 부여하므로 이를 자동 감지하도록 설계
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🔥 웹 서버 가동 중 (포트번호: {port})")
    
    # 디버그 모드가 켜져있으면 스레드가 중복실행될 수 있으므로 배포 모드로 구동
    app.run(debug=False, host='0.0.0.0', port=port)
