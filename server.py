from functools import cache
import json
from flask import (
    Flask,
    make_response,
    redirect,
    request,
    jsonify,
    render_template,
    send_from_directory,
    send_file,
)
import os
import json
import requests
from datetime import datetime, timezone
import dotenv

dotenv.load_dotenv()

HSD_HOST = os.getenv("HSD_HOST", "127.0.0.1")
HSD_PORT = os.getenv("HSD_PORT", "12037")
HSD_API_KEY = os.getenv("HSD_API_KEY", "y5cSK42tgVCdt4E58jkHjI3nQ9GU32bC")


app = Flask(__name__)


def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)


def HSD_URL():
    """
    Returns the HSD URL based on the environment variables.
    """
    if not HSD_API_KEY:
        return f"http://{HSD_HOST}:{HSD_PORT}"
    return f"http://x:{HSD_API_KEY}@{HSD_HOST}:{HSD_PORT}"

# Assets routes


@app.route("/assets/<path:path>")
def send_assets(path):
    if path.endswith(".json"):
        return send_from_directory(
            "templates/assets", path, mimetype="application/json"
        )

    if os.path.isfile("templates/assets/" + path):
        return send_from_directory("templates/assets", path)

    # Try looking in one of the directories
    filename: str = path.split("/")[-1]
    if (
        filename.endswith(".png")
        or filename.endswith(".jpg")
        or filename.endswith(".jpeg")
        or filename.endswith(".svg")
    ):
        if os.path.isfile("templates/assets/img/" + filename):
            return send_from_directory("templates/assets/img", filename)
        if os.path.isfile("templates/assets/img/favicon/" + filename):
            return send_from_directory("templates/assets/img/favicon", filename)

    return render_template("404.html"), 404


# region Special routes
@app.route("/favicon.png")
def faviconPNG():
    return send_from_directory("templates/assets/img", "favicon.png")


@app.route("/.well-known/<path:path>")
def wellknown(path):
    # Try to proxy to https://nathan.woodburn.au/.well-known/
    req = requests.get(f"https://nathan.woodburn.au/.well-known/{path}")
    return make_response(
        req.content, 200, {"Content-Type": req.headers["Content-Type"]}
    )


# endregion


# region Main routes
@app.route("/")
def index():
    # Get current time in the format "dd MMM YYYY hh:mm AM/PM"
    current_datetime = datetime.now().strftime("%d %b %Y %I:%M %p")
    return render_template("index.html", datetime=current_datetime)


@app.route("/<path:path>")
def catch_all(path: str):
    if os.path.isfile("templates/" + path):
        return render_template(path)

    # Try with .html
    if os.path.isfile("templates/" + path + ".html"):
        return render_template(path + ".html")

    if os.path.isfile("templates/" + path.strip("/") + ".html"):
        return render_template(path.strip("/") + ".html")

    # Try to find a file matching
    if path.count("/") < 1:
        # Try to find a file matching
        filename = find(path, "templates")
        if filename:
            return send_file(filename)

    return render_template("404.html"), 404


# endregion


# region API routes

@app.route("/api/v1/status")
def api_status():
    """
    This endpoint checks the status of the HSD node.
    """
    try:
        response = requests.get(HSD_URL())
        if response.status_code == 200:
            data = response.json()
            return jsonify(
                {
                    "status": "HSD is running",
                    "version": data.get("version", "unknown"),
                    "progress": data.get("chain", {}).get("progress", 0),
                    "inbound": data.get("pool", {}).get("inbound", 0),
                    "outbound": data.get("pool", {}).get("outbound", 0),
                    "agent": data.get("pool", {}).get("agent", "unknown"),
                }), 200
        else:
            return jsonify({"error": "HSD is not running"}), 503
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/chain")
def api_chain():
    """
    This endpoint returns the chain status of the HSD node.
    """
    try:
        response = requests.get(HSD_URL())
        if response.status_code == 200:
            if 'chain' in response.json():
                chain_status = response.json()['chain']
                return jsonify({"chain": chain_status}), 200
            else:
                return jsonify({"error": "Chain status not found in response"}), 503
        else:
            return jsonify({"error": "Failed to get chain status"}), 503
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/mempool")
def mempool():
    """
    This endpoint returns the current mempool status from the HSD node.
    """

    try:
        url = f"{HSD_URL()}/mempool"
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Command failed", "status_code": response.status_code}), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/<datatype>/<blockid>")
def api_block_or_header(datatype, blockid):
    """
    This endpoint returns block or header data for the given blockid from the HSD node.
    Allowed datatypes: 'block', 'header'
    """
    if datatype not in ["block", "header"]:
        # Return a 404 error for invalid datatype
        return jsonify({"error": "API endpoint not found"}), 400
    try:
        url = f"{HSD_URL()}/{datatype}/{blockid}"
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": f"Failed to get {datatype}", "status_code": response.status_code}), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/coin/<coinhash>/<index>")
def api_coin(coinhash, index):
    """
    This endpoint returns information about a specific coin.
    """
    try:
        url = f"{HSD_URL()}/coin/{coinhash}/{index}"
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Failed to get coin data", "status_code": response.status_code}), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/coin/address/<address>")
def api_coin_address(address):
    """
    This endpoint returns information about coins for a specific address.
    """
    try:
        url = f"{HSD_URL()}/coin/address/{address}"
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Failed to get coins for address", "status_code": response.status_code}), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/tx/<txid>")
def api_transaction(txid):
    """
    This endpoint returns information about a specific transaction.
    """
    try:
        url = f"{HSD_URL()}/tx/{txid}"
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Failed to get transaction data", "status_code": response.status_code}), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/tx/address/<address>")
def api_transaction_address(address):
    """
    This endpoint returns transactions for a specific address.
    """
    try:
        url = f"{HSD_URL()}/tx/address/{address}"
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Failed to get transactions for address", "status_code": response.status_code}), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/name/<name>")
def api_name(name):
    """
    This endpoint returns information about a specific name.
    """
    try:
        url = f"{HSD_URL()}/"
        data = {
            "method": "getnameinfo",
            "params": [name]
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            # Check if error is null
            if 'error' in response.json() and response.json()['error'] is not None:
                return jsonify({"error": response.json()['error']}), 400

            # Check if result is empty
            if 'result' not in response.json() or not response.json()['result']:
                return jsonify({"error": "Name not found"}), 404
            return jsonify(response.json()['result']), 200
        else:
            return jsonify({"error": "Failed to get name data", "status_code": response.status_code}), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/namehash/<namehash>")
def api_namehash(namehash):
    """
    This endpoint returns information about a specific name.
    """
    try:
        url = f"{HSD_URL()}/"
        data = {
            "method": "getnamebyhash",
            "params": [namehash]
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Failed to get name data", "status_code": response.status_code}), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/nameresource/<name>")
def api_nameresource(name):
    """
    This endpoint returns the resource for a specific name.
    """
    try:
        url = f"{HSD_URL()}/"
        data = {
            "method": "getnameresource",
            "params": [name]
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            # Check if error is null
            if 'error' in response.json() and response.json()['error'] is not None:
                return jsonify({"error": response.json()['error']}), 400

            # Check if result is empty
            if 'result' not in response.json() or not response.json()['result']:
                return jsonify({"error": "Resource not found"}), 404
            return jsonify(response.json()['result']), 200
        else:
            return jsonify({"error": "Failed to get name resource", "status_code": response.status_code}), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/namesummary/<name>")
def api_namesummary(name):
    """
    This endpoint returns a summary of a specific name.
    """
    try:
        summary = {
            "name": name,
            "height": None,
            "mintTimestamp": None,
            "mintDate": None,
            "value": None,
            "blocksUntilExpire": None,
            "owner": None,
            "hash": None,
            "state": "CLOSED",
            "resources": [],
            "error": None
        }

        url = f"{HSD_URL()}/"
        data = {
            "method": "getnameinfo",
            "params": [name]
        }
        response = requests.post(url, json=data)
        if response.status_code != 200:
            return jsonify({"error": "Failed to get name summary", "status_code": response.status_code}), response.status_code

        # Check if error is null
        if 'error' in response.json() and response.json()['error'] is not None:
            return jsonify({"error": response.json()['error']}), 400

        # Check if result is empty
        if 'result' not in response.json() or not response.json()['result']:
            return jsonify({"error": "Name summary not found"}), 404
        name_info = response.json()['result']

        if 'info' not in name_info or name_info['info'] is None:
            summary["error"] = "Name info not found"
            return jsonify(summary), 404

        summary["height"] = name_info['info'].get('height', None)
        summary["hash"] = name_info['info'].get('nameHash', None)
        summary["state"] = name_info['info'].get('state', None)

        summary["value"] = name_info['info'].get('value', None)
        # Convert from satoshis to HNS
        if summary["value"] is not None:
            summary["value"] = summary["value"] / 1000000

        if 'stats' in name_info['info']:
            summary["blocksUntilExpire"] = name_info['info']['stats'].get(
                'blocksUntilExpire', None)

        if 'owner' in name_info['info']:
            owner_hash = name_info['info']['owner'].get('hash', None)
            owner_index = name_info['info']['owner'].get('index', None)
            if owner_hash is not None and owner_index is not None:
                # Fetch the owner address using the coin endpoint
                owner_response = requests.get(
                    f"{HSD_URL()}/coin/{owner_hash}/{owner_index}")
                if owner_response.status_code == 200:
                    owner_data = owner_response.json()
                    summary["owner"] = owner_data.get('address', None)

        # If the height it set, get the mint time
        response = requests.get(f"{HSD_URL()}/header/{summary['height']}")
        if response.status_code == 200:
            block_header = response.json()
            if 'time' in block_header:
                summary["mintTimestamp"] = block_header['time']
                summary["mintDate"] = datetime.fromtimestamp(block_header['time'],tz=timezone.utc).isoformat()



        # Get resources
        data = {
            "method": "getnameresource",
            "params": [name]
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            # Check if error is null
            if 'error' in response.json() and response.json()['error'] is not None:
                return jsonify(summary), 200

            # Check if result is empty
            if 'result' not in response.json() or not response.json()['result']:
                return jsonify(summary), 200

            resources = response.json()['result']
            if isinstance(resources, list):
                summary["resources"] = resources
            else:
                summary["resources"].append(resources)

        return jsonify(summary), 200

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/help")
def api_help():
    """
    This endpoint returns a list of available API endpoints and their descriptions.
    """
    api_endpoints = [
        {"endpoint": "/api/v1/status", "description": "Check HSD node status"},
        {"endpoint": "/api/v1/chain", "description": "Get chain status"},
        {"endpoint": "/api/v1/mempool", "description": "Get mempool status"},
        {"endpoint": "/api/v1/block/<blockid>",
            "description": "Get block data by block height or hash"},
        {"endpoint": "/api/v1/header/<blockid>",
            "description": "Get header data by block height or hash"},
        {"endpoint": "/api/v1/coin/<coinhash>/<index>",
            "description": "Get coin info"},
        {"endpoint": "/api/v1/coin/address/<address>",
            "description": "Get coins for address"},
        {"endpoint": "/api/v1/tx/<txid>", "description": "Get transaction info"},
        {"endpoint": "/api/v1/tx/address/<address>",
            "description": "Get transactions for address"},
        {"endpoint": "/api/v1/name/<name>", "description": "Get name info"},
        {"endpoint": "/api/v1/namehash/<namehash>",
            "description": "Get name by hash"},
        {"endpoint": "/api/v1/nameresource/<name>",
            "description": "Get name resource"},
        {"endpoint": "/api/v1/namesummary/<name>",
         "description": "Get a summary of a name"},
        {"endpoint": "/api/v1/help", "description": "List all API endpoints"},

    ]
    return jsonify({"api": api_endpoints}), 200


@app.route("/api/v1")
@app.route("/api/v1/")
@app.route("/api/v1/<catch_all>")
def api_index(catch_all=None):
    """
    This endpoint returns a 404 error for any API endpoint that is not found.
    """
    return jsonify({"error": "API endpoint not found"}), 404

# endregion


# region Demo routes

DEMO_URLS = {
    "status": "/api/v1/status",
    "chain": "/api/v1/chain",
    "mempool": "/api/v1/mempool",
    "block": "/api/v1/block/210241",
    "header": "/api/v1/header/210241",
    "coin": "/api/v1/coin/e6fc6b6759761cfa310c8260de11aacd88481795b4794e1231b0434825763ec8/10",
    "coin/address": "/api/v1/coin/address/hs1qz3fnjn70fs7rdxt57fhrl4yzsqngg55sqyz83a",
    "tx": "/api/v1/tx/e6fc6b6759761cfa310c8260de11aacd88481795b4794e1231b0434825763ec8",
    "tx/address": "/api/v1/tx/address/hs1qz3fnjn70fs7rdxt57fhrl4yzsqngg55sqyz83a",
    "name": "/api/v1/name/woodburn",
    "namehash": "/api/v1/namehash/368d90d6a3cf9fa3a588d0e4c15d2d265896d2c0bf514644f2e9c86df2f00350",
    "nameresource": "/api/v1/nameresource/woodburn",
    "namesummary": "/api/v1/namesummary/woodburn",
    "help": "/api/v1/help"
}


@app.route("/demo/v1/<path:api_name>")
def demo(api_name):
    demo_url = DEMO_URLS.get(api_name, None)
    if not demo_url:
        return render_template("404.html"), 404
    return render_template("demo.html", url=demo_url)


# endregion


# region Error Catching
# 404 catch all
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# endregion
@app.after_request
def add_cors_headers(response):
    # Allow CORS for all API endpoints
    if request.path.startswith('/api/'):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="127.0.0.1")
