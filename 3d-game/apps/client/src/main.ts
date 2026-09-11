import { Vec3, Mat4, Transform, Aabb, Sphere } from "@engine/math";
import {
  RigidBody,
  World,
  SpatialHash,
  sphereSphereContact,
  sphereAabbContact,
  resolveContact,
} from "@engine/physics";
import { createProgram } from "./gl.ts";
import { uvSphere } from "./sphere.ts";

// ---------------------------------------------------------------- setup
const canvas = document.getElementById("c") as HTMLCanvasElement;
const gl = canvas.getContext("webgl2", { antialias: true });
if (!gl) {
  const err = document.getElementById("err")!;
  err.style.display = "grid";
  err.textContent = "WebGL2 is not available in this browser.";
  throw new Error("webgl2 unavailable");
}

gl.enable(gl.DEPTH_TEST);
gl.clearColor(0.04, 0.043, 0.055, 1);

// ---------------------------------------------------------------- shaders
const litVert = `#version 300 es
layout(location=0) in vec3 a_position;
layout(location=1) in vec3 a_normal;
uniform mat4 u_viewProj;
uniform mat4 u_model;
out vec3 v_normal;
void main() {
  v_normal = mat3(u_model) * a_normal;
  gl_Position = u_viewProj * u_model * vec4(a_position, 1.0);
}`;

const litFrag = `#version 300 es
precision highp float;
in vec3 v_normal;
uniform vec3 u_color;
uniform vec3 u_lightDir;
out vec4 outColor;
void main() {
  vec3 n = normalize(v_normal);
  float diff = max(dot(n, u_lightDir), 0.0);
  float rim = pow(1.0 - max(n.y, 0.0), 3.0) * 0.15;
  vec3 c = u_color * (0.28 + 0.85 * diff) + rim;
  outColor = vec4(pow(c, vec3(1.0 / 2.2)), 1.0);
}`;

const floorVert = `#version 300 es
layout(location=0) in vec3 a_position;
uniform mat4 u_viewProj;
out vec3 v_world;
void main() {
  v_world = a_position;
  gl_Position = u_viewProj * vec4(a_position, 1.0);
}`;

const floorFrag = `#version 300 es
precision highp float;
in vec3 v_world;
out vec4 outColor;
void main() {
  vec2 g = abs(fract(v_world.xz) - 0.5) / fwidth(v_world.xz);
  float line = 1.0 - min(min(g.x, g.y), 1.0);
  vec3 base = vec3(0.055, 0.062, 0.078);
  vec3 c = mix(base, vec3(0.16, 0.19, 0.26), line);
  float d = length(v_world.xz);
  c = mix(c, base, smoothstep(24.0, 55.0, d));
  outColor = vec4(c, 1.0);
}`;

const litProgram = createProgram(gl, litVert, litFrag);
const floorProgram = createProgram(gl, floorVert, floorFrag);

const uLit = {
  viewProj: gl.getUniformLocation(litProgram, "u_viewProj"),
  model: gl.getUniformLocation(litProgram, "u_model"),
  color: gl.getUniformLocation(litProgram, "u_color"),
  lightDir: gl.getUniformLocation(litProgram, "u_lightDir"),
};
const uFloor = { viewProj: gl.getUniformLocation(floorProgram, "u_viewProj") };

// ---------------------------------------------------------------- geometry
function makeIndexedVao(mesh: { positions: Float32Array; normals: Float32Array; indices: Uint16Array }) {
  const vao = gl!.createVertexArray()!;
  gl!.bindVertexArray(vao);
  for (const [loc, data] of [[0, mesh.positions], [1, mesh.normals]] as const) {
    const buf = gl!.createBuffer()!;
    gl!.bindBuffer(gl!.ARRAY_BUFFER, buf);
    gl!.bufferData(gl!.ARRAY_BUFFER, data, gl!.STATIC_DRAW);
    gl!.enableVertexAttribArray(loc);
    gl!.vertexAttribPointer(loc, 3, gl!.FLOAT, false, 0, 0);
  }
  const ib = gl!.createBuffer()!;
  gl!.bindBuffer(gl!.ELEMENT_ARRAY_BUFFER, ib);
  gl!.bufferData(gl!.ELEMENT_ARRAY_BUFFER, mesh.indices, gl!.STATIC_DRAW);
  gl!.bindVertexArray(null);
  return { vao, count: mesh.indices.length };
}

const sphereMesh = makeIndexedVao(uvSphere());

const FLOOR_HALF = 60;
const floorVao = gl.createVertexArray()!;
gl.bindVertexArray(floorVao);
const floorBuf = gl.createBuffer()!;
gl.bindBuffer(gl.ARRAY_BUFFER, floorBuf);
// two triangles in the y=0 plane
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
  -FLOOR_HALF, 0, -FLOOR_HALF,  FLOOR_HALF, 0, -FLOOR_HALF,  FLOOR_HALF, 0, FLOOR_HALF,
  -FLOOR_HALF, 0, -FLOOR_HALF,  FLOOR_HALF, 0, FLOOR_HALF,  -FLOOR_HALF, 0, FLOOR_HALF,
]), gl.STATIC_DRAW);
gl.enableVertexAttribArray(0);
gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
gl.bindVertexArray(null);

// ---------------------------------------------------------------- physics
const GRAVITY = new Vec3(0, -22, 0);
const FLOOR = new Aabb(new Vec3(-FLOOR_HALF, -1, -FLOOR_HALF), new Vec3(FLOOR_HALF, 0, FLOOR_HALF));
const FLOOR_BODY = new RigidBody({ mass: 0 }); // static
const FLOOR_RESTITUTION = 0.4;
const SPHERE_RESTITUTION = 0.5;
const MAX = 90;

const PALETTE: Vec3[] = [
  new Vec3(0.45, 0.6, 1.0), new Vec3(0.65, 0.5, 0.95), new Vec3(0.3, 0.8, 0.75),
  new Vec3(1.0, 0.7, 0.35), new Vec3(0.95, 0.45, 0.55), new Vec3(0.55, 0.85, 0.5),
];

interface Ball { body: RigidBody; radius: number; color: Vec3; }
let balls: Ball[] = [];
let world = new World(GRAVITY);
const hash = new SpatialHash(3);

function spawn(x?: number, z?: number, y = 14): void {
  if (balls.length >= MAX) {
    const old = balls.shift()!;
    world.bodies.splice(world.bodies.indexOf(old.body), 1);
  }
  const radius = 0.45 + Math.random() * 0.55;
  const body = new RigidBody({
    mass: radius * radius * radius,
    position: new Vec3(x ?? (Math.random() - 0.5) * 12, y, z ?? (Math.random() - 0.5) * 12),
    velocity: new Vec3((Math.random() - 0.5) * 3, 0, (Math.random() - 0.5) * 3),
  });
  world.add(body);
  balls.push({ body, radius, color: PALETTE[balls.length % PALETTE.length] });
}

function reset(): void {
  balls = [];
  world = new World(GRAVITY);
  for (let i = 0; i < 16; i++) spawn(undefined, undefined, 3 + Math.random() * 12);
}
reset();

let lastPairs = 0;
function simulate(dt: number): void {
  world.step(dt); // gravity + integrate every body
  const aabbs = balls.map((b) => Aabb.fromCenter(b.body.position, new Vec3(b.radius, b.radius, b.radius)));
  for (let iter = 0; iter < 2; iter++) {
    for (const b of balls) {
      const c = sphereAabbContact(new Sphere(b.body.position, b.radius), FLOOR);
      if (c) resolveContact(b.body, FLOOR_BODY, c, FLOOR_RESTITUTION);
    }
    const pairs = hash.pairs(aabbs);
    if (iter === 0) lastPairs = pairs.length;
    for (const [i, j] of pairs) {
      const a = balls[i], b = balls[j];
      const c = sphereSphereContact(
        new Sphere(a.body.position, a.radius),
        new Sphere(b.body.position, b.radius),
      );
      if (c) resolveContact(a.body, b.body, c, SPHERE_RESTITUTION);
    }
  }
}

// ---------------------------------------------------------------- render
const LIGHT = new Vec3(0.4, 1.0, 0.35).normalize();

function resize(): void {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.floor(canvas.clientWidth * dpr);
  const h = Math.floor(canvas.clientHeight * dpr);
  if (canvas.width !== w || canvas.height !== h) {
    canvas.width = w;
    canvas.height = h;
    gl!.viewport(0, 0, w, h);
  }
}

function f32(m: Mat4): Float32Array {
  return new Float32Array(m.toArray());
}

function render(time: number): void {
  resize();
  gl!.clear(gl!.COLOR_BUFFER_BIT | gl!.DEPTH_BUFFER_BIT);

  const aspect = canvas.width / Math.max(canvas.height, 1);
  const proj = Mat4.perspective(Math.PI / 4, aspect, 0.1, 200);
  const angle = time * 0.15;
  const eye = new Vec3(Math.cos(angle) * 26, 17, Math.sin(angle) * 26);
  const viewProj = proj.multiply(Mat4.lookAt(eye, new Vec3(0, 3, 0), new Vec3(0, 1, 0)));
  const vp = f32(viewProj);

  gl!.useProgram(floorProgram);
  gl!.uniformMatrix4fv(uFloor.viewProj, false, vp);
  gl!.bindVertexArray(floorVao);
  gl!.drawArrays(gl!.TRIANGLES, 0, 6);

  gl!.useProgram(litProgram);
  gl!.uniformMatrix4fv(uLit.viewProj, false, vp);
  gl!.uniform3f(uLit.lightDir, LIGHT.x, LIGHT.y, LIGHT.z);
  gl!.bindVertexArray(sphereMesh.vao);
  for (const b of balls) {
    const model = new Transform(
      b.body.position,
      b.body.orientation,
      new Vec3(b.radius, b.radius, b.radius),
    ).toMatrix();
    gl!.uniformMatrix4fv(uLit.model, false, f32(model));
    gl!.uniform3f(uLit.color, b.color.x, b.color.y, b.color.z);
    gl!.drawElements(gl!.TRIANGLES, sphereMesh.count, gl!.UNSIGNED_SHORT, 0);
  }
}

// ---------------------------------------------------------------- loop + input
const hud = document.getElementById("hud")!;
let fps = 60;
let last = performance.now();
let acc = 0;
const STEP = 1 / 120;

function frame(now: number): void {
  const dt = Math.min((now - last) / 1000, 0.05);
  last = now;
  fps += ((1 / Math.max(dt, 1e-4)) - fps) * 0.1;
  acc += dt;
  while (acc >= STEP) {
    simulate(STEP);
    acc -= STEP;
  }
  render(now / 1000);
  hud.innerHTML =
    `<span class="n">${fps.toFixed(0)}</span> fps · ` +
    `<span class="n">${balls.length}</span> bodies · ` +
    `<span class="n">${lastPairs}</span> broadphase pairs`;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

canvas.addEventListener("click", () => spawn());
window.addEventListener("keydown", (e) => {
  if (e.key === "r" || e.key === "R") reset();
});
