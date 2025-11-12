
import json
import re

def parse_time_location(text):
    """
    '월 1 2 (H101)'와 같은 문자열을 파싱하여
    [('월', [1, 2], 'H101'), ('수', [3, 4], 'H101')] 형태로 반환합니다.
    """
    if not text:
        return []

    # 정규표현식을 사용하여 요일, 교시, 강의실 코드를 추출
    # 예: '월 1 2 (H101)'
    pattern = re.compile(r'([월화수목금토일])\s*([\d\s]+)\s*\(([^)]+)\)')
    
    # 쉼표로 구분된 여러 시간/장소를 처리
    entries = text.split(',')
    parsed_data = []

    for entry in entries:
        match = pattern.search(entry)
        if match:
            day = match.group(1)
            periods_str = match.group(2).strip().split()
            periods = [int(p) for p in periods_str]
            room_code = match.group(3).strip()
            parsed_data.append((day, periods, room_code))
            
    return parsed_data

def get_full_classroom_name(code):
    """
    '3201'과 같은 강의실 코드를 '사회과학관 201호'와 같은 전체 이름으로 변환합니다.
    """
    building_map = {
        '0': '본관',
        '1': '인문과학관',
        '2': '교수학습개발원',
        '3': '사회과학관',
        '5': '법학관',
        '6': '대학원',
        '8': '국제관',
        'C': '사이버관',
        'B': '미네르바컴플렉스',
        'H': '역사관'
    }
    
    # 사이버관과 같이 숫자 부분이 없는 경우 처리
    if code in building_map:
        return building_map[code]

    # 첫 글자가 건물 코드인지 확인
    building_code = code[0]
    if building_code in building_map:
        building_name = building_map[building_code]
        room_number = code[1:]
        return f"{building_name} {room_number}호"
    else:
        # 매핑되지 않은 코드 (예: 외부 강의실)
        return code

# 제외할 강의실 목록 (공용 공간, 특수 공간 등)
BLACKLISTED_ROOMS = {
    "오바마홀", "한예종", "무용실", "운동장",
    "AT B106", "7208"
}

def main():
    """
    메인 실행 함수
    """
    input_filename = "hufs_lectures_2025_2_university_wide.json"
    output_filename = "classroom_schedule.json"
    
    print(f"데이터 가공을 시작합니다: '{input_filename}' -> '{output_filename}'")
    
    try:
        with open(f"/Users/gukim/cli/{input_filename}", "r", encoding="utf-8") as f:
            lectures = json.load(f)
    except FileNotFoundError:
        print(f"오류: '{input_filename}' 파일을 찾을 수 없습니다.")
        print("먼저 hufs_scraper.py를 실행하여 데이터를 수집해주세요.")
        return

    master_schedule = {}
    processed_lectures = 0

    for lecture in lectures:
        time_location_str = lecture.get("강의시간_강의실")
        
        if time_location_str:
            parsed_entries = parse_time_location(time_location_str)
            if not parsed_entries:
                continue

            processed_lectures += 1
            for day, periods, room_code in parsed_entries:
                full_room_name = get_full_classroom_name(room_code)
                
                # 블랙리스트에 있는 강의실은 건너뛰기
                if full_room_name in BLACKLISTED_ROOMS:
                    continue
                
                # 마스터 스케줄에 강의실이 없으면 새로 추가
                if full_room_name not in master_schedule:
                    master_schedule[full_room_name] = {
                        "월": set(), "화": set(), "수": set(),
                        "목": set(), "금": set(), "토": set(), "일": set()
                    }
                
                # 해당 요일에 교시 추가
                master_schedule[full_room_name][day].update(periods)

    # 집합(set)을 정렬된 리스트(list)로 변환
    for room, schedule in master_schedule.items():
        for day in schedule:
            schedule[day] = sorted(list(schedule[day]))

    # 가공된 데이터를 JSON 파일로 저장
    with open(f"/Users/gukim/cli/{output_filename}", "w", encoding="utf-8") as f:
        json.dump(master_schedule, f, ensure_ascii=False, indent=4)

    print(f"\n총 {len(lectures)}개의 강의 중 {processed_lectures}개의 시간표를 처리했습니다.")
    print(f"총 {len(master_schedule)}개의 고유한 강의실을 찾았습니다. (블랙리스트 제외)")
    print(f"강의실별 시간표 데이터를 '{output_filename}' 파일로 성공적으로 저장했습니다.")

if __name__ == "__main__":
    main()
