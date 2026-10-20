"""Unit tests for polyglot language trimming."""

import unittest
from tokentrim.polyglot_trimmer import trim_polyglot_code


class TestPolyglotTrimmer(unittest.TestCase):
    def test_typescript_interface_and_function(self):
        source = """
import { Request, Response } from 'express';

export interface UserDTO {
  id: string;
  email: string;
  role: 'admin' | 'user';
}

export function sanitizeUser(user: UserDTO): Partial<UserDTO> {
  const clean = { ...user };
  delete clean.role;
  return clean;
}
"""
        trimmed = trim_polyglot_code(source, "ts")
        self.assertIn("export interface UserDTO {", trimmed)
        self.assertIn("email: string;", trimmed)
        self.assertIn("export function sanitizeUser(user: UserDTO): Partial<UserDTO> { /* ... */ }", trimmed)
        self.assertNotIn("delete clean.role;", trimmed)

    def test_javascript_class_methods(self):
        source = """
class AuthService {
  constructor(secret) {
    this.secret = secret;
    this.tokens = new Map();
  }

  generateToken(userId) {
    const payload = { sub: userId, exp: Date.now() + 3600 };
    return jwt.sign(payload, this.secret);
  }
}
"""
        trimmed = trim_polyglot_code(source, "js")
        self.assertIn("class AuthService {", trimmed)
        self.assertIn("generateToken(userId) { /* ... */ }", trimmed)
        self.assertNotIn("this.tokens = new Map()", trimmed)

    def test_go_func_and_struct(self):
        source = """
package main

import "fmt"

type ServerConfig struct {
    Port int
    Host string
}

func StartServer(cfg ServerConfig) error {
    fmt.Printf("Starting on %s:%d\\n", cfg.Host, cfg.Port)
    return nil
}
"""
        trimmed = trim_polyglot_code(source, "go")
        self.assertIn("type ServerConfig struct {", trimmed)
        self.assertIn("func StartServer(cfg ServerConfig) error { /* ... */ }", trimmed)
        self.assertNotIn("fmt.Printf", trimmed)

    def test_rust_fn_and_struct(self):
        source = """
pub struct TokenMetrics {
    pub original: usize,
    pub trimmed: usize,
}

pub fn calculate_ratio(metrics: &TokenMetrics) -> f64 {
    let diff = metrics.original - metrics.trimmed;
    (diff as f64) / (metrics.original as f64)
}
"""
        trimmed = trim_polyglot_code(source, "rs")
        self.assertIn("pub struct TokenMetrics {", trimmed)
        self.assertIn("pub fn calculate_ratio(metrics: &TokenMetrics) -> f64 { /* ... */ }", trimmed)
        self.assertNotIn("let diff = metrics.original", trimmed)


if __name__ == "__main__":
    unittest.main()
