/**
 * ORBIT-TRUST adapter for the procedural model in
 * 3d-game/apps/client/src/sphere.ts. Kept local because the Vercel application
 * root cannot bundle arbitrary files outside orbit-trust. The source project
 * remains unchanged and authoritative for future engine development.
 */
export interface SphereMesh {
  positions: Float32Array;
  normals: Float32Array;
  indices: Uint16Array;
}

export function uvSphere(segments = 24, rings = 16): SphereMesh {
  const positions: number[] = [];
  const indices: number[] = [];
  for (let y = 0; y <= rings; y += 1) {
    const phi = (y / rings) * Math.PI;
    for (let x = 0; x <= segments; x += 1) {
      const theta = (x / segments) * Math.PI * 2;
      positions.push(Math.sin(phi) * Math.cos(theta), Math.cos(phi), Math.sin(phi) * Math.sin(theta));
    }
  }
  const stride = segments + 1;
  for (let y = 0; y < rings; y += 1) {
    for (let x = 0; x < segments; x += 1) {
      const a = y * stride + x;
      const b = a + stride;
      indices.push(a, b, a + 1, a + 1, b, b + 1);
    }
  }
  const points = new Float32Array(positions);
  return { positions: points, normals: points.slice(), indices: new Uint16Array(indices) };
}
