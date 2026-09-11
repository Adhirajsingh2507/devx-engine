import { Vec3 } from "@engine/math";

/**
 * A point-mass rigid body (no rotation yet). Mutable — unlike the math value
 * types, a body IS its evolving state. Integrated with semi-implicit Euler,
 * which is stable enough for games (velocity updates first, then position).
 *
 * mass 0 ⇒ static/immovable (inverseMass 0), so forces never move it.
 */
export class RigidBody {
  position: Vec3;
  velocity: Vec3;
  readonly mass: number;
  readonly inverseMass: number;
  /** Accumulated force for the current step; cleared after integrate(). */
  private force: Vec3 = Vec3.zero;

  constructor(opts: { position?: Vec3; velocity?: Vec3; mass?: number } = {}) {
    this.position = opts.position ?? Vec3.zero;
    this.velocity = opts.velocity ?? Vec3.zero;
    const mass = opts.mass ?? 1;
    if (mass < 0) throw new RangeError("mass must be ≥ 0");
    this.mass = mass;
    this.inverseMass = mass === 0 ? 0 : 1 / mass;
  }

  get isStatic(): boolean {
    return this.inverseMass === 0;
  }

  /** Queue a force (Newtons) to apply on the next integrate(). */
  applyForce(f: Vec3): void {
    this.force = this.force.add(f);
  }

  /** Advance by dt seconds and clear the accumulated force. */
  integrate(dt: number): void {
    if (this.isStatic) {
      this.force = Vec3.zero;
      return;
    }
    const accel = this.force.scale(this.inverseMass);
    this.velocity = this.velocity.add(accel.scale(dt)); // v += a·dt
    this.position = this.position.add(this.velocity.scale(dt)); // x += v·dt
    this.force = Vec3.zero;
  }
}
