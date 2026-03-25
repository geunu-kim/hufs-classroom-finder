import json
import re

def parse_lecture_time_room(time_room_str):
    """
    Parses the "강의시간_강의실" string to extract day, periods, and raw room number.
    Example: "월 7 8 9 (2508)" -> day='월', periods=[7, 8, 9], raw_room='2508'
    """
    match = re.match(r'([월화수목금토일])\s+([\d\s]+)\s+\((.+)\)', time_room_str)
    if match:
        day = match.group(1)
        periods = [int(p) for p in match.group(2).split()]
        raw_room = match.group(3)
        return day, periods, raw_room
    return None, None, None

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

def map_raw_room_to_full_name(raw_room):
    return get_full_classroom_name(raw_room)

def main():
    input_file = "/Users/gukim/hufs_lectures_2026_1_university_wide.json"
    output_file = "/Users/gukim/hufs-classroom-finder/data/classroom_schedule.json"

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lectures = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file}")
        return

    classroom_schedule = {}

    for lecture in lectures:
        time_room_str = lecture.get("강의시간_강의실")
        if not time_room_str:
            continue

        day, periods, raw_room = parse_lecture_time_room(time_room_str)

        if day and periods and raw_room:
            full_classroom_name = map_raw_room_to_full_name(raw_room) # This needs proper implementation

            if full_classroom_name not in classroom_schedule:
                classroom_schedule[full_classroom_name] = {
                    "월": [], "화": [], "수": [], "목": [], "금": [], "토": [], "일": []
                }
            
            # Add periods, ensuring no duplicates and sorted
            current_periods = classroom_schedule[full_classroom_name][day]
            for p in periods:
                if p not in current_periods:
                    current_periods.append(p)
            current_periods.sort()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(classroom_schedule, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully processed {len(lectures)} lectures and saved to {output_file}")

if __name__ == "__main__":
    main()
