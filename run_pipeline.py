"""Run the full analysis pipeline in order."""

from data_cleaning import main as clean_main
from retail_eda import main as eda_main
from business_analysis import main as biz_main
from generate_report import main as report_main


if __name__ == "__main__":
    clean_main()
    eda_main()
    biz_main()
    report_main()
    print("Pipeline complete.")
