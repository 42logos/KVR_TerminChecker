import requests
import json
def get_available_days(start_date, end_date, office_id, service_id, service_count=1, captcha_token=None):
    """
    Simulate GET request to Munich appointment system API
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        office_id (str): Office ID
        service_id (str): Service ID
        service_count (int): Number of services (default: 1)
        captcha_token (str): Captcha token (optional)
    
    Returns:
        requests.Response: API response
    """
    url = "https://www48.muenchen.de/buergeransicht/api/backend/available-days/"
    
    params = {
        'startDate': start_date,
        'endDate': end_date,
        'officeId': office_id,
        'serviceId': service_id,
        'serviceCount': service_count
    }
    
    if captcha_token!= None:
        params['captchaToken'] = captcha_token
    else:
        params['captchaToken'] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpcCI6IjJhMDI6ODEwZDo5YTU6YjAwMDpiMTUyOjcyZGU6NTdkNjplOTFkIiwiaWF0IjoxNzU1MjE1MDg5LCJleHAiOjE3NTUyMTUzODl9.PsL-o9vlEvFFaxxcaiws8zNeImYQizFIgC3Npz51dQo"
    headers = {
        'Host': 'www48.muenchen.de',
        'Sec-Ch-Ua': '"Chromium";v="125", "Not.A/Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Accept': '*/*',
        'Origin': 'https://stadt.muenchen.de',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://stadt.muenchen.de/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Priority': 'u=1, i',
        'Connection': 'keep-alive'
    }
    
    response = requests.get(url, params=params, headers=headers)
    return response


def is_available():
    """
    Check if the appointment system is available by making a test request.
    
    Returns:
        bool: True if available, False otherwise
    """
    try:
        response = get_available_days(
        start_date="2025-08-15",
        end_date="2026-02-15", 
        office_id="10187259",
        service_id="10339027"
    )
        data = response.json()
        if not isinstance(data, dict):
            return False
        if len(data.keys()) == 1 and 'errors' in data.keys():
            if data['errors'][0]['errorCode'] == "captchaExpired" or data['errors'][0]['errorCode'] == "captchaInvalid":
                print(json.dumps(data, indent=4, ensure_ascii=False))
                raise ValueError("Captcha expired, please get a new token.")
            else:
                return False
    except requests.RequestException as e:
        print(f"Error checking availability: {e}")
        return False
    
def get_captcha_token():
    """
    Get a captcha token by making a POST request to the captcha-verify endpoint.

    Returns:
        str: Captcha token if successful, None otherwise
    """
    url = "https://www48.muenchen.de/buergeransicht/api/backend/captcha-verify/"

    headers = {
        'Host': 'www48.muenchen.de',
        'Sec-Ch-Ua': '"Chromium";v="125", "Not.A/Brand";v="24"',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Ch-Ua-Mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Origin': 'https://stadt.muenchen.de',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://stadt.muenchen.de/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Priority': 'u=1, i',
        'Connection': 'keep-alive'
    }

    payload = {
        "payload": "eyJhbGdvcml0aG0iOiJTSEEtMjU2IiwiY2hhbGxlbmdlIjoiOWZkNzkyMzRlODU5NmY2ZmE3NTZlMzdmMTZlMjIzOWJmYTE0NDVlMDQ0ZjNhYzY2NTY0OWVkNmQ2ZTllNjgzMiIsIm51bWJlciI6NDE2NTEsInNhbHQiOiI4ZTI5MjlkYjFlZDQwNTY4YjIwNTRmMWQ/ZXhwaXJlcz0xNzU1MjE0OTc2Iiwic2lnbmF0dXJlIjoiZDQ5MzJmYTUxMGNlMDAxZDU4YjQ2ODk0MDE4NmVlMmYwYzMyOGI2YzMxMGM0MWVlNGIyOWQ4NGQ1ZThkMDUyZSIsInRvb2siOjI5NH0="
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data.get('token')
        return None
    except requests.RequestException as e:
        print(f"Error getting captcha token: {e}")
        return None
# Example usage
if __name__ == "__main__":
    # response = get_available_days(
    #     start_date="2025-08-15",
    #     end_date="2026-02-15", 
    #     office_id="10187259",
    #     service_id="10339027",
    # )
    # print(f"Status: {response.status_code}")
    # print(f"Response: {response.text}")
    
    # print(f"Available: {is_available()}")
    
    # example for getting captcha token if the old one is expired
    token = get_captcha_token()
    print(f"Captcha Token: {token}")
    
    response = get_available_days(
        start_date="2025-08-15",
        end_date="2026-02-15",
        office_id="10187259",
        service_id="10339027",
        service_count=1,
        captcha_token=token
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
