import json
import os
import requests
import time
import sys

git_api = os.environ["GITHUB_API_URL"]
repo = os.environ["GITHUB_REPOSITORY"]
sha = os.environ["INPUT_SHA"]
token = os.environ["INPUT_TOKEN"]
name = os.environ["INPUT_NAME"]
strict = (True if (os.environ["INPUT_STRICT"] == "true") else False)
timeout = (0 if (os.environ["INPUT_TIMEOUT"] == "") else int(os.environ["INPUT_TIMEOUT"]))
seconds = (1 if (os.environ["INPUT_SECONDS"] == "") else int(os.environ["INPUT_SECONDS"]))

statuses_url = f"{git_api}/repos/{repo}/commits/{sha}/status"
checks_url = f"{git_api}/repos/{repo}/commits/{sha}/check-runs"

def wait():
    total_count = 0
    IS_STAT = False
    IS_CHECK = False    
    while total_count == 0:
        statuses = get_data(statuses_url)
        checks = get_data(checks_url)
        if (statuses["total_count"] != 0) or (checks["total_count"] != 0):
            for stat in statuses["statuses"]:
                if stat["context"] == name:
                    IS_STAT = True
                    print("stat is true")
                    total_count = 1
            for check in checks["check_runs"]:
                if check["name"] == name:
                    IS_CHECK = True
                    print("check is true")
                    total_count = 1
        print("Waiting for Runs to start")
        time.sleep(seconds)
    return {"stat":IS_STAT,"check":IS_CHECK}
def main():
    PASSED = 0
    print(statuses_url,checks_url)
    results = wait()
    if results["stat"]:
        print("This is a Status")
        status_code = "pending"
        while status_code not in {'success', 'failed'}:
            status_code = getStatStatus()
            print("In Progress " + status_code)            
            time.sleep(1)
            PASSED = PASSED + 1
            if timeout == PASSED:
                sys.exit("Timeout Reached")            
        if status_code != "success":
            print(f"::set-output name=result::Failed")
            if strict is True:
                sys.exit("Dag Failed")
        else:
            print(f"::set-output name=result::Success")
            sys.exit(0)
    if results["check"]:
        print("This is a Check")
        status_code = "in_progress"
        while status_code not in {'success', 'failed'}:
            temp = getStatStatus()
            if temp["status"] != "in_progress":
                status_code = temp["conclusion"]
            else:
                status_code = temp["status"]
            print("In Progress " + status_code)    
            time.sleep(1)
            PASSED = PASSED + 1
            if timeout == PASSED:
                sys.exit("Timeout Reached")
        if status_code != "success":
            print(f"::set-output name=result::Failed")
            if strict is True:
                sys.exit("Dag Failed")
        else:
            print(f"::set-output name=result::Success")
            sys.exit(0)       

def getStatStatus():
    temp_statuses = get_data(statuses_url)
    for stat in temp_statuses["statuses"]:
        if stat["context"] == name:
            return stat["state"]

def getCheckStatus():
    temp_checks = get_data(checks_url)
    for check in temp_checks["check_runs"]:
        if check["name"] == name:
            return {"status": check["status"],"conclusion": check["conclusion"]}

def get_data(url):
    resp = requests.request(
        "GET",
        url,
        headers={"Authorization": "Bearer " + token},
    )    
    if resp.status_code != 200:
        raise Exception(
            "Bad response from application: " + str(resp.status_code) + " / " + str(resp.headers) + " / " + str(resp.text)
        )
    else:
        data = json.loads(str(resp.text).replace("'", ""))
        return data

if __name__ == "__main__":
    main()