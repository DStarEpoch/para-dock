#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2025/4/16 8:30
# @Author : yuyeqing
# @File   : top_file.py
# @IDE    : PyCharm
import re
from pathlib import Path


class TopElement:

    def __init__(self, element_type: str='element'):
        self.element_type = element_type
        self.elem_line = ''

    @staticmethod
    def is_type_match(line:str):
        return True

    @classmethod
    def create_from_line(cls, line: str):
        """
        Create an element from a line of text.
        :param line: The line of text to create the element from.
        """
        instance = cls()
        instance.elem_line = line.strip()
        return instance

    def __str__(self):
        return self.elem_line

class TopComment(TopElement):
    def __init__(self):
        super().__init__(element_type='comment')

    @staticmethod
    def is_type_match(line: str):
        ls = line.strip()
        pattern = r'^\s*;'
        match = re.match(pattern, ls)
        if match:
            return True
        else:
            return False

class TopInclude(TopElement):

    def __init__(self):
        super().__init__(element_type='include')

    @staticmethod
    def is_type_match(line: str):
        pattern = r'^\s*#include\s+<([^>]+)>'
        match = re.match(pattern, line)
        if match:
            return True
        else:
            return False

registered_elements = [
    ('comment', TopComment),
    ('include', TopInclude),
    ('element', TopElement),
]


class TopBlock:

    def __init__(self, block_type: str=''):
        self.block_type = block_type
        self.elements: list[TopElement] = []

    def add_element(self, ele: TopElement):
        self.elements.append(ele)

    @staticmethod
    def is_block_start(line: str):
        pattern = r'^\[\s*(.*?)\s*\](.*)$'
        match = re.match(pattern, line)
        if match:
            block_type = match.group(1)
            content_after_brackets = match.group(2).strip()
            return block_type, content_after_brackets
        else:
            return None, None

    def __str__(self):
        """
        Convert the block to a string representation.
        """
        if self.block_type:
            block_str = f"[ {self.block_type} ]\n"
        else:
            block_str = ''
        for ele in self.elements:
            block_str += str(ele) + '\n'
        return block_str.strip()


class TopFile:
    """
    A class to handle topology file for molecular simulations.
    """

    def __init__(self, top_file_path: str):
        """
        Initialize the TopFile object.

        :param top_file_path: Path to the topology file.
        """
        self.top_file_path = Path(top_file_path)
        self.topol_info = self.load_topology()

    def load_topology(self):
        """
        Load the topology file and parse it.

        :return: Parsed topology data.
        """
        if not self.top_file_path.exists():
            raise FileNotFoundError(f"Topology file {self.top_file_path} does not exist.")

        with open(self.top_file_path, 'r') as file:
            topology_data = file.readlines()

        last_block = TopBlock()
        topol_info = [last_block, ]
        for line in topology_data:
            block_type, content_after_brackets = TopBlock.is_block_start(line)
            if block_type:
                last_block = TopBlock(block_type)
                if content_after_brackets:
                    last_block.add_element(self.assign_element(content_after_brackets))
                topol_info.append(last_block)
                continue
            ele = self.assign_element(line)
            if ele:
                last_block.add_element(ele)
                continue

        return topol_info

    @staticmethod
    def assign_element(line: str):
        """
        Assign the line to the appropriate element type.

        :param line: The line to be assigned.
        :return: The assigned element.
        """
        for name, cls in registered_elements:
            if cls.is_type_match(line):
                return cls.create_from_line(line)
        raise ValueError(f"Unknown element type for line: {line}")

    def __str__(self):
        """
        Convert the topology file to a string representation.
        """
        top_str = ''
        for block in self.topol_info:
            top_str += str(block) + '\n\n'
        return top_str
