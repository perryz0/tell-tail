import requests, os

class TailscaleAPI:
    """
    Client for interacting with the Tailscale API.
    """

    BASE_URL = "https://api.tailscale.com/api/v2"
    api_token = os.getenv("TAILSCALE_API_TOKEN")
    if not api_token:
        raise ValueError("API Token not found within .env!")

    def __init__(self, api_token):
        """
        Initialize the Tailscale API client.

        :param api_token: Current API key stored in venv.
        """
        self.api_token = api_token

    def _make_request(self, method, endpoint, params=None, data=None):
        """
        Internal method to make HTTP requests to the Tailscale API.

        :param method: HTTP method.
        :param endpoint: API endpoint (relative to BASE_URL).
        :param params: Query params (if applicable).
        :param data: JSON data for POST requests (if any).
        :return: Response object.
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        response = requests.request(
            method,
            url,
            headers=headers,
            params=params,
            json=data,
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)
        return response.json()

    def list_devices(self, tailnet):
        """
        List all devices on the specified tailnet.

        :param tailnet: Tailnet name (e.g., "perryz0@github").
        :return: List of devices.
        """
        endpoint = f"/tailnet/{tailnet}/devices"
        return self._make_request("GET", endpoint)

    def get_device(self, device_id):
        """
        Get details about a specific device.

        :param device_id: The ID of the device.
        :return: Device details.
        """
        endpoint = f"/device/{device_id}"
        return self._make_request("GET", endpoint)

    def delete_device(self, device_id):
        """
        Delete a specific device.

        :param device_id: The ID of the device.
        :return: API response.
        """
        endpoint = f"/device/{device_id}"
        return self._make_request("DELETE", endpoint)

    def expire_device(self, device_id):
        """
        Expire a specific device, effectively removing its session.

        :param device_id: The ID of the device.
        :return: API response.
        """
        endpoint = f"/device/{device_id}/expire"
        return self._make_request("POST", endpoint)
