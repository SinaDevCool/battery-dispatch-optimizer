from pathlib import Path


def main():
    raw_data_dir = Path("data/raw")
    processed_data_dir = Path("data/processed")
    output_data_dir = Path("data/outputs")

    raw_data_dir.mkdir(parents=True, exist_ok=True)
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    output_data_dir.mkdir(parents=True, exist_ok=True)

    print("Data folders are ready:")
    print(f"Raw data: {raw_data_dir}")
    print(f"Processed data: {processed_data_dir}")
    print(f"Outputs: {output_data_dir}")

    print("\nNext step:")
    print("Later this script will download/update data from:")
    print("- Netztransparenz API")
    print("- ENTSO-E API")
    print("- forecast model outputs")


if __name__ == "__main__":
    main()