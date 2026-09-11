import { RigidBody } from "./rigidbody.ts";
import type { Contact } from "./narrowphase.ts";

const CORRECTION_PERCENT = 0.8; // fraction of penetration fixed per resolve
const SLOP = 0.01; // penetration left unfixed, to avoid jitter at rest

/**
 * Resolve a contact between a and b with a linear impulse (with restitution) plus
 * positional correction. `contact.normal` must point from a → b.
 *
 * restitution 0 = perfectly inelastic, 1 = perfectly elastic (energy-preserving).
 *
 * ponytail: linear response only — no friction, and no torque from off-centre
 * hits (that needs the contact point applied through a real inertia tensor). The
 * contact already carries `point`; add angular + friction as the next rung.
 */
export function resolveContact(
  a: RigidBody,
  b: RigidBody,
  contact: Contact,
  restitution = 0,
): void {
  const invMassSum = a.inverseMass + b.inverseMass;
  if (invMassSum === 0) return; // two static bodies — nothing to move

  const n = contact.normal;
  const relVelAlongN = b.velocity.sub(a.velocity).dot(n);

  // impulse only if the bodies are approaching along the normal
  if (relVelAlongN < 0) {
    const j = (-(1 + restitution) * relVelAlongN) / invMassSum;
    const impulse = n.scale(j);
    a.velocity = a.velocity.sub(impulse.scale(a.inverseMass));
    b.velocity = b.velocity.add(impulse.scale(b.inverseMass));
  }

  // positional correction: shove the bodies apart along the normal
  const corr = (Math.max(contact.depth - SLOP, 0) / invMassSum) * CORRECTION_PERCENT;
  if (corr > 0) {
    const correction = n.scale(corr);
    a.position = a.position.sub(correction.scale(a.inverseMass));
    b.position = b.position.add(correction.scale(b.inverseMass));
  }
}
