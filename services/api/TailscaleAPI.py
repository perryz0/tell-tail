import requests, os, logging

class TailscaleAPI:
    """
    Client for interacting with the Tailscale API.
    """

    BASE_URL = "https://api.tailscale.com/api/v2"

    def __init__(self, api_token=None):
        """
        Initialize the Tailscale API client.

        :param api_token: Current API key stored in venv.
        """
        # Load the API token during initialization
        self.api_token = api_token or os.getenv("TAILSCALE_API_TOKEN")
        if not self.api_token:
            raise ValueError("API Token not found within .env!")

    def _make_request(self, method, endpoint, params=None, data=None):
        """
        Internal method to make HTTP requests to the Tailscale API.
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=data,
            )
            response.raise_for_status()  # HTTPError for bad responses (4xx, 5xx)

            # Log raw response to check its format
            logging.info(f"Raw response: {response.text}")

            # Try to parse JSON, handle cases where it fails
            try:
                return response.json()
            except ValueError:
                logging.error(f"Failed to parse JSON from response: {response.text}")
                return None
        except requests.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None

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
