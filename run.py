# ==========================================
# BaleBet - Run
# ==========================================

from database import init_database
from bot import run


def main():
    print("================================")
    print("        BaleBet Starting...")
    print("================================")

    init_database()

    print("[OK] Database ready")
    print("[OK] Bot is running...")

    run()


if __name__ == "__main__":
    main()