#!/usr/bin/env python3
"""
字节长度测试类

用于测试不同编码方式下字符串的字节长度。
"""

import unittest
import sys
from typing import Dict, List, Any


class ByteLengthTest(unittest.TestCase):
    """字节长度测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.test_string = "Xsv9hRk1z5ystj9MhnA7Lq4vjSsLwzL2nxrwmwtD3re"
        self.expected_lengths = {
            'utf-8': 43,
            'ascii': 43,
            'latin-1': 43,
            'utf-16': 88,  # 包含BOM
            'utf-16le': 86,
            'utf-16be': 86,
            'utf-32': 176,  # 包含BOM
            'utf-32le': 172,
            'utf-32be': 172
        }
    
    def test_utf8_byte_length(self):
        """测试UTF-8编码的字节长度"""
        byte_length = len(self.test_string.encode('utf-8'))
        print(f"UTF-8字节长度: {byte_length}")
        self.assertEqual(byte_length, self.expected_lengths['utf-8'])
    
    def test_ascii_byte_length(self):
        """测试ASCII编码的字节长度"""
        byte_length = len(self.test_string.encode('ascii'))
        print(f"ASCII字节长度: {byte_length}")
        self.assertEqual(byte_length, self.expected_lengths['ascii'])
    
    def test_latin1_byte_length(self):
        """测试Latin-1编码的字节长度"""
        byte_length = len(self.test_string.encode('latin-1'))
        print(f"Latin-1字节长度: {byte_length}")
        self.assertEqual(byte_length, self.expected_lengths['latin-1'])
    
    def test_utf16_byte_length(self):
        """测试UTF-16编码的字节长度"""
        byte_length = len(self.test_string.encode('utf-16'))
        print(f"UTF-16字节长度: {byte_length}")
        self.assertEqual(byte_length, self.expected_lengths['utf-16'])
    
    def test_utf16le_byte_length(self):
        """测试UTF-16LE编码的字节长度"""
        byte_length = len(self.test_string.encode('utf-16le'))
        print(f"UTF-16LE字节长度: {byte_length}")
        self.assertEqual(byte_length, self.expected_lengths['utf-16le'])
    
    def test_utf16be_byte_length(self):
        """测试UTF-16BE编码的字节长度"""
        byte_length = len(self.test_string.encode('utf-16be'))
        print(f"UTF-16BE字节长度: {byte_length}")
        self.assertEqual(byte_length, self.expected_lengths['utf-16be'])
    
    def test_utf32_byte_length(self):
        """测试UTF-32编码的字节长度"""
        byte_length = len(self.test_string.encode('utf-32'))
        print(f"UTF-32字节长度: {byte_length}")
        self.assertEqual(byte_length, self.expected_lengths['utf-32'])
    
    def test_utf32le_byte_length(self):
        """测试UTF-32LE编码的字节长度"""
        byte_length = len(self.test_string.encode('utf-32le'))
        print(f"UTF-32LE字节长度: {byte_length}")
        self.assertEqual(byte_length, self.expected_lengths['utf-32le'])
    
    def test_utf32be_byte_length(self):
        """测试UTF-32BE编码的字节长度"""
        byte_length = len(self.test_string.encode('utf-32be'))
        print(f"UTF-32BE字节长度: {byte_length}")
        self.assertEqual(byte_length, self.expected_lengths['utf-32be'])
    
    def test_all_encodings(self):
        """测试所有编码的字节长度"""
        print(f"\n测试字符串: {self.test_string}")
        print(f"字符串长度: {len(self.test_string)}")
        
        for encoding in ['utf-8', 'ascii', 'latin-1', 'utf-16', 'utf-16le', 'utf-16be', 'utf-32', 'utf-32le', 'utf-32be']:
            try:
                byte_length = len(self.test_string.encode(encoding))
                print(f"{encoding.upper()}: {byte_length} 字节")
                self.assertEqual(byte_length, self.expected_lengths[encoding])
            except UnicodeEncodeError as e:
                print(f"{encoding.upper()}: 编码错误 - {e}")
    
    def test_character_analysis(self):
        """分析字符串中每个字符的字节长度"""
        print(f"\n字符分析:")
        print(f"字符串: {self.test_string}")
        print(f"总字符数: {len(self.test_string)}")
        
        for i, char in enumerate(self.test_string):
            utf8_bytes = char.encode('utf-8')
            utf8_length = len(utf8_bytes)
            print(f"字符 {i+1}: '{char}' -> UTF-8: {utf8_bytes.hex()} ({utf8_length} 字节)")
    
    def test_byte_representation(self):
        """显示不同编码的字节表示"""
        print(f"\n字节表示:")
        print(f"字符串: {self.test_string}")
        
        encodings = ['utf-8', 'ascii', 'utf-16le', 'utf-32le']
        
        for encoding in encodings:
            try:
                bytes_data = self.test_string.encode(encoding)
                hex_representation = bytes_data.hex()
                print(f"{encoding.upper()}: {hex_representation} ({len(bytes_data)} 字节)")
            except UnicodeEncodeError as e:
                print(f"{encoding.upper()}: 编码错误 - {e}")


class ByteLengthAnalyzer:
    """字节长度分析器"""
    
    def __init__(self, test_string: str):
        """
        初始化分析器
        
        Args:
            test_string: 要分析的字符串
        """
        self.test_string = test_string
        self.encodings = [
            'utf-8', 'ascii', 'latin-1', 
            'utf-16', 'utf-16le', 'utf-16be',
            'utf-32', 'utf-32le', 'utf-32be'
        ]
    
    def analyze_byte_lengths(self) -> Dict[str, int]:
        """
        分析所有编码的字节长度
        
        Returns:
            Dict[str, int]: 编码名称到字节长度的映射
        """
        results = {}
        
        for encoding in self.encodings:
            try:
                byte_length = len(self.test_string.encode(encoding))
                results[encoding] = byte_length
            except UnicodeEncodeError:
                results[encoding] = -1  # 表示编码错误
        
        return results
    
    def print_analysis(self):
        """打印分析结果"""
        print(f"字符串: {self.test_string}")
        print(f"字符数: {len(self.test_string)}")
        print(f"字符类型: {type(self.test_string)}")
        print()
        
        results = self.analyze_byte_lengths()
        
        print("各编码字节长度:")
        for encoding, length in results.items():
            if length == -1:
                print(f"  {encoding.upper()}: 编码错误")
            else:
                print(f"  {encoding.upper()}: {length} 字节")
        
        print()
        
        # 显示UTF-8的详细分析
        utf8_bytes = self.test_string.encode('utf-8')
        print(f"UTF-8详细分析:")
        print(f"  字节数据: {utf8_bytes}")
        print(f"  十六进制: {utf8_bytes.hex()}")
        print(f"  字节长度: {len(utf8_bytes)}")
        
        # 分析每个字符
        print(f"\n字符分析:")
        for i, char in enumerate(self.test_string):
            char_bytes = char.encode('utf-8')
            print(f"  {i+1:2d}. '{char}' -> {char_bytes.hex()} ({len(char_bytes)} 字节)")
    
    def get_optimal_encoding(self) -> str:
        """
        获取最优编码（字节数最少的编码）
        
        Returns:
            str: 最优编码名称
        """
        results = self.analyze_byte_lengths()
        valid_results = {k: v for k, v in results.items() if v != -1}
        
        if not valid_results:
            return "无有效编码"
        
        optimal_encoding = min(valid_results, key=valid_results.get)
        return optimal_encoding


def run_byte_length_test():
    """运行字节长度测试"""
    test_string = "Xsv9hRk1z5ystj9MhnA7Lq4vjSsLwzL2nxrwmwtD3re"
    
    print("=== 字节长度测试 ===")
    
    # 使用分析器
    analyzer = ByteLengthAnalyzer(test_string)
    analyzer.print_analysis()
    
    print(f"\n最优编码: {analyzer.get_optimal_encoding()}")
    
    # 运行单元测试
    print(f"\n=== 单元测试 ===")
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_byte_length_test() 