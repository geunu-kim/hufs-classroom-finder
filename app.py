import json
import time
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# 실시간 사용 인원 저장을 위한 딕셔너리
# { "강의실이름": [(타임스탬프, 인원수), ...], ... }
occupancy_data = {}

from flask import send_from_directory

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('.', 'sw.js')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# 애플리케이션 시작 시, 가공된 시간표 데이터를 메모리에 로드합니다.
try:
    with open("data/classroom_schedule.json", "r", encoding="utf-8") as f:
        schedule_data = json.load(f)
    print("classroom_schedule.json 파일을 성공적으로 로드했습니다.")
except FileNotFoundError:
    print("오류: classroom_schedule.json 파일을 찾을 수 없습니다.")
    schedule_data = {}

# 교시별 시작/종료 시간 매핑
PERIOD_TIMES = {
    1: "09:00", 2: "10:00", 3: "11:00", 4: "12:00",
    5: "13:00", 6: "14:00", 7: "15:00", 8: "16:00",
    9: "17:00", 10: "18:00", 11: "19:00", 12: "20:00"
}

def time_to_period(time_str):
    """ 'HH:MM' 형식의 시간을 교시로 변환합니다. (예: '10:30' -> 2교시) """
    try:
        hour = int(time_str.split(':')[0])
        # 9시가 1교시
        if 9 <= hour <= 20:
            return hour - 9 + 1
        return None
    except:
        return None

@app.route('/')
def index():
    """
    메인 HTML 페이지를 렌더링합니다.
    """
    return render_template('index.html')

@app.route('/buildings', methods=['GET'])
def get_buildings():
    """
    모든 고유한 건물 이름 목록을 반환하는 API 엔드포인트입니다.
    """
    if not schedule_data:
        return jsonify({"error": "시간표 데이터가 로드되지 않았습니다."}), 500

    unique_buildings = set()
    for room_name in schedule_data.keys():
        # "사회과학관 201호" -> "사회과학관"
        building_name = room_name.split(' ')[0]
        unique_buildings.add(building_name)
    
    return jsonify(sorted(list(unique_buildings)))

@app.route('/occupancy', methods=['POST'])
def update_occupancy():
    """
    실시간 강의실 사용 인원 정보를 업데이트하는 API. (합산 모델)
    """
    data = request.get_json()
    classroom = data.get('classroom')
    count_range = data.get('count_range')

    if not classroom or not count_range:
        return jsonify({"error": "강의실과 인원 범위 정보가 필요합니다."}), 400

    # 범위 문자열을 대표 숫자로 변환
    count_map = {
        "1명": 1,
        "2명": 2,
        "3명": 3,
        "4명": 4,
        "5명 이상": 5 # 5명 이상은 5로 처리
    }
    count = count_map.get(count_range)
    if count is None:
        return jsonify({"error": "잘못된 인원 범위입니다."}), 400

    now = time.time()
    
    if classroom not in occupancy_data:
        occupancy_data[classroom] = []

    # 새 인원 정보 추가
    occupancy_data[classroom].append((now, count))
    
    # 45분이 지난 데이터 정리
    valid_entries = [(ts, c) for ts, c in occupancy_data[classroom] if now - ts < 2700]
    occupancy_data[classroom] = valid_entries
    
    # 현재 유효한 총 인원수 계산
    total_occupancy = sum(c for ts, c in valid_entries)

    return jsonify({"success": True, "total_occupancy": total_occupancy})

@app.route('/find', methods=['GET'])
def find_empty_classrooms():
    """
    특정 요일, 시간 범위, 건물에 비어있는 강의실 목록을 반환하는 API.
    실시간 사용 인원 정보를 포함합니다.
    """
    day = request.args.get('day')
    start_time = request.args.get('startTime')
    end_time = request.args.get('endTime')
    buildings = request.args.get('buildings')

    if not all([day, start_time, end_time]):
        return jsonify({"error": "요일, 시작 시간, 종료 시간을 모두 입력해주세요."}), 400

    start_period = time_to_period(start_time)
    end_period = time_to_period(end_time)

    if start_period is None or end_period is None or start_period > end_period:
        return jsonify({"error": "시간 입력이 잘못되었습니다."}), 400

    required_periods = set(range(start_period, end_period + 1))

    if not schedule_data:
        return jsonify({"error": "시간표 데이터가 로드되지 않았습니다."}), 500

    selected_buildings = buildings.split(',') if buildings else []
    empty_classrooms = []
    now = time.time()

    for room, schedule in schedule_data.items():
        if selected_buildings:
            if not any(room.startswith(b) for b in selected_buildings):
                continue

        scheduled_periods = set(schedule.get(day, []))
        if not required_periods.isdisjoint(scheduled_periods):
            continue
            
        next_class_period = "없음"
        upcoming_classes = [p for p in scheduled_periods if p > end_period]
        if upcoming_classes:
            next_period = min(upcoming_classes)
            next_class_period = f"{next_period}교시 ({PERIOD_TIMES.get(next_period, '')})"

        # 실시간 사용 인원 계산
        total_occupancy = 0
        if room in occupancy_data:
            # 45분이 지나지 않은 유효한 데이터만 필터링하고, 만료된 데이터는 정리
            valid_entries = [(ts, c) for ts, c in occupancy_data[room] if now - ts < 2700] # 45분 = 2700초
            occupancy_data[room] = valid_entries
            total_occupancy = sum(c for ts, c in valid_entries)

        empty_classrooms.append({
            "classroom": room,
            "next_class": next_class_period,
            "occupancy": total_occupancy
        })
    
    def get_sort_key(room):
        import re
        match = re.search(r' (\d+)', room['classroom'])
        if match:
            room_num_str = match.group(1)
            floor = int(room_num_str[0])
            room_num = int(room_num_str)
            return (floor, room_num)
        return (0, 0)

    sorted_classrooms = sorted(empty_classrooms, key=get_sort_key)
    
    return jsonify(sorted_classrooms)

if __name__ == '__main__':
    # debug=True 모드는 개발 중에 코드가 변경되면 서버를 자동으로 재시작해줍니다.
    app.run(debug=True, port=5001)
