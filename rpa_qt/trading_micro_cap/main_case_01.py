from pathlib import Path


if __name__ == '__main__':
    from trading_script import main

    data_dir = Path(__file__).resolve().parent
    main("case_01/chatgpt_portfolio_update.csv", Path("case_01"))