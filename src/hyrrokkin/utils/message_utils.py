#   Hyrrokkin - a Python library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2023  Visual Topology Ltd
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this software
#   and associated documentation files (the "Software"), to deal in the Software without
#   restriction, including without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or
#   substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#   BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json

class MessageUtils:

    @staticmethod
    def encode_message(*message_parts):

        encoded_components = []
        headers = []
        for content in message_parts:
            content_b = content
            header = {}
            if content is None:
                header["content_type"] = "null"
                content_b = b''
            elif isinstance(content,bytes):
                header["content_type"] = "binary"
            elif isinstance(content,str):
                content_b = content.encode("utf-8")
                header["content_type"] = "string"
            else:
                try:
                    content_b = json.dumps(content).encode("utf-8")
                    header["content_type"] = "json"
                except:
                    raise ValueError("content must by bytes, string, JSON-serialisable or None")
            header["length"] = len(content_b)
            headers.append(header)
            encoded_components.append(content_b)

        header = { "components": headers }
        header_b = json.dumps(header).encode("utf-8")
        return len(header_b).to_bytes(4,"big")+header_b+b"".join(encoded_components)


    @staticmethod
    def decode_message(encoded_message):
        header_len = int.from_bytes(encoded_message[0:4],"big")
        header_b = encoded_message[4:4+header_len]
        main_header_s = header_b.decode("utf-8")
        main_header = json.loads(main_header_s)
        offset = 4+header_len
        message_parts = []
        for header in main_header["components"]:
            content_len = header["length"]
            content_b = encoded_message[offset:offset+content_len]
            if header["content_type"] == "null":
                content = None
            elif header["content_type"] == "string":
                content = content_b.decode("utf-8")
            elif header["content_type"] == "binary":
                content = content_b
            elif header["content_type"] == "json":
                content = json.loads(content_b.decode("utf-8"))
            else:
                raise Exception("Corrupted message, cannot decode")
            message_parts.append(content)
            offset += content_len
        return message_parts