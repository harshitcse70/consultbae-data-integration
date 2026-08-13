import pandas as pd


FILES = {
    "Naukri": "data/source1_naukri_applicants.csv",
    "Gig Workers": "data/source2_gig_workers.csv",
    "CBNexus": "data/source3_cbnexus_contacts.csv",
}


for source_name, file_path in FILES.items():
    print("\n" + "=" * 60)
    print(source_name)
    print("=" * 60)

    df = pd.read_csv(file_path)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())

    print("\nFirst 5 rows:")
    print(df.head())