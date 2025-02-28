# compare with
#   DTHF：Kinnunen N . Decision tree learning with hierarchical features.  2018.
#   RuleGO：Gruca A ,  Sikora M . Data- and expert-driven rule induction and filtering framework for functional
#       interpretation and description of gene sets[J]. Journal of Biomedical Semantics, 2017, 8(1).


import os
import time
import multiprocessing

from Map_RIR.src.main import Intention
from Map_RIR.src.main.samples.input import Sample
from Map_RIR.src.main.samples.input.Data import Data
from Map_RIR.src.main.intention_recognition import Config, DTHF_Kinnunen2018, RuleGO_Gruca2017, Run_Map_RIR
from Map_RIR.src.main.experience import Evaluation_IM
from Map_RIR.src.main.util.FileUtil import save_as_json, load_json

sample_version = Intention.__sample_version__
output_path_prefix = os.path.join("../../../result", "scenes_" +
                                  sample_version + "_" + Intention.__version__)
if not os.path.exists(output_path_prefix):
    os.mkdir(output_path_prefix)
auto_save_threshold = 100


def experience_get_specific_samples_result(part_name, sample_paths):
    # import time, datetime
    output_dir = os.path.join(output_path_prefix, "experience_comparison_result")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    tmp_round_num = 0  # 为了自动保存而设置的变量
    # set parameters
    feedback_noise_rates = [0, 0.1, 0.2, 0.3]
    label_noise_rates = [0, 0.2, 0.4, 0.6, 0.8, 1]
    methods = ["MDL_RM_r", "DTHF", "RuleGO"]
    total_run_num = len(sample_paths) * len(feedback_noise_rates) * len(label_noise_rates) * len(methods)

    # config
    run_time = 1
    # for MDL_RM
    tmp_threshold = Config.rule_covered_positive_sample_rate_threshold
    Config.adjust_sample_num = True
    Config.TAG_RECORD_MERGE_PROCESS = False
    Config.With_negative = False
    # for RuleGO
    Config.RuleGO_statistical_significance_level = 0.05  # 规则的统计显著性阈值
    Config.RuleGO_min_support = 40  # 最小支持度
    Config.RuleGO_max_term_num_in_rule = 4  # 一个规则包含的词项的最大值
    Config.RuleGO_rule_similarity_threshold = 0.5  # 意图的相似度阈值
    Config.RuleGO_use_similarity_criteria = False  # 是否基于意图相似度保证意图多样
    # for DTHF
    Config.DTHF_use_min_support = False

    output_path = os.path.join(output_dir,
                               "result_jaccard_similarity_time_use_avg" + str(run_time) + "_" + part_name)
    result = []
    finished_record_keys = []
    if os.path.exists(output_path):
        result = load_json(output_path)
        finished_record_keys = [(x["scene"], x["feedback_noise_rate"], x["label_noise_rate"], x["method"])
                                for x in result]

    tmp_run_num = 0
    real_intentions = Sample.get_real_intent()
    for tmp_sample_name in sample_paths:
        # print("##### ", tmp_sample_name, " #####")
        tmp_sample_path_prefix = sample_paths[tmp_sample_name]

        for tmp_sample_level_noise_rate in feedback_noise_rates:
            tmp_sample_level_noise_rate_str = "_S" + str(tmp_sample_level_noise_rate).replace(".", "p")
            for tmp_label_level_noise_rate in label_noise_rates:
                tmp_label_level_noise_rate_str = "_L" + str(tmp_label_level_noise_rate).replace(".", "p")

                if tmp_sample_level_noise_rate == 0:
                    if tmp_label_level_noise_rate == 0:
                        tmp_sample_path = os.path.join(tmp_sample_path_prefix, "final_samples.json")
                    else:
                        tmp_sample_path = os.path.join(tmp_sample_path_prefix,
                                                       "noise_samples" + tmp_label_level_noise_rate_str+".json")
                else:
                    if tmp_label_level_noise_rate == 0:
                        tmp_sample_path = os.path.join(tmp_sample_path_prefix,
                                                       "noise_samples" + tmp_sample_level_noise_rate_str+".json")
                    else:
                        tmp_sample_path = os.path.join(tmp_sample_path_prefix,
                                                       "noise_samples" + tmp_sample_level_noise_rate_str
                                                       + tmp_label_level_noise_rate_str+".json")
                # load sample data
                # docs, real_intention = Sample.load_sample_from_file(tmp_sample_path)

                docs, real_intention = Sample.load_real_intents(real_intentions, tmp_sample_path, tmp_sample_name)

                data = Data(docs, real_intention)

                samples = data.docs
                positive_samples = samples["relevance"]
                negative_samples = samples["irrelevance"]
                ancestors = Data.Ancestor
                ontologies = Data.Ontologies
                ontology_root = Data.Ontology_Root
                direct_ancestors = Data.direct_Ancestor
                information_content = data.concept_information_content
                terms = data.all_relevance_concepts
                terms_covered_samples = data.all_relevance_concepts_retrieved_docs
                for tmp_method in methods:
                    tmp_run_num += 1
                    tmp_record_key = (
                        tmp_sample_name, tmp_sample_level_noise_rate, tmp_label_level_noise_rate, tmp_method)
                    if tmp_record_key in finished_record_keys:
                        continue

                    print(
                        f"running: {part_name} - {tmp_run_num}/{total_run_num} - {tmp_sample_name} - "
                        f"{tmp_sample_level_noise_rate} - {tmp_label_level_noise_rate} - {tmp_method}")
                    all_jaccard_index = []
                    all_intention_similarity = []
                    all_precision = []
                    all_recall = []
                    all_time_use = []
                    all_rules = []
                    for i in range(run_time):
                        time01 = time.time()
                        intention_result = []
                        if tmp_method == "MDL_RM_r":
                            tmp_result, usetime = Run_Map_RIR.run_IM(samples, 0.3, 10)
                            time02 = time.time()
                            intention_result = []
                            # 转换成字典格式
                            for sub_intent in tmp_result.intention:
                                real_sub_intent = {"positive": sub_intent.positive_sub_Intention,
                                                   "negative": sub_intent.negative_sub_Intention}
                                intention_result.append(real_sub_intent)

                        elif tmp_method == "DTHF":
                            tmp_result = DTHF_Kinnunen2018.DTHF(positive_samples, negative_samples,
                                                                      direct_ancestors, ancestors, ontology_root)


                            intention_result = Evaluation_IM.trans_intent(tmp_result)
                            time02 = time.time()
                        elif tmp_method == "RuleGO":
                            intention_result = RuleGO_Gruca2017.RuleGo(terms, positive_samples, negative_samples,
                                                                       terms_covered_samples, direct_ancestors,
                                                                       ancestors, ontologies, ontology_root)
                            intention_result = Evaluation_IM.trans_intent(intention_result)
                            time02 = time.time()


                        all_time_use.append(time02 - time01)
                        jaccard_index = Evaluation_IM.get_jaccard_index(samples, real_intention,
                                                                          intention_result,
                                                                          Data.Ontologies, Data.Ontology_Root)
                        best_map_average_semantic_similarity = \
                            Evaluation_IM.get_intention_similarity(intention_result, real_intention,
                                                                     direct_ancestors, ontology_root,
                                                                     information_content)
                        # if tmp_method == "MDL_RM_r":
                            # print("time", all_time_use)
                        #     print("intention_result",intention_result)
                        #     print("real_intention", real_intention)
                        #     print("best_map_average_semantic_similarity", best_map_average_semantic_similarity)
                        precision = Evaluation_IM.get_precision(samples, real_intention,
                                                                  intention_result,
                                                                  Data.Ontologies, Data.Ontology_Root)
                        recall = Evaluation_IM.get_recall(samples, real_intention,
                                                            intention_result,
                                                            Data.Ontologies, Data.Ontology_Root)
                        all_intention_similarity.append(best_map_average_semantic_similarity)
                        all_jaccard_index.append(jaccard_index)
                        all_precision.append(precision)
                        all_recall.append(recall)
                        all_rules.append(intention_result)

                    tmp_result = {"scene": tmp_sample_name, "feedback_noise_rate": tmp_sample_level_noise_rate,
                                  "label_noise_rate": tmp_label_level_noise_rate,
                                  "method": tmp_method,
                                  "rule_covered_positive_sample_rate_threshold": tmp_threshold,
                                  "time_use": all_time_use,
                                  "jaccard_index": all_jaccard_index,
                                  "intention_similarity": all_intention_similarity,
                                  "precision": all_precision,
                                  "recall": all_recall,
                                  "extracted_rules_json": all_rules}
                    result.append(tmp_result)
                    finished_record_keys.append(tmp_record_key)
                    tmp_round_num += 1
                    if tmp_round_num == auto_save_threshold:
                        save_as_json(result, output_path)
                        tmp_round_num = 0
    save_as_json(result, output_path)



def experience_get_specific_samples_result_single(sample_names, sample_paths):
    # import time, datetime
    output_dir = os.path.join(output_path_prefix, "experience_comparison_result")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    tmp_round_num = 0  # 为了自动保存而设置的变量
    # set parameters
    feedback_noise_rates = [0, 0.1, 0.2, 0.3]
    label_noise_rates = [0, 0.2, 0.4, 0.6, 0.8, 1]
    methods = ["MDL_RM_r", "DTHF", "RuleGO"]
    total_run_num = len(sample_paths) * len(feedback_noise_rates) * len(label_noise_rates) * len(methods)

    # config
    run_time = 1
    # for MDL_RM
    tmp_threshold = Config.rule_covered_positive_sample_rate_threshold
    Config.adjust_sample_num = True
    Config.TAG_RECORD_MERGE_PROCESS = False
    Config.With_negative = True
    # for RuleGO
    Config.RuleGO_statistical_significance_level = 0.05  # 规则的统计显著性阈值
    Config.RuleGO_min_support = 40  # 最小支持度
    Config.RuleGO_max_term_num_in_rule = 4  # 一个规则包含的词项的最大值
    Config.RuleGO_rule_similarity_threshold = 0.5  # 意图的相似度阈值
    Config.RuleGO_use_similarity_criteria = False  # 是否基于意图相似度保证意图多样
    # for DTHF
    Config.DTHF_use_min_support = False

    output_path = os.path.join(output_dir,
                               "result_jaccard_similarity_time_use_avg" + str(run_time) + "_single")
    result = []
    finished_record_keys = []
    if os.path.exists(output_path):
        result = load_json(output_path)
        finished_record_keys = [(x["scene"], x["feedback_noise_rate"], x["label_noise_rate"], x["method"])
                                for x in result]

    tmp_run_num = 0
    real_intentions = Sample.get_real_intent()
    for tmp_sample_name in sample_names:
        # print("##### ", tmp_sample_name, " #####")
        tmp_sample_path_prefix = sample_paths[tmp_sample_name]

        for tmp_sample_level_noise_rate in feedback_noise_rates:
            tmp_sample_level_noise_rate_str = "_S" + str(tmp_sample_level_noise_rate).replace(".", "p")
            for tmp_label_level_noise_rate in label_noise_rates:
                tmp_label_level_noise_rate_str = "_L" + str(tmp_label_level_noise_rate).replace(".", "p")

                if tmp_sample_level_noise_rate == 0:
                    if tmp_label_level_noise_rate == 0:
                        tmp_sample_path = os.path.join(tmp_sample_path_prefix, "final_samples.json")
                    else:
                        tmp_sample_path = os.path.join(tmp_sample_path_prefix,
                                                       "noise_samples" + tmp_label_level_noise_rate_str+".json")
                else:
                    if tmp_label_level_noise_rate == 0:
                        tmp_sample_path = os.path.join(tmp_sample_path_prefix,
                                                       "noise_samples" + tmp_sample_level_noise_rate_str+".json")
                    else:
                        tmp_sample_path = os.path.join(tmp_sample_path_prefix,
                                                       "noise_samples" + tmp_sample_level_noise_rate_str
                                                       + tmp_label_level_noise_rate_str+".json")
                # load sample data
                # docs, real_intention = Sample.load_sample_from_file(tmp_sample_path)

                docs, real_intention = Sample.load_real_intents(real_intentions, tmp_sample_path, tmp_sample_name)

                data = Data(docs, real_intention)

                samples = data.docs
                positive_samples = samples["relevance"]
                negative_samples = samples["irrelevance"]
                ancestors = Data.Ancestor
                ontologies = Data.Ontologies
                ontology_root = Data.Ontology_Root
                direct_ancestors = Data.direct_Ancestor
                information_content = data.concept_information_content
                terms = data.all_relevance_concepts
                terms_covered_samples = data.all_relevance_concepts_retrieved_docs
                for tmp_method in methods:
                    tmp_run_num += 1
                    tmp_record_key = (
                        tmp_sample_name, tmp_sample_level_noise_rate, tmp_label_level_noise_rate, tmp_method)
                    if tmp_record_key in finished_record_keys:
                        continue

                    print(
                        f"running: {tmp_run_num}/{total_run_num} - {tmp_sample_name} - "
                        f"{tmp_sample_level_noise_rate} - {tmp_label_level_noise_rate} - {tmp_method}")
                    all_jaccard_index = []
                    all_intention_similarity = []
                    all_precision = []
                    all_recall = []
                    all_time_use = []
                    all_rules = []
                    for i in range(run_time):
                        time01 = time.time()
                        intention_result = []
                        if tmp_method == "MDL_RM_r":
                            tmp_result, usetime = Run_Map_RIR.run_IM(samples, 0.3, 15)
                            time02 = time.time()
                            intention_result = []
                            # 转换成字典格式
                            for sub_intent in tmp_result.intention:
                                real_sub_intent = {"positive": sub_intent.positive_sub_Intention,
                                                   "negative": sub_intent.negative_sub_Intention}
                                intention_result.append(real_sub_intent)

                        elif tmp_method == "DTHF":
                            DTHF_Kinnunen2018.DTHF(positive_samples, negative_samples,
                                                                direct_ancestors, ancestors, ontology_root)
                            tmp_result = DTHF_Kinnunen2018.DTHF(positive_samples, negative_samples,
                                                                      direct_ancestors, ancestors, ontology_root)


                            intention_result = Evaluation_IM.trans_intent(tmp_result)
                            time02 = time.time()
                        elif tmp_method == "RuleGO":
                            RuleGO_Gruca2017.RuleGo(terms, positive_samples, negative_samples,
                                                    terms_covered_samples, direct_ancestors,
                                                    ancestors, ontologies, ontology_root)
                            intention_result = RuleGO_Gruca2017.RuleGo(terms, positive_samples, negative_samples,
                                                                       terms_covered_samples, direct_ancestors,
                                                                       ancestors, ontologies, ontology_root)
                            intention_result = Evaluation_IM.trans_intent(intention_result)
                            time02 = time.time()


                        all_time_use.append(time02 - time01)
                        jaccard_index = Evaluation_IM.get_jaccard_index(samples, real_intention,
                                                                          intention_result,
                                                                          Data.Ontologies, Data.Ontology_Root)
                        best_map_average_semantic_similarity = \
                            Evaluation_IM.get_intention_similarity(intention_result, real_intention,
                                                                     direct_ancestors, ontology_root,
                                                                     information_content)
                        # if tmp_method == "MDL_RM_r":
                            # print("time", all_time_use)
                        #     print("intention_result",intention_result)
                        #     print("real_intention", real_intention)
                        #     print("best_map_average_semantic_similarity", best_map_average_semantic_similarity)
                        precision = Evaluation_IM.get_precision(samples, real_intention,
                                                                  intention_result,
                                                                  Data.Ontologies, Data.Ontology_Root)
                        recall = Evaluation_IM.get_recall(samples, real_intention,
                                                            intention_result,
                                                            Data.Ontologies, Data.Ontology_Root)
                        all_intention_similarity.append(best_map_average_semantic_similarity)
                        all_jaccard_index.append(jaccard_index)
                        all_precision.append(precision)
                        all_recall.append(recall)
                        all_rules.append(intention_result)

                    tmp_result = {"scene": tmp_sample_name, "feedback_noise_rate": tmp_sample_level_noise_rate,
                                  "label_noise_rate": tmp_label_level_noise_rate,
                                  "method": tmp_method,
                                  "rule_covered_positive_sample_rate_threshold": tmp_threshold,
                                  "time_use": all_time_use,
                                  "jaccard_index": all_jaccard_index,
                                  "intention_similarity": all_intention_similarity,
                                  "precision": all_precision,
                                  "recall": all_recall,
                                  "extracted_rules_json": all_rules}
                    result.append(tmp_result)
                    finished_record_keys.append(tmp_record_key)
                    tmp_round_num += 1
                    if tmp_round_num == auto_save_threshold:
                        save_as_json(result, output_path)
                        tmp_round_num = 0
    save_as_json(result, output_path)


# take scene, sample level noise rate, label level noise rate method as variable
# and record the time use, jaccard score， intention_similarity，and rules(in json_str).
def experience_get_all_samples_result():
    # load sample paths
    # sample_paths = get_sample_paths()
    samples_dir = os.path.join("./../../../resources/samples", "scenes_" + sample_version)
    samples_dir = os.path.join("./../../../resources/samples", "scenes_v4_5")
    sample_names = os.listdir(samples_dir)
    sample_paths = {}
    for tmp_sample_name in sample_names:
        sample_paths[tmp_sample_name] = os.path.join(samples_dir, tmp_sample_name)
    sample_names = list(sample_paths.keys())
    print(len(sample_names), sample_names)
    part_num = 1  # 12 process
    split_size = len(sample_names) // part_num + 1
    all_samples_parts = []
    for i in range(part_num - 1):
        tmp_sample_part = {}
        for j in range(split_size):
            tmp_sample_name = sample_names.pop(0)
            tmp_sample_part[tmp_sample_name] = sample_paths[tmp_sample_name]
        all_samples_parts.append(tmp_sample_part)
    last_sample_part = {}
    for tmp_sample_name in sample_names:
        last_sample_part[tmp_sample_name] = sample_paths[tmp_sample_name]
    all_samples_parts.append(last_sample_part)
    for i, tmp_sample_part in enumerate(all_samples_parts):
        part_name = "PART_" + str(i)
        tmp_p = multiprocessing.Process(target=experience_get_specific_samples_result,
                                        args=(part_name, tmp_sample_part))
        tmp_p.start()


def experience_get_all_samples_result_single():
    # load sample paths
    # sample_paths = get_sample_paths()
    samples_dir = os.path.join("./../../../resources/samples", "scenes_" + sample_version)
    samples_dir = os.path.join("./../../../resources/samples", "scenes_v4_5")
    sample_names = os.listdir(samples_dir)
    sample_paths = {}
    for tmp_sample_name in sample_names:
        sample_paths[tmp_sample_name] = os.path.join(samples_dir, tmp_sample_name)
    sample_names = list(sample_paths.keys())
    print(len(sample_names), sample_names)
    experience_get_specific_samples_result_single(sample_names, sample_paths)



def experience_get_samples_result():
    # load sample paths
    # sample_paths = get_sample_paths()
    samples_dir = os.path.join("./../../../resources/samples", "scenes_" + sample_version)
    samples_dir = os.path.join("./../../../resources/samples", "scenes_v4_5")
    sample_names = os.listdir(samples_dir)
    sample_names = os.listdir(samples_dir)
    sample_paths = {}
    for tmp_sample_name in sample_names:
        sample_paths[tmp_sample_name] = os.path.join(samples_dir, tmp_sample_name)
    sample_names = list(sample_paths.keys())
    print(len(sample_names), sample_names)
    part_num = 12  # 12 process
    split_size = len(sample_names) // part_num + 1
    all_samples_parts = []
    for i in range(len(sample_names)):
        tmp_sample_part = {}
        for j in range(1):
            tmp_sample_name = sample_names.pop(0)
            tmp_sample_part[tmp_sample_name] = sample_paths[tmp_sample_name]
        all_samples_parts.append(tmp_sample_part)
    last_sample_part = {}
    for tmp_sample_name in sample_names:
        last_sample_part[tmp_sample_name] = sample_paths[tmp_sample_name]
    all_samples_parts.append(last_sample_part)
    experience_get_specific_samples_result("PART_36", all_samples_parts[33])

if __name__ == "__main__":
    experience_get_all_samples_result()
    #experience_get_samples_result()
    print("Aye")
