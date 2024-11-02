import requests

def send_request_with_csrf(url: str, payload: str):
    # Fail-fast validations
    assert isinstance(url, str) and url.startswith("http"), "Invalid URL: URL must be a valid HTTP/HTTPS URL."
    assert isinstance(payload, str) and payload, "Invalid CSRF token: Payload must be a non-empty string."
    
    # Define headers to mimic a browser request, including X-Csrf-Token
    headers = {
        "X-Csrf-Token": payload,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # Send a GET request with the custom headers
    response = requests.get(url, headers=headers)
    
    # Print the response from the server
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:", response.json())
    except ValueError:
        print("Response Text:", response.text)

# Example usage
url = "http://127.0.0.1:5000/CoDE/http"
csrf_token_value = "your_csrf_token_value_here"
send_request_with_csrf(url, csrf_token_value)
