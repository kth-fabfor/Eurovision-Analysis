import json
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

def create_country_file(result_file_path, input_file_path):
    with open(input_file_path, "r") as input_file:
        lines = input_file.readlines()
        countries = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            name = line.split("\t")[0].strip()
            countries[name] = {}

    with open(result_file_path, "w") as f:
        json.dump(countries, f, indent=4)

def read_points(result_file_path, input_file_path):
    countries = json.load(open(result_file_path, "r"))
    countries = {country: {} for country in sorted(countries.keys(), key=lambda x: x.lower())}
    countries["Rest of the World"] = {}

    input_file = open(input_file_path, "r")

    for line in input_file:
        line = line.strip()
        if not line:
            continue
        name = line.split("\t")[0].strip()
        total = int(line.split("\t")[1].strip())
        for i, country in enumerate(countries.keys()):
            try:
                result = int(line.split("\t")[2 + i].strip())
            except:
                result = 0
            countries[country][name] = result
            
            
    input_file.close()

    with open(result_file_path, "w") as f:
        json.dump(countries, f, indent=4)

def read_results(result_file_path):
    countries = pd.read_json(result_file_path)
    return countries

def allocate_points(voting_results: dict[str, dict[str, int]]):
    """
    Allocate points to countries based on their voting results.
    """
    points = {}
    for country, votes in voting_results.items():
        points[country] = {}
        votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        for i, (voted_country, vote_count) in enumerate(votes):
            if i == 0:
                points[country][voted_country] = 12
            elif i == 1:
                points[country][voted_country] = 10
            elif i == 2:
                points[country][voted_country] = 8
            elif i == 3:
                points[country][voted_country] = 7
            elif i == 4:
                points[country][voted_country] = 6
            elif i == 5:
                points[country][voted_country] = 5
            elif i == 6:
                points[country][voted_country] = 4
            elif i == 7:
                points[country][voted_country] = 3
            elif i == 8:
                points[country][voted_country] = 2
            elif i == 9:
                points[country][voted_country] = 1
            else:
                points[country][voted_country] = 0
    points_df = pd.DataFrame(points).T
    return points_df

def draw_points_bar_chart(points):
    """
    Draw a histogram of the points allocated to each country.
    """
    plt.figure(figsize=(10, 6))
    plt.bar(points.index, points.sum(axis=1))
    plt.xlabel("Countries")
    plt.ylabel("Points")
    plt.title("Points allocated to each country")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

def draw_points_histogram_for_country(points, country):
    """
    Draw a histogram of the points allocated to a specific country.
    """
    plt.figure(figsize=(10, 6))
    plt.hist(points.T[country], bins=10)
    plt.xlabel("Points")
    plt.ylabel("Frequency")
    plt.title(f"Points allocated to {country}")
    plt.tight_layout()
    plt.show()

def compile_data(year): 
    create_country_file(f"pandas_results/{year}_ESC_points_pandas_ready.json", f"raw_data/{year}_countries.txt")
    read_points(f"pandas_results/{year}_ESC_points_pandas_ready.json", f"raw_data/{year}_points.txt")

def read_polling_results(year): 
    """
    Read the polling results from the file and return a dictionary of countries and their votes.
    """
    with open(f"raw_data/{year}_poll.txt", "r") as input_file:
        lines = input_file.readlines()
        countries = {}
        for i, line in enumerate(lines[::2]):
            number_of_votes = int(line.replace(",", "").strip())
            country = lines[2 * i + 1].strip()
            countries[country] = number_of_votes

    country_df = pd.DataFrame(countries.items(), columns=["Country", "Votes"])
    country_df = country_df.sort_values(by="Votes", ascending=False)
    country_df = country_df.set_index("Country")
    return country_df

# Investigate the statistical significance of the polling compared to the actual results
def run_polling_comparison(year):
    # Read the polling results
    polling_results = read_polling_results(year)
    polling_results_normalized = polling_results / polling_results.sum()
    # Create a DataFrame with the polling results
    polling_results_df = pd.DataFrame(polling_results_normalized).reset_index()
    polling_results_df.columns = ["Country", "Votes"]
    polling_results_df = polling_results_df.set_index("Country")
    polling_results_df = polling_results_df.sort_values(by="Country", ascending=False)

    # Read the actual results
    actual_results = read_results(f"pandas_results/{year}_ESC_points_pandas_ready.json")
    actual_results = actual_results.sum(axis=1).sort_values(ascending=False)
    actual_results_normalized = actual_results / actual_results.sum()

    # Creat a DataFrame with the actual results
    actual_results_normalized = pd.DataFrame(actual_results_normalized).reset_index()
    actual_results_normalized.columns = ["Country", "Votes"]
    actual_results_normalized = actual_results_normalized.set_index("Country")
    actual_results_normalized = actual_results_normalized.sort_values(by="Country", ascending=False)

    # Create a DataFrame with the polling and actual results
    comparison_df = pd.DataFrame({
        "Polling": polling_results_normalized["Votes"],
        "Actual": actual_results_normalized["Votes"]
    })
    comparison_df = comparison_df.dropna()

    # Calculate the correlation
    correlation, p_value = stats.pearsonr(comparison_df["Polling"], comparison_df["Actual"])
    print(f"Correlation between polling and actual results for {year}: {correlation:.2f} (p-value: {p_value:.2e})")

    # Draw the correlation with 2 standard deviations
    plt.figure(figsize=(10, 6))
    plt.scatter(comparison_df["Polling"], comparison_df["Actual"])
    plt.xlabel("Polling Results")
    plt.ylabel("Actual Results")
    plt.title(f"Polling vs Actual Results for {year} (Correlation: {correlation:.2f})")
    plt.xlim(0, 0.2)
    plt.ylim(0, 0.2)
    plt.plot([0, 0.2], [0, 0.2], color="black", linestyle="--")
    plt.tight_layout()
    plt.grid()
    plt.savefig(f"figures/{year}_polling_vs_actual.png")
    plt.show()

    return correlation, p_value

def investigate_yearly_correlation():
    correlations = []
    years = []
    p_values = []
    
    for year in range(2021, 2026): 
        try:
            correlation, p_value = run_polling_comparison(year)
            correlations.append(correlation)
            p_values.append(p_value)
            years.append(year)
        except Exception as e:
            print(f"Error processing year {year}: {e}")

    # Create a figure for the correlation
    plt.figure(figsize=(10, 6))
    plt.plot(years, correlations, marker="o")
    plt.xlabel("Year")
    plt.ylabel("Correlation")
    plt.title("Correlation between polling and actual results")
    plt.xticks(years)
    plt.grid()
    plt.savefig("figures/polling_vs_actual_correlation.png")
    plt.show()

    # Create a figure for the p-values
    plt.figure(figsize=(10, 6))
    plt.plot(years, p_values, marker="o")
    plt.xlabel("Year")
    plt.ylabel("p-value")
    plt.title("p-value for correlation between polling and actual results")
    plt.xticks(years)
    plt.grid()
    plt.savefig("figures/polling_vs_actual_p_value.png")
    plt.show()

def detect_outliers(year): 
    """
    Detect outliers in the voting results for a specific year, compared to the polling of that year.
    """
    # Read the actual results
    actual_results = read_results(f"pandas_results/{year}_ESC_points_pandas_ready.json")
    actual_results = actual_results.sum(axis=1).sort_values(ascending=False)
    actual_results_normalized = actual_results / actual_results.sum()
    actual_results_normalized = pd.DataFrame(actual_results_normalized).reset_index()
    actual_results_normalized.columns = ["Country", "Votes"]
    actual_results_normalized = actual_results_normalized.set_index("Country")
    actual_results_normalized = actual_results_normalized.sort_values(by="Country", ascending=False)

    # Read the polling results
    polling_results = read_polling_results(year)
    polling_results_normalized = polling_results / polling_results.sum()
    polling_results_df = pd.DataFrame(polling_results_normalized).reset_index()
    polling_results_df.columns = ["Country", "Votes"]
    polling_results_df = polling_results_df.set_index("Country")
    polling_results_df = polling_results_df.sort_values(by="Country", ascending=False)

    comparison_df = pd.DataFrame({
        "Polling": polling_results_normalized["Votes"],
        "Actual": actual_results_normalized["Votes"]
    })
    comparison_df = comparison_df.dropna()

    difference = actual_results_normalized - polling_results_normalized

    difference = difference.dropna()

    # Calculate the z-scores
    z_scores = stats.zscore(difference)

    # Create a DataFrame with the z-scores
    z_scores_df = pd.DataFrame(z_scores, index=difference.index, columns=["Votes"])

    # Plot the actual results, polling results, and z-scores, with the z-scores being represented by the color of the points. Circle the outliers.
    plt.figure(figsize=(10, 6))
    plt.scatter(comparison_df["Polling"], comparison_df["Actual"], c=z_scores_df["Votes"], cmap="coolwarm", s=100)
    outliers = z_scores_df[abs(z_scores_df["Votes"]) > 2].index
    for outlier in outliers:
        plt.annotate(f"{outlier}: {z_scores_df.loc[outlier]['Votes']:.2f}", (comparison_df["Polling"][outlier], comparison_df["Actual"][outlier]), fontsize=12, color="black", ha="left", va="bottom")
    plt.xlabel("Polling Results")
    plt.ylabel("Actual Results")
    plt.title(f"Outlier Detection for {year} (Z-scores)")
    plt.colorbar(label="Z-score")
    plt.xlim(0, 0.2)
    plt.ylim(0, 0.2)
    plt.plot([0, 0.2], [0, 0.2], color="black", linestyle="--")
    plt.tight_layout()
    plt.grid()
    plt.savefig(f"figures/{year}_outlier_detection.png")
    plt.show()

def detect_outliers_excluding_countries(year, countries_to_exclude): 
    """
    Detect outliers in the voting results for a specific year, compared to the polling of that year.
    """
    # Read the actual results
    actual_results = read_results(f"pandas_results/{year}_ESC_points_pandas_ready.json")
    actual_results = actual_results.sum(axis=1).sort_values(ascending=False)
    actual_results_normalized = actual_results / actual_results.sum()
    actual_results_normalized = pd.DataFrame(actual_results_normalized).reset_index()
    actual_results_normalized.columns = ["Country", "Votes"]
    actual_results_normalized = actual_results_normalized.set_index("Country")
    actual_results_normalized = actual_results_normalized.sort_values(by="Country", ascending=False)

    # Read the polling results
    polling_results = read_polling_results(year)
    polling_results_normalized = polling_results / polling_results.sum()
    polling_results_df = pd.DataFrame(polling_results_normalized).reset_index()
    polling_results_df.columns = ["Country", "Votes"]
    polling_results_df = polling_results_df.set_index("Country")
    polling_results_df = polling_results_df.sort_values(by="Country", ascending=False)

    comparison_df = pd.DataFrame({
        "Polling": polling_results_normalized["Votes"],
        "Actual": actual_results_normalized["Votes"]
    })

    # Exclude the specified countries from the comparison
    for country in countries_to_exclude:
        if country in comparison_df.index:
            comparison_df = comparison_df.drop(country)

    comparison_df = comparison_df.dropna()

    difference = comparison_df["Actual"] - comparison_df["Polling"]

    difference = difference.dropna()

    # Calculate the z-scores
    z_scores = stats.zscore(difference)

    # Create a DataFrame with the z-scores
    z_scores_df = pd.DataFrame(z_scores, index=difference.index, columns=["Votes"])

    # Calculate the correlation
    correlation, p_value = stats.pearsonr(comparison_df["Polling"], comparison_df["Actual"])
    print(f"Correlation between polling and actual results for {year} (excluding countries): {correlation:.2f} (p-value: {p_value:.2e})")

    # Plot the actual results, polling results, and z-scores, with the z-scores being represented by the color of the points. Circle the outliers.
    plt.figure(figsize=(10, 6))
    plt.scatter(comparison_df["Polling"], comparison_df["Actual"], c=z_scores_df["Votes"], cmap="coolwarm", s=100)
    outliers = z_scores_df[abs(z_scores_df["Votes"]) > 2].index
    for outlier in outliers:
        plt.annotate(f"{outlier}: {z_scores_df.loc[outlier]['Votes']:.2f}", (comparison_df["Polling"][outlier], comparison_df["Actual"][outlier]), fontsize=12, color="black", ha="left", va="bottom")
    plt.xlabel("Polling Results")
    plt.ylabel("Actual Results")
    plt.title(f"Outlier Detection for {year} (Z-scores)")
    plt.colorbar(label="Z-score")
    plt.xlim(0, 0.2)
    plt.ylim(0, 0.2)
    plt.plot([0, 0.2], [0, 0.2], color="black", linestyle="--")
    plt.tight_layout()
    plt.grid()
    plt.savefig(f"figures/{year}_outlier_detection_excluding_countries.png")
    plt.show()