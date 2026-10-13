"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const axis = require("./calculator.js");

test("lead order does not reverse the QRS vector", () => {
  const target = 23 * Math.PI / 180;
  const i = Math.cos(target);
  const avf = Math.sin(target);
  assert.equal(axis.pair("I", i, "aVF", avf).axis_degrees, 23);
  assert.equal(axis.pair("aVF", avf, "I", i).axis_degrees, 23);
});

test("borderline negative aVF remains normal above -30 degrees", () => {
  const r = axis.pair("I", 1, "aVF", -0.1);
  assert.equal(r.classification, "normal");
  assert.ok(Math.abs(r.axis_degrees + 5.7) < 0.1);
});

test("multi-lead OLS recovers consistent vector", () => {
  const degrees = 37;
  const values = {};
  for (const [key, lead] of Object.entries(axis.ANGLES)) {
    values[key] = Math.cos((degrees - lead) * Math.PI / 180);
  }
  const r = axis.multi(values);
  assert.equal(r.n_leads, 6);
  assert.equal(r.axis_degrees, degrees);
});

test("zero vector is indeterminate", () => {
  assert.equal(axis.pair("I", 0, "aVF", 0).axis_degrees, null);
  assert.equal(axis.multi({I: 0, II: 0, aVF: 0}).classification, "indeterminate");
});

test("invalid lead selection and nonfinite input are rejected", () => {
  assert.throws(() => axis.pair("I", 0.2, "I", 0.4));
  assert.throws(() => axis.pair("I", "", "aVF", 1));
  assert.throws(() => axis.multi({I: "NaN", aVF: 1}));
  assert.throws(() => axis.multi({I: 1, aVF: 0.2, AVF: 0.5}));
});

test("CSV batch parses quoted fields and reports row errors", () => {
  const input = 'lead_i_net,lead_avf_net\r\n"1","-0.1"\r\n0,0\r\nbad,2\r\n';
  const out = axis.batchCsv(input);
  assert.equal(out.total, 3);
  assert.equal(out.errors, 1);
  const rows = axis.csvRows(out.csv);
  assert.equal(rows.length, 4);
  assert.equal(rows[1][2], "normal");
  assert.equal(rows[2][2], "indeterminate");
  assert.ok(rows[3][3].includes("finite"));
});

test("CSV cells with formula prefixes are neutralized in export", () => {
  const input = 'lead_i_net,lead_avf_net\n1,=CMD()\n';
  const out = axis.batchCsv(input);
  assert.equal(out.errors, 1);
  assert.ok(out.csv.includes("finite"));
});

test("CSV validates required columns and malformed quotes", () => {
  assert.throws(() => axis.batchCsv("id,value\na,b\n"), /requires/);
  assert.throws(() => axis.batchCsv('lead_i_net,lead_avf_net\n"1,2\n'), /Unterminated/);
});


test("wrapped 180 degrees and nonzero tiny vectors are consistent", () => {
  assert.equal(axis.classify(180), axis.classify(-180));
  assert.equal(axis.classify(540), "extreme_axis");
  assert.equal(axis.pair("I", 1e-15, "aVF", 1e-15).axis_degrees, 45);
  assert.equal(axis.multi({I: 1e-15, aVF: 1e-15}).axis_degrees, 45);
});
