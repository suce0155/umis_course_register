#Title: UMIS Course Registration with capsolver
#Change information on 'set your config' field
#Non-Department (process 2) not working (lazy)


import sys
import requests
import time

# TODO: set your config
email    = ""                                         #UMIS EMAIL
password = ""                                         #UMIS PASSWORD
api_key  = ""                                         #CAPSOLVER API KEY

#GLOBALS
site_key = "6LelIscaAAAAAA0ODBaTFs_FUqS3WTgy-G0bP1pG" 
site_url = "https://umis.bau.edu.tr/login"            
bearer = ""


def menu():
    print("***********************************************")
    print("1.Department Course")
    print("2.Non-Department Course")
    print("3.GE Course")
    print("***********************************************")

def question():
    prompt = input("Create New Token? (Y/N): ")
    if not (prompt.__eq__("Y") or prompt.__eq__("y")):
        sys.exit(0)
    return create_bearer_token()
def capsolver():
    payload = {
        "clientKey": api_key,
        "task": {
            "type": 'ReCaptchaV2TaskProxyLess',
            "websiteKey": site_key,
            "websiteURL": site_url
        }
    }
    res = requests.post("https://api.capsolver.com/createTask", json=payload)
    resp = res.json()
    task_id = resp.get("taskId")
    if not task_id:
        print("Failed to create task:", res.text)
        return
    # print(f"Got taskId: {task_id} / Getting result...")

    while True:
        time.sleep(3)  # delay
        payload = {"clientKey": api_key, "taskId": task_id}
        res = requests.post("https://api.capsolver.com/getTaskResult", json=payload)
        resp = res.json()
        status = resp.get("status")
        if status == "ready":
            return resp.get("solution", {}).get('gRecaptchaResponse')
        if status == "failed" or resp.get("errorId"):
            print("Solve failed! response:", res.text)
            return


def create_bearer_token():
    print("[*] Creating new token...")
    session = requests.session()
    target_url = "https://umis.bau.edu.tr/login"

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
        'Accept': 'application/json',
        'Accept-Language': 'tr',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://umis.bau.edu.tr/',
        'pathname': '/login',
        'Content-Type': 'application/json',
        'Origin': 'https://umis.bau.edu.tr',
        'Connection': 'keep-alive'
    }
    check_req = session.get(target_url)
    # if check_req.status_code == 200:
    # print("Site is up!")

    token = capsolver()

    data = {"email": email,
            "password": password,
            "g_recaptcha_token": token}

    post_req = session.post(url="https://authapi.bau.edu.tr/api/auth/login", data=data)

    if not('status' in post_req.json()):
        print("[-]",post_req.json()['message'])
        sys.exit(0)


    bearer = post_req.json()['data']['access_token']
    print("[+] Token Created: ", bearer)
    print("[*] Writing token to 'umis_token.txt'...")
    with open("umis_token.txt", "w") as file1:
        file1.write(bearer)

    return bearer

def main():
    print(
        "***********************************************\nUMIS COURSE SELECTION\n***********************************************")
    print("[*] Checking For Existing Token...")
    try:
        with open("umis_token.txt", "r") as file:
            bearer = file.readline()
            if bearer.startswith("ey"):
                print("[+] Token Found!")
                print(bearer)
            else:
                print("[-] Couldn't Find Token...")
                bearer = question()


    except FileNotFoundError:
        print("[-] File or token not found.")
        bearer = question()

    api_me = requests.get("https://oisapi.bau.edu.tr/api/v1/users/me",
                          headers={
                              'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
                              'Accept': 'application/json',
                              'Accept-Language': 'tr',
                              'Accept-Encoding': 'gzip, deflate, br',
                              'Referer': 'https://umis.bau.edu.tr/',
                              'Authorization': f'Bearer {bearer}',
                              'Pathname': '/dashboard',
                              'Origin': 'https://umis.bau.edu.tr',
                              'Connection': 'keep-alive'
                          })
    if api_me.json()["success"] == False:
        print("Invalid Token or Something went wrong...")
        sys.exit(0)
    program_id = api_me.json()['data']['student']['id']
    print(f"[+] Found ID: {program_id}")
    print("[*] Printing Student Info...")
    req = requests.get(f"https://oisapi.bau.edu.tr/api/v1/course/registration/{program_id}",
                       headers={
                           'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
                           'Accept': 'application/json',
                           'Accept-Language': 'tr',
                           'Accept-Encoding': 'gzip, deflate, br',
                           'Referer': 'https://umis.bau.edu.tr/',
                           'Authorization': f'Bearer {bearer}',
                           'Pathname': '/dashboard',
                           'Origin': 'https://umis.bau.edu.tr',
                           'Connection': 'keep-alive'
                       })
    if req.json()["success"] == False:
        print("Invalid Token or Something went wrong...")
        sys.exit(0)
    jso = req.json()['data']

    dep_slot = jso['slots'][1]['slots']['not_taken'][0]['id']
    non_slot = jso['slots'][2]['slots']['not_taken'][0]['id']
    ge_slot = jso['slots'][3]['slots']['not_taken'][0]['id']

    student_no = jso['student']['student_number']
    program_name = jso['student']['program_name_en']
    year = jso['student']['class']
    used_credits = jso['student']['sum_of_credits']
    remain_credits = jso['student']['remaining_credits']
    print("***********************************************")
    print(
        f"StudentNo: {student_no}, ProgramName: {program_name}, Year: {year}, Used Credits: {used_credits}, Remaing Credits: {remain_credits}")
    print("***********************************************")
    print("Taken Clases:")
    for i in jso['taken_courses']:
        print(f"Name: {i['course_name_en']},Type: {i['slot_type_text_en']}")

    while True:
        menu()
        inp = input("Process Number:")
        if inp.__eq__("1"):
            req1 = requests.get(
                f"https://oisapi.bau.edu.tr/api/v1/course/registration/{dep_slot}/elective/courses?limit=-1",
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
                    'Accept': 'application/json',
                    'Accept-Language': 'tr',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://umis.bau.edu.tr/',
                    'Authorization': f'Bearer {bearer}',
                    'Pathname': '/dashboard',
                    'Origin': 'https://umis.bau.edu.tr',
                    'Connection': 'keep-alive'
                })
            if req1.json()["success"] == False:
                print("Something Went Wrong with Dep Course Request...")
                continue
            js1 = req1.json()['data']

            temp1_count = 0
            for i in js1:
                if (i['quota'] != 0):
                    print(
                        f"CourseID: {i['course_id']},Name: {i['course_name_en']},Credit: {i['credit']},Quota: {i['quota']},SectionID: {i['sections'][0]['id']}")
                    temp1_count += 1
            if temp1_count == 0:
                print("[-] No Course with space found.")
                temp1_count = 0
            else:
                print("Registering to Course...")
                csid1 = int(input("CourseID of Course:"))
                scid1 = int(input("SectionID of Course:"))

                reg1_data = {"student_program_id": program_id, "student_slot_id": dep_slot, "course_id": csid1,
                             "section_id": scid1}

                post1 = requests.post(f"https://oisapi.bau.edu.tr/api/v1/course/registration",
                                      headers={
                                          'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
                                          'Accept': 'application/json',
                                          'Accept-Language': 'tr',
                                          'Accept-Encoding': 'gzip, deflate, br',
                                          'Referer': 'https://umis.bau.edu.tr/',
                                          'Authorization': f'Bearer {bearer}',
                                          'Pathname': '/dashboard',
                                          'Origin': 'https://umis.bau.edu.tr',
                                          'Connection': 'keep-alive'
                                      }, data=reg1_data)
                print("[!] Server Message: ", post1.json()['message'])







        elif inp.__eq__("2"):
            print("[!] Not Configured.")
            continue

        elif inp.__eq__("3"):
            req3 = requests.get(
                f"https://oisapi.bau.edu.tr/api/v1/course/registration/{ge_slot}/elective/courses?limit=-1",
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
                    'Accept': 'application/json',
                    'Accept-Language': 'tr',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://umis.bau.edu.tr/',
                    'Authorization': f'Bearer {bearer}',
                    'Pathname': '/dashboard',
                    'Origin': 'https://umis.bau.edu.tr',
                    'Connection': 'keep-alive'
                })
            if req3.json()["success"] == False:
                print("Something Went Wrong with Dep Course Request...")
                continue
            js3 = req3.json()['data']
            names3 = {'Aviation Security', 'Community Service Applications', 'Spanish I'}
            temp3_count = 0
            for i in js3:
                if not (i['course_name_en'] in names3) and i['quota'] != 0:
                    print(
                        f"CourseID: {i['course_id']},Name: {i['course_name_en']},Credit: {i['credit']},Quota: {i['quota']},Sections: {i['sections']}")
                    temp3_count += 1
            if temp3_count == 0:
                print("[-] No Course with space found.")
                temp3_count = 0
            else:
                print("Registering to Course...")
                csid3 = int(input("CourseID of Course:"))
                scid3 = int(input("SectionID of Course:"))

                reg1_data = {"student_program_id": program_id,
                             "student_slot_id": ge_slot, "course_id": csid3,
                             "section_id": scid3}
                post3 = requests.post(
                    f"https://oisapi.bau.edu.tr/api/v1/course/registration",
                    headers={
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
                        'Accept': 'application/json',
                        'Accept-Language': 'tr',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Referer': 'https://umis.bau.edu.tr/',
                        'Authorization': f'Bearer {bearer}',
                        'Pathname': '/dashboard',
                        'Origin': 'https://umis.bau.edu.tr',
                        'Connection': 'keep-alive'
                    }, data=reg1_data)
                print("[!] Server Message: ", post3.json()['message'])

        else:
            print("Enter a valid number...")



    
if __name__=="__main__":
    main()

