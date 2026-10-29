"""
로또 6/45 분석 및 추천 엔진 (Lotto Engine)
- 역대 당첨 데이터 통계 분석
- 5가지 AI/통계 기반 추천 알고리즘
- 과거 회차 당첨 시뮬레이터 (백테스트)
"""
import json
import os
import random
import numpy as np
import pandas as pd
from itertools import combinations
from collections import Counter

# 로또 볼 색상 매핑
def get_ball_color(num):
    if 1 <= num <= 10:
        return {"bg": "#fbc400", "text": "#ffffff", "name": "노랑", "range": "1~10"}
    elif 11 <= num <= 20:
        return {"bg": "#2b8be8", "text": "#ffffff", "name": "파랑", "range": "11~20"}
    elif 21 <= num <= 30:
        return {"bg": "#e74c3c", "text": "#ffffff", "name": "빨강", "range": "21~30"}
    elif 31 <= num <= 40:
        return {"bg": "#8e959d", "text": "#ffffff", "name": "회색", "range": "31~40"}
    else:
        return {"bg": "#27ae60", "text": "#ffffff", "name": "초록", "range": "41~45"}

def calculate_ac(numbers):
    sorted_nums = sorted(numbers)
    diffs = set()
    for a, b in combinations(sorted_nums, 2):
        diffs.add(abs(a - b))
    return len(diffs) - (len(numbers) - 1)

def max_consecutive(numbers):
    sorted_nums = sorted(numbers)
    max_c = 1
    curr_c = 1
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i] + 1 == sorted_nums[i + 1]:
            curr_c += 1
            if curr_c > max_c:
                max_c = curr_c
        else:
            curr_c = 1
    return max_c

def max_same_tail(numbers):
    tails = [n % 10 for n in numbers]
    c = Counter(tails)
    return max(c.values()) if c else 1

class LottoAnalyzer:
    def __init__(self, data_path="lotto_data.json"):
        self.data_path = data_path
        self.records = []
        self.df = None
        self.load_data()

    def load_data(self):
        if not os.path.exists(self.data_path):
            from fetch_lotto_data import fetch_and_enrich_lotto_data, save_all
            df, raw = fetch_and_enrich_lotto_data()
            save_all(df, raw)
            
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.records = json.load(f)
            
        # 데이터프레임 구성
        rows = []
        for r in self.records:
            nums = r['numbers']
            rows.append({
                'round': r['round'],
                'date': r['date'],
                1: nums[0],
                2: nums[1],
                3: nums[2],
                4: nums[3],
                5: nums[4],
                6: nums[5],
                'bonus': r['bonus'],
                'sum': r.get('sum', sum(nums)),
                'odd_even': r.get('odd_even', ''),
                'low_high': r.get('low_high', ''),
                'ac': r.get('ac', calculate_ac(nums)),
                'winner_count': r.get('winner_count', 0),
                'prize_1st': r.get('prize_1st', 0)
            })
        self.df = pd.DataFrame(rows)
        self._compute_base_stats()

    def _compute_base_stats(self):
        # 1~45번 전체 출현 빈도수
        all_nums = []
        for r in self.records:
            all_nums.extend(r['numbers'])
        self.num_counter = Counter(all_nums)
        
        # 1~45 빈도 리스트 (인덱스 0 = 1번)
        self.freq_list = [self.num_counter.get(i, 0) for i in range(1, 46)]
        total_occurrences = sum(self.freq_list)
        self.weights = [f / total_occurrences for f in self.freq_list]
        
        # 과거 1등 당첨 조합 (튜플 정렬 세트)
        self.past_winning_sets = set([tuple(sorted(r['numbers'])) for r in self.records])
        
        # 각 번호별 마지막 출현 회차 및 미출현 기간
        latest_round = self.records[-1]['round']
        self.last_seen = {}
        for num in range(1, 46):
            self.last_seen[num] = 0
            
        for r in reversed(self.records):
            rnd = r['round']
            for n in r['numbers']:
                if self.last_seen[n] == 0:
                    self.last_seen[n] = rnd
                    
        # 미출현 기간 (현재 회차 - 마지막 출현 회차)
        self.unseen_periods = {
            num: latest_round - self.last_seen[num] if self.last_seen[num] > 0 else latest_round
            for num in range(1, 46)
        }

    def get_summary_stats(self):
        """대시보드 메인 요약 통계"""
        latest = self.records[-1]
        top10 = self.get_top_numbers(10)
        bottom10 = self.get_bottom_numbers(10)
        cold_numbers = sorted(self.unseen_periods.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 구간별 출현 빈도
        sections = {
            '1~10 (노랑)': sum(self.freq_list[0:10]),
            '11~20 (파랑)': sum(self.freq_list[10:20]),
            '21~30 (빨강)': sum(self.freq_list[20:30]),
            '31~40 (회색)': sum(self.freq_list[30:40]),
            '41~45 (초록)': sum(self.freq_list[40:45])
        }
        
        # 총합 평균 및 표준편차
        sums = [r['sum'] for r in self.records]
        mean_sum = float(np.mean(sums))
        std_sum = float(np.std(sums))
        
        return {
            'total_rounds': len(self.records),
            'latest_round': latest,
            'top10': top10,
            'bottom10': bottom10,
            'cold10': [{'number': n, 'period': p} for n, p in cold_numbers],
            'sections': sections,
            'mean_sum': round(mean_sum, 1),
            'std_sum': round(std_sum, 1),
            'recommended_sum_range': [int(round(mean_sum - std_sum)), int(round(mean_sum + std_sum))]
        }

    def get_top_numbers(self, n=10):
        sorted_items = sorted(self.num_counter.items(), key=lambda x: x[1], reverse=True)
        return [{'number': k, 'count': v, 'rate': round(v / len(self.records) * 100, 1)} for k, v in sorted_items[:n]]

    def get_bottom_numbers(self, n=10):
        sorted_items = sorted(self.num_counter.items(), key=lambda x: x[1])
        return [{'number': k, 'count': v, 'rate': round(v / len(self.records) * 100, 1)} for k, v in sorted_items[:n]]

    def get_top_pairs(self, n=15):
        pair_counts = Counter()
        for r in self.records:
            nums = sorted(r['numbers'])
            pair_counts.update(combinations(nums, 2))
        return [{'pair': list(p), 'count': c} for p, c in pair_counts.most_common(n)]

    def get_top_triplets(self, n=10):
        triplet_counts = Counter()
        for r in self.records:
            nums = sorted(r['numbers'])
            triplet_counts.update(combinations(nums, 3))
        return [{'triplet': list(t), 'count': c} for t, c in triplet_counts.most_common(n)]

    def validate_combination(self, nums, custom_filters=None):
        """
        조합 유효성 검증
        """
        nums = sorted(nums)
        s_sum = sum(nums)
        odds = sum(1 for n in nums if n % 2 != 0)
        evens = 6 - odds
        lows = sum(1 for n in nums if n <= 22)
        highs = 6 - lows
        ac_val = calculate_ac(nums)
        consec = max_consecutive(nums)
        tail_same = max_same_tail(nums)
        
        reasons = []
        
        # 1. 과거 1등과 동일한지
        if tuple(nums) in self.past_winning_sets:
            reasons.append("과거 1등 중복")
            
        # 2. 총합 (100 ~ 200 추천)
        min_sum = 100
        max_sum = 200
        if custom_filters and 'min_sum' in custom_filters:
            min_sum = custom_filters['min_sum']
        if custom_filters and 'max_sum' in custom_filters:
            max_sum = custom_filters['max_sum']
            
        if not (min_sum <= s_sum <= max_sum):
            reasons.append(f"총합({s_sum}) 범위 이탈({min_sum}~{max_sum})")
            
        # 3. 극단적 홀짝 (6:0, 0:6 배제)
        if odds == 0 or odds == 6:
            reasons.append(f"극단적 홀짝({odds}:{evens})")
            
        # 4. 극단적 고저 (6:0, 0:6 배제)
        if lows == 0 or lows == 6:
            reasons.append(f"극단적 고저({lows}:{highs})")
            
        # 5. 연속 번호 (3연번 이상 배제, 예: 12,13,14)
        if consec >= 3:
            reasons.append(f"{consec}연속 번호 포함")
            
        # 6. 동일 끝수 3개 이상 배제 (예: 3, 13, 23)
        if tail_same >= 3:
            reasons.append(f"동일 끝수 {tail_same}개 중복")
            
        # 7. AC값 (산술적 복합도 7 미만 배제)
        if ac_val < 7:
            reasons.append(f"AC값({ac_val}) 저조(7이상 권장)")
            
        is_valid = len(reasons) == 0
        grade = "S+" if (is_valid and 120 <= s_sum <= 160 and 2 <= odds <= 4 and ac_val >= 8) else ("A" if is_valid else "B")
        
        return {
            'is_valid': is_valid,
            'grade': grade,
            'reasons': reasons,
            'sum': s_sum,
            'odd_even': f"{odds}:{evens}",
            'low_high': f"{lows}:{highs}",
            'ac': ac_val,
            'consecutive': consec,
            'tail_same': tail_same
        }

    def generate_numbers(self, n_games=5, strategy="golden", fixed_nums=None, exclude_nums=None):
        """
        다양한 전략 모드 기반 추천 번호 생성:
        - golden: 황금 밸런스 AI (가중치 + 표준 필터링)
        - cold: 미출현(콜드수) 반등형 (장기 미출현수 2~3개 + 핫수)
        - hot: 최근 대세(핫수) 추종형 (최근 10회차 다출수 중심)
        - random: 순수 무작위 + 안전 필터링
        """
        fixed_nums = set(fixed_nums or [])
        exclude_nums = set(exclude_nums or [])
        
        # 고정수와 제외수 충돌 방지
        exclude_nums = exclude_nums - fixed_nums
        available_pool = [n for n in range(1, 46) if n not in exclude_nums]
        
        results = []
        max_attempts = 3000
        attempts = 0
        
        # 최근 10회 핫수 계산
        recent_10 = self.records[-10:]
        recent_nums = []
        for r in recent_10:
            recent_nums.extend(r['numbers'])
        recent_counts = Counter(recent_nums)
        hot_pool = [n for n, c in recent_counts.most_common(15) if n in available_pool and n not in fixed_nums]
        
        # 장기 미출현 콜드수 풀 (미출현 회차 높은 상위 15개)
        sorted_cold = sorted(self.unseen_periods.items(), key=lambda x: x[1], reverse=True)
        cold_pool = [n for n, p in sorted_cold[:15] if n in available_pool and n not in fixed_nums]

        while len(results) < n_games and attempts < max_attempts:
            attempts += 1
            chosen = set(fixed_nums)
            need_count = 6 - len(chosen)
            
            if need_count <= 0:
                candidate = sorted(list(chosen))[:6]
            else:
                if strategy == "cold" and len(cold_pool) >= 2:
                    # 콜드수에서 2개 추출, 나머지는 가중치 풀에서
                    cold_sample_size = min(random.randint(2, 3), len(cold_pool), need_count)
                    c_pick = random.sample(cold_pool, cold_sample_size)
                    chosen.update(c_pick)
                    
                    rem_need = 6 - len(chosen)
                    rem_pool = [n for n in available_pool if n not in chosen]
                    if rem_need > 0 and len(rem_pool) >= rem_need:
                        p_sub = [self.weights[n - 1] for n in rem_pool]
                        sum_p = sum(p_sub)
                        p_sub = [p / sum_p for p in p_sub]
                        picks = np.random.choice(rem_pool, size=rem_need, replace=False, p=p_sub)
                        chosen.update(picks)
                        
                elif strategy == "hot" and len(hot_pool) >= 3:
                    # 핫수에서 3~4개 추출, 나머지는 일반 풀에서
                    hot_sample_size = min(random.randint(3, 4), len(hot_pool), need_count)
                    h_pick = random.sample(hot_pool, hot_sample_size)
                    chosen.update(h_pick)
                    
                    rem_need = 6 - len(chosen)
                    rem_pool = [n for n in available_pool if n not in chosen]
                    if rem_need > 0 and len(rem_pool) >= rem_need:
                        picks = random.sample(rem_pool, rem_need)
                        chosen.update(picks)
                        
                else: # golden or default
                    rem_pool = [n for n in available_pool if n not in chosen]
                    if len(rem_pool) >= need_count:
                        p_sub = [self.weights[n - 1] for n in rem_pool]
                        sum_p = sum(p_sub)
                        p_sub = [p / sum_p for p in p_sub]
                        picks = np.random.choice(rem_pool, size=need_count, replace=False, p=p_sub)
                        chosen.update(picks)
                        
                candidate = [int(x) for x in sorted(list(chosen))]
                
            if len(candidate) != 6:
                continue
                
            # 유효성 검사
            check = self.validate_combination(candidate)
            if check['is_valid']:
                # 중복 추천 방지
                if not any(r['numbers'] == candidate for r in results):
                    results.append({
                        'game_no': len(results) + 1,
                        'numbers': candidate,
                        'balls': [{'number': n, **get_ball_color(n)} for n in candidate],
                        'sum': check['sum'],
                        'odd_even': check['odd_even'],
                        'low_high': check['low_high'],
                        'ac': check['ac'],
                        'grade': check['grade'],
                        'strategy': strategy
                    })

        return results

    def backtest_combination(self, user_numbers):
        """
        사용자 지정 6개 번호가 역대 전체 회차(1회 ~ 최신)에서 몇 등에 당첨되었었는지 백테스팅
        """
        user_set = set(user_numbers)
        win_records = []
        counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 0: 0}
        total_prize = 0
        
        for r in self.records:
            draw_set = set(r['numbers'])
            bonus = r['bonus']
            match_count = len(user_set.intersection(draw_set))
            
            rank = 0
            prize = 0
            if match_count == 6:
                rank = 1
                prize = r.get('prize_1st', 2000000000)
            elif match_count == 5 and bonus in user_set:
                rank = 2
                prize = 55000000 # 평균 2등 추정액
            elif match_count == 5:
                rank = 3
                prize = 1500000  # 평균 3등 추정액
            elif match_count == 4:
                rank = 4
                prize = 50000
            elif match_count == 3:
                rank = 5
                prize = 5000
                
            counts[rank] += 1
            total_prize += prize
            
            if rank in [1, 2, 3, 4, 5]:
                win_records.append({
                    'round': r['round'],
                    'date': r['date'],
                    'rank': rank,
                    'matches': match_count,
                    'bonus_match': (bonus in user_set),
                    'draw_numbers': r['numbers'],
                    'bonus': bonus,
                    'prize': prize
                })
                
        total_games = len(self.records)
        total_spent = total_games * 1000 # 1게임 1000원 기준
        roi = round(((total_prize - total_spent) / total_spent) * 100, 1) if total_spent > 0 else 0
        
        return {
            'numbers': sorted(list(user_numbers)),
            'total_rounds_tested': total_games,
            'summary_counts': counts,
            'total_prize': total_prize,
            'total_spent': total_spent,
            'net_profit': total_prize - total_spent,
            'roi_percent': roi,
            'winning_history': win_records[:30] # 상위 최근 30개 기록
        }
