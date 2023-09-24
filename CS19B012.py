import os
import xml.etree.ElementTree as ET
from lxml import etree
import copy
import itertools


class ALCConcept:
    def __init__(self, type, content=None):
        self.type = type
        self.content = content

    def __repr__(self):
        if self.type == "NOT":
            return f"<NOT>\n{self.content}\n</NOT>"
        elif self.type in ["AND", "OR"]:
            return f"<{self.type}>\n" + "".join([str(c) for c in self.content]) + f"</{self.type}>"
        else:
            return f"<CONCEPT>{self.type}</CONCEPT>"

    def __eq__(self, other):
        if isinstance(other, ALCConcept):
            return self.type == other.type and self.content == other.content
        return False


class Node:
    def __init__(self, concepts, label='None', parents=[], numOfchildren=0):
        self.concepts = concepts
        self.label = label
        self.parents = parents
        self.numOfchildren = numOfchildren

    def __repr__(self):
        return "Node " + self.label +  " : [" + ", ".join([str(c) for c in self.concepts]) + "]"
    
class RoleNode:
    def __init__(self, roles, left=None, right=None):
        self.roles = roles
        self.left = left
        self.right = right

def check_same(node1, node2):
    if node1.label == node2.label:
        if len(node1.parents) == len(node2.parents):
            for (parent1, parent2) in zip(node1.parents, node2.parents):
                if not parent1.label == parent2.label:
                    return False 
            return True            
    return False

def check_closed(node):
    for concept1 in node.concepts:
        for concept2 in node.concepts:
            if concept1.type == "NOT" and concept1.content == concept2:
                return True
    return False

def check_blocking(node):
    if node.label.isdigit():
        for parent in reversed(node.parents):
            if parent.label.isdigit() and all(i in parent.concepts for i in node.concepts):
                return True
    return False


def parse_alc_concept_from_xml(element):
    if element.tag == "CONCEPT":
        return ALCConcept(element.text.strip())
    elif element.tag in ["AND", "OR"]:
        return ALCConcept(element.tag, [parse_alc_concept_from_xml(child) for child in element])
    elif element.tag == "NOT":
        return ALCConcept("NOT", parse_alc_concept_from_xml(element[0]))
    elif element.tag == "EXISTS":
        role = element.find("ROLE").text.strip()
        concept = parse_alc_concept_from_xml(element[1])
        return ALCConcept("EXISTS", (role, concept))
    elif element.tag == "FORALL":
        role = element.find("ROLE").text.strip()
        concept = parse_alc_concept_from_xml(element[1])
        return ALCConcept("FORALL", (role, concept))
    return None


def parse_individual_from_xml(element):
    individual = element.find("INDIVIDUAL").text.strip()
    concepts_elements = element.findall(".//Types/*")
    concepts = [parse_alc_concept_from_xml(concept) for concept in concepts_elements]

    roles = []
    fact_elements = element.findall('.//Facts/*')
    for fact in fact_elements:
        role = fact.find("ROLE").text.strip()
        right = fact.find("INDIVIDUAL").text.strip()
        roles.append((role,right))

    if not concepts and not roles:
        print(f"Error: Could not parse concept for individual {individual}")

    return (individual, concepts, roles)


def parse_xml_file(file_path):
    tree = etree.parse(file_path)
    root = tree.getroot()

    tbox_elements = []
    abox_elements = []
    for elem in root.xpath("//EquivalentTo/*"):
        tbox_elements.append(parse_alc_concept_from_xml(elem))

    for elem in root.xpath("//Individual"):
        abox_elements.append(parse_individual_from_xml(elem))

    return tbox_elements, abox_elements


def apply_rule_and(node, concept):
    new_nodes = []
    new_concepts = node.concepts.copy()
    new_concepts.remove(concept)
    for child in concept.content:
        if child not in new_concepts:
            new_concepts.append(child)
    new_node = copy.deepcopy(node)
    new_node.concepts = new_concepts
    new_nodes.append(new_node)    
    return new_nodes

def apply_rule_or(node, concept):
    new_nodes = []
    if not any(i in node.concepts for i in concept.content):
        for child in concept.content:
            new_concepts = node.concepts.copy()
            new_concepts.remove(concept)
            new_concepts.append(child)
            new_node = copy.deepcopy(node)
            new_node.concepts = new_concepts
            new_nodes.append(new_node)        
    return new_nodes

def apply_rule_exists(node, concept, tbox):
    global role_list

    new_nodes = []
    for role_node in role_list:
        if check_same(role_node.left,node) and concept.content[0] in role_node.roles:
            return new_nodes
                
    new_concepts = [copy.deepcopy(concept.content[1])]
    new_concepts.extend(tbox)
    new_node = Node(new_concepts)
    new_node.parents = node.parents + [node]
    new_node.label = str(node.numOfchildren + 1)

    if check_blocking(new_node):
        return new_nodes
    
    new_nodes.append(new_node)

    new_role = concept.content[0]
    new_rolenode = RoleNode(new_role,node,new_node)
    role_list.append(new_rolenode)

    for concept_temp in node.concepts:
        if concept_temp.type == "FORALL" and concept_temp.content[0] == concept.content[0]:
            new_nodes.extend(apply_rule_forall(node, concept_temp))

    node.numOfchildren = node.numOfchildren + 1
    return new_nodes


def apply_rule_forall(node, concept):
    global role_list
    new_nodes = []
    for role_node in role_list:
        if check_same(role_node.left,node) and concept.content[0] in role_node.roles:
            if concept.content[1] not in role_node.right.concepts:
                new_concept = copy.deepcopy(concept.content[1])
                new_node = copy.deepcopy(role_node.right)
                new_node.concepts.append(new_concept)
                new_nodes.append(new_node) 

    return new_nodes


def expand(node, tbox):
    new_nodes = []
    for concept in node.concepts:
        if concept.type == "AND":
            new_nodes_and = apply_rule_and(node, concept)
            if new_nodes_and: 
                new_nodes.extend(new_nodes_and)
                return new_nodes
            else: 
                continue  
        elif concept.type == "OR":
            new_nodes_or = apply_rule_or(node, concept)
            if new_nodes_or:
                new_nodes.extend(new_nodes_or) 
                return new_nodes
            else: 
                continue 
        elif concept.type == "EXISTS":
            new_nodes.extend(apply_rule_exists(node, concept, tbox))
        elif concept.type == "FORALL":
            new_nodes.extend(apply_rule_forall(node, concept))

    return new_nodes


def isEntailed(abox, tbox, debug=False): 
    return not IsSatisfiable(abox, tbox, debug)

def IsSatisfiable(abox, tbox, debug=False):
    open_list = [Node(tbox)]
    closed_list = []
    global role_list
    role_list = []

    for abox_elements in abox:
        newnode_label = abox_elements[0]
        flag = 0
        for node in open_list:
            if node.label == newnode_label:
                node.concepts.extend(abox_elements[1])
                flag = 1
                break
        if not flag:    
            newnode = abox_elements[1]
            newnode.extend(tbox)
            open_list.append(Node(newnode, newnode_label))

    for abox_elements in abox:
        node1 = abox_elements[0]
        roles = abox_elements[2]
        for leftnode in open_list:
            if leftnode.label == node1:
                for role_element in roles:
                    role = role_element[0]
                    node2 = role_element[1]
                    flag = 0
                    for rightnode in open_list:
                        if rightnode.label == node2:
                            role_list.append(RoleNode(role, leftnode, rightnode))
                            flag = 1
                            break
                    if not flag:    
                        new_node = Node([],node2)
                        open_list.append(new_node)
                        role_list.append(RoleNode(role, leftnode, new_node))
                break



    while open_list:
        node = open_list.pop(0)
        closed_list.append(node)

        if debug:
            print(f"Processing node: {node}")

        flag = 0
        if check_closed(node):
            for other_node in open_list:
                if check_same(node, other_node):
                    flag = 1
                    break
            if not flag: return False
        else:
            new_nodes = expand(node, tbox)
            for new_node in new_nodes:
                if new_node not in open_list and new_node not in closed_list:
                    open_list.append(new_node)

    return True    

    

def main():
    tbox, abox = parse_xml_file("./testcases/case1/kb.xml")
    #print("Printing TBox : ", tbox)
    #print("Printing ABox : ", abox)

    if os.path.exists("./testcases/case1/query.xml"):
        query_tbox, query_abox = parse_xml_file("./testcases/case1/query.xml")
        tbox.extend(query_tbox)
        abox.extend(query_abox)
        result = isEntailed(abox,tbox, debug=False)
        print("Query is entailed by the Knowledge Base." if result else "Query is not entailed by the Knowledge Base.")
    else:
        result = IsSatisfiable(abox,tbox, debug=False)
        print("The given Knowledge Base is satisfiable" if result else "The given Knowledge Base is not satisfiable")





if __name__ == "__main__":
    main()
