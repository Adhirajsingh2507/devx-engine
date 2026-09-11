import { Vec3 } from "@engine/math";
import { RigidBody } from "./rigidbody.ts";

/**
 * Holds bodies and steps them under a uniform gravity field. Gravity is applied
 * as a force (mass·g) so it cancels to a pure acceleration on dynamic bodies and
 * leaves static bodies untouched.
 *
 * ponytail: no broadphase/collision yet — bodies pass through each other. Add a
 * spatial hash + contact solver here when the first game needs collisions.
 */
export class World {
  readonly gravity: Vec3;
  readonly bodies: RigidBody[] = [];

  constructor(gravity: Vec3 = new Vec3(0, -9.81, 0)) {
    this.gravity = gravity;
  }

  add(body: RigidBody): RigidBody {
    this.bodies.push(body);
    return body;
  }

  step(dt: number): void {
    for (const body of this.bodies) {
      if (!body.isStatic) body.applyForce(this.gravity.scale(body.mass));
      body.integrate(dt);
    }
  }
}
