
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- 설정 ---
# !!! 실행 전, 반드시 실제 학번과 비밀번호로 수정해주세요 !!!
USER_ID = "202200451"
USER_PASSWORD = "qkdrhd12!@"
# !!! 경고: 이 정보를 다른 사람과 공유하지 마세요 !!!

LOGIN_URL = "https://wis.hufs.ac.kr/"
# 로그인 후 이동할 강의 조회 페이지
LECTURE_PAGE_URL = "https://wis.hufs.ac.kr/src08/jsp/lecture/LECTURE2020L.jsp"

def handle_swal_popup(driver):
    """
    SweetAlert 팝업을 감지하고 닫는 함수.
    팝업을 닫았으면 True, 팝업이 없었으면 False를 반환합니다.
    """
    try:
        # 팝업 버튼이 실제로 클릭 가능한 상태가 될 때까지 대기
        swal_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "swal-button--confirm"))
        )
        print("    - (팝업 감지) 경고 팝업을 닫습니다.")
        driver.execute_script("arguments[0].click();", swal_button)
        
        # 팝업 창이 DOM에서 완전히 사라질 때까지 최대 5초 대기
        WebDriverWait(driver, 5).until(
            EC.staleness_of(swal_button)
        )
        print("    - (팝업 확인) 팝업이 완전히 닫혔습니다.")
        return True
    except:
        return False

def main():
    """
    메인 실행 함수
    """
    print("자동화 스크립트를 시작합니다.")
    
    if USER_ID == "YOUR_ID" or USER_PASSWORD == "YOUR_PASSWORD":
        print("오류: 스크립트 상단의 USER_ID와 USER_PASSWORD를 실제 정보로 수정해주세요.")
        return

    driver = None
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        
        # 로그인
        print(f"로그인 페이지({LOGIN_URL})에 접속합니다.")
        driver.get(LOGIN_URL)
        print("아이디와 비밀번호를 입력합니다.")
        id_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div/form[3]/div[2]/div/div[2]/div/input[1]")))
        id_field.send_keys(USER_ID)
        pw_field = driver.find_element(By.NAME, "password")
        pw_field.send_keys(USER_PASSWORD)
        print("로그인 버튼을 클릭합니다.")
        login_button = driver.find_element(By.XPATH, "/html/body/div/form[3]/div[2]/div/div[2]/div/a")
        login_button.click()
        print("로그인 성공을 기다립니다...")
        time.sleep(5)
        
        # 강의 조회 페이지로 이동
        print(f"강의 조회 페이지({LECTURE_PAGE_URL})로 이동합니다.")
        driver.get(LECTURE_PAGE_URL)
        print("페이지가 완전히 로드되기를 기다립니다...")
        time.sleep(3)

        # --- 1. 조회 조건 설정: 2025년 2학기 ---
        print("조회 조건을 '2025년 2학기'로 설정합니다.")
        Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ag_ledg_year")))).select_by_value("2026")
        time.sleep(1)
        Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ag_ledg_sessn")))).select_by_value("1")
        time.sleep(3)

        # --- 2. 모든 소속 목록 가져오기 ---
        print("전체 소속 목록을 가져옵니다...")
        affiliation_select_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ag_org_sect")))
        affiliations = [{"name": opt.text.strip(), "value": opt.get_attribute("value")} for opt in Select(affiliation_select_element).options if opt.get_attribute("value")]

        all_lectures = []
        search_button = driver.find_element(By.NAME, "btnSearch")

        # --- 3. 모든 소속, 모든 강의 구분에 대해 스크레이핑 ---
        for aff in affiliations:
            print(f"\n====================================================")
            print(f"소속: '{aff['name']}'({aff['value']}) 스크레이핑 시작...")
            
            try:
                Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ag_org_sect")))).select_by_value(aff['value'])
                if handle_swal_popup(driver): continue
                time.sleep(2)

                # 사용자 피드백 반영: 소속 변경 후 조회 버튼 클릭
                print("    - (수정) 소속 변경 후 조회 버튼을 클릭하여 초기 데이터를 로드합니다.")
                search_button.click()
                time.sleep(2) # 데이터 로드 대기
                if handle_swal_popup(driver):
                    print("    - (정보) 초기 데이터가 없습니다. 계속 진행합니다.")

            except Exception as e:
                print(f"  - '{aff['name']}' 소속을 선택할 수 없습니다. 건너뜁니다. ({e})")
                continue

            course_types = []
            if aff['value'] == 'A': # 학부
                course_types = [
                    {"name": "전공/부전공", "gubun_value": "1", "select_id": "ag_crs_strct_cd"},
                    {"name": "교양", "gubun_value": "2", "select_id": "ag_compt_fld_cd"},
                    {"name": "기초", "gubun_value": "3", "select_id": "ag_basic_fld_cd"}
                ]
            else: # 대학원
                course_types = [{"name": "전공/공통/논문", "gubun_value": "1", "select_id": "ag_crs_strct_cd_b"}]

            for course_type in course_types:
                print(f"\n--- '{course_type['name']}' 강의 목록 추출 시작 ---")
                
                try:
                    if aff['value'] == 'A':
                        gubun_radio = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, f"input[name='gubun'][value='{course_type['gubun_value']}']")))
                        driver.execute_script("arguments[0].click();", gubun_radio)
                        if handle_swal_popup(driver): continue
                        time.sleep(2)

                        # 사용자 피드백 반영: 첫 데이터 로드를 위해 조회 버튼 클릭
                        print("    - (수정) 조회 버튼을 클릭하여 초기 데이터를 로드합니다.")
                        search_button.click()
                        time.sleep(2) # 데이터 로드 대기
                        if handle_swal_popup(driver):
                            print("    - (정보) 초기 데이터가 없습니다. 계속 진행합니다.")

                    current_select = Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, course_type['select_id']))))
                    options_to_scrape = [{"name": opt.text.strip(), "value": opt.get_attribute("value")} for opt in current_select.options if opt.get_attribute("value") and opt.get_attribute("value") != "!_!"]
                    
                    print(f"총 {len(options_to_scrape)}개의 '{course_type['name']}' 영역/학과를 찾았습니다.")

                    for i, option_item in enumerate(options_to_scrape):
                        print(f"  [{i+1}/{len(options_to_scrape)}] {option_item['name']} 데이터 수집 중...")
                        
                        # 1. 학과/영역 선택
                        Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, course_type['select_id'])))).select_by_value(option_item['value'])
                        
                        # 2. onchange로 인해 즉시 팝업이 뜨는지 1초간 확인
                        time.sleep(1) 
                        if handle_swal_popup(driver):
                            print("    - (정보) '데이터 없음' 팝업(onchange) 확인. 건너뜁니다.")
                            continue

                        # 3. onchange 팝업이 없었다면, 조회 버튼을 클릭
                        print("    - (정보) 조회 버튼 클릭.")
                        search_button.click()
                        
                        # 4. 조회 결과로 팝업이 뜨는지 1초간 다시 확인
                        time.sleep(1)
                        if handle_swal_popup(driver):
                            print("    - (정보) '데이터 없음' 팝업(조회) 확인. 건너뜁니다.")
                            continue
                        
                        # 5. 두 번의 팝업 체크를 모두 통과했으면, 데이터가 로드되기를 기다린 후 파싱
                        try:
                            WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "#lssnlist tr"))
                            )
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            lssnlist_tbody = soup.find('tbody', id='lssnlist')
                            
                            if lssnlist_tbody:
                                rows = lssnlist_tbody.find_all('tr')
                                print(f"    - {len(rows)}개의 강의를 발견하여 수집합니다.")
                                for row in rows:
                                    cols = row.find_all('td')
                                    if len(cols) > 15:
                                        all_lectures.append({
                                            "소속": aff['name'],
                                            "강의구분": course_type['name'],
                                            "학과_영역명": option_item['name'],
                                            "학수번호": cols[3].text.strip(),
                                            "교과목명": cols[4].text.strip(),
                                            "담당교수": cols[11].text.strip(),
                                            "학점": cols[12].text.strip(),
                                            "강의시간_강의실": cols[14].text.strip(),
                                        })
                        except:
                            print("    - (경고) 데이터 테이블을 찾을 수 없어 파싱에 실패했습니다.")
                            continue
                except Exception as e:
                    print(f"  - '{course_type['name']}' 처리 중 오류 발생. 다음으로 넘어갑니다. ({e})")
                    continue
        
        output_filename = "hufs_lectures_2026_1_university_wide.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(all_lectures, f, ensure_ascii=False, indent=4)
        
        print(f"\n====================================================")
        print(f"총 {len(all_lectures)}개의 강의 데이터를 '{output_filename}' 파일로 저장했습니다.")
        print("스크립트 실행 완료. 10초 후 종료합니다.")
        time.sleep(10)

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        if driver:
            driver.save_screenshot("error_screenshot.png")
            print("에러 스크린샷을 'error_screenshot.png' 파일로 저장했습니다.")
        time.sleep(10)
        
    finally:
        if driver:
            driver.quit()
        print("스크립트를 종료합니다.")

if __name__ == "__main__":
    main()
