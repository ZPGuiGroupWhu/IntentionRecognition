import sys

from Map_RIR.src.main.util.FileUtil import load_json
from Map_RIR.src.main.samples.generation.ConceptIdTransform import Ontology_concept_to_id, \
    concept_to_id, Information_Content_concept_to_id
import os.path

file_path_prefix = os.getcwd().split("RFSCE_MRIR")[0] + "RFSCE_MRIR/resources/ontologies/geonames_america"

Ontologies_path = os.path.join(file_path_prefix, "Ontologies.json")
direct_Ancestor_path = os.path.join(file_path_prefix, "direct_Ancestor.json")
Ancestors_path = os.path.join(file_path_prefix, "Ancestors.json")
Neighborhood_path = os.path.join(file_path_prefix, "neighbors.json")
Information_Content_Path = os.path.join(file_path_prefix, "concept_information_content_yuan2013.json")
Ontologies = load_json(Ontologies_path)        # 空间实体区域内的所有级别的所有空间实体，最小级别为一级行政区
Ancestors = load_json(Ancestors_path)           #
direct_Ancestor = load_json(direct_Ancestor_path)        # 包含某个空间实体的上一级空间实体，最上级为美洲（America）
Neighborhood = load_json(Neighborhood_path)     # 包含某个空间实体E的上一级实体和E包含的下一级空间实体
Information_Content = load_json(Information_Content_Path)
Ontology_Root = "America"

if os.path.basename(sys.argv[0]) == "GenerateSamples.py":
    # print(len(Ontologies["United States"]))
    Ontologies = Ontology_concept_to_id(Ontologies)
    Ancestors = Ontology_concept_to_id(Ancestors)
    direct_Ancestor = Ontology_concept_to_id(direct_Ancestor)
    Neighborhood = Ontology_concept_to_id(Neighborhood)
    Ontology_Root = concept_to_id(Ontology_Root)
    Information_Content = Information_Content_concept_to_id(Information_Content)