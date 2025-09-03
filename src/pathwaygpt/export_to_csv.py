import csv


def export_to_csv(results, filename ):
    with open(filename, 'w', encoding = 'utf-8', newline = '') as f :
        writer = csv.writer(f)
        writer.writerow("")
        writer.writerows(results)

    print("Do you want a custom csv file for your search keywords?")

    cmd = input("\nCommand (yes, no, y , n): ").strip().lower()
    if cmd in ("yes", "y"):
        custom_filename = (input("Enter your csv file name (with.csv) : ")).strip()
        export_to_csv(results, custom_filename)



