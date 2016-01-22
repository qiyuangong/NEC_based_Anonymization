"""
main module for EC_based_Anon
"""
#!/usr/bin/env python
#coding=utf-8

from models.numrange import NumRange
from models.gentree import GenTree
from utils.utility import get_num_list_from_str, cmp_str, list_to_str
import random
import time
import operator
import pdb


__DEBUG = False
# att_tree store root node for each att
ATT_TREES = []
# databack store all reacord for dataset
LEN_DATA = 0
QI_LEN = 0
QI_RANGE = []
IS_CAT = []
# get_LCA, middle and NCP require huge running time, while most of the function are duplicate
# we can use cache to reduce the running time
LCA_CACHE = []
NCP_CACHE = {}


class Cluster(object):

    """Cluster is for cluster based k-anonymity
    middle denote generlized value for one cluster
    self.member: record list in cluster
    self.middle: middle node in cluster
    """

    def __init__(self, member, middle):
        self.information_loss = 0.0
        self.member = member
        self.middle = middle[:]

    def add_record(self, record):
        """
        add record to cluster
        """
        self.member.append(record)
        self.update_middle(record)

    def update_middle(self, merge_middle):
        """
        update middle and information_loss after adding record or merging cluster
        :param merge_middle:
        :return:
        """
        self.middle = middle(self.middle, merge_middle)
        self.information_loss = len(self.member) * NCP(self.middle)

    def add_same_record(self, record):
        """
        add record with same qid to cluster
        """
        self.member.append(record)

    def merge_cluster(self, cluster):
        """merge cluster into self and do not delete cluster elements.
        update self.middle with middle
        """
        self.member.extend(cluster.member)
        self.update_middle(cluster.middle)

    def __getitem__(self, item):
        """
        :param item: index number
        :return: middle[item]
        """
        return self.middle[item]

    def __len__(self):
        """
        return number of records in cluster
        """
        return len(self.member)


def diff_distance(source, target):
    """
    return IL(source and target) - IL(souce) - IL(target).
    """
    source_len = 1
    source_mid = source
    source_iloss = 0.0
    if isinstance(source, Cluster):
        source_mid = source.middle
        source_len = len(source)
        source_iloss = source.information_loss
    mid_after = middle(source_mid, target.middle)
    return NCP(mid_after) * (len(target) + source_len)\
        - target.information_loss - source_iloss


def r_distance(source, target):
    """
    Return distance between source (cluster or record)
    and target (cluster or record). The distance is based on
    NCP (Normalized Certainty Penalty) on relational part.
    If source or target are cluster, func need to multiply
    source_len (or target_len).
    """
    source_mid = source
    target_mid = target
    source_len = 1
    target_len = 1
    # check if target is Cluster
    if isinstance(target, Cluster):
        target_mid = target.middle
        target_len = len(target)
    # check if souce is Cluster
    if isinstance(source, Cluster):
        source_mid = source.middle
        source_len = len(source)
    if source_mid == target_mid:
        return 0
    mid = middle(source_mid, target_mid)
    # len should be taken into account
    distance = (source_len + target_len) * NCP(mid)
    return distance


def NCP(mid):
    """Compute NCP (Normalized Certainty Penalty)
    when generate record to middle.
    """
    ncp = 0.0
    # exclude SA values(last one type [])
    list_key = list_to_str(mid)
    try:
        return NCP_CACHE[list_key]
    except KeyError:
        pass
    for i in range(QI_LEN):
        # if leaf_num of numerator is 1, then NCP is 0
        width = 0.0
        if IS_CAT[i] is False:
            try:
                float(mid[i])
            except ValueError:
                temp = mid[i].split(',')
                width = float(temp[1]) - float(temp[0])
        else:
            width = len(ATT_TREES[i][mid[i]]) * 1.0
        width /= QI_RANGE[i]
        ncp += width
    NCP_CACHE[list_key] = ncp
    return ncp


def get_LCA(index, item1, item2):
    """Get lowest commmon ancestor (including themselves)"""
    # get parent list from
    if item1 == item2:
        return item1
    try:
        return LCA_CACHE[index][item1 + item2]
    except KeyError:
        pass
    parent1 = ATT_TREES[index][item1].parent[:]
    parent2 = ATT_TREES[index][item2].parent[:]
    parent1.insert(0, ATT_TREES[index][item1])
    parent2.insert(0, ATT_TREES[index][item2])
    min_len = min(len(parent1), len(parent2))
    last_LCA = parent1[-1]
    # note here: when trying to access list reversely, take care of -0
    for i in range(1, min_len + 1):
        if parent1[-i].value == parent2[-i].value:
            last_LCA = parent1[-i]
        else:
            break
    LCA_CACHE[index][item1 + item2] = last_LCA.value
    return last_LCA.value


def middle(record1, record2):
    """
    Compute relational generalization result of record1 and record2
    """
    mid = []
    for i in range(QI_LEN):
        if IS_CAT[i] is False:
            split_number = []
            split_number.extend(get_num_list_from_str(record1[i]))
            split_number.extend(get_num_list_from_str(record2[i]))
            split_number = list(set(split_number))
            if len(split_number) == 1:
                mid.append(split_number[0])
            else:
                split_number.sort(cmp=cmp_str)
                mid.append(split_number[0] + ',' + split_number[-1])
        else:
            mid.append(get_LCA(i, record1[i], record2[i]))
    return mid


def middle_for_cluster(records):
    """
    calculat middle of records(list) recursively.
    Compute both relational middle for records (list).
    """
    len_r = len(records)
    mid = records[0]
    for i in range(1, len_r):
        mid = middle(mid, records[i])
    return mid


def find_best_knn(index, k, nec_set):
    """key fuction of KNN. Find k nearest neighbors of record, remove them from data"""
    dist_dict = {}
    seed_cluster = nec_set[index]
    pop_index = [index]
    # add random seed to cluster
    for i, t in enumerate(nec_set):
        if i == index:
            continue
        dist = diff_distance(t, seed_cluster)
        dist_dict[i] = dist
    sorted_dict = sorted(dist_dict.iteritems(), key=operator.itemgetter(1))
    knn = sorted_dict[:k - 1]
    for current_index, _ in knn:
        if len(seed_cluster) < k:
            seed_cluster.merge_cluster(nec_set[current_index])
            pop_index.append(current_index)
        else:
            break
    # delete multiple elements from data according to knn index list
    return seed_cluster, pop_index


def find_best_cluster_knn(cluster, clusters):
    """residual assignment. Find best cluster for record."""
    min_distance = 1000000000000
    min_index = 0
    for i, t in enumerate(clusters):
        distance = diff_distance(cluster, t)
        if distance < min_distance:
            min_distance = distance
            min_index = i
    # add record to best cluster
    return min_index


def find_furthest_record(record, nec_set):
    """
    find the furthest nec from record in nec_set
    :param record:
    :param nec_set:
    :return: the index of furthest nec
    """
    max_distance = 0
    max_index = -1
    for index in range(len(nec_set)):
        current_distance = r_distance(record, nec_set[index])
        if current_distance >= max_distance:
            max_distance = current_distance
            max_index = index
    return max_index


def find_best_cluster_kmember(nec, clusters):
    """residual assignment. Find best cluster for record."""
    min_diff = 1000000000000
    min_index = 0
    best_cluster = clusters[0]
    for i, t in enumerate(clusters):
        IF_diff = diff_distance(nec, t)
        if IF_diff < min_diff:
            min_distance = IF_diff
            min_index = i
            best_cluster = t
    # add record to best cluster
    return min_index


def find_best_record_kmember(cluster, nec_set):
    """
    :param cluster: current
    :param data: remain dataset
    :return: index of record with min diff on information loss
    """
    # pdb.set_trace()
    min_diff = 1000000000000
    min_index = 0
    for index, nec in enumerate(nec_set):
        # IF_diff = diff_distance(record, cluster)
        # IL(cluster and record) and |cluster| + 1 is a constant
        # so IL(record, cluster.middle) is enough
        IF_diff = diff_distance(nec, cluster)
        if IF_diff < min_diff:
            min_diff = IF_diff
            min_index = index
    return min_index


def clustering_knn(nec_set, k=25):
    """
    Group record according to QID distance. KNN
    """
    clusters = [cluster for cluster in nec_set if len(cluster) >= k]
    nec_set = [cluster for cluster in nec_set if len(cluster) < k]
    remain = sum([len(t) for t in nec_set])
    # randomly choose seed and find k-1 nearest records to form cluster with size k
    while remain >= k:
        index = random.randrange(len(nec_set))
        # if len(nec_set[index]) >= k:
        #     cluster = nec_set.pop(index)
        #     clusters.append(cluster)
        #     continue
        cluster, pop_index = find_best_knn(index, k, nec_set)
        nec_set = [t for i, t in enumerate(nec_set) if i not in set(pop_index)]
        clusters.append(cluster)
        remain -= len(cluster)
    # residual assignment
    while len(nec_set) > 0:
        t = nec_set.pop()
        cluster_index = find_best_cluster_knn(t, clusters)
        clusters[cluster_index].merge_cluster(t)
    return clusters


def clustering_kmember(nec_set, k=25):
    """
    group record accroding to QID distance. K-member
    :param nec_set: natural EC
    :param k: k
    :return: grouped clusters
    """
    clusters = [cluster for cluster in nec_set if len(cluster) >= k]
    nec_set = [cluster for cluster in nec_set if len(cluster) < k]
    remain = sum([len(t) for t in nec_set])
    # randomly choose seed and find k-1 nearest records to form cluster with size k
    try:
        r_pos = random.randrange(len(nec_set))
        r_i = nec_set[r_pos].middle
    except ValueError:
        return clusters
    while remain >= k:
        r_pos = find_furthest_record(r_i, nec_set)
        cluster = nec_set.pop(r_pos)
        while len(cluster) < k:
            r_pos = find_best_record_kmember(cluster, nec_set)
            r_j = nec_set.pop(r_pos)
            cluster.merge_cluster(r_j)
        clusters.append(cluster)
        remain -= len(cluster)
    while len(nec_set) > 0:
        t = nec_set.pop()
        cluster_index = find_best_cluster_kmember(t, clusters)
        clusters[cluster_index].merge_cluster(t)
    return clusters


def OKA(nec_set, k=25):
    pass


def create_nec(data):
    """
    create NEC from dateset using dict
    :param data: dataset
    :return: NEC in dict format: key is str, value is Cluster
    """
    nec_dict = dict()
    for record in data:
        key = ';'.join(record[:QI_LEN])
        try:
            nec_dict[key].add_same_record(record)
        except KeyError:
            nec_dict[key] = Cluster([record], record)
    return nec_dict


def init(att_trees, data, QI_num=-1):
    """
    init global variables
    """
    global ATT_TREES, DATA_BACKUP, LEN_DATA, QI_RANGE, IS_CAT, QI_LEN, LCA_CACHE, NCP_CACHE
    ATT_TREES = att_trees
    QI_RANGE = []
    IS_CAT = []
    LEN_DATA = len(data)
    LCA_CACHE = []
    NCP_CACHE = {}
    if QI_num <= 0:
        QI_LEN = len(data[0]) - 1
    else:
        QI_LEN = QI_num
    for i in range(QI_LEN):
        LCA_CACHE.append(dict())
        if isinstance(ATT_TREES[i], NumRange):
            IS_CAT.append(False)
            QI_RANGE.append(ATT_TREES[i].range)
        else:
            IS_CAT.append(True)
            QI_RANGE.append(len(ATT_TREES[i]['*']))


def EC_based_Anon(att_trees, data, type_alg='knn', k=10, QI_num=-1):
    """
    the main function of EC_based_Anon
    """
    init(att_trees, data, QI_num)
    result = []
    start_time = time.time()
    nec_dict = create_nec(data)
    if type_alg == 'knn':
        print "Begin to KNN Cluster based on NCP"
        clusters = clustering_knn(nec_dict.values(), k)
    elif type_alg == 'kmember':
        print "Begin to K-Member Cluster based on NCP"
        clusters = clustering_kmember(nec_dict.values(), k)
    else:
        print "Please choose merge algorithm types"
        print "knn | kmember"
        return (0, (0, 0))
    rtime = float(time.time() - start_time)
    ncp = 0.0
    # pdb.set_trace()
    for cluster in clusters:
        gen_result = []
        mid = cluster.middle
        for i in range(len(cluster)):
            # do not forget to add SA!!!
            gen_result.append(mid + [cluster.member[i][-1]])
        result.extend(gen_result)
        ncp += cluster.information_loss
    ncp /= LEN_DATA
    ncp /= QI_LEN
    ncp *= 100
    if __DEBUG:
        print "NCP=", ncp
    if len(result) != len(data):
        print "Record lost"
        pdb.set_trace()
    return (result, (ncp, rtime))
