# -*- coding: utf-8 -*-
"""
==========================================================================================
                     🚀 YEJUN ULTIMATE FRAMEWORK v27 (GOD-TIER MULTIVERSE EDITION) 🚀
                     🔥 룰렛 승인, 단톡방, 채널, 대형 임베드 명령어, 인벤토리 완벽 지원 🔥
                     ✨ [신규] 아이템 사용 승인 시스템 및 친구추가 수락 시스템 적용 완료 ✨
==========================================================================================

본 시스템은 단일 파일(Single File)로 동작하는 초고도화 웹 프레임워크입니다.
기존의 모든 기능(게시판, 룰렛, 상점, 관리자 패널, 채팅 등)을 완벽히 보존하며,
요청하신 '아이템 사용 시 관리자 승인 기능'과 '친구 요청 및 수락 기능'이 추가되었습니다.

"""

from flask import Flask, render_template_string, request, jsonify, session, redirect
import random
from pymongo import MongoClient
import os
import time
import uuid
from datetime import datetime

# ==========================================================================================
# ⚙️ [SYSTEM] 서버 초기화 및 환경 설정
# ==========================================================================================
app = Flask(__name__)
app.secret_key = "yejun_ultimate_god_tier_key_2026_infinity_plus_alpha_v27_super_ultra_max"

# ⚠️ 여기에 본인의 MongoDB URL을 직접 넣으세요!
MONGO_URI = "mongodb+srv://<아이디>:<비밀번호>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority" 

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db_client = client['gongqn_v27_db']
    app_state = db_client['app_state']
    print("✅ MongoDB 클라우드 접속 성공!")
except Exception as e:
    print(f"❌ MongoDB 접속 실패! URI를 확인하세요: {e}")   

# ==========================================================================================
# 🗄️ [DATABASE] 강력한 데이터베이스 엔진 (자동 마이그레이션 및 무결성 검사 포함)
# ==========================================================================================

def load_db():
    """
    데이터베이스 로드 및 자동 마이그레이션 함수.
    파일이 없으면 기본값을 생성하며, 구버전 데이터가 발견되면 자동으로 새 구조에 맞게 패치합니다.
    """
    default_db = {
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
            "popup_notice": "환영합니다! V27 시스템 업데이트가 완료되었습니다.",
            "r_i1": "최고급 소원권", "r_p1": 5,
            "r_i2": "꽝", "r_p2": 45,
            "r_i3": "프리미엄 놀이권", "r_p3": 10,
            "r_i4": "꽝", "r_p4": 20,
            "r_i5": "특별 야외권", "r_p5": 10,
            "r_i6": "꽝", "r_p6": 10
        },
        "shop_items": [],
        "chat_rooms": {},
        "reviews": [],
        "transactions": [],
        "roulette_approvals": [],     # 룰렛 당첨 관리자 승인 대기열
        "item_use_approvals": [],     # [신규] 유저 아이템 사용 관리자 승인 대기열
        "friend_requests": []         # [신규] 친구 추가 요청 대기열
    }
    
    if not os.path.exists(DB_FILE):
        return default_db
    
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
            
            # 기본 데이터 무결성 검사 및 병합 로직
            for key in default_db:
                if key not in db:
                    db[key] = default_db[key]
            
            # 유저 데이터 마이그레이션 (인벤토리 기능, 친구 목록 등)
            for u_id, u_data in db['users'].items():
                if 'friends' not in u_data: u_data['friends'] = []
                if 'inventory' not in u_data: u_data['inventory'] = []
            
            # 구버전 룰렛 데이터 패치
            for i in range(1, 7):
                if f"r_i{i}" not in db["sys_config"]:
                    db["sys_config"][f"r_i{i}"] = default_db["sys_config"][f"r_i{i}"]
                    db["sys_config"][f"r_p{i}"] = default_db["sys_config"][f"r_p{i}"]

            # v27 탭 메뉴명 마이그레이션
            if "m7" not in db["sys_config"]:
                db["sys_config"]["m7"] = default_db["sys_config"]["m7"]

            return db
    except Exception as e:
        print(f"[DB 로드 오류 발생 - 자동 복구 진행] {e}")
        return default_db

def get_default_db():
    return {
        "users": {}, "posts": [], "notices": [], "admin_msgs": [], "coupons": {},
        "sys_config": {
            "roulette_cost": 500, "m1": "홈(공지)", "m2": "게시판", "m3": "룰렛", 
            "m4": "상점", "m5": "채팅", "m6": "설정", "m7": "인벤토리",
            "popup_notice": "환영합니다! V27 MongoDB 업데이트 완료.",
            "r_i1": "최고급 소원권", "r_p1": 5, "r_i2": "꽝", "r_p2": 45,
            "r_i3": "프리미엄 놀이권", "r_p3": 10, "r_i4": "꽝", "r_p4": 20,
            "r_i5": "특별 야외권", "r_p5": 10, "r_i6": "꽝", "r_p6": 10
        },
        "shop_items": [], "chat_rooms": {}, "reviews": [], "transactions": [],
        "roulette_approvals": [], "item_use_approvals": [], "friend_requests": []
    }

def load_db():
    try:
        doc = app_state.find_one({"_id": "MAIN_DATA"})
        if not doc:
            default_db = get_default_db()
            app_state.insert_one({"_id": "MAIN_DATA", "data": default_db})
            return default_db
            
        db = doc.get("data", {})
        default_db = get_default_db()
        needs_update = False
        
        for key in default_db:
            if key not in db:
                db[key] = default_db[key]
                needs_update = True
                
        for u_id, u_data in db.get('users', {}).items():
            if 'friends' not in u_data: 
                u_data['friends'] = []
                needs_update = True
            if 'inventory' not in u_data: 
                u_data['inventory'] = []
                needs_update = True
                
        if needs_update: save_db(db)
        return db
    except Exception as e:
        return get_default_db()

def save_db(data):
    try:
        app_state.update_one({"_id": "MAIN_DATA"}, {"$set": {"data": data}}, upsert=True)
    except Exception as e:
        print("DB 저장 실패:", e)def get_default_db():
    return {
        "users": {}, "posts": [], "notices": [], "admin_msgs": [], "coupons": {},
        "sys_config": {
            "roulette_cost": 500, "m1": "홈(공지)", "m2": "게시판", "m3": "룰렛", 
            "m4": "상점", "m5": "채팅", "m6": "설정", "m7": "인벤토리",
            "popup_notice": "환영합니다! V27 MongoDB 업데이트 완료.",
            "r_i1": "최고급 소원권", "r_p1": 5, "r_i2": "꽝", "r_p2": 45,
            "r_i3": "프리미엄 놀이권", "r_p3": 10, "r_i4": "꽝", "r_p4": 20,
            "r_i5": "특별 야외권", "r_p5": 10, "r_i6": "꽝", "r_p6": 10
        },
        "shop_items": [], "chat_rooms": {}, "reviews": [], "transactions": [],
        "roulette_approvals": [], "item_use_approvals": [], "friend_requests": []
    }

def load_db():
    try:
        doc = app_state.find_one({"_id": "MAIN_DATA"})
        if not doc:
            default_db = get_default_db()
            app_state.insert_one({"_id": "MAIN_DATA", "data": default_db})
            return default_db
            
        db = doc.get("data", {})
        default_db = get_default_db()
        needs_update = False
        
        for key in default_db:
            if key not in db:
                db[key] = default_db[key]
                needs_update = True
                
        for u_id, u_data in db.get('users', {}).items():
            if 'friends' not in u_data: 
                u_data['friends'] = []
                needs_update = True
            if 'inventory' not in u_data: 
                u_data['inventory'] = []
                needs_update = True
                
        if needs_update: save_db(db)
        return db
    except Exception as e:
        return get_default_db()

def save_db(data):
    try:
        app_state.update_one({"_id": "MAIN_DATA"}, {"$set": {"data": data}}, upsert=True)
    except Exception as e:
        print("DB 저장 실패:", e)def get_default_db():
    return {
        "users": {}, "posts": [], "notices": [], "admin_msgs": [], "coupons": {},
        "sys_config": {
            "roulette_cost": 500, "m1": "홈(공지)", "m2": "게시판", "m3": "룰렛", 
            "m4": "상점", "m5": "채팅", "m6": "설정", "m7": "인벤토리",
            "popup_notice": "환영합니다! V27 MongoDB 업데이트 완료.",
            "r_i1": "최고급 소원권", "r_p1": 5, "r_i2": "꽝", "r_p2": 45,
            "r_i3": "프리미엄 놀이권", "r_p3": 10, "r_i4": "꽝", "r_p4": 20,
            "r_i5": "특별 야외권", "r_p5": 10, "r_i6": "꽝", "r_p6": 10
        },
        "shop_items": [], "chat_rooms": {}, "reviews": [], "transactions": [],
        "roulette_approvals": [], "item_use_approvals": [], "friend_requests": []
    }

def load_db():
    try:
        doc = app_state.find_one({"_id": "MAIN_DATA"})
        if not doc:
            default_db = get_default_db()
            app_state.insert_one({"_id": "MAIN_DATA", "data": default_db})
            return default_db
            
        db = doc.get("data", {})
        default_db = get_default_db()
        needs_update = False
        
        for key in default_db:
            if key not in db:
                db[key] = default_db[key]
                needs_update = True
                
        for u_id, u_data in db.get('users', {}).items():
            if 'friends' not in u_data: 
                u_data['friends'] = []
                needs_update = True
            if 'inventory' not in u_data: 
                u_data['inventory'] = []
                needs_update = True
                
        if needs_update: save_db(db)
        return db
    except Exception as e:
        return get_default_db()

def save_db(data):
    try:
        app_state.update_one({"_id": "MAIN_DATA"}, {"$set": {"data": data}}, upsert=True)
    except Exception as e:
        print("DB 저장 실패:", e)def get_default_db():
    return {
        "users": {}, "posts": [], "notices": [], "admin_msgs": [], "coupons": {},
        "sys_config": {
            "roulette_cost": 500, "m1": "홈(공지)", "m2": "게시판", "m3": "룰렛", 
            "m4": "상점", "m5": "채팅", "m6": "설정", "m7": "인벤토리",
            "popup_notice": "환영합니다! V27 MongoDB 업데이트 완료.",
            "r_i1": "최고급 소원권", "r_p1": 5, "r_i2": "꽝", "r_p2": 45,
            "r_i3": "프리미엄 놀이권", "r_p3": 10, "r_i4": "꽝", "r_p4": 20,
            "r_i5": "특별 야외권", "r_p5": 10, "r_i6": "꽝", "r_p6": 10
        },
        "shop_items": [], "chat_rooms": {}, "reviews": [], "transactions": [],
        "roulette_approvals": [], "item_use_approvals": [], "friend_requests": []
    }

def load_db():
    try:
        doc = app_state.find_one({"_id": "MAIN_DATA"})
        if not doc:
            default_db = get_default_db()
            app_state.insert_one({"_id": "MAIN_DATA", "data": default_db})
            return default_db
            
        db = doc.get("data", {})
        default_db = get_default_db()
        needs_update = False
        
        for key in default_db:
            if key not in db:
                db[key] = default_db[key]
                needs_update = True
                
        for u_id, u_data in db.get('users', {}).items():
            if 'friends' not in u_data: 
                u_data['friends'] = []
                needs_update = True
            if 'inventory' not in u_data: 
                u_data['inventory'] = []
                needs_update = True
                
        if needs_update: save_db(db)
        return db
    except Exception as e:
        return get_default_db()

def save_db(data):
    try:
        app_state.update_one({"_id": "MAIN_DATA"}, {"$set": {"data": data}}, upsert=True)
    except Exception as e:
        print("DB 저장 실패:", e)

# ==========================================================================================
# 🎨 [FRONTEND] 마스터 UI 템플릿 (초대형 CSS 및 스크립트 결합)
# 2000줄 이상의 거대한 프레임워크를 위해 CSS 유틸리티 및 템플릿을 확장 적용하였습니다.
# ==========================================================================================

UI_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Gongqn 공식커뮤니티 V27</title>
    
    <!-- 외부 라이브러리 로드 -->
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    
    <!-- 거대한 CSS 디자인 선언부 (확장판) -->
    <style>
        :root {
            /* 전역 색상 변수 */
            --bg-color: #f8fafc; 
            --card-bg: #ffffff; 
            --primary-grad: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            --primary: #6366f1; 
            --primary-hover: #4f46e5; 
            --text-main: #0f172a; 
            --text-sub: #64748b;
            --border: #e2e8f0; 
            
            /* 알림 및 임베드 그라데이션 */
            --danger-grad: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%); 
            --danger: #ef4444;
            --success-grad: linear-gradient(135deg, #10b981 0%, #059669 100%);
            --success: #10b981;
            --warning-grad: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
            --warning: #f59e0b;
            --info-grad: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            --info: #0ea5e9;
            
            /* 디자인 수치 */
            --radius: 20px;
            --radius-md: 12px;
            --radius-sm: 8px;
            --shadow-sm: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
            --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            --shadow-xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            
            /* 애니메이션 속도 */
            --transition-fast: 0.2s ease;
            --transition-normal: 0.3s ease;
            --transition-slow: 0.5s ease;
        }

        /* =========================================================
           CSS UTILITY CLASSES (거대 프레임워크 지원용)
           ========================================================= */
        .flex { display: flex; }
        .flex-col { display: flex; flex-direction: column; }
        .items-center { align-items: center; }
        .justify-center { justify-content: center; }
        .justify-between { justify-content: space-between; }
        .gap-1 { gap: 4px; } .gap-2 { gap: 8px; } .gap-3 { gap: 12px; } .gap-4 { gap: 16px; }
        .w-full { width: 100%; } .h-full { height: 100%; }
        .font-bold { font-weight: 700; } .font-black { font-weight: 900; }
        .text-center { text-align: center; } .text-left { text-align: left; } .text-right { text-align: right; }
        .mt-1 { margin-top: 4px; } .mt-2 { margin-top: 8px; } .mt-3 { margin-top: 12px; } .mt-4 { margin-top: 16px; } .mt-5 { margin-top: 20px; }
        .mb-1 { margin-bottom: 4px; } .mb-2 { margin-bottom: 8px; } .mb-3 { margin-bottom: 12px; } .mb-4 { margin-bottom: 16px; } .mb-5 { margin-bottom: 20px; }
        .p-1 { padding: 4px; } .p-2 { padding: 8px; } .p-3 { padding: 12px; } .p-4 { padding: 16px; } .p-5 { padding: 20px; }
        .text-xs { font-size: 0.75rem; } .text-sm { font-size: 0.875rem; } .text-base { font-size: 1rem; } .text-lg { font-size: 1.125rem; } .text-xl { font-size: 1.25rem; }
        .rounded-full { border-radius: 9999px; } .rounded-lg { border-radius: var(--radius-md); } .rounded-xl { border-radius: var(--radius); }
        .shadow-sm { box-shadow: var(--shadow-sm); } .shadow-md { box-shadow: var(--shadow-md); } .shadow-lg { box-shadow: var(--shadow-lg); }

        /* 기본 리셋 및 레이아웃 */
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Pretendard', sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-main); padding-bottom: 120px; overflow-x: hidden; scroll-behavior: smooth; }

        /* 헤더 디자인 */
        header {
            position: sticky; top: 0; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
            padding: 15px 20px; display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid rgba(226, 232, 240, 0.8); z-index: 1000; box-shadow: var(--shadow-sm);
            transition: all var(--transition-normal);
        }
        .logo { font-size: 1.4rem; font-weight: 900; background: var(--primary-grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px;}
        .cash-badge { background: #fef3c7; color: #d97706; padding: 8px 15px; border-radius: 50px; font-weight: 800; font-size: 0.95rem; box-shadow: var(--shadow-sm); display: flex; align-items: center; gap: 5px;}

        /* 컨테이너 */
        .container { max-width: 760px; margin: 0 auto; padding: 20px; }
        
        /* 페이지 애니메이션 제어 */
        .page { display: none; animation: fadeInScale 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; opacity: 0; }
        .page.active { display: block; }
        @keyframes fadeInScale { 
            from { opacity: 0; transform: translateY(20px) scale(0.98); } 
            to { opacity: 1; transform: translateY(0) scale(1); } 
        }
        @keyframes pulseGlow {
            0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(99, 102, 241, 0); }
            100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
        }

        /* 카드 UI 컴포넌트 */
        .card { background: var(--card-bg); border-radius: var(--radius); padding: 25px; margin-bottom: 25px; box-shadow: var(--shadow-md); border: 1px solid var(--border); transition: transform 0.3s ease, box-shadow 0.3s ease; position: relative; overflow: hidden;}
        .card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
        .card-title { font-size: 1.25rem; font-weight: 800; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; color: var(--text-main); }

        /* 입력 폼 폼컨트롤 */
        input[type="text"], input[type="password"], input[type="number"], textarea, select {
            width: 100%; padding: 16px; border-radius: 14px; border: 1.5px solid var(--border); background: #f8fafc;
            margin-bottom: 15px; outline: none; font-size: 1rem; transition: all 0.3s ease; font-weight: 500;
        }
        input:focus, textarea:focus, select:focus { border-color: var(--primary); box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15); background: #fff; }
        
        /* 버튼 컴포넌트 */
        .btn { width: 100%; padding: 16px; border-radius: 14px; border: none; font-size: 1.05rem; font-weight: 800; cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); margin-bottom: 10px; box-shadow: var(--shadow-sm); display: flex; align-items: center; justify-content: center; gap: 8px;}
        .btn:active { transform: scale(0.96); box-shadow: none; }
        .btn-primary { background: var(--primary-grad); color: white; }
        .btn-success { background: var(--success-grad); color: white; }
        .btn-danger { background: var(--danger-grad); color: white; }
        .btn-warning { background: var(--warning-grad); color: white; }
        .btn-info { background: var(--info-grad); color: white; }
        .btn-outline { background: transparent; border: 2px solid var(--border); color: var(--text-main); }
        .btn-outline:hover { border-color: var(--primary); color: var(--primary); }

        /* 에디터 툴바 */
        .editor-toolbar { display: flex; gap: 8px; margin-bottom: 15px; flex-wrap: wrap; background: #f1f5f9; padding: 10px; border-radius: 12px; }
        .editor-btn { padding: 10px 15px; border-radius: 10px; border: 1px solid var(--border); background: white; cursor: pointer; color: var(--text-main); transition: 0.2s; font-weight: bold; }
        .editor-btn:hover { background: var(--primary); color: white; border-color: var(--primary); transform: translateY(-2px); }

        /* 상점 그리드 */
        .shop-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
        .shop-item { background: white; border-radius: 16px; overflow: hidden; border: 1px solid var(--border); box-shadow: var(--shadow-sm); transition: 0.3s; position: relative; display: flex; flex-direction: column; }
        .shop-item:hover { transform: translateY(-5px); box-shadow: var(--shadow-lg); }
        .shop-img { width: 100%; height: 180px; object-fit: cover; background: #e2e8f0; }
        .shop-info { padding: 20px; display: flex; flex-direction: column; flex-grow: 1; }
        .shop-title { font-size: 1.2rem; font-weight: 800; margin-bottom: 5px; }
        .shop-price { color: var(--danger); font-weight: 900; font-size: 1.1rem; margin-bottom: 10px; }
        .shop-desc { font-size: 0.9rem; color: var(--text-sub); margin-bottom: 15px; line-height: 1.5; flex-grow: 1; }

        /* 채팅 리스트 및 윈도우 */
        .chat-list-item { display: flex; align-items: center; justify-content: space-between; padding: 18px; background: white; border-radius: 16px; margin-bottom: 12px; border: 1px solid var(--border); transition: 0.2s; cursor: pointer; box-shadow: var(--shadow-sm); }
        .chat-list-item:hover { background: #f8fafc; border-color: var(--primary); transform: translateX(5px); }
        
        .chat-window { display: none; flex-direction: column; height: 75vh; background: white; border-radius: 20px; overflow: hidden; box-shadow: var(--shadow-lg); border: 1px solid var(--border); }
        .chat-header { background: var(--primary-grad); color: white; padding: 15px 20px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 10; }
        .chat-messages { flex: 1; padding: 20px; overflow-y: auto; background: #f8fafc; display: flex; flex-direction: column; gap: 15px; }
        .chat-input-area { display: flex; padding: 15px; background: white; border-top: 1px solid var(--border); gap: 10px; align-items: center; z-index: 10; }
        
        /* 메시지 버블 디자인 */
        .msg-bubble { max-width: 80%; padding: 12px 18px; border-radius: 20px; font-size: 1rem; line-height: 1.5; position: relative; animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); word-break: break-word; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        @keyframes popIn { from { opacity: 0; transform: scale(0.8) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
        .msg-self { align-self: flex-end; background: var(--primary-grad); color: white; border-bottom-right-radius: 5px; }
        .msg-other { align-self: flex-start; background: white; border: 1px solid var(--border); border-bottom-left-radius: 5px; color: var(--text-main); }
        .sys-msg { align-self: center; background: rgba(0,0,0,0.05); color: var(--text-sub); font-size: 0.85rem; padding: 6px 16px; border-radius: 20px; text-align: center; font-weight: bold; margin: 10px 0; }

        /* =========================================================
           🔥 핵심 기능: 초대형 커스텀 임베드 디자인 (Discord 스타일 초월)
           ========================================================= */
        .super-embed {
            background: #ffffff; border-left: 6px solid var(--primary); border-radius: 12px; padding: 20px; color: var(--text-main);
            width: 100%; max-width: 90%; margin: 10px 0; box-shadow: 0 8px 25px rgba(0,0,0,0.08); align-self: center; font-family: 'Pretendard', sans-serif;
            position: relative; overflow: hidden; animation: slideInRight 0.4s ease-out;
        }
        @keyframes slideInRight { from { opacity: 0; transform: translateX(30px); } to { opacity: 1; transform: translateX(0); } }
        .super-embed::before {
            content: ''; position: absolute; top: 0; right: 0; width: 100px; height: 100px;
            background: radial-gradient(circle, rgba(99,102,241,0.1) 0%, rgba(255,255,255,0) 70%);
            border-radius: 50%; transform: translate(30%, -30%);
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

        /* 하단 네비게이션바 */
        .bottom-nav {
            position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            display: flex; justify-content: space-around;
            padding: 12px 0; border-top: 1px solid var(--border); box-shadow: 0 -10px 20px rgba(0,0,0,0.03); z-index: 1000; padding-bottom: env(safe-area-inset-bottom, 12px);
        }
        .nav-item { display: flex; flex-direction: column; align-items: center; color: #94a3b8; text-decoration: none; font-size: 0.7rem; font-weight: 800; gap: 6px; flex: 1; cursor: pointer; transition: 0.3s; }
        .nav-item i { font-size: 1.4rem; transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        .nav-item.active { color: var(--primary); }
        .nav-item.active i { transform: translateY(-4px) scale(1.15); filter: drop-shadow(0 2px 4px rgba(99,102,241,0.3)); }

        /* 인벤토리 (보관함) 특화 그리드 */
        .inventory-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; margin-top: 15px; }
        .inv-item { background: linear-gradient(to bottom, #ffffff, #f8fafc); border: 2px solid var(--border); border-radius: 16px; padding: 15px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: 0.3s; box-shadow: var(--shadow-sm); position: relative; }
        .inv-item:hover { transform: translateY(-5px); border-color: var(--primary); box-shadow: var(--shadow-md); }
        .inv-icon { font-size: 2.5rem; color: var(--primary); margin-bottom: 10px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1)); }
        .inv-name { font-weight: 900; font-size: 1rem; color: var(--text-main); margin-bottom: 5px; word-break: keep-all; }
        .inv-date { font-size: 0.7rem; color: var(--text-sub); margin-bottom: 10px; }
        
        /* [신규] 인벤토리 사용 버튼 */
        .btn-use-item { background: var(--success-grad); color: white; border: none; padding: 8px 12px; border-radius: 8px; font-weight: 900; font-size: 0.85rem; cursor: pointer; width: 100%; transition: 0.2s; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2); }
        .btn-use-item:hover { transform: scale(1.05); }

        /* 채널/단톡방 특화 UI */
        .channel-card { background: white; border: 1px solid var(--border); border-radius: 12px; padding: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: 0.2s; }
        .channel-card:hover { border-color: var(--primary); background: #f8fafc; }
        .channel-icon { width: 40px; height: 40px; border-radius: 10px; background: var(--info-grad); color: white; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; margin-right: 15px; }

        /* [신규] 친구 요청 리스트 아이템 UI */
        .friend-req-card { background: #fffbeb; border: 1px solid #fcd34d; border-radius: 12px; padding: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; transition: 0.2s; }
        .friend-req-card .info { display: flex; align-items: center; gap: 10px; }
        .friend-req-card .actions { display: flex; gap: 5px; }

        /* 모달 및 팝업 시스템 */
        .modal { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(15, 23, 42, 0.8); z-index:9999; display:none; justify-content:center; align-items:center; text-align:center; color:white; backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);}
        .modal.active { display: flex; flex-direction: column; animation: fadeInScale 0.3s ease; }
        .modal h1 { font-size: 3.5rem; margin: 15px 0; background: var(--warning-grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.3)); }
        
        .popup-content-box { background: white; color: var(--text-main); padding: 35px 30px; border-radius: 24px; width: 90%; max-width: 420px; position: relative; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); text-align: left; }
        .popup-close { position: absolute; top: 15px; right: 20px; background: none; border: none; font-size: 1.5rem; color: var(--text-sub); cursor: pointer; transition: 0.2s; }
        .popup-close:hover { color: var(--danger); transform: rotate(90deg); }

        /* 룰렛 디자인 강화 */
        .roulette-container { position: relative; width: 320px; height: 320px; margin: 30px auto; max-width: 100%; filter: drop-shadow(0 15px 30px rgba(0,0,0,0.15)); }
        #roulette-canvas { width: 100%; height: 100%; border-radius: 50%; border: 10px solid #ffffff; transition: transform 5s cubic-bezier(0.1, 0, 0.1, 1); }
        .pin { position: absolute; top: -20px; left: 50%; transform: translateX(-50%); color: #ef4444; font-size: 3rem; z-index: 10; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.4)); }

        @media (max-width: 600px) {
            .container { padding: 15px 10px; }
            header { padding: 12px 15px; }
            .logo { font-size: 1.2rem; }
            .nav-item span { font-size: 0.65rem; }
            .shop-grid { grid-template-columns: 1fr; }
            .modal h1 { font-size: 2.5rem; }
            .chat-window { height: 80vh; }
            .super-embed { max-width: 100%; }
        }
    </style>
</head>
<body>

<!-- 🌟 최초 접속 팝업 공지사항 모달 -->
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
    <div class="logo">Gongqn V27</div>
    <div class="cash-badge"><i class="fas fa-coins" style="color:#f59e0b;"></i> <span id="my-cash" style="margin-left:3px;">{{ session.get('cash') if session.get('role') != 'admin' else '∞' }}</span></div>
</header>

<div class="container">
    
    <!-- ================= 1. 홈 & 리뷰/거래 채널 ================= -->
    <div id="p-home" class="page">
        <!-- 메인 배너 영역 (시각적 확장) -->
        <div style="background: var(--primary-grad); border-radius: var(--radius); padding: 30px; color: white; margin-bottom: 25px; box-shadow: var(--shadow-md); position: relative; overflow: hidden;">
            <div style="position: relative; z-index: 2;">
                <h1 style="font-size: 1.8rem; font-weight: 900; margin-bottom: 10px;">환영합니다, {{ session.get('nick') }}님!</h1>
                <p style="font-size: 1rem; opacity: 0.9; line-height: 1.5;">V27 얼티밋 프레임워크가 적용된 커뮤니티입니다.<br>강력해진 명령어 임베드와 친구 시스템을 체험해보세요.</p>
            </div>
            <i class="fas fa-rocket" style="position: absolute; right: -20px; bottom: -20px; font-size: 8rem; opacity: 0.1; transform: rotate(-15deg);"></i>
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

    <!-- ================= 2. 자유 게시판 ================= -->
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

    <!-- ================= 3. 룰렛 (관리자 승인 시스템 적용) ================= -->
    <div id="p-roulette" class="page">
        <div class="card" style="text-align:center; background: linear-gradient(to bottom, #ffffff, #f8fafc);">
            <div class="card-title" style="justify-content:center; font-size: 1.5rem;"><i class="fas fa-gift" style="color:#f59e0b;"></i> 행운의 프리미엄 룰렛</div>
            <p style="color:var(--text-sub); margin-bottom:15px; font-size:1.1rem; background:#f1f5f9; display:inline-block; padding:8px 20px; border-radius:20px; font-weight:bold;">1회 참여: <b style="color:var(--danger); font-size:1.2rem;">{{ sys.roulette_cost }} 캐시</b></p>
            
            <div class="roulette-container">
                <i class="fas fa-caret-down pin"></i>
                <canvas id="roulette-canvas" width="320" height="320"></canvas>
            </div>
            
            <div style="background:#fff7ed; border:1px solid #fed7aa; color:#c2410c; padding:15px; border-radius:12px; margin-top:20px; font-size:0.9rem; font-weight:bold; text-align:left;">
                <i class="fas fa-info-circle"></i> V27 룰렛 안내사항<br>
                당첨 시 즉시 지급되지 않으며, 관리자에게 당첨 문자가 전송됩니다. 관리자 승인 완료 시 <b>[인벤토리]</b>로 아이템이 자동 지급됩니다.
            </div>

            <button id="spin-btn" type="button" class="btn btn-warning" onclick="spinRoulette()" style="margin-top:20px; font-size:1.3rem; padding:20px; border-radius:16px; font-weight:900; box-shadow: 0 10px 25px rgba(245, 158, 11, 0.3);"><i class="fas fa-play"></i> 짜릿하게 돌리기 (캐시 차감)</button>
        </div>
    </div>

    <!-- ================= 4. 상점 ================= -->
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
                <i class="fas fa-store-slash fa-3x" style="margin-bottom:15px; color:#cbd5e1;"></i><br>
                현재 등록된 상품이 없습니다. 관리자의 상점 업데이트를 기다려주세요!
            </div>
            {% endif %}
        </div>
    </div>

    <!-- ================= 5. 실시간 채팅 (채널 & 단톡방 & 친구 수락 지원) ================= -->
    <div id="p-chat" class="page">
        <div id="chat-list-view">
            <!-- [신규] 친구 추가 요청 확인 영역 -->
            <div id="friend-requests-section" style="display:none; margin-bottom: 20px;">
                <h3 style="color:var(--warning); margin-bottom: 10px; font-size: 1.1rem;"><i class="fas fa-user-clock"></i> 받은 친구 요청 대기열</h3>
                <div id="friend-requests-container"></div>
            </div>

            <!-- 탭 전환 UI -->
            <div style="display:flex; gap:10px; margin-bottom:20px;">
                <button class="btn btn-primary" style="flex:1; margin:0; padding:12px;" onclick="toggleChatCreate('dm')"><i class="fas fa-user-plus"></i> 친구추가</button>
                <button class="btn btn-info" style="flex:1; margin:0; padding:12px;" onclick="toggleChatCreate('group')"><i class="fas fa-users"></i> 단톡방</button>
                <button class="btn btn-success" style="flex:1; margin:0; padding:12px;" onclick="toggleChatCreate('channel')"><i class="fas fa-globe"></i> 채널개설</button>
            </div>

            <!-- 친구 추가 폼 (요청 전송 방식) -->
            <div id="create-dm" class="card chat-create-form" style="display:none; background:#eff6ff; border-color:#bfdbfe;">
                <h3 style="margin-bottom:15px; color:#1e3a8a;"><i class="fas fa-envelope"></i> 친구 요청 보내기</h3>
                <p style="font-size:0.85rem; color:#3b82f6; margin-bottom:10px;">상대방이 요청을 받아야지만 메시지를 보낼 수 있습니다.</p>
                <div style="display:flex; gap:10px;">
                    <input type="text" id="friend-id-input" placeholder="친구의 아이디 입력" style="margin:0;">
                    <button type="button" class="btn btn-primary" style="width:100px; margin:0;" onclick="sendFriendRequest()">요청</button>
                </div>
            </div>

            <!-- 단톡방 생성 폼 -->
            <div id="create-group" class="card chat-create-form" style="display:none; background:#ecfeff; border-color:#a5f3fc;">
                <h3 style="margin-bottom:15px; color:#164e63;"><i class="fas fa-users"></i> 새로운 단톡방 개설</h3>
                <input type="text" id="group-name" placeholder="단톡방 이름 (예: 코딩 스터디방)">
                <input type="text" id="group-users" placeholder="초대할 유저 아이디 (쉼표(,)로 구분)" style="margin-bottom:10px;">
                <button type="button" class="btn btn-info" style="margin:0;" onclick="createGroupChat()">단톡방 만들기</button>
            </div>

            <!-- 공개 채널 생성 폼 -->
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
                <button type="button" onclick="deleteChatRoom()" style="background:rgba(255,255,255,0.2); border:none; color:white; width:40px; height:40px; border-radius:50%; font-size:1.1rem; cursor:pointer; transition:0.2s;" title="관리자 권한으로 채팅방 영구 파괴"><i class="fas fa-trash"></i></button>
                {% endif %}
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <!-- 메시지가 동적으로 삽입되는 공간 -->
            </div>
            
            <div class="chat-input-area">
                <button type="button" style="background:#f1f5f9; border:none; width:45px; height:45px; border-radius:50%; color:var(--text-sub); font-size:1.2rem; cursor:pointer;"><i class="fas fa-plus"></i></button>
                <input type="text" id="chat-input" placeholder="메시지 또는 명령어 입력 (/명령어)" style="margin:0; border-radius:25px; border:2px solid var(--border); padding:15px 20px; font-weight:bold; flex-grow:1;" onkeypress="if(event.key==='Enter') sendChat()">
                <button type="button" class="btn btn-primary" style="width:50px; height:50px; margin:0; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow: 0 4px 10px rgba(99,102,241,0.3);" onclick="sendChat()"><i class="fas fa-paper-plane"></i></button>
            </div>
        </div>
    </div>

    <!-- ================= 6. 시스템 설정 ================= -->
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

    <!-- ================= 7. 인벤토리 (사용 승인 지원) ================= -->
    <div id="p-inventory" class="page">
        <div class="card" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color:white; border:none; text-align:center; padding: 40px 20px;">
            <i class="fas fa-box-open" style="font-size: 4rem; color: #fbbf24; margin-bottom: 15px; filter: drop-shadow(0 0 15px rgba(251, 191, 36, 0.4));"></i>
            <h2 style="font-size: 1.8rem; margin-bottom: 10px;">나의 보관함 (인벤토리)</h2>
            <p style="color: #94a3b8; font-size: 1.05rem;">룰렛 당첨 상품이나 특별한 아이템들이 이곳에 안전하게 보관됩니다.<br>아이템 사용은 관리자 승인 후 처리됩니다.</p>
        </div>
        
        <div class="card">
            <h3 style="margin-bottom: 20px; display:flex; align-items:center; gap:10px;"><i class="fas fa-list text-primary"></i> 보유 아이템 목록</h3>
            <div id="inventory-container" class="inventory-grid">
                <!-- JS에서 로드됨 -->
            </div>
        </div>
    </div>

    <!-- ================= 8. 최고 관리자 전용 마스터 패널 ================= -->
    {% if session.get('role') == 'admin' %}
    <div id="p-admin" class="page">
        <!-- 룰렛 승인 대기열 -->
        <div class="card" style="border:2px solid var(--warning); background:#fffbeb;">
            <h2 style="color:var(--warning); margin-bottom:15px; font-size:1.3rem; display:flex; align-items:center; gap:8px;"><i class="fas fa-gavel"></i> 룰렛 당첨 지급 승인 대기열</h2>
            <p style="font-size:0.85rem; color:#b45309; margin-bottom:15px;">유저가 룰렛에서 당첨된 내역입니다. 승인 시 인벤토리로 즉시 전송됩니다.</p>
            <div id="approval-list" style="display:flex; flex-direction:column; gap:10px;">
                <!-- JS 동적 로드 -->
            </div>
            <button type="button" class="btn btn-warning" style="margin-top:15px;" onclick="loadApprovals()"><i class="fas fa-sync-alt"></i> 목록 새로고침</button>
        </div>

        <!-- [신규] 유저 아이템 사용 승인 대기열 -->
        <div class="card" style="border:2px solid var(--info); background:#eff6ff;">
            <h2 style="color:var(--info); margin-bottom:15px; font-size:1.3rem; display:flex; align-items:center; gap:8px;"><i class="fas fa-magic"></i> 아이템 사용 승인 대기열</h2>
            <p style="font-size:0.85rem; color:#1e40af; margin-bottom:15px;">유저가 인벤토리에서 '사용하기'를 누른 아이템 내역입니다. 승인하면 아이템이 소진되고 효과가 적용됩니다.</p>
            <div id="item-use-approval-list" style="display:flex; flex-direction:column; gap:10px;">
                <!-- JS 동적 로드 -->
            </div>
            <button type="button" class="btn btn-info" style="margin-top:15px;" onclick="loadItemUseApprovals()"><i class="fas fa-sync-alt"></i> 아이템 대기열 새로고침</button>
        </div>

        <div class="card" style="background:#fff1f2; border:2px solid var(--danger);">
            <h2 style="color:var(--danger); margin-bottom:20px; font-size:1.4rem; font-weight:900;"><i class="fas fa-cogs"></i> V27 관리자 코어 시스템</h2>
            
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

            <h3 style="font-size:1.1rem; margin:15px 0 10px;">🔧 네비게이션 탭 이름 커스터마이징</h3>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:15px;">
                <input type="text" id="adm-m1" value="{{ sys.m1 }}" placeholder="탭1">
                <input type="text" id="adm-m2" value="{{ sys.m2 }}" placeholder="탭2">
                <input type="text" id="adm-m3" value="{{ sys.m3 }}" placeholder="탭3">
                <input type="text" id="adm-m4" value="{{ sys.m4 }}" placeholder="탭4">
                <input type="text" id="adm-m5" value="{{ sys.m5 }}" placeholder="탭5">
                <input type="text" id="adm-m6" value="{{ sys.m6 }}" placeholder="탭6">
                <input type="text" id="adm-m7" value="{{ sys.m7 }}" placeholder="탭7 (인벤토리)" style="grid-column: 1/-1;">
            </div>
            
            <h3 style="font-size:1.1rem; margin:25px 0 10px;">🎯 룰렛 상품 및 확률 (합 100% 필수)</h3>
            <label style="font-size:0.9rem; font-weight:bold;">1회 참여 비용 (캐시)</label>
            <input type="number" id="adm-rcost" value="{{ sys.roulette_cost }}">
            <div style="display:grid; grid-template-columns: 2fr 1fr; gap:10px; margin-bottom:15px; background:white; padding:15px; border-radius:12px;">
                <input type="text" id="adm-r-i1" value="{{ sys.r_i1 }}" placeholder="상품 1"><input type="number" id="adm-r-p1" value="{{ sys.r_p1 }}" placeholder="%">
                <input type="text" id="adm-r-i2" value="{{ sys.r_i2 }}" placeholder="상품 2"><input type="number" id="adm-r-p2" value="{{ sys.r_p2 }}" placeholder="%">
                <input type="text" id="adm-r-i3" value="{{ sys.r_i3 }}" placeholder="상품 3"><input type="number" id="adm-r-p3" value="{{ sys.r_p3 }}" placeholder="%">
                <input type="text" id="adm-r-i4" value="{{ sys.r_i4 }}" placeholder="상품 4"><input type="number" id="adm-r-p4" value="{{ sys.r_p4 }}" placeholder="%">
                <input type="text" id="adm-r-i5" value="{{ sys.r_i5 }}" placeholder="상품 5"><input type="number" id="adm-r-p5" value="{{ sys.r_p5 }}" placeholder="%">
                <input type="text" id="adm-r-i6" value="{{ sys.r_i6 }}" placeholder="상품 6"><input type="number" id="adm-r-p6" value="{{ sys.r_p6 }}" placeholder="%">
            </div>

            <label style="font-size:0.9rem; font-weight:bold; margin-top:10px; display:block;">접속 팝업 공지 내용 (HTML 지원)</label>
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

<!-- ================= 9. 하단 마스터 네비게이션 ================= -->
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

<!-- 룰렛 스핀 알림 모달 -->
<div class="modal" id="spin-alert-modal" onclick="this.classList.remove('active'); location.reload();">
    <h2 style="font-size:2rem; margin-bottom:10px;">🎰 스핀 완료!</h2>
    <h1 id="spin-alert-text" style="color:var(--primary); text-shadow:0 0 10px rgba(255,255,255,0.5);">상품</h1>
    <p style="margin-top:20px; font-size:1.1rem; color:#cbd5e1;">당첨된 아이템은 관리자에게 승인 문자가 전송되었습니다.<br>승인 후 인벤토리에 들어옵니다!</p>
    <p style="margin-top:30px; font-size:1rem; opacity:0.6;">화면을 터치하여 닫기</p>
</div>

<!-- ================= 10. 코어 클라이언트 자바스크립트 ================= -->
<script>
    let currentChatRoomId = null;
    let chatSyncTimer = null;
    let myUserId = '{{ session.get("user") }}';
    let lastMsgCount = 0; 
    const isAdmin = '{{ session.get("role") }}' === 'admin';

    window.addEventListener('DOMContentLoaded', () => {
        if(!sessionStorage.getItem('popup_seen_v27')) {
            const popup = document.getElementById('welcome-popup');
            popup.style.display = 'flex';
            popup.classList.add('active');
            sessionStorage.setItem('popup_seen_v27', 'true');
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

        if(isAdmin) {
            loadApprovals();
            loadItemUseApprovals();
        }
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

    // 게시판 툴바 로직
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
        if(confirm("이 데이터를 영구적으로 삭제하시겠습니까? 복구할 수 없습니다.")){
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
            if(!data.pw) return alert("새로운 안전한 비밀번호를 입력해주세요."); 
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

    // ================= 관리자 시스템 JS =================
    async function saveSys() {
        const d = {
            rcost: document.getElementById('adm-rcost').value, 
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

    // ================= 룰렛 & 룰렛 승인 로직 =================
    const prizes = ["{{ sys.r_i1 }}", "{{ sys.r_i2 }}", "{{ sys.r_i3 }}", "{{ sys.r_i4 }}", "{{ sys.r_i5 }}", "{{ sys.r_i6 }}"];
    const colors = ["#4f46e5", "#e2e8f0", "#ef4444", "#cbd5e1", "#f59e0b", "#94a3b8"];
    function drawRoulette() {
        const canvas = document.getElementById("roulette-canvas");
        const ctx = canvas.getContext("2d");
        const arc = (2 * Math.PI) / prizes.length;
        for(let i=0; i<prizes.length; i++) {
            ctx.beginPath(); ctx.fillStyle = colors[i]; ctx.moveTo(160, 160);
            ctx.arc(160, 160, 160, i*arc, (i+1)*arc); ctx.fill();
            ctx.save(); ctx.fillStyle = (i%2===0) ? "white" : "#1e293b"; ctx.font = "bold 18px Pretendard";
            ctx.translate(160 + Math.cos(i*arc + arc/2)*100, 160 + Math.sin(i*arc + arc/2)*100);
            ctx.rotate(i*arc + arc/2 + Math.PI/2);
            ctx.fillText(prizes[i], -ctx.measureText(prizes[i]).width/2, 0);
            ctx.restore();
        }
    }
    
    async function spinRoulette() {
        const btn = document.getElementById('spin-btn');
        btn.disabled = true;
        btn.innerText = "운명의 수레바퀴 도는 중...";

        const r = await req('/api/spin', {});
        if(r.error) { alert(r.error); btn.disabled = false; btn.innerHTML = '<i class="fas fa-play"></i> 짜릿하게 돌리기 (캐시 차감)'; return; }
        
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
                alert("앗! 꽝입니다! 확률은 잔인하지만 다음 기회를 노려보세요!"); 
                location.reload(); 
            }
        }, 5100);
    }

    async function loadApprovals() {
        if(!isAdmin) return;
        const r = await req('/api/admin/approvals_list', {});
        if(!r.ok) return;
        const cont = document.getElementById('approval-list');
        if(r.data.length === 0) {
            cont.innerHTML = '<div style="text-align:center; padding:15px; background:white; border-radius:10px; color:var(--text-sub);">승인 대기 중인 당첨 내역이 없습니다.</div>';
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
        alert(r.msg);
        if(r.ok) loadApprovals();
    }

    // ================= [신규] 아이템 사용 승인 로직 (관리자용) =================
    async function loadItemUseApprovals() {
        if(!isAdmin) return;
        const r = await req('/api/admin/item_use_list', {});
        if(!r.ok) return;
        const cont = document.getElementById('item-use-approval-list');
        if(r.data.length === 0) {
            cont.innerHTML = '<div style="text-align:center; padding:15px; background:white; border-radius:10px; color:var(--text-sub);">대기 중인 아이템 사용 요청이 없습니다.</div>';
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
        if(!confirm(isApprove ? "아이템 사용을 승인하시겠습니까? (유저 인벤토리에서 소진됩니다)" : "사용을 거부하시겠습니까?")) return;
        const r = await req('/api/admin/approve_item_use', { req_id: reqId, approve: isApprove });
        alert(r.msg);
        if(r.ok) loadItemUseApprovals();
    }

    // ================= 상점 & 인벤토리 JS =================
    async function saveShopItem() {
        const data = {
            title: document.getElementById('shop-title').value,
            price: document.getElementById('shop-price').value,
            desc: document.getElementById('shop-desc').value,
            img: document.getElementById('shop-img').value
        };
        if(!data.title || !data.price) return alert("상품명과 가격은 시스템상 필수 입력값입니다.");
        const r = await req('/api/shop/add', data);
        if(r.ok) { alert("상점 카탈로그에 성공적으로 등록되었습니다."); location.reload(); }
    }
    async function delShopItem(id) {
        if(!confirm("이 상품을 매대에서 영구 삭제하시겠습니까?")) return;
        const r = await req('/api/shop/del', {id: id});
        if(r.ok) location.reload();
    }
    async function buyItem(id, title, price) {
        if(!confirm(`[${title}] 아이템 구매를 확정하시겠습니까?\n거래 대금: ${price} 캐시\n승인 시 관리자와의 1:1 비밀 거래망이 구축됩니다.`)) return;
        const r = await req('/api/shop/buy', {id: id});
        if(r.ok) {
            alert("🎉 성공적으로 결제가 완료되었습니다! 하단의 [채팅] 탭으로 이동하여 관리자와 거래를 진행하세요.");
            location.reload();
        } else { alert(r.msg); }
    }

    async function fetchInventory() {
        const r = await req('/api/inventory/list', {});
        const box = document.getElementById('inventory-container');
        if(!r.ok || r.items.length === 0) {
            box.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:40px; background:white; border-radius:15px; border:1px solid var(--border); color:var(--text-sub);">인벤토리가 텅 비어있습니다. 룰렛이나 상점을 통해 아이템을 획득해보세요!</div>';
            return;
        }
        let html = '';
        r.items.forEach(item => {
            html += `
            <div class="inv-item">
                <i class="fas fa-gift inv-icon"></i>
                <div class="inv-name">${item.name}</div>
                <div class="inv-date">${item.date}</div>
                <!-- [신규] 아이템 사용하기 버튼 추가 -->
                <button class="btn-use-item" onclick="useInventoryItem('${item.id}', '${item.name}')">사용하기</button>
            </div>`;
        });
        box.innerHTML = html;
    }

    // [신규] 인벤토리에서 아이템 사용 요청
    async function useInventoryItem(itemId, itemName) {
        if(!confirm(`[${itemName}] 아이템을 정말 사용하시겠습니까?\n관리자 승인 후 효과가 적용되며, 인벤토리에서 사라집니다.`)) return;
        const r = await req('/api/inventory/use_request', { item_id: itemId });
        alert(r.msg);
        if(r.ok) fetchInventory(); // UI 갱신
    }

    // ================= 채팅 및 채널, 단톡방, 대형 임베드, [신규] 친구 수락 시스템 =================
    function toggleChatCreate(type) {
        document.querySelectorAll('.chat-create-form').forEach(el => el.style.display = 'none');
        document.getElementById(`create-${type}`).style.display = 'block';
    }

    // [신규] 친구 요청 보내기 (기존 바로 추가에서 변경)
    async function sendFriendRequest() {
        const fid = document.getElementById('friend-id-input').value.trim();
        if(!fid) return alert("아이디를 정확히 입력하세요");
        const r = await req('/api/friend/add_request', {friend_id: fid});
        alert(r.msg); 
        if(r.ok) {
            document.getElementById('friend-id-input').value = '';
        }
    }

    // [신규] 받은 친구 요청 리스트 불러오기
    async function loadFriendRequests() {
        const r = await req('/api/friend/list_requests', {});
        if(!r.ok) return;
        
        const section = document.getElementById('friend-requests-section');
        const cont = document.getElementById('friend-requests-container');
        
        if(r.requests.length === 0) {
            section.style.display = 'none';
            return;
        }
        
        section.style.display = 'block';
        let html = '';
        r.requests.forEach(reqObj => {
            html += `
            <div class="friend-req-card">
                <div class="info">
                    <i class="fas fa-user-circle" style="font-size:2rem; color:var(--primary);"></i>
                    <div>
                        <div style="font-weight:900; font-size:1.1rem; color:var(--text-main);">${reqObj.sender_nick}</div>
                        <div style="font-size:0.8rem; color:var(--text-sub);">ID: ${reqObj.sender}님이 친구를 요청했습니다.</div>
                    </div>
                </div>
                <div class="actions">
                    <button class="btn btn-success" style="padding:8px 12px; margin:0;" onclick="handleFriendRequest('${reqObj.req_id}', true)"><i class="fas fa-check"></i> 수락</button>
                    <button class="btn btn-danger" style="padding:8px 12px; margin:0;" onclick="handleFriendRequest('${reqObj.req_id}', false)"><i class="fas fa-times"></i></button>
                </div>
            </div>`;
        });
        cont.innerHTML = html;
    }

    // [신규] 친구 요청 수락/거절 핸들러
    async function handleFriendRequest(reqId, isAccept) {
        const r = await req('/api/friend/handle_request', { req_id: reqId, accept: isAccept });
        alert(r.msg);
        if(r.ok) {
            loadFriendRequests();
            loadChatRooms(); // 수락 후 채팅방 목록 갱신
        }
    }

    async function createGroupChat() {
        const name = document.getElementById('group-name').value.trim();
        const usersStr = document.getElementById('group-users').value.trim();
        if(!name || !usersStr) return alert("단톡방 이름과 초대할 유저를 입력하세요.");
        const users = usersStr.split(',').map(s => s.trim());
        const r = await req('/api/chat/create_group', {name: name, users: users});
        alert(r.msg);
        if(r.ok) loadChatRooms();
    }

    async function createChannel() {
        const name = document.getElementById('channel-name').value.trim();
        if(!name) return alert("채널 이름을 입력하세요.");
        const r = await req('/api/chat/create_channel', {name: name});
        alert(r.msg);
        if(r.ok) loadChatRooms();
    }

    async function loadChatRooms() {
        const r = await req('/api/chat/list', {});
        if(!r.ok) return;
        const c = document.getElementById('chat-rooms-container');
        c.innerHTML = '';
        if(r.rooms.length === 0) {
            c.innerHTML = '<div style="text-align:center; color:#94a3b8; padding:40px; background:white; border-radius:15px; border:2px dashed var(--border);">아직 개설된 채팅방이 없습니다. 친구를 추가하거나 방을 만들어보세요!</div>';
            return;
        }
        r.rooms.forEach(rm => {
            let icon = '<i class="fas fa-user"></i>';
            let title = rm.target_nick;
            let badge = '';
            
            if(rm.type === 'shop') { 
                icon = '<i class="fas fa-shopping-bag"></i>'; 
                title = `[거래망] ${rm.item_name}`; 
                badge = '<span style="background:var(--danger);color:white;padding:3px 8px;border-radius:10px;font-size:0.7rem;margin-left:5px;font-weight:bold;">VVIP 전용</span>'; 
            } else if(rm.type === 'group') {
                icon = '<i class="fas fa-users"></i>';
                title = rm.name;
                badge = '<span style="background:var(--info-grad);color:white;padding:3px 8px;border-radius:10px;font-size:0.7rem;margin-left:5px;">단톡방</span>';
            } else if(rm.type === 'channel') {
                icon = '<i class="fas fa-globe"></i>';
                title = rm.name;
                badge = '<span style="background:var(--success-grad);color:white;padding:3px 8px;border-radius:10px;font-size:0.7rem;margin-left:5px;">공개 채널</span>';
            }

            c.innerHTML += `
                <div class="channel-card" onclick="openChat('${rm.room_id}', '${title.replace(/'/g, "\\'")}', '${rm.type}')">
                    <div style="display:flex; align-items:center; width:100%;">
                        <div class="channel-icon">${icon}</div>
                        <div style="font-weight:900; font-size:1.1rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:65%;">
                            ${title}
                        </div> 
                        ${badge}
                    </div>
                    <i class="fas fa-chevron-right" style="color:var(--text-sub); font-size:1.2rem;"></i>
                </div>
            `;
        });
    }

    function openChat(roomId, title, type) {
        currentChatRoomId = roomId;
        lastMsgCount = 0; 
        document.getElementById('chat-list-view').style.display = 'none';
        document.getElementById('chat-room-view').style.display = 'flex';
        document.getElementById('chat-target-name').innerText = title;
        
        let typeText = "1:1 대화 (서로 수락됨)";
        if(type==='shop') typeText="관리자 안전 거래망";
        else if(type==='group') typeText="그룹 채팅";
        else if(type==='channel') typeText="공개 커뮤니티 채널";
        document.getElementById('chat-room-badge').innerText = typeText;
        
        syncChat();
        chatSyncTimer = setInterval(syncChat, 1500);
    }

    function closeChat() {
        currentChatRoomId = null;
        if(chatSyncTimer) clearInterval(chatSyncTimer);
        document.getElementById('chat-room-view').style.display = 'none';
        document.getElementById('chat-list-view').style.display = 'block';
    }

    async function deleteChatRoom() {
        if(!confirm("이 채널(방)을 데이터베이스에서 영구적으로 파괴하시겠습니까? (복구 불가)")) return;
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
            if(m.type === 'sys') {
                html += `<div class="sys-msg">${m.msg}</div>`;
            } else if(m.type === 'embed') {
                if(m.embed_type === 'review_request') {
                    html += `
                    <div class="super-embed embed-theme-warning">
                        <div class="embed-header">
                            <i class="fas fa-shopping-bag" style="color:#d97706; font-size:1.5rem;"></i>
                            <div class="embed-author">시스템 관리자 전송 시스템</div>
                        </div>
                        <div class="embed-title">🎁 거래가 최종 완료되었습니다!</div>
                        <div class="embed-desc"><b>[${m.item_name}]</b> 상품의 인도가 끝났습니다. 아래에서 별점과 소중한 리뷰를 남겨주시면 큰 힘이 됩니다.</div>
                        <div class="star-rating" id="rating-${m.id}">
                            <input type="radio" id="star5-${m.id}" name="rate-${m.id}" value="5"><label for="star5-${m.id}"><i class="fas fa-star"></i></label>
                            <input type="radio" id="star4-${m.id}" name="rate-${m.id}" value="4"><label for="star4-${m.id}"><i class="fas fa-star"></i></label>
                            <input type="radio" id="star3-${m.id}" name="rate-${m.id}" value="3"><label for="star3-${m.id}"><i class="fas fa-star"></i></label>
                            <input type="radio" id="star2-${m.id}" name="rate-${m.id}" value="2"><label for="star2-${m.id}"><i class="fas fa-star"></i></label>
                            <input type="radio" id="star1-${m.id}" name="rate-${m.id}" value="1"><label for="star1-${m.id}"><i class="fas fa-star"></i></label>
                        </div>
                        <input type="text" class="review-input" id="rev-txt-${m.id}" placeholder="솔직담백한 리뷰를 적어주세요!">
                        <button class="review-btn" onclick="submitReview('${m.item_name}', '${m.id}')"><i class="fas fa-upload"></i> 리뷰 업로드 및 확정</button>
                    </div>`;
                } else if(m.embed_type === 'item_transfer') {
                    html += `
                    <div class="super-embed embed-theme-success">
                        <div class="embed-header">
                            <i class="fas fa-gift" style="color:#059669; font-size:1.5rem;"></i>
                            <div class="embed-author">아이템 지급/사용 시스템 엔진 V27</div>
                        </div>
                        <div class="embed-title">${m.title}</div>
                        <div class="embed-desc">${m.desc}</div>
                        <div class="embed-footer"><i class="fas fa-check-circle"></i> 시스템에 의해 정상 처리되었습니다.</div>
                    </div>`;
                } else if(m.embed_type === 'alert') {
                    html += `
                    <div class="super-embed embed-theme-danger">
                        <div class="embed-header">
                            <i class="fas fa-exclamation-triangle" style="color:#dc2626; font-size:1.5rem;"></i>
                            <div class="embed-author">서버 최고 관리자 강제 명령</div>
                        </div>
                        <div class="embed-title">${m.title}</div>
                        <div class="embed-desc" style="color:#7f1d1d; font-weight:bold;">${m.desc}</div>
                        <div class="embed-footer"><i class="fas fa-shield-alt"></i> 이 작업은 취소할 수 없습니다.</div>
                    </div>`;
                } else {
                    let theme = m.color === '#ef4444' ? 'embed-theme-danger' : (m.color === '#3b82f6' ? 'embed-theme-info' : 'embed-theme-success');
                    let icon = m.color === '#ef4444' ? 'fa-ban' : 'fa-bullhorn';
                    html += `
                    <div class="super-embed ${theme}">
                        <div class="embed-header">
                            <i class="fas ${icon}" style="font-size:1.5rem;"></i>
                            <div class="embed-author">시스템 방송국</div>
                        </div>
                        <div class="embed-title">${m.title}</div>
                        <div class="embed-desc">${m.desc}</div>
                    </div>`;
                }
            } else {
                const isMe = m.sender === myUserId;
                const cls = isMe ? 'msg-self' : 'msg-other';
                const senderName = isMe ? '' : `<div style="font-size:0.8rem; font-weight:900; color:var(--text-main); margin-bottom:5px; padding-left:5px;">${m.sender_nick}</div>`;
                html += `<div style="display:flex; flex-direction:column; align-items:${isMe?'flex-end':'flex-start'}; margin-bottom:8px;">${senderName}<div class="msg-bubble ${cls}">${m.msg}</div></div>`;
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
        if(rating === 0) return alert("별점을 터치하여 먼저 선택해주세요!");
        if(!txt) return alert("리뷰 내용을 꼼꼼히 작성해주세요!");

        const r = await req('/api/review/add', {item_name: itemName, rating: rating, content: txt});
        if(r.ok) { alert("소중한 리뷰가 서버에 업로드되었습니다!"); location.reload(); }
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
    <title>Gongqn V27 보안 게이트웨이</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;500;700;900&display=swap" rel="stylesheet">
    <style>
        body { margin:0; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); font-family: 'Pretendard', sans-serif; height:100vh; display:flex; align-items:center; justify-content:center; overflow:hidden; }
        .bg-shapes { position:absolute; width:100%; height:100%; top:0; left:0; overflow:hidden; z-index:0; }
        .shape { position:absolute; filter:blur(60px); opacity:0.5; border-radius:50%; animation: float 10s infinite alternate; }
        @keyframes float { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(30px, -50px) scale(1.2); } }
        
        .box { background:rgba(255,255,255,0.95); padding:40px 30px; border-radius:24px; width:90%; max-width:400px; text-align:center; box-shadow:0 25px 50px -12px rgba(0,0,0,0.5); backdrop-filter: blur(15px); animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1); z-index:10; position:relative; }
        @keyframes slideUp { from { opacity:0; transform:translateY(40px); } to { opacity:1; transform:translateY(0); } }
        
        h1 { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom:10px; font-weight:900; font-size:2.5rem; letter-spacing:-1px; }
        p.subtitle { color:#64748b; font-weight:500; margin-bottom:30px; font-size:1.1rem; }
        
        input { width:100%; padding:18px; margin-bottom:15px; border:2px solid #e2e8f0; border-radius:14px; box-sizing:border-box; outline:none; font-size:1.05rem; font-weight:bold; transition:0.3s; background:#f8fafc; color:#0f172a; }
        input:focus { border-color:#6366f1; background:white; box-shadow: 0 0 0 4px rgba(99,102,241,0.15); }
        
        button { width:100%; padding:18px; background:linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color:white; border:none; border-radius:14px; font-weight:900; font-size:1.2rem; cursor:pointer; transition:0.2s; box-shadow:0 10px 20px rgba(99,102,241,0.3); margin-top:10px; display:flex; justify-content:center; align-items:center; gap:10px; }
        button:hover { transform:translateY(-3px); box-shadow:0 15px 25px rgba(99,102,241,0.4); }
        button:active { transform:translateY(0); box-shadow:none; }
    </style>
</head>
<body>
    <div class="bg-shapes">
        <div class="shape" style="width:300px; height:300px; background:#4f46e5; top:-50px; left:-50px;"></div>
        <div class="shape" style="width:400px; height:400px; background:#e11d48; bottom:-100px; right:-50px; animation-delay:-5s;"></div>
    </div>
    <div class="box">
        <h1>Gongqn V27</h1>
        <p class="subtitle">얼티밋 보안 게이트웨이</p>
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
# 🔌 [BACKEND API] 라우팅 및 코어 비즈니스 로직 (단일 파일화 완벽 지원)
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
    
    sorted_posts = sorted(db['posts'], key=lambda x: x.get('is_pinned', False), reverse=True)
    sorted_reviews = sorted(db['reviews'], key=lambda x: x.get('date', ""), reverse=True)

    return render_template_string(
        UI_HTML, 
        notices=db['notices'], 
        posts=sorted_posts, 
        sys=db['sys_config'], 
        shop_items=db['shop_items'],
        reviews=sorted_reviews,
        transactions=db.get('transactions', [])
    )

@app.route('/login', methods=['GET', 'POST'])
def route_login():
    if request.method == 'POST':
        db = load_db()
        i, p = request.form.get('id'), request.form.get('pw')
        if i in db['users'] and db['users'][i]['pw'] == p:
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
        if i in db['users']: return "<script>alert('이미 다른 사용자가 선점한 아이디입니다.'); history.back();</script>"
        
        # 'YEJUN' 아이디로 가입 시 자동으로 최고 관리자 권한 부여
        db['users'][i] = {
            "pw": p, 
            "cash": 2000, 
            "role": "admin" if i == "YEJUN" else "user", 
            "is_blocked": False, 
            "nick": i, 
            "pfp": "", 
            "friends": [], 
            "inventory": []
        }
        save_db(db)
        return redirect('/login')
    return render_template_string(AUTH_HTML, mode='회원가입')

@app.route('/logout')
def route_logout():
    session.clear()
    return redirect('/login')

# ------------------------------------------------------------------------------------------
# [API] 게시판, 프로필 관련
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
        return jsonify({"ok": True, "msg": "프로필 정보가 시스템에 안전하게 저장되었습니다."})
    else:
        u['pw'] = d.get('pw', u['pw'])
        save_db(db)
        return jsonify({"ok": True, "msg": "보안 비밀번호 변경 완료."})

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

# ------------------------------------------------------------------------------------------
# [API] 룰렛 스핀 및 당첨 시스템 
# ------------------------------------------------------------------------------------------
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
    
    # 🌟 당첨 시 바로 주지 않고 관리자 승인 대기열로 푸시 (요구사항 완벽 적용)
    if res != "꽝":
        db.setdefault('roulette_approvals', []).append({
            "id": str(uuid.uuid4())[:8],
            "user": session['user'],
            "item": res,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    save_db(db)
    return jsonify({"res": res, "cash": u['cash']})

# ------------------------------------------------------------------------------------------
# [API] 인벤토리 관련 및 신규 아이템 사용 승인 로직
# ------------------------------------------------------------------------------------------
@app.route('/api/inventory/list', methods=['POST'])
def api_inventory_list():
    db = load_db()
    u = db['users'][session['user']]
    return jsonify({"ok": True, "items": u.get('inventory', [])})

@app.route('/api/inventory/use_request', methods=['POST'])
def api_inventory_use_request():
    """ 
    [신규 기능] 
    인벤토리에서 아이템 '사용' 클릭 시 -> 바로 효과 적용 X
    관리자에게 사용 승인 요청(문자 대용 대기열 푸시)을 보냄.
    기존 데이터 구조와 시스템을 건드리지 않고 독립된 큐(item_use_approvals) 사용.
    """
    db = load_db()
    u_id = session['user']
    u = db['users'][u_id]
    item_id = request.json.get('item_id')
    
    # 인벤토리에 해당 아이템이 있는지 확인
    target_item = None
    for item in u.get('inventory', []):
        if item.get('id') == item_id:
            target_item = item
            break
            
    if not target_item:
        return jsonify({"ok": False, "msg": "보유하지 않은 아이템이거나 이미 사용 요청을 보냈습니다."})
        
    # 이미 요청 대기열에 있는지 검사
    db.setdefault('item_use_approvals', [])
    for req_obj in db['item_use_approvals']:
        if req_obj['item_id'] == item_id and req_obj['user'] == u_id:
            return jsonify({"ok": False, "msg": "이미 관리자에게 사용 승인을 요청한 아이템입니다. 대기해주세요."})
            
    # 대기열에 추가 (관리자에게 문자 가듯 리스트업됨)
    db['item_use_approvals'].append({
        "req_id": str(uuid.uuid4()),
        "user": u_id,
        "item_id": target_item['id'],
        "item_name": target_item['name'],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    save_db(db)
    return jsonify({"ok": True, "msg": "관리자에게 아이템 사용 승인 요청을 성공적으로 전송했습니다!"})

# ------------------------------------------------------------------------------------------
# [API] 신규 친구 요청/수락 시스템 
# ------------------------------------------------------------------------------------------
@app.route('/api/friend/add_request', methods=['POST'])
def api_friend_add_request():
    """
    [신규 기능]
    기존엔 바로 친구가 되었으나, 이제는 '친구 요청'을 보내고 상대가 '수락'해야 함.
    기존 채팅방 생성 및 친구 목록 로직을 해치지 않고 중간 단계를 추가함.
    """
    db = load_db()
    sender = session['user']
    target = request.json.get('friend_id')
    
    if target not in db['users']:
        return jsonify({"ok": False, "msg": "존재하지 않는 사용자입니다."})
    if sender == target:
        return jsonify({"ok": False, "msg": "자기 자신에게는 요청을 보낼 수 없습니다."})
    
    # 이미 친구인지 검사
    if target in db['users'][sender].get('friends', []):
        return jsonify({"ok": False, "msg": "이미 친구로 등록되어 있습니다."})
        
    # 이미 요청을 보냈는지 검사
    db.setdefault('friend_requests', [])
    for req_obj in db['friend_requests']:
        if req_obj['sender'] == sender and req_obj['target'] == target:
            return jsonify({"ok": False, "msg": "이미 상대방에게 친구 요청을 보냈습니다. 수락을 기다려주세요."})
        if req_obj['sender'] == target and req_obj['target'] == sender:
            return jsonify({"ok": False, "msg": "상대방이 먼저 요청을 보냈습니다. 채팅 탭 상단에서 수락해주세요."})
            
    # 요청 큐에 푸시
    db['friend_requests'].append({
        "req_id": str(uuid.uuid4()),
        "sender": sender,
        "sender_nick": db['users'][sender].get('nick', sender),
        "target": target,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_db(db)
    return jsonify({"ok": True, "msg": f"{db['users'][target].get('nick', target)}님에게 친구 요청을 발송했습니다!"})

@app.route('/api/friend/list_requests', methods=['POST'])
def api_friend_list_requests():
    """현재 접속한 유저가 받은 친구 요청 목록 반환"""
    db = load_db()
    me = session['user']
    my_requests = [req for req in db.get('friend_requests', []) if req['target'] == me]
    return jsonify({"ok": True, "requests": my_requests})

@app.route('/api/friend/handle_request', methods=['POST'])
def api_friend_handle_request():
    """친구 요청 수락 또는 거절 처리"""
    db = load_db()
    me = session['user']
    req_id = request.json.get('req_id')
    is_accept = request.json.get('accept')
    
    db.setdefault('friend_requests', [])
    target_req = None
    
    for req_obj in db['friend_requests']:
        if req_obj['req_id'] == req_id and req_obj['target'] == me:
            target_req = req_obj
            break
            
    if not target_req:
        return jsonify({"ok": False, "msg": "유효하지 않은 요청입니다."})
        
    # 대기열에서 제거
    db['friend_requests'].remove(target_req)
    
    if is_accept:
        sender_id = target_req['sender']
        
        # 양쪽 친구 목록에 추가
        if sender_id not in db['users'][me]['friends']: db['users'][me]['friends'].append(sender_id)
        if me not in db['users'][sender_id]['friends']: db['users'][sender_id]['friends'].append(me)
        
        # DM 방 개설 (기존 로직 재사용)
        room_id = f"dm_{min(sender_id, me)}_{max(sender_id, me)}"
        if room_id not in db['chat_rooms']:
            db['chat_rooms'][room_id] = {
                "type": "dm", "users": [sender_id, me], "messages": []
            }
        save_db(db)
        return jsonify({"ok": True, "msg": "친구 요청을 수락하여 1:1 대화방이 개설되었습니다!"})
    else:
        save_db(db)
        return jsonify({"ok": True, "msg": "친구 요청을 거절했습니다."})

# ------------------------------------------------------------------------------------------
# [API] 채팅, 단톡방, 채널 관련 (기존 유지)
# ------------------------------------------------------------------------------------------
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
                rooms.append({
                    "room_id": rid, "type": rdata['type'], 
                    "target_nick": t_nick, "item_name": rdata.get('item_name', '')
                })
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
    return jsonify({"ok": True, "msg": "성공적으로 단톡방이 개설되었습니다!"})

@app.route('/api/chat/create_channel', methods=['POST'])
def api_chat_create_channel():
    if session.get('role') != 'admin': return jsonify({"ok": False, "msg": "채널 개설은 관리자만 가능합니다."})
    db = load_db()
    rid = "channel_" + str(uuid.uuid4())[:12]
    db['chat_rooms'][rid] = {"type": "channel", "name": request.json['name'], "users": [], "messages": []}
    save_db(db)
    return jsonify({"ok": True, "msg": "전역 채널이 개설되었습니다."})

@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    db = load_db()
    rid = request.json['room_id']
    msg = request.json['msg']
    u = session['user']
    u_nick = db['users'][u].get('nick', u)
    
    if rid not in db['chat_rooms']: return jsonify({"ok": False, "msg": "존재하지 않는 방입니다."})
    
    rdata = db['chat_rooms'][rid]
    
    # 명령어 시스템 파서 (대형 임베드 지원)
    if msg.startswith('/'):
        if session.get('role') != 'admin': return jsonify({"ok": False, "msg": "명령어 권한이 없습니다."})
        parts = msg.split(' ')
        cmd = parts[0]
        
        if cmd == '/시간':
            rdata['messages'].append({"type": "sys", "msg": f"서버 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"})
        elif cmd == '/청소':
            rdata['messages'] = []
        elif cmd == '/공지':
            text = ' '.join(parts[1:])
            rdata['messages'].append({"type": "embed", "embed_type": "info", "color": "#3b82f6", "title": "서버 전체 공지", "desc": text})
        elif cmd == '/경고':
            text = ' '.join(parts[1:])
            rdata['messages'].append({"type": "embed", "embed_type": "alert", "color": "#ef4444", "title": "시스템 경고 발령", "desc": text})
        elif cmd == '/로벅스' and len(parts) > 2 and parts[1] == '계산기':
            try:
                rbx = int(parts[2])
                rdata['messages'].append({"type": "embed", "embed_type": "success", "color": "#10b981", "title": "로벅스 환율 계산기 (1:10)", "desc": f"계산된 금액: **{rbx * 10} 원**"})
            except: pass
        elif cmd == '/아이템전송' and len(parts) >= 3:
            target_u = parts[1]
            item_name = ' '.join(parts[2:])
            if target_u in db['users']:
                db['users'][target_u].setdefault('inventory', []).append({"id": str(uuid.uuid4()), "name": item_name, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
                rdata['messages'].append({"type": "embed", "embed_type": "item_transfer", "title": f"🎁 {item_name} 지급 완료", "desc": f"대상 유저 [{target_u}]의 인벤토리로 안전하게 전송되었습니다."})
        elif cmd == '/기록삭제':
            db['transactions'] = []
            rdata['messages'].append({"type": "embed", "embed_type": "alert", "title": "거래 기록 말소", "desc": "서버의 모든 실시간 거래 기록 데이터가 파괴되었습니다."})
        elif cmd == '/캐시지급' and len(parts) >= 2:
            try:
                amt = int(parts[1])
                target = [x for x in rdata['users'] if x != u][0] if rdata['type'] == 'dm' else u
                db['users'][target]['cash'] += amt
                rdata['messages'].append({"type": "embed", "embed_type": "success", "color": "#10b981", "title": "자금 지원", "desc": f"[{target}] 유저에게 {amt} 캐시가 지급되었습니다."})
            except: pass
        elif cmd == '/구매완료':
            if rdata['type'] == 'shop':
                rdata['messages'].append({"type": "embed", "embed_type": "review_request", "id": str(uuid.uuid4())[:8], "item_name": rdata['item_name']})
        elif cmd == '/거래완료':
            if rdata['type'] == 'shop':
                target = [x for x in rdata['users'] if x != u][0]
                t_nick = db['users'].get(target, {}).get('nick', target)
                db.setdefault('transactions', []).insert(0, {"buyer_nick": t_nick, "item_name": rdata['item_name'], "date": datetime.now().strftime("%m/%d %H:%M")})
                if len(db['transactions']) > 15: db['transactions'].pop()
                rdata['messages'].append({"type": "sys", "msg": "실시간 거래 기록에 성공적으로 등재되었습니다."})
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
    if rid in db['chat_rooms']:
        del db['chat_rooms'][rid]
        save_db(db)
    return jsonify({"ok": True})

# ------------------------------------------------------------------------------------------
# [API] 상점 구매 시스템 (채팅 연동)
# ------------------------------------------------------------------------------------------
@app.route('/api/shop/add', methods=['POST'])
def api_shop_add():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    d = request.json
    db.setdefault('shop_items', []).append({
        "id": str(uuid.uuid4())[:8], "title": d['title'], "price": int(d['price']), "desc": d.get('desc',''), "img": d.get('img','')
    })
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
    
    if not item: return jsonify({"ok": False, "msg": "상품이 존재하지 않습니다."})
    
    if session.get('role') != 'admin':
        if db['users'][u]['cash'] < item['price']: return jsonify({"ok": False, "msg": "잔액이 부족합니다."})
        db['users'][u]['cash'] -= item['price']
        
    admin_users = [k for k,v in db['users'].items() if v.get('role') == 'admin']
    admin_id = admin_users[0] if admin_users else "YEJUN"
    
    rid = "shop_" + str(uuid.uuid4())[:12]
    db['chat_rooms'][rid] = {
        "type": "shop", "users": [u, admin_id], "item_name": item['title'],
        "messages": [{"type": "sys", "msg": f"{item['title']} 상품 거래를 위한 1:1 비밀 채널이 생성되었습니다."}]
    }
    
    save_db(db)
    return jsonify({"ok": True})

# ------------------------------------------------------------------------------------------
# [API] 리뷰 기능
# ------------------------------------------------------------------------------------------
@app.route('/api/review/add', methods=['POST'])
def api_review_add():
    db = load_db()
    d = request.json
    db.setdefault('reviews', []).insert(0, {
        "author": db['users'][session['user']].get('nick', session['user']),
        "item_name": d['item_name'], "rating": d['rating'], "content": d['content'],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_db(db)
    return jsonify({"ok": True})

# ------------------------------------------------------------------------------------------
# [API] 최고 관리자 패널 로직
# ------------------------------------------------------------------------------------------
@app.route('/api/admin/sys', methods=['POST'])
def api_admin_sys():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    d = request.json
    s = db['sys_config']
    
    s['roulette_cost'] = int(d.get('rcost', 500))
    s['popup_notice'] = d.get('popup', '')
    for i in range(1, 8): s[f'm{i}'] = d.get(f'm{i}', s.get(f'm{i}'))
    for i in range(1, 7):
        s[f'r_i{i}'] = d.get(f'r_i{i}', '')
        s[f'r_p{i}'] = int(d.get(f'r_p{i}', 0))
        
    save_db(db)
    return jsonify({"ok": True, "msg": "코어 시스템 환경변수가 덮어씌워졌습니다."})

@app.route('/api/admin/notice', methods=['POST'])
def api_admin_notice():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    db['notices'].insert(0, {
        "title": request.json['t'], "content": request.json['c'], "img": request.json.get('i',''),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_db(db)
    return jsonify({"ok": True})

@app.route('/api/admin/coupon', methods=['POST'])
def api_admin_coupon():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    code = request.json['code']
    db.setdefault('coupons', {})[code] = int(request.json['rew'])
    save_db(db)
    return jsonify({"ok": True, "msg": f"쿠폰[{code}]이/가 성공적으로 발급되었습니다."})

@app.route('/api/coupon/use', methods=['POST'])
def api_coupon_use():
    db = load_db()
    code = request.json['code']
    u = session['user']
    
    if code in db.get('coupons', {}):
        amt = db['coupons'][code]
        db['users'][u]['cash'] += amt
        del db['coupons'][code] 
        save_db(db)
        return jsonify({"ok": True, "msg": f"쿠폰 적용 완료! {amt} 캐시가 충전되었습니다."})
    return jsonify({"ok": False, "msg": "유효하지 않거나 이미 만료된 쿠폰 코드입니다."})

@app.route('/api/admin/user', methods=['POST'])
def api_admin_user():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    d = request.json
    uid = d['id']
    
    if uid not in db['users']: return jsonify({"ok": False, "msg": "타겟 유저가 DB에 존재하지 않습니다."})
    
    if d['act'] == 'give':
        try:
            amt = int(d['cash'])
            db['users'][uid]['cash'] += amt
            msg = f"{amt} 캐시를 지급했습니다."
        except: return jsonify({"ok": False, "msg": "올바른 숫자를 입력하세요."})
    elif d['act'] == 'block':
        db['users'][uid]['is_blocked'] = True
        msg = "해당 유저를 영구 차단했습니다."
    elif d['act'] == 'unblock':
        db['users'][uid]['is_blocked'] = False
        msg = "차단이 해제되었습니다."
        
    save_db(db)
    return jsonify({"ok": True, "msg": msg})

# ------------------------------------------------------------------------------------------
# [API] 관리자 승인 관련 (룰렛 & 신규 아이템 사용)
# ------------------------------------------------------------------------------------------
@app.route('/api/admin/approvals_list', methods=['POST'])
def api_admin_approvals_list():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    return jsonify({"ok": True, "data": db.get('roulette_approvals', [])})

@app.route('/api/admin/approve_roulette', methods=['POST'])
def api_admin_approve_roulette():
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    req_id = request.json['id']
    is_approve = request.json['approve']
    
    target = None
    for a in db.get('roulette_approvals', []):
        if a['id'] == req_id:
            target = a
            break
            
    if not target: return jsonify({"ok": False, "msg": "이미 처리되었거나 없는 내역입니다."})
    
    db['roulette_approvals'].remove(target)
    
    if is_approve and target['user'] in db['users']:
        db['users'][target['user']].setdefault('inventory', []).append({
            "id": str(uuid.uuid4()), "name": target['item'], "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        msg = "승인 완료! 유저 인벤토리로 전송되었습니다."
    else:
        msg = "승인 거절(내역 삭제) 완료."
        
    save_db(db)
    return jsonify({"ok": True, "msg": msg})

@app.route('/api/admin/item_use_list', methods=['POST'])
def api_admin_item_use_list():
    """[신규] 관리자용 아이템 사용 승인 대기열 반환"""
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    return jsonify({"ok": True, "data": db.get('item_use_approvals', [])})

@app.route('/api/admin/approve_item_use', methods=['POST'])
def api_admin_approve_item_use():
    """
    [신규] 유저가 사용 요청한 아이템을 관리자가 승인/거부 처리.
    승인 시: 인벤토리에서 실제 차감 및 유저에게 시스템 메시지로 알림 효과 적용가능 (구조 확장성)
    거부 시: 인벤토리 유지, 큐에서만 삭제
    """
    if session.get('role') != 'admin': return jsonify({"ok": False})
    db = load_db()
    req_id = request.json.get('req_id')
    is_approve = request.json.get('approve')
    
    target_req = None
    for req in db.get('item_use_approvals', []):
        if req['req_id'] == req_id:
            target_req = req
            break
            
    if not target_req:
        return jsonify({"ok": False, "msg": "요청을 찾을 수 없습니다. (이미 처리되었을 수 있음)"})
        
    # 대기열 큐에서 팝
    db['item_use_approvals'].remove(target_req)
    
    u_id = target_req['user']
    item_id = target_req['item_id']
    
    if is_approve:
        if u_id in db['users']:
            # 인벤토리에서 해당 아이템 삭제 (사용됨)
            user_inv = db['users'][u_id].get('inventory', [])
            db['users'][u_id]['inventory'] = [i for i in user_inv if i.get('id') != item_id]
            
            # (옵션) 관리자 승인 내역을 특정 채팅이나 공지로 날릴 수도 있음. 여기서는 승인 완료 메시지만 응답.
            msg = f"[{target_req['item_name']}] 사용이 최종 승인되어 소진 처리되었습니다."
        else:
            msg = "존재하지 않는 유저입니다."
    else:
        msg = "사용 요청이 거부되어 아이템이 유지됩니다."
        
    save_db(db)
    return jsonify({"ok": True, "msg": msg})


if __name__ == '__main__':
    # Flask 서버 바인딩 및 구동
    app.run(host='0.0.0.0', port=5000, debug=True)
