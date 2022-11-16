# -*- coding: utf-8 -*-
import hashlib
from functools import wraps
from flask import redirect, url_for

class SHA256:
    @staticmethod
    def encrypt(value):
        return hashlib.sha256(value.encode()).hexdigest()

    @staticmethod
    def compare_with(a, b):
        return SHA256.encrypt(a) == SHA256.encrypt(b)

