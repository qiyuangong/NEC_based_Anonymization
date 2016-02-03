"""
examine nature EC in raw dataset
"""

# !/usr/bin/env python
# coding=utf-8
from utils.utility import list_to_str
import pdb


def size_ec_distribution(data):
    length = len(data)
    joint = 5000
    all_k = [2, 5, 10, 15, 25, 50, 100]
    data_set_size = []
    check_time = length / joint
    if length % joint == 0:
        check_time -= 1
    for i in range(check_time):
        data_set_size.append(joint * (i + 1))
    data_set_size.append(length)
    for pos in data_set_size:
        static_list = []
        dist_dict = ec_distribution(data[:pos])
        for k in all_k:
            num = pos
            for i in range(k):
                try:
                    num -= dist_dict[i] * i
                except KeyError:
                    pass
            static_list.append(num)
        print "Size=", pos
        print static_list



def dim_ec_distribution(data):
    qi_len = len(data[0]) - 1
    total = len(data)
    all_k = [2, 5, 10, 15, 25, 50, 100]
    for dim in range(1, qi_len + 1):
        static_list = []
        dist_dict = ec_distribution(data, dim)
        for k in all_k:
            num = total
            for i in range(k):
                try:
                    num -= dist_dict[i] * i
                except KeyError:
                    pass
            static_list.append(num)
        print "Dimensional=", dim
        print static_list

def ec_distribution(data, dim=-1):
    """
    examine the distribution of NEC in raw dataset
    """
    ec_dict = dict()
    for record in data:
        key = ';'.join(record[:dim])
        try:
            ec_dict[key] += 1
        except KeyError:
            ec_dict[key] = 1
    dist_dict = dict()
    for key, ec_size in ec_dict.items():
        try:
            dist_dict[ec_size] += 1
        except KeyError:
            dist_dict[ec_size] = 1
    # print dist_dict
    return dist_dict


def ec_exam_by_dim(dataset):
    """
    examine nature EC in raw dataset
    """
    qi_len = len(dataset[0]) - 1
    for dim in range(1, qi_len + 1):
        ec_dict = dict()
        for record in dataset:
            key = ';'.join(record[:dim])
            try:
                ec_dict[key] += 1
            except KeyError:
                ec_dict[key] = 1
        non_single_ec = [ec_size for key, ec_size in ec_dict.items() if ec_size >= 2]
        print "*" * 30
        print "Dimensional=", dim
        print "Size of dataset =", len(dataset)
        print "Num of nature EC =", len(ec_dict)
        print "Num of nature EC larger than 1 =", len(non_single_ec)
        print "Num of single Ec =", (len(ec_dict) - len(non_single_ec))


def ec_exam_by_size_data(dataset):
    joint = 5000
    data_size = []
    check_time = len(dataset) / joint
    if len(dataset) % joint == 0:
        check_time -= 1
    for i in range(check_time):
        data_size.append(joint * (i + 1))
    data_size.append(len(dataset))
    for pos in data_size:
        temp_data = dataset[:pos]
        ec_dict = dict()
        for record in temp_data:
            key = ';'.join(record[:-1])
            try:
                ec_dict[key] += 1
            except KeyError:
                ec_dict[key] = 1
        non_single_ec = [ec_size for key, ec_size in ec_dict.items() if ec_size >= 2]
        print "*" * 30
        print "Size of dataset =", pos
        print "Num of nature EC =", len(ec_dict)
        print "Num of nature EC larger than 1 =", len(non_single_ec)
        print "Num of single Ec =", (len(ec_dict) - len(non_single_ec))
