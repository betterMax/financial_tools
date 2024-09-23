import pandas as pd
from difflib import SequenceMatcher
from utilities.similarity_utils import SimilarityCalculator


def calculate_similarity(str1, str2):
    """计算字符串之间的相似度"""
    return SequenceMatcher(None, str1, str2).ratio()


def process_xlsx_and_calculate_similarity(file_path):
    try:
        # 读取CSV文件
        df = pd.read_excel(file_path, sheet_name=0)

        # 检查是否有足够的列
        if df.shape[1] < 4:
            raise ValueError("CSV文件列数不正确，至少应有4列")

        # 提取数据：第1列是类别，第2、3、4列用于相似度计算
        category_column = df.iloc[:, 0]  # 第1列为类别

        # 初始化相似度计算器
        similarity_calculator = SimilarityCalculator(method="jaccard")  # 相似度计算方法是jaccard, cosine, levenshtein

        # 最终结果存储
        final_results = []
        average_similarities = []

        # 针对每个类别进行相似性计算
        for category in category_column.unique():
            # 过滤出相同类别的数据
            same_category_data = df[df.iloc[:, 0] == category]

            # 如果同类记录不足2行，跳过相似度计算
            if len(same_category_data) < 2:
                continue

            category_similarities = []

            # 遍历同类数据，计算每两行之间的相似度
            for i in range(len(same_category_data)):
                for j in range(i + 1, len(same_category_data)):
                    row_1 = same_category_data.iloc[i]
                    row_2 = same_category_data.iloc[j]

                    # 使用 calculate_total_similarity 计算每对记录的相似度
                    similarity_result = similarity_calculator.calculate_total_similarity(
                        row_1[1], row_2[1], row_1[2], row_2[2], row_1[3], row_2[3]
                    )

                    # 记录每列的相似度以及总相似度
                    similarity_details = {
                        "类别": category,
                        "记录1": row_1[1:4].values.tolist(),
                        "记录2": row_2[1:4].values.tolist(),
                        "第2列相似度": similarity_result['similarity_long'],
                        "第3列相似度": similarity_result['similarity_middle'],
                        "第4列相似度": similarity_result['similarity_shape'],
                        "整体相似度": similarity_result['total_similarity']
                    }
                    final_results.append(similarity_details)

                    # 计算该对的总相似度
                    category_similarities.append(similarity_result['total_similarity'])

            # 计算类别下的平均相似性
            if category_similarities:
                average_similarity = sum(category_similarities) / len(category_similarities)
                average_similarities.append({
                    "类别": category,
                    "整体相似度": average_similarity
                })

        return final_results, average_similarities

    except Exception as e:
        print(f"处理文件时发生错误: {e}")
        return [], []


def run(future_history_database_path):
    # 调用主函数进行相似性计算
    pairwise_results, average_results = process_xlsx_and_calculate_similarity(future_history_database_path)

    # 输出每两行之间的相似性结果
    if pairwise_results:
        for result in pairwise_results:
            print(f"类别: {result['类别']} - 记录1: {result['记录1']} - 记录2: {result['记录2']}"
                  f" - 长期趋势相似度: {result['第2列相似度']:.2f} - 中期趋势相似度: {result['第3列相似度']:.2f}"
                  f" - 形态相似度: {result['第4列相似度']:.2f} - 整体相似度: {result['整体相似度']:.2f}")

    # 输出每个类别的平均相似性结果
    if average_results:
        for avg_result in average_results:
            print(f"类别: {avg_result['类别']} - 整体相似度: {avg_result['整体相似度']:.2f}")
