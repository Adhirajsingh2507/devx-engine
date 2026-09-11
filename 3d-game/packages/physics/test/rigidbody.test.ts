import { test } from "node:test";
import assert from "node:assert/strict";
import { Vec3 } from "@engine/math";
import { RigidBody, World } from "../src/index.ts";

test("inverseMass: dynamic vs static", () => {
  assert.equal(new RigidBody({ mass: 2 }).inverseMass, 0.5);
  const s = new RigidBody({ mass: 0 });
  assert.equal(s.inverseMass, 0);
  assert.ok(s.isStatic);
});

test("negative mass is rejected", () => {
  assert.throws(() => new RigidBody({ mass: -1 }), RangeError);
});

test("constant velocity, no force: x += v·dt", () => {
  const b = new RigidBody({ velocity: new Vec3(2, 0, 0) });
  b.integrate(0.5);
  assert.ok(b.position.equals(new Vec3(1, 0, 0)));
  assert.ok(b.velocity.equals(new Vec3(2, 0, 0)));
});

test("applyForce accelerates by F/m and is cleared after the step", () => {
  const b = new RigidBody({ mass: 2 });
  b.applyForce(new Vec3(10, 0, 0)); // a = 5 m/s²
  b.integrate(1);
  assert.ok(b.velocity.equals(new Vec3(5, 0, 0)));
  assert.ok(b.position.equals(new Vec3(5, 0, 0))); // semi-implicit: uses new v
  // force cleared → next step with no new force keeps velocity constant
  b.integrate(1);
  assert.ok(b.velocity.equals(new Vec3(5, 0, 0)));
});

test("static body ignores forces", () => {
  const s = new RigidBody({ mass: 0, position: new Vec3(1, 2, 3) });
  s.applyForce(new Vec3(1000, 0, 0));
  s.integrate(1);
  assert.ok(s.position.equals(new Vec3(1, 2, 3)));
});

test("World applies gravity as pure acceleration (mass-independent)", () => {
  const w = new World(new Vec3(0, -10, 0));
  const light = w.add(new RigidBody({ mass: 1 }));
  const heavy = w.add(new RigidBody({ mass: 100 }));
  w.step(0.1);
  // both fall at the same rate
  assert.ok(light.velocity.equals(new Vec3(0, -1, 0)));
  assert.ok(heavy.velocity.equals(new Vec3(0, -1, 0)));
  assert.ok(light.position.equals(heavy.position));
});

test("World leaves static bodies (the ground) put", () => {
  const w = new World(new Vec3(0, -10, 0));
  const ground = w.add(new RigidBody({ mass: 0, position: Vec3.zero }));
  w.step(0.1);
  assert.ok(ground.position.equals(Vec3.zero));
});
