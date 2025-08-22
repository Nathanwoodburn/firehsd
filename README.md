# Fire HSD - Public Handshake API

A Python Flask webserver providing a free public API for the [Handshake](https://handshake.org/) blockchain.

## Features

- Query blocks, headers, transactions, coins, and names from a public HSD node
- No authentication required for read-only endpoints
- Fast, simple, and open source ([AGPLv3](./LICENSE))

## Quick Start

1. **Install requirements**
    ```bash
    python3 -m pip install -r requirements.txt
    ```
2. **Run the dev server**
    ```bash
    python3 server.py
    ```
3. **Production (Gunicorn)**
    ```bash
    python3 main.py
    ```

## API Endpoints

Some examples:
- `/api/v1/status` &mdash; Check HSD node status
- `/api/v1/block/<blockid>` &mdash; Get block data by block id
- `/api/v1/header/<blockid>` &mdash; Get header data by block id
- `/api/v1/tx/<txid>` &mdash; Get transaction info
- `/api/v1/name/<name>` &mdash; Get name info
- `/api/v1/help` &mdash; List all API endpoints

## Configuration

Set environment variables in `.env` or use `example.env`:
```
HSD_HOST=127.0.0.1
HSD_API_KEY=APIKEY
```

## Support & Donations

If you'd like to help keep the service running and growing, consider donating:

- [PayPal](https://paypal.me/nathanwoodburn)
- [Card (Stripe)](https://donate.stripe.com/8wM6pv0VD08Xe408ww)
- [HNS, BTC, or other](https://nathan.woodburn.au/donate)

## License

[GNU AGPLv3](./LICENSE)

&copy; 2025 Nathan Woodburn