"""
동행복권 로또 6/45 역대 전회차(1회 ~ 최신회차) 완전 수집 및 고급 통계 지표 자동 계산 모듈
"""
import requests
import json
import time
import os
import urllib3
import pandas as pd
from itertools import combinations

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def calculate_ac(numbers):
    """
    AC값 (Arithmetic Complexity, 산술적 복합도) 계산
    6개 번호의 2개 차이(Difference) 중 고유한 값의 개수 - (6 - 1)
    범위: 0 ~ 10 (로또에서는 보통 6~10이 대부분, 7 이상 권장)
    """
    sorted_nums = sorted(numbers)
    diffs = set()
    for a, b in combinations(sorted_nums, 2):
        diffs.add(abs(a - b))
    return len(diffs) - (len(numbers) - 1)

def max_consecutive_count(numbers):
    """최대 연속 번호 길이 (예: [1,2,3] -> 3, [5,6] -> 2, 없으면 1)"""
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

def max_same_tail_digit(numbers):
    """최대 동일 끝수 개수 (예: 3, 13, 23 -> 끝수 3이 3개)"""
    tails = [n % 10 for n in numbers]
    from collections import Counter
    c = Counter(tails)
    return max(c.values()) if c else 1

def fetch_and_enrich_lotto_data():
    timestamp = int(time.time() * 1000)
    url = f"https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do?srchLtEpsd=all&_={timestamp}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.dhlottery.co.kr/',
    }
    
    print("동행복권 공식 서버에서 1회차부터 최신 회차까지 전체 데이터를 수집합니다...")
    resp = requests.get(url, headers=headers, verify=False, timeout=30)
    resp.raise_for_status()
    
    data = resp.json()
    raw_list = data.get('data', {}).get('list', [])
    print(f"총 {len(raw_list)}개 회차 수집 완료! 고급 통계 필드 계산 중...")
    
    # 회차 오름차순 정렬
    raw_list.sort(key=lambda x: x.get('ltEpsd', 0))
    
    enriched_rows = []
    prev_nums = None
    
    for item in raw_list:
        round_no = item.get('ltEpsd')
        raw_date = str(item.get('ltRflYmd', ''))
        draw_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}" if len(raw_date) == 8 else raw_date
        
        nums = sorted([
            int(item.get('tm1WnNo')),
            int(item.get('tm2WnNo')),
            int(item.get('tm3WnNo')),
            int(item.get('tm4WnNo')),
            int(item.get('tm5WnNo')),
            int(item.get('tm6WnNo')),
        ])
        bonus = int(item.get('bnsWnNo'))
        
        # 이전 회차 이월수
        carryover = []
        if prev_nums:
            carryover = sorted(list(set(nums).intersection(set(prev_nums))))
        prev_nums = nums
        carryover_str = ",".join(map(str, carryover)) if carryover else ""
        
        # 통계 지표 계산
        total_sum = sum(nums)
        odds = sum(1 for n in nums if n % 2 != 0)
        evens = 6 - odds
        lows = sum(1 for n in nums if n <= 22)   # 저번호
        highs = 6 - lows                         # 고번호
        
        sec_1_10 = sum(1 for n in nums if 1 <= n <= 10)
        sec_11_20 = sum(1 for n in nums if 11 <= n <= 20)
        sec_21_30 = sum(1 for n in nums if 21 <= n <= 30)
        sec_31_40 = sum(1 for n in nums if 31 <= n <= 40)
        sec_41_45 = sum(1 for n in nums if 41 <= n <= 45)
        
        ac_val = calculate_ac(nums)
        consec_max = max_consecutive_count(nums)
        tail_max = max_same_tail_digit(nums)
        
        row = {
            '회차': round_no,
            '추첨일': draw_date,
            '당첨번호 1': nums[0],
            '2': nums[1],
            '3': nums[2],
            '4': nums[3],
            '5': nums[4],
            '6': nums[5],
            '보너스번호': bonus,
            '지난회 번호': carryover_str,
            '낮은 번호': lows,
            '높은 번호': highs,
            '홀수': odds,
            '짝수': evens,
            '1-10': sec_1_10,
            '11-20': sec_11_20,
            '21-30': sec_21_30,
            '31-40': sec_31_40,
            '41-45': sec_41_45,
            '총합': total_sum,
            'AC값': ac_val,
            '최대연속수': consec_max,
            '최대동일끝수': tail_max,
            '1등 당첨자수': item.get('rnk1WnNope', 0),
            '1등 당첨금액': item.get('rnk1WnAmt', 0),
            '2등 당첨자수': item.get('rnk2WnNope', 0),
            '2등 당첨금액': item.get('rnk2WnAmt', 0),
            '3등 당첨자수': item.get('rnk3WnNope', 0),
            '3등 당첨금액': item.get('rnk3WnAmt', 0),
            '4등 당첨자수': item.get('rnk4WnNope', 0),
            '4등 당첨금액': item.get('rnk4WnAmt', 0),
            '5등 당첨자수': item.get('rnk5WnNope', 0),
            '5등 당첨금액': item.get('rnk5WnAmt', 0),
            '자동': item.get('winType1', 0),
            '수동': item.get('winType2', 0),
            '반자동': item.get('winType3', 0),
            '총판매금액': item.get('wholEpsdSumNtslAmt', 0),
            # 호환용 숫자 컬럼 (1, 2, 3, 4, 5, 6, '보너스')
            1: nums[0],
            2: nums[1],
            3: nums[2],
            4: nums[3],
            5: nums[4],
            6: nums[5],
            '보너스': bonus
        }
        enriched_rows.append(row)
        
    df = pd.DataFrame(enriched_rows)
    return df, raw_list

def save_all(df, raw_list, base_dir="."):
    excel_path = os.path.join(base_dir, "lotto_history.xlsx")
    csv_path = os.path.join(base_dir, "lotto_history.csv")
    json_path = os.path.join(base_dir, "lotto_data.json")
    
    # 엑셀 저장용 컬럼 순서 (사용자 기존 양식과 100% 동일 + 확장 통계)
    export_cols = [
        '회차', '추첨일', '당첨번호 1', '2', '3', '4', '5', '6', '보너스번호',
        '지난회 번호', '낮은 번호', '높은 번호', '홀수', '짝수',
        '1-10', '11-20', '21-30', '31-40', '41-45', '총합', 'AC값', '최대연속수', '최대동일끝수',
        '1등 당첨자수', '1등 당첨금액', '2등 당첨자수', '2등 당첨금액',
        '3등 당첨자수', '3등 당첨금액', '4등 당첨자수', '4등 당첨금액',
        '5등 당첨자수', '5등 당첨금액', '자동', '수동', '반자동', '총판매금액'
    ]
    
    df_export = df[export_cols].copy()
    
    # 최신 회차가 상단에 오도록 내림차순 정렬 시트도 함께 제공
    df_desc = df_export.sort_values(by='회차', ascending=False)
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_desc.to_excel(writer, sheet_name='최신순_당첨이력', index=False)
        df_export.to_excel(writer, sheet_name='회차순_당첨이력', index=False)
    print(f" [1/3] 엑셀 파일 생성 완료: {excel_path} (1회~{df['회차'].max()}회 전체)")
    
    df_desc.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f" [2/3] CSV 파일 생성 완료: {csv_path}")
    
    # 웹 앱 및 빠른 조회를 위한 경량화 JSON
    clean_records = []
    for row in df.to_dict(orient='records'):
        clean_records.append({
            'round': row['회차'],
            'date': row['추첨일'],
            'numbers': [row[1], row[2], row[3], row[4], row[5], row[6]],
            'bonus': row['보너스'],
            'sum': row['총합'],
            'odd_even': f"{row['홀수']}:{row['짝수']}",
            'low_high': f"{row['낮은 번호']}:{row['높은 번호']}",
            'ac': row['AC값'],
            'carryover': row['지난회 번호'],
            'winner_count': row['1등 당첨자수'],
            'prize_1st': row['1등 당첨금액'],
            'auto': row['자동'],
            'manual': row['수동'],
            'semi_auto': row['반자동']
        })
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(clean_records, f, ensure_ascii=False, indent=2)
    print(f" [3/3] JSON 파일 생성 완료: {json_path}")

if __name__ == "__main__":
    df, raw_list = fetch_and_enrich_lotto_data()
    save_all(df, raw_list)
    last = df.iloc[-1]
    print(f"\n 데이터 구축 완료! (총 {len(df)}개 회차)")
    print(f"최신 {last['회차']}회 ({last['추첨일']}): {[last[i] for i in range(1, 7)]} + 보너스 {last['보너스']}")
