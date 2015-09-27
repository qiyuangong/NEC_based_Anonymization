"""
examine nature EC in raw dataset
"""

# !/usr/bin/env python
# coding=utf-8
from utils.utility import list_to_str


def ec_exam(dataset):
    """
    examine nature EC in raw dataset
    """
    ec_dict = dict()
    for record in dataset:
        key = ';'.join(record[:-1])
        try:
            ec_dict[key].append(record)
        except KeyError:
            ec_dict[key] = [record]
    non_single_ec = [record_set for key, record_set in ec_dict.items() if len(record_set) >= 2]
    print "Size of dataset =", len(dataset)
    print "Num of nature EC =", len(ec_dict)
    print "Num of nature EC larger than 1 =", len(non_single_ec)
    print "Num of single Ec =", (len(ec_dict) - len(non_single_ec))
