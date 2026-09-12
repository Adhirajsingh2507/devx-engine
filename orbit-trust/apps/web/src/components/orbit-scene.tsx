"use client";

import { useEffect, useRef } from "react";
import { Vec3 } from "@engine/math";
import { uvSphere } from "../engine/uv-sphere";

const TAU = Math.PI * 2;

function rotate(point: Vec3, yaw: number, pitch: number): Vec3 {
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x = point.x * cy - point.z * sy;
  const z = point.x * sy + point.z * cy;
  return new Vec3(x, point.y * cp - z * sp, point.y * sp + z * cp);
}

export function OrbitScene() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;
    const sphere = uvSphere(30, 18);
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let frame = 0;
    let handle = 0;

    const draw = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.max(320, canvas.clientWidth);
      const height = Math.max(240, canvas.clientHeight);
      if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
        canvas.width = width * dpr;
        canvas.height = height * dpr;
      }
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      context.clearRect(0, 0, width, height);

      const cx = width * 0.5;
      const cy = height * 0.52;
      const radius = Math.min(width, height) * 0.22;
      const bg = context.createRadialGradient(cx, cy, radius * 0.2, cx, cy, width * 0.66);
      bg.addColorStop(0, "#132a42");
      bg.addColorStop(1, "#07101d");
      context.fillStyle = bg;
      context.fillRect(0, 0, width, height);

      context.strokeStyle = "rgba(96,165,250,.18)";
      context.lineWidth = 1;
      for (const scale of [1.55, 1.95]) {
        context.beginPath();
        context.ellipse(cx, cy, radius * scale, radius * scale * 0.34, -0.22, 0, TAU);
        context.stroke();
      }

      const earth = context.createRadialGradient(cx - radius * 0.32, cy - radius * 0.4, radius * 0.08, cx, cy, radius);
      earth.addColorStop(0, "#60a5fa");
      earth.addColorStop(0.48, "#1d4f86");
      earth.addColorStop(1, "#071524");
      context.fillStyle = earth;
      context.beginPath();
      context.arc(cx, cy, radius, 0, TAU);
      context.fill();

      const yaw = reducedMotion ? 0.35 : frame * 0.002;
      context.fillStyle = "rgba(191,219,254,.28)";
      for (let i = 0; i < sphere.positions.length; i += 15) {
        const p = rotate(new Vec3(sphere.positions[i], sphere.positions[i + 1], sphere.positions[i + 2]), yaw, -0.28);
        if (p.z < -0.08) continue;
        context.globalAlpha = 0.12 + p.z * 0.18;
        context.fillRect(cx + p.x * radius, cy - p.y * radius, 1.2, 1.2);
      }
      context.globalAlpha = 1;

      const t = reducedMotion ? 0.68 : frame * 0.006;
      const satellites = [
        { angle: t, scale: 1.55, color: "#f8fafc", label: "ASTERIA-3" },
        { angle: t + 0.16, scale: 1.55, color: "#fb7185", label: "DEBRIS" },
        { angle: t + 2.6, scale: 1.95, color: "#38bdf8", label: "VARUNA-2" },
      ];
      for (const sat of satellites) {
        const x = cx + Math.cos(sat.angle) * radius * sat.scale;
        const y = cy + Math.sin(sat.angle) * radius * sat.scale * 0.34;
        context.shadowColor = sat.color;
        context.shadowBlur = 12;
        context.fillStyle = sat.color;
        context.beginPath();
        context.arc(x, y, sat.label === "DEBRIS" ? 3 : 4.5, 0, TAU);
        context.fill();
        context.shadowBlur = 0;
        context.font = "600 10px Inter, system-ui, sans-serif";
        context.fillStyle = "rgba(226,232,240,.82)";
        context.fillText(sat.label, x + 9, y - 7);
      }

      const x = cx + Math.cos(t + 0.08) * radius * 1.55;
      const y = cy + Math.sin(t + 0.08) * radius * 1.55 * 0.34;
      context.setLineDash([3, 3]);
      context.strokeStyle = "rgba(251,113,133,.78)";
      context.beginPath();
      context.ellipse(x, y, 22, 9, -0.2, 0, TAU);
      context.stroke();
      context.setLineDash([]);

      frame += 1;
      if (!reducedMotion) handle = requestAnimationFrame(draw);
    };

    draw();
    const onResize = () => draw();
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(handle);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <figure className="orbit-figure">
      <canvas ref={ref} className="orbit-canvas" aria-label="Schematic 3D encounter view showing ASTERIA-3, a debris object, and VARUNA-2 around Earth" />
      <figcaption>
        <span>Schematic encounter geometry</span>
        <span>synthetic_inertial · revision r18</span>
      </figcaption>
    </figure>
  );
}
