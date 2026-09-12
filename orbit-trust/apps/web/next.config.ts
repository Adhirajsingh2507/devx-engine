import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  transpilePackages: ["@engine/math"],
  turbopack: {
    // Include the sibling engine source so linked package files can be watched.
    root: path.resolve(__dirname, "../../.."),
  },
  experimental: {
    externalDir: true,
  },
};

export default nextConfig;
