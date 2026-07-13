# -*- coding: utf-8 -*-
"""
==========================================================================================
                     🚀 YEJUN ULTIMATE FRAMEWORK v28 (MONGODB CLOUD EDITION) 🚀
                     🔥 룰렛 승인, 단톡방, 채널, 대형 임베드 명령어, 인벤토리 완벽 지원 🔥
                     ✨ [신규] 클라우드 MongoDB 연동으로 데이터 영구 보존 및 절대 초기화 방지 ✨
                     ✨ [신규] 출석체크 시스템 (관리자 보상액 커스텀 제어) 추가 ✨
                     ✨ [신규] 관리자 패널 내 특정 유저 아이템 직접 꽂아주기 기능 추가 ✨
                     ✨ [패치] 채팅 메시지 및 임베드 스크롤 압축(축소) 버그 완벽 픽스 ✨
==========================================================================================

본 시스템은 단일 파일(Single File)로 동작하는 초고도화 웹 프레임워크입니다.
기존 JSON 파일 입출력 방식을 MongoDB의 Document 기반으로 업그레이드하여
Render 등 클라우드 호스팅에서의 '재시작 시 데이터 증발' 현상을 완벽히 해결했습니다.
기존의 모든 설정, 로직, 확률, UI는 단 하나도 건드리지 않고 100% 보존되었습니다.
"""

from flask import Flask, render_template_string, request, jsonify, session, redirect
from pymongo import MongoClient
import random
import os
import time
import uuid
from datetime import datetime

# ==========================================================================================
# ⚙️ [SYSTEM] 서버 초기화 및 환경 설정
# ==========================================================================================
app = Flask(__name__)
app.secret_key = "yejun_ultimate_god_tier_key_2026_infinity_plus_alpha_v28_mongodb_max"

# ⚠️ [매우 중요] 본인의 MongoDB URI를 아래에 입력하세요. 
# (예: "mongodb+srv://<아이디>:<비밀번호>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority")
MONGO_URI = os.environ.get("MONGO_URI", "여기에_MONGODB_URI를_입력하세요")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # 연결 테스트
    client.server_info()
    db_client = client['gongqn_v28_db']
    app_state = db_client['app_state']
    print("✅ MongoDB 클라우드 데이터베이스 접속 성공!")
except Exception as e:
    print(f"❌ MongoDB 접속 실패! URI를 확인해주세요. 에러: {e}")
    # Fallback 또는 오류 처리 필요시 여기서 제어


# ==========================================================================================
# 🗄️ [DATABASE] 클라우드 NoSQL 데이터베이스 엔진 (자동 마이그레이션 및 무결성 검사)
# ==========================================================================================

def get_default_db():
    return {
        "users": {}, 
        "posts": [], 
        "notices": [], 
        "admin_msgs": [], 
        "coupons": {},
        "sys_config": {
            "roulette_cost": 500, 
            "m1": "홈(공지)", 
            "m2": "게시판", 
            "m3": "룰렛", 
            "m4": "상점", 
            "m5": "채팅", 
            "m6": "설정", 
            "m7": "인벤토리",
            "popup_notice": "환영합니다! V28 몽고DB 클라우드 시스템 업데이트가 완료되었습니다.",
            "r_i1": "최고급 소원권", "r_p1": 5,
            "r_i2": "꽝", "r_p2": 45,
            "r_i3": "프리미엄 놀이권", "r_p3": 10,
            "r_i4": "꽝", "r_p4": 20,
            "r_i5": "특별 야외권", "r_p5": 10,
            "r_i6": "꽝", "r_p6": 10,
            "att_reward": 150 # [신규] 기본 출석체크 보상금액
        },
        "shop_items": [],
        "chat_rooms": {},
        "reviews": [],
        "transactions": [],
        "roulette_approvals": [],     
        "item_use_approvals": [],     
        "friend_requests": []         
    }

def load_db():
    """
    MongoDB에서 메인 데이터를 로드합니다.
    데이터가 없거나 새 기능(출석체크 등)의 변수가 누락된 경우 자동 마이그레이션을 수행합니다.
    """
    try:
        doc = app_state.find_one({"_id": "MAIN_DATA_V28"})
        default_db = get_default_db()
        
        if not doc:
            print("최초 실행: MongoDB에 기본 데이터베이스 구조를 구축합니다.")
            app_state.insert_one({"_id": "MAIN_DATA_V28", "data": default_db})
            return default_db
            
        db = doc.get("data", {})
        needs_update = False
        
        # 최상위 키 무결성 검사
        for key in default_db:
            if key not in db:
                db[key] = default_db[key]
                needs_update = True
                
        # 유저 데이터 마이그레이션 (인벤토리, 친구 목록, [신규] 출석체크 날짜)
        for u_id, u_data in db.get('users', {}).items():
            if 'friends' not in u_data: 
                u_data['friends'] = []
                needs_update = True
            if 'inventory' not in u_data: 
                u_data['inventory'] = []
                needs_update = True
            if 'last_attendance' not in u_data:
                u_data['last_attendance'] = ""
                needs_update = True
                
        # 시스템 컨피그 마이그레이션 (출석 보상)
        if "att_reward" not in db["sys_config"]:
            db["sys_config"]["att_reward"] = default_db["sys_config"]["att_reward"]
            needs_update = True

        if needs_update:
            save_db(db)
            
        return db
    except Exception as e:
        print(f"[DB 로드 심각한 오류] {e}")
        return get_default_db()

def save_db(data):
    """
    데이터베이스 변경사항을 클라우드 MongoDB에 영구 저장합니다.
    Render 재시작 시에도 데이터가 완벽하게 보존됩니다.
    """
    try:
        app_state.update_one(
            {"_id": "MAIN_DATA_V28"},
            {"$set": {"data": data}},
            upsert=True
        )
    except Exception as e:
        print(f"[DB 저장 심각한 오류] {e}")

# ==========================================================================================
# 🎨 [FRONTEND] 마스터 UI 템플릿 (초대형 CSS 및 스크립트 결합)
# ==========================================================================================

UI_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Gongqn 공식커뮤니티 V28</title>
    
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --bg-color: #f8fafc;
            --card-bg: #ffffff; 
            --primary-grad: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            --primary: #6366f1; 
            --primary-hover: #4f46e5; 
            --text-main: #0f172a; 
            --text-sub: #64748b;
            --border: #e2e8f0;
            --danger-grad: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%);
            --danger: #ef4444;
            --success-grad: linear-gradient(135deg, #10b981 0%, #059669 100%);
            --success: #10b981;
            --warning-grad: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
            --warning: #f59e0b;
            --info-grad: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            --info: #0ea5e9;
            
            --radius: 20px;
            --radius-md: 12px;
            --radius-sm: 8px;
            --shadow-sm: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
            --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            --shadow-xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            
            --transition-fast: 0.2s ease;
            --transition-normal: 0.3s ease;
            --transition-slow: 0.5s ease;
        }

        /* 기본 리셋 및 레이아웃 */
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Pretendard', sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-main); padding-bottom: 120px; overflow-x: hidden; scroll-behavior: smooth; }

        header {
            position: sticky; top: 0; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
            padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(226, 232, 240, 0.8); z-index: 1000; box-shadow: var(--shadow-sm);
            transition: all var(--transition-normal);
        }
        .logo { font-size: 1.4rem; font-weight: 900; background: var(--primary-grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px;}
        .cash-badge { background: #fef3c7; color: #d97706; padding: 8px 15px; border-radius: 50px; font-weight: 800; font-size: 0.95rem; box-shadow: var(--shadow-sm); display: flex; align-items: center; gap: 5px;}

        .container { max-width: 760px; margin: 0 auto; padding: 20px; }
        
        .page { display: none; animation: fadeInScale 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; opacity: 0; }
        .page.active { display: block; }
        @keyframes fadeInScale { from { opacity: 0; transform: translateY(20px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }

        .card { background: var(--card-bg); border-radius: var(--radius); padding: 25px; margin-bottom: 25px; box-shadow: var(--shadow-md); border: 1px solid var(--border); transition: transform 0.3s ease, box-shadow 0.3s ease; position: relative; overflow: hidden;}
        .card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
        .card-title { font-size: 1.25rem; font-weight: 800; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; color: var(--text-main); }

        input[type="text"], input[type="password"], input[type="number"], textarea, select {
            width: 100%; padding: 16px; border-radius: 14px; border: 1.5px solid var(--border); background: #f8fafc;
            margin-bottom: 15px; outline: none; font-size: 1rem; transition: all 0.3s ease; font-weight: 500;
        }
        input:focus, textarea:focus, select:focus { border-color: var(--primary); box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15); background: #fff; }
        
        .btn { width: 100%; padding: 16px; border-radius: 14px; border: none; font-size: 1.05rem; font-weight: 800; cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); margin-bottom: 10px; box-shadow: var(--shadow-sm); display: flex; align-items: center; justify-content: center; gap: 8px;}
        .btn:active { transform: scale(0.96); box-shadow: none; }
        .btn-primary { background: var(--primary-grad); color: white; }
        .btn-success { background: var(--success-grad); color: white; }
        .btn-danger { background: var(--danger-grad); color: white; }
        .btn-warning { background: var(--warning-grad); color: white; }
        .btn-info { background: var(--info-grad); color: white; }
        .btn-outline { background: transparent; border: 2px solid var(--border); color: var(--text-main); }
        .btn-outline:hover { border-color: var(--primary); color: var(--primary); }

        .editor-toolbar { display: flex; gap: 8px; margin-bottom: 15px; flex-wrap: wrap; background: #f1f5f9; padding: 10px; border-radius: 12px; }
        .editor-btn { padding: 10px 15px; border-radius: 10px; border: 1px solid var(--border); background: white; cursor: pointer; color: var(--text-main); transition: 0.2s; font-weight: bold; }
        .editor-btn:hover { background: var(--primary); color: white; border-color: var(--primary); transform: translateY(-2px); }

        .shop-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
        .shop-item { background: white; border-radius: 16px; overflow: hidden; border: 1px solid var(--border); box-shadow: var(--shadow-sm); transition: 0.3s; position: relative; display: flex; flex-direction: column; }
        .shop-item:hover { transform: translateY(-5px); box-shadow: var(--shadow-lg); }
        .shop-img { width: 100%; height: 180px; object-fit: cover; background: #e2e8f0; }
        .shop-info { padding: 20px; display: flex; flex-direction: column; flex-grow: 1; }
        .shop-title { font-size: 1.2rem; font-weight: 800; margin-bottom: 5px; }
        .shop-price { color: var(--danger); font-weight: 900; font-size: 1.1rem; margin-bottom: 10px; }
        .shop-desc { font-size: 0.9rem; color: var(--text-sub); margin-bottom: 15px; line-height: 1.5; flex-grow: 1; }

        .chat-list-item { display: flex; align-items: center; justify-content: space-between; padding: 18px; background: white; border-radius: 16px; margin-bottom: 12px; border: 1px solid var(--border); transition: 0.2s; cursor: pointer; box-shadow: var(--shadow-sm); }
        .chat-list-item:hover { background: #f8fafc; border-color: var(--primary); transform: translateX(5px); }
        
        .chat-window { display: none; flex-direction: column; height: 75vh; background: white; border-radius: 20px; overflow: hidden; box-shadow: var(--shadow-lg); border: 1px solid var(--border); }
        .chat-header { background: var(--primary-grad); color: white; padding: 15px 20px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 10; }
        .chat-messages { flex: 1; padding: 20px; overflow-y: auto; background: #f8fafc; display: flex; flex-direction: column; gap: 15px; }
        .chat-input-area { display: flex; padding: 15px; background: white; border-top: 1px solid var(--border); gap: 10px; align-items: center; z-index: 10; }
        
        /* 🔥 버그 패치: 임베드 및 말풍선이 찌그러지는 현상 수정 (flex-shrink: 0) */
        .msg-bubble { max-width: 80%; padding: 12px 18px; border-radius: 20px; font-size: 1rem; line-height: 1.5; position: relative; animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); word-break: break-word; box-shadow: 0 2px 5px rgba(0,0,0,0.05); flex-shrink: 0; }
        @keyframes popIn { from { opacity: 0; transform: scale(0.8) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
        .msg-self { align-self: flex-end; background: var(--primary-grad); color: white; border-bottom-right-radius: 5px; }
        .msg-other { align-self: flex-start; background: white; border: 1px solid var(--border); border-bottom-left-radius: 5px; color: var(--text-main); }
        .sys-msg { align-self: center; background: rgba(0,0,0,0.05); color: var(--text-sub); font-size: 0.85rem; padding: 6px 16px; border-radius: 20px; text-align: center; font-weight: bold; margin: 10px 0; flex-shrink: 0;}

        /* 초대형 커스텀 임베드 디자인 */
        .super-embed {
            background: #ffffff; border-left: 6px solid var(--primary); border-radius: 12px; padding: 20px; color: var(--text-main);
            width: 100%; max-width: 90%; margin: 10px 0; box-shadow: 0 8px 25px rgba(0,0,0,0.08); align-self: center; font-family: 'Pretendard', sans-serif;
            position: relative; overflow: hidden; animation: slideInRight 0.4s ease-out; flex-shrink: 0; /* 🔥 찌그러짐 방지 */
        }
        @keyframes slideInRight { from { opacity: 0; transform: translateX(30px); } to { opacity: 1; transform: translateX(0); } }
        .super-embed::before {
            content: ''; position: absolute; top: 0; right: 0; width: 100px; height: 100px;
            background: radial-gradient(circle, rgba(99,102,241,0.1) 0%, rgba(255,255,255,0) 70%); border-radius: 50%; transform: translate(30%, -30%);
        }
        .embed-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
        .embed-author { font-size: 0.85rem; font-weight: bold; color: var(--text-sub); display: flex; align-items: center; gap: 5px; }
        .embed-title { font-weight: 900; font-size: 1.3rem; margin-bottom: 10px; line-height: 1.3; }
        .embed-desc { font-size: 1rem; margin-bottom: 15px; line-height: 1.6; color: #334155; }
        .embed-footer { font-size: 0.75rem; color: #94a3b8; display: flex; align-items: center; gap: 5px; margin-top: 10px; border-top: 1px solid #f1f5f9; padding-top: 10px; }
        
        .embed-theme-success { border-left-color: #10b981; } .embed-theme-success .embed-title { color: #059669; }
        .embed-theme-danger { border-left-color: #ef4444; } .embed-theme-danger .embed-title { color: #dc2626; }
        .embed-theme-info { border-left-color: #3b82f6; } .embed-theme-info .embed-title { color: #2563eb; }
        .embed-theme-warning { border-left-color: #f59e0b; } .embed-theme-warning .embed-title { color: #d97706; }
        
        .star-rating { display: flex; flex-direction: row-reverse; justify-content: flex-end; gap: 5px; margin: 10px 0; }
        .star-rating input { display: none; }
        .star-rating label { font-size: 1.8rem; color: #cbd5e1; cursor: pointer; transition: 0.2s; }
        .star-rating label:hover, .star-rating label:hover ~ label, .star-rating input:checked ~ label { color: #fbbf24; transform: scale(1.1); }
        .review-input { background: #f8fafc; border: 2px solid #e2e8f0; color: var(--text-main); padding: 12px; border-radius: 8px; width: 100%; margin-top: 10px; outline: none; font-size: 0.95rem; font-weight: bold; }
        .review-btn { background: var(--primary-grad); color: white; border: none; padding: 12px 15px; border-radius: 8px; font-weight: 900; cursor: pointer; margin-top: 10px; transition: 0.2s; width: 100%; font-size: 1.05rem; }
        .review-btn:hover { box-shadow: 0 4px 15px rgba(99,102,241,0.4); }

        .bottom-nav {
            position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid var(--border); box-shadow: 0 -10px 20px rgba(0,0,0,0.03); z-index: 1000; padding-bottom: env(safe-area-inset-bottom, 12px);
        }
        .nav-item { display: flex; flex-direction: column; align-items: center; color: #94a3b8; text-decoration: none; font-size: 0.7rem; font-weight: 800; gap: 6px; flex: 1; cursor: pointer; transition: 0.3s; }
        .nav-item i { font-size: 1.4rem; transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        .nav-item.active { color: var(--primary); }
        .nav-item.active i { transform: translateY(-4px) scale(1.15); filter: drop-shadow(0 2px 4px rgba(99,102,241,0.3)); }

        .inventory-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; margin-top: 15px; }
        .inv-item { background: linear-gradient(to bottom, #ffffff, #f8fafc); border: 2px solid var(--border); border-radius: 16px; padding: 15px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: 0.3s; box-shadow: var(--shadow-sm); position: relative; }
        .inv-item:hover { transform: translateY(-5px); border-color: var(--primary); box-shadow: var(--shadow-md); }
        .inv-icon { font-size: 2.5rem; color: var(--primary); margin-bottom: 10px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1)); }
        .inv-name { font-weight: 900; font-size: 1rem; color: var(--text-main); margin-bottom: 5px; word-break: keep-all; }
        .inv-date { font-size: 0.7rem; color: var(--text-sub); margin-bottom: 10px; }
        
        .btn-use-item { background: var(--success-grad); color: white; border: none; padding: 8px 12px; border-radius: 8px; font-weight: 900; font-size: 0.85rem; cursor: pointer; width: 100%; transition: 0.2s; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2); }
        .btn-use-item:hover { transform: scale(1.05); }

        .channel-card { background: white; border: 1px solid var(--border); border-radius: 12px; padding: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: 0.2s; }
        .channel-card:hover { border-color: var(--primary); background: #f8fafc; }
        .channel-icon { width: 40px; height: 40px; border-radius: 10px; background: var(--info-grad); color: white; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; margin-right: 15px; }

        .friend-req-card { background: #fffbeb; border: 1px solid #fcd34d; border-radius: 12px; padding: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; transition: 0.2s; }
        .friend-req-card .info { display: flex; align-items: center; gap: 10px; }
        .friend-req-card .actions { display: flex; gap: 5px; }

        .modal { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(15, 23, 42, 0.8); z-index:9999; display:none; justify-content:center; align-items:center; text-align:center; color:white; backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);}
        .modal.active { display: flex; flex-direction: column; animation: fadeInScale 0.3s ease; }
        .popup-content-box { background: white; color: var(--text-main); padding: 35px 30px; border-radius: 24px; width: 90%; max-width: 420px; position: relative; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); text-align: left; }
        .popup-close { position: absolute; top: 15px; right: 20px; background: none; border: none; font-size: 1.5rem; color: var(--text-sub); cursor: pointer; transition: 0.2s; }
        .popup-close:hover { color: var(--danger); transform: rotate(90deg); }

        .roulette-container { position: relative; width: 320px; height: 320px; margin: 30px auto; max-width: 100%; filter: drop-shadow(0 15px 30px rgba(0,0,0,0.15)); }
        #roulette-canvas { width: 100%; height: 100%; border-radius: 50%; border: 10px solid #ffffff; transition: transform 5s cubic-bezier(0.1, 0, 0.1, 1); }
        .pin { position: absolute; top: -20px; left: 50%; transform: translateX(-50%); color: #ef4444; font-size: 3rem; z-index: 10; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.4)); }

        @media (max-width: 600px) {
            .container { padding: 15px 10px; }
            header { padding: 12px 15px; }
            .logo { font-size: 1.2rem; }
            .nav-item span { font-size: 0.65rem; }
            .shop-grid { grid-template-columns: 1fr; }
            .chat-window { height: 80vh; }
            .super-embed { max-width: 100%; }
        }
    </style>
</head>
<body>

<div class="modal" id="welcome-popup">
    <div class="popup-content-box">
        <button class="popup-close" onclick="closePopup()"><i class="fas fa-times"></i></button>
        <h2 style="margin-bottom: 20px; color: var(--primary); display: flex; align-items: center; gap: 10px; font-weight: 900; font-size: 1.4rem;">
            <i class="fas fa-bell"></i> 서버 운영자 공지
        </h2>
        <div style="font-size: 1.05rem; line-height: 1.6; margin-bottom: 30px; color: var(--text-sub); background: #f8fafc; padding: 15px; border-radius: 12px; border-left: 4px solid var(--primary);">
            {{ sys.popup_notice|safe }}
        </div>
        <button class="btn btn-primary" onclick="closePopup()" style="margin-bottom: 0; padding: 18px; font-size: 1.1rem;">확인하고 입장하기</button>
    </div>
</div>

<header>
    <div class="logo">Gongqn V28</div>
    <div class="cash-badge"><i class="fas fa-coins" style="color:#f59e0b;"></i> <span id="my-cash" style="margin-left:3px;">{{ session.get('cash') if session.get('role') != 'admin' else '∞' }}</span></div>
</header>

<div class="container">
    
    <div id="p-home" class="page">
        <div style="background: var(--primary-grad); border-radius: var(--radius); padding: 30px; color: white; margin-bottom: 25px; box-shadow: var(--shadow-md); position: relative; overflow: hidden;">
            <div style="position: relative; z-index: 2;">
                <h1 style="font-size: 1.8rem; font-weight: 900; margin-bottom: 10px;">환영합니다, {{ session.get('nick') }}님!</h1>
                <p style="font-size: 1rem; opacity: 0.9; line-height: 1.5;">V28 MongoDB 클라우드 시스템이 적용되었습니다.<br>데이터가 절대 초기화되지 않는 안전한 환경을 즐겨보세요.</p>
            </div>
            <i class="fas fa-database" style="position: absolute; right: -20px; bottom: -20px; font-size: 8rem; opacity: 0.1; transform: rotate(-15deg);"></i>
        </div>

        <div class="card" style="border: 2px solid var(--info); background: #f0f9ff; text-align: center;">
            <div class="card-title" style="justify-content: center; color: #0369a1;"><i class="fas fa-calendar-check"></i> 매일매일 출석체크</div>
            <p style="color: var(--text-sub); margin-bottom: 15px; font-weight: bold;">오늘 접속하셨다면 버튼을 눌러 보상을 받으세요!</p>
            <button id="btn-attendance" class="btn btn-info" onclick="checkAttendance()" style="padding: 20px; font-size: 1.2rem; box-shadow: 0 10px 20px rgba(14, 165, 233, 0.3);">
                <i class="fas fa-gift"></i> 출석 완료하고 {{ sys.att_reward }} 캐시 받기
            </button>
        </div>

        <div class="card">
            <div class="card-title"><i class="fas fa-bullhorn" style="color:var(--primary);"></i> 주요 공지사항</div>
            {% if not notices %}<p style="text-align:center; color:var(--text-sub); padding: 30px; background:#f8fafc; border-radius:12px;">등록된 공지가 없습니다.</p>{% endif %}
            {% for n in notices %}
            <div style="border-bottom: 1px solid var(--border); padding: 20px 0;">
                <h3 style="margin-bottom:12px; font-size:1.3rem; font-weight:900; color:var(--text-main);">{{ n.title|safe }}</h3>
                <div style="font-size: 1rem; line-height: 1.7; word-break: break-all; color:#334155;">{{ n.content|safe }}</div>
                {% if n.img %}<img src="{{ n.img }}" style="max-width:100%; border-radius:16px; margin-top:20px; box-shadow: var(--shadow-sm);">{% endif %}
                <div style="margin-top:20px; font-size:0.85rem; color:var(--text-sub); display:flex; justify-content:space-between; align-items:center;">
                    <span style="background:#f1f5f9; padding:5px 10px; border-radius:8px;"><i class="far fa-clock"></i> {{ n.date }}</span>
                    {% if session.get('role') == 'admin' %} <button type="button" onclick="delContent('notice', {{ loop.index0 }})" style="color:var(--danger); background:rgba(239, 68, 68, 0.1); padding:6px 12px; border-radius:8px; border:none; cursor:pointer; font-weight:bold; transition:0.2s;"><i class="fas fa-trash"></i> 삭제</button> {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="card" style="border: 2px solid #10b981; position: relative;">
            <div style="position: absolute; top: -12px; right: 20px; background: var(--success-grad); color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 0.8rem; box-shadow: var(--shadow-sm);">LIVE</div>
            <div class="card-title"><i class="fas fa-handshake" style="color:#10b981;"></i> 실시간 거래 기록</div>
            <div id="tx-list">
                {% if not transactions %}<p style="text-align:center; color:var(--text-sub); padding: 20px; background:#f8fafc; border-radius:12px;">아직 거래 내역이 없습니다.</p>{% endif %}
                {% for t in transactions %}
                <div class="chat-list-item" style="border-left: 4px solid #10b981; margin-bottom: 8px; padding: 15px;">
                    <div>
                        <span style="font-weight:900; color:var(--primary);">{{ t.buyer_nick }}</span>님이 
                        <span style="font-weight:900; color:#0f172a;">{{ t.item_name }}</span> 상품 거래를 완료했습니다! 🎉
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-sub); min-width:80px; text-align:right;">{{ t.date }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <div id="p-board" class="page">
        <div class="card">
            <div class="card-title"><i class="fas fa-pen text-primary"></i> 커뮤니티 글쓰기</div>
            <input type="text" id="post-title" placeholder="제목을 멋지게 지어주세요 (최대 50자)">
            <div class="editor-toolbar">
                <button type="button" class="editor-btn" onclick="formatText('post-content', 'b')" title="굵게"><i class="fas fa-bold"></i></button>
                <button type="button" class="editor-btn" onclick="formatText('post-content', 'i')" title="기울임"><i class="fas fa-italic"></i></button>
                <button type="button" class="editor-btn" onclick="formatText('post-content', 'u')" title="밑줄"><i class="fas fa-underline"></i></button>
                <button type="button" class="editor-btn" onclick="formatColor('post-content')" title="글자색"><i class="fas fa-palette"></i></button>
            </div>
            <textarea id="post-content" rows="5" placeholder="내용을 작성해주세요 (HTML 태그 및 서식 지원)"></textarea>
            <button type="button" class="btn btn-primary" onclick="submitPost()"><i class="fas fa-paper-plane"></i> 게시물 등록 완료</button>
        </div>

        <div style="position: relative; margin-bottom: 20px;">
            <i class="fas fa-search" style="position: absolute; left: 20px; top: 50%; transform: translateY(-50%); color: var(--text-sub); font-size: 1.2rem;"></i>
            <input type="text" id="search-box" placeholder="제목이나 내용으로 빠르게 검색..." onkeyup="searchBoard()" style="background:white; border:2px solid var(--border); border-radius:20px; padding:18px 20px 18px 50px; font-weight:bold; box-shadow: var(--shadow-sm); margin:0;">
        </div>

        <div id="board-list">
            {% for p in posts %}
            <div class="card post" style="{% if p.is_pinned %}border: 2px solid var(--primary); background: #f8faff;{% endif %} padding: 25px; margin-bottom: 20px;">
                {% if p.is_pinned %}<div style="position:absolute; top:-12px; left:20px; background:var(--primary-grad); color:white; padding:6px 15px; border-radius:20px; font-size:0.85rem; font-weight:bold; box-shadow: var(--shadow-sm);"><i class="fas fa-thumbtack"></i> 관리자 고정됨</div>{% endif %}
                
                <div style="display:flex; align-items:center; gap:15px; margin-bottom:20px; margin-top: {% if p.is_pinned %}10px{% else %}0{% endif %};">
                    <img src="{{ p.author_pfp if p.author_pfp else 'https://cdn-icons-png.flaticon.com/512/149/149071.png' }}" style="width:50px; height:50px; border-radius:50%; object-fit:cover; border:2px solid #e2e8f0;">
                    <div>
                        <div style="font-weight:900; font-size:1.1rem; color:var(--text-main);">{{ p.author_nick }}</div>
                        <div style="font-size:0.85rem; color:var(--text-sub); margin-top:3px;"><i class="fas fa-at"></i>{{ p.author }} &nbsp;|&nbsp; <i class="far fa-clock"></i> {{ p.date }}</div>
                    </div>
                    <div style="margin-left:auto; display:flex; gap:10px;">
                        {% if session.get('role') == 'admin' %}
                        <button type="button" onclick="pinPost({{ loop.index0 }})" style="background:#fef3c7; border:none; color:#d97706; padding:8px 12px; border-radius:10px; cursor:pointer; font-size:1rem; transition:0.2s;" title="고정 토글"><i class="fas fa-thumbtack"></i></button>
                        {% endif %}
                        {% if session.get('role') == 'admin' or p.author == session.get('user') %}
                        <button type="button" onclick="delContent('post', {{ loop.index0 }})" style="background:#fee2e2; border:none; color:#ef4444; padding:8px 12px; border-radius:10px; cursor:pointer; font-size:1rem; transition:0.2s;" title="삭제"><i class="fas fa-trash"></i></button>
                        {% endif %}
                    </div>
                </div>
                
                <h3 class="p-title" style="margin-bottom:15px; font-size:1.4rem; font-weight:900; line-height:1.4;">{{ p.title|safe }}</h3>
                <div class="p-desc" style="font-size:1.05rem; line-height:1.7; white-space:pre-wrap; word-break:break-all; color:#334155; padding-bottom: 20px;">{{ p.content|safe }}</div>
                
                <div style="display:flex; gap:12px; margin-top:10px; border-top:1px dashed var(--border); padding-top:20px;">
                    <button type="button" class="editor-btn" onclick="actPost('like', {{ loop.index0 }})" style="border-radius:20px; font-weight:900; color:#ef4444; background: #fef2f2; border-color: #fecaca; flex:1; padding:12px;"><i class="fas fa-heart"></i> 좋아요 {{ p.likes|length }}</button>
                    <button type="button" class="editor-btn" onclick="actPost('report', {{ loop.index0 }})" style="border-radius:20px; font-weight:bold; color:var(--text-sub); flex:1; padding:12px;"><i class="fas fa-exclamation-triangle"></i> 신고하기</button>
                </div>
            </div>
            {% endfor %}
            {% if not posts %}<div style="text-align:center; padding: 50px 20px; color:var(--text-sub); background:white; border-radius:20px; border:2px dashed var(--border);">첫 번째 게시글의 주인공이 되어보세요!</div>{% endif %}
        </div>
    </div>

    <div id="p-roulette" class="page">
        <div class="card" style="text-align:center; background: linear-gradient(to bottom, #ffffff, #f8fafc);">
            <div class="card-title" style="justify-content:center; font-size: 1.5rem;"><i class="fas fa-gift" style="color:#f59e0b;"></i> 행운의 프리미엄 룰렛</div>
            <p style="color:var(--text-sub); margin-bottom:15px; font-size:1.1rem; background:#f1f5f9; display:inline-block; padding:8px 20px; border-radius:20px; font-weight:bold;">1회 참여: <b style="color:var(--danger); font-size:1.2rem;">{{ sys.roulette_cost }} 캐시</b></p>
            
            <div class="roulette-container">
                <i class="fas fa-caret-down pin"></i>
                <canvas id="roulette-canvas" width="320" height="320"></canvas>
            </div>
            
            <div style="background:#fff7ed; border:1px solid #fed7aa; color:#c2410c; padding:15px; border-radius:12px; margin-top:20px; font-size:0.9rem; font-weight:bold; text-align:left;">
                <i class="fas fa-info-circle"></i> V28 룰렛 안내사항<br>
                당첨 시 즉시 지급되지 않으며, 관리자에게 당첨 문자가 전송됩니다. 관리자 승인 완료 시 <b>[인벤토리]</b>로 아이템이 자동 지급됩니다.
            </div>

            <button id="spin-btn" type="button" class="btn btn-warning" onclick="spinRoulette()" style="margin-top:20px; font-size:1.3rem; padding:20px; border-radius:16px; font-weight:900; box-shadow: 0 10px 25px rgba(245, 158, 11, 0.3);"><i class="fas fa-play"></i> 짜릿하게 돌리기 (캐시 차감)</button>
        </div>
    </div>

    <div id="p-shop" class="page">
        <div class="card" style="background: var(--primary-grad); color: white; border:none; box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);">
            <h2 style="margin-bottom: 10px; font-size: 1.6rem;"><i class="fas fa-shopping-cart"></i> 프리미엄 공식 상점</h2>
            <p style="opacity: 0.9; line-height:1.5; font-size: 1.05rem;">원하는 상품을 구매하세요!<br>구매 즉시 VVIP 전용 1:1 채팅 채널이 개설되어 안전한 인도가 보장됩니다.</p>
        </div>
        
        <div class="shop-grid">
            {% for item in shop_items %}
            <div class="shop-item">
                {% if item.img %}
                <img src="{{ item.img }}" class="shop-img" alt="상품 이미지">
                {% else %}
                <div class="shop-img" style="display:flex;align-items:center;justify-content:center;color:#94a3b8;background:linear-gradient(45deg, #f1f5f9, #e2e8f0);"><i class="fas fa-box-open fa-4x"></i></div>
                {% endif %}
                <div class="shop-info">
                    <div class="shop-title">{{ item.title }}</div>
                    <div class="shop-price"><i class="fas fa-coins"></i> {{ item.price }} 캐시</div>
                    <div class="shop-desc">{{ item.desc }}</div>
                    <div style="display:flex; gap:10px; margin-top:auto;">
                        <button type="button" class="btn btn-primary" style="padding:15px; margin:0; flex-grow:1; font-size:1.1rem;" onclick="buyItem('{{ item.id }}', '{{ item.title }}', {{ item.price }})"><i class="fas fa-check-circle"></i> 구매 신청</button>
                    </div>
                </div>
            </div>
            {% endfor %}
            {% if not shop_items %}
            <div style="grid-column: 1/-1; text-align:center; padding: 60px 20px; color:var(--text-sub); background:white; border-radius:20px; border:2px dashed var(--border); font-size:1.1rem; font-weight:bold;">
                <i class="fas fa-store-slash fa-3x" style="margin-bottom:15px; color:#cbd5e1;"></i><br>현재 등록된 상품이 없습니다.
            </div>
            {% endif %}
        </div>
    </div>

    <div id="p-chat" class="page">
        <div id="chat-list-view">
            <div id="friend-requests-section" style="display:none; margin-bottom: 20px;">
                <h3 style="color:var(--warning); margin-bottom: 10px; font-size: 1.1rem;"><i class="fas fa-user-clock"></i> 받은 친구 요청 대기열</h3>
                <div id="friend-requests-container"></div>
            </div>

            <div style="display:flex; gap:10px; margin-bottom:20px;">
                <button class="btn btn-primary" style="flex:1; margin:0; padding:12px;" onclick="toggleChatCreate('dm')"><i class="fas fa-user-plus"></i> 친구추가</button>
                <button class="btn btn-info" style="flex:1; margin:0; padding:12px;" onclick="toggleChatCreate('group')"><i class="fas fa-users"></i> 단톡방</button>
                <button class="btn btn-success" style="flex:1; margin:0; padding:12px;" onclick="toggleChatCreate('channel')"><i class="fas fa-globe"></i> 채널개설</button>
            </div>

            <div id="create-dm" class="card chat-create-form" style="display:none; background:#eff6ff; border-color:#bfdbfe;">
                <h3 style="margin-bottom:15px; color:#1e3a8a;"><i class="fas fa-envelope"></i> 친구 요청 보내기</h3>
                <p style="font-size:0.85rem; color:#3b82f6; margin-bottom:10px;">상대방이 요청을 받아야지만 메시지를 보낼 수 있습니다.</p>
                <div style="display:flex; gap:10px;">
                    <input type="text" id="friend-id-input" placeholder="친구의 아이디 입력" style="margin:0;">
                    <button type="button" class="btn btn-primary" style="width:100px; margin:0;" onclick="sendFriendRequest()">요청</button>
                </div>
            </div>

            <div id="create-group" class="card chat-create-form" style="display:none; background:#ecfeff; border-color:#a5f3fc;">
                <h3 style="margin-bottom:15px; color:#164e63;"><i class="fas fa-users"></i> 새로운 단톡방 개설</h3>
                <input type="text" id="group-name" placeholder="단톡방 이름 (예: 코딩 스터디방)">
                <input type="text" id="group-users" placeholder="초대할 유저 아이디 (쉼표(,)로 구분)" style="margin-bottom:10px;">
                <button type="button" class="btn btn-info" style="margin:0;" onclick="createGroupChat()">단톡방 만들기</button>
            </div>

            <div id="create-channel" class="card chat-create-form" style="display:none; background:#f0fdf4; border-color:#bbf7d0;">
                <h3 style="margin-bottom:15px; color:#14532d;"><i class="fas fa-globe"></i> 누구나 참여 가능한 채널 개설</h3>
                <div style="display:flex; gap:10px;">
                    <input type="text" id="channel-name" placeholder="채널 이름 (예: 자유 소통 채널)" style="margin:0;">
                    <button type="button" class="btn btn-success" style="width:120px; margin:0;" onclick="createChannel()">개설</button>
                </div>
            </div>

            <h3 style="margin: 25px 0 15px; padding-left:10px; font-size:1.3rem; display:flex; align-items:center; gap:8px;"><i class="fas fa-comments text-primary"></i> 나의 채팅 목록</h3>
            <div id="chat-rooms-container"></div>
        </div>

        <div id="chat-room-view" class="chat-window">
            <div class="chat-header">
                <div style="display:flex; align-items:center; gap:15px; overflow:hidden;">
                    <button type="button" onclick="closeChat()" style="background:none; border:none; color:white; font-size:1.4rem; cursor:pointer; padding:5px; transition:0.2s;"><i class="fas fa-arrow-left"></i></button>
                    <div style="display:flex; flex-direction:column;">
                        <span id="chat-target-name" style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-size:1.2rem; font-weight:900;">상대방 이름</span>
                        <span id="chat-room-badge" style="font-size:0.75rem; background:rgba(0,0,0,0.2); padding:3px 8px; border-radius:10px; width:fit-content; margin-top:3px;"></span>
                    </div>
                </div>
                {% if session.get('role') == 'admin' %}
                <button type="button" onclick="deleteChatRoom()" style="background:rgba(255,255,255,0.2); border:none; color:white; width:40px; height:40px; border-radius:50%; font-size:1.1rem; cursor:pointer; transition:0.2s;" title="관리자 권한으로 방 삭제"><i class="fas fa-trash"></i></button>
                {% endif %}
            </div>
            
            <div class="chat-messages" id="chat-messages">
                </div>
            
            <div class="chat-input-area">
                <button type="button" style="background:#f1f5f9; border:none; width:45px; height:45px; border-radius:50%; color:var(--text-sub); font-size:1.2rem; cursor:pointer;"><i class="fas fa-plus"></i></button>
                <input type="text" id="chat-input" placeholder="메시지 또는 명령어 입력 (/명령어)" style="margin:0; border-radius:25px; border:2px solid var(--border); padding:15px 20px; font-weight:bold; flex-grow:1;" onkeypress="if(event.key==='Enter') sendChat()">
                <button type="button" class="btn btn-primary" style="width:50px; height:50px; margin:0; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow: 0 4px 10px rgba(99,102,241,0.3);" onclick="sendChat()"><i class="fas fa-paper-plane"></i></button>
            </div>
        </div>
    </div>

    <div id="p-settings" class="page">
        <div class="card" style="border: 2px dashed var(--primary); background:#e0e7ff;">
            <div class="card-title text-primary" style="color:#3730a3;"><i class="fas fa-ticket-alt"></i> 특별 쿠폰 등록</div>
            <div style="display:flex; gap:10px;">
                <input type="text" id="cp-code" placeholder="발급받은 비밀 쿠폰 코드를 입력하세요" style="margin-bottom:0; border-color:#a5b4fc; background:white;">
                <button type="button" class="btn btn-primary" style="width:120px; margin-bottom:0;" onclick="useCoupon()">사용하기</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title"><i class="fas fa-user-edit"></i> 내 프로필 최적화 설정</div>
            <label style="font-size:0.9rem; font-weight:bold; color:var(--text-main); margin-bottom:8px; display:block;">닉네임 (게시판/채팅 표시용)</label>
            <input type="text" id="set-nick" value="{{ session.get('nick') }}">
            
            <label style="font-size:0.9rem; font-weight:bold; color:var(--text-main); margin-bottom:8px; display:block;">프로필 사진 URL (웹상의 이미지 주소)</label>
            <input type="text" id="set-pfp" value="{{ session.get('pfp') }}" placeholder="https://...">
            
            <button type="button" class="btn btn-primary" onclick="updateInfo('profile')"><i class="fas fa-save"></i> 프로필 정보 저장하기</button>
            
            <hr style="border:0; border-top:1px dashed var(--border); margin:30px 0;">
            
            <label style="font-size:0.9rem; font-weight:bold; color:var(--danger); margin-bottom:8px; display:block;"><i class="fas fa-lock"></i> 보안 비밀번호 변경</label>
            <input type="password" id="set-pw" placeholder="새롭게 사용할 비밀번호 입력">
            <button type="button" class="btn" style="background:#334155; color:white; box-shadow:none;" onclick="updateInfo('pw')">비밀번호 안전하게 변경</button>
        </div>
        <button type="button" class="btn" style="background:#f1f5f9; color:var(--danger); margin-top:15px; font-weight:900; border:2px solid #e2e8f0;" onclick="location.href='/logout'"><i class="fas fa-sign-out-alt"></i> 시스템 전체 로그아웃</button>
    </div>

    <div id="p-inventory" class="page">
        <div class="card" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color:white; border:none; text-align:center; padding: 40px 20px;">
            <i class="fas fa-box-open" style="font-size: 4rem; color: #fbbf24; margin-bottom: 15px; filter: drop-shadow(0 0 15px rgba(251, 191, 36, 0.4));"></i>
            <h2 style="font-size: 1.8rem; margin-bottom: 10px;">나의 보관함 (인벤토리)</h2>
            <p style="color: #94a3b8; font-size: 1.05rem;">룰렛 당첨 상품이나 특별한 아이템들이 이곳에 안전하게 보관됩니다.<br>아이템 사용은 관리자 승인 후 처리됩니다.</p>
        </div>
        
        <div class="card">
            <h3 style="margin-bottom: 20px; display:flex; align-items:center; gap:10px;"><i class="fas fa-list text-primary"></i> 보유 아이템 목록</h3>
            <div id="inventory-container" class="inventory-grid">
            </div>
        </div>
    </div>

    {% if session.get('role') == 'admin' %}
    <div id="p-admin" class="page">
        
        <div class="card" style="border:2px solid #8b5cf6; background:#f5f3ff;">
            <h2 style="color:#6d28d9; margin-bottom:15px; font-size:1.3rem; display:flex; align-items:center; gap:8px;"><i class="fas fa-fighter-jet"></i> 관리자 강제 아이템 전송기</h2>
            <p style="font-size:0.85rem; color:#5b21b6; margin-bottom:15px;">유저 ID를 입력하여 원하는 아이템을 즉시 인벤토리에 꽂아줍니다.</p>
            <input type="text" id="adm-give-uid" placeholder="지급받을 타겟 유저 ID" style="border-color:#ddd6fe;">
            <input type="text" id="adm-give-item" placeholder="지급할 아이템 이름 (예: VIP 야외권, 스페셜 박스)" style="border-color:#ddd6fe;">
            <button type="button" class="btn" style="background:linear-gradient(135deg, #8b5cf6, #6d28d9); color:white;" onclick="giveItemToUser()"><i class="fas fa-bolt"></i> 아이템 즉시 전송</button>
        </div>

        <div class="card" style="border:2px solid var(--warning); background:#fffbeb;">
            <h2 style="color:var(--warning); margin-bottom:15px; font-size:1.3rem; display:flex; align-items:center; gap:8px;"><i class="fas fa-gavel"></i> 룰렛 당첨 지급 승인 대기열</h2>
            <p style="font-size:0.85rem; color:#b45309; margin-bottom:15px;">유저가 룰렛에서 당첨된 내역입니다. 승인 시 인벤토리로 즉시 전송됩니다.</p>
            <div id="approval-list" style="display:flex; flex-direction:column; gap:10px;"></div>
            <button type="button" class="btn btn-warning" style="margin-top:15px;" onclick="loadApprovals()"><i class="fas fa-sync-alt"></i> 목록 새로고침</button>
        </div>

        <div class="card" style="border:2px solid var(--info); background:#eff6ff;">
            <h2 style="color:var(--info); margin-bottom:15px; font-size:1.3rem; display:flex; align-items:center; gap:8px;"><i class="fas fa-magic"></i> 아이템 사용 승인 대기열</h2>
            <p style="font-size:0.85rem; color:#1e40af; margin-bottom:15px;">유저가 인벤토리에서 '사용하기'를 누른 아이템 내역입니다.</p>
            <div id="item-use-approval-list" style="display:flex; flex-direction:column; gap:10px;"></div>
            <button type="button" class="btn btn-info" style="margin-top:15px;" onclick="loadItemUseApprovals()"><i class="fas fa-sync-alt"></i> 아이템 대기열 새로고침</button>
        </div>

        <div class="card" style="background:#fff1f2; border:2px solid var(--danger);">
            <h2 style="color:var(--danger); margin-bottom:20px; font-size:1.4rem; font-weight:900;"><i class="fas fa-cogs"></i> V28 관리자 코어 시스템</h2>
            
            <div style="background:white; padding:20px; border-radius:15px; margin-bottom:25px; border:2px solid var(--border); box-shadow:var(--shadow-sm);">
                <h3 style="font-size:1.15rem; margin-bottom:15px; color:var(--primary);"><i class="fas fa-terminal"></i> 대형 임베드 지원 명령어 (채팅방 입력)</h3>
                <ul style="font-size:0.95rem; color:var(--text-main); line-height:1.8; padding-left:25px; font-weight:500;">
                    <li><b style="color:var(--primary);">/아이템전송 [유저ID] [아이템이름]</b> : 타겟 유저 인벤토리로 강제 전송</li>
                    <li><b style="color:var(--danger);">/기록삭제</b> : 서버 전체의 실시간 거래 기록 완전 삭제</li>
                    <li><b style="color:var(--success);">/캐시지급 [수량]</b> & <b style="color:#ef4444;">/캐시차감 [수량]</b> : 자금 조정</li>
                    <li><b>/구매완료</b> : 거래 종료, 별점/리뷰 유도 임베드 생성</li>
                    <li><b>/거래완료</b> : 실시간 거래기록 등재</li>
                    <li><b>/로벅스 계산기 [로벅스]</b> : 환율(1:10) 자동 계산 출력</li>
                    <li><b>/공지 [내용]</b> & <b>/경고 [내용]</b> : 대형 공지/경고 임베드 전송</li>
                </ul>
            </div>

            <h3 style="font-size:1.1rem; margin:15px 0 10px;">🎁 출석체크 보상금액 설정</h3>
            <input type="number" id="adm-att-rew" value="{{ sys.att_reward }}" placeholder="1일 출석 보상 캐시량">

            <h3 style="font-size:1.1rem; margin:25px 0 10px;">🔧 네비게이션 탭 이름 커스터마이징</h3>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:15px;">
                <input type="text" id="adm-m1" value="{{ sys.m1 }}">
                <input type="text" id="adm-m2" value="{{ sys.m2 }}">
                <input type="text" id="adm-m3" value="{{ sys.m3 }}">
                <input type="text" id="adm-m4" value="{{ sys.m4 }}">
                <input type="text" id="adm-m5" value="{{ sys.m5 }}">
                <input type="text" id="adm-m6" value="{{ sys.m6 }}">
                <input type="text" id="adm-m7" value="{{ sys.m7 }}" style="grid-column: 1/-1;">
            </div>
            
            <h3 style="font-size:1.1rem; margin:25px 0 10px;">🎯 룰렛 상품 및 확률 (합 100% 필수)</h3>
            <label style="font-size:0.9rem; font-weight:bold;">1회 참여 비용 (캐시)</label>
            <input type="number" id="adm-rcost" value="{{ sys.roulette_cost }}">
            <div style="display:grid; grid-template-columns: 2fr 1fr; gap:10px; margin-bottom:15px; background:white; padding:15px; border-radius:12px;">
                <input type="text" id="adm-r-i1" value="{{ sys.r_i1 }}"><input type="number" id="adm-r-p1" value="{{ sys.r_p1 }}">
                <input type="text" id="adm-r-i2" value="{{ sys.r_i2 }}"><input type="number" id="adm-r-p2" value="{{ sys.r_p2 }}">
                <input type="text" id="adm-r-i3" value="{{ sys.r_i3 }}"><input type="number" id="adm-r-p3" value="{{ sys.r_p3 }}">
                <input type="text" id="adm-r-i4" value="{{ sys.r_i4 }}"><input type="number" id="adm-r-p4" value="{{ sys.r_p4 }}">
                <input type="text" id="adm-r-i5" value="{{ sys.r_i5 }}"><input type="number" id="adm-r-p5" value="{{ sys.r_p5 }}">
                <input type="text" id="adm-r-i6" value="{{ sys.r_i6 }}"><input type="number" id="adm-r-p6" value="{{ sys.r_p6 }}">
            </div>

            <label style="font-size:0.9rem; font-weight:bold; margin-top:10px; display:block;">접속 팝업 공지 내용</label>
            <textarea id="adm-popup" rows="4">{{ sys.popup_notice }}</textarea>
            <button type="button" class="btn btn-danger" onclick="saveSys()" style="font-size:1.1rem; padding:18px;"><i class="fas fa-save"></i> 코어 시스템 설정 덮어쓰기</button>

            <hr style="margin:30px 0; border:0; border-top:2px dashed var(--danger); opacity:0.3;">
            
            <h3 style="font-size:1.1rem; margin-bottom:15px;">🛠️ 프리미엄 상점 상품 추가/관리</h3>
            <input type="hidden" id="shop-id">
            <input type="text" id="shop-title" placeholder="상품 이름 (예: VIP 권한, 특급 무기)">
            <input type="number" id="shop-price" placeholder="가격 (캐시)">
            <textarea id="shop-desc" placeholder="상품 상세 설명" rows="3"></textarea>
            <input type="text" id="shop-img" placeholder="상품 이미지 URL (선택사항, https://...)">
            <button type="button" class="btn btn-success" onclick="saveShopItem()"><i class="fas fa-plus-circle"></i> 상점 카탈로그에 등록</button>
            
            <div style="background:white; padding:15px; border-radius:12px; border:1px solid var(--border); margin-top:15px;">
                {% for item in shop_items %}
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid #f1f5f9; padding-bottom:10px;">
                    <span style="font-weight:bold;">{{ item.title }} <span style="color:var(--danger);">({{ item.price }}c)</span></span>
                    <button type="button" onclick="delShopItem('{{ item.id }}')" style="color:white; background:var(--danger); padding:6px 12px; border-radius:8px; border:none; cursor:pointer;"><i class="fas fa-trash"></i></button>
                </div>
                {% endfor %}
            </div>

            <hr style="margin:30px 0; border:0; border-top:2px dashed var(--danger); opacity:0.3;">
            <h3 style="font-size:1.1rem; margin-bottom:15px;">🎟️ 자금/이벤트 쿠폰 발전기</h3>
            <div style="display:flex; gap:10px;">
                <input type="text" id="adm-c-code" placeholder="쿠폰 코드" style="margin:0;">
                <input type="number" id="adm-c-rew" placeholder="지급 캐시" style="margin:0; width:120px;">
                <button type="button" class="btn btn-primary" style="margin:0; width:100px;" onclick="makeCoupon()">생성</button>
            </div>

            <h3 style="font-size:1.1rem; margin:30px 0 15px;">📢 메인 공지사항 쾌속 등록기</h3>
            <input type="text" id="adm-n-title" placeholder="공지 제목">
            <textarea id="adm-n-content" rows="4" placeholder="공지 내용 (HTML 태그 허용)"></textarea>
            <input type="text" id="adm-n-img" placeholder="첨부 이미지 URL (선택)">
            <button type="button" class="btn btn-primary" onclick="addNotice()">공지사항 라이브 송출</button>

            <h3 style="font-size:1.1rem; margin:30px 0 15px;">👤 유저 제재 및 자산 제어 패널</h3>
            <input type="text" id="adm-u-id" placeholder="타겟 대상 유저 아이디 (정확히 입력)">
            <input type="number" id="adm-u-cash" placeholder="지급/차감할 캐시 액수">
            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                <button type="button" class="btn btn-success" style="flex:1;" onclick="ctrlUser('give')"><i class="fas fa-hand-holding-usd"></i> 지급</button>
                <button type="button" class="btn btn-danger" style="flex:1;" onclick="ctrlUser('block')"><i class="fas fa-ban"></i> 차단</button>
                <button type="button" class="btn" style="background:#64748b; color:white; flex:1; box-shadow:none;" onclick="ctrlUser('unblock')"><i class="fas fa-unlock"></i> 해제</button>
            </div>
        </div>
    </div>
    {% endif %}
</div>

<nav class="bottom-nav">
    <a class="nav-item" onclick="nav('home', this)"><i class="fas fa-home"></i> <span>{{ sys.m1 }}</span></a>
    <a class="nav-item" onclick="nav('board', this)"><i class="fas fa-list-alt"></i> <span>{{ sys.m2 }}</span></a>
    <a class="nav-item" onclick="nav('roulette', this)"><i class="fas fa-gamepad"></i> <span>{{ sys.m3 }}</span></a>
    <a class="nav-item" onclick="nav('shop', this)"><i class="fas fa-shopping-bag"></i> <span>{{ sys.m4 }}</span></a>
    <a class="nav-item" onclick="nav('chat', this)"><i class="fas fa-comment-dots"></i> <span>{{ sys.m5 }}</span></a>
    <a class="nav-item" onclick="nav('settings', this)"><i class="fas fa-cog"></i> <span>{{ sys.m6 }}</span></a>
    <a class="nav-item" onclick="nav('inventory', this, true, true)"><i class="fas fa-box-open"></i> <span>{{ sys.m7 }}</span></a>
    {% if session.get('role') == 'admin' %}
    <a class="nav-item" onclick="nav('admin', this)"><i class="fas fa-crown"></i> <span>관리자</span></a>
    {% endif %}
</nav>

<div class="modal" id="spin-alert-modal" onclick="this.classList.remove('active'); location.reload();">
    <h2 style="font-size:2rem; margin-bottom:10px;">🎰 스핀 완료!</h2>
    <h1 id="spin-alert-text" style="color:var(--primary); text-shadow:0 0 10px rgba(255,255,255,0.5);">상품</h1>
    <p style="margin-top:20px; font-size:1.1rem; color:#cbd5e1;">당첨된 아이템은 관리자에게 승인 문자가 전송되었습니다.<br>승인 후 인벤토리에 들어옵니다!</p>
    <p style="margin-top:30px; font-size:1rem; opacity:0.6;">화면을 터치하여 닫기</p>
</div>

<script>
    let currentChatRoomId = null;
    let chatSyncTimer = null;
    let myUserId = '{{ session.get("user") }}';
    let lastMsgCount = 0; 
    const isAdmin = '{{ session.get("role") }}' === 'admin';

    window.addEventListener('DOMContentLoaded', () => {
        if(!sessionStorage.getItem('popup_seen_v28')) {
            const popup = document.getElementById('welcome-popup');
            popup.style.display = 'flex';
            popup.classList.add('active');
            sessionStorage.setItem('popup_seen_v28', 'true');
        }
        const savedTab = sessionStorage.getItem('current_tab') || 'home';
        const navEl = document.querySelector(`.nav-item[onclick*="${savedTab}"]`);
        if(navEl) {
            if(savedTab === 'inventory') nav('inventory', navEl, false, true);
            else nav(savedTab, navEl, false);
        } else {
            document.getElementById('p-home').classList.add('active');
            document.querySelector('.nav-item').classList.add('active');
        }
        if(isAdmin) { loadApprovals(); loadItemUseApprovals(); }
    });

    function closePopup() { document.getElementById('welcome-popup').style.display = 'none'; }

    async function req(url, data) {
        try {
            const res = await fetch(url, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
            return await res.json();
        } catch(e) { return {ok: false, msg: "서버 통신 오류 발생 (네트워크 확인)"}; }
    }

    function nav(pageId, el, doScroll=true, loadInv=false) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const targetPage = document.getElementById('p-' + pageId);
        if(targetPage) targetPage.classList.add('active');
        
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        if(el) el.classList.add('active');
        sessionStorage.setItem('current_tab', pageId); 
        
        if(doScroll) window.scrollTo({top:0, behavior:'smooth'});
        if(pageId === 'roulette') drawRoulette();
        if(pageId === 'chat') { loadChatRooms(); loadFriendRequests(); } else { closeChat(); }
        if(loadInv) fetchInventory();
        if(pageId === 'admin') { loadApprovals(); loadItemUseApprovals(); }
    }

    // [신규] 출석체크 호출
    async function checkAttendance() {
        const btn = document.getElementById('btn-attendance');
        btn.disabled = true;
        const r = await req('/api/attendance', {});
        alert(r.msg);
        if(r.ok) location.reload();
        btn.disabled = false;
    }

    // [신규] 관리자 강제 아이템 전송기 호출
    async function giveItemToUser() {
        const uid = document.getElementById('adm-give-uid').value;
        const item = document.getElementById('adm-give-item').value;
        if(!uid || !item) return alert("유저ID와 아이템 이름을 모두 입력하세요.");
        if(!confirm(`[${uid}] 님에게 [${item}] 아이템을 강제로 지급하시겠습니까?`)) return;
        
        const r = await req('/api/admin/give_item', {uid: uid, item: item});
        alert(r.msg);
        if(r.ok) { document.getElementById('adm-give-item').value = ''; }
    }

    // --- 이하 기존 JS 그대로 ---
    function formatText(id, tag) {
        const el = document.getElementById(id);
        const start = el.selectionStart, end = el.selectionEnd, txt = el.value;
        if(start === end) return alert("글씨를 먼저 드래그하여 선택한 뒤 버튼을 눌러주세요!");
        el.value = txt.substring(0, start) + `<${tag}>` + txt.substring(start, end) + `</${tag}>` + txt.substring(end);
    }
    function formatColor(id) {
        const c = prompt("글씨 색상을 영어 또는 헥스코드로 입력하세요 (예: red, blue, #ff0000)", "#ef4444");
        if(!c) return;
        const el = document.getElementById(id);
        const start = el.selectionStart, end = el.selectionEnd, txt = el.value;
        if(start === end) return alert("글씨를 드래그하여 선택해주세요!");
        el.value = txt.substring(0, start) + `<span style="color:${c}; font-weight:bold;">` + txt.substring(start, end) + `</span>` + txt.substring(end);
    }
    function searchBoard() {
        const q = document.getElementById('search-box').value.toLowerCase();
        document.querySelectorAll('.post').forEach(el => {
            const title = el.querySelector('.p-title').innerText.toLowerCase();
            const desc = el.querySelector('.p-desc').innerText.toLowerCase();
            el.style.display = (title.includes(q) || desc.includes(q)) ? 'block' : 'none';
        });
    }
    async function submitPost() {
        const t = document.getElementById('post-title').value;
        const c = document.getElementById('post-content').value;
        if(!t || !c) return alert("게시물 제목과 내용을 완벽히 작성해주세요.");
        const r = await req('/api/post', {title: t, content: c});
        if(r.ok) location.reload();
    }
    async function actPost(type, idx) {
        const r = await req('/api/action', {type: type, idx: idx});
        if(r.ok) location.reload(); else alert(r.msg);
    }
    async function pinPost(idx) {
        const r = await req('/api/pin', {idx: idx});
        if(r.ok) location.reload();
    }
    async function delContent(type, idx) {
        if(confirm("데이터를 영구 삭제하시겠습니까?")){
            const r = await req('/api/delete', {type: type, idx: idx});
            if(r.ok) location.reload();
        }
    }
    async function updateInfo(mode) {
        const data = {mode: mode};
        if(mode === 'profile'){ 
            data.nick = document.getElementById('set-nick').value;
            data.pfp = document.getElementById('set-pfp').value; 
        } else { 
            data.pw = document.getElementById('set-pw').value;
            if(!data.pw) return alert("비밀번호를 입력해주세요."); 
        }
        const r = await req('/api/update', data);
        alert(r.msg); if(r.ok) location.reload();
    }
    async function useCoupon() {
        const code = document.getElementById('cp-code').value;
        if(!code) return alert("쿠폰 코드가 비어있습니다.");
        const r = await req('/api/coupon/use', {code: code});
        alert(r.msg); if(r.ok) location.reload();
    }

    async function saveSys() {
        const d = {
            rcost: document.getElementById('adm-rcost').value, 
            att_reward: document.getElementById('adm-att-rew').value, 
            m1: document.getElementById('adm-m1').value, m2: document.getElementById('adm-m2').value, 
            m3: document.getElementById('adm-m3').value, m4: document.getElementById('adm-m4').value, 
            m5: document.getElementById('adm-m5').value, m6: document.getElementById('adm-m6').value, m7: document.getElementById('adm-m7').value,
            popup: document.getElementById('adm-popup').value
        };
        for(let i=1; i<=6; i++) {
            d[`r_i${i}`] = document.getElementById(`adm-r-i${i}`).value;
            d[`r_p${i}`] = document.getElementById(`adm-r-p${i}`).value;
        }
        const r = await req('/api/admin/sys', d);
        alert(r.msg); if(r.ok) location.reload();
    }
    async function makeCoupon() {
        const r = await req('/api/admin/coupon', { code: document.getElementById('adm-c-code').value, rew: document.getElementById('adm-c-rew').value });
        alert(r.msg);
    }
    async function addNotice() {
        const r = await req('/api/admin/notice', { t: document.getElementById('adm-n-title').value, c: document.getElementById('adm-n-content').value, i: document.getElementById('adm-n-img').value });
        if(r.ok) { alert("공지 등록 완료!"); location.reload(); }
    }
    async function ctrlUser(act) {
        const r = await req('/api/admin/user', { act: act, id: document.getElementById('adm-u-id').value, cash: document.getElementById('adm-u-cash').value });
        alert(r.msg);
    }

    const prizes = ["{{ sys.r_i1 }}", "{{ sys.r_i2 }}", "{{ sys.r_i3 }}", "{{ sys.r_i4 }}", "{{ sys.r_i5 }}", "{{ sys.r_i6 }}"];
    const colors = ["#4f46e5", "#e2e8f0", "#ef4444", "#cbd5e1", "#f59e0b", "#94a3b8"];
    function drawRoulette() {
        const canvas = document.getElementById("roulette-canvas");
        const ctx = canvas.getContext("2d");
        const arc = (2 * Math.PI) / prizes.length;
        for(let i=0; i<prizes.length; i++) {
            ctx.beginPath(); ctx.fillStyle = colors[i];
            ctx.moveTo(160, 160);
            ctx.arc(160, 160, 160, i*arc, (i+1)*arc); ctx.fill();
            ctx.save(); ctx.fillStyle = (i%2===0) ? "white" : "#1e293b";
            ctx.font = "bold 18px Pretendard";
            ctx.translate(160 + Math.cos(i*arc + arc/2)*100, 160 + Math.sin(i*arc + arc/2)*100);
            ctx.rotate(i*arc + arc/2 + Math.PI/2);
            ctx.fillText(prizes[i], -ctx.measureText(prizes[i]).width/2, 0);
            ctx.restore();
        }
    }
    async function spinRoulette() {
        const btn = document.getElementById('spin-btn');
        btn.disabled = true; btn.innerText = "운명의 수레바퀴 도는 중...";
        const r = await req('/api/spin', {});
        if(r.error) { alert(r.error); btn.disabled = false; btn.innerHTML = '<i class="fas fa-play"></i> 돌리기 (캐시 차감)'; return; }
        
        const winIdx = prizes.indexOf(r.res);
        const rot = (360 * 15) + (360 - (winIdx * 60)) - 90; 
        document.getElementById('roulette-canvas').style.transform = `rotate(${rot}deg)`;
        setTimeout(() => {
            if(r.res !== "꽝") {
                confetti({ particleCount: 300, spread: 120, origin: { y: 0.6 }, zIndex: 10000 });
                document.getElementById('spin-alert-text').innerText = `[${r.res}] 당첨!`;
                document.getElementById('spin-alert-modal').style.display = 'flex';
                document.getElementById('spin-alert-modal').classList.add('active');
            } else { 
                alert("앗! 꽝입니다! 확률은 잔인하지만 다음 기회를 노려보세요!"); location.reload(); 
            }
        }, 5100);
    }

    async function loadApprovals() {
        if(!isAdmin) return;
        const r = await req('/api/admin/approvals_list', {});
        if(!r.ok) return;
        const cont = document.getElementById('approval-list');
        if(r.data.length === 0) {
            cont.innerHTML = '<div style="text-align:center; padding:15px; background:white; border-radius:10px; color:var(--text-sub);">대기 중인 당첨 내역이 없습니다.</div>';
            return;
        }
        let html = '';
        r.data.forEach((item) => {
            html += `
            <div style="background:white; border:1px solid #fcd34d; padding:15px; border-radius:12px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:900; font-size:1.1rem;">${item.user}</div>
                    <div style="color:var(--danger); font-weight:bold;">🎁 ${item.item}</div>
                    <div style="font-size:0.75rem; color:var(--text-sub);">${item.date}</div>
                </div>
                <div style="display:flex; flex-direction:column; gap:5px;">
                    <button class="btn btn-success" style="padding:10px 15px; margin:0;" onclick="handleApproval('${item.id}', true)">수령 승인</button>
                    <button class="btn btn-danger" style="padding:10px 15px; margin:0;" onclick="handleApproval('${item.id}', false)">거절(삭제)</button>
                </div>
            </div>`;
        });
        cont.innerHTML = html;
    }
    async function handleApproval(aid, isApprove) {
        if(!confirm(isApprove ? "해당 유저의 인벤토리로 아이템을 전송합니까?" : "승인을 거절하고 삭제합니까?")) return;
        const r = await req('/api/admin/approve_roulette', { id: aid, approve: isApprove });
        alert(r.msg); if(r.ok) loadApprovals();
    }

    async function loadItemUseApprovals() {
        if(!isAdmin) return;
        const r = await req('/api/admin/item_use_list', {});
        if(!r.ok) return;
        const cont = document.getElementById('item-use-approval-list');
        if(r.data.length === 0) {
            cont.innerHTML = '<div style="text-align:center; padding:15px; background:white; border-radius:10px; color:var(--text-sub);">대기 중인 요청이 없습니다.</div>';
            return;
        }
        let html = '';
        r.data.forEach((req_item) => {
            html += `
            <div style="background:white; border:1px solid #93c5fd; padding:15px; border-radius:12px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:900; font-size:1.1rem;">${req_item.user}</div>
                    <div style="color:var(--info); font-weight:bold;">🪄 사용 요청: ${req_item.item_name}</div>
                    <div style="font-size:0.75rem; color:var(--text-sub);">${req_item.date}</div>
                </div>
                <div style="display:flex; flex-direction:column; gap:5px;">
                    <button class="btn btn-primary" style="padding:10px 15px; margin:0;" onclick="handleItemUseApproval('${req_item.req_id}', true)">사용 승인</button>
                    <button class="btn btn-outline" style="padding:10px 15px; margin:0; border:1px solid var(--danger); color:var(--danger);" onclick="handleItemUseApproval('${req_item.req_id}', false)">거부</button>
                </div>
            </div>`;
        });
        cont.innerHTML = html;
    }
    async function handleItemUseApproval(reqId, isApprove) {
        if(!confirm(isApprove ? "아이템 사용을 승인하시겠습니까?" : "거부하시겠습니까?")) return;
        const r = await req('/api/admin/approve_item_use', { req_id: reqId, approve: isApprove });
        alert(r.msg); if(r.ok) loadItemUseApprovals();
    }

    async function saveShopItem() {
        const data = {
            title: document.getElementById('shop-title').value, price: document.getElementById('shop-price').value,
            desc: document.getElementById('shop-desc').value, img: document.getElementById('shop-img').value
        };
        if(!data.title || !data.price) return alert("필수값을 채워주세요.");
        const r = await req('/api/shop/add', data);
        if(r.ok) { alert("등록 완료!"); location.reload(); }
    }
    async function delShopItem(id) {
        if(!confirm("영구 삭제하시겠습니까?")) return;
        const r = await req('/api/shop/del', {id: id});
        if(r.ok) location.reload();
    }
    async function buyItem(id, title, price) {
        if(!confirm(`[${title}] 구매 확정 (대금: ${price})`)) return;
        const r = await req('/api/shop/buy', {id: id});
        if(r.ok) { alert("결제 완료! 채팅 탭에서 거래를 진행하세요."); location.reload(); } else { alert(r.msg); }
    }

    async function fetchInventory() {
        const r = await req('/api/inventory/list', {});
        const box = document.getElementById('inventory-container');
        if(!r.ok || r.items.length === 0) {
            box.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:40px; background:white; border-radius:15px; border:1px solid var(--border); color:var(--text-sub);">인벤토리가 텅 비어있습니다.</div>';
            return;
        }
        let html = '';
        r.items.forEach(item => {
            html += `
            <div class="inv-item">
                <i class="fas fa-gift inv-icon"></i>
                <div class="inv-name">${item.name}</div>
                <div class="inv-date">${item.date}</div>
                <button class="btn-use-item" onclick="useInventoryItem('${item.id}', '${item.name}')">사용하기</button>
            </div>`;
        });
        box.innerHTML = html;
    }
    async function useInventoryItem(itemId, itemName) {
        if(!confirm(`[${itemName}] 아이템을 사용하시겠습니까? (승인 후 소진)`)) return;
        const r = await req('/api/inventory/use_request', { item_id: itemId });
        alert(r.msg); if(r.ok) fetchInventory();
    }

    function toggleChatCreate(type) {
        document.querySelectorAll('.chat-create-form').forEach(el => el.style.display = 'none');
        document.getElementById(`create-${type}`).style.display = 'block';
    }
    async function sendFriendRequest() {
        const fid = document.getElementById('friend-id-input').value.trim();
        if(!fid) return alert("아이디 입력");
        const r = await req('/api/friend/add_request', {friend_id: fid});
        alert(r.msg); if(r.ok) document.getElementById('friend-id-input').value = '';
    }
    async function loadFriendRequests() {
        const r = await req('/api/friend/list_requests', {});
        if(!r.ok) return;
        const section = document.getElementById('friend-requests-section');
        const cont = document.getElementById('friend-requests-container');
        if(r.requests.length === 0) { section.style.display = 'none'; return; }
        section.style.display = 'block';
        let html = '';
        r.requests.forEach(reqObj => {
            html += `
            <div class="friend-req-card">
                <div class="info"><i class="fas fa-user-circle" style="font-size:2rem; color:var(--primary);"></i>
                    <div><div style="font-weight:900; font-size:1.1rem; color:var(--text-main);">${reqObj.sender_nick}</div><div style="font-size:0.8rem; color:var(--text-sub);">ID: ${reqObj.sender}님이 요청</div></div>
                </div>
                <div class="actions">
                    <button class="btn btn-success" style="padding:8px 12px; margin:0;" onclick="handleFriendRequest('${reqObj.req_id}', true)"><i class="fas fa-check"></i></button>
                    <button class="btn btn-danger" style="padding:8px 12px; margin:0;" onclick="handleFriendRequest('${reqObj.req_id}', false)"><i class="fas fa-times"></i></button>
                </div>
            </div>`;
        });
        cont.innerHTML = html;
    }
    async function handleFriendRequest(reqId, isAccept) {
        const r = await req('/api/friend/handle_request', { req_id: reqId, accept: isAccept });
        alert(r.msg); if(r.ok) { loadFriendRequests(); loadChatRooms(); }
    }
    async function createGroupChat() {
        const name = document.getElementById('group-name').value.trim();
        const usersStr = document.getElementById('group-users').value.trim();
        if(!name || !usersStr) return alert("입력 오류");
        const users = usersStr.split(',').map(s => s.trim());
        const r = await req('/api/chat/create_group', {name: name, users: users});
        alert(r.msg); if(r.ok) loadChatRooms();
    }
    async function createChannel() {
        const name = document.getElementById('channel-name').value.trim();
        if(!name) return;
        const r = await req('/api/chat/create_channel', {name: name});
        alert(r.msg); if(r.ok) loadChatRooms();
    }

    async function loadChatRooms() {
        const r = await req('/api/chat/list', {});
        if(!r.ok) return;
        const c = document.getElementById('chat-rooms-container');
        c.innerHTML = '';
        if(r.rooms.length === 0) {
            c.innerHTML = '<div style="text-align:center; color:#94a3b8; padding:40px; background:white; border-radius:15px; border:2px dashed var(--border);">개설된 채팅방이 없습니다.</div>';
            return;
        }
        r.rooms.forEach(rm => {
            let icon = '<i class="fas fa-user"></i>'; let title = rm.target_nick; let badge = '';
            if(rm.type === 'shop') { icon = '<i class="fas fa-shopping-bag"></i>'; title = `[거래망] ${rm.item_name}`; badge = '<span style="background:var(--danger);color:white;padding:3px 8px;border-radius:10px;font-size:0.7rem;margin-left:5px;font-weight:bold;">VVIP 전용</span>'; } 
            else if(rm.type === 'group') { icon = '<i class="fas fa-users"></i>'; title = rm.name; badge = '<span style="background:var(--info-grad);color:white;padding:3px 8px;border-radius:10px;font-size:0.7rem;margin-left:5px;">단톡방</span>'; } 
            else if(rm.type === 'channel') { icon = '<i class="fas fa-globe"></i>'; title = rm.name; badge = '<span style="background:var(--success-grad);color:white;padding:3px 8px;border-radius:10px;font-size:0.7rem;margin-left:5px;">공개 채널</span>'; }
            
            c.innerHTML += `
                <div class="channel-card" onclick="openChat('${rm.room_id}', '${title.replace(/'/g, "\\'")}', '${rm.type}')">
                    <div style="display:flex; align-items:center; width:100%;">
                        <div class="channel-icon">${icon}</div>
                        <div style="font-weight:900; font-size:1.1rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:65%;">${title}</div> ${badge}
                    </div>
                    <i class="fas fa-chevron-right" style="color:var(--text-sub); font-size:1.2rem;"></i>
                </div>`;
        });
    }
    function openChat(roomId, title, type) {
        currentChatRoomId = roomId; lastMsgCount = 0; 
        document.getElementById('chat-list-view').style.display = 'none';
        document.getElementById('chat-room-view').style.display = 'flex';
        document.getElementById('chat-target-name').innerText = title;
        let typeText = "1:1 대화";
        if(type==='shop') typeText="관리자 안전 거래망"; else if(type==='group') typeText="그룹 채팅"; else if(type==='channel') typeText="공개 커뮤니티 채널";
        document.getElementById('chat-room-badge').innerText = typeText;
        syncChat(); chatSyncTimer = setInterval(syncChat, 1500);
    }
    function closeChat() {
        currentChatRoomId = null; if(chatSyncTimer) clearInterval(chatSyncTimer);
        document.getElementById('chat-room-view').style.display = 'none';
        document.getElementById('chat-list-view').style.display = 'block';
    }
    async function deleteChatRoom() {
        if(!confirm("이 채널(방)을 삭제하시겠습니까?")) return;
        const r = await req('/api/chat/delete', {room_id: currentChatRoomId});
        if(r.ok) { alert("파괴 완료."); closeChat(); loadChatRooms(); }
    }
    async function sendChat() {
        const inp = document.getElementById('chat-input');
        const text = inp.value.trim();
        if(!text) return;
        inp.value = ''; 
        const r = await req('/api/chat/send', {room_id: currentChatRoomId, msg: text});
        if(r.ok) { syncChat(); } else { alert(r.msg); }
    }

    async function syncChat() {
        if(!currentChatRoomId) return;
        const r = await req('/api/chat/sync', {room_id: currentChatRoomId});
        if(!r.ok) { closeChat(); loadChatRooms(); return; } 
        
        if(lastMsgCount === r.messages.length) return;
        lastMsgCount = r.messages.length;

        const box = document.getElementById('chat-messages');
        const isAtBottom = box.scrollHeight - box.clientHeight <= box.scrollTop + 60;
        let html = '';
        
        r.messages.forEach(m => {
            /* 🔥 채팅 및 임베드 찌그러짐 방지를 위해 flex-shrink: 0 추가 */
            if(m.type === 'sys') {
                html += `<div class="sys-msg">${m.msg}</div>`;
            } else if(m.type === 'embed') {
                if(m.embed_type === 'review_request') {
                    html += `
                    <div class="super-embed embed-theme-warning">
                        <div class="embed-header"><i class="fas fa-shopping-bag" style="color:#d97706; font-size:1.5rem;"></i><div class="embed-author">시스템 관리자 전송 시스템</div></div>
                        <div class="embed-title">🎁 거래가 최종 완료되었습니다!</div>
                        <div class="embed-desc"><b>[${m.item_name}]</b> 상품의 인도가 끝났습니다. 아래에서 별점을 남겨주세요.</div>
                        <div class="star-rating" id="rating-${m.id}">
                            <input type="radio" id="star5-${m.id}" name="rate-${m.id}" value="5"><label for="star5-${m.id}"><i class="fas fa-star"></i></label>
                            <input type="radio" id="star4-${m.id}" name="rate-${m.id}" value="4"><label for="star4-${m.id}"><i class="fas fa-star"></i></label>
                            <input type="radio" id="star3-${m.id}" name="rate-${m.id}" value="3"><label for="star3-${m.id}"><i class="fas fa-star"></i></label>
                            <input type="radio" id="star2-${m.id}" name="rate-${m.id}" value="2"><label for="star2-${m.id}"><i class="fas fa-star"></i></label>
                            <input type="radio" id="star1-${m.id}" name="rate-${m.id}" value="1"><label for="star1-${m.id}"><i class="fas fa-star"></i></label>
                        </div>
                        <input type="text" class="review-input" id="rev-txt-${m.id}" placeholder="리뷰를 적어주세요!">
                        <button class="review-btn" onclick="submitReview('${m.item_name}', '${m.id}')"><i class="fas fa-upload"></i> 리뷰 업로드</button>
                    </div>`;
                } else if(m.embed_type === 'item_transfer') {
                    html += `
                    <div class="super-embed embed-theme-success">
                        <div class="embed-header"><i class="fas fa-gift" style="color:#059669; font-size:1.5rem;"></i><div class="embed-author">시스템 엔진 V28</div></div>
                        <div class="embed-title">${m.title}</div>
                        <div class="embed-desc">${m.desc}</div>
                        <div class="embed-footer"><i class="fas fa-check-circle"></i> 정상 처리됨</div>
                    </div>`;
                } else if(m.embed_type === 'alert') {
                    html += `
                    <div class="super-embed embed-theme-danger">
                        <div class="embed-header"><i class="fas fa-exclamation-triangle" style="color:#dc2626; font-size:1.5rem;"></i><div class="embed-author">최고 관리자 명령</div></div>
                        <div class="embed-title">${m.title}</div>
                        <div class="embed-desc" style="color:#7f1d1d; font-weight:bold;">${m.desc}</div>
                    </div>`;
                } else {
                    let theme = m.color === '#ef4444' ? 'embed-theme-danger' : (m.color === '#3b82f6' ? 'embed-theme-info' : 'embed-theme-success');
                    let icon = m.color === '#ef4444' ? 'fa-ban' : 'fa-bullhorn';
                    html += `
                    <div class="super-embed ${theme}">
                        <div class="embed-header"><i class="fas ${icon}" style="font-size:1.5rem;"></i><div class="embed-author">시스템 방송국</div></div>
                        <div class="embed-title">${m.title}</div>
                        <div class="embed-desc">${m.desc}</div>
                    </div>`;
                }
            } else {
                const isMe = m.sender === myUserId;
                const cls = isMe ? 'msg-self' : 'msg-other';
                const senderName = isMe ? '' : `<div style="font-size:0.8rem; font-weight:900; color:var(--text-main); margin-bottom:5px; padding-left:5px;">${m.sender_nick}</div>`;
                html += `<div style="display:flex; flex-direction:column; align-items:${isMe?'flex-end':'flex-start'}; margin-bottom:8px; flex-shrink:0;">${senderName}<div class="msg-bubble ${cls}">${m.msg}</div></div>`;
            }
        });
        
        box.innerHTML = html;
        if(isAtBottom || lastMsgCount <= 5) { box.scrollTop = box.scrollHeight; }
    }

    async function submitReview(itemName, embedId) {
        let rating = 0;
        const radios = document.getElementsByName(`rate-${embedId}`);
        for(let r of radios) { if(r.checked) { rating = parseInt(r.value); break; } }
        const txt = document.getElementById(`rev-txt-${embedId}`).value.trim();
        if(rating === 0) return alert("별점을 선택해주세요!");
        if(!txt) return alert("리뷰를 작성해주세요!");
        const r = await req('/api/review/add', {item_name: itemName, rating: rating, content: txt});
        if(r.ok) { alert("리뷰가 업로드되었습니다!"); location.reload(); }
    }
</script>
</body>
</html>
"""

AUTH_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Gongqn V28 보안 게이트웨이 (MongoDB)</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;500;700;900&display=swap" rel="stylesheet">
    <style>
        body { margin:0; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); font-family: 'Pretendard', sans-serif; height:100vh; display:flex; align-items:center; justify-content:center; overflow:hidden; }
        .box { background:rgba(255,255,255,0.95); padding:40px 30px; border-radius:24px; width:90%; max-width:400px; text-align:center; box-shadow:0 25px 50px -12px rgba(0,0,0,0.5); backdrop-filter: blur(15px); animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1); z-index:10; position:relative; }
        @keyframes slideUp { from { opacity:0; transform:translateY(40px); } to { opacity:1; transform:translateY(0); } }
        h1 { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom:10px; font-weight:900; font-size:2.5rem; letter-spacing:-1px; }
        p.subtitle { color:#64748b; font-weight:500; margin-bottom:30px; font-size:1.1rem; }
        input { width:100%; padding:18px; margin-bottom:15px; border:2px solid #e2e8f0; border-radius:14px; box-sizing:border-box; outline:none; font-size:1.05rem; font-weight:bold; transition:0.3s; background:#f8fafc; color:#0f172a; }
        input:focus { border-color:#6366f1; background:white; box-shadow: 0 0 0 4px rgba(99,102,241,0.15); }
        button { width:100%; padding:18px; background:linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color:white; border:none; border-radius:14px; font-weight:900; font-size:1.2rem; cursor:pointer; transition:0.2s; box-shadow:0 10px 20px rgba(99,102,241,0.3); margin-top:10px; display:flex; justify-content:center; align-items:center; gap:10px; }
        button:hover { transform:translateY(-3px); box-shadow:0 15px 25px rgba(99,102,241,0.4); }
    </style>
</head>
<body>
    <div class="box">
        <h1>Gongqn V28</h1>
        <p class="subtitle">Cloud MongoDB 게이트웨이</p>
        <form method="post">
            <input type="text" name="id" placeholder="등록된 아이디" required>
            <input type="password" name="pw" placeholder="보안 비밀번호" required>
            <button type="submit"><i class="fas fa-sign-in-alt"></i> {{ mode }} 완료하기</button>
        </form>
        <a href="{{ '/signup' if mode=='로그인' else '/login' }}" style="display:block; margin-top:25px; color:#64748b; text-decoration:none; font-weight:bold; transition:0.2s;"><i class="fas fa-user-plus"></i> {{ '신규 계정 발급 (회원가입)' if mode=='로그인' else '이미 계정이 있다면 로그인' }}</a>
    </div>
</body>
</html>
"""

# ==========================================================================================
# 🔌 [BACKEND API] 라우팅 및 코어 비즈니스 로직
# ==========================================================================================

@app.route('/')
def route_index():
    if 'user' not in session: return redirect('/login')
    db = load_db()
    u = db['users'].get(session['user'])
    
    if not u or u.get('is_blocked'):
        session.clear()
        return "접근 거부: 서버 최고 관리자에 의해 네트워크 접근이 차단된 계정입니다."

    session['nick'] = u.get('nick', session['user'])
    session['pfp'] = u.get('pfp', "")
    session['cash'] = u.get('cash', 0)
    session['role'] = u.get('role', 'user')
    
    sorted_posts = sorted(db.get('posts', []), key=lambda x: x.get('is_pinned', False), reverse=True)
    sorted_reviews = sorted(db.get('reviews', []), key=lambda x: x.get('date', ""), reverse=True)

    return render_template_string(
        UI_HTML, 
        notices=db.get('notices', []), 
        posts=sorted_posts, 
        sys=db.get('sys_config', {}), 
        shop_items=db.get('shop_items', []),
        reviews=sorted_reviews,
        transactions=db.get('transactions', [])
    )

@app.route('/login', methods=['GET', 'POST'])
def route_login():
    if request.method == 'POST':
        db = load_db()
        i, p = request.form.get('id'), request.form.get('pw')
        if i in db.get('users', {}) and db['users'][i]['pw'] == p:
            session['user'] = i
            return redirect('/')
        return "<script>alert('로그인 자격 증명이 일치하지 않습니다.'); history.back();</script>"
    return render_template_string(AUTH_HTML, mode='로그인')

@app.route('/signup', methods=['GET', 'POST'])
def route_signup():
    if request.method == 'POST':
        db = load_db()
        i, p = request.form.get('id').strip(), request.form.get('pw')
        if not i or not p: return "<script>alert('아이디와 비밀번호 규격을 맞춰주세요.'); history.back();</script>"
        if i in db.get('users', {}): return "<script>alert('이미 선점된 아이디입니다.'); history.back();</script>"
        
        db.setdefault('users', {})[i] = {
            "pw": p, "cash": 2000, "role": "admin" if i == "YEJUN" else "user", 
            "is_blocked": False, "nick": i, "pfp": "", "friends": [], "inventory": [], "last_attendance": ""
        }
        save_db(db)
        return redirect('/login')
    return render_template_string(AUTH_HTML, mode='회원가입')

@app.route('/logout')
def route_logout():
    session.clear()
    return redirect('/login')

# ------------------------------------------------------------------------------------------
# [API] 신규 시스템: 매일 출석체크 기능
# ------------------------------------------------------------------------------------------
@app.route('/api/attendance', methods=['POST'])
def api_attendance():
    db = load_db()
    u_id = session.get('user')
    u = db['users'][u_id]
    
    today = datetime.now().strftime("%Y-%m-%d")
    if u.get('last_attendance') == today:
        return jsonify({"ok": False, "msg": "오늘은 이미 출석체크를 하셨습니다. 내일 다시 와주세요!"})
        
    reward = int(db['sys_config'].get('att_reward', 150))
    u['cash'] = u.get('cash', 0) + reward
    u['last_attendance'] = today
    
    save_db(db)
    return jsonify({"ok": True, "msg": f"🎉 출석체크 완료! {reward} 캐시가 지급되었습니다."})

# ------------------------------------------------------------------------------------------
# [API] 신규 시스템: 관리자가 유저에게 아이템 직접 지정 전송
# ------------------------------------------------------------------------------------------
@app.route('/api/admin/give_item', methods=['POST'])
def api_admin_give_item():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    d = request.json
    uid = d.get('uid')
    item_name = d.get('item')
    
    if uid not in db.get('users', {}):
        return jsonify({"ok": False, "msg": "존재하지 않는 유저 ID입니다."})
        
    db['users'][uid].setdefault('inventory', []).append({
        "id": str(uuid.uuid4()),
        "name": item_name,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    save_db(db)
    return jsonify({"ok": True, "msg": f"[{uid}] 유저의 인벤토리로 [{item_name}] 아이템이 강제 전송되었습니다."})


# ------------------------------------------------------------------------------------------
# [API] 기타 기존 로직 (게시판, 룰렛, 채팅, 상점 등 완전 보존)
# ------------------------------------------------------------------------------------------

@app.route('/api/update', methods=['POST'])
def api_update():
    db = load_db()
    u = db['users'][session['user']]
    d = request.json
    if d['mode'] == 'profile':
        u['nick'], u['pfp'] = d.get('nick', u['nick']), d.get('pfp', u['pfp'])
        for p in db['posts']:
            if p['author'] == session['user']: 
                p['author_nick'], p['author_pfp'] = u['nick'], u['pfp']
        save_db(db)
        return jsonify({"ok": True, "msg": "프로필 정보 저장됨."})
    else:
        u['pw'] = d.get('pw', u['pw'])
        save_db(db)
        return jsonify({"ok": True, "msg": "비밀번호 변경 완료."})

@app.route('/api/post', methods=['POST'])
def api_post():
    db = load_db()
    u = db['users'][session['user']]
    db['posts'].insert(0, {
        "title": request.json['title'], "content": request.json['content'],
        "author": session['user'], "author_nick": u['nick'], "author_pfp": u['pfp'],
        "likes": [], "reports": [], "is_pinned": False, "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/action', methods=['POST'])
def api_action():
    db = load_db()
    p = db['posts'][request.json['idx']]
    u = session['user']
    if request.json['type'] == 'like':
        if u not in p['likes']: p['likes'].append(u)
        else: return jsonify({"ok": False, "msg": "이미 좋아요를 누른 게시물입니다."})
    else:
        if u not in p['reports']: p['reports'].append(u)
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/pin', methods=['POST'])
def api_pin():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    idx = request.json['idx']
    sorted_posts = sorted(db['posts'], key=lambda x: x.get('is_pinned', False), reverse=True)
    target = sorted_posts[idx]
    for p in db['posts']:
        if p == target: 
            p['is_pinned'] = not p.get('is_pinned', False)
            break
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/delete', methods=['POST'])
def api_delete():
    db = load_db()
    idx = request.json['idx']
    if request.json['type'] == 'notice' and session.get('role') == 'admin':
        db['notices'].pop(idx)
    else:
        sorted_posts = sorted(db['posts'], key=lambda x: x.get('is_pinned', False), reverse=True)
        t = sorted_posts[idx]
        if session.get('role') == 'admin' or t['author'] == session['user']: 
            db['posts'].remove(t)
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/spin', methods=['POST'])
def api_spin():
    db = load_db()
    u = db['users'][session['user']]
    cost = int(db['sys_config'].get('roulette_cost', 500))
    if u['role'] != 'admin':
        if u['cash'] < cost: return jsonify({"error": "자산이 부족하여 룰렛을 돌릴 수 없습니다."})
        u['cash'] -= cost
        
    s = db['sys_config']
    items = [s.get('r_i1'), s.get('r_i2'), s.get('r_i3'), s.get('r_i4'), s.get('r_i5'), s.get('r_i6')]
    probs = [int(s.get('r_p1',0)), int(s.get('r_p2',0)), int(s.get('r_p3',0)), int(s.get('r_p4',0)), int(s.get('r_p5',0)), int(s.get('r_p6',0))]
    
    if sum(probs) == 0: probs = [1,1,1,1,1,1]
    res = random.choices(items, weights=probs, k=1)[0]
    
    if res != "꽝":
        db.setdefault('roulette_approvals', []).append({
            "id": str(uuid.uuid4())[:8], "user": session['user'], "item": res, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    save_db(db)
    return jsonify({"res": res, "cash": u['cash']})

@app.route('/api/inventory/list', methods=['POST'])
def api_inventory_list():
    db = load_db()
    return jsonify({"ok": True, "items": db['users'][session['user']].get('inventory', [])})

@app.route('/api/inventory/use_request', methods=['POST'])
def api_inventory_use_request():
    db = load_db()
    u_id = session['user']
    u = db['users'][u_id]
    item_id = request.json.get('item_id')
    
    target_item = next((i for i in u.get('inventory', []) if i.get('id') == item_id), None)
    if not target_item: return jsonify({"ok": False, "msg": "보유하지 않은 아이템입니다."})
        
    db.setdefault('item_use_approvals', [])
    if any(r['item_id'] == item_id and r['user'] == u_id for r in db['item_use_approvals']):
        return jsonify({"ok": False, "msg": "이미 대기열에 있습니다."})
            
    db['item_use_approvals'].append({
        "req_id": str(uuid.uuid4()), "user": u_id, "item_id": target_item['id'], "item_name": target_item['name'], "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_db(db)
    return jsonify({"ok": True, "msg": "사용 승인 요청 전송됨!"})

@app.route('/api/friend/add_request', methods=['POST'])
def api_friend_add_request():
    db = load_db()
    sender, target = session['user'], request.json.get('friend_id')
    
    if target not in db['users']: return jsonify({"ok": False, "msg": "존재하지 않는 사용자입니다."})
    if sender == target: return jsonify({"ok": False, "msg": "자신에게 불가능합니다."})
    if target in db['users'][sender].get('friends', []): return jsonify({"ok": False, "msg": "이미 친구입니다."})
        
    db.setdefault('friend_requests', [])
    if any(r['sender'] == sender and r['target'] == target for r in db['friend_requests']): return jsonify({"ok": False, "msg": "이미 보냈습니다."})
    if any(r['sender'] == target and r['target'] == sender for r in db['friend_requests']): return jsonify({"ok": False, "msg": "상대방이 먼저 보냈습니다."})
            
    db['friend_requests'].append({
        "req_id": str(uuid.uuid4()), "sender": sender, "sender_nick": db['users'][sender].get('nick', sender), "target": target, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_db(db)
    return jsonify({"ok": True, "msg": f"{db['users'][target].get('nick', target)}님에게 친구 요청 발송!"})

@app.route('/api/friend/list_requests', methods=['POST'])
def api_friend_list_requests():
    db = load_db()
    return jsonify({"ok": True, "requests": [r for r in db.get('friend_requests', []) if r['target'] == session['user']]})

@app.route('/api/friend/handle_request', methods=['POST'])
def api_friend_handle_request():
    db = load_db()
    me, req_id, is_accept = session['user'], request.json.get('req_id'), request.json.get('accept')
    
    target_req = next((r for r in db.get('friend_requests', []) if r['req_id'] == req_id and r['target'] == me), None)
    if not target_req: return jsonify({"ok": False, "msg": "유효하지 않음."})
        
    db['friend_requests'].remove(target_req)
    
    if is_accept:
        sender_id = target_req['sender']
        if sender_id not in db['users'][me]['friends']: db['users'][me]['friends'].append(sender_id)
        if me not in db['users'][sender_id]['friends']: db['users'][sender_id]['friends'].append(me)
        
        room_id = f"dm_{min(sender_id, me)}_{max(sender_id, me)}"
        if room_id not in db['chat_rooms']:
            db['chat_rooms'][room_id] = {"type": "dm", "users": [sender_id, me], "messages": []}
        save_db(db)
        return jsonify({"ok": True, "msg": "수락하여 방이 개설되었습니다!"})
    else:
        save_db(db)
        return jsonify({"ok": True, "msg": "거절했습니다."})

@app.route('/api/chat/list', methods=['POST'])
def api_chat_list():
    db = load_db()
    u = session['user']
    rooms = []
    
    for rid, rdata in db['chat_rooms'].items():
        if rdata['type'] == 'channel':
            rooms.append({"room_id": rid, "type": "channel", "name": rdata.get('name', '공개채널')})
        elif u in rdata.get('users', []):
            if rdata['type'] == 'dm' or rdata['type'] == 'shop':
                target = [x for x in rdata['users'] if x != u]
                target_id = target[0] if target else u
                t_nick = db['users'].get(target_id, {}).get('nick', target_id)
                rooms.append({"room_id": rid, "type": rdata['type'], "target_nick": t_nick, "item_name": rdata.get('item_name', '')})
            elif rdata['type'] == 'group':
                rooms.append({"room_id": rid, "type": "group", "name": rdata.get('name', '단톡방')})
                
    return jsonify({"ok": True, "rooms": rooms})

@app.route('/api/chat/create_group', methods=['POST'])
def api_chat_create_group():
    db = load_db()
    d = request.json
    u = session['user']
    users = [u] + [x for x in d.get('users', []) if x in db['users'] and x != u]
    rid = "group_" + str(uuid.uuid4())[:12]
    db['chat_rooms'][rid] = {"type": "group", "name": d['name'], "users": users, "messages": []}
    save_db(db)
    return jsonify({"ok": True, "msg": "단톡방 개설 완료!"})

@app.route('/api/chat/create_channel', methods=['POST'])
def api_chat_create_channel():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    rid = "channel_" + str(uuid.uuid4())[:12]
    db['chat_rooms'][rid] = {"type": "channel", "name": request.json['name'], "users": [], "messages": []}
    save_db(db)
    return jsonify({"ok": True, "msg": "채널 개설 완료."})

@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    db = load_db()
    rid, msg, u = request.json['room_id'], request.json['msg'], session['user']
    u_nick = db['users'][u].get('nick', u)
    
    if rid not in db['chat_rooms']: return jsonify({"ok": False})
    rdata = db['chat_rooms'][rid]
    
    if msg.startswith('/'):
        if session.get('role') != 'admin': return jsonify({"ok": False})
        parts = msg.split(' ')
        cmd = parts[0]
        
        if cmd == '/시간': rdata['messages'].append({"type": "sys", "msg": f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"})
        elif cmd == '/청소': rdata['messages'] = []
        elif cmd == '/공지': rdata['messages'].append({"type": "embed", "embed_type": "info", "color": "#3b82f6", "title": "공지", "desc": ' '.join(parts[1:])})
        elif cmd == '/경고': rdata['messages'].append({"type": "embed", "embed_type": "alert", "color": "#ef4444", "title": "경고", "desc": ' '.join(parts[1:])})
        elif cmd == '/로벅스' and len(parts) > 2 and parts[1] == '계산기':
            try: rdata['messages'].append({"type": "embed", "embed_type": "success", "color": "#10b981", "title": "환율 계산", "desc": f"**{int(parts[2]) * 10} 원**"})
            except: pass
        elif cmd == '/아이템전송' and len(parts) >= 3:
            target_u, item_name = parts[1], ' '.join(parts[2:])
            if target_u in db['users']:
                db['users'][target_u].setdefault('inventory', []).append({"id": str(uuid.uuid4()), "name": item_name, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
                rdata['messages'].append({"type": "embed", "embed_type": "item_transfer", "title": f"🎁 지급", "desc": f"[{target_u}] 전송됨."})
        elif cmd == '/기록삭제':
            db['transactions'] = []
            rdata['messages'].append({"type": "embed", "embed_type": "alert", "title": "기록 말소", "desc": "삭제 완료."})
        elif cmd == '/캐시지급' and len(parts) >= 2:
            try:
                amt = int(parts[1])
                target = [x for x in rdata['users'] if x != u][0] if rdata['type'] == 'dm' else u
                db['users'][target]['cash'] += amt
                rdata['messages'].append({"type": "embed", "embed_type": "success", "color": "#10b981", "title": "자금 지원", "desc": f"{amt} 지급."})
            except: pass
        elif cmd == '/구매완료' and rdata['type'] == 'shop': rdata['messages'].append({"type": "embed", "embed_type": "review_request", "id": str(uuid.uuid4())[:8], "item_name": rdata['item_name']})
        elif cmd == '/거래완료' and rdata['type'] == 'shop':
            target = [x for x in rdata['users'] if x != u][0]
            db.setdefault('transactions', []).insert(0, {"buyer_nick": db['users'].get(target, {}).get('nick', target), "item_name": rdata['item_name'], "date": datetime.now().strftime("%m/%d %H:%M")})
            rdata['messages'].append({"type": "sys", "msg": "거래기록 등재됨."})
    else:
        rdata['messages'].append({"type": "msg", "sender": u, "sender_nick": u_nick, "msg": msg, "date": datetime.now().strftime("%H:%M")})
    
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/chat/sync', methods=['POST'])
def api_chat_sync():
    db = load_db()
    rid = request.json['room_id']
    if rid not in db['chat_rooms']: return jsonify({"ok": False})
    return jsonify({"ok": True, "messages": db['chat_rooms'][rid]['messages']})

@app.route('/api/chat/delete', methods=['POST'])
def api_chat_delete():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    rid = request.json['room_id']
    if rid in db['chat_rooms']: del db['chat_rooms'][rid]; save_db(db)
    return jsonify({"ok": True})

@app.route('/api/shop/add', methods=['POST'])
def api_shop_add():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    d = request.json
    db.setdefault('shop_items', []).append({"id": str(uuid.uuid4())[:8], "title": d['title'], "price": int(d['price']), "desc": d.get('desc',''), "img": d.get('img','')})
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/shop/del', methods=['POST'])
def api_shop_del():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    db['shop_items'] = [x for x in db['shop_items'] if x['id'] != request.json['id']]
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/shop/buy', methods=['POST'])
def api_shop_buy():
    db = load_db()
    u = session['user']
    target_id = request.json['id']
    item = next((x for x in db['shop_items'] if x['id'] == target_id), None)
    
    if not item: return jsonify({"ok": False, "msg": "상품 없음."})
    if session.get('role') != 'admin':
        if db['users'][u]['cash'] < item['price']: return jsonify({"ok": False, "msg": "잔액 부족."})
        db['users'][u]['cash'] -= item['price']
        
    admin_id = next((k for k,v in db['users'].items() if v.get('role') == 'admin'), "YEJUN")
    rid = "shop_" + str(uuid.uuid4())[:12]
    db['chat_rooms'][rid] = {"type": "shop", "users": [u, admin_id], "item_name": item['title'], "messages": [{"type": "sys", "msg": f"{item['title']} 1:1 채널 생성됨."}]}
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/review/add', methods=['POST'])
def api_review_add():
    db = load_db()
    d = request.json
    db.setdefault('reviews', []).insert(0, {"author": db['users'][session['user']].get('nick', session['user']), "item_name": d['item_name'], "rating": d['rating'], "content": d['content'], "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/admin/sys', methods=['POST'])
def api_admin_sys():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    d, s = request.json, db['sys_config']
    
    s['roulette_cost'] = int(d.get('rcost', 500))
    s['att_reward'] = int(d.get('att_reward', 150))
    s['popup_notice'] = d.get('popup', '')
    for i in range(1, 8): s[f'm{i}'] = d.get(f'm{i}', s.get(f'm{i}'))
    for i in range(1, 7): s[f'r_i{i}'], s[f'r_p{i}'] = d.get(f'r_i{i}', ''), int(d.get(f'r_p{i}', 0))
        
    save_db(db)
    return jsonify({"ok": True, "msg": "시스템 변수 덮어쓰기 완료."})

@app.route('/api/admin/notice', methods=['POST'])
def api_admin_notice():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    db['notices'].insert(0, {"title": request.json['t'], "content": request.json['c'], "img": request.json.get('i',''), "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/admin/coupon', methods=['POST'])
def api_admin_coupon():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    code = request.json['code']
    db.setdefault('coupons', {})[code] = int(request.json['rew'])
    save_db(db)
    return jsonify({"ok": True, "msg": f"쿠폰[{code}] 발급 완료."})

@app.route('/api/coupon/use', methods=['POST'])
def api_coupon_use():
    db = load_db()
    code, u = request.json['code'], session['user']
    if code in db.get('coupons', {}):
        amt = db['coupons'][code]
        db['users'][u]['cash'] += amt
        del db['coupons'][code] 
        save_db(db)
        return jsonify({"ok": True, "msg": f"쿠폰 완료! {amt} 캐시 충전."})
    return jsonify({"ok": False, "msg": "유효하지 않음."})

@app.route('/api/admin/user', methods=['POST'])
def api_admin_user():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db, d = load_db(), request.json
    uid = d['id']
    if uid not in db['users']: return jsonify({"ok": False, "msg": "없는 유저."})
    
    if d['act'] == 'give':
        try:
            amt = int(d['cash'])
            db['users'][uid]['cash'] += amt
            msg = f"{amt} 캐시 지급."
        except: return jsonify({"ok": False, "msg": "숫자 오류."})
    elif d['act'] == 'block':
        db['users'][uid]['is_blocked'] = True; msg = "영구 차단됨."
    elif d['act'] == 'unblock':
        db['users'][uid]['is_blocked'] = False; msg = "차단 해제됨."
        
    save_db(db)
    return jsonify({"ok": True, "msg": msg})

@app.route('/api/admin/approvals_list', methods=['POST'])
def api_admin_approvals_list():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    return jsonify({"ok": True, "data": load_db().get('roulette_approvals', [])})

@app.route('/api/admin/approve_roulette', methods=['POST'])
def api_admin_approve_roulette():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db, req_id, is_approve = load_db(), request.json['id'], request.json['approve']
    target = next((a for a in db.get('roulette_approvals', []) if a['id'] == req_id), None)
    if not target: return jsonify({"ok": False, "msg": "내역 없음."})
    
    db['roulette_approvals'].remove(target)
    if is_approve and target['user'] in db['users']:
        db['users'][target['user']].setdefault('inventory', []).append({"id": str(uuid.uuid4()), "name": target['item'], "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
        msg = "승인/지급 완료."
    else: msg = "거절/삭제 완료."
        
    save_db(db)
    return jsonify({"ok": True, "msg": msg})

@app.route('/api/admin/item_use_list', methods=['POST'])
def api_admin_item_use_list():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    return jsonify({"ok": True, "data": load_db().get('item_use_approvals', [])})

@app.route('/api/admin/approve_item_use', methods=['POST'])
def api_admin_approve_item_use():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db, req_id, is_approve = load_db(), request.json.get('req_id'), request.json.get('approve')
    target_req = next((r for r in db.get('item_use_approvals', []) if r['req_id'] == req_id), None)
    if not target_req: return jsonify({"ok": False, "msg": "찾을 수 없음."})
        
    db['item_use_approvals'].remove(target_req)
    u_id, item_id = target_req['user'], target_req['item_id']
    
    if is_approve:
        if u_id in db['users']:
            db['users'][u_id]['inventory'] = [i for i in db['users'][u_id].get('inventory', []) if i.get('id') != item_id]
            msg = f"[{target_req['item_name']}] 승인 처리됨."
        else: msg = "유저 없음."
    else: msg = "거부됨."
    save_db(db)
    return jsonify({"ok": True, "msg": msg})


if __name__ == '__main__':
    # Flask 서버 바인딩 및 구동
    app.run(host='0.0.0.0', port=5000, debug=True)
