# MIT License
#
# Narvi - a simple python web application server
#
# Copyright (C) 2022-2024 Visual Topology Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from hyrrokkin.utils.message_utils import MessageUtils

import unittest

class TestMessageUtils(unittest.TestCase):

    def test1(self):
        header = { "test": "test1" }
        content = "foobaz"

        encoded_msg = MessageUtils.encode_message(header, content)
        decoded = MessageUtils.decode_message(encoded_msg)

        self.assertEqual(decoded[0],header)
        self.assertEqual(decoded[1],content)

    def test2(self):
        header = {"test": "test1"};
        content = b'ff' * 10

        encoded_msg = MessageUtils.encode_message(header, content)
        decoded = MessageUtils.decode_message(encoded_msg)
        self.assertEqual(decoded[0], header)
        self.assertEqual(decoded[1], content)

    def test3(self):
        header = {"test": "test1"};
        content1 = b'ff' * 10
        content2 = "aaa"

        encoded_msg = MessageUtils.encode_message(header, content1, content2)
        decoded = MessageUtils.decode_message(encoded_msg)
        self.assertEqual(decoded[0], header)
        self.assertEqual(decoded[1], content1)
        self.assertEqual(decoded[2], content2)

if __name__ == '__main__':
    unittest.main()


