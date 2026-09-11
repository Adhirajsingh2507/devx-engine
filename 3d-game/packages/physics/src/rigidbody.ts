import { Vec3, Quaternion, Transform } from "@engine/math";

/**
 * A rigid body with linear AND angular dynamics. Mutable — a body IS its
 * evolving state. Integrated with semi-implicit Euler (velocity first, then
 * position/orientation), which is stable enough for games.
 *
 * Rotation uses a **scalar (isotropic) inertia** — correct for a uniform sphere
 * and a fine first cut. ponytail: a full inertia tensor needs a Mat3 that gets
 * rotated into world space each step (I_world = R·I_body·Rᵀ); add that (and Mat3)
 * when a game needs non-spherical angular response.
 *
 * mass 0 ⇒ static (inverseMass = inverseInertia = 0): forces and torques never
 * move it. A dynamic body may still lock rotation by passing inertia 0.
 */
export class RigidBody {
  position: Vec3;
  velocity: Vec3;
  orientation: Quaternion;
  angularVelocity: Vec3; // rad/s, world space

  readonly mass: number;
  readonly inverseMass: number;
  readonly inertia: number;
  readonly inverseInertia: number;

  private force: Vec3 = Vec3.zero;
  private torque: Vec3 = Vec3.zero;

  constructor(
    opts: {
      position?: Vec3;
      velocity?: Vec3;
      orientation?: Quaternion;
      angularVelocity?: Vec3;
      mass?: number;
      /** Scalar moment of inertia. Defaults to `mass`; 0 locks rotation. */
      inertia?: number;
    } = {},
  ) {
    this.position = opts.position ?? Vec3.zero;
    this.velocity = opts.velocity ?? Vec3.zero;
    this.orientation = opts.orientation ?? Quaternion.identity;
    this.angularVelocity = opts.angularVelocity ?? Vec3.zero;

    const mass = opts.mass ?? 1;
    if (mass < 0) throw new RangeError("mass must be ≥ 0");
    this.mass = mass;
    this.inverseMass = mass === 0 ? 0 : 1 / mass;

    const inertia = opts.inertia ?? mass; // sensible nonzero default for dynamic bodies
    if (inertia < 0) throw new RangeError("inertia must be ≥ 0");
    this.inertia = inertia;
    this.inverseInertia = mass === 0 || inertia === 0 ? 0 : 1 / inertia;
  }

  get isStatic(): boolean {
    return this.inverseMass === 0;
  }

  /** Pose (position + orientation, unit scale) for the renderer / ECS. */
  get transform(): Transform {
    return new Transform(this.position, this.orientation, Vec3.one);
  }

  /** Queue a linear force (N) for the next integrate(). */
  applyForce(f: Vec3): void {
    this.force = this.force.add(f);
  }

  /** Queue a torque (N·m) for the next integrate(). */
  applyTorque(t: Vec3): void {
    this.torque = this.torque.add(t);
  }

  /** Advance by dt seconds; clears accumulated force and torque. */
  integrate(dt: number): void {
    if (this.inverseMass > 0) {
      const accel = this.force.scale(this.inverseMass);
      this.velocity = this.velocity.add(accel.scale(dt)); // v += a·dt
      this.position = this.position.add(this.velocity.scale(dt)); // x += v·dt
    }

    if (this.inverseInertia > 0) {
      const angAccel = this.torque.scale(this.inverseInertia);
      this.angularVelocity = this.angularVelocity.add(angAccel.scale(dt));
      // integrate the orientation quaternion: q += ½·dt·(ω⊗q), then renormalize
      const w = this.angularVelocity;
      const spin = new Quaternion(w.x, w.y, w.z, 0).multiply(this.orientation);
      const o = this.orientation;
      const h = 0.5 * dt;
      this.orientation = new Quaternion(
        o.x + h * spin.x,
        o.y + h * spin.y,
        o.z + h * spin.z,
        o.w + h * spin.w,
      ).normalize();
    }

    this.force = Vec3.zero;
    this.torque = Vec3.zero;
  }
}
