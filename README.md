# claim-rewards

Claim rewards for multiple Hive accounts using a single authority account

## Command-line Arguments

```bash
claim-rewards [--posting-key Posting Key] [--debug] [--dry-run] [--accounts PATH]
```

| Argument     | Type | Description                                                                                 |
| ------------ | ---- | ------------------------------------------------------------------------------------------- |
| `--posting-key`      | str  | Posting Posting Key (private key) for authority account. If omitted, uses POSTING_Posting Key env variable. |
| `--debug`    | flag | Enable debug logging.                                                                       |
| `--dry-run`  | flag | Simulate reward claims without broadcasting transactions.                                   |
| `--accounts` | str  | Path to YAML file with accounts and/or Posting Key. If omitted, uses accounts.yaml if available.    |

## Usage Examples

Claim rewards for accounts listed in `accounts.yaml` (using Posting Key from env or YAML):

```bash
claim-rewards
```

Specify a custom accounts file:

```bash
claim-rewards --accounts myaccounts.yaml
```

Provide the posting key directly (not recommended for security reasons):

```bash
claim-rewards --posting-key <YOUR_POSTING_KEY>
```

Enable debug logging:

```bash
claim-rewards --debug
```

Simulate (dry-run) without making actual transactions:

```bash
claim-rewards --dry-run
```

## 🛠️ Installation (Editable/Development Mode)

```bash
# Clone the repo
$ git clone https://github.com/thecrazygm/claim-rewards.git
$ cd claim-rewards

# Install in editable mode (recommended for development)
$ uv sync
# or
$ pip install -e .
```

## 🏃 Usage

After installation, simply run:

```bash
claim-rewards
```

Or use the module directly:

```bash
python -m claim_rewards.main
```

## 🗂️ Project Structure

```bash
claim-rewards/
├── src/
│   └── claim_rewards/
│       ├── __init__.py
│       └── main.py
├── pyproject.toml
├── README.md
└── ...
```

## 📝 Contributing & Linting

- Code style and linting are enforced by Ruff. Run `ruff check .` and `ruff format .` before submitting PRs.
- All configuration is in `pyproject.toml`.

## ❤️ Thanks & Credits

- Built with [Hatchling](https://hatch.pypa.io/latest/)
- Of course [uv](https://docs.astral.sh/uv/) and [Ruff](https://docs.astral.sh/ruff/) for the amazing python tools.
- Maintained by Michael Garcia (@thecrazygm).
