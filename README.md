# claim-rewards

Claim rewards for multiple Hive accounts using a single authority account. This package provides two command-line tools:

- `claim-hive`: Claim Hive blockchain rewards (HIVE, HBD, VESTS)
- `claim-scot`: Claim SCOT token rewards from the Hive-Engine sidechain

## Features

- Claim rewards for multiple accounts using a single posting key
- Support for both Hive blockchain rewards and SCOT tokens
- Configurable via YAML file, command-line arguments, or environment variables
- Dry-run mode to simulate claims without broadcasting transactions
- Detailed logging with debug option

## Command-line Arguments

Both commands (`claim-hive` and `claim-scot`) accept the same arguments:

```bash
claim-hive [--posting-key POSTING_KEY] [--debug] [--dry-run] [--accounts PATH]
claim-scot [--posting-key POSTING_KEY] [--debug] [--dry-run] [--accounts PATH]
```

| Argument           | Type | Description                                                                          |
| ------------------ | ---- | ------------------------------------------------------------------------------------ |
| `-k/--posting-key` | str  | Posting key for the main account. If omitted, uses POSTING_KEY env variable or YAML. |
| `-d/--debug`       | flag | Enable debug logging.                                                                |
| `--dry-run`        | flag | Simulate reward claims without broadcasting transactions.                            |
| `-a/--accounts`    | str  | Path to YAML file with accounts and/or posting key. Defaults to accounts.yaml.       |

## Usage Examples

### Claiming Hive Rewards

Claim Hive rewards for accounts listed in `accounts.yaml` (using posting key from env or YAML):

```bash
claim-hive
```

Specify a custom accounts file:

```bash
claim-hive -a myaccounts.yaml
```

Provide the posting key directly (not recommended for security reasons):

```bash
claim-hive -k <YOUR_POSTING_KEY>
```

Enable debug logging:

```bash
claim-hive -d
```

Simulate (dry-run) without making actual transactions:

```bash
claim-hive --dry-run
```

### Claiming SCOT Token Rewards

Claim SCOT token rewards for accounts listed in `accounts.yaml`:

```bash
claim-scot
```

With debug logging and dry-run mode:

```bash
claim-scot -d --dry-run
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

After installation, you can use either command:

```bash
# For Hive blockchain rewards
claim-hive

# For SCOT token rewards
claim-scot
```

Or use the modules directly:

```bash
# For Hive blockchain rewards
python -m claim_rewards.hive

# For SCOT token rewards
python -m claim_rewards.scot
```

## 🗂️ Project Structure

```bash
claim-rewards/
├── src/
│   └── claim_rewards/
│       ├── __init__.py         # Package version information
│       ├── config.py           # Configuration handling
│       ├── hive_client.py      # Hive blockchain operations
│       ├── logging_setup.py    # Logging configuration
│       ├── hive.py             # Hive rewards claiming script
│       ├── scot.py             # SCOT token rewards claiming script
│       └── scot_client.py      # SCOT token operations
├── pyproject.toml
├── README.md
└── ...
```

## 📄 Configuration

The package can be configured using a YAML file. By default, it looks for `accounts.yaml` in the current directory, but you can specify a different file using the `-a/--accounts` argument.

Example `accounts.yaml`:

```yaml
# List of accounts to claim rewards for
# The first account is used as the authority (posting key must be for this account)
accounts:
  - mainaccount # This account's posting key will be used
  - otheraccount1 # Will use mainaccount's authority
  - otheraccount2 # Will use mainaccount's authority

# Optional: Posting key for the main account
# If not provided, will use POSTING_KEY environment variable
posting_key: 5J... # Your private posting key
```

## 📝 Contributing & Linting

- Code style and linting are enforced by Ruff. Run `ruff check .` and `ruff format .` before submitting PRs.
- All configuration is in `pyproject.toml`.

## ❤️ Thanks & Credits

- [hive-nectar](https://github.com/thecrazygm/hive-nectar/) - Python library for Hive blockchain interactions
- Built with [Hatchling](https://hatch.pypa.io/latest/)
- Of course [uv](https://docs.astral.sh/uv/) and [Ruff](https://docs.astral.sh/ruff/) for the amazing python tools.
- Maintained by Michael Garcia (@thecrazygm).
