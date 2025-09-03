import csv


def export_to_csv(results, filename = "search_results.csv"):
    with open(filename, 'w', encoding = 'utf-8', newline = '') as f :
        writer = csv.writer(f)
        writer.writerow("")
        writer.writerows(results)

