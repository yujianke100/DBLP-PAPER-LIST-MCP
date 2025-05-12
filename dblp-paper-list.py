from typing import Any
import requests
import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dblp-conference-paper-list")

# def fetch_conference_papers(conference_series, year):
#     save_path = './'
@mcp.tool("get_conference_paper_list", "Get conference paper list from DBLP")
async def fetch_conference_papers(conference_series: str, year: str, save_path) -> str:
    """
    Fetch and display the list of papers for the specified conference and year.
    Handles cases where the conference requires appending -1, -2, etc., to the query.

    Args:
        conference_series (str): The name of the conference series (e.g., "ICDE").
        year (str): The year of the conference (e.g., "2024").
        save_path (str): The path to save the results. default is the current directory.
    """
    base_url = "https://dblp.org/search/publ/api"
    query_template = "toc:db/conf/{}/{}{}.bht:"
    results = []
    suffix = ""  # Start with no suffix
    index = 1

    while True:
        # Construct the query
        # 如果是SIGMOD，需要在年份后面加上c
        if conference_series.lower() == "sigmod":
            year = year + "c"
        query = query_template.format(conference_series.lower(), conference_series.lower() + year, suffix)
        api_url = f"{base_url}?q={query}&h=1000&format=json"

        try:
            # Send a GET request to the API
            response = requests.get(api_url)
            response.raise_for_status()

            # Parse the JSON response
            data = response.json()
            total_hits = int(data.get("result", {}).get("hits", {}).get("@total", "0"))

            if total_hits == 0:
                # If no results and suffix is not empty, stop the loop
                if suffix == "":
                    suffix = f"-{index}"
                    continue
                else:
                    if suffix == "-1":
                        return f"No papers found for {conference_series.upper()} {year}."
                    else:
                        break

            # Collect papers from the current query
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            for hit in hits:
                title = hit.get("info", {}).get("title", "Unknown Title")
                authors = hit.get("info", {}).get("authors", {}).get("author", [])
                author_names = ", ".join([author.get("text", "Unknown Author") for author in authors]) if isinstance(authors, list) else authors.get("text", "Unknown Author")
                ee = hit.get("info", {}).get("ee", "Unknown URL")
                results.append((title, author_names, ee))
                # results.append(title)

            # Update suffix for the next iteration
            if suffix != "":
                suffix = f"-{index}"
                index += 1
            else:
                break

        except requests.exceptions.RequestException as e:
            return f"Error while accessing DBLP API: {e}"

    # Display the collected results
    # print(f"\nPapers for {conference_series.upper()} {year}:\n")
    # for idx, (title, authors) in enumerate(results, start=1):
    #     print(f"{idx}. {title}")
    #     print(f"   Authors: {authors}\n")
    # 新建一个文件夹来保存结果，文件夹名称为会议名称和年份
    save_dir = f"{conference_series}_{year}"
    save_dir = os.path.join(save_path, save_dir)
    os.makedirs(save_dir, exist_ok=True)
    # 将results保存到用会议名称和年份命名的文件中
    with open(os.path.join(save_dir, f"{conference_series}_{year}.txt"), "w", encoding="utf-8") as f:
        for idx, result in enumerate(results, start=1):
            f.write(f"{result[0]}\n\n")
    # 再保存一个有作者信息的版本
    with open(os.path.join(save_dir, f"{conference_series}_{year}_with_authors.txt"), "w", encoding="utf-8") as f:
        for idx, result in enumerate(results, start=1):
            f.write(f"{result[0]}\n{result[1]}\n\n")
    # 再保存一个有链接的版本
    with open(os.path.join(save_dir, f"{conference_series}_{year}_with_links.txt"), "w", encoding="utf-8") as f:
        for idx, result in enumerate(results, start=1):
            f.write(f"{result[0]}\n{result[2]}\n\n")

    return "Save completed. Save directory: " + save_dir

# 当用户提供json链接时，按照fetch_conference_papers的逻辑处理并保存到本地。因为已经有json链接了，所以不再需要判断是否有数据啊循环获取suffix以及其他格式了
@mcp.tool("get_conference_paper_list_from_json", "Get conference paper list from DBLP")
async def fetch_conference_papers_from_json(json_url, save_path) -> str:
    """
    Fetch and display the list of papers for the specified conference and year.
    Handles cases where the conference requires appending -1, -2, etc., to the query.

    Args:
        json_url (str): The json url of the conference series.
        save_path (str): The path to save the results. default is the current directory.
    """
    # 保存的文件夹从url中提取，比如https://dblp.org/search/publ/api?q=toc%3Adb/journals/pvldb/pvldb17.bht%3A&h=1000&format=json，保存的文件夹就应该是pvbldb_17
    save_name = json_url.split("/")[-1].split(".")[0]
    # 去除.json这个后缀
    save_name = save_name.split("?")[0]
    save_dir = os.path.join(save_path, save_name)

    results = []

    # Send a GET request to the API
    response = requests.get(json_url)
    response.raise_for_status()

    # Parse the JSON response
    data = response.json()
    total_hits = int(data.get("result", {}).get("hits", {}).get("@total", "0"))


    # Collect papers from the current query
    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    for hit in hits:
        title = hit.get("info", {}).get("title", "Unknown Title")
        authors = hit.get("info", {}).get("authors", {}).get("author", [])
        author_names = ", ".join([author.get("text", "Unknown Author") for author in authors]) if isinstance(authors, list) else authors.get("text", "Unknown Author")
        ee = hit.get("info", {}).get("ee", "Unknown URL")
        results.append((title, author_names, ee))

    # 保存
    # 新建一个文件夹来保存结果，文件夹名称为会议名称和年份
    os.makedirs(save_dir, exist_ok=True)
    # 将results保存到用会议名称和年份命名的文件中
    with open(os.path.join(save_dir, f"{save_name}.txt"), "w", encoding="utf-8") as f:
        for idx, result in enumerate(results, start=1):
            f.write(f"{result[0]}\n\n")
    # 再保存一个有作者信息的版本
    with open(os.path.join(save_dir, f"{save_name}_with_authors.txt"), "w", encoding="utf-8") as f:
        for idx, result in enumerate(results, start=1):
            f.write(f"{result[0]}\n{result[1]}\n\n")
    # 再保存一个有链接的版本
    with open(os.path.join(save_dir, f"{save_name}_with_links.txt"), "w", encoding="utf-8") as f:
        for idx, result in enumerate(results, start=1):
            f.write(f"{result[0]}\n{result[2]}\n\n")
    
    return "Save completed. Save directory: " + save_dir

    

# if __name__ == "__main__":
#     # Example user query
#     user_query = input("Enter the conference query (e.g., 'ICDE 2024'): ")
#     try:
#         # Extract the conference series and year from the query
#         conference_series, year = user_query.split()
#         fetch_conference_papers(conference_series, year)
#     except ValueError:
#         print("Invalid input format. Please use the format 'CONFERENCE YEAR' (e.g., 'ICDE 2024').")
# if __name__ == "__main__":
#     # Example user query
#     user_query = input("Json url: ")
#     try:
#         # Extract the conference series and year from the query

#         fetch_conference_papers_from_json(user_query, os.getcwd())
#     except ValueError:
#         print("Invalid input format. Please use the format 'CONFERENCE YEAR' (e.g., 'ICDE 2024').")
if __name__ == "__main__":
    mcp.run(transport="stdio")