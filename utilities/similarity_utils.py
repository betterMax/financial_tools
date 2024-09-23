from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Levenshtein import distance as levenshtein_distance


class SimilarityCalculator:
    def __init__(self, method="jaccard", weight_a=0.2, weight_b=0.4, weight_c=0.4):
        self.weight_a = weight_a
        self.weight_b = weight_b
        self.weight_c = weight_c

        # 配置相似度方法
        self.method = method
        self.similarity_methods = {
            "cosine": self.cosine_similarity,
            "jaccard": self.jaccard_similarity,
            "levenshtein": self.levenshtein_similarity
        }

    @staticmethod
    # 计算余弦相似度
    def cosine_similarity(text1, text2):
        vectorizer = TfidfVectorizer().fit_transform([text1, text2])
        vectors = vectorizer.toarray()
        return cosine_similarity(vectors)[0][1]

    @staticmethod
    # 定义 Jaccard 相似度
    def jaccard_similarity(segment1, segment2):
        set1 = set(segment1)
        set2 = set(segment2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0

    @staticmethod
    # 定义 Levenshtein 相似度
    def levenshtein_similarity(segment1, segment2):
        max_len = max(len(segment1), len(segment2))
        if max_len == 0:
            return 1.0
        return 1 - (levenshtein_distance(segment1, segment2) / max_len)

    # 获取选择的相似度计算方法
    def get_similarity_method(self):
        return self.similarity_methods.get(self.method, self.jaccard_similarity)  # 默认使用 jaccard 相似度

    # 因子A和B的相似度计算（基于 "+" 分隔）
    def calculate_similarity_factor_ab(self, str1, str2):
        if "+" in str1:
            segments_1 = str1.split("+")
        else:
            segments_1 = [str1]
        if "+" in str2:
            segments_2 = str2.split("+")
        else:
            segments_2 = [str2]

        # 获取当前选择的相似度方法
        similarity_method = self.get_similarity_method()
        # print(f"K线走势 - segments1: {segments_1}, segments2: {segments_2}")

        # 情况 1：两组数量相同，按顺序匹配
        if len(segments_1) == len(segments_2):
            similarities = [similarity_method(segments_1[i], segments_2[i]) for i in range(len(segments_1))]
            return sum(similarities) / len(similarities)

        # 情况 2：一组只有1个因子，另一组多个因子，取最大相似度
        elif len(segments_1) == 1 or len(segments_2) == 1:
            if len(segments_1) == 1:
                similarities = [similarity_method(segments_1[0], seg) for seg in segments_2]
            else:
                similarities = [similarity_method(seg, segments_2[0]) for seg in segments_1]
            return max(similarities)

        # 情况 3：两组数量不一致但都大于1，逐对匹配
        else:
            # 判断哪组是 2 个元素，哪组是 3 个元素
            if len(segments_1) == 2 and len(segments_2) == 3:
                shorter_segments = segments_1  # [A1, A2]
                longer_segments = segments_2  # [B1, B2, B3]
            elif len(segments_1) == 3 and len(segments_2) == 2:
                shorter_segments = segments_2  # [A1, A2]
                longer_segments = segments_1  # [B1, B2, B3]
            else:
                raise ValueError("只能处理一组 2 个元素，另一组 3 个元素的情况")

            # 第一步：计算 A1 与 B1、B2 的相似度，选择较大者
            sim_a1_b1 = similarity_method(shorter_segments[0], longer_segments[0])
            sim_a1_b2 = similarity_method(shorter_segments[0], longer_segments[1])

            if sim_a1_b1 >= sim_a1_b2:
                sim_a2_b2 = similarity_method(shorter_segments[1], longer_segments[1])
                sim_a2_b3 = similarity_method(shorter_segments[1], longer_segments[2])
                final_sim_a2 = max(sim_a2_b2, sim_a2_b3)
            else:
                final_sim_a2 = similarity_method(shorter_segments[1], longer_segments[2])

            # 返回 A1 的相似度和 A2 的相似度的平均值
            final_similarity = (max(sim_a1_b1, sim_a1_b2) + final_sim_a2) / 2
            return final_similarity

    @staticmethod
    # 因子C的相似度计算（基于 "+" 分隔，考虑加分）
    def calculate_similarity_factor_c(str1, str2):
        if "+" in str1:
            segments_1 = str1.split("+")
        else:
            segments_1 = [str1]
        if "+" in str2:
            segments_2 = str2.split("+")
        else:
            segments_2 = [str2]

        # print(f"形态 - segments1: {segments_1}, segments2: {segments_2}")
        # 计算共有多少个完全匹配的段落
        common_segments = len(set(segments_1) & set(segments_2))

        # 计算基本相似度：匹配段落数除以总段落数
        total_segments = max(len(segments_1), len(segments_2))
        base_similarity = common_segments / total_segments

        # 加分项：如果匹配段落数超过2，则每多一个匹配段加 0.1 分
        extra_score = max(0, (common_segments - 2) * 0.1)

        # 最终相似度 = 基本相似度 * 权重 0.4 + 加分
        return base_similarity * 0.4 + extra_score

    # 计算整体相似度
    def calculate_total_similarity(self, str_a1, str_a2, str_b1, str_b2, str_c1, str_c2):
        similarity_a = self.calculate_similarity_factor_ab(str_a1, str_a2)
        similarity_b = self.calculate_similarity_factor_ab(str_b1, str_b2)
        similarity_c = self.calculate_similarity_factor_c(str_c1, str_c2)

        total_similarity = (self.weight_a * similarity_a +
                            self.weight_b * similarity_b +
                            self.weight_c * similarity_c)

        # 返回整体相似度和各因子相似度
        return {
            "total_similarity": total_similarity,
            "similarity_long": similarity_a,
            "similarity_middle": similarity_b,
            "similarity_shape": similarity_c
        }
